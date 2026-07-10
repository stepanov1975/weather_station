# Comprehensive Test Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise meaningful branch coverage to at least 85% by exercising GUI, controller, service, and utility behavior with mocks and local fixtures.

**Architecture:** The tests remain at the repository root. A small fake CustomTkinter widget records configuration and callback calls, allowing UI behavior to be asserted without a display server. Tests mock IMS, time, image, and filesystem boundaries.

**Tech Stack:** Python 3.10+, pytest, unittest.mock, pytest-cov, ruff, mypy.

## Global Constraints

- Use `./weather_venv/bin/python -m pytest` for all tests.
- Do not open GUI windows, access IMS over the network, or depend on Raspberry Pi hardware.
- Only change production code for a defect proven by a failing test.
- Do not stage logs, coverage artifacts, caches, or `__pycache__` files.

---

## File Structure

- Create `test_app_window.py` for headless AppWindow rendering and fullscreen tests.
- Modify `test_runtime_refactor.py` for controller lifecycle, loop, and status tests.
- Modify `test_ims_forecast.py` and `test_ims_lasthour.py` for parsing and fallback tests.
- Create `test_utils.py` for localization, time, connectivity, image, icon-cache, and model tests.

### Task 1: Headless GUI behavior

**Files:**

- Create: `test_app_window.py`

**Interfaces:**

- Consumes: `AppWindow.update_time`, `update_date`, `update_current_weather`, `update_forecast`, `update_status_indicators`, and `_apply_fullscreen`.
- Produces: `_Widget` recording `configure` calls and `_window_with_labels()` bypassing `AppWindow.__init__`.

- [ ] **Step 1: Write the failing test**

```python
def test_update_time_and_date_split_values_on_headless_window() -> None:
    window = _window_with_labels()
    window.update_time("08:09:10")
    window.update_date("Friday, 04 July 2026")
    assert window.time_label.values["text"] == "08:09"
    assert window.day_label.values["text"] == "4"
```

- [ ] **Step 2: Verify red**

Run: `./weather_venv/bin/python -m pytest test_app_window.py::test_update_time_and_date_split_values_on_headless_window -v`

Expected: FAIL because the test harness does not exist.

- [ ] **Step 3: Write the minimal test harness**

```python
class _Widget:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}
    def configure(self, **kwargs: object) -> None:
        self.values.update(kwargs)

def _window_with_labels() -> AppWindow:
    window = object.__new__(AppWindow)
    window.time_label = window.weekday_label = _Widget()
    window.day_label = window.month_year_label = _Widget()
    return window
```

- [ ] **Step 4: Verify green**

Run: `./weather_venv/bin/python -m pytest test_app_window.py -v`

Expected: PASS after adding malformed time/date, absent temperature/humidity, loaded/missing forecast icon, all temperature range, API status, disabled status bar, and fullscreen fallback tests.

- [ ] **Step 5: Commit**

Run: `git add test_app_window.py && git commit -m "test: cover app window rendering branches"`

### Task 2: Controller and services

**Files:**

- Modify: `test_runtime_refactor.py`
- Modify: `test_ims_forecast.py`
- Modify: `test_ims_lasthour.py`

**Interfaces:**

- Consumes: `WeatherDisplayApp.start`, `stop`, `_update_time_and_date`, update loops, status scheduling, and IMS fetch/parse/accessor methods.
- Produces: deterministic fake-window/thread tests and local XML/JSON fixture tests.

- [ ] **Step 1: Write the failing test**

```python
def test_time_update_publishes_values_and_reschedules_when_running() -> None:
    app = _controller_for_status_tests()
    app.running = True
    app._time_update_job_id = None
    app.app_window.update_time = Mock()
    app.app_window.update_date = Mock()
    with patch("weather_display.main.TimeService.get_current_datetime", return_value=("08:09:10", "Friday, 4 July 2026")):
        app._update_time_and_date()
    app.app_window.update_time.assert_called_once_with("08:09:10")
```

- [ ] **Step 2: Verify red**

Run: `./weather_venv/bin/python -m pytest test_runtime_refactor.py::test_time_update_publishes_values_and_reschedules_when_running -v`

Expected: FAIL until the fake window supports the time/date update methods.

- [ ] **Step 3: Extend only test fakes and fixtures**

```python
class _FakeWindow:
    def update_time(self, _value: str) -> None:
        pass
    def update_date(self, _value: str) -> None:
        pass
```

Add one behavior test each for headless/windowed start, time-service failure, callback cancellation, thread creation failure, status priority, cache/network fallback, invalid payload, missing forecast data, nonnumeric temperatures, unknown codes, station network error, malformed local XML, and empty accessors.

- [ ] **Step 4: Verify green**

Run: `./weather_venv/bin/python -m pytest test_runtime_refactor.py test_ims_forecast.py test_ims_lasthour.py -v`

Expected: PASS with no external requests or lingering threads.

- [ ] **Step 5: Commit**

Run: `git add test_runtime_refactor.py test_ims_forecast.py test_ims_lasthour.py && git commit -m "test: cover runtime and IMS failure paths"`

### Task 3: Utilities, coverage closure, and verification

**Files:**

- Create: `test_utils.py`
- Modify: `test_weather_display.py`
- Modify: `test_icon_handling.py`

**Interfaces:**

- Consumes: localization, `TimeService`, `check_internet_connection`, `load_image`, `WeatherIconHandler.load_icon`, and `ForecastDay.to_dict`.
- Produces: behavior assertions for normal, fallback, and invalid input paths.

- [ ] **Step 1: Write the failing tests**

```python
def test_load_icon_caches_image_by_effective_code_and_size() -> None:
    handler = WeatherIconHandler()
    with patch("weather_display.utils.icon_handler.load_image", return_value=object()) as load:
        assert handler.load_icon(1, (32, 32)) is handler.load_icon(1, (32, 32))
    load.assert_called_once()
```

- [ ] **Step 2: Verify red**

Run: `./weather_venv/bin/python -m pytest test_utils.py -v`

Expected: FAIL because the test module is absent.

- [ ] **Step 3: Add utility behavior tests**

```python
def test_get_day_name_returns_not_available_for_none() -> None:
    with patch("weather_display.utils.helpers.config.LANGUAGE", "en"):
        assert get_day_name(None) == "N/A"
```

Cover unknown language/key fallback, unmapped/None conditions, valid/invalid dates, frozen date formatting, socket failure, missing/corrupt images, icon cache miss/failure, and `ForecastDay.to_dict`.

- [ ] **Step 4: Close report-identified branches with red-green tests**

Run: `./weather_venv/bin/python -m pytest --cov=weather_display --cov-branch --cov-report=term-missing`

Expected: use the report to identify each remaining reachable behavior; add one focused test, confirm it fails, then extend only the relevant test harness or fix a demonstrated defect.

- [ ] **Step 5: Verify and commit**

Run: `./weather_venv/bin/python -m pytest && ./weather_venv/bin/python -m ruff check . && ./weather_venv/bin/python -m mypy weather_display`

Expected: all commands exit 0 and coverage is at least 85%.

Run: `git add test_*.py weather_display && git commit -m "test: close comprehensive coverage gaps"`
