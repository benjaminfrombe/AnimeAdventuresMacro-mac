"""Dungeon state machine — Cream's-style room routing, rebuilt for Anime
Adventures using the original macro's detection templates and settings.

Room priority (default, from reference-settings.ini):
  Rare Chest > Chest > Shop > Hoard > Shrine > Boss > Curse > Purple/Green/Grey
Curse rooms can be avoided per type; shrines accepted/denied per type; shop
purchases follow a relic priority list.
"""
from __future__ import annotations

import logging
import time

from .config import load_config
from .input import Input
from .vision import Vision

log = logging.getLogger("aa.dungeon")

ROOM_TYPES = [
    # template-name fragment -> room type (checked in priority order)
    ("Dungeons/chests-title", "chest"),
    ("Dungeons/shop-title", "shop"),
    ("Dungeons/shrine-title", "shrine"),
    ("Dungeons/boss-label", "boss"),
    ("Dungeons/death-title", "death"),
    ("Dungeons/victory-title", "victory"),
]

CURSES = {
    "Curse of Shopping": "Curses/room-shopping",
    "Curse of Money": "Curses/room-money",
    "Curse of Explosion": "Curses/room-explosion",
    "Curse of Health": "Curses/room-health",
    "Curse of Shielding": "Curses/room-shielding",
    "Curse of Wind": "Curses/room-wind",
    "Curse of Flight": "Curses/room-flight",
    "Curse of Regen": "Curses/room-regen",
}

SHRINES = {
    "Armor": "Curses/shrine-armor", "Burst": "Curses/shrine-burst",
    "Chaos": "Curses/shrine-chaos", "Eruption": "Curses/shrine-eruption",
    "Frenzy": "Curses/shrine-frenzy", "Vampirism": "Curses/shrine-vampirism",
    "Vitality": "Curses/shrine-vitality",
}


class DungeonRunner:
    def __init__(self, cfg=None):
        self.cfg = cfg or load_config()
        self.vision = Vision(self.cfg)
        self.input = Input()
        self.room_priority = [s.strip() for s in self.cfg.get(
            "Dungeon", "RoomPriority").split("|")] if self.cfg.has_option("Dungeon", "RoomPriority") else \
            ["Rare Chest", "Chest", "Shop", "Hoard", "Shrine", "Boss", "Curse"]
        self.avoid_curses = [s.strip() for s in self.cfg.get(
            "Dungeon", "AvoidCurses").split("|")] if self.cfg.has_option("Dungeon", "AvoidCurses") else []
        self.shop_limit = self.cfg.getint("Dungeon", "ShopLimit") if self.cfg.has_option("Dungeon", "ShopLimit") else 2
        self.shop_bought = 0
        self.rooms_cleared = 0

    # ---- detection -----------------------------------------------------
    def current_room(self) -> str | None:
        for fragment, room in ROOM_TYPES:
            if self.vision.find(fragment, confidence=0.75):
                return room
        return None

    def curse_in_room(self) -> str | None:
        """Return the curse name if a curse room is detected."""
        for curse, template in CURSES.items():
            if self.vision.find(template, confidence=0.75):
                return curse
        return None

    def shrine_type(self) -> str | None:
        for shrine, template in SHRINES.items():
            if self.vision.find(template, confidence=0.75):
                return shrine
        return None

    # ---- decisions -----------------------------------------------------
    def decide(self, room: str | None) -> str:
        """Action for the current room: 'enter' | 'avoid' | 'buy' | 'shrine-ok'
        | 'shrine-deny' | 'open-chest' | 'boss' | 'exit'."""
        if room == "chest":
            return "open-chest"
        if room == "shop":
            return "buy" if self.shop_bought < self.shop_limit else "avoid"
        if room == "shrine":
            shrine = self.shrine_type()
            deny = [s.strip() for s in self.cfg.get(
                "Dungeon", "ShrineDeny").split("|")] if self.cfg.has_option("Dungeon", "ShrineDeny") else []
            return "shrine-deny" if shrine in deny else "shrine-ok"
        if room == "boss":
            return "boss"
        if room == "death":
            return "retry"
        if room == "victory":
            return "exit"
        curse = self.curse_in_room()
        if curse and curse in self.avoid_curses:
            log.info("avoiding %s", curse)
            return "avoid"
        return "enter"

    # ---- actions -------------------------------------------------------
    def act(self, action: str) -> bool:
        """Execute one action; returns True when the macro acted."""
        v, inp = self.vision, self.input
        if action == "open-chest":
            return bool(v.find("Dungeons/chests-title")) and self._click_center()
        if action == "buy":
            # buy the highest-priority relic visible in the shop
            for relic in self._shop_priority():
                m = v.find(f"Dungeons/{relic}-name", confidence=0.7)
                if m:
                    inp.click(m.x, m.y)
                    self.shop_bought += 1
                    log.info("bought %s (%d/%d)", relic, self.shop_bought, self.shop_limit)
                    return True
            return False
        if action in ("shrine-ok", "shrine-deny"):
            return self._click_center()  # confirm/deny via center prompt
        if action == "boss":
            time.sleep(2)  # fight; upgrades handled by the main loop
            return False
        if action == "retry":
            m = v.find("AA/retry") or v.find("AA/replay")
            if m:
                inp.click(m.x, m.y)
                return True
        if action == "exit":
            m = v.find("AA/return-to-lobby")
            if m:
                inp.click(m.x, m.y)
                return True
        if action == "avoid":
            return self._click_next_door()
        return False

    def _click_center(self) -> bool:
        w, h = self.cfg.getint("Macro", "CropW"), self.cfg.getint("Macro", "CropH")
        ox, oy = self.vision._offset
        self.input.click(ox + w // 2, oy + h // 2)
        return True

    def _click_next_door(self) -> bool:
        m = self.vision.find("Dungeons/next-label", confidence=0.7)
        if m:
            self.input.click(m.x, m.y)
            self.rooms_cleared += 1
            return True
        return False

    def _shop_priority(self) -> list[str]:
        """Relic priority from settings; fall back to all known relics."""
        if self.cfg.has_option("Dungeon", "ShopPriority"):
            return [s.strip().replace(" ", "").replace("'", "")
                    for s in self.cfg.get("Dungeon", "ShopPriority").split("|")]
        return [p.stem[:-5] for p in (self.vision and __import__("pathlib").Path(__file__).parent.parent
                / "assets/images/Detection/AA/Dungeons").glob("*-name.png")]

    def run_until_exit(self, max_rooms: int = 40, idle_timeout: float = 90.0):
        """Run the dungeon loop until victory/exit or timeout."""
        last_action = time.time()
        while self.rooms_cleared < max_rooms:
            room = self.current_room()
            action = self.decide(room)
            log.info("room=%s action=%s", room, action)
            if action == "exit":
                return "victory"
            acted = self.act(action)
            if acted:
                last_action = time.time()
                time.sleep(1.5)
            elif time.time() - last_action > idle_timeout:
                log.warning("idle timeout in dungeon, backing out")
                return "stuck"
            time.sleep(1.0)
        return "max-rooms"
