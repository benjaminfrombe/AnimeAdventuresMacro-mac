"""Mouse/keyboard input via pynput. Coordinates are logical screen pixels."""
from __future__ import annotations

import random
import time

from pynput.keyboard import Controller as Keyboard, Key
from pynput.mouse import Button, Controller as Mouse

KEY_MAP = {
    "F1": Key.f1, "F2": Key.f2, "F3": Key.f3, "F4": Key.f4,
    "F5": Key.f5, "F6": Key.f6, "F7": Key.f7, "F8": Key.f8,
    "enter": Key.enter, "esc": Key.esc, "space": Key.space,
}


class Input:
    def __init__(self, humanize: bool = True):
        self.mouse = Mouse()
        self.kb = Keyboard()
        self.humanize = humanize

    def click(self, x: int, y: int, delay_after: float = 0.15):
        self.mouse.position = (int(x), int(y))
        time.sleep(random.uniform(0.03, 0.08) if self.humanize else 0.01)
        self.mouse.click(Button.left, 1)
        time.sleep(delay_after)

    def press(self, key: str, delay_after: float = 0.1):
        k = KEY_MAP.get(key.lower(), key)  # plain chars pass through
        self.kb.press(k)
        self.kb.release(k)
        time.sleep(delay_after)

    def drag(self, x1, y1, x2, y2, steps: int = 12):
        self.mouse.position = (int(x1), int(y1))
        time.sleep(0.05)
        self.mouse.press(Button.left)
        for i in range(1, steps + 1):
            t = i / steps
            self.mouse.position = (
                int(x1 + (x2 - x1) * t), int(y1 + (y2 - y1) * t))
            time.sleep(0.015)
        self.mouse.release(Button.left)
        time.sleep(0.1)
