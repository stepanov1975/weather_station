# Weather Display for Raspberry Pi 5

A Python-based GUI application for Raspberry Pi 5 touchscreen that displays time, date, and weather information for a configured location using the **AccuWeather API**.

## Features

- Current time (hours/minutes/seconds) in 24-hour format
- Current date, month, and year
- Current temperature and humidity.
- Current Air Quality Index (AQI) category and value (fetched via AccuWeather Indices API, depends on API plan).
- 3-day forecast (high/low temperatures and weather conditions) (fetched via AccuWeather 5-day forecast API).
- Dark-themed interface optimized for touchscreens.
- Fullscreen mode for a clean, kiosk-like view.
- Headless mode for running without a GUI (e.g., for testing via SSH).
- Supports English and Russian languages.
- Configurable location and update intervals.
- Mock data mode for testing without an API key.

## Requirements

- Raspberry Pi 5 with touchscreen display
- Python 3.7+
- Internet connection for weather data

## Dependencies

- CustomTkinter: Modern UI toolkit based on Tkinter
- Pillow: Image processing library
- Requests: HTTP library for API calls

## Installation

1. Clone this repository to your Raspberry Pi:

```bash
git clone https://github.com/yourusername/weather-display.git
cd weather-display
```

2. Install the required dependencies:

```bash
pip install customtkinter pillow requests
```

3. Get an API key from [AccuWeather Developer Portal](https://developer.accuweather.com/):
   - Sign up for an account.
   - Create an application to get an API key. Note that different features (like AQI or extended forecasts) might require specific API plans.

4. **Provide your API key via Environment Variable or Command Line:**
   - **Environment Variable (Recommended):** Set the `ACCUWEATHER_API_KEY` environment variable before running the application.
     ```bash
     export ACCUWEATHER_API_KEY="YOUR_ACCUWEATHER_API_KEY"
     python run_weather_display.py
     ```
   - **Command Line Argument:** Use the `--api-key` argument when running.
     ```bash
     python run_weather_display.py --api-key "YOUR_ACCUWEATHER_API_KEY"
     ```
   - **Note:** The API key is no longer stored in `config.py`.

## Usage

Run the application:

```bash
python run_weather_display.py
```

### Command Line Options

- `--api-key KEY`: Specify the AccuWeather API key (overrides environment variable).
- `--mock`: Use mock data instead of real API data (for testing).
- `--windowed`: Run in windowed mode instead of fullscreen.
- `--headless`: Run without a GUI (logs data fetching to console/log file). Useful for testing in non-graphical environments.

Example:

```bash
python run_weather_display.py --api-key YOUR_API_KEY --windowed
```

## Auto-start on Raspberry Pi Boot

To make the application start automatically when your Raspberry Pi boots:

### Method 1: Using systemd (recommended)

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/weather-display.service
```

2. Add the following content (adjust paths as needed):

```
[Unit]
Description=Weather Display
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/weather-display/run_weather_display.py
WorkingDirectory=/home/pi/weather-display
User=pi
Restart=on-failure
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl enable weather-display.service
sudo systemctl start weather-display.service
```

### Method 2: Using autostart (desktop environment)

1. Create an autostart directory if it doesn't exist:

```bash
mkdir -p ~/.config/autostart
```

2. Create a desktop entry file:

```bash
nano ~/.config/autostart/weather-display.desktop
```

3. Add the following content (adjust paths as needed):

```
[Desktop Entry]
Type=Application
Name=Weather Display
Exec=/usr/bin/python3 /home/pi/weather-display/run_weather_display.py
Terminal=false
```

## Customization

You can customize various aspects of the application by editing the `weather_display/config.py` file:

- `LOCATION`: The location query for weather data (e.g., "City,Country"). AccuWeather uses this to find a location key.
- `LANGUAGE`: Set to 'en' or 'ru'.
- `ACCUWEATHER_API_KEY`: (Loaded from environment/argument) Your AccuWeather API key.
- `WEATHER_UPDATE_INTERVAL_MINUTES`: How often to fetch new weather data.
- `FULLSCREEN`: Set to `False` to disable fullscreen by default.
- Font sizes, colors, etc.

## Troubleshooting

- If the application fails to start, check the `weather_display.log` file for error messages.
- Ensure your API key is provided correctly (via environment or `--api-key`) and is valid for the required AccuWeather endpoints (Current Conditions, 5-Day Forecast, Indices API for AQI). Check your AccuWeather plan limits.
- Verify that your Raspberry Pi has an active internet connection.
- If using mock data (`--mock`), no API key is required.
- If running with GUI and it fails with display errors, ensure a display environment is available (`DISPLAY` environment variable is set) or use `--headless`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
