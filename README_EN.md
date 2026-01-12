
---

# 📕 3️⃣ `README_EN.md` (ENGLISH)

```md
# 🎮 Gamepad Switcher & Tester (Legion Go ↔ 8BitDo)

A Linux terminal tool that allows you to switch between two game controllers
without physically unplugging them, and test all inputs in real time.

## How it works
The program changes permissions of `/dev/input/event*` devices:
- active controller → `chmod 666`
- inactive controller → `chmod 000`

This makes games and Steam see **only one controller at a time**.

## Features
- Controller switching (Legion Go ↔ 8BitDo)
- Terminal-based controller tester
- No GUI required (TTY friendly)
- Works with Steam and emulators

## Requirements
```bash
sudo apt install python3-evdev

Gentoo:

sudo emerge -av dev-python/evdev

Setup

List devices:

ls /dev/input/by-id/

Edit paths in gamepad_switcher.py:

LEGION = "/dev/input/by-id/..."
BITDO  = "/dev/input/by-id/..."

Run

python3 gamepad_switcher.py

Tips

    Restart Steam after switching

    Use from TTY for best results

    Permissions reset after reboot

Author

bofh@retro-technology.pl

https://github.com/kupababra
