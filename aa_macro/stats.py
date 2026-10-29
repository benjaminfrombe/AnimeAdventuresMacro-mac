"""Session + all-time win/loss stats and recent-run history (Cream's-style)."""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATS_FILE = ROOT / "stats.json"


class Stats:
    def __init__(self):
        self.session = {"victory": 0, "defeat": 0, "started": time.time()}
        self.all_time = {"victory": 0, "defeat": 0}
        self.recent: list[dict] = []
        if STATS_FILE.exists():
            d = json.loads(STATS_FILE.read_text())
            self.all_time = d.get("all_time", self.all_time)

    def record(self, result: str, mode: str, waves: int, yen: int):
        self.session[result] = self.session.get(result, 0) + 1
        self.all_time[result] = self.all_time.get(result, 0) + 1
        self.recent.insert(0, {
            "time": time.strftime("%H:%M:%S"), "result": result,
            "mode": mode, "waves": waves, "yen": yen,
        })
        self.recent = self.recent[:20]
        STATS_FILE.write_text(json.dumps({
            "all_time": self.all_time, "recent": self.recent}, indent=2))

    @property
    def session_time(self) -> str:
        s = int(time.time() - self.session["started"])
        return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"

    @property
    def win_rate(self) -> float:
        total = self.all_time["victory"] + self.all_time["defeat"]
        return self.all_time["victory"] / total if total else 0.0
