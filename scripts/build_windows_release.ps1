param(
    [string]$Version = '1.0.0',
    [string]$CertificateThumbprint = $env:VISIONCONTROL_SIGN_CERT_THUMBPRINT,
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv311\Scripts\python.exe'
$bundle = Join-Path $root 'dist\voice-release\VisionControl'
$exe = Join-Path $bundle 'VisionControl.exe'
$release = Join-Path $root 'release'
$zip = Join-Path $release "VisionControl-$Version-windows-x64.zip"
$checksum = "$zip.sha256"

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw 'Version must use major.minor.patch format.'
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python environment not found: $python"
}
Set-Location -LiteralPath $root

if (-not $SkipBuild) {
    & $python -m PyInstaller --noconfirm --clean --distpath dist/voice-release `
        --workpath build/voice-release VisionControl.spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
}
if (-not (Test-Path -LiteralPath $exe)) {
    throw "Built executable not found: $exe"
}

if ($CertificateThumbprint) {
    $windowsKits = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    $signTools = Get-ChildItem -Path $windowsKits -Filter signtool.exe `
        -Recurse -ErrorAction SilentlyContinue
    $signTool = $signTools |
        Where-Object FullName -Match '\\x64\\signtool\.exe$' |
        Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $signTool) {
        $signTool = $signTools | Sort-Object FullName -Descending | Select-Object -First 1
    }
    if (-not $signTool) { throw 'signtool.exe was not found. Install the Windows SDK.' }
    $certificate = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
        Where-Object Thumbprint -EQ $CertificateThumbprint
    if (-not $certificate) { throw 'The requested code-signing certificate was not found.' }
    & $signTool.FullName sign /sha1 $CertificateThumbprint /fd SHA256 /tr `
        http://timestamp.digicert.com /td SHA256 $exe
    if ($LASTEXITCODE -ne 0) { throw 'Authenticode signing failed.' }
    & $signTool.FullName verify /pa /v $exe
    if ($LASTEXITCODE -ne 0) { throw 'Authenticode verification failed.' }
} else {
    Write-Warning 'No trusted code-signing certificate supplied; the release will be unsigned.'
}

New-Item -ItemType Directory -Force -Path $release | Out-Null
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -LiteralPath $bundle -DestinationPath $zip -CompressionLevel Optimal
$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $zip
"$($hash.Hash)  $([IO.Path]::GetFileName($zip))" | Set-Content -LiteralPath $checksum -Encoding ascii

[pscustomobject]@{
    Version = $Version
    Archive = $zip
    SizeMB = [math]::Round((Get-Item -LiteralPath $zip).Length / 1MB, 1)
    SHA256 = $hash.Hash
    Signed = [bool](Get-AuthenticodeSignature -LiteralPath $exe).SignerCertificate
} | Format-List
