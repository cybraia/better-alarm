# alarm-clock

A simple Python CLI alarm clock. No web UI, no database — alarms are stored
in a local JSON file (default: `~/.alarm_clock/alarms.json`).

## Install

```bash
pip install -e .
```

This registers the `alarm` command (via `pyproject.toml`). You can also run
it without installing: `python -m alarm_clock ...`.

## Usage

```bash
# one-time alarm today at 07:30
alarm add 07:30 --label "Wake up"

# one-time alarm on a specific date
alarm add 09:00 --date 2026-09-20 --label "Flight"

# daily alarm
alarm add 06:45 --repeat daily --label "Gym"

# weekly alarm on specific weekdays
alarm add 08:00 --repeat weekly --days mon,wed,fri --label "Standup"

# use a custom sound instead of the system beep
alarm add 07:30 --sound C:\sounds\wake.wav

alarm list
alarm disable 2
alarm enable 2
alarm remove 2

# start the watcher (foreground; Ctrl+C to stop)
alarm start
```

When an alarm is due, `alarm start` rings for about a minute, then rings
again every 5 minutes until you press any key. One-time alarms disable
themselves after ringing; daily/weekly alarms stay enabled for their next
occurrence. `add`/`remove`/`enable`/`disable` take effect immediately in a
running `alarm start`, no restart needed.

Sound playback and beeping use `winsound` (Windows only); dismiss-key
detection uses `msvcrt` (Windows only).

## Tests

```bash
pytest
```
