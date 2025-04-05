# Weather Display for Raspberry Pi 5 Touchscreen

A Python-based GUI application designed for Raspberry Pi 5 with a touchscreen display. It presents real-time clock, date, and detailed weather information fetched from the **AccuWeather API**.

## Overview

This application provides a clean, dark-themed interface optimized for touch interaction, displaying essential information at a glance. It's ideal for creating a dedicated weather station or information kiosk.

**Key Information Displayed:**

*   **Time:** Current hours and minutes (HH:MM) in 24-hour format.
*   **Date:** Current weekday, day, month, and year.
*   **Current Weather:**
    *   Temperature (°C)
    *   Humidity (%)
    *   Air Quality Index (AQI) category and value (requires appropriate AccuWeather API plan).
*   **Forecast:** 3-day weather forecast including:
    *   Day name
    *   Weather condition icon
    *   Weather condition description (localized)
    *   High/Low temperatures (°C)

## Features

*   **AccuWeather Integration:** Fetches current conditions, 3-day forecast, and AQI data.
*   **Touchscreen Optimized UI:** Dark theme, large fonts, and clear layout using CustomTkinter.
*   **Fullscreen Mode:** Runs fullscreen by default for a kiosk-like experience (can be disabled).
*   **Windowed Mode:** Option to run in a standard desktop window (`--windowed`).
*   **Headless Mode:** Run the application logic without launching the GUI, useful for testing data fetching (`--headless`).
*   **Mock Data Mode:** Test the UI and application flow without needing a live API key or internet connection (`--mock`).
*   **Localization:** Supports multiple languages for UI text and weather descriptions (currently configured for English 'en' and Russian 'ru' via `config.py`).
*   **Configurable:** Easily change location, language, update intervals, and UI appearance via `config.py`.
*   **API Key Handling:** Securely provide your AccuWeather API key via environment variable (`ACCUWEATHER_API_KEY`) or command-line argument (`--api-key`). The key is *not* stored directly in the configuration file.
*   **Connection Monitoring:** Displays status indicators for internet connectivity and potential AccuWeather API limit issues. Automatically attempts to refresh data when the connection is restored.
*   **Background Updates:** Time and weather data are updated periodically in background threads without blocking the UI.
*   **Logging:** Logs application events and potential errors to `weather_display.log` and the console.

## Requirements

*   Raspberry Pi 5 (or similar Linux system with desktop environment)
*   Touchscreen Display (recommended for intended use)
*   Python 3.7+
*   Internet connection (for live weather data)
*   AccuWeather API Key (free or paid plan, depending on desired features like AQI)

## Dependencies

The application relies on the following Python libraries:

*   **customtkinter:** For the modern graphical user interface.
*   **Pillow:** For handling and displaying weather icons.
*   **requests:** For making HTTP requests to the AccuWeather API.

Install them using pip:
```bash
pip install -r requirements.txt
```
Or individually:
```bash
pip install customtkinter pillow requests
```

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/weather-display.git # Replace with actual URL if known
    cd weather-display
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Get an AccuWeather API Key:**
    *   Visit the [AccuWeather Developer Portal](https://developer.accuweather.com/).
    *   Sign up or log in.
    *   Register a new application to obtain an API key.
    *   **Important:** Note that certain data points (like the detailed AQI) might require specific API plans or tiers. Check the AccuWeather documentation for details based on your key's plan.

4.  **Provide the API Key:** You **must** provide the API key for the application to fetch live data. Choose one method:
    *   **Environment Variable (Recommended):** Set the `ACCUWEATHER_API_KEY` variable in your shell environment before running the script. This is the most secure method.
        ```bash
        export ACCUWEATHER_API_KEY="YOUR_ACCUWEATHER_API_KEY"
        python run_weather_display.py
        ```
        To make this permanent, add the `export` line to your shell profile (e.g., `~/.bashrc` or `~/.profile`).
    *   **Command Line Argument:** Pass the key directly when running the script using the `--api-key` flag. This overrides the environment variable if set.
        ```bash
        python run_weather_display.py --api-key "YOUR_ACCUWEATHER_API_KEY"
        ```

## Usage

Run the main application script from the project's root directory:

```bash
python run_weather_display.py [OPTIONS]
```

### Command Line Options

*   `--api-key KEY`: Specify your AccuWeather API key. Overrides the `ACCUWEATHER_API_KEY` environment variable.
*   `--mock`: Run using built-in mock data. No API key or internet connection needed. Useful for UI testing.
*   `--windowed`: Start the application in a normal window instead of fullscreen. Overrides the `FULLSCREEN` setting in `config.py`.
*   `--headless`: Run without the GUI. The application will fetch data and log it according to the configured intervals. Useful for testing API calls or running on systems without a display.

### Examples

*   **Run normally (fullscreen, using environment variable for API key):**
    ```bash
    export ACCUWEATHER_API_KEY="YOUR_KEY"
    python run_weather_display.py
    ```
*   **Run in windowed mode, providing API key via argument:**
    ```bash
    python run_weather_display.py --api-key "YOUR_KEY" --windowed
    ```
*   **Run using mock data (no API key needed):**
    ```bash
    python run_weather_display.py --mock
    ```
*   **Run in headless mode:**
    ```bash
    export ACCUWEATHER_API_KEY="YOUR_KEY"
    python run_weather_display.py --headless
    ```

## Auto-start on Raspberry Pi Boot (Desktop Environment)

To make the application launch automatically when your Raspberry Pi boots into its graphical desktop environment:

1.  **Create Autostart Directory:** Ensure the autostart directory exists:
    ```bash
    mkdir -p ~/.config/autostart
    ```

2.  **Create Desktop Entry File:** Create a `.desktop` file for the application:
    ```bash
    nano ~/.config/autostart/weather-display.desktop
    ```

3.  **Add Content:** Paste the following content into the file. **Adjust the `Exec` and `Path` lines** to match the actual location where you cloned the repository and the path to your Python interpreter if necessary. Also, ensure the `ACCUWEATHER_API_KEY` environment variable is set system-wide or within this execution context if not using the `--api-key` argument here.

    ```ini
    [Desktop Entry]
    Type=Application
    Name=Weather Display
    Comment=Displays time, date, and weather information
    # Option 1: Rely on environment variable being set elsewhere (e.g., in .profile)
    Exec=/usr/bin/python3 /home/pi/weather-display/run_weather_display.py
    # Option 2: Provide API key directly (less secure)
    # Exec=/usr/bin/python3 /home/pi/weather-display/run_weather_display.py --api-key "YOUR_KEY"
    # Option 3: Use env command to set variable just for this launch
    # Exec=env ACCUWEATHER_API_KEY="YOUR_KEY" /usr/bin/python3 /home/pi/weather-display/run_weather_display.py
    Path=/home/pi/weather-display/
    Terminal=false
    StartupNotify=false
    ```
    *Choose **one** `Exec` line method.* Using `env` (Option 3) is often a good balance for autostart scripts if the environment variable isn't set globally.

4.  **Save and Exit:** Save the file (Ctrl+O in nano, then Enter) and exit (Ctrl+X).

The application should now start automatically the next time you boot into the desktop.

## Customization

Modify the `weather_display/config.py` file to tailor the application:

*   `LOCATION`: Set the target location (e.g., "London,UK", "Paris,France", "10001"). AccuWeather uses this to find a unique location key.
*   `LANGUAGE`: Change the display language ('en', 'ru' supported currently). Requires corresponding translations in `localization.py`.
*   `WEATHER_UPDATE_INTERVAL_MINUTES`: How often (in minutes) to fetch new weather data. Be mindful of API call limits.
*   `FULLSCREEN`: Set the default mode (`True` for fullscreen, `False` for windowed). Can be overridden by `--windowed`.
*   `DARK_MODE`: Toggle between dark (`True`) and light (`False`) themes.
*   `FONT_FAMILY`, Font Sizes, Paddings, Colors: Adjust UI appearance details.
*   `USE_MOCK_DATA`: Set to `True` to use mock data by default (can be overridden by `--mock`).

## Troubleshooting

*   **No Data / Errors:**
    *   Check `weather_display.log` for detailed error messages.
    *   Verify your `ACCUWEATHER_API_KEY` is correct and provided either via environment variable or `--api-key`.
    *   Ensure your AccuWeather API key plan supports the requested data (especially AQI). Check your usage limits on the AccuWeather developer portal.
    *   Confirm your Raspberry Pi has a stable internet connection. The app has a connection indicator.
*   **GUI Fails to Start:**
    *   Ensure you are running in a graphical desktop environment.
    *   Check if the `DISPLAY` environment variable is set correctly (usually `:0` or `:0.0`). Run `echo $DISPLAY` in the terminal.
    *   Try running with `--windowed` first.
    *   Check `weather_display.log` for specific Tkinter or display-related errors.
*   **Incorrect Location:** Double-check the `LOCATION` string in `config.py`. Use a format AccuWeather recognizes (City, Country; Zip Code; etc.).
*   **Mock Data Not Working:** Ensure `USE_MOCK_DATA = True` in `config.py` or you are using the `--mock` flag.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
