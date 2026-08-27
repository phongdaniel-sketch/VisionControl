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
        }
        self.held_keys: set[str] = set()
        self.held_buttons: set[str] = set()

    def move(self, x, y): self.mouse.position = (int(x), int(y))
    def position(self): return self.mouse.position
    def button_down(self, button): self.mouse.press(self.buttons[button]); self.held_buttons.add(button)
    def button_up(self, button): self.mouse.release(self.buttons[button]); self.held_buttons.discard(button)
    def scroll(self, amount): self.mouse.scroll(0, int(amount))
    def _key(self, key): return self.keys.get(key, key)
    def key_press(self, key): self.keyboard.press(self._key(key)); self.keyboard.release(self._key(key))
    def key_down(self, key): self.keyboard.press(self._key(key)); self.held_keys.add(key)
    def key_up(self, key): self.keyboard.release(self._key(key)); self.held_keys.discard(key)
    def release_all(self):
        for key in tuple(self.held_keys): self.key_up(key)
        for button in tuple(self.held_buttons): self.button_up(button)
