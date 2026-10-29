"""Task queue — Cream's-style: build a queue of tasks (mode, stage, repeats)
and let the macro work through all of them in order. Persisted to queue.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE_FILE = ROOT / "queue.json"


@dataclass
class Task:
    mode: str = "Portals"        # Portals | Story | Raids | Legend Stages | Dungeons | Infinite
    map: str = ""                # map/portal name (optional; empty = first available)
    stage: str = ""              # stage/act (Story modes)
    difficulty: str = "Hard"
    solo: bool = True
    repeats: int = 1
    done: int = 0                # completed runs for this task


@dataclass
class Queue:
    tasks: list[Task] = field(default_factory=list)
    current: int = 0

    def save(self):
        QUEUE_FILE.write_text(json.dumps({"current": self.current,
            "tasks": [asdict(t) for t in self.tasks]}, indent=2))

    @classmethod
    def load(cls) -> "Queue":
        if QUEUE_FILE.exists():
            d = json.loads(QUEUE_FILE.read_text())
            q = cls(current=d.get("current", 0))
            q.tasks = [Task(**t) for t in d.get("tasks", [])]
            return q
        return cls()

    def next_task(self) -> Task | None:
        while self.current < len(self.tasks):
            t = self.tasks[self.current]
            if t.done < t.repeats:
                return t
            self.current += 1
        return None

    def mark_done(self, task: Task):
        task.done += 1
        self.save()
