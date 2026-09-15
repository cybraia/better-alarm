from __future__ import annotations

from dataclasses import dataclass, field

REPEAT_KINDS = ("once", "daily", "weekly")
WEEKDAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@dataclass
class Alarm:
    id: int
    time: str
    label: str = ""
    repeat: str = "once"
    date: str | None = None
    weekdays: list[int] = field(default_factory=list)
    sound_file: str | None = None
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time,
            "label": self.label,
            "repeat": self.repeat,
            "date": self.date,
            "weekdays": self.weekdays,
            "sound_file": self.sound_file,
            "enabled": self.enabled,
        }

    @staticmethod
    def from_dict(data: dict) -> "Alarm":
        return Alarm(
            id=data["id"],
            time=data["time"],
            label=data.get("label", ""),
            repeat=data.get("repeat", "once"),
            date=data.get("date"),
            weekdays=data.get("weekdays", []),
            sound_file=data.get("sound_file"),
            enabled=data.get("enabled", True),
        )

    def schedule_description(self) -> str:
        if self.repeat == "once":
            return f"{self.date} {self.time}" if self.date else self.time
        if self.repeat == "daily":
            return f"daily {self.time}"
        days = ",".join(WEEKDAY_NAMES[d] for d in sorted(self.weekdays))
        return f"weekly[{days}] {self.time}"
