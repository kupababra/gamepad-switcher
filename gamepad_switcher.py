#!/usr/bin/env python3
import sys
import os
import time
from evdev import InputDevice, ecodes
import termios
import tty

# ====================== Konfiguracja =======================
# UWAGA: Ścieżki do urządzeń gamepadów mogą się różnić w zależności od systemu i podłączonych urządzeń.
# Sprawdź dostępne urządzenia poleceniem:
#   ls /dev/input/by-id/
# i dopasuj ścieżki w LEGION i BITDO.
#
# Aby program działał, zainstaluj wymagany pakiet:
#   sudo apt install python3-evdev
#
# Na Gentoo Linux należy zainstalować odpowiedni pakiet:
#   sudo emerge -av dev-python/evdev

LEGION = "/dev/input/by-id/usb-_Legion_Controller_for_Windows_********-event-joystick" #dokonaj zmian w _********-
BITDO = "/dev/input/by-id/usb-8BitDo_Ultimate_C_Wired_Controller_**********-event-joystick" #dokonaj zmian _***********-

TRIGGER_MAX_VALUES = {
    LEGION: 1023,
    BITDO: 255,
}

# Kolory ANSI
PURPLE = "\033[1;35m"
WHITE = "\033[1;37m"
GRAY = "\033[0;37m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"
CLEAR_SCREEN = "\033[2J\033[H"

# ====================== Funkcje =======================

def normalize(val, max_val):
    val = max(0, min(val, max_val))
    return int(val * 10 / max_val)

def stick_pos(val):
    pos = int((val + 32768) * 5 / 65536)
    return max(0, min(pos, 4))

def clear():
    print(CLEAR_SCREEN, end='')

def get_privilege_cmd():
    for cmd in ("doas", "sudo"):
        if os.system(f"command -v {cmd} >/dev/null 2>&1") == 0:
            return cmd
    print("❌ Error: neither doas nor sudo found.", file=sys.stderr)
    sys.exit(1)

def print_banner():
    clear()
    print(f"{WHITE}=========================================================={RESET}")
    print(f"{PURPLE}   Gentoo Linux GAMEPAD SWITCHER & TESTER 0.1.0-alpha{RESET}")
    print(f"{WHITE}   by id3fix@retro-technology.pl Legion Go ↔ 8BitDo{RESET}")
    print(f"{PURPLE}   tipply.pl/@unix-tech -  buy coffe.{RESET}")
    print(f"{PURPLE}   Check https://github.com/kupababra/{RESET}")
    print(f"{WHITE}=========================================================={RESET}\n")
    print(f"{YELLOW}INSTRUKCJA:{RESET}")
    print(" - Zainstaluj zależności: sudo apt install python3-evdev")
    print(" - Na Gentoo Linux: sudo emerge -av dev-python/evdev")
    print(" - Sprawdź ścieżki do kontrolerów: ls /dev/input/by-id/")
    print(" - Dostosuj LEGION i BITDO w konfiguracji programu")
    print(" - Uruchom program z odpowiednimi uprawnieniami")
    print()
    # Dodana nowa sekcja wyjaśniająca działanie programu
    print(f"{YELLOW}WYJAŚNIENIE:{RESET}")
    print(" Ten program służy do wygodnego przełączania się między dwoma kontrolerami:")
    print("  - LEGION GO oraz 8BitDo (Xbox).")
    print(" Zamiast podłączać lub odłączać joystick fizycznie, program manipuluje uprawnieniami do urządzeń Linux")
    print(" (plików w /dev/input/...), aby system widział tylko jeden aktywny kontroler naraz.")
    print(" W ten sposób 'chowa' joystick, który chcemy wyłączyć (ustawia brak praw do odczytu),")
    print(" a drugi udostępnia (dodaje prawa do odczytu/zapisu).")
    print(" To pomaga uniknąć konfliktów w grach czy Steamie, gdzie podłączenie kilku urządzeń może powodować problemy.")
    print(" Możesz także uruchomić tester kontrolera, który pokazuje aktualne przyciski, pozycję drążków i wyzwalaczy.")
    print()

def status():
    legion_access = os.access(LEGION, os.R_OK)
    bitdo_access = os.access(BITDO, os.R_OK)
    if legion_access and not bitdo_access:
        active = "Legion Go"
    elif bitdo_access and not legion_access:
        active = "8BitDo (Xbox)"
    else:
        active = "UNKNOWN / BOTH"
    print(f"{PURPLE}▶ Active controller:{RESET} {WHITE}{active}{RESET}")

def change_permissions(legion_mode: bool):
    """
    Zmienia uprawnienia do urządzeń joysticków:
      - jeśli legion_mode == True: Legion Go jest odsłonięty (chmod 666),
        8BitDo jest schowany (chmod 000)
      - jeśli legion_mode == False: 8BitDo jest odsłonięty, Legion Go jest schowany
    
    Działanie to pozwala systemowi i aplikacjom “widzieć” tylko jeden kontroler na raz.
    """
    priv = get_privilege_cmd()
    if legion_mode:
        os.system(f"{priv} chmod 666 {LEGION}")
        os.system(f"{priv} chmod 000 {BITDO}")
    else:
        os.system(f"{priv} chmod 666 {BITDO}")
        os.system(f"{priv} chmod 000 {LEGION}")

def find_device(devnode):
    if not os.path.exists(devnode):
        print(f"❌ Device {devnode} not found or not connected.", file=sys.stderr)
        sys.exit(1)
    try:
        return InputDevice(devnode)
    except Exception as e:
        print(f"❌ Failed to open device {devnode}: {e}", file=sys.stderr)
        sys.exit(1)

class GamepadState:
    def __init__(self, trigger_max):
        self.A = 0; self.B = 0; self.X = 0; self.Y = 0
        self.LB = 0; self.RB = 0; self.START = 0; self.SELECT = 0
        self.HOME = 0; self.BACK = 0; self.GUIDE = 0; self.MODE = 0; self.FAVOURITES = 0
        self.DPAD_UP = 0; self.DPAD_DOWN = 0; self.DPAD_LEFT = 0; self.DPAD_RIGHT = 0
        self.LX = 0; self.LY = 0; self.RX = 0; self.RY = 0
        self.LT = 0; self.RT = 0
        self.trigger_max = trigger_max

    def draw(self, device_name):
        clear()
        print_banner()
        print(f"{PURPLE}▶ Device:{RESET} {WHITE}{device_name}{RESET}\n")

        def btn(on, label):
            return f"{PURPLE}{label}{RESET}" if on else f"{WHITE}{label}{RESET}"

        print("Buttons:")
        print(f"  {btn(self.LB, '[LB]')}  {btn(self.RB, '[RB]')}  {btn(self.SELECT, '[SEL]')}  {btn(self.START, '[ST]')}")
        print(f"  {btn(self.X, '[Y]')}  {btn(self.Y, '[X]')}  {btn(self.B, '[B]')}  {btn(self.A, '[A]')}")
        print(f"  {btn(self.HOME, '[HOME]')}")
        print(f"  {btn(self.BACK, '[BACK]')}  {btn(self.GUIDE, '[GUIDE]')}  {btn(self.MODE, '[MODE]')}  {btn(self.FAVOURITES, '[*]')}\n")

        up = btn(self.DPAD_UP, "-")
        down = btn(self.DPAD_DOWN, "-")
        left = btn(self.DPAD_LEFT, "-")
        right = btn(self.DPAD_RIGHT, "-")

        print("D-Pad:")
        print(f"    {up}    ")
        print(f" {left}     {right} ")
        print(f"    {down}    \n")

        LXG = stick_pos(self.LX)
        LYG = 4 - stick_pos(self.LY)
        RXG = stick_pos(self.RX)
        RYG = 4 - stick_pos(self.RY)

        def draw_stick(x_pos, y_pos):
            grid = []
            for y in range(5):
                row = ""
                for x in range(5):
                    row += f"{PURPLE}●{RESET}" if (x == x_pos and y == y_pos) else "○"
                grid.append(row)
            return "\n".join(grid)

        print("Left Stick (LX/LY):")
        print(draw_stick(LXG, LYG))
        print()
        print("Right Stick (RX/RY):")
        print(draw_stick(RXG, RYG))
        print()

        def bar(val):
            n = normalize(val, self.trigger_max)
            return f"{PURPLE}{'■' * n}{RESET}"

        print(f"Triggers: LT[{bar(self.LT)}] RT[{bar(self.RT)}]\n")
        print(f"{GRAY}Press buttons / move sticks / pull triggers | [m]enu (Ctrl+C to exit){RESET}")

def print_main_menu():
    clear()
    print_banner()
    print(f"{YELLOW}Menu interaktywne:{RESET}")
    print("  1) Przełącz na LEGION GO")
    print("  2) Przełącz na 8BITDO (XBOX)")
    print("  3) Pokaż status aktywnego kontrolera")
    print("  4) Uruchom tester kontrolera")
    print("  0) Wyjście")
    print()
    print(f"{GRAY}Wybierz opcję (0-4):{RESET} ", end='', flush=True)

def run_switch_mode(legion_mode: bool):
    print(f"{GRAY}Przełączanie kontrolerów...{RESET}")
    change_permissions(legion_mode)
    mode_name = "LEGION GO" if legion_mode else "8BITDO (XBOX)"
    print(f"{PURPLE}▶ Tryb:{RESET} {WHITE}{mode_name}{RESET}\n")
    status()
    print(f"{WHITE}✔ Gotowe. Zrestartuj Steam, by zastosować zmiany.{RESET}")
    print("\nNaciśnij Enter by wrócić do menu...", end='', flush=True)
    input()

def run_status():
    clear()
    print_banner()
    status()
    print("\nNaciśnij Enter by wrócić do menu...", end='', flush=True)
    input()

def run_tester(menu_callback):
    legion_access = os.access(LEGION, os.R_OK)
    bitdo_access = os.access(BITDO, os.R_OK)

    if bitdo_access and not legion_access:
        device_path = BITDO
        device_name = "8BitDo (Xbox)"
    elif legion_access and not bitdo_access:
        device_path = LEGION
        device_name = "Legion Go"
    else:
        clear()
        print("❌ Nie można określić aktywnego kontrolera (problem z uprawnieniami lub dostępem).", file=sys.stderr)
        print("\nNaciśnij Enter by wrócić do menu...", end='', flush=True)
        input()
        return

    device = find_device(device_path)
    gs = GamepadState(trigger_max=TRIGGER_MAX_VALUES.get(device_path, 255))

    key_map = {
        ecodes.BTN_SOUTH: 'A',
        ecodes.BTN_EAST:  'B',
        ecodes.BTN_NORTH: 'Y',
        ecodes.BTN_WEST:  'X',
        ecodes.BTN_TL:    'LB',
        ecodes.BTN_TR:    'RB',
        ecodes.BTN_START: 'START',
        ecodes.BTN_SELECT:'SELECT',
        ecodes.BTN_MODE:  'MODE',
        ecodes.BTN_TOOL_PEN: 'HOME',
        ecodes.BTN_THUMBR: 'GUIDE',
        ecodes.BTN_THUMBL: 'BACK',
        ecodes.BTN_TRIGGER_HAPPY1: 'FAVOURITES',
    }

    abs_codes = {
        ecodes.ABS_X: 'LX',
        ecodes.ABS_Y: 'LY',
        ecodes.ABS_RX: 'RX',
        ecodes.ABS_RY: 'RY',
    }

    left_trigger_abs_candidates = [ecodes.ABS_Z, ecodes.ABS_GAS, ecodes.ABS_MISC, ecodes.ABS_THROTTLE]
    right_trigger_abs_candidates = [ecodes.ABS_RZ, ecodes.ABS_BRAKE, ecodes.ABS_WHEEL, ecodes.ABS_RUDDER]

    try:
        orig_settings = termios.tcgetattr(sys.stdin.fileno())
    except Exception:
        orig_settings = None
    try:
        tty.setcbreak(sys.stdin.fileno())
    except Exception:
        pass

    import select
    try:
        gs.draw(device_name)
        device_fd = device.fd
        stdin_fd = sys.stdin.fileno()

        while True:
            rlist, _, _ = select.select([device_fd, stdin_fd], [], [])
            if stdin_fd in rlist:
                ch = os.read(stdin_fd, 1)
                if not ch:
                    break
                c = ch.decode(errors='ignore').lower()
                if c == 'm':
                    break
            if device_fd in rlist:
                for event in device.read():
                    if event.type == ecodes.EV_KEY:
                        attr = key_map.get(event.code)
                        if attr is not None:
                            setattr(gs, attr, event.value)
                    elif event.type == ecodes.EV_ABS:
                        if event.code in abs_codes:
                            setattr(gs, abs_codes[event.code], event.value)
                        elif event.code in left_trigger_abs_candidates:
                            gs.LT = event.value
                        elif event.code in right_trigger_abs_candidates:
                            gs.RT = event.value
                        elif event.code == ecodes.ABS_HAT0Y:
                            gs.DPAD_UP = 1 if event.value == -1 else 0
                            gs.DPAD_DOWN = 1 if event.value == 1 else 0
                        elif event.code == ecodes.ABS_HAT0X:
                            gs.DPAD_LEFT = 1 if event.value == -1 else 0
                            gs.DPAD_RIGHT = 1 if event.value == 1 else 0
                    gs.draw(device_name)
                    print(f"{GRAY}(Naciśnij 'm', by wrócić do menu){RESET}")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if orig_settings:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, orig_settings)
        clear()
        print(f"❌ Błąd czasu wykonania: {e}", file=sys.stderr)
        print("\nNaciśnij Enter by wrócić do menu...", end='', flush=True)
        input()
    finally:
        if orig_settings:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, orig_settings)

    menu_callback()

def interactive_menu():
    while True:
        print_main_menu()
        try:
            c = input().strip()
        except EOFError:
            c = "0"
        if c == '0':
            clear()
            print(f"{WHITE}Koniec programu Gamepad Switcher & Tester. Do zobaczenia!{RESET}")
            sys.exit(0)
        elif c == '1':
            run_switch_mode(True)
        elif c == '2':
            run_switch_mode(False)
        elif c == '3':
            run_status()
        elif c == '4':
            run_tester(interactive_menu)
        else:
            print(f"{PURPLE}Nieznana opcja: {c}{RESET}")
            time.sleep(1)

def main():
    try:
        interactive_menu()
    except KeyboardInterrupt:
        clear()
        print(f"\n{WHITE}Koniec programu Gamepad Switcher & Tester. Do zobaczenia!{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
