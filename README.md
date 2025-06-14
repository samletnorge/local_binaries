
# local binaries that that are collected as a local package.

## Binaries
- `adb`: Android Debug Bridge binary for local use.
- `scrcpy`: Screen mirroring and control tool for Android devices. and keyboard/mouse input.

## Installation

```bash
uv sync

source .venv/bin/activate

uv run example.py
```

## Prerequisites
- uv
- Android device with USB debugging enabled

## Configuration
- `device_id`: Set this to your Android device's ID.

