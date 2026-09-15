from alarm_clock.models import Alarm


def test_to_dict_from_dict_round_trip():
    alarm = Alarm(
        id=3,
        time="06:45",
        label="Gym",
        repeat="weekly",
        weekdays=[0, 2, 4],
        sound_file="C:\\sounds\\gym.wav",
        enabled=False,
    )
    restored = Alarm.from_dict(alarm.to_dict())
    assert restored == alarm


def test_from_dict_defaults():
    alarm = Alarm.from_dict({"id": 1, "time": "07:00"})
    assert alarm.label == ""
    assert alarm.repeat == "once"
    assert alarm.date is None
    assert alarm.weekdays == []
    assert alarm.sound_file is None
    assert alarm.enabled is True


def test_schedule_description_once_with_date():
    alarm = Alarm(id=1, time="07:00", repeat="once", date="2026-09-20")
    assert alarm.schedule_description() == "2026-09-20 07:00"


def test_schedule_description_daily():
    alarm = Alarm(id=1, time="07:00", repeat="daily")
    assert alarm.schedule_description() == "daily 07:00"


def test_schedule_description_weekly():
    alarm = Alarm(id=1, time="07:00", repeat="weekly", weekdays=[0, 4])
    assert alarm.schedule_description() == "weekly[mon,fri] 07:00"
