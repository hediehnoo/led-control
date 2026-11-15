
#!/usr/bin/env python3

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from threading import Event
from gpiozero import LED

# Raspberry Pi GPIO configuration
GPIO_PIN = 17

PID_FILE = Path("/tmp/led_git_gpio17.pid")
LOG_FILE = Path("/tmp/led_git_gpio17.log")

stop_event = Event()


def running_pid():
    if not PID_FILE.exists():
        return None

    try:
        pid = int(PID_FILE.read_text().strip())

        os.kill(pid, 0)

        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
        if b"led_git.py" in cmdline and b"_hold" in cmdline:
            return pid

    except (ValueError, OSError):
        pass

    PID_FILE.unlink(missing_ok=True)
    return None


def hold_led():
    def stop_handler(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    led = LED(GPIO_PIN)

    try:
        led.on()
        print("LED GPIO17 ON", flush=True)

        while not stop_event.wait(1):
            pass

    finally:
        led.off()
        led.close()
        PID_FILE.unlink(missing_ok=True)
        print("LED GPIO17 OFF", flush=True)


def turn_on():
    pid = running_pid()

    if pid:
        print(f"LED is already running. PID={pid}")
        return

    log = open(LOG_FILE, "a")

    try:
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "_hold"
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
    finally:
        log.close()

    PID_FILE.write_text(str(process.pid))

    time.sleep(0.5)

    if running_pid() is None:
        print("ERROR: LED process failed.")
        print(LOG_FILE.read_text(errors="replace")[-2000:])
        return

    print("LED ON - Background process started.")


def turn_off():
    pid = running_pid()

    if not pid:
        print("LED is already OFF.")
        return

    os.kill(pid, signal.SIGTERM)

    for _ in range(30):
        if running_pid() is None:
            print("LED OFF")
            return
        time.sleep(0.1)

    print("WARNING: LED process did not stop.")


def status():
    pid = running_pid()

    if pid:
        print(f"LED process RUNNING - PID={pid}")
    else:
        print("LED process STOPPED")


if __name__ == "__main__":

    command = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    if command == "_hold":
        hold_led()

    elif command == "on":
        turn_on()

    elif command == "off":
        turn_off()

    elif command == "status":
        status()

    else:
        print("Usage:")
        print("python3 led_git.py on")
        print("python3 led_git.py off")
        print("python3 led_git.py status")
