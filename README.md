# 🎮 Gamepad Switcher & Tester (Legion Go ↔ 8BitDo)

Linux terminal tool for switching and testing game controllers.

## Features
- Switch active controller without unplugging
- Hide inactive controller from Steam/games
- Terminal-based controller tester
- Works on TTY (no X / Wayland)

## Requirements
```bash
sudo apt install python3-evdev

Gentoo:

sudo emerge -av dev-python/evdev

Configuration

Check device paths:

ls /dev/input/by-id/

Edit:

LEGION = "/dev/input/by-id/..."
BITDO  = "/dev/input/by-id/..."

Run

python3 gamepad_switcher.py

Notes

After switching controllers, restart Steam.
Author

id3fix@retro-technology.pl
