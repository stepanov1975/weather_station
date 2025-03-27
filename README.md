# Weather Display for Raspberry Pi 5

A Python-based GUI application for Raspberry Pi 5 touchscreen that displays time, date, and weather information for Hadera, Israel.

## Features

- Current time (hours/minutes/seconds) in 24-hour format
- Current date, month, and year
- Current temperature, humidity, and air quality for Hadera, Israel
- 3-day forecast (high/low temperatures and weather conditions)
- Dark-themed interface optimized for touchscreens
- Fullscreen mode for a clean, kiosk-like view

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

3. Get a free API key from [WeatherAPI.com](https://www.weatherapi.com/):
   - Sign up for a free account
   - Navigate to your dashboard
   - Copy your API key

4. Add your API key to the configuration:
   - Edit `weather_display/config.py`
   - Replace the empty string for `WEATHER_API_KEY` with your API key

## Usage

Run the application:

```bash
python run_weather_display.py
```

### Command Line Options

- `--api-key KEY`: Specify the WeatherAPI.com API key
- `--mock`: Use mock data instead of real API data (for testing)
- `--windowed`: Run in windowed mode instead of fullscreen

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

- Change the location (default is Hadera, Israel)
- Adjust update intervals
- Modify UI settings (colors, fonts, sizes)
- Toggle fullscreen mode

## Troubleshooting

- If the application fails to start, check the `weather_display.log` file for error messages
- Ensure your API key is correct and has not exceeded its usage limits
- Verify that your Raspberry Pi has an active internet connection
- If using mock data (with `--mock` flag), no API key is required

## License

This project is licensed under the MIT License - see the LICENSE file for details.
