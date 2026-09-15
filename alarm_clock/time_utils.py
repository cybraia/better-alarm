from __future__ import annotations

from datetime import datetime, timedelta

from alarm_clock.models import Alarm


def parse_hhmm(value: str) -> tuple[int, int]:
    hour_str, _, minute_str = value.partition(":")
    hour, minute = int(hour_str), int(minute_str)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"time out of range: {value}")
    return hour, minute


def next_trigger(alarm: Alarm, now: datetime) -> datetime | None:
    """Return the next datetime this alarm should fire at or after `now`.

    Returns None for a `once` alarm whose date/time has already passed.
    """
    hour, minute = parse_hhmm(alarm.time)

    if alarm.repeat == "once":
        if not alarm.date:
            raise ValueError("once alarm requires a date")
        year, month, day = (int(part) for part in alarm.date.split("-"))
        candidate = datetime(year, month, day, hour, minute)
        return candidate if candidate >= now else None

    if alarm.repeat == "daily":
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate < now:
            candidate += timedelta(days=1)
        return candidate

    if alarm.repeat == "weekly":
        if not alarm.weekdays:
            raise ValueError("weekly alarm requires at least one weekday")
        today_candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        for offset in range(8):
            candidate = today_candidate + timedelta(days=offset)
            if candidate < now:
                continue
            if candidate.weekday() in alarm.weekdays:
                return candidate
        raise AssertionError("unreachable: a matching weekday exists within 7 days")

    raise ValueError(f"unknown repeat kind: {alarm.repeat}")
