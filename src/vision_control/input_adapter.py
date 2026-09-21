def release_each(operations):
    """Attempt every release, then report failures without losing retry state."""
    errors = []
    for operation in operations:
        try:
            operation()
        except Exception as exc:
            errors.append(exc)
    if errors:
        raise ExceptionGroup("Some input releases failed", errors)


class InputAdapter:
    """Side-effect boundary. Production implementation can be replaced per OS."""

    def move(self, x: float, y: float) -> None: raise NotImplementedError
    def position(self) -> tuple[float, float]: raise NotImplementedError
    def button_down(self, button: str) -> None: raise NotImplementedError
    def button_up(self, button: str) -> None: raise NotImplementedError
    def scroll(self, amount: int) -> None: raise NotImplementedError
    def key_press(self, key: str) -> None: raise NotImplementedError
    def key_down(self, key: str) -> None: raise NotImplementedError
    def key_up(self, key: str) -> None: raise NotImplementedError
    def release_all(self) -> None: raise NotImplementedError

    def scroll_xy(self, x, y):
        if x:
            raise NotImplementedError('Horizontal scroll is unavailable in this adapter')
        self.scroll(y)

    def perform(self, action):
        """One-shot action; do not release modifier keys owned by another gesture."""
        if not action:
            return
        if action in ('voice_listen_toggle', 'pause_gestures', 'open_computer'):
            handler = getattr(self, 'app_action_handler', None)
            if handler is not None:
                handler(action)
            return
        import sys
        actions = {'volume_up': 'media_volume_up', 'volume_down': 'media_volume_down',
                   'mute': 'media_volume_mute',
                   'play_pause': 'media_play_pause', 'next_track': 'media_next',
                   'previous_track': 'media_previous',
                   'zoom_in': ('win' if sys.platform == 'darwin' else 'ctrl') + '+=',
                   'zoom_out': ('win' if sys.platform == 'darwin' else 'ctrl') + '+-'}
        keys = actions.get(action, action).split('+')
        acquired = []
        try:
            for key in keys:
                if key not in getattr(self, 'held_keys', set()):
                    acquired.append(key)
                    self.key_down(key)
        finally:
            release_each([lambda key=k: self.key_up(key) for k in reversed(acquired)])

    def lock_computer(self):
        import sys
        import ctypes
        if sys.platform != 'win32':
            raise RuntimeError('Lock computer requires Windows')
        if not ctypes.windll.user32.LockWorkStation():
            raise RuntimeError('Windows could not lock the workstation')

    def close_window(self, target):
        import sys
        import ctypes
        from ctypes import wintypes
        if sys.platform != 'win32':
            raise RuntimeError('Close window requires Windows')
        api = ctypes.windll.user32
        api.GetForegroundWindow.restype = wintypes.HWND
        api.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
        api.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        name = ctypes.create_unicode_buffer(256)
        if not target or api.GetForegroundWindow() != target:
            raise ValueError('Target window changed')
        if not api.GetClassNameW(target, name, len(name)) or name.value in (
                'Progman', 'WorkerW', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd'):
            raise ValueError('Cannot close the desktop or taskbar')
        # A normal close request preserves the application's unsaved-work prompts.
        if not api.PostMessageW(target, 0x0010, 0, 0):
            raise RuntimeError('Windows could not send the close request')


class PynputInputAdapter(InputAdapter):
    def __init__(self):
        from pynput.keyboard import Controller as KeyboardController, Key
        from pynput.mouse import Button, Controller as MouseController
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.buttons = {"left": Button.left, "right": Button.right, "middle": Button.middle}
        self.keys = {
            "space": Key.space, "enter": Key.enter, "esc": Key.esc,
            "tab": Key.tab, "shift": Key.shift, "ctrl": Key.ctrl,
            "alt": Key.alt, "win": Key.cmd, "left": Key.left,
            "right": Key.right, "up": Key.up, "down": Key.down,
            "backspace": Key.backspace, "delete": Key.delete,
            "media_volume_up": Key.media_volume_up,
            "media_volume_down": Key.media_volume_down,
            "media_volume_mute": Key.media_volume_mute,
            "media_play_pause": Key.media_play_pause,
            "media_next": Key.media_next,
            "media_previous": Key.media_previous,
        }
        self.held_keys: set[str] = set()
        self.held_buttons: set[str] = set()

    def move(self, x, y): self.mouse.position = (int(x), int(y))
    def position(self): return self.mouse.position
    def button_down(self, button):
        self.held_buttons.add(button)
        self.mouse.press(self.buttons[button])
    def button_up(self, button): self.mouse.release(self.buttons[button]); self.held_buttons.discard(button)
    def scroll(self, amount): self.mouse.scroll(0, int(amount))
    def scroll_xy(self, x, y): self.mouse.scroll(int(x), int(y))
    def _key(self, key): return self.keys.get(key, key)
    def key_press(self, key):
        try:
            self.key_down(key)
        finally:
            self.key_up(key)

    def key_down(self, key):
        self.held_keys.add(key)
        self.keyboard.press(self._key(key))
    def key_up(self, key): self.keyboard.release(self._key(key)); self.held_keys.discard(key)
    def release_all(self):
        release_each(
            [lambda key=key: self.key_up(key) for key in tuple(self.held_keys)] +
            [lambda button=button: self.button_up(button)
             for button in tuple(self.held_buttons)])
