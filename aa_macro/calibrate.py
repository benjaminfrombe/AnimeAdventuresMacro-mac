"""Calibration helper: shows live matches so you can verify template detection
on your setup. Run while Roblox is on the screen you want to check."""
from __future__ import annotations

import time

from .config import load_config, DETECTION
from .vision import Vision


def main():
    cfg = load_config()
    vision = Vision(cfg)
    names = sorted(
        str(p.relative_to(DETECTION)).removesuffix(".png")
        for p in DETECTION.rglob("*.png")
    )
    print("Live detection — press Ctrl+C to stop. Checking", len(names), "templates.")
    print("Enter a template name to filter (e.g. 'AA/vote-start'), or Enter for all:")
    filt = input("> ").strip()
    while True:
        hits = []
        for name in names:
            if filt and filt not in name:
                continue
            m = vision.find(name, confidence=0.75)
            if m:
                hits.append(m)
        if hits:
            for m in hits:
                print(f"  MATCH {m.name}  score={m.score:.2f}  at=({m.x},{m.y})")
        else:
            print("  no matches")
        time.sleep(1.0)


if __name__ == "__main__":
    main()
