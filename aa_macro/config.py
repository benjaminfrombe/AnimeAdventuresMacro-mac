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
        "MaxWaves": "0",            # 0 = unlimited
    },
}


def load_config(path: Path | None = None) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(DEFAULTS)
    target = path or ROOT / "config.ini"
    if target.exists():
        # original file is UTF-16LE; configparser handles str content
        text = target.read_bytes()
        try:
            content = text.decode("utf-16")
        except UnicodeDecodeError:
            content = text.decode("utf-8", "replace")
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
