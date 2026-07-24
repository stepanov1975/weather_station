"""Headless behavior tests for controller, GUI fallbacks, and IMS XML edges."""

import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import pytest
import requests

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
    app._stop_event = threading.Event()
    app._current_update_lock = threading.Lock()
    app._forecast_update_lock = threading.Lock()
    app._connection_status_initialized = True
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
        {
            "data": {"temperature": 27.6, "humidity": 61},
            "connection_status": True,
            "api_status": "ok",
            "stale": False,
        }
    ]
    assert app.app_window.statuses[-1][:2] == (True, "ok")


def test_controller_keeps_last_current_weather_after_fetch_failure() -> None:
    app = _headless_controller()
    app.ims_weather = SimpleNamespace(
        fetch_data=Mock(side_effect=[True, False]),
        get_all_measurements=Mock(
            return_value={"TD": {"value": "27.6"}, "RH": {"value": "61"}}
        ),
    )

    with patch("weather_display.main.config.USE_MOCK_DATA", False):
        app._update_weather()
        app._update_weather()

    assert app.app_window.weather[-1] == {
        "data": {"temperature": 27.6, "humidity": 61},
        "connection_status": False,
        "api_status": "error",
        "stale": True,
    }


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
    with (
        patch("weather_display.gui.app_window.config.LANGUAGE", "en"),
        patch("weather_display.gui.app_window.datetime") as mock_datetime,
    ):
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
            return_value={
                "api_status": "ok",
                "connection_status": True,
                "cache_hit": True,
                "cache_timestamp": 456.0,
                "data": [],
            }
        )
    )
    app._update_forecast_data(force_refresh=False)
    assert app.last_forecast_success_time == 456.0

    app.ims_forecast.get_forecast.side_effect = RuntimeError("offline")
    app._update_forecast_data()
    assert app._forecast_api_status == "error"


def test_controller_sleep_and_status_validation_cover_stop_boundaries() -> None:
    app = _headless_controller()
    app.running = True
    assert app._sleep_until_stop(0) is True

    app._stop_event.set()
    with patch("weather_display.main.time.sleep", side_effect=AssertionError("polling sleep used")):
        assert app._sleep_until_stop(60) is False
    with pytest.raises(ValueError, match="Unknown API"):
        app._record_api_status("other", "ok")


def test_parse_arguments_reads_the_supported_cli_flags() -> None:
    with patch("weather_display.main.sys.argv", ["weather", "--mock", "--windowed", "--headless"]):
        args = main_module.parse_arguments()

    assert (args.mock, args.windowed, args.headless) == (True, True, True)


def test_controller_stop_cancels_updates_joins_threads_and_destroys_window() -> None:
    class JoinedThread:
        name = "weather"

        def __init__(self) -> None:
            self.joined = False

        def is_alive(self) -> bool:
            return not self.joined

        def join(self, timeout: float) -> None:
            assert timeout == 2.0
            self.joined = True

    app = _headless_controller()
    thread = JoinedThread()
    app._stop_lock = threading.Lock()
    app._time_update_job_id = "time-update"
    app._update_threads = [thread]
    app.app_window = Mock()
    app.app_window.winfo_exists.return_value = True
    window = app.app_window

    app.stop()

    assert app._stop_event.is_set()
    window.after_cancel.assert_called_once_with("time-update")
    assert thread.joined is True
    window.destroy.assert_called_once_with()
    assert app.app_window is None


def test_controller_stop_without_work_returns_without_sleeping() -> None:
    app = _headless_controller()
    app.running = False
    app._time_update_job_id = None
    app._update_threads = []
    app.app_window = None

    with patch("weather_display.main.time.sleep") as sleep:
        app.stop()

    sleep.assert_not_called()


def test_controller_shutdown_logs_widget_and_thread_failures_without_raising() -> None:
    app = _headless_controller()
    app._time_update_job_id = "time-update"
    app.app_window = Mock()
    app.app_window.after_cancel.side_effect = RuntimeError("cancel failed")

    failing_thread = Mock()
    failing_thread.name = "failing"
    failing_thread.is_alive.return_value = True
    failing_thread.join.side_effect = RuntimeError("join failed")
    app._update_threads = [failing_thread]

    app._cancel_time_update()
    app._join_update_threads()

    app.app_window.winfo_exists.side_effect = RuntimeError("window failed")
    app._destroy_window()

    assert app._update_threads == []
    assert app.app_window is not None


def test_controller_start_schedules_gui_initial_updates_without_fetching_inline() -> None:
    app = _headless_controller()
    app.running = False
    app.ims_weather = object()
    app.ims_forecast = object()
    app.app_window.mainloop = Mock()
    app._start_update_threads = Mock()
    app._update_time_and_date = Mock()
    app._update_weather = Mock()
    app._initial_forecast_update = Mock()
    app._start_one_off_update = Mock()
    app.stop = Mock()

    with patch("weather_display.main.signal.signal") as register_signal:
        app.start()

    app._start_update_threads.assert_called_once_with()
    app._update_time_and_date.assert_called_once_with()
    app._update_weather.assert_not_called()
    app._initial_forecast_update.assert_not_called()
    assert app._start_one_off_update.call_args_list == [
        call(app._update_weather, "IMSInitialUpdate"),
        call(app._initial_forecast_update, "IMSForecastInitialUpdate"),
    ]
    assert register_signal.call_count == 2
    app.app_window.mainloop.assert_called_once_with()
    app.stop.assert_called_once_with()


def test_controller_start_headlessly_launches_initial_updates_in_workers() -> None:
    app = _headless_controller()
    app.headless = True
    app.app_window = None
    app.running = False
    app.ims_weather = object()
    app.ims_forecast = object()
    app._start_update_threads = Mock()
    app._update_weather = Mock()
    app._initial_forecast_update = Mock()
    app._start_one_off_update = Mock()
    app._sleep_until_stop = Mock(side_effect=lambda _seconds: False)

    with (
        patch("weather_display.main.signal.signal") as register_signal,
        patch("weather_display.main.time.sleep", side_effect=lambda _seconds: setattr(app, "running", False)),
    ):
        app.start()

    assert register_signal.call_count == 2
    app._update_weather.assert_not_called()
    app._initial_forecast_update.assert_not_called()
    assert app._start_one_off_update.call_count == 2


def test_controller_start_stops_invalid_non_gui_non_headless_state() -> None:
    app = _headless_controller()
    app.running = False
    app.app_window = None
    app.headless = False
    app._start_update_threads = Mock()
    app.stop = Mock()

    app.start()

    app.stop.assert_called_once_with()


def test_controller_connection_monitor_recovers_after_a_check_error() -> None:
    app = _headless_controller()
    app._sleep_until_stop = Mock(side_effect=lambda _seconds: setattr(app, "running", False))

    with patch("weather_display.main.check_internet_connection", side_effect=RuntimeError("network")):
        app._connection_monitoring_loop()

    app._sleep_until_stop.assert_called_once_with(30)


def test_controller_first_connection_check_does_not_duplicate_initial_updates() -> None:
    app = _headless_controller()
    app.last_connection_status = False
    app._connection_status_initialized = False
    app.ims_weather = None
    app.ims_forecast = None
    app._start_one_off_update = Mock()

    def stop_after_check(_seconds: int) -> bool:
        app.running = False
        return False

    app._sleep_until_stop = Mock(side_effect=stop_after_check)

    with patch("weather_display.main.check_internet_connection", return_value=True):
        app._connection_monitoring_loop()

    assert app.last_connection_status is True
    app._start_one_off_update.assert_not_called()


def test_controller_skips_overlapping_source_updates() -> None:
    app = _headless_controller()
    app.ims_weather = SimpleNamespace(fetch_data=Mock())
    app.ims_forecast = SimpleNamespace(get_forecast=Mock())

    app._current_update_lock.acquire()
    app._forecast_update_lock.acquire()
    try:
        app._update_weather()
        app._update_forecast_data()
    finally:
        app._current_update_lock.release()
        app._forecast_update_lock.release()

    app.ims_weather.fetch_data.assert_not_called()
    app.ims_forecast.get_forecast.assert_not_called()


def test_controller_starts_only_connection_monitor_when_ims_clients_are_unavailable() -> None:
    class FakeThread:
        def __init__(self, target: object, name: str, daemon: bool) -> None:
            self.target = target
            self.name = name
            self.daemon = daemon
            self.started = False

        def start(self) -> None:
            self.started = True

    app = _headless_controller()
    app.ims_weather = None
    app.ims_forecast = None
    with patch("weather_display.main.threading.Thread", FakeThread):
        app._start_update_threads()

    assert [thread.name for thread in app._update_threads] == ["ConnectionMonitorThread"]
    assert app._update_threads[0].started is True


def test_controller_starts_one_off_update_in_a_daemon_thread() -> None:
    thread = Mock()
    app = _headless_controller()

    with patch("weather_display.main.threading.Thread", return_value=thread) as thread_type:
        app._start_one_off_update(app._update_weather, "manual-refresh")

    thread_type.assert_called_once_with(target=app._update_weather, name="manual-refresh", daemon=True)
    thread.start.assert_called_once_with()
    assert app._update_threads == [thread]


def test_controller_destroy_window_leaves_nonexistent_window_intact() -> None:
    app = _headless_controller()
    window = Mock()
    window.winfo_exists.return_value = False
    app.app_window = window

    app._destroy_window()

    window.destroy.assert_not_called()
    assert app.app_window is None


@pytest.mark.parametrize(
    ("measurements", "expected_data"),
    [
        (None, {}),
        ({"TD": {"value": "21.5"}, "RH": {"value": "40"}}, {"temperature": 21.5, "humidity": 40}),
    ],
)
def test_controller_weather_fetch_handles_empty_and_complete_measurements(
    measurements: dict[str, dict[str, str]] | None, expected_data: dict[str, object]
) -> None:
    app = _headless_controller()
    app.ims_weather = SimpleNamespace(fetch_data=Mock(return_value=True), get_all_measurements=Mock(return_value=measurements))

    with patch("weather_display.main.config.USE_MOCK_DATA", False):
        app._update_weather()

    assert app.app_window.weather[-1]["data"] == expected_data
    assert app._current_api_status == ("ok" if measurements else "error")


def test_ims_fetch_returns_false_for_network_and_xml_parse_errors() -> None:
    weather = IMSLastHourWeather("En Hahoresh")

    with patch(
        "weather_display.services.ims_lasthour.requests.get",
        side_effect=requests.exceptions.ConnectionError("offline"),
    ):
        assert weather.fetch_data() is False

    response = SimpleNamespace(content=b"<ims>", raise_for_status=Mock())
    with patch("weather_display.services.ims_lasthour.requests.get", return_value=response):
        assert weather.fetch_data() is False


def test_ims_fetch_parses_hebrew_names_and_prefers_exact_station_match(tmp_path: Path) -> None:
    xml_path = tmp_path / "ims.xml"
    xml_path.write_text(
        """<ims><HebrewVariablesNames><TD>Temperature</TD></HebrewVariablesNames>
        <Observation><stn_name>En Hahoresh North</stn_name><TD>25</TD></Observation>
        <Observation><stn_name>En Hahoresh</stn_name><stn_num>123</stn_num>
        <time_obs>2026-07-10T08:09:10</time_obs><TD>26</TD></Observation></ims>""",
        encoding="utf-8",
    )
    weather = IMSLastHourWeather("En Hahoresh")

    assert weather.fetch_data(use_local_file=True, local_file_path=str(xml_path)) is True
    assert weather.get_metadata() == {"StationName": "En Hahoresh", "StationNumber": "123"}
    assert weather.get_measurement("TD") == {"value": "26", "description": "Temperature"}
    assert weather.get_hebrew_variables() == {"TD": "Temperature"}


def test_ims_accessors_return_none_before_data_is_fetched() -> None:
    weather = IMSLastHourWeather("En Hahoresh")

    assert weather.get_all_data() is None
    assert weather.get_metadata() is None
    assert weather.get_measurement("TD") is None
    assert weather.get_all_measurements() is None
    assert weather.get_observation_time() is None


def test_ims_list_all_stations_keeps_first_duplicate_and_skips_blank_names(tmp_path: Path) -> None:
    xml_path = tmp_path / "stations.xml"
    xml_path.write_text(
        """<ims><Observation><stn_name> Alpha </stn_name><stn_num>1</stn_num></Observation>
        <Observation><stn_name>Alpha</stn_name><stn_num>99</stn_num></Observation>
        <Observation><stn_name> </stn_name></Observation>
        <Observation><stn_name>Beta</stn_name></Observation></ims>""",
        encoding="utf-8",
    )

    assert IMSLastHourWeather.list_all_stations(use_local_file=True, local_file_path=str(xml_path)) == {
        "Alpha": {"StationNumber": "1"},
        "Beta": {},
    }


def test_ims_list_all_stations_returns_empty_for_network_and_xml_parse_errors() -> None:
    with patch(
        "weather_display.services.ims_lasthour.requests.get",
        side_effect=requests.exceptions.ConnectionError("offline"),
    ):
        assert IMSLastHourWeather.list_all_stations() == {}

    response = SimpleNamespace(content=b"<ims>", raise_for_status=Mock())
    with patch("weather_display.services.ims_lasthour.requests.get", return_value=response):
        assert IMSLastHourWeather.list_all_stations() == {}
