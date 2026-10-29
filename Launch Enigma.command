#!/bin/sh
# macOS: double-click this file after completing the README setup.
cd -- "$(dirname -- "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo 'First run the Python setup commands in README.md from this folder.'
  exit 1
fi
exec .venv/bin/python desktop/enigma_gui.py
