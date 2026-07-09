"""Regression tests for runtime lifecycle and IMS forecast caching."""

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest

from weather_display import config, main as main_module
from weather_display.main import WeatherDisplayApp
from weather_display.services.ims_forecast import IMSCityForecast


class _FakeWindow:
    def __init__(self) -> None:
        self.cancelled: list[str] = []
        self.destroyed = False
        self.status_updates: list[tuple[bool, str | None, float | None]] = []

    def after_cancel(self, job_id: str) -> None:
        self.cancelled.append(job_id)

    def after(self, _delay: int, callback: Any) -> None:
        callback()

    def winfo_exists(self) -> bool:
        return True

    def destroy(self) -> None:
        self.destroyed = True

    def update_status_indicators(
        self,
        connection_status: bool,
        api_status: str | None,
        last_success_time: float | None,
    ) -> None:
        self.status_updates.append((connection_status, api_status, last_success_time))


def test_default_log_file_is_outside_project_tree() -> None:
    assert not config.LOG_FILE_PATH.is_relative_to(config.PROJECT_ROOT)
    assert config.LOG_FILE_PATH.name == "weather_display.log"
    assert config.LOG_FILE_PATH.parent.name == "weather_display"


def test_log_file_respects_xdg_state_home(tmp_path: Path) -> None:
    script = "from weather_display import config; print(config.LOG_FILE_PATH)"

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        env={"XDG_STATE_HOME": str(tmp_path)},
        text=True,
    )

    assert Path(result.stdout.strip()) == tmp_path / "weather_display" / "weather_display.log"


def test_default_forecast_cache_is_outside_project_tree() -> None:
    assert not config.IMS_FORECAST_CACHE_PATH.is_relative_to(config.PROJECT_ROOT)
    assert config.IMS_FORECAST_CACHE_PATH.name == "forecast_cache.json"
    assert config.IMS_FORECAST_CACHE_PATH.parent.name == "weather_display"


def test_forecast_cache_respects_xdg_state_home(tmp_path: Path) -> None:
    script = "from weather_display import config; print(config.IMS_FORECAST_CACHE_PATH)"
    env = os.environ.copy()
    env["XDG_STATE_HOME"] = str(tmp_path)

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert Path(result.stdout.strip()) == (
        tmp_path / "weather_display" / "forecast_cache.json"
    )


def test_signal_shutdown_runs_cleanup_even_when_signal_flips_running() -> None:
    app = object.__new__(WeatherDisplayApp)
    app.running = True
    app.app_window = cast(Any, _FakeWindow())
    app._time_update_job_id = "clock-job"
    app._update_threads = []

    with patch("weather_display.main.time.sleep"), pytest.raises(SystemExit):
        app._handle_signal(15, None)

    assert app.running is False
    assert app._time_update_job_id is None
    assert app.app_window is None


def test_forecast_uses_persistent_cache_when_offline(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"
    payload = _city_payload("2026-07-03")

    client = IMSCityForecast(location_id=18, cache_path=cache_path)
    with patch("weather_display.services.ims_forecast.requests.get") as get:
        get.return_value.status_code = 200
        get.return_value.json.return_value = payload
        get.return_value.raise_for_status.return_value = None

        result = client.fetch_payload(force_refresh=True)

    assert result["api_status"] == "ok"
    assert cache_path.exists()

    offline_client = IMSCityForecast(location_id=18, cache_path=cache_path)
    with patch.object(offline_client, "_request_payload", side_effect=OSError("offline")):
        offline_result = offline_client.fetch_payload(force_refresh=True)

    assert offline_result["api_status"] == "offline"
    assert offline_result["cache_hit"] is True
    assert offline_result["data"] == payload

    cached_json = json.loads(cache_path.read_text(encoding="utf-8"))
    assert cached_json["payload"]["data"]["title"] == "Hadera"


def test_valid_forecast_cache_does_not_report_fresh_startup_offline(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"
    payload = _city_payload("2026-07-03")
    cache_data = {"timestamp": 9999999999.0, "payload": payload}
    cache_path.write_text(json.dumps(cache_data), encoding="utf-8")

    client = IMSCityForecast(location_id=18, cache_path=cache_path)
    result = client.fetch_payload(force_refresh=False)

    assert result["cache_hit"] is True
    assert result["api_status"] == "ok"
    assert result["connection_status"] is None


def test_forecast_fetch_reports_ok_when_cache_write_fails(tmp_path: Path) -> None:
    cache_path = tmp_path / "missing" / "forecast.json"
    payload = _city_payload("2026-07-03")

    client = IMSCityForecast(location_id=18, cache_path=cache_path)
    with (
        patch.object(client, "_request_payload", return_value=payload),
        patch.object(client.cache, "store", side_effect=OSError("read only")),
    ):
        result = client.fetch_payload(force_refresh=True)

    assert result["data"] == payload
    assert result["api_status"] == "ok"
    assert result["connection_status"] is True
    assert result["cache_hit"] is False


def test_forecast_accepts_string_cache_path(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"

    client = IMSCityForecast(location_id=18, cache_path=str(cache_path))

    assert client.cache.path == cache_path


def test_main_starts_app_when_network_is_unavailable() -> None:
    fake_app = SimpleNamespace(running=False, start=lambda: None, stop=lambda: None)
    args = SimpleNamespace(mock=False, windowed=False, headless=True)

    with (
        patch.object(main_module, "parse_arguments", return_value=args),
        patch.object(main_module.config, "USE_MOCK_DATA", False),
        patch.object(main_module, "check_internet_connection", return_value=False),
        patch.object(main_module, "WeatherDisplayApp", return_value=fake_app) as app_class,
    ):
        main_module.main()

    app_class.assert_called_once_with(headless=True)


def test_headless_start_fetches_initial_data_before_sleeping() -> None:
    app = object.__new__(WeatherDisplayApp)
    app.running = False
    app.headless = True
    app.app_window = None
    app.ims_weather = cast(Any, object())
    app.ims_forecast = cast(Any, object())
    app._update_threads = []

    calls: list[str] = []

    def stop_after_initial_sleep(_seconds: float) -> None:
        calls.append("sleep")
        app.running = False

    with (
        patch.object(app, "_start_update_threads", side_effect=lambda: calls.append("threads")),
        patch.object(app, "_update_weather", side_effect=lambda: calls.append("weather")),
        patch.object(app, "_initial_forecast_update", side_effect=lambda: calls.append("forecast")),
        patch("weather_display.main.signal.signal"),
        patch("weather_display.main.time.sleep", side_effect=stop_after_initial_sleep),
    ):
        app.start()

    assert calls[:3] == ["threads", "weather", "forecast"]
    assert "sleep" in calls


def test_weather_update_exception_updates_status_with_required_arguments() -> None:
    app = object.__new__(WeatherDisplayApp)
    app.ims_weather = cast(Any, SimpleNamespace(fetch_data=lambda: (_ for _ in ()).throw(RuntimeError("boom"))))
    fake_window = _FakeWindow()
    app.app_window = cast(Any, fake_window)
    app.headless = False
    app.last_connection_status = True

    app._update_weather()

    assert fake_window.status_updates == [(False, "error", None)]
    assert app.last_connection_status is False


def _city_payload(date: str) -> dict[str, Any]:
    return {
        "data": {
            "title": "Hadera",
            "analysis": {
                "temperature": "26",
                "relative_humidity": "70",
                "weather_code": "1230",
                "forecast_time": f"{date} 12:00:00",
            },
            "weather_codes": {
                "1230": {"desc_en": "Cloudy", "desc": "Cloudy"},
            },
            "forecast_data": {
                date: {
                    "daily": {
                        "forecast_date": date,
                        "maximum_temperature": "30",
                        "minimum_temperature": "23",
                        "weather_code": "1230",
                    }
                }
            },
        }
    }
