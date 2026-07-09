# Runtime State and Refactor Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct cache, connectivity, status, logging, and socket behavior while removing the confirmed leftovers from the IMS-only refactor.

**Architecture:** The connection monitor becomes the sole owner of network state, while current-observation and forecast API states are recorded separately and combined for the existing status label. Generated forecast data moves to the XDG state directory, and process-wide side effects are moved behind explicit function calls.

**Tech Stack:** Python 3.10+, pytest, unittest.mock, CustomTkinter, requests, Ruff, mypy

## Global Constraints

- Use `./weather_venv/bin/python` for every Python tool invocation.
- Use pytest for tests, Ruff for linting, and mypy for type checking.
- Preserve the existing GUI layout and standalone IMS station-listing command.
- Do not reintroduce API-key arguments or AccuWeather behavior.
- Keep edits surgical; trim only stale comments adjacent to changed code.
- Do not commit logs, caches, or `__pycache__` files.

---

### Task 1: Move and Correct the Forecast Cache

**Files:**
- Modify: `weather_display/config.py:11-14`
- Modify: `weather_display/services/ims_forecast.py:45-105`
- Test: `test_runtime_refactor.py:45-119`

**Interfaces:**
- Consumes: `XDG_STATE_HOME`, `JsonCache`, `IMSCityForecast.fetch_payload(force_refresh: bool)`.
- Produces: `config.APP_STATE_DIR: Path`, a writable `config.IMS_FORECAST_CACHE_PATH`, and cache-hit results whose `connection_status` is `None`.

- [ ] **Step 1: Write failing cache-location and cache-connectivity tests**

Add these tests to `test_runtime_refactor.py`, and change the existing valid-cache assertion from `True` to `None`:

```python
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
```

Update the existing assertion:

```python
assert result["connection_status"] is None
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
./weather_venv/bin/python -m pytest \
  test_runtime_refactor.py::test_default_forecast_cache_is_outside_project_tree \
  test_runtime_refactor.py::test_forecast_cache_respects_xdg_state_home \
  test_runtime_refactor.py::test_valid_forecast_cache_does_not_report_fresh_startup_offline -v
```

Expected: the path tests fail because the cache is under `PROJECT_ROOT`, and the cache-connectivity assertion fails because the result is `True`.

- [ ] **Step 3: Implement the XDG path and unknown cached connectivity**

Replace the path definitions in `config.py` with:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
USER_STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
APP_STATE_DIR = USER_STATE_DIR / "weather_display"
LOG_FILE_PATH = APP_STATE_DIR / "weather_display.log"
IMS_FORECAST_CACHE_PATH = APP_STATE_DIR / "forecast_cache.json"
```

In `IMSCityForecast`, type `_connection_status` and its property as `bool | None`, and make the valid-cache branch return unknown connectivity:

```python
self._connection_status: bool | None = False

@property
def connection_status(self) -> bool | None:
    return self._connection_status

# valid cache branch
self._connection_status = None
return {
    "data": self.cache.payload,
    "connection_status": None,
    "api_status": "ok",
    "cache_hit": True,
}
```

- [ ] **Step 4: Run the focused cache tests and verify GREEN**

Run the command from Step 2.

Expected: all three tests pass.

- [ ] **Step 5: Commit the cache behavior**

```bash
git add weather_display/config.py weather_display/services/ims_forecast.py test_runtime_refactor.py
git commit -m "fix: store forecast cache in user state"
```

---

### Task 2: Isolate Logging and Socket Side Effects

**Files:**
- Modify: `weather_display/main.py:67-111,800-815`
- Modify: `weather_display/utils/helpers.py:35-69`
- Test: `test_runtime_refactor.py`

**Interfaces:**
- Consumes: `config.LOG_FILE_PATH`, `logging.handlers.TimedRotatingFileHandler`, `socket.create_connection`.
- Produces: `configure_logging() -> bool`; importing `weather_display.main` has no logging side effects; `check_internet_connection(...)` preserves the process-wide socket default.

- [ ] **Step 1: Write failing regression tests for both side effects**

Add imports and tests to `test_runtime_refactor.py`:

```python
import logging
import os
import socket

from weather_display.utils.helpers import check_internet_connection


def test_importing_main_preserves_root_logging_configuration(tmp_path: Path) -> None:
    script = """
import logging
marker = logging.NullHandler()
root = logging.getLogger()
root.handlers = [marker]
import weather_display.main
print(marker in root.handlers)
"""
    env = os.environ.copy()
    env["XDG_STATE_HOME"] = str(tmp_path)

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.stdout.splitlines()[-1] == "True"
    assert not (tmp_path / "weather_display" / "weather_display.log").exists()


def test_connection_check_does_not_change_default_socket_timeout() -> None:
    original_timeout = socket.getdefaulttimeout()

    with patch("weather_display.utils.helpers.socket.create_connection") as connect:
        assert check_internet_connection("example.test", 443, timeout=7)

    connect.assert_called_once_with(("example.test", 443), timeout=7)
    assert socket.getdefaulttimeout() == original_timeout
```

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
./weather_venv/bin/python -m pytest \
  test_runtime_refactor.py::test_importing_main_preserves_root_logging_configuration \
  test_runtime_refactor.py::test_connection_check_does_not_change_default_socket_timeout -v
```

Expected: the logging test reports `False`, and the connection test fails because `socket.create_connection` is not called.

- [ ] **Step 3: Move logging setup behind an explicit function**

Replace import-time setup in `main.py` with module constants, a logger, and this function:

```python
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO
logger = logging.getLogger(__name__)


def configure_logging() -> bool:
    formatter = logging.Formatter(LOG_FORMAT)
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(LOG_LEVEL)
    root_logger.addHandler(stream_handler)

    try:
        config.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(config.LOG_FILE_PATH),
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
    except OSError as exc:
        root_logger.error(
            "Failed to initialize file logging to %s: %s",
            config.LOG_FILE_PATH,
            exc,
        )
        return False

    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)
    root_logger.addHandler(file_handler)
    return True
```

Call `configure_logging()` as the first statement in `main()` before argument parsing.

- [ ] **Step 4: Make the socket timeout connection-local**

Replace the body of `check_internet_connection` with:

```python
try:
    with socket.create_connection((host, port), timeout=timeout):
        logger.debug("Internet connection check succeeded for %s:%s", host, port)
    return True
except (OSError, socket.timeout) as exc:
    logger.debug("Internet connection check failed for %s:%s: %s", host, port, exc)
    return False
```

- [ ] **Step 5: Run the focused tests and verify GREEN**

Run the command from Step 2.

Expected: both tests pass.

- [ ] **Step 6: Commit side-effect isolation**

```bash
git add weather_display/main.py weather_display/utils/helpers.py test_runtime_refactor.py
git commit -m "fix: isolate process-wide runtime setup"
```

---

### Task 3: Give Connectivity and API Status Single Owners

**Files:**
- Modify: `weather_display/main.py:143-209,483-534,580-747`
- Test: `test_runtime_refactor.py:18-43,189-200`

**Interfaces:**
- Consumes: per-source strings `ok`, `error`, `offline`, `mock`, or `None`.
- Produces: `_record_api_status(source: str, status: str | None) -> None`, `_combined_api_status() -> str | None`, and `_schedule_status_update() -> None`.

- [ ] **Step 1: Write failing aggregation and ownership tests**

Extend `_FakeWindow.after` to return a stable job id so it remains compatible with controller scheduling:

```python
def after(self, _delay: int, callback: Any) -> str:
    callback()
    return "job-id"
```

Add a helper for controller-only test instances:

```python
def _controller_for_status_tests() -> WeatherDisplayApp:
    app = object.__new__(WeatherDisplayApp)
    app.app_window = cast(Any, _FakeWindow())
    app.last_connection_status = True
    app.last_forecast_success_time = 123.0
    app._current_api_status = None
    app._forecast_api_status = None
    app._status_lock = threading.Lock()
    return app
```

Add tests:

```python
def test_current_success_does_not_hide_forecast_failure() -> None:
    app = _controller_for_status_tests()

    app._record_api_status("forecast", "offline")
    app._record_api_status("current", "ok")
    app._schedule_status_update()

    window = cast(_FakeWindow, app.app_window)
    assert window.status_updates[-1] == (True, "offline", 123.0)


def test_weather_failure_does_not_overwrite_monitor_connectivity() -> None:
    app = _controller_for_status_tests()
    app.app_window = None
    app.ims_weather = cast(Any, SimpleNamespace(fetch_data=lambda: False))
    app.headless = True

    app._update_weather()

    assert app.last_connection_status is True


def test_forecast_failure_does_not_overwrite_monitor_connectivity() -> None:
    app = _controller_for_status_tests()
    app.app_window = None
    app.ims_forecast = cast(
        Any,
        SimpleNamespace(
            get_forecast=lambda force_refresh: {
                "data": [],
                "connection_status": False,
                "api_status": "offline",
                "cache_hit": True,
            }
        ),
    )
    app.headless = True

    app._update_forecast_data()

    assert app.last_connection_status is True
```

Import `threading` in the test module. Build the existing weather-exception
test with `_controller_for_status_tests()` and expect monitor connectivity to
remain `True`. Patch `configure_logging` in tests that call `main()` so those
tests stay focused on application startup rather than process logging setup.

- [ ] **Step 2: Run the focused status tests and verify RED**

```bash
./weather_venv/bin/python -m pytest \
  test_runtime_refactor.py::test_current_success_does_not_hide_forecast_failure \
  test_runtime_refactor.py::test_weather_failure_does_not_overwrite_monitor_connectivity \
  test_runtime_refactor.py::test_forecast_failure_does_not_overwrite_monitor_connectivity \
  test_runtime_refactor.py::test_weather_update_exception_updates_status_with_required_arguments -v
```

Expected: tests fail because the aggregation helpers do not exist and service updates still mutate `last_connection_status`.

- [ ] **Step 3: Add per-source API state and deterministic aggregation**

Initialize these fields in `WeatherDisplayApp.__init__`:

```python
self._status_lock = threading.Lock()
self._current_api_status: str | None = None
self._forecast_api_status: str | None = None
```

Add controller helpers:

```python
def _record_api_status(self, source: str, status: str | None) -> None:
    if source not in {"current", "forecast"}:
        raise ValueError(f"Unknown API status source: {source}")
    with self._status_lock:
        if source == "current":
            self._current_api_status = status
        else:
            self._forecast_api_status = status

def _combined_api_status(self) -> str | None:
    priority = {None: 0, "ok": 1, "mock": 2, "offline": 3, "error": 4}
    with self._status_lock:
        statuses = (self._current_api_status, self._forecast_api_status)
    return max(statuses, key=lambda status: priority.get(status, 4))

def _schedule_status_update(self) -> None:
    if not self.app_window:
        return
    connection_status = self.last_connection_status
    api_status = self._combined_api_status()
    success_time = self.last_forecast_success_time
    self.app_window.after(
        0,
        lambda: self.app_window.update_status_indicators(
            connection_status,
            api_status,
            success_time,
        ),
    )
```

- [ ] **Step 4: Route all status publishing through the aggregator**

In `_update_weather`, record the current status and schedule one combined update:

```python
self._record_api_status("current", api_status)
self._schedule_status_update()
```

In its exception handler, record `error` and schedule again. Remove every assignment to `last_connection_status` from `_update_weather`.

In `_update_forecast_data`, record `final_api_status`, schedule the combined update, and remove every assignment to `last_connection_status` from both success and exception paths.

In `_connection_monitoring_loop`, retain the assignment to `last_connection_status` and call `_schedule_status_update()` whenever the connectivity value changes. This loop remains the only writer after initialization.

- [ ] **Step 5: Run the focused status tests and verify GREEN**

Run the command from Step 2.

Expected: all four tests pass.

- [ ] **Step 6: Run all runtime regression tests**

```bash
./weather_venv/bin/python -m pytest test_runtime_refactor.py -v
```

Expected: every runtime regression test passes.

- [ ] **Step 7: Commit status ownership**

```bash
git add weather_display/main.py test_runtime_refactor.py
git commit -m "fix: centralize runtime status ownership"
```

---

### Task 4: Remove Confirmed Refactor Leftovers

**Files:**
- Modify: `weather_display/models.py`
- Modify: `weather_display/services/ims_forecast.py`
- Modify: `weather_display/utils/helpers.py`
- Modify: `weather_display/utils/__init__.py`
- Modify: `weather_display/utils/icon_handler.py`
- Modify: `weather_display/config.py`
- Modify: `weather_display/gui/app_window.py`
- Modify: `test_ims_forecast.py`
- Modify: `test_weather_display.py`

**Interfaces:**
- Consumes: production call-site search and the existing forecast/icon/UI tests.
- Produces: only `ForecastDay` in `models.py`; no eager utility export; bundled icons are read-only; no impossible AccuWeather-era status/configuration branches.

- [ ] **Step 1: Establish the cleanup baseline**

Run:

```bash
grep -RInE '\bformat_temperature\b|\bget_current_weather\b|\bparse_current_weather\b|\bCurrentWeather\b|\bforecast_time\b|limit_reached|status_no_connection_bg|status_api_limit_bg|status_api_error_bg|ctk_theme_name' \
  --include='*.py' weather_display test_*.py
```

Expected: matches identify each confirmed leftover and its tests; no production controller call site uses the city-current API.

- [ ] **Step 2: Remove the unused city-current model and service path**

Make `models.py` contain only `ForecastDay`:

```python
"""Typed forecast data shared between services and the display controller."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ForecastDay:
    date: str
    max_temp: float | None
    min_temp: float | None
    condition: str | None
    icon_code: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

In `ims_forecast.py`, import only `ForecastDay`; delete `get_current_weather`, `parse_current_weather`, `_to_int`, and `forecast_time` from mock analysis data. Remove current-analysis assertions from `test_ims_forecast.py` and the `get_current_weather` mock-data section from `test_weather_display.py`.

- [ ] **Step 3: Remove unused utility and configuration branches**

Delete `format_temperature` and its now-unused `Union` import from `helpers.py`.

Reduce `utils/__init__.py` to:

```python
"""Utility helpers for localization, connectivity, and weather icons."""
```

Delete `ctk_theme_name` and the three unused status-background entries from `config.py`. Delete the `limit_reached` branch and its docstring mention from `AppWindow.update_status_indicators`, plus the obsolete color-placeholder footer.

- [ ] **Step 4: Treat bundled icon assets as read-only**

In `WeatherIconHandler.__init__`, replace directory creation with direct initialization:

```python
self.icon_dir = self._ICON_BASE_DIR
self.icon_cache: Dict[str, ctk.CTkImage] = {}
logger.info("Icon directory set to: %s", self.icon_dir)
```

Move `load_image` to a normal module-level import now that `utils.__init__` no longer creates the circular import, and replace the dynamic import block in `load_icon` with:

```python
icon_image = load_image(icon_path, size=size)
```

Trim only stale comments adjacent to these removals and the status changes from Task 3.

- [ ] **Step 5: Run focused cleanup tests**

```bash
./weather_venv/bin/python -m pytest \
  test_ims_forecast.py test_weather_display.py test_icon_handling.py -v
```

Expected: all focused tests pass.

- [ ] **Step 6: Verify removed names have no Python call sites**

```bash
grep -RInE '\bformat_temperature\b|\bget_current_weather\b|\bparse_current_weather\b|\bCurrentWeather\b|\bforecast_time\b|limit_reached|status_no_connection_bg|status_api_limit_bg|status_api_error_bg|ctk_theme_name' \
  --include='*.py' weather_display test_*.py
```

Expected: no output and exit status 1.

- [ ] **Step 7: Commit cleanup**

```bash
git add weather_display test_ims_forecast.py test_weather_display.py test_icon_handling.py
git commit -m "refactor: remove IMS-only migration leftovers"
```

---

### Task 5: Full Verification

**Files:**
- Verify: all changed Python files and tests

**Interfaces:**
- Consumes: repository-standard verification commands.
- Produces: evidence that behavior, lint, types, and repository hygiene are clean.

- [ ] **Step 1: Run the full test suite**

```bash
./weather_venv/bin/python -m pytest
```

Expected: all tests pass with zero failures.

- [ ] **Step 2: Run Ruff**

```bash
./weather_venv/bin/python -m ruff check .
```

Expected: `All checks passed!`

- [ ] **Step 3: Run mypy**

```bash
./weather_venv/bin/python -m mypy weather_display
```

Expected: `Success: no issues found in 15 source files` or the updated source-file count.

- [ ] **Step 4: Check the diff and generated-file hygiene**

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only intentional source, test, and documentation changes are present. No logs, cache files, or `__pycache__` entries are staged.

- [ ] **Step 5: Commit any verification-only corrections**

If verification required a source or test correction, stage only those intentional files and commit:

```bash
git add weather_display test_*.py
git commit -m "test: finalize runtime cleanup verification"
```

If no correction was required, do not create an empty commit.
