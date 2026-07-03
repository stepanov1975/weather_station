"""Typed data shapes shared between services and the display controller."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CurrentWeather:
    temperature: float | None
    humidity: int | None
    condition: str | None = None
    icon_code: int | None = None
    forecast_time: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ForecastDay:
    date: str
    max_temp: float | None
    min_temp: float | None
    condition: str | None
    icon_code: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
