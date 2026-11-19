"""Headless rendering tests for the application window."""

import os
from unittest.mock import Mock, patch

import pytest

from weather_display import config
from weather_display.gui.app_window import AppWindow
from weather_display.utils.localization import get_translation


class _Widget:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self.visible = True

    def grid_remove(self) -> None:
        self.visible = False

    def grid(self) -> None:
        self.visible = True

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
    window.temp_title = _Widget()
    window.humidity_title = _Widget()
    window.temp_value = _Widget()
    window.humidity_value = _Widget()
    window.forecast_day_frames = _forecast_day_frames()
    window._forecast_icon_size = config.FORECAST_ICON_SIZE
    window.icon_handler = Mock()
    window.status_bar_frame = object()
    window.network_status_label = _Widget()
    window.api_status_label = _Widget()
    window._get_color = Mock(side_effect=lambda key: f"{key}-color")
    return window


def test_update_time_and_date_split_values_on_headless_window() -> None:
    window = _window_with_labels()
    window.update_time("08:09:10")
    with patch.object(config, "LANGUAGE", "en"):
        window.update_date("Friday, 04 July 2026")
    assert window.time_label.values["text"] == "08:09"
    assert window.day_label.values["text"] == "4 July"
    assert window.month_year_label.values["text"] == "2026"
    with patch.object(config, "LANGUAGE", "ru"):
        window.update_date("Четверг, 19 Ноября 2026")
    assert window.day_label.values["text"] == "19 ноября"


def test_update_time_and_date_fall_back_to_raw_values_on_malformed_input() -> None:
    window = _window_with_labels()

    window.update_time("not-a-time")
    window.update_date("not a date")

    assert window.time_label.values["text"] == "not-a-time"
    assert window.weekday_label.values["text"] == "not a date"
    assert window.day_label.values["text"] == ""
    assert window.month_year_label.values["text"] == ""


def test_update_current_weather_keeps_existing_values_when_data_is_empty() -> None:
    window = _window_with_labels()
    window.temp_value.configure(text="24°C")
    window.humidity_value.configure(text="60%")

    window.update_current_weather({"data": {}})

    assert window.temp_value.values["text"] == "24°C"
    assert window.humidity_value.values["text"] == "60%"


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


def test_update_forecast_hides_missing_icon_and_restores_valid_icon() -> None:
    window = _window_with_labels()
    window.icon_handler.load_icon.return_value = None

    window.update_forecast({"data": [{"icon_code": 99}]})

    assert not window.forecast_day_frames[0]["icon"].visible
    window.icon_handler.load_icon.return_value = object()
    window.update_forecast({"data": [{"icon_code": 1}]})
    assert window.forecast_day_frames[0]["icon"].visible


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
        assert not forecast_day["icon"].visible
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

    with (
        patch("weather_display.gui.app_window.config.LANGUAGE", "en"),
        patch("weather_display.gui.app_window.datetime") as mock_datetime,
    ):
        mock_datetime.fromtimestamp.return_value.strftime.return_value = "08:09"
        window.update_status_indicators(connection_status, api_status, last_success_time)

    assert window.network_status_label.values["text"] == expected_network
    assert window.api_status_label.values["text"] == expected_api


def test_update_status_indicators_localizes_russian_text() -> None:
    window = _window_with_labels()

    with (
        patch("weather_display.gui.app_window.config.LANGUAGE", "ru"),
        patch("weather_display.gui.app_window.datetime") as mock_datetime,
    ):
        mock_datetime.fromtimestamp.return_value.strftime.return_value = "08:09"
        window.update_status_indicators(False, "error", 1.0)

    assert window.network_status_label.values["text"] == "Сеть: Офлайн"
    assert window.api_status_label.values["text"] == "API: Ошибка (08:09)"


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


def test_stale_readings_are_marked_individually_and_recover() -> None:
    window = _window_with_labels()
    window.status_bar_frame = None
    data = {"temperature": 27, "humidity": 60}
    with patch.object(config, "LANGUAGE", "en"):
        window.update_current_weather({"data": data, "stale": True, "stale_fields": ["humidity"]})
        assert window.temp_title.values["text"] == "Temperature"
        assert "stale" in window.humidity_title.values["text"].lower()
        window.update_current_weather({"data": data, "stale": False})
        assert window.humidity_title.values["text"] == "Humidity"


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="requires an X display")
def test_forecast_and_readings_fit_after_window_resize(monkeypatch) -> None:
    monkeypatch.setattr(config, "FULLSCREEN", False)
    monkeypatch.setattr(config, "LANGUAGE", "ru")
    window = AppWindow()
    try:
        window.overrideredirect(True)
        window.update_time("22:08")
        window.update_date("Понедельник, 28 Сентября 2026")
        window.update_current_weather({"data": {"temperature": -12, "humidity": 100}, "stale": True})
        day = {"date": "2026-11-23", "condition": "Partly cloudy, possible rain", "icon_code": 14,
               "min_temp": -12, "max_temp": 24}
        window.update_forecast({"data": [day] * 3})
        card = window.forecast_day_frames[0]
        for size in ("1440x810", "800x480", "1920x1080"):
            window.geometry(f"{size}+8000+8000")
            window.update()
            header = window.time_date_frame
            forecast = window.forecast_frame
            readings = window.current_conditions_frame
            scale = min(window.winfo_width() / 1440, window.winfo_height() / 810)
            assert card["frame"].winfo_height() >= round(90 * scale)
            assert card["icon"].winfo_height() >= round(82 * scale)
            assert card["day"].winfo_rootx() == card["condition"].winfo_rootx()
            surface = window._enamel
            clock_layers = surface.find_withtag(surface.widget_tag(window.time_label))
            assert len(clock_layers) > 1
            assert surface.itemcget(clock_layers[-1], "text") == "22:08"
            assert surface.itemcget(clock_layers[-1], "fill") == config.ACTIVE_COLORS["accent"]
            for index, forecast_row in enumerate(window.forecast_day_frames):
                assert bool(forecast_row["frame"].grid_slaves(row=0)) == bool(index)
                assert surface.find_withtag(surface.widget_tag(forecast_row["icon"]))
            assert window.time_label.winfo_rootx() + window.time_label.winfo_width() <= window.day_label.winfo_rootx()
            assert header.winfo_rooty() + header.winfo_height() <= forecast.winfo_rooty()
            assert readings.winfo_rootx() + readings.winfo_width() <= forecast.winfo_rootx()
            assert forecast.winfo_rooty() + forecast.winfo_height() <= window.status_bar_frame.winfo_rooty()
            for widget in (window.time_label, window.weekday_label, window.day_label,
                           window.month_year_label, window.temp_title, window.temp_value,
                           window.humidity_title, window.humidity_value,
                           card["day"], card["condition"], card["icon"], card["temp"]):
                label = widget._label
                left, top = label.winfo_rootx(), label.winfo_rooty()
                right, bottom = left + label.winfo_width(), top + label.winfo_height()
                parent = widget
                while parent is not None:
                    x, y = parent.winfo_rootx(), parent.winfo_rooty()
                    left, top = max(left, x), max(top, y)
                    right = min(right, x + parent.winfo_width())
                    bottom = min(bottom, y + parent.winfo_height())
                    parent = parent.master
                assert right - left >= label.winfo_reqwidth(), (size, widget.cget("text"))
                assert bottom - top >= label.winfo_reqheight(), (size, widget.cget("text"))
        window.update_forecast({"data": []})
        window.update()
        assert not card["icon"].winfo_ismapped()
        assert not surface.find_withtag(surface.widget_tag(card["icon"]))
        window.update_forecast({"data": [day]})
        window.update()
        assert card["icon"].winfo_ismapped()
        window.update_status_indicators(False, "offline", None)
        window.update_time("23:41")
        window.update()
        status_face = surface.find_withtag(surface.widget_tag(window.api_status_label))[-1]
        assert surface.itemcget(status_face, "fill") == config.ACTIVE_COLORS["status_error_text"]
        assert surface.itemcget(surface.find_withtag(surface.widget_tag(window.time_label))[-1], "text") == "23:41"
    finally:
        window.destroy()


def test_status_colors_have_readable_contrast_in_light_mode() -> None:
    def luminance(color: str) -> float:
        rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
        return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    background = luminance(config.COLOR_THEME["background"][1])
    for key in ("status_text", "status_ok_text", "status_error_text"):
        foreground = luminance(config.COLOR_THEME[key][1])
        light, dark = max(background, foreground), min(background, foreground)
        assert (light + 0.05) / (dark + 0.05) >= 4.5
