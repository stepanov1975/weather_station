"""Focused tests for utility normal, fallback, and invalid-input behavior."""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from weather_display.models import ForecastDay
from weather_display.services.time_service import TimeService
from weather_display.utils.helpers import (
    check_internet_connection,
    get_day_name,
    load_image,
)
from weather_display.utils.localization import (
    get_day_name_localized,
    get_formatted_date,
    get_translation,
    translate_weather_condition,
)


class _FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz: object = None) -> "_FrozenDateTime":
        del tz
        return cls(2026, 7, 10, 8, 9, 10)


def test_get_day_name_returns_not_available_for_none() -> None:
    with patch("weather_display.utils.helpers.config.LANGUAGE", "en"):
        assert get_day_name(None) == "N/A"


def test_localization_falls_back_for_unknown_language_and_key() -> None:
    assert get_translation("not_available", "unsupported") == "N/A"
    assert get_translation("missing_key", "ru") == "missing_key"


def test_weather_condition_handles_none_and_unmapped_text() -> None:
    assert translate_weather_condition(None, "en") == "Unknown"
    assert translate_weather_condition("Volcanic ash", "en") == "Volcanic ash"


def test_weather_condition_translates_muggy_without_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="weather_display.utils.localization"):
        assert translate_weather_condition("Muggy", "en") == "Muggy"
        assert translate_weather_condition("Muggy", "ru") == "Душно"

    assert "No translation mapping found" not in caplog.text


@pytest.mark.parametrize(
    ("condition", "expected"),
    [
        ("Sleet", "Мокрый снег"),
        ("Frost", "Мороз"),
        ("Stormy", "Шторм"),
        ("Cloudy, possible rain", "Облачно, возможен дождь"),
        ("Partly cloudy, possible rain", "Переменная облачность, возможен дождь"),
    ],
)
def test_official_ims_conditions_are_translated(condition: str, expected: str) -> None:
    assert translate_weather_condition(condition, "ru") == expected


def test_day_name_localization_accepts_iso_date_and_rejects_invalid_input() -> None:
    assert get_day_name_localized("2026-07-10T08:09:10+03:00", "en") == "Friday"
    assert get_day_name_localized("not-a-date", "en") == "Unknown"


def test_formatted_date_uses_frozen_clock_and_language_fallback() -> None:
    with patch("weather_display.utils.localization.datetime", _FrozenDateTime):
        assert get_formatted_date("en") == "Friday, 10 July 2026"
        assert get_formatted_date("unsupported") == "Friday, 10 July 2026"


def test_time_service_uses_frozen_clock_and_configured_language() -> None:
    with (
        patch("weather_display.services.time_service.datetime", _FrozenDateTime),
        patch("weather_display.services.time_service.config.LANGUAGE", "en"),
        patch("weather_display.utils.localization.datetime", _FrozenDateTime),
    ):
        assert TimeService.get_current_time() == "08:09:10"
        assert TimeService.get_current_date() == "Friday, 10 July 2026"
        assert TimeService.get_current_datetime() == ("08:09:10", "Friday, 10 July 2026")


def test_connection_check_returns_true_for_socket_context_manager() -> None:
    socket_connection = MagicMock()
    with patch(
        "weather_display.utils.helpers.socket.create_connection", return_value=socket_connection
    ) as connect:
        assert check_internet_connection("example.test", 443, timeout=7) is True

    connect.assert_called_once_with(("example.test", 443), timeout=7)


def test_connection_check_returns_false_when_socket_fails() -> None:
    with patch(
        "weather_display.utils.helpers.socket.create_connection", side_effect=OSError("offline")
    ):
        assert check_internet_connection() is False


def test_load_image_returns_none_for_missing_or_corrupt_file() -> None:
    with patch("weather_display.utils.helpers.os.path.exists", return_value=False):
        assert load_image("missing.png") is None

    with (
        patch("weather_display.utils.helpers.os.path.exists", return_value=True),
        patch("weather_display.utils.helpers.Image.open", side_effect=OSError("corrupt")),
    ):
        assert load_image("corrupt.png") is None


def test_load_image_wraps_image_with_requested_size() -> None:
    image = MagicMock(width=20, height=10)
    rendered_image = object()
    with (
        patch("weather_display.utils.helpers.os.path.exists", return_value=True),
        patch("weather_display.utils.helpers.Image.open", return_value=image),
        patch("weather_display.utils.helpers.ctk.CTkImage", return_value=rendered_image) as ctk_image,
    ):
        assert load_image("icon.png", (32, 32)) is rendered_image

    ctk_image.assert_called_once_with(light_image=image, dark_image=image, size=(32, 32))


@pytest.mark.parametrize(
    ("max_temp", "min_temp", "condition", "icon_code"),
    [(30.0, 22.0, "Clear", 1), (None, None, None, None)],
)
def test_forecast_day_to_dict_preserves_all_fields(
    max_temp: float | None,
    min_temp: float | None,
    condition: str | None,
    icon_code: int | None,
) -> None:
    forecast = ForecastDay("2026-07-10", max_temp, min_temp, condition, icon_code)

    assert forecast.to_dict() == {
        "date": "2026-07-10",
        "max_temp": max_temp,
        "min_temp": min_temp,
        "condition": condition,
        "icon_code": icon_code,
    }
