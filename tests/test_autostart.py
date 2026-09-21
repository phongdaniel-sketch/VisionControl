import unittest
from unittest.mock import MagicMock, patch
from vision_control import autostart


class AutostartTests(unittest.TestCase):
    def setUp(self):
        self.registry = MagicMock()
        self.modules = patch.dict('sys.modules', winreg=self.registry)
        self.modules.start()
        self.platform = patch.object(autostart.sys, 'platform', 'win32')
        self.platform.start()
        self.addCleanup(self.modules.stop)
        self.addCleanup(self.platform.stop)

    def test_enable_writes_only_our_current_user_value(self):
        with patch.object(autostart, 'launch_command', return_value='command'):
            autostart.set_enabled(True)
        self.registry.CreateKeyEx.assert_called_once_with(
            self.registry.HKEY_CURRENT_USER, autostart.RUN_KEY, 0, self.registry.KEY_SET_VALUE)
        self.assertEqual(self.registry.SetValueEx.call_args.args[1:],
                         ('VisionControl', 0, self.registry.REG_SZ, 'command'))

    def test_disable_removes_only_our_value(self):
        autostart.set_enabled(False)
        self.assertEqual(self.registry.DeleteValue.call_args.args[1], 'VisionControl')
        self.registry.DeleteKey.assert_not_called()

    def test_missing_value_is_disabled_and_disable_is_idempotent(self):
        self.registry.OpenKey.side_effect = FileNotFoundError
        self.assertFalse(autostart.is_enabled())
        autostart.set_enabled(False)

    def test_permission_error_propagates(self):
        self.registry.OpenKey.side_effect = PermissionError
        with self.assertRaises(PermissionError): autostart.is_enabled()
        with self.assertRaises(PermissionError): autostart.set_enabled(False)

    def test_read_does_not_write(self):
        self.registry.QueryValueEx.return_value = ('command', 1)
        self.assertTrue(autostart.is_enabled())
        self.registry.SetValueEx.assert_not_called()

    def test_source_launch_is_absolute_and_uses_pythonw(self):
        with patch.object(autostart.sys, 'frozen', False, create=True), patch.object(autostart.Path, 'is_file', return_value=True):
            command=autostart.launch_command()
        self.assertIn('pythonw.exe', command)
        self.assertIn('sys.path.insert', command)
        self.assertIn('vision_control.launcher', command)

    def test_packaged_launch_quotes_spaces(self):
        with patch.object(autostart.sys, 'frozen', True, create=True), patch.object(autostart.sys, 'executable', 'C:/Program Files/VisionControl/app.exe'):
            self.assertTrue(autostart.launch_command().startswith('"'))

    def test_non_windows_does_not_access_registry(self):
        with patch.object(autostart.sys, 'platform', 'darwin'):
            self.assertFalse(autostart.is_enabled())
            with self.assertRaises(RuntimeError):autostart.set_enabled(True)
        self.registry.OpenKey.assert_not_called()
