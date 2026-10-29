# AnimeAdventuresMacro-mac

macOS port of [Capy's AA Macro](https://github.com/capybarnia4life/AnimeAdventuresMacro)
(v3.1, Windows / AutoHotkey). This is a clean-room reimplementation in Python:
the original ships no source code, only a compiled `.exe`, so the game loop was
reconstructed from the shipped detection templates and `Settings.ini`.

**Reuses the original `Images/Detection` templates** (115 PNGs) directly —
template matching is platform-independent.

## How it works

- Screen capture with `mss`, template matching with OpenCV (`cv2.matchTemplate`).
- Mouse/keyboard via `pynput` (clicks, keys, drag).
- All captures and clicks are normalized to a reference resolution so the
  original Windows templates still match on Retina / any window size.
- State machine: lobby → portal/story select → vote start → place & upgrade
  units → victory/defeat → replay/next → reconnect on disconnect.
- Global hotkeys: F1 start, F2 pause, F3 stop (same as the original).

## Requirements

- macOS 12+ (Apple Silicon or Intel), Roblox desktop app
- Python 3.10+
- System Settings → Privacy & Security → grant your terminal (or the app)
  **Accessibility**, **Input Monitoring** and **Screen Recording**.
  Without these, clicks do nothing and captures come back black.

## Install

```bash
./run.sh setup      # creates a venv and installs deps
./run.sh            # starts the macro
./run.sh calibrate  # helper: click in Roblox to record coordinates
```

## Configure

Edit `config.ini` (same keys as the original `Settings.ini`, which is kept in
`assets/reference-settings.ini`). Key sections:

- `[Server]` — private server link, public rejoin
- `[Delays]` — scan/placement/victory delays (ms)
- `[Webhook]` — optional Discord webhook reporting

## Status

Work in progress. Core vision + input + loop are implemented; the menu flow
needs per-user calibration on first run (`run.sh calibrate`), because button
positions depend on your Roblox window size. Detection templates are matched
anywhere on screen, so most steps work without calibration.

## Legal / risk

Automation violates Roblox ToS and can get your account banned. Use a throwaway
account. The original macro's assets belong to their author; this repo is for
personal use.

## Calibrated templates (mac)

`AA/portal-start.png` and `AA/vote-yes.png` were captured on macOS from the
live game and pre-scaled by 1/0.90 so the pipeline's `ScaleFactor=0.90`
normalizes them back. Capture new templates the same way (see
`aa_macro/calibrate.py`).
