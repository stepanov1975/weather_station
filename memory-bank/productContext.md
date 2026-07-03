# Product Context

The display is intended for a Raspberry Pi kiosk that can sit unattended and
show useful local weather at a glance.

## User Experience

- Large clock and date.
- Current temperature and humidity.
- Three-day local forecast.
- Status text for network/API state.
- Fullscreen by default, with windowed and headless modes available for testing.

## Reliability Expectations

- The display should come up during boot even if Wi-Fi or Ethernet is late.
- Forecast data should use the last successful IMS response while offline.
- Background updates should not freeze the GUI.
- Shutdown should be graceful when the desktop session or the user sends a stop
  signal.
