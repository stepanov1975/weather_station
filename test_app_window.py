"""Headless rendering tests for the application window."""

from unittest.mock import Mock, patch

import pytest

from weather_display import config
from weather_display.gui.app_window import AppWindow
from weather_display.utils.localization import get_translation


class _Widget:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def configure(self, **kwargs: object) -> None:
        self.values.update(kwargs)


def _forecast_day_frames() -> list[dict[str, _Widget]]:
    return [
        {
            "frame": _Widget(),
            "day": _Widget(),
            "icon": _Widget(),
            "condition": _Widget(),
            "temp": _Widget(),
        }
        for _ in range(3)
    ]


def _window_with_labels() -> AppWindow:
    window = object.__new__(AppWindow)
    window.time_label = _Widget()
    window.weekday_label = _Widget()
    window.day_label = _Widget()
    window.month_year_label = _Widget()
    window.temp_value = _Widget()
    window.humidity_value = _Widget()
    window.forecast_day_frames = _forecast_day_frames()
    window.icon_handler = Mock()
    window.status_bar_frame = object()
    window.network_status_label = _Widget()
    window.api_status_label = _Widget()
    window._get_color = Mock(side_effect=lambda key: f"{key}-color")
    return window


def test_update_time_and_date_split_values_on_headless_window() -> None:
    window = _window_with_labels()
    window.update_time("08:09:10")
    window.update_date("Friday, 04 July 2026")
    assert window.time_label.values["text"] == "08:09"
    assert window.day_label.values["text"] == "4"


def test_update_time_and_date_fall_back_to_raw_values_on_malformed_input() -> None:
    window = _window_with_labels()

    window.update_time("not-a-time")
    window.update_date("not a date")

    assert window.time_label.values["text"] == "not-a-time"
    assert window.weekday_label.values["text"] == "not a date"
    assert window.day_label.values["text"] == ""
    assert window.month_year_label.values["text"] == ""


def test_update_current_weather_uses_not_available_for_absent_values() -> None:
    window = _window_with_labels()

    window.update_current_weather({"data": {}})

    not_available = get_translation("not_available", config.LANGUAGE)
    assert window.temp_value.values["text"] == not_available
    assert window.humidity_value.values["text"] == not_available


def test_update_forecast_displays_loaded_icon() -> None:
    window = _window_with_labels()
    icon = object()
    window.icon_handler.load_icon.return_value = icon

    with patch("weather_display.gui.app_window.get_day_name", return_value="Saturday"):
        window.update_forecast(
            {
                "data": [
                    {
                        "date": "2026-07-04",
                        "max_temp": 28.2,
                        "min_temp": 19.6,
                        "condition": "Clear",
                        "icon_code": 1,
                    }
                ]
            }
        )

    first_day = window.forecast_day_frames[0]
    assert first_day["day"].values["text"] == "Saturday"
    assert first_day["icon"].values == {"image": icon, "text": ""}
    assert first_day["temp"].values["text"] == "28° / 20°"
    window.icon_handler.load_icon.assert_called_once_with(1, config.FORECAST_ICON_SIZE)


def test_update_forecast_displays_not_available_when_icon_is_missing() -> None:
    window = _window_with_labels()
    window.icon_handler.load_icon.return_value = None

    window.update_forecast({"data": [{"icon_code": 99}]})

    not_available = get_translation("not_available", config.LANGUAGE)
    assert window.forecast_day_frames[0]["icon"].values == {
        "image": None,
        "text": not_available,
    }


@pytest.mark.parametrize(
    ("max_temp", "min_temp", "expected"),
    [
        (28.2, 19.6, "28° / 20°"),
        (28.2, None, "28° / --°"),
        (None, 19.6, "--° / 20°"),
        (None, None, None),
    ],
)
def test_update_forecast_displays_each_temperature_range(
    max_temp: float | None, min_temp: float | None, expected: str | None
) -> None:
    window = _window_with_labels()
    window.icon_handler.load_icon.return_value = object()

    window.update_forecast({"data": [{"max_temp": max_temp, "min_temp": min_temp}]})

    not_available = get_translation("not_available", config.LANGUAGE)
    expected_text = expected if expected is not None else not_available
    assert window.forecast_day_frames[0]["temp"].values["text"] == expected_text


def test_update_forecast_clears_frames_without_forecast_data() -> None:
    window = _window_with_labels()

    window.update_forecast({"data": []})

    not_available = get_translation("not_available", config.LANGUAGE)
    for forecast_day in window.forecast_day_frames:
        assert forecast_day["day"].values["text"] == not_available
        assert forecast_day["icon"].values == {"image": None, "text": ""}
        assert forecast_day["condition"].values["text"] == ""
        assert forecast_day["temp"].values["text"] == ""


@pytest.mark.parametrize(
    (
        "connection_status",
        "api_status",
        "last_success_time",
        "expected_network",
        "expected_api",
    ),
    [
        (True, "ok", 1.0, "Network: OK", "API: OK (08:09)"),
        (False, "error", 1.0, "Network: Offline", "API: Error (08:09)"),
        (True, "mock", 1.0, "Network: OK", "API: Mock"),
        (False, "offline", 1.0, "Network: Offline", "API: Offline (08:09)"),
        (True, None, 1.0, "Network: OK", "API: OK (08:09)"),
        (True, "unknown", 1.0, "Network: OK", "API: unknown (08:09)"),
        (True, "ok", None, "Network: OK", "API: OK"),
        (True, None, None, "Network: OK", "API: Pending"),
    ],
)
def test_update_status_indicators_formats_api_statuses(
    connection_status: bool,
    api_status: str | None,
    last_success_time: float | None,
    expected_network: str,
    expected_api: str,
) -> None:
    window = _window_with_labels()

    with patch("weather_display.gui.app_window.datetime") as mock_datetime:
        mock_datetime.fromtimestamp.return_value.strftime.return_value = "08:09"
        window.update_status_indicators(connection_status, api_status, last_success_time)

    assert window.network_status_label.values["text"] == expected_network
    assert window.api_status_label.values["text"] == expected_api


def test_update_status_indicators_leaves_widgets_unchanged_when_bar_is_disabled() -> None:
    window = _window_with_labels()
    window.status_bar_frame = None

    window.update_status_indicators(True, "ok", 1.0)

    assert window.network_status_label.values == {}
    assert window.api_status_label.values == {}


def test_apply_fullscreen_falls_back_to_screen_geometry() -> None:
    window = object.__new__(AppWindow)
    window.attributes = Mock(side_effect=RuntimeError("unsupported"))
    window.state = Mock()
    window.geometry = Mock()
    window.winfo_screenwidth = Mock(return_value=1920)
    window.winfo_screenheight = Mock(return_value=1080)

    window._apply_fullscreen()

    window.state.assert_called_once_with("normal")
    window.geometry.assert_called_once_with("1920x1080+0+0")


def test_apply_fullscreen_uses_configured_size_when_fallback_fails() -> None:
    window = object.__new__(AppWindow)
    window.attributes = Mock(side_effect=RuntimeError("unsupported"))
    window.state = Mock(side_effect=RuntimeError("unsupported"))
    window.geometry = Mock()
    window.winfo_screenwidth = Mock(return_value=1920)
    window.winfo_screenheight = Mock(return_value=1080)

    window._apply_fullscreen()

    window.geometry.assert_called_once_with(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
