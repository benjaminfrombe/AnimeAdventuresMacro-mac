# AnimeAdventuresMacro-mac

**Cream's-style auto-farm macro for Roblox *Anime Adventures*, built for macOS.**

Inspired by [Cream's Macro for Anime Expeditions](https://github.com/Cweamy/Anime-Expeditions-Creams-Macro)
(task queue, auto-recovery, vision-based automation, macOS support) — but for
the right game: **Anime Adventures**. Detection templates come from
[Capy's AA Macro](https://github.com/capybarnia4life/AnimeAdventuresMacro)
(v3.1), reused with credit; the game logic is a clean-room reimplementation in
Python since the original ships only a compiled Windows `.exe`.

## Features

- **Vision-based automation** — screen capture (`mss`) + OpenCV template
  matching against 120 detection templates. No injection, no memory reading.
- **Task queue** (`queue.json`) — queue up Portals / Story / Raids / Dungeons /
  Infinite tasks with repeat counts; the macro works through them in order.
- **Auto-recovery** — no recognizable screen for 90 s → backs out to the lobby
  and retries instead of derailing an unattended session.
- **Full run loop (live-verified)** — portal start → vote Yes → match →
  victory/defeat → Next → Return to lobby → next run.
- **Dungeon state machine** — room routing by priority (Rare Chest > Chest >
  Shop > Hoard > Shrine > Boss > Curse), curse avoidance per type, shop
  purchases by relic priority, shrine accept/deny, boss/death handling.
- **Win/loss stats** — session + all-time counters, win rate, recent-run
  history (`stats.json`).
- **Discord webhooks** — optional victory/defeat embeds with mode, waves, yen
  and session time.
- **Global hotkeys** — F1 start, F2 pause, F3 stop (same as the original).
- **Calibration tools** — `run.sh calibrate` shows live template matches so
  any setup can be calibrated in minutes.

## Requirements

- macOS 12+ (Apple Silicon or Intel), Roblox desktop app
- Python 3.10+
- System Settings → Privacy & Security → grant your terminal (or the app)
  **Accessibility**, **Input Monitoring** and **Screen Recording**.
  Without these, clicks do nothing and captures come back black.

## Install

```bash
./run.sh setup      # creates a venv and installs deps
./run.sh            # starts the macro (F1 to start, F3 to stop)
./run.sh calibrate  # live template-match viewer for calibration
```

## Configure

`config.ini` uses the same keys as the original `Settings.ini`
(`assets/reference-settings.ini`), plus:

- `[Macro]` — mode, game-window crop (monitor + rect), scale factor, confidence
- `[Dungeon]` — room priority, curse avoidance, shop limit/priority, shrine deny
- `[Webhook]` — Discord webhook reporting

Queue tasks live in `queue.json`:

```json
{"current": 0, "tasks": [
  {"mode": "Portals", "repeats": 10},
  {"mode": "Dungeons", "repeats": 3}
]}
```

## Calibrated setup (reference)

The shipped defaults were calibrated on a 2560×1440 display with the Roblox
window at a 998×658 game area: `ScaleFactor=0.90`, `MonitorIndex=2`,
crop `222,142,998,658`. Templates captured on macOS are pre-scaled by 1/0.90
(see `aa_macro/calibrate.py`).

## Status

- [x] Vision + input pipeline (live-tested)
- [x] Portal → vote → match → result → lobby loop (live-tested)
- [x] Task queue, auto-recovery, stats, webhooks
- [x] Dungeon state machine (needs live calibration)
- [ ] Auto unit placement / upgrades (templates need recapture on macOS)
- [ ] OCR reward reading (Tesseract)
- [ ] Walk path recorder
- [ ] Dashboard UI

## Legal / risk

Automation violates Roblox ToS and can get your account banned. Use a throwaway
account. Original macro assets belong to their respective authors; this repo is
for personal use.
