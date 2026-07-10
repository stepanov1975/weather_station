"""Headless behavior tests for controller, GUI fallbacks, and IMS XML edges."""

import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from weather_display import main as main_module
from weather_display.gui.app_window import AppWindow
from weather_display.services.ims_lasthour import IMSLastHourWeather


class _RecordingWindow:
    def __init__(self) -> None:
        self.weather: list[dict[str, object]] = []
        self.forecasts: list[dict[str, object]] = []
        self.statuses: list[tuple[bool, str | None, float | None]] = []

    def after(self, _delay: int, callback: object) -> str:
        callback()  # type: ignore[operator]
        return "scheduled"

    def update_current_weather(self, value: dict[str, object]) -> None:
        self.weather.append(value)

    def update_forecast(self, value: dict[str, object]) -> None:
        self.forecasts.append(value)

    def update_status_indicators(
        self, connected: bool, status: str | None, updated: float | None
    ) -> None:
        self.statuses.append((connected, status, updated))


def _headless_controller() -> main_module.WeatherDisplayApp:
    app = object.__new__(main_module.WeatherDisplayApp)
    app.headless = False
    app.running = True
    app._update_threads = []
    app._time_update_job_id = None
    app._status_lock = threading.Lock()
    app._current_api_status = None
    app._forecast_api_status = None
    app.last_connection_status = True
    app.last_forecast_success_time = None
    app.app_window = _RecordingWindow()
    return app


def test_controller_updates_gui_from_successful_current_weather_fetch() -> None:
    app = _headless_controller()
    app.ims_weather = SimpleNamespace(
        fetch_data=Mock(return_value=True),
        get_all_measurements=Mock(
            return_value={"TD": {"value": "27.6"}, "RH": {"value": "61"}}
        ),
    )

    with patch("weather_display.main.config.USE_MOCK_DATA", False):
        app._update_weather()

    assert app.app_window.weather == [
        {"data": {"temperature": 27.6, "humidity": 61}, "connection_status": True, "api_status": "ok"}
    ]
    assert app.app_window.statuses[-1][:2] == (True, "ok")


@pytest.mark.parametrize(
    ("api_status", "cache_hit", "expected_status", "sets_timestamp"),
    [
        ("ok", False, "ok", True),
        ("mock", False, "mock", False),
        ("offline", False, "offline", False),
        ("error", False, "error", False),
    ],
)
def test_controller_publishes_each_forecast_result_status(
    api_status: str, cache_hit: bool, expected_status: str, sets_timestamp: bool
) -> None:
    app = _headless_controller()
    app.ims_forecast = SimpleNamespace(
        get_forecast=Mock(
            return_value={
                "api_status": api_status,
                "connection_status": api_status != "offline",
                "cache_hit": cache_hit,
                "data": [{"date": "2026-07-10"}],
            }
        )
    )

    with patch("weather_display.main.time.time", return_value=123.0):
        app._update_forecast_data()

    assert app._forecast_api_status == expected_status
    assert app.app_window.forecasts[0]["api_status"] == api_status
    assert (app.last_forecast_success_time == 123.0) is sets_timestamp


def test_controller_skips_updates_without_initialized_clients() -> None:
    app = _headless_controller()
    app.ims_weather = None
    app.ims_forecast = None

    app._update_weather()
    app._update_forecast_data()

    assert app.app_window.weather == []
    assert app.app_window.forecasts == []


def test_weather_display_app_initializes_headlessly_without_gui() -> None:
    weather_client = object()
    forecast_client = object()
    with (
        patch("weather_display.main.IMSLastHourWeather", return_value=weather_client),
        patch("weather_display.main.IMSCityForecast", return_value=forecast_client),
        patch("weather_display.main.check_internet_connection", return_value=False),
    ):
        app = main_module.WeatherDisplayApp(headless=True)

    assert app.app_window is None
    assert app.ims_weather is weather_client
    assert app.ims_forecast is forecast_client
    assert app.last_connection_status is False


def test_main_applies_cli_overrides_and_starts_headless_app() -> None:
    app = Mock(running=False)
    args = SimpleNamespace(mock=True, windowed=True, headless=True)
    with (
        patch("weather_display.main.configure_logging", return_value=True),
        patch("weather_display.main.parse_arguments", return_value=args),
        patch("weather_display.main.WeatherDisplayApp", return_value=app) as app_type,
        patch("weather_display.main.config.USE_MOCK_DATA", False),
        patch("weather_display.main.config.FULLSCREEN", True),
    ):
        main_module.main()

    app_type.assert_called_once_with(headless=True)
    app.start.assert_called_once_with()


def test_ims_fetch_handles_missing_local_file_and_invalid_station_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        IMSLastHourWeather("")

    weather = IMSLastHourWeather("En Hahoresh")
    assert weather.fetch_data(use_local_file=True, local_file_path=str(tmp_path / "missing.xml")) is False


def test_ims_parses_partial_station_and_invalid_timestamp_from_local_xml(tmp_path: Path) -> None:
    xml_path = tmp_path / "ims.xml"
    xml_path.write_text(
        """<ims><Observation><stn_name>En Hahoresh North</stn_name><TD>  </TD>
        <RH>55</RH><time_obs>invalid</time_obs></Observation></ims>""",
        encoding="utf-8",
    )
    weather = IMSLastHourWeather("Hahoresh")

    assert weather.fetch_data(use_local_file=True, local_file_path=str(xml_path)) is True
    assert weather.get_measurement("RH") == {"value": "55", "description": "N/A"}
    assert weather.get_measurement("TD") is None
    assert "Conversion_Error" in weather.get_observation_time()


def test_ims_time_conversion_constructs_components_and_returns_errors() -> None:
    weather = IMSLastHourWeather("En Hahoresh")

    converted = weather._convert_to_israel_time(
        {"Year": "2026", "Month": "07", "Day": "10", "Hour": "08", "Minute": "09", "Second": "10"}
    )
    failed = weather._convert_to_israel_time({"Year": "0"})

    assert converted["Hour"] == "11"
    assert "Conversion_Error" in failed


def test_ims_accessors_fall_back_to_utc_time_when_converted_time_is_absent() -> None:
    weather = IMSLastHourWeather("En Hahoresh")
    weather.data = {"metadata": {}, "measurements": {}, "time": {"raw": "2026-07-10T08:00:00"}}

    assert weather.get_metadata() == {}
    assert weather.get_all_measurements() == {}
    assert weather.get_observation_time() == {"raw": "2026-07-10T08:00:00"}
    assert weather.get_observation_time(israel_time=False) == {"raw": "2026-07-10T08:00:00"}


def test_list_all_stations_returns_empty_for_missing_local_file(tmp_path: Path) -> None:
    assert IMSLastHourWeather.list_all_stations(
        use_local_file=True, local_file_path=str(tmp_path / "missing.xml")
    ) == {}


def test_window_reports_widget_and_timestamp_errors_without_gui() -> None:
    class FailingOnceWidget:
        def __init__(self) -> None:
            self.calls = 0

        def configure(self, **_kwargs: object) -> None:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("widget failure")

    window = object.__new__(AppWindow)
    window.time_label = FailingOnceWidget()
    window.weekday_label = FailingOnceWidget()
    window.day_label = Mock()
    window.month_year_label = Mock()
    window.status_bar_frame = object()
    window.network_status_label = Mock()
    window.api_status_label = Mock()
    window._get_color = Mock(return_value="color")

    window.update_time("08:09")
    window.update_date("Friday, 10 July 2026")
    with patch("weather_display.gui.app_window.datetime") as mock_datetime:
        mock_datetime.fromtimestamp.side_effect = ValueError("bad")
        window.update_status_indicators(True, "error", 1.0)

    assert window.api_status_label.configure.call_args.kwargs["text"] == "API: Error (??:??)"


def test_exit_fullscreen_invokes_window_operations_headlessly() -> None:
    window = object.__new__(AppWindow)
    window.attributes = Mock()
    window.overrideredirect = Mock()
    window.state = Mock()

    window.exit_fullscreen()

    window.attributes.assert_called_once_with("-fullscreen", False)
    window.overrideredirect.assert_called_once_with(False)
    window.state.assert_called_once_with("normal")


def test_app_window_builds_its_widget_tree_with_headless_toolkit() -> None:
    class Widget:
        def grid(self, **_kwargs: object) -> None:
            pass

        def pack(self, **_kwargs: object) -> None:
            pass

        def configure(self, **_kwargs: object) -> None:
            pass

        def grid_columnconfigure(self, *_args: object, **_kwargs: object) -> None:
            pass

        def grid_rowconfigure(self, *_args: object, **_kwargs: object) -> None:
            pass

        def grid_propagate(self, *_args: object, **_kwargs: object) -> None:
            pass

    with (
        patch("weather_display.gui.app_window.ctk.CTk.__init__", return_value=None),
        patch("weather_display.gui.app_window.ctk.CTk.title"),
        patch("weather_display.gui.app_window.ctk.CTk.geometry"),
        patch("weather_display.gui.app_window.ctk.CTk.configure"),
        patch("weather_display.gui.app_window.ctk.CTk.bind"),
        patch("weather_display.gui.app_window.ctk.CTk.grid_columnconfigure"),
        patch("weather_display.gui.app_window.ctk.CTk.grid_rowconfigure"),
        patch("weather_display.gui.app_window.ctk.CTkFrame", side_effect=lambda *_args, **_kwargs: Widget()),
        patch("weather_display.gui.app_window.ctk.CTkLabel", side_effect=lambda *_args, **_kwargs: Widget()),
        patch("weather_display.gui.app_window.ctk.CTkFont", return_value=object()),
    ):
        window = AppWindow()

    assert len(window.forecast_day_frames) == 3
    assert window.status_bar_frame is not None
    assert window.humidity_value is not None


def test_configure_logging_creates_the_configured_log_file(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "weather.log"
    with patch("weather_display.main.config.LOG_FILE_PATH", log_path):
        assert main_module.configure_logging() is True

    assert log_path.parent.exists()


def test_controller_starts_threads_and_runs_each_periodic_loop_once() -> None:
    class FakeThread:
        def __init__(self, target: object, name: str, daemon: bool) -> None:
            self.target = target
            self.name = name
            self.daemon = daemon
            self.started = False

        def start(self) -> None:
            self.started = True

    app = _headless_controller()
    app.ims_weather = object()
    app.ims_forecast = object()
    with patch("weather_display.main.threading.Thread", FakeThread):
        app._start_update_threads()

    assert [thread.name for thread in app._update_threads] == [
        "IMSWeatherUpdateThread",
        "IMSForecastUpdateThread",
        "ConnectionMonitorThread",
    ]
    assert all(thread.started for thread in app._update_threads)

    app._update_weather = Mock()
    app._sleep_until_stop = Mock(side_effect=[True, False])
    app._weather_update_loop()
    app._update_weather.assert_called_once_with()

    app._update_forecast_data = Mock()
    app._sleep_until_stop = Mock(side_effect=[True, False])
    app._forecast_update_loop()
    app._update_forecast_data.assert_called_once_with()


def test_controller_connection_monitor_triggers_refresh_after_reconnection() -> None:
    app = _headless_controller()
    app.headless = True
    app.last_connection_status = False
    app.ims_weather = object()
    app.ims_forecast = object()
    app._start_one_off_update = Mock()
    app._schedule_status_update = Mock()

    def stop_after_wait(_seconds: int) -> bool:
        app.running = False
        return False

    app._sleep_until_stop = Mock(side_effect=stop_after_wait)
    with patch("weather_display.main.check_internet_connection", return_value=True):
        app._connection_monitoring_loop()

    assert app.last_connection_status is True
    assert app._start_one_off_update.call_count == 2
    app._schedule_status_update.assert_called_once_with()


def test_controller_time_updates_skip_stopped_app_and_reschedule_failures() -> None:
    app = _headless_controller()
    app.running = False
    app.time_service = Mock()
    app._update_time_and_date()
    app.time_service.get_current_datetime.assert_not_called()

    app.running = True
    app.time_service.get_current_datetime.side_effect = RuntimeError("clock")
    app.app_window.after = Mock(return_value="scheduled")
    app._update_time_and_date()
    assert app._time_update_job_id == "scheduled"


def test_controller_uses_mock_weather_and_records_update_exceptions() -> None:
    app = _headless_controller()
    app.ims_weather = SimpleNamespace(fetch_data=Mock(side_effect=RuntimeError("bad")))
    with patch("weather_display.main.config.USE_MOCK_DATA", True):
        app._update_weather()

    assert app.app_window.weather[0]["api_status"] == "mock"
    assert app._current_api_status == "mock"

    with patch("weather_display.main.config.USE_MOCK_DATA", False):
        app._update_weather()
    assert app._current_api_status == "error"


def test_controller_forecast_handles_headless_cache_and_errors() -> None:
    app = _headless_controller()
    app.app_window = None
    app.headless = True
    app.ims_forecast = SimpleNamespace(
        get_forecast=Mock(
            return_value={"api_status": "ok", "connection_status": True, "cache_hit": True, "data": []}
        )
    )
    app._update_forecast_data(force_refresh=False)
    assert app.last_forecast_success_time is None

    app.ims_forecast.get_forecast.side_effect = RuntimeError("offline")
    app._update_forecast_data()
    assert app._forecast_api_status == "error"


def test_controller_sleep_and_status_validation_cover_stop_boundaries() -> None:
    app = _headless_controller()
    app.running = True
    with patch("weather_display.main.time.sleep") as sleep:
        assert app._sleep_until_stop(2) is True
    assert sleep.call_count == 2

    app.running = False
    assert app._sleep_until_stop(1) is False
    with pytest.raises(ValueError, match="Unknown API"):
        app._record_api_status("other", "ok")


def test_parse_arguments_reads_the_supported_cli_flags() -> None:
    with patch("weather_display.main.sys.argv", ["weather", "--mock", "--windowed", "--headless"]):
        args = main_module.parse_arguments()

    assert (args.mock, args.windowed, args.headless) == (True, True, True)
