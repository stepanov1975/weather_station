#!/usr/bin/env python3
"""Tests for IMS city portal forecast parsing."""

import unittest

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
