"""Discord webhook reporting (optional, Cream's-style win/loss embeds)."""
from __future__ import annotations

import json
import urllib.request

from . import config as cfgmod


def post_run(cfg, *, result: str, mode: str, waves: int, yen: int, session_time: str):
    if cfg.get("Webhook", "WebhookEnabled").lower() != "on":
        return
    url = cfg.get("Webhook", "Webhook").strip()
    if not url:
        return
    embed = {
        "title": f"AA Macro — {result}",
        "color": 0x2ECC40 if result == "victory" else 0xE74C3C,
        "fields": [
            {"name": "Mode", "value": mode, "inline": True},
            {"name": "Waves", "value": str(waves), "inline": True},
            {"name": "Yen", "value": f"{yen:,}", "inline": True},
            {"name": "Session", "value": session_time, "inline": True},
        ],
    }
    body = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass  # never let reporting break the loop
