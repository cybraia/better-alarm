# Python CLI Alarm Clock

## Context

The user wants a standalone alarm clock as a Python CLI application — no web UI, no database. `task-app/` is currently an empty directory (fresh git-less project), so this is a greenfield build with no existing code or patterns to reconcile. Requirements were locked through two rounds of clarifying questions:

- Alarms are **persistent**: saved to a local JSON file, addable/removable at any time, and a separate `start` command watches for due alarms in the foreground.
- Alarms support **full recurrence**: one-time (specific date), daily, or specific weekdays.
- Ringing plays a **configured sound file, falling back to a system beep** if none is set or playback fails.
- Ringing **repeats until dismissed**: beep/play for ~1 minute, then if not dismissed, pause 5 minutes and beep for another minute, repeating indefinitely until the user presses a key.
- **No snooze** — only dismiss.
- Alarms support an **optional label**.
- CLI uses **subcommands** (argparse-style: `add`, `list`, `remove`, `start`, etc.), not an interactive menu.

Since the environment is Windows (win32) and no sound/UI dependencies were requested, the implementation uses **only the Python standard library** — `winsound` (Windows-only, stdlib) handles both beeping and playing `.wav` files, and `msvcrt` (Windows-only, stdlib) handles non-blocking dismiss-keypress detection. This avoids any third-party dependency for a personal Windows CLI tool.

## Project Structure

```
task-app/
  alarm_clock/
    __init__.py
    __main__.py       # enables `python -m alarm_clock ...`
    cli.py            # argparse subcommands: add/list/remove/enable/disable/start
    models.py         # Alarm dataclass + to_dict/from_dict
    storage.py         # load_alarms()/save_alarms() — JSON file I/O
    time_utils.py     # next_trigger(alarm, now) — recurrence math
    ring.py            # ring(alarm) — beep/play-sound-until-dismissed loop
  tests/
    test_time_utils.py
    test_storage.py
    test_models.py
  pyproject.toml       # packaging + `alarm` console-script entry point
  README.md
```

Default storage path: `~/.alarm_clock/alarms.json` (via `pathlib.Path.home()`), overridable with a `--file` option on every subcommand for testing/scripting.

## Data Model (`models.py`)

```python
@dataclass
class Alarm:
    id: int
    time: str                # "HH:MM", 24h
    label: str = ""
    repeat: str = "once"      # "once" | "daily" | "weekly"
    date: str | None = None   # "YYYY-MM-DD", only for repeat == "once"
    weekdays: list[int] = []  # 0=Mon..6=Sun, only for repeat == "weekly"
    sound_file: str | None = None
    enabled: bool = True
```

Validation lives in `cli.py` at `add` time: `--date` requires `repeat=once`, `--days` requires `repeat=weekly`, time parses as `HH:MM`, sound file path exists if given.

## Recurrence Logic (`time_utils.py`)

Single function `next_trigger(alarm, now: datetime) -> datetime | None`:
- `once`: combine `date`+`time`; return `None` if it's already in the past (caller then disables/reports as expired).
- `daily`: today at `time` if that's still ahead of `now`, else tomorrow at `time`.
- `weekly`: nearest date (today included, if time hasn't passed) whose weekday is in `weekdays`.

Pure function taking `now` as a parameter (not `datetime.now()` internally) so it's directly unit-testable without freezing the clock.

## Storage (`storage.py`)

- `load_alarms(path) -> list[Alarm]`: reads JSON, returns `[]` if file doesn't exist yet.
- `save_alarms(path, alarms)`: writes JSON, creating parent dir if needed.
- `next_id(alarms) -> int`: max existing id + 1 (or 1).

## CLI (`cli.py`, argparse subcommands)

- `alarm add TIME [--date YYYY-MM-DD] [--repeat once|daily|weekly] [--days mon,wed,fri] [--label TEXT] [--sound PATH]`
- `alarm list` — table: id, time, schedule description, label, enabled/disabled, sound file (or "beep").
- `alarm remove ID`
- `alarm enable ID` / `alarm disable ID`
- `alarm start [--interval SECONDS]` — foreground watcher (see below).

Entry point `main()` wires subcommands to handler functions; `__main__.py` calls `main()` for `python -m alarm_clock`. `pyproject.toml` also registers `alarm = "alarm_clock.cli:main"` as a console script.

## Watcher Loop (`start` command, in `cli.py`)

Runs until Ctrl+C:
1. Every tick (default 5s, `--interval` configurable): reload alarms from disk (so `add`/`remove`/`enable`/`disable` run in another terminal take effect live, no restart needed).
2. For each enabled alarm, compute `next_trigger`. Track an in-memory `fired_for: dict[id, datetime]` to avoid double-firing within the same trigger instant.
3. When `now >= next_trigger` and not already fired for that instant: print the alarm's label/time, call `ring.ring(alarm)` (blocks until dismissed), then:
   - `once` → set `enabled = False`, save.
   - `daily`/`weekly` → leave enabled; next loop iteration computes the following occurrence naturally.
4. Sleep `interval` seconds between ticks.

## Ringing (`ring.py`)

```python
def ring(alarm) -> None:
    """Beep/play sound in ~60s bursts every 5 min until a key is pressed."""
```
- Uses `msvcrt.kbhit()` in a tight poll loop so dismissal is near-instant, both during the active burst and during the 5-minute quiet gap.
- Burst: if `alarm.sound_file` is set and exists, `winsound.PlaySound(file, SND_FILENAME | SND_ASYNC)` looped for ~60s; on any exception, fall back to `winsound.Beep(...)` pulses.
- No sound file configured → `winsound.Beep(1000, 500)` pulses for ~60s.
- Any keypress (checked every ~0.1-0.2s) stops immediately and returns.

## Testing

- `tests/test_time_utils.py`: table-driven cases for `once` (future/past), `daily` (before/after today's time), `weekly` (today still ahead, today already passed, next matching weekday, wraparound to next week).
- `tests/test_storage.py`: round-trip save/load, missing-file returns `[]`, `next_id` behavior.
- `tests/test_models.py`: `to_dict`/`from_dict` round trip, default values.
- `winsound`/`msvcrt` are not unit tested (Windows-only side effects) — `ring.py` is structured so the burst/gap timing logic could be tested by injecting a fake "kbhit" check, but given the small scope this is verified manually instead.

## Manual Verification

1. `pip install -e .` (or run via `python -m alarm_clock`).
2. `alarm add 14:32 --label "Test" --repeat once` (pick a time ~1 min out).
3. `alarm list` — confirm it shows correctly.
4. `alarm start` — confirm it beeps at the right time, keeps beeping every 5 min until a key is pressed, and disables itself afterward (`alarm list` shows disabled).
5. Add a `--repeat daily` alarm, confirm after dismissing it stays enabled and `alarm list` reflects the next occurrence logic (via a quick unit-level sanity check since waiting 24h isn't practical).
6. While `start` is running, run `alarm add`/`alarm remove` in a second terminal and confirm the watcher picks up the change without restart.