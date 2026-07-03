# System Patterns

## Architecture

- `weather_display/main.py` owns application lifecycle, background polling, signal
  handling, and GUI scheduling.
- `weather_display/services/ims_lasthour.py` fetches current station observations
  from the IMS last-hour XML feed.
- `weather_display/services/ims_forecast.py` fetches and normalizes the Hadera
  city forecast from the IMS city portal.
- `weather_display/services/json_cache.py` persists the last successful forecast
  payload for offline startup and recovery.
- `weather_display/models.py` contains small typed weather data shapes used by
  services before converting to GUI-compatible dictionaries.
- `weather_display/gui/app_window.py` renders the kiosk UI and exposes update
  methods for the controller.

## Runtime Flow

1. CLI arguments adjust mock/window/headless mode.
2. The app logs the initial network status but does not block boot.
3. Current observations and forecast updates run on background threads.
4. GUI mutations are scheduled through Tk `after()` calls.
5. Reconnection triggers one-off refresh threads that are tracked for shutdown.
6. `stop()` is idempotent and performs clock-job cancellation, thread joins, and
   GUI destruction.

## Data Resilience

The forecast service tries IMS directly. On request failure it returns the last
persisted IMS forecast payload when available; otherwise it reports an error with
an empty payload. Mock data is used only when mock mode is explicitly enabled.
