"""Global hotkeys (F1 start, F2 pause, F3 stop) via pynput."""
from __future__ import annotations

from pynput import keyboard

from .config import load_config
from .game import Game


def main():
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config()
    game = Game(cfg)

    def on_press(key):
        name = getattr(key, "name", "") or ""
        if name == cfg.get("Keybinds", "StartKey").lower():
            if not game.running:
                import threading
                threading.Thread(target=game.run_forever, daemon=True).start()
        elif name == cfg.get("Keybinds", "PauseKey").lower():
            game.paused = not game.paused
        elif name == cfg.get("Keybinds", "CloseKey").lower():
            game.running = False
            return False  # stop listener

    print("AA Macro (mac). F1=start F2=pause F3=stop. Focus Roblox and press F1.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    main()
