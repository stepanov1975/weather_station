"""
IMS city portal forecast service.

The IMS city portal endpoint returns JSON for a city, including daily forecasts.
This service normalizes that payload into the small dictionaries consumed by
the existing weather display GUI.
"""

import logging
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests

from .. import config
from ..models import ForecastDay
from .json_cache import JsonCache

logger = logging.getLogger(__name__)


class IMSCityForecast:
    """Fetches and parses forecast data from the IMS city portal JSON endpoint."""

    BASE_URL = "https://ims.gov.il/en/city_portal/{location_id}"

    IMS_ICON_CODE_MAP: dict[str, int] = {
        "1010": 45,  # Sandstorms
        "1020": 15,  # Thunderstorms
        "1060": 22,  # Snow
        "1070": 49,  # Light snow
        "1080": 25,  # Sleet
        "1140": 18,  # Rainy
        "1160": 11,  # Fog
        "1220": 3,   # Partly cloudy
        "1230": 7,   # Cloudy
        "1250": 1,   # Clear
        "1260": 32,  # Windy
        "1270": 47,  # Muggy
        "1300": 48,  # Frost
        "1310": 30,  # Hot
        "1320": 31,  # Cold
        "1510": 51,  # Stormy
        "1520": 50,  # Heavy snow
        "1530": 14,  # Partly cloudy, possible rain
        "1540": 13,  # Cloudy, possible rain
        "1560": 13,  # Cloudy, light rain
        "1570": 46,  # Dust
        "1580": 30,  # Extremely hot
        "1590": 31,  # Extremely cold
    }

    WEATHER_ICON_MAP: dict[str, int] = {
        "sunny": 1,
        "mostly sunny": 2,
        "partly sunny": 3,
        "intermittent clouds": 4,
        "hazy sunshine": 5,
        "mostly cloudy": 6,
        "overcast": 8,
        "dreary": 8,
        "mist": 11,
        "clear": 1,
        "partly cloudy": 3,
        "cloudy": 7,
        "fog": 11,
        "rain": 18,
        "light rain": 12,
        "showers": 12,
        "thunderstorm": 15,
        "t-storms": 15,
        "mostly cloudy with showers": 13,
        "partly sunny with showers": 14,
        "mostly cloudy with thunderstorms": 16,
        "partly sunny with thunderstorms": 17,
        "flurries": 19,
        "mostly cloudy with flurries": 20,
        "partly sunny with flurries": 21,
        "mostly cloudy with snow": 23,
        "ice": 24,
        "freezing rain": 26,
        "rain and snow": 29,
        "clear (night)": 33,
        "mostly clear (night)": 34,
        "partly cloudy (night)": 35,
        "intermittent clouds (night)": 36,
        "hazy moonlight": 37,
        "mostly cloudy (night)": 38,
        "partly cloudy with showers (night)": 39,
        "mostly cloudy with showers (night)": 40,
        "partly cloudy with thunderstorms (night)": 41,
        "mostly cloudy with thunderstorms (night)": 42,
        "mostly cloudy with flurries (night)": 43,
        "mostly cloudy with snow (night)": 44,
        "dust": 46,
        "sandstorms": 45,
        "hot": 30,
        "extremely hot": 30,
        "cold": 31,
        "extremely cold": 31,
        "snow": 22,
        "sleet": 25,
        "windy": 32,
        "muggy": 47,
        "frost": 48,
        "stormy": 51,
        "light snow": 49,
        "heavy snow": 50,
        "partly cloudy, possible rain": 14,
        "cloudy, possible rain": 13,
        "cloudy, light rain": 13,
    }

    def __init__(
        self,
        location_id: int = 18,
        timeout_seconds: int | tuple[int, int] = (3, 10),
        cache_path: str | Path | None = None,
    ):
        self.location_id = location_id
        self.timeout_seconds = timeout_seconds
        self.url = self.BASE_URL.format(location_id=location_id)
        default_cache_path = config.IMS_FORECAST_CACHE_PATH
        self.cache = JsonCache(cache_path or default_cache_path.with_name(
            f"{default_cache_path.stem}_{location_id}{default_cache_path.suffix}"
        ))
        if self.cache.payload is not None:
            try:
                self._validate_payload(self.cache.payload)
            except ValueError as exc:
                logger.warning("Ignoring invalid forecast cache %s: %s", self.cache.path, exc)
                self.cache.payload = None
                self.cache.timestamp = None
        self._connection_status: bool | None = False
        logger.info("IMSCityForecast initialized for location id %s", location_id)

    @property
    def connection_status(self) -> bool | None:
        return self._connection_status

    def fetch_payload(self, force_refresh: bool = False) -> dict[str, Any]:
        cache_duration = config.IMS_FORECAST_UPDATE_INTERVAL_MINUTES * 60
        if config.USE_MOCK_DATA:
            payload = self._get_mock_payload()
            self._connection_status = True
            return {
                "data": payload,
                "connection_status": True,
                "api_status": "mock",
                "cache_hit": False,
                "cache_timestamp": None,
            }

        if not force_refresh and self.cache.is_valid(cache_duration):
            logger.info("Using cached IMS city forecast payload.")
            self._connection_status = None
            return {
                "data": self.cache.payload,
                "connection_status": None,
                "api_status": "ok",
                "cache_hit": True,
                "cache_timestamp": self.cache.timestamp,
            }

        try:
            payload = self._request_payload()
            self._validate_payload(payload)
            try:
                self.cache.store(payload)
            except OSError as exc:
                logger.warning("Fetched IMS city forecast but could not write cache %s: %s", self.cache.path, exc)
            self._connection_status = True
            return {
                "data": payload,
                "connection_status": True,
                "api_status": "ok",
                "cache_hit": False,
                "cache_timestamp": self.cache.timestamp,
            }
        except (OSError, requests.exceptions.RequestException, ValueError) as exc:
            logger.error("Failed to fetch IMS city forecast: %s", exc, exc_info=True)
            self._connection_status = False
            fallback = self.cache.payload
            return {
                "data": fallback or self._empty_payload(),
                "connection_status": False,
                "api_status": "offline" if fallback else "error",
                "cache_hit": fallback is not None,
                "cache_timestamp": self.cache.timestamp if fallback else None,
            }

    def get_forecast(self, days: int = 3, force_refresh: bool = False) -> dict[str, Any]:
        payload_result = self.fetch_payload(force_refresh=force_refresh)
        return {
            "data": self.parse_forecast(payload_result["data"], days=days),
            "connection_status": payload_result["connection_status"],
            "api_status": payload_result["api_status"],
            "cache_hit": payload_result["cache_hit"],
            "cache_timestamp": payload_result["cache_timestamp"],
        }

    def parse_forecast(
        self,
        payload: dict[str, Any],
        days: int = 3,
        today: date | None = None,
    ) -> list[dict[str, Any]]:
        data = payload.get("data", {})
        forecast_data = data.get("forecast_data", {})
        parsed_days: list[dict[str, Any]] = []
        earliest_date = (today or date.today()).isoformat()

        for forecast_date in sorted(forecast_data.keys()):
            daily = forecast_data.get(forecast_date, {}).get("daily", {})
            if not daily:
                continue
            display_date = daily.get("forecast_date") or forecast_date
            if display_date < earliest_date:
                continue
            weather_code = daily.get("weather_code")
            condition = self._condition_from_code(data, weather_code)
            parsed_days.append(
                ForecastDay(
                    date=display_date,
                    max_temp=self._to_float(daily.get("maximum_temperature")),
                    min_temp=self._to_float(daily.get("minimum_temperature")),
                    condition=condition,
                    icon_code=self._icon_code_for_weather(weather_code, condition),
                ).to_dict()
            )
            if len(parsed_days) >= days:
                break

        return parsed_days

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        """Require a renderable forecast before replacing the last good cache."""
        try:
            forecast_count = len(payload["data"]["forecast_data"])
            forecast = self.parse_forecast(payload, days=forecast_count, today=date.min)
            if not forecast:
                raise ValueError("No daily forecasts")
            for day in forecast:
                date.fromisoformat(day["date"])
                if day["condition"] is not None and not isinstance(day["condition"], str):
                    raise ValueError("Invalid weather condition")
                for key in ("max_temp", "min_temp"):
                    if day[key] is not None and not math.isfinite(day[key]):
                        raise ValueError("Non-finite forecast temperature")
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid IMS forecast payload: {exc}") from exc

    def _request_payload(self) -> dict[str, Any]:
        logger.info("Fetching IMS city forecast from %s", self.url)
        response = requests.get(self.url, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("IMS city portal response was not a JSON object")
        return payload

    def _condition_from_code(self, data: dict[str, Any], weather_code: Any | None) -> str | None:
        if not weather_code:
            return None
        weather_codes = data.get("weather_codes", {})
        code_data = weather_codes.get(str(weather_code), {})
        return code_data.get("desc_en") or code_data.get("desc") or str(weather_code)

    def _icon_code_for_condition(self, condition: str | None) -> int | None:
        if not condition:
            return None
        condition_lower = " ".join(condition.lower().split())
        if condition_lower in self.WEATHER_ICON_MAP:
            return self.WEATHER_ICON_MAP[condition_lower]
        # Preserve precipitation in mixed phrases such as "mostly cloudy with
        # light rain", even when the sky description is the longer match.
        precipitation = ("rain", "snow", "sleet", "flurries", "storm", "showers")
        for key in sorted(
            self.WEATHER_ICON_MAP,
            key=lambda phrase: (any(term in phrase for term in precipitation), len(phrase)),
            reverse=True,
        ):
            if key in condition_lower:
                return self.WEATHER_ICON_MAP[key]
        return 7

    def _icon_code_for_weather(
        self,
        weather_code: Any | None,
        condition: str | None,
    ) -> int | None:
        mapped_code = self.IMS_ICON_CODE_MAP.get(str(weather_code))
        return mapped_code if mapped_code is not None else self._icon_code_for_condition(condition)

    def _get_mock_payload(self) -> dict[str, Any]:
        forecast_dates = [(date.today() + timedelta(days=offset)).isoformat() for offset in range(3)]
        return {
            "data": {
                "title": "Hadera",
                "analysis": {
                    "temperature": "26",
                    "relative_humidity": "70",
                    "weather_code": "1230",
                },
                "weather_codes": {
                    "1230": {"desc_en": "Cloudy", "desc": "Cloudy"},
                    "1250": {"desc_en": "Clear", "desc": "Clear"},
                },
                "forecast_data": {
                    forecast_dates[0]: {
                        "daily": {
                            "forecast_date": forecast_dates[0],
                            "maximum_temperature": "30",
                            "minimum_temperature": "23",
                            "weather_code": "1230",
                        }
                    },
                    forecast_dates[1]: {
                        "daily": {
                            "forecast_date": forecast_dates[1],
                            "maximum_temperature": "31",
                            "minimum_temperature": "24",
                            "weather_code": "1250",
                        }
                    },
                    forecast_dates[2]: {
                        "daily": {
                            "forecast_date": forecast_dates[2],
                            "maximum_temperature": "31",
                            "minimum_temperature": "25",
                            "weather_code": "1250",
                        }
                    },
                },
            }
        }

    @staticmethod
    def _empty_payload() -> dict[str, Any]:
        return {"data": {"analysis": {}, "weather_codes": {}, "forecast_data": {}}}

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
