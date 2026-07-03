# Project Brief

The project is an always-on Raspberry Pi weather display for Hadera-area weather.
It shows the current time/date, recent local observations, and a short forecast
using Israel Meteorological Service (IMS) data.

## Goals

- Run unattended at Raspberry Pi boot.
- Use IMS data only.
- Display current temperature and humidity from the configured IMS station.
- Display a three-day Hadera forecast from the IMS city portal.
- Continue launching when the network is unavailable and recover automatically
  when connectivity returns.
- Use cached forecast data instead of stale hardcoded fallback data.

## Success Criteria

- No API key is required.
- The app starts in GUI or headless mode without blocking on internet access.
- Shutdown via signals or window close cleans up background threads and GUI jobs.
- `pytest`, `ruff`, and `mypy` run cleanly from the project virtual environment.
