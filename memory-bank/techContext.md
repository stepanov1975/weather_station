# Technical Context

## Stack

- Python 3.11
- CustomTkinter for the kiosk UI
- Requests for IMS HTTP calls
- Pillow for weather icon loading
- Pytest for tests
- Ruff for linting
- Mypy for type checking

## Standard Commands

```bash
./weather_venv/bin/python -m pytest
./weather_venv/bin/python -m ruff check .
./weather_venv/bin/python -m mypy weather_display
```

## Weather Sources

- Current observations: IMS last-hour XML feed.
- Forecast: IMS city portal, configured with `IMS_CITY_LOCATION_ID = 18` for
  Hadera.

## Startup

The app should be launched from the repository or installed package without any
weather API key. Raspberry Pi boot must not fail just because the network is not
ready yet.

Logs are written outside the repository by default:
`~/.local/state/weather_display/weather_display.log`.
