# Progress

## Working

- IMS station observations are fetched from `IMSLastHourWeather`.
- Hadera forecast is fetched from `IMSCityForecast`.
- Forecast data is cached persistently for offline fallback.
- GUI update methods consume the existing dictionary payload shape.
- Tests, linting, and type checking are part of the repo workflow.

## Remaining Improvement Ideas

- Add parser fixture tests for real IMS city portal responses.
- Add lifecycle tests for periodic update loops with fake clocks.
- Consider splitting `AppWindow` into smaller view components if more UI work is
  needed.
- Consider adding a desktop-autostart smoke test for Raspberry Pi deployment.
