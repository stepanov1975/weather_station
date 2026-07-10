#!/usr/bin/env python3
"""Tests for IMS city portal forecast parsing."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from weather_display.services.ims_forecast import IMSCityForecast


class TestIMSCityForecast(unittest.TestCase):
    def test_parse_hadera_city_portal_payload(self):
        payload = {
            "data": {
                "title": "Hadera",
                "analysis": {
                    "temperature": "26.4",
                    "relative_humidity": "76",
                    "weather_code": "1230",
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
                },
            }
        }

        client = IMSCityForecast(location_id=18)
        forecast = client.parse_forecast(payload, days=2)

        self.assertEqual(forecast[0]["date"], "2026-07-03")
        self.assertEqual(forecast[0]["max_temp"], 30.0)
        self.assertEqual(forecast[0]["min_temp"], 23.0)
        self.assertEqual(forecast[0]["condition"], "Cloudy")
        self.assertEqual(forecast[0]["icon_code"], 7)
        self.assertEqual(forecast[1]["condition"], "Clear")
        self.assertEqual(forecast[1]["icon_code"], 1)


if __name__ == "__main__":
    unittest.main()


def test_network_failure_uses_the_cached_payload(tmp_path: Path) -> None:
    cached_payload = {
        "data": {"forecast_data": {}, "weather_codes": {}, "analysis": {}}
    }
    client = IMSCityForecast(location_id=18, cache_path=tmp_path / "forecast.json")
    client.cache.store(cached_payload)

    with patch.object(
        client,
        "_request_payload",
        side_effect=requests.exceptions.ConnectionError("offline"),
    ):
        result = client.fetch_payload(force_refresh=True)

    assert result == {
        "data": cached_payload,
        "connection_status": False,
        "api_status": "offline",
        "cache_hit": True,
    }


def test_invalid_json_payload_is_reported_as_a_fetch_error(tmp_path: Path) -> None:
    client = IMSCityForecast(location_id=18, cache_path=tmp_path / "forecast.json")
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = []

    with patch("weather_display.services.ims_forecast.requests.get", return_value=response):
        result = client.fetch_payload(force_refresh=True)

    assert result["data"] == {"data": {"analysis": {}, "weather_codes": {}, "forecast_data": {}}}
    assert result["connection_status"] is False
    assert result["api_status"] == "error"
    assert result["cache_hit"] is False


def test_missing_forecast_data_returns_no_days() -> None:
    client = IMSCityForecast(location_id=18)

    assert client.parse_forecast({"data": {"weather_codes": {}}}) == []


def test_nonnumeric_forecast_temperatures_remain_empty() -> None:
    client = IMSCityForecast(location_id=18)
    payload = {
        "data": {
            "weather_codes": {"1230": {"desc_en": "Cloudy"}},
            "forecast_data": {
                "2026-07-03": {
                    "daily": {
                        "forecast_date": "2026-07-03",
                        "maximum_temperature": "unknown",
                        "minimum_temperature": None,
                        "weather_code": "1230",
                    }
                }
            },
        }
    }

    assert client.parse_forecast(payload) == [
        {
            "date": "2026-07-03",
            "max_temp": None,
            "min_temp": None,
            "condition": "Cloudy",
            "icon_code": 7,
        }
    ]


def test_unknown_weather_code_is_preserved_with_the_default_icon() -> None:
    client = IMSCityForecast(location_id=18)
    payload = {
        "data": {
            "weather_codes": {},
            "forecast_data": {
                "2026-07-03": {
                    "daily": {
                        "forecast_date": "2026-07-03",
                        "maximum_temperature": "30",
                        "minimum_temperature": "23",
                        "weather_code": "9999",
                    }
                }
            },
        }
    }

    forecast = client.parse_forecast(payload)

    assert forecast[0]["condition"] == "9999"
    assert forecast[0]["icon_code"] == 7
