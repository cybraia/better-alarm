from __future__ import annotations

import time
from pathlib import Path

from alarm_clock.models import Alarm

BURST_SECONDS = 60
GAP_SECONDS = 300
POLL_INTERVAL = 0.15

try:
    import winsound
except ImportError:  # pragma: no cover - non-Windows fallback
    winsound = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows fallback
    msvcrt = None


def _dismissed() -> bool:
    if msvcrt is None:
        return False
    if msvcrt.kbhit():
        msvcrt.getch()
        return True
    return False


def _start_sound_file(sound_file: str) -> bool:
    """Start looping playback of a sound file. Returns True on success."""
    if winsound is None:
        return False
    try:
        winsound.PlaySound(
            sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
        )
        return True
    except Exception:
        return False


def _stop_sound() -> None:
    if winsound is not None:
        winsound.PlaySound(None, winsound.SND_PURGE)


def _run_burst(alarm: Alarm) -> bool:
    """Play for BURST_SECONDS. Returns True if dismissed during the burst."""
    sound_file = alarm.sound_file
    using_file = bool(sound_file and Path(sound_file).exists() and _start_sound_file(sound_file))

    burst_end = time.monotonic() + BURST_SECONDS
    while time.monotonic() < burst_end:
        if _dismissed():
            _stop_sound()
            return True
        if not using_file and winsound is not None:
            winsound.Beep(1000, 400)
        else:
            time.sleep(POLL_INTERVAL)

    _stop_sound()
    return False


def ring(alarm: Alarm) -> None:
    """Beep/play sound in ~60s bursts every 5 min until a key is pressed."""
    print(f"\a*** ALARM: {alarm.label or alarm.time} *** (press any key to dismiss)")
    while True:
        if _run_burst(alarm):
            print("Alarm dismissed.")
            return

        gap_end = time.monotonic() + GAP_SECONDS
        while time.monotonic() < gap_end:
            if _dismissed():
                print("Alarm dismissed.")
                return
            time.sleep(POLL_INTERVAL)
