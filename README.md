# Weather Display for Raspberry Pi

A Python GUI weather station for a Raspberry Pi touchscreen. The active app is
IMS-only: it reads current local observations from the Israel Meteorological
Service last-hour XML feed and Hadera forecasts from the IMS city portal:

`https://ims.gov.il/en/city_portal/18`

## What It Shows

* Current time and date.
* Current temperature and humidity from the configured IMS station.
* Three-day forecast for Hadera from the IMS city portal.
* Weather icons mapped from IMS condition text to the local icon set.
* Network/API status indicators.

## Requirements

* Raspberry Pi OS or another Linux desktop environment.
* Python 3.10+.
* Internet connection for live IMS data.
* Python dependencies from `requirements.txt`.

Install dependencies:

```bash
python3 -m venv weather_venv
source weather_venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Edit `weather_display/config.py`:

* `IMS_STATION_NAME`: station for current observations. Current value:
  `"En Hahoresh"`.
* `IMS_CITY_LOCATION_ID`: IMS city portal id for the forecast. Hadera is `18`.
* `LANGUAGE`: display language, currently `"en"` or `"ru"`.
* `IMS_UPDATE_INTERVAL_MINUTES`: refresh interval for current observations.
* `IMS_FORECAST_UPDATE_INTERVAL_MINUTES`: refresh interval for forecast data.
* `FULLSCREEN`: fullscreen kiosk mode.
* `USE_MOCK_DATA`: run without live IMS calls for testing.

## Running

From the project root:

```bash
source weather_venv/bin/activate
python run_weather_display.py
```

Useful options:

```bash
python run_weather_display.py --windowed
python run_weather_display.py --mock
python run_weather_display.py --headless
```

## Startup Strategy

The GUI app is started by the Raspberry Pi desktop session, not by systemd.
This is intentional. Tk/CustomTkinter needs the logged-in desktop display
environment, and a system service does not reliably inherit `DISPLAY`,
`XAUTHORITY`, or the user session runtime.

Use this desktop autostart hook as the source of truth:
`/home/alex/.config/autostart/weather-display.desktop`.

Do not enable or rely on `weather-display.service` for GUI launch. If that
service exists on the machine, leave it disabled; it is not the active startup
strategy for this project.

### Desktop Autostart

Create or update `~/.config/autostart/weather-display.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Weather Display
Exec=/home/alex/weather_claude/weather_venv/bin/python /home/alex/weather_claude/run_weather_display.py
Path=/home/alex/weather_claude
Terminal=false
StartupNotify=false
```

No API key is needed.

### Manual Restart

If the app is already running, stop the current Python process and relaunch it
inside the active desktop session. On this Raspberry Pi, the working manual
launch command is:

```bash
env DISPLAY=:0 \
  XAUTHORITY=/home/alex/.Xauthority \
  XDG_RUNTIME_DIR=/run/user/1000 \
  /home/alex/weather_claude/weather_venv/bin/python \
  /home/alex/weather_claude/run_weather_display.py
```

Do not use `systemctl start weather-display.service` to preview GUI changes.

## Troubleshooting

* Check `~/.local/state/weather_display/weather_display.log` for startup and
  data-fetch errors.
* If the GUI fails, confirm the Pi booted into a desktop session and `DISPLAY`
  is set.
* If current observations are missing, verify `IMS_STATION_NAME` matches a
  station in the IMS last-hour XML feed.
* If forecasts are missing, verify `IMS_CITY_LOCATION_ID = 18` for Hadera or
  open the IMS city portal URL in a browser.
