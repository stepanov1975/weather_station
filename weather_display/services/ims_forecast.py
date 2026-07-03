"""
IMS city portal forecast service.

The IMS city portal endpoint returns JSON for a city, including current forecast
analysis and daily forecasts. This service normalizes that payload into the
small dictionaries consumed by the existing weather display GUI.
"""

import logging
from pathlib import Path
from typing import Any

import requests

from .. import config
from ..models import CurrentWeather, ForecastDay
from .json_cache import JsonCache

logger = logging.getLogger(__name__)


class IMSCityForecast:
    """Fetches and parses forecast data from the IMS city portal JSON endpoint."""

    BASE_URL = "https://ims.gov.il/en/city_portal/{location_id}"

    WEATHER_ICON_MAP: dict[str, int] = {
        "clear": 1,
        "partly cloudy": 3,
        "cloudy": 7,
        "fog": 11,
        "rain": 18,
        "light rain": 12,
        "showers": 12,
        "thunderstorm": 15,
        "dust": 5,
        "sandstorms": 5,
        "hot": 30,
        "extremely hot": 30,
        "cold": 31,
        "extremely cold": 31,
        "snow": 22,
    }

    def __init__(
        self,
        location_id: int = 18,
        timeout_seconds: int = 30,
        cache_path: str | Path | None = None,
    ):
        self.location_id = location_id
        self.timeout_seconds = timeout_seconds
        self.url = self.BASE_URL.format(location_id=location_id)
        self.cache = JsonCache(cache_path or config.IMS_FORECAST_CACHE_PATH)
        self._connection_status = False
        logger.info("IMSCityForecast initialized for location id %s", location_id)

    @property
    def connection_status(self) -> bool:
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
            }

        if not force_refresh and self.cache.is_valid(cache_duration):
            logger.info("Using cached IMS city forecast payload.")
            self._connection_status = True
            return {
                "data": self.cache.payload,
                "connection_status": True,
                "api_status": "ok",
                "cache_hit": True,
            }

        try:
            payload = self._request_payload()
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
            }

    def get_current_weather(self, force_refresh: bool = False) -> dict[str, Any]:
        payload_result = self.fetch_payload(force_refresh=force_refresh)
        return {
            "data": self.parse_current_weather(payload_result["data"]),
            "connection_status": payload_result["connection_status"],
            "api_status": payload_result["api_status"],
            "cache_hit": payload_result["cache_hit"],
        }

    def get_forecast(self, days: int = 3, force_refresh: bool = False) -> dict[str, Any]:
        payload_result = self.fetch_payload(force_refresh=force_refresh)
        return {
            "data": self.parse_forecast(payload_result["data"], days=days),
            "connection_status": payload_result["connection_status"],
            "api_status": payload_result["api_status"],
            "cache_hit": payload_result["cache_hit"],
        }

    def parse_current_weather(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data", {})
        analysis = data.get("analysis", {})
        condition = self._condition_from_code(data, analysis.get("weather_code"))
        return CurrentWeather(
            temperature=self._to_float(analysis.get("temperature")),
            humidity=self._to_int(analysis.get("relative_humidity")),
            condition=condition,
            icon_code=self._icon_code_for_condition(condition),
            forecast_time=analysis.get("forecast_time"),
        ).to_dict()

    def parse_forecast(self, payload: dict[str, Any], days: int = 3) -> list[dict[str, Any]]:
        data = payload.get("data", {})
        forecast_data = data.get("forecast_data", {})
        parsed_days: list[dict[str, Any]] = []

        for forecast_date in sorted(forecast_data.keys()):
            daily = forecast_data.get(forecast_date, {}).get("daily", {})
            if not daily:
                continue
            condition = self._condition_from_code(data, daily.get("weather_code"))
            parsed_days.append(
                ForecastDay(
                    date=daily.get("forecast_date") or forecast_date,
                    max_temp=self._to_float(daily.get("maximum_temperature")),
                    min_temp=self._to_float(daily.get("minimum_temperature")),
                    condition=condition,
                    icon_code=self._icon_code_for_condition(condition),
                ).to_dict()
            )
            if len(parsed_days) >= days:
                break

        return parsed_days

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
        condition_lower = condition.lower().strip()
        if condition_lower in self.WEATHER_ICON_MAP:
            return self.WEATHER_ICON_MAP[condition_lower]
        for key, icon_code in self.WEATHER_ICON_MAP.items():
            if key in condition_lower:
                return icon_code
        return 7

    def _get_mock_payload(self) -> dict[str, Any]:
        return {
            "data": {
                "title": "Hadera",
                "analysis": {
                    "temperature": "26",
                    "relative_humidity": "70",
                    "weather_code": "1230",
                    "forecast_time": "2026-07-03 12:00:00",
                },
                "weather_codes": {
                    "1230": {"desc_en": "Cloudy", "desc": "Cloudy"},
                    "1250": {"desc_en": "Clear", "desc": "Clear"},
                },
                "forecast_data": {
                    "2026-07-03": {
                        "daily": {
                            "forecast_date": "2026-07-03",
                            "maximum_temperature": "30",
                            "minimum_temperature": "23",
                            "weather_code": "1230",
                        }
                    },
                    "2026-07-04": {
                        "daily": {
                            "forecast_date": "2026-07-04",
                            "maximum_temperature": "31",
                            "minimum_temperature": "24",
                            "weather_code": "1250",
                        }
                    },
                    "2026-07-05": {
                        "daily": {
                            "forecast_date": "2026-07-05",
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

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None
