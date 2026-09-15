from alarm_clock.models import Alarm
from alarm_clock.storage import load_alarms, next_id, save_alarms


def test_load_missing_file_returns_empty(tmp_path):
    assert load_alarms(tmp_path / "does_not_exist.json") == []


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "alarms.json"
    alarms = [
        Alarm(id=1, time="07:30", label="Wake up", repeat="daily"),
        Alarm(id=2, time="09:00", repeat="weekly", weekdays=[0, 2, 4]),
    ]
    save_alarms(alarms, path)
    loaded = load_alarms(path)
    assert loaded == alarms


def test_save_creates_parent_dir(tmp_path):
    path = tmp_path / "nested" / "dir" / "alarms.json"
    save_alarms([Alarm(id=1, time="07:30")], path)
    assert path.exists()


def test_next_id_empty():
    assert next_id([]) == 1


def test_next_id_increments_from_max():
    alarms = [Alarm(id=1, time="07:30"), Alarm(id=5, time="08:00")]
    assert next_id(alarms) == 6
