#!/bin/bash
# AnimeAdventuresMacro-mac launcher
set -e
cd "$(dirname "$0")"

VENV=".venv"

setup() {
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -r requirements.txt
  echo "Setup done. Grant Accessibility, Input Monitoring and Screen Recording"
  echo "permissions to your terminal app in System Settings > Privacy & Security."
}

case "${1:-run}" in
  setup) setup ;;
  calibrate) "$VENV/bin/python" -m aa_macro.calibrate ;;
  *) exec "$VENV/bin/python" -m aa_macro "$@" ;;
esac
