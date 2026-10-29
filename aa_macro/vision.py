"""Screen capture + template matching.

All captures are downscaled from Retina (2x) to logical pixels and then
rescaled so the game window matches the reference resolution the original
Windows templates were captured at. Matching therefore works on any setup.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import mss
import numpy as np

from . import config as cfgmod

# Roblox game area: the top bar and taskbar chrome are excluded; the macro
# matches against the full virtual screen by default (Roblox is fullscreen-ish).
@dataclass
class Match:
    name: str
    x: int          # logical screen coordinates (for clicking)
    y: int
    score: float


class Vision:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ref_w = cfg.getint("Macro", "ReferenceWidth")
        self.ref_h = cfg.getint("Macro", "ReferenceHeight")
        self.confidence = cfg.getfloat("Macro", "Confidence")
        self._templates: dict[str, np.ndarray] = {}

    # ---- capture -------------------------------------------------------
    def grab_gray(self) -> np.ndarray:
        with mss.mss() as sct:
            mon = sct.monitors[0]  # full virtual screen
            frame = np.array(sct.grab(mon))
        bgr = frame[:, :, :3]
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        # Retina: physical pixels = 2x logical. Normalize to logical size.
        h, w = gray.shape
        if h > 1440:  # crude but effective Retina heuristic; calibrated later
            gray = cv2.resize(gray, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        self._last_logical = gray
        return gray

    def _scale_for(self, gray: np.ndarray) -> float:
        """Scale factor mapping reference-resolution templates onto this capture."""
        h, w = gray.shape
        # The game window is assumed to fill the screen; scale by height.
        return h / self.ref_h

    # ---- templates -----------------------------------------------------
    def template(self, name: str) -> np.ndarray:
        if name not in self._templates:
            path = cfgmod.template_path(name)
            img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise FileNotFoundError(path)
            self._templates[name] = img
        return self._templates[name]

    # ---- matching ------------------------------------------------------
    def find(self, name: str, confidence: float | None = None) -> Match | None:
        """Find a template anywhere on screen. Returns Match in screen coords."""
        conf = confidence if confidence is not None else self.confidence
        gray = self.grab_gray()
        tpl = self.template(name)
        scale = self._scale_for(gray)
        scaled = cv2.resize(tpl, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        if scaled.shape[0] > gray.shape[0] or scaled.shape[1] > gray.shape[1]:
            return None
        res = cv2.matchTemplate(gray, scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val < conf:
            return None
        # max_loc is in logical-capture coords; screen coords == logical coords
        return Match(name=name, x=max_loc[0] + scaled.shape[1] // 2,
                     y=max_loc[1] + scaled.shape[0] // 2, score=float(max_val))

    def wait_for(self, name: str, timeout: float = 15.0, interval: float = 0.3) -> Match | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            m = self.find(name)
            if m:
                return m
            time.sleep(interval)
        return None

    def any_of(self, names: list[str]) -> Match | None:
        for n in names:
            m = self.find(n)
            if m:
                return m
        return None
