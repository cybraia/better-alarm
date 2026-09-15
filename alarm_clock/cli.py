from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path

from alarm_clock.models import REPEAT_KINDS, WEEKDAY_NAMES, Alarm
from alarm_clock.ring import ring
from alarm_clock.storage import DEFAULT_PATH, load_alarms, next_id, save_alarms
from alarm_clock.time_utils import next_trigger, parse_hhmm


def _parse_days(value: str) -> list[int]:
    days = []
    for part in value.split(","):
        part = part.strip().lower()
        if part not in WEEKDAY_NAMES:
            raise argparse.ArgumentTypeError(
                f"invalid day '{part}', expected one of {','.join(WEEKDAY_NAMES)}"
            )
        days.append(WEEKDAY_NAMES.index(part))
    return sorted(set(days))


def cmd_add(args: argparse.Namespace) -> None:
    parse_hhmm(args.time)  # validate format early

    if args.repeat == "once":
        if not args.date:
            args.date = datetime.now().strftime("%Y-%m-%d")
        if args.days:
            raise SystemExit("--days is only valid with --repeat weekly")
    elif args.repeat == "daily":
        if args.date or args.days:
            raise SystemExit("--date/--days are not valid with --repeat daily")
    elif args.repeat == "weekly":
        if not args.days:
            raise SystemExit("--repeat weekly requires --days")
        if args.date:
            raise SystemExit("--date is not valid with --repeat weekly")

    if args.sound and not Path(args.sound).exists():
        raise SystemExit(f"sound file not found: {args.sound}")

    alarms = load_alarms(args.file)
    alarm = Alarm(
        id=next_id(alarms),
        time=args.time,
        label=args.label or "",
        repeat=args.repeat,
        date=args.date,
        weekdays=_parse_days(args.days) if args.days else [],
        sound_file=args.sound,
    )
    alarms.append(alarm)
    save_alarms(alarms, args.file)
    print(f"Added alarm {alarm.id}: {alarm.schedule_description()}")


def cmd_list(args: argparse.Namespace) -> None:
    alarms = load_alarms(args.file)
    if not alarms:
        print("No alarms.")
        return
    for a in alarms:
        status = "enabled" if a.enabled else "disabled"
        sound = a.sound_file or "beep"
        label = f' "{a.label}"' if a.label else ""
        print(f"[{a.id}] {a.schedule_description()}{label} ({status}, sound={sound})")


def cmd_remove(args: argparse.Namespace) -> None:
    alarms = load_alarms(args.file)
    remaining = [a for a in alarms if a.id != args.id]
    if len(remaining) == len(alarms):
        raise SystemExit(f"no alarm with id {args.id}")
    save_alarms(remaining, args.file)
    print(f"Removed alarm {args.id}")


def _set_enabled(args: argparse.Namespace, enabled: bool) -> None:
    alarms = load_alarms(args.file)
    for a in alarms:
        if a.id == args.id:
            a.enabled = enabled
            save_alarms(alarms, args.file)
            print(f"{'Enabled' if enabled else 'Disabled'} alarm {args.id}")
            return
    raise SystemExit(f"no alarm with id {args.id}")


def cmd_enable(args: argparse.Namespace) -> None:
    _set_enabled(args, True)


def cmd_disable(args: argparse.Namespace) -> None:
    _set_enabled(args, False)


def cmd_start(args: argparse.Namespace) -> None:
    """Foreground watcher loop.

    `next_trigger(alarm, now)` always returns a time >= now, so re-deriving it
    fresh every tick would make the fire check `now >= trigger` true only in
    a razor-thin instant that a polling loop would almost always miss. Instead
    each alarm's next trigger is computed once and cached; the alarm fires
    once wall-clock time reaches that fixed point, then the cache is advanced
    from just past that point (not from "now", which may have moved a long
    way forward while the alarm was ringing).
    """
    print(f"Watching alarms in {args.file} (interval={args.interval}s). Ctrl+C to stop.")
    next_run: dict[int, datetime] = {}
    try:
        while True:
            alarms = load_alarms(args.file)
            now = datetime.now()
            changed = False
            live_ids = set()
            for alarm in alarms:
                if not alarm.enabled:
                    next_run.pop(alarm.id, None)
                    continue
                live_ids.add(alarm.id)

                if alarm.id not in next_run:
                    trigger = next_trigger(alarm, now)
                    if trigger is None:
                        alarm.enabled = False
                        changed = True
                        continue
                    next_run[alarm.id] = trigger

                if now >= next_run[alarm.id]:
                    fired_at = next_run.pop(alarm.id)
                    ring(alarm)
                    if alarm.repeat == "once":
                        alarm.enabled = False
                        changed = True
                    else:
                        next_run[alarm.id] = next_trigger(alarm, fired_at + timedelta(seconds=1))

            for stale_id in set(next_run) - live_ids:
                next_run.pop(stale_id, None)

            if changed:
                save_alarms(alarms, args.file)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alarm", description="A simple CLI alarm clock.")
    parser.add_argument(
        "--file", type=Path, default=DEFAULT_PATH, help="path to the alarms JSON file"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a new alarm")
    p_add.add_argument("time", help="alarm time, HH:MM (24h)")
    p_add.add_argument("--date", help="date YYYY-MM-DD (only with --repeat once)")
    p_add.add_argument("--repeat", choices=REPEAT_KINDS, default="once")
    p_add.add_argument("--days", help="comma-separated weekdays, e.g. mon,wed,fri")
    p_add.add_argument("--label", help="optional label")
    p_add.add_argument("--sound", help="path to a .wav file to play instead of beeping")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="list alarms")
    p_list.set_defaults(func=cmd_list)

    p_remove = sub.add_parser("remove", help="remove an alarm")
    p_remove.add_argument("id", type=int)
    p_remove.set_defaults(func=cmd_remove)

    p_enable = sub.add_parser("enable", help="enable an alarm")
    p_enable.add_argument("id", type=int)
    p_enable.set_defaults(func=cmd_enable)

    p_disable = sub.add_parser("disable", help="disable an alarm")
    p_disable.add_argument("id", type=int)
    p_disable.set_defaults(func=cmd_disable)

    p_start = sub.add_parser("start", help="watch for due alarms (foreground)")
    p_start.add_argument("--interval", type=int, default=5, help="poll interval in seconds")
    p_start.set_defaults(func=cmd_start)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
