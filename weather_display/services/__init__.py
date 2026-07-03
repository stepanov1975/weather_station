"""
Services Package for the Weather Display Application.

This package groups modules that provide distinct functionalities or interact
with external systems. These services encapsulate specific logic, making the
main application structure cleaner and more modular.

Services included:
- `ims_lasthour`: Client for fetching weather observations from the Israel
  Meteorological Service (IMS) last hour feed.
- `ims_forecast`: Client for fetching current analysis and forecasts from the
  IMS city portal.
- `time_service`: Provides formatted current time and date information, handling
  localization aspects.

Each service typically exposes a class or functions that can be instantiated or
called by the main application controller (`WeatherDisplayApp`) to retrieve
data or perform actions.
"""
# This __init__.py file marks the 'services' directory as a Python package.
