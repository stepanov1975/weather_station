# Comprehensive Test Coverage Design

## Goal

Increase meaningful automated coverage across the weather display, including
the CustomTkinter GUI, without requiring a graphical display or live IMS
network access.

## Scope

- Add mock-based unit tests for `AppWindow` rendering, status changes,
  scheduling callbacks, and graceful handling of unavailable display data.
- Add mock-based tests for `WeatherDisplayApp` lifecycle, refresh scheduling,
  cache fallback, and service failure paths.
- Cover untested parser, cache, localization, time, image, and connectivity
  branches where their behavior is externally observable.
- Keep production changes limited to defects demonstrated by a new failing test.

## Test Design

Tests will replace CustomTkinter widgets, image creation, timers, and external
services with small mocks. Assertions will verify widget configuration, callback
registration, and resulting user-visible values rather than implementation-only
method calls. IMS HTTP and filesystem cases will use existing test fixtures and
temporary paths.

The suite will not create real windows, contact live services, or depend on
Raspberry Pi hardware. It will avoid tests that only execute lines without
checking behavior.

## Success Criteria

- The full pytest suite passes with branch coverage enabled.
- The new tests cover the principal GUI and controller lifecycle branches and
  important service failure/fallback paths.
- Overall branch coverage reaches at least 85%, unless an environment-bound
  integration path cannot be reached without real hardware; any such exception
  will be explicitly reported.
- Ruff and mypy complete without new errors.
