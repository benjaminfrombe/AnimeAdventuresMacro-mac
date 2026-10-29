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
from .queue import Queue
from .stats import Stats
from .vision import Vision
from .webhooks import post_run

log = logging.getLogger("aa")

# template name groups
CONNECTION = ["AA/Connection/reconnect", "AA/Connection/title", "AA/Connection/idle-278"]
RESULT_WIN = ["AA/victory"]
RESULT_LOSE = ["AA/defeat"]
# result screens: Next -> Return to lobby / Pick Next Portal
NEXT = ["AA/result-next", "AA/next-level", "AA/next-room", "AA/reward-continue",
        "AA/replay", "AA/retry", "AA/return-to-lobby"]
UPGRADES = [f"AA/upgrade-{i}" for i in range(5)] + ["AA/upgrade-max-button"]


class Game:
    def __init__(self, cfg):
        self.cfg = cfg
        self.vision = Vision(cfg)
        self.input = Input()
        self.running = False
        self.paused = False
        self.runs = 0
        self.queue = Queue.load()
        self.stats = Stats()
        self._last_progress = time.time()   # for auto-recovery

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
        """From lobby: join a portal, then vote Yes to start."""
        # portal join prompt / start button in the portal lobby
        for name in ("AA/portal-start", "AA/vote-start"):
            if self._click_match(name, delay=1.0):
                time.sleep(self.cfg.getint("Delays", "StageClickDelay") / 1000)
                # confirm the vote
                self._click_match("AA/vote-yes", delay=1.0)
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

    def close_overlays(self):
        """The chat overlay blocks clicks on game buttons. Toggle it closed via
        the topbar chat bubble (game-area-relative position, calibrated)."""
        ox, oy = self.vision._offset
        self.input.click(ox + 139, oy + 34, delay_after=0.5)

    # ---- auto-recovery (Cream's-style) ---------------------------------
    def _stuck_check(self):
        """No recognizable screen for too long -> back out and retry."""
        if time.time() - self._last_progress > 90:
            log.warning("no progress for 90s — attempting recovery")
            self.input.press("esc", delay_after=1.0)
            m = self.vision.find("AA/return-to-lobby")
            if m:
                self.input.click(m.x, m.y)
            self._last_progress = time.time()

    # ---- main loop -----------------------------------------------------
    def run_forever(self):
        self.running = True
        max_waves = self.cfg.getint("Macro", "MaxWaves")
        while self.running:
            if self.paused:
                time.sleep(0.5)
                continue
            try:
                self.close_overlays()
                if self._handle_connection():
                    self._last_progress = time.time()
                    continue
                result = self.handle_result()
                if result:
                    self.runs += 1
                    self._last_progress = time.time()
                    mode = self.cfg.get("Macro", "Mode")
                    self.stats.record(result, mode, waves=0, yen=0)
                    post_run(self.cfg, result=result, mode=mode, waves=0, yen=0,
                             session_time=self.stats.session_time)
                    log.info("run %d finished: %s (win rate %.0f%%)",
                             self.runs, result, self.stats.win_rate * 100)
                    task = self.queue.next_task()
                    if task:
                        self.queue.mark_done(task)
                        self.cfg.set("Macro", "Mode", task.mode)
                    if max_waves and self.runs >= max_waves:
                        log.info("max runs reached (%d), stopping", max_waves)
                        self.running = False
                        break
                    continue
                if self.start_run():
                    self._last_progress = time.time()
                    continue
                self.in_game()
                self._stuck_check()
            except KeyboardInterrupt:
                self.running = False
            except Exception:
                log.exception("loop error; retrying in 2s")
                time.sleep(2)
        log.info("stopped after %d runs", self.runs)
