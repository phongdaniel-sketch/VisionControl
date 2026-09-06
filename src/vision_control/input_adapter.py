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
        import sys
        actions = {'volume_up': 'media_volume_up', 'volume_down': 'media_volume_down',
                   'mute': 'media_volume_mute',
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
