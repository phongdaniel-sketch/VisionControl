import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class StartupAndDisplayClarityTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows launch helper')
    def test_windows_helper_pause_flag_is_opt_in(self):
        import subprocess
        root = Path(__file__).parents[1]
        command = r'''
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path (Get-Location) 'scripts/windows.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'PowerShell parse failed'}
$switch=$ast.Find({param($n) $n -is [System.Management.Automation.Language.SwitchStatementAst]},$true)
$run=$switch.Clauses | Where-Object { $_.Item1.Value -eq 'run' }
if(-not $run){throw 'Run branch missing'}
$body=[scriptblock]::Create('& '+$run.Item2.Extent.Text)
function Invoke-Checked { param($Executable,$Arguments) $script:captured=$Arguments }
$pythonPath='mock-python'; $CameraIndex=7
$StartPaused=$false
& $body
if($captured -contains '--start-paused'){throw 'Normal launch ignores saved preference'}
if(($captured -join ' ') -ne '-m vision_control.launcher --camera-index 7'){throw 'Unexpected launch arguments'}
$StartPaused=$true
& $body
if($captured -notcontains '--start-paused'){throw 'Explicit safe launch is not paused'}
'''
        result = subprocess.run(['powershell','-NoProfile','-Command',command],
                                cwd=root,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_settings_explain_startup_override_and_disable_unsupported_switch(self):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        from PySide6.QtWidgets import QApplication, QLabel
        from vision_control import settings_ui
        from vision_control.settings import DesktopSettings, save_desktop_settings, load_desktop_settings
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory)/'settings.json'
            profile = Path(directory)/'profile.json'
            save_desktop_settings(settings,DesktopSettings(start_paused=False))
            with patch.object(settings_ui,'APP_SETTINGS',settings), patch.object(settings_ui,'USER_PROFILE',profile):
                window = settings_ui.SettingsWindow()
                try:
                    self.assertFalse(window.start_paused.isChecked())
                    labels = [label.text() for label in window.findChildren(QLabel)]
                    self.assertTrue(any('--start-paused' in text and 'Save' in text for text in labels))
                    self.assertIn('--start-paused',window.start_paused.toolTip())
                    window.monitor_mode.setCurrentText('active')
                    for mode in ('palm','thumb_lock'):
                        window.pointer_mode.setCurrentIndex(window.pointer_mode.findData(mode))
                        window._update_monitor_state()
                        self.assertFalse(window.edge_switch.isEnabled())
                        self.assertFalse(window.edge_dwell.isEnabled())
                        self.assertFalse(window.edge_zone.isEnabled())
                        self.assertIn('Unavailable',window.edge_switch_note.text())
                    # Opening and reading Settings never rewrites the preference.
                    self.assertFalse(load_desktop_settings(settings).start_paused)
                finally:
                    window.close()


if __name__ == '__main__':
    unittest.main()
