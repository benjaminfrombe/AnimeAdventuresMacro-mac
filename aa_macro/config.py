"""Configuration loader. Reads config.ini (UTF-8) with the same keys as the
original Windows macro's Settings.ini (kept in assets/reference-settings.ini)."""
import configparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DETECTION = ASSETS / "images" / "Detection"

DEFAULTS = {
    "Keybinds": {
        "StartKey": "F1", "PauseKey": "F2", "CloseKey": "F3",
        "RestartKey": "F4", "CaptureKey": "F5",
    },
    "Server": {
        "UsePrivateServerLink": "on", "PrivateServer": "", "PublicRejoin": "on",
        "WaveRestart": "0",
    },
    "Delays": {
        "ScanDelay": "150", "PlacementRetryDelay": "450",
        "StageClickDelay": "500", "VictoryDelay": "500",
    },
    "Webhook": {"WebhookEnabled": "off", "Webhook": ""},
    "Macro": {
        "Mode": "Portals",          # Portals | Story | Raids | Legend Stages | Dungeons | Infinite
        "ReferenceWidth": "1280",   # resolution the templates were captured at
        "ReferenceHeight": "720",
        "Confidence": "0.82",
        "ScaleFactor": "0.90",      # calibrated on a 998x658 game area (2026-10-29)
        "MonitorIndex": "2",        # mss monitor holding the Roblox window
        "CropX": "222", "CropY": "142", "CropW": "998", "CropH": "658",
        "MaxWaves": "0",            # 0 = unlimited
    },
    "Dungeon": {
        "RoomPriority": "Rare Chest|Chest|Shop|Hoard|Shrine|Boss|Curse",
        "AvoidCurses": "Curse of Shopping|Curse of Explosion|Curse of Health|Curse of Shielding",
        "ShopLimit": "2",
        "ShopPriority": "",         # empty = template order; e.g. Philosopher's Stone|Genie Lamp
        "ShrineDeny": "",           # shrine types to deny, e.g. Chaos|Frenzy
    },
}


def load_config(path: Path | None = None) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(DEFAULTS)
    target = path or ROOT / "config.ini"
    if target.exists():
        # original file is UTF-16LE with BOM; our own config.ini is UTF-8
        raw = target.read_bytes()
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            content = raw.decode("utf-16")
        else:
            content = raw.decode("utf-8", "replace")
        cfg.read_string(content)
    else:
        save_config(cfg, target)
    return cfg


def save_config(cfg: configparser.ConfigParser, path: Path | None = None) -> None:
    target = path or ROOT / "config.ini"
    with open(target, "w", encoding="utf-8") as fh:
        cfg.write(fh)


def template_path(name: str) -> Path:
    """Resolve a template name like 'AA/vote-start' or 'AA/Connection/reconnect'."""
    p = DETECTION / f"{name}.png"
    if not p.exists():
        raise FileNotFoundError(f"template not found: {p}")
    return p
