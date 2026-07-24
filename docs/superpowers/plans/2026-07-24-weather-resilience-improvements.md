# Weather Resilience Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the Raspberry Pi display responsive and honest during network failures while completing IMS mappings and lightweight deployment checks.

**Architecture:** Preserve the existing controller, service, and GUI boundaries. Add only small data fields and locks/events where required: services normalize/cache data, the controller owns background work and stale state, and the window only renders supplied status.

**Tech Stack:** Python 3.10+, CustomTkinter, requests, pytest, Ruff, mypy, GitHub Actions.

## Global Constraints

- Use `./weather_venv` for Python tools.
- Keep the existing IMS-only architecture and dictionary payloads.
- Do not add a framework, generic retry layer, or configuration subsystem.
- Write a failing behavior test before each production change.
- Do not commit or restart the deployed application unless explicitly requested.

---

### Task 1: Truthful Forecast Cache

**Files:**
- Modify: `weather_display/services/ims_forecast.py`
- Modify: `weather_display/services/json_cache.py`
- Test: `test_ims_forecast.py`
- Test: `test_json_cache.py`

**Interfaces:**
- `JsonCache.store(payload)` remains unchanged and writes atomically.
- `IMSCityForecast.get_forecast(...)["cache_timestamp"]` exposes the persisted fetch time.
- `parse_forecast(..., today=None)` filters rows older than the local date.

- [x] Add a failing test proving past forecast dates are excluded.
- [x] Add a failing test proving cache timestamps are returned for cached and offline results.
- [x] Add a failing test that simulates replacement and verifies atomic cache storage.
- [x] Implement the minimum filtering, metadata propagation, and temporary-file replacement.
- [x] Run `./weather_venv/bin/python -m pytest test_ims_forecast.py test_json_cache.py`.

### Task 2: Resilient Current Observations

**Files:**
- Modify: `weather_display/main.py`
- Modify: `weather_display/gui/app_window.py`
- Test: `test_runtime_refactor.py`
- Test: `test_app_window.py`

**Interfaces:**
- The controller retains `_last_current_weather_data` after a successful fetch.
- Current update payloads contain `stale: bool` without changing existing data keys.
- Empty failed payloads do not erase displayed temperature and humidity.

- [x] Add a failing test: success followed by failure republishes the last data with `stale=True`.
- [x] Add a failing window test: an empty payload retains existing label text.
- [x] Implement the retained snapshot and early return in the renderer.
- [x] Run the focused controller/window tests.

### Task 3: Responsive Lifecycle

**Files:**
- Modify: `weather_display/main.py`
- Modify: `weather_display/services/ims_forecast.py`
- Modify: `weather_display/services/ims_lasthour.py`
- Modify: `weather_display/utils/helpers.py`
- Test: `test_runtime_refactor.py`
- Test: `test_coverage_closure.py`

**Interfaces:**
- GUI `start()` enters `mainloop()` without calling network fetch methods synchronously.
- A `threading.Event` interrupts periodic waits during shutdown.
- Per-source locks skip overlapping current or forecast fetches.
- Signal handlers are registered before both GUI and headless run loops.
- HTTP calls use separate short connect/read timeouts.

- [x] Add failing lifecycle tests for asynchronous initial updates and GUI signal registration.
- [x] Add failing tests for event-driven stop and overlap suppression.
- [x] Implement initial one-off workers, event waits, signal registration, and source locks.
- [x] Remove duplicate startup connectivity probing; keep the monitor only for UI/reconnect hints.
- [x] Run the focused lifecycle tests.

### Task 4: IMS Conditions, Timezones, and Localized Status

**Files:**
- Modify: `weather_display/services/ims_forecast.py`
- Modify: `weather_display/services/ims_lasthour.py`
- Modify: `weather_display/utils/localization.py`
- Modify: `weather_display/gui/app_window.py`
- Test: `test_ims_forecast.py`
- Test: `test_ims_lasthour.py`
- Test: `test_utils.py`
- Test: `test_app_window.py`

**Interfaces:**
- IMS weather codes map directly to bundled internal icon codes.
- Offset-aware and `Z` timestamps convert without `Conversion_Error`.
- Status prefixes/states use existing `get_translation()`.

- [x] Add a realistic weather-code fixture covering sleet, windy, frost, stormy, and rainy-cloud conditions.
- [x] Add failing aware-timestamp tests.
- [x] Add failing Russian status-label tests.
- [x] Implement direct code mapping, aware datetime conversion, and translation keys.
- [x] Run the focused service/localization/window tests.

### Task 5: Lightweight Deployment Verification

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `requirements-dev.txt`
- Create: `requirements-lock.txt`
- Modify: `README.md`

**Interfaces:**
- CI runs supported Python 3.10 and deployed Python 3.11.
- CI builds a wheel once and runs a minimal Xvfb import/window smoke check.
- `requirements-lock.txt` pins runtime packages for Raspberry Pi reinstalls.

- [x] Add `build` and `wheel` development requirements.
- [x] Add the Python matrix, wheel build, and minimal Xvfb smoke command.
- [x] Record installed runtime dependency versions in `requirements-lock.txt`.
- [x] Document locked deployment installation in the README.
- [x] Build an sdist/wheel in `/tmp` if local build tooling is available.

### Task 6: Final Verification

- [x] Run `./weather_venv/bin/python -m pytest`.
- [x] Run `./weather_venv/bin/python -m ruff check .`.
- [x] Run `./weather_venv/bin/python -m mypy weather_display`.
- [x] Review `git diff --check`, the complete diff, and `git status`.
- [x] Confirm no generated logs, caches, or bytecode are tracked.
