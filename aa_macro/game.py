"""Game state machine — the reconstructed core loop of Capy's AA Macro.

Flow per run (reconstructed from the shipped detection templates):
  connection check -> lobby (portal/story select) -> vote-start ->
  in-game (place units, upgrade) -> victory/defeat -> replay / next-level ->
  back to lobby. Disconnects trigger rejoin handling.
"""
from __future__ import annotations

import logging
import time

from .input import Input
from .vision import Vision

log = logging.getLogger("aa")

# template name groups
CONNECTION = ["AA/Connection/reconnect", "AA/Connection/title", "AA/Connection/idle-278"]
RESULT_WIN = ["AA/victory"]
RESULT_LOSE = ["AA/defeat"]
NEXT = ["AA/next-level", "AA/next-room", "AA/reward-continue", "AA/replay", "AA/retry"]
UPGRADES = [f"AA/upgrade-{i}" for i in range(5)] + ["AA/upgrade-max-button"]


class Game:
    def __init__(self, cfg):
        self.cfg = cfg
        self.vision = Vision(cfg)
        self.input = Input()
        self.running = False
        self.paused = False
        self.runs = 0

    # ---- helpers -------------------------------------------------------
    def _click_match(self, name: str, delay: float = 0.4) -> bool:
        m = self.vision.find(name)
        if m:
            log.info("click %s (score %.2f at %d,%d)", name, m.score, m.x, m.y)
            self.input.click(m.x, m.y, delay_after=delay)
            return True
        return False

    def _handle_connection(self) -> bool:
        for name in CONNECTION:
            if self._click_match(name, delay=1.5):
                log.info("reconnect flow triggered via %s", name)
                time.sleep(5)
                return True
        return False

    # ---- phases --------------------------------------------------------
    def start_run(self):
        """From lobby: select mode entry and start the match."""
        # vote/start button appears on the mode select screen
        if self._click_match("AA/vote-start", delay=1.0):
            time.sleep(self.cfg.getint("Delays", "StageClickDelay") / 1000)
            return True
        return False

    def in_game(self):
        """Place/upgrade loop while in a match."""
        scan = self.cfg.getint("Delays", "ScanDelay") / 1000
        retry = self.cfg.getint("Delays", "PlacementRetryDelay") / 1000
        for name in UPGRADES:
            if self._click_match(name, delay=retry / 1000):
                return  # one action per scan cycle
        time.sleep(scan)

    def handle_result(self) -> str | None:
        """victory/defeat -> click through next/replay screens. Returns phase."""
        for name in RESULT_WIN:
            if self.vision.find(name):
                log.info("victory detected")
                time.sleep(self.cfg.getint("Delays", "VictoryDelay") / 1000)
                self._click_through_next()
                return "victory"
        for name in RESULT_LOSE:
            if self.vision.find(name):
                log.info("defeat detected")
                self._click_through_next()
                return "defeat"
        return None

    def _click_through_next(self):
        # click successive next/replay/continue screens until none matches
        for _ in range(6):
            clicked = False
            for name in NEXT:
                if self._click_match(name, delay=0.8):
                    clicked = True
                    break
            if not clicked:
                break
            time.sleep(0.5)

    # ---- main loop -----------------------------------------------------
    def run_forever(self):
        self.running = True
        max_waves = self.cfg.getint("Macro", "MaxWaves")
        while self.running:
            if self.paused:
                time.sleep(0.5)
                continue
            try:
                if self._handle_connection():
                    continue
                result = self.handle_result()
                if result:
                    self.runs += 1
                    log.info("run %d finished: %s", self.runs, result)
                    if max_waves and self.runs >= max_waves:
                        log.info("max runs reached (%d), stopping", max_waves)
                        self.running = False
                        break
                    continue
                if self.start_run():
                    continue
                self.in_game()
            except KeyboardInterrupt:
                self.running = False
            except Exception:
                log.exception("loop error; retrying in 2s")
                time.sleep(2)
        log.info("stopped after %d runs", self.runs)
