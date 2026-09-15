from datetime import datetime

import pytest

from alarm_clock.models import Alarm
from alarm_clock.time_utils import next_trigger


def test_once_future():
    alarm = Alarm(id=1, time="10:00", repeat="once", date="2026-09-20")
    now = datetime(2026, 9, 15, 8, 0)
    assert next_trigger(alarm, now) == datetime(2026, 9, 20, 10, 0)


def test_once_past_returns_none():
    alarm = Alarm(id=1, time="10:00", repeat="once", date="2026-09-10")
    now = datetime(2026, 9, 15, 8, 0)
    assert next_trigger(alarm, now) is None


def test_once_today_exact_time_is_included():
    alarm = Alarm(id=1, time="10:00", repeat="once", date="2026-09-15")
    now = datetime(2026, 9, 15, 10, 0)
    assert next_trigger(alarm, now) == datetime(2026, 9, 15, 10, 0)


def test_daily_before_time_today():
    alarm = Alarm(id=1, time="10:00", repeat="daily")
    now = datetime(2026, 9, 15, 8, 0)
    assert next_trigger(alarm, now) == datetime(2026, 9, 15, 10, 0)


def test_daily_after_time_rolls_to_tomorrow():
    alarm = Alarm(id=1, time="10:00", repeat="daily")
    now = datetime(2026, 9, 15, 12, 0)
    assert next_trigger(alarm, now) == datetime(2026, 9, 16, 10, 0)


def test_weekly_today_still_ahead():
    # 2026-09-15 is a Tuesday (weekday 1)
    alarm = Alarm(id=1, time="10:00", repeat="weekly", weekdays=[1, 3])
    now = datetime(2026, 9, 15, 8, 0)
    assert next_trigger(alarm, now) == datetime(2026, 9, 15, 10, 0)


def test_weekly_today_already_passed_picks_next_match():
    # Tuesday already passed 10:00 -> next match is Thursday (weekday 3)
    alarm = Alarm(id=1, time="10:00", repeat="weekly", weekdays=[1, 3])
    now = datetime(2026, 9, 15, 12, 0)
    assert next_trigger(alarm, now) == datetime(2026, 9, 17, 10, 0)


def test_weekly_wraps_to_next_week():
    # Only Tuesday selected, already passed today -> next Tuesday
    alarm = Alarm(id=1, time="10:00", repeat="weekly", weekdays=[1])
    now = datetime(2026, 9, 15, 12, 0)
    assert next_trigger(alarm, now) == datetime(2026, 9, 22, 10, 0)


def test_weekly_requires_weekdays():
    alarm = Alarm(id=1, time="10:00", repeat="weekly", weekdays=[])
    with pytest.raises(ValueError):
        next_trigger(alarm, datetime(2026, 9, 15))


def test_once_requires_date():
    alarm = Alarm(id=1, time="10:00", repeat="once", date=None)
    with pytest.raises(ValueError):
        next_trigger(alarm, datetime(2026, 9, 15))
