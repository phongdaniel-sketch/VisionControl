param(
    [ValidateSet('setup', 'test', 'run', 'diagnose')]
    [string]$Action = 'test',
    [int]$CameraIndex = 0
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot '.venv311/Scripts/python.exe'
$previousPythonPath = $env:PYTHONPATH
$previousQtPlatform = $env:QT_QPA_PLATFORM

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable failed with exit code $LASTEXITCODE"
    }
}

Push-Location $repoRoot
try {
    if ($Action -eq 'setup') {
        if (-not (Test-Path -LiteralPath $pythonPath)) {
            Invoke-Checked 'py' @('-3.11', '-m', 'venv', '.venv311')
        }
    }
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        throw 'Run scripts/windows.ps1 setup after installing Python 3.11.'
    }
    Invoke-Checked $pythonPath @('-c', 'import sys; assert sys.version_info[:2] == (3, 11), sys.version; print(sys.version)')
    $env:PYTHONPATH = Join-Path $repoRoot 'src'
    switch ($Action) {
        'diagnose' {
            Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
            Invoke-Checked $pythonPath @('-m', 'vision_control.launcher', '--diagnostics', '--camera-index', "$CameraIndex")
        }
        'setup' {
            Invoke-Checked $pythonPath @('-m', 'pip', 'install', '-r', 'requirements.txt')
            Invoke-Checked $pythonPath @('-m', 'pip', 'install', '-e', '.')
            Invoke-Checked $pythonPath @('-m', 'pip', 'check')
        }
        'test' {
            $env:QT_QPA_PLATFORM = 'offscreen'
            Invoke-Checked $pythonPath @('-m', 'unittest', 'discover', '-s', 'tests', '-v')
            Invoke-Checked $pythonPath @('-m', 'compileall', '-q', 'src', 'tests', 'scripts')
            Invoke-Checked 'git' @('diff', '--check')
        }
        'run' {
            Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
            Invoke-Checked $pythonPath @('-m', 'vision_control.launcher', '--camera-index', "$CameraIndex", '--start-paused')
        }
    }
}
finally {
    $env:PYTHONPATH = $previousPythonPath
    $env:QT_QPA_PLATFORM = $previousQtPlatform
    Pop-Location
}
