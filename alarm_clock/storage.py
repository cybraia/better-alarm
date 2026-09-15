from __future__ import annotations

import json
from pathlib import Path

from alarm_clock.models import Alarm

DEFAULT_PATH = Path.home() / ".alarm_clock" / "alarms.json"


def load_alarms(path: Path = DEFAULT_PATH) -> list[Alarm]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Alarm.from_dict(item) for item in raw]


def save_alarms(alarms: list[Alarm], path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([a.to_dict() for a in alarms], f, indent=2)


def next_id(alarms: list[Alarm]) -> int:
    return max((a.id for a in alarms), default=0) + 1
