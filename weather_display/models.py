"""Typed forecast data shared between services and the display controller."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ForecastDay:
    date: str
    max_temp: float | None
    min_temp: float | None
    condition: str | None
    icon_code: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
