# Weather Display for Raspberry Pi 4

A Python-based GUI application designed primarily for Raspberry Pi 4 with a touchscreen display (though usable on other Linux systems). It presents a real-time clock, date, and detailed weather information fetched from multiple sources:

*   **AccuWeather API:** Provides multi-day forecasts, current conditions (including Air Quality Index - AQI, if supported by your API plan), and location lookup.
*   **Israel Meteorological Service (IMS):** Provides hyper-local, frequently updated current temperature and humidity readings for specific stations within Israel (via their public XML feed).

## Overview

This application offers a clean, customizable (dark/light) interface optimized for touch interaction, displaying essential time, date, and weather information at a glance. It's well-suited for creating a dedicated weather station, information kiosk, or simply a helpful desktop display, especially on a Raspberry Pi 4.

**Key Information Displayed:**

*   **Time:** Current hours and minutes (HH:MM) in 24-hour format, updated every second.
*   **Date:** Current weekday, day, month, and year, localized to the configured language.
*   **Current Weather (Combined Sources):**
    *   Temperature (°C) - Primarily from IMS for frequent updates, potentially supplemented by AccuWeather.
    *   Humidity (%) - Primarily from IMS, potentially supplemented by AccuWeather.
    *   Air Quality Index (AQI) - Category (e.g., "Good", "Moderate") fetched from AccuWeather (requires appropriate API plan).
*   **Forecast:** 3-day weather forecast fetched from AccuWeather, including:
    *   Day name (localized)
    *   Weather condition icon
    *   Weather condition description (localized)
    *   High/Low temperatures (°C)

## Features

*   **Dual Weather Sources:** Combines frequent local updates (Temp/Humidity) from IMS with broader forecast and AQI data from AccuWeather.
*   **Touchscreen Optimized UI:** Clear layout, large fonts, and configurable dark/light theme using the CustomTkinter library.
*   **Fullscreen Mode:** Runs fullscreen by default for an immersive kiosk-like experience (can be disabled via config or command-line).
*   **Windowed Mode:** Option to run in a standard desktop window (`--windowed`).
*   **Headless Mode:** Run the application logic without launching the GUI, useful for testing data fetching or running on servers (`--headless`).
*   **Mock Data Mode:** Test the UI and application flow without needing live API keys or an internet connection (`--mock`).
*   **Localization:** Supports multiple languages for UI text, dates, and weather descriptions (currently English 'en' and Russian 'ru' are configured via `config.py`). Easily extendable by adding new language dictionaries in `localization.py`.
*   **Configurable:** Modify location (for AccuWeather), IMS station name, language, update intervals, UI appearance (theme, fonts, colors, padding), and API keys via `weather_display/config.py`.
*   **AccuWeather API Key Handling:** Securely provide your AccuWeather API key via environment variable (`ACCUWEATHER_API_KEY`) or command-line argument (`--api-key`). The key is *not* stored directly in the configuration file. (IMS service does not require an API key).
*   **Persistent Location Cache:** Caches the AccuWeather location key to a file (`location_cache.json`) to reduce API calls.
*   **Connection Monitoring:** Displays status indicators for internet connectivity and potential AccuWeather API limit issues. Automatically attempts to refresh data when the connection is restored.
*   **Background Updates:** Time, IMS weather, and AccuWeather data are updated periodically in background threads without blocking the UI.
*   **Logging:** Logs application events, API calls, and potential errors to `weather_display.log` and the console for monitoring and debugging.

## Requirements

*   **Raspberry Pi 4** (Recommended target platform) or similar Linux system with a desktop environment (if using GUI).
*   Touchscreen Display (Recommended for intended UI interaction, but optional).
*   Python 3.7+
*   Internet connection (required for fetching live weather data from IMS and AccuWeather, unless using `--mock`).
*   **AccuWeather API Key:** A free or paid plan is required for AccuWeather data. Note that certain data points (like detailed AQI) might require specific API plans. Check the AccuWeather documentation.

## Dependencies

The application relies on the following Python libraries:

*   **customtkinter:** For the modern graphical user interface elements.
*   **Pillow:** For handling and displaying weather icons.
*   **requests:** For making HTTP requests to the AccuWeather API and IMS feed.
*   **pytz:** For handling timezone conversions (specifically for IMS data).

Install them using the provided requirements file:
```bash
pip install -r requirements.txt
```
Or individually:
```bash
pip install customtkinter pillow requests pytz
```

## Installation

1.  **Clone the Repository:**
    ```bash
    # Replace with the actual URL if hosted on GitHub/GitLab etc.
    # git clone https://github.com/yourusername/weather-display.git
    # cd weather-display
    # If you just have the files locally, navigate to the project directory.
    cd /path/to/weather_claude
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv weather_venv
    source weather_venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Get an AccuWeather API Key:**
    *   Visit the [AccuWeather Developer Portal](https://developer.accuweather.com/).
    *   Sign up or log in.
    *   Register a new application to obtain an API key.
    *   **Important:** Note that certain data points (like the detailed AQI) might require specific API plans or tiers. Check the AccuWeather documentation for details based on your key's plan.

5.  **Provide the AccuWeather API Key:** You **must** provide the AccuWeather API key for the application to fetch live forecast/AQI data. Choose one method:
    *   **Environment Variable (Recommended):** Set the `ACCUWEATHER_API_KEY` variable in your shell environment before running the script. This is the most secure method.
        ```bash
        export ACCUWEATHER_API_KEY="YOUR_ACCUWEATHER_API_KEY"
        python run_weather_display.py
        ```
        To make this permanent, add the `export` line to your shell profile (e.g., `~/.bashrc`, `~/.profile`, or `/etc/environment` for system-wide).
    *   **Command Line Argument:** Pass the key directly when running the script using the `--api-key` flag. This overrides the environment variable if set.
        ```bash
        python run_weather_display.py --api-key "YOUR_ACCUWEATHER_API_KEY"
        ```
    *(Note: The IMS service currently does not require an API key).*

6.  **Configure Location and IMS Station:**
    *   Edit `weather_display/config.py`.
    *   Set the `LOCATION` variable for AccuWeather (e.g., `"Hadera,Israel"`).
    *   Set the `IMS_STATION_NAME` variable to the desired Israeli station (e.g., `"En Hahoresh"`). You can list available stations by running `python weather_display/services/ims_lasthour.py --list`.

## Usage

Ensure your virtual environment is activated (`source weather_venv/bin/activate`) if you created one. Run the main application script from the project's root directory (`weather_claude`):

```bash
python run_weather_display.py [OPTIONS]
```

### Command Line Options

*   `--api-key KEY`: Specify your AccuWeather API key. Overrides the `ACCUWEATHER_API_KEY` environment variable and config file setting.
*   `--mock`: Run using built-in mock data for both AccuWeather and IMS. No API key or internet connection needed. Useful for UI testing.
*   `--windowed`: Start the application in a normal window instead of fullscreen. Overrides the `FULLSCREEN` setting in `config.py`.
*   `--headless`: Run without the GUI. The application will fetch data (or use mock data if configured) and log it according to the configured intervals. Useful for testing API calls or running on systems without a display.

### Examples

*   **Run normally (fullscreen, using environment variable for API key):**
    ```bash
    # Ensure ACCUWEATHER_API_KEY is set in your environment
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
    # Ensure ACCUWEATHER_API_KEY is set in your environment
    python run_weather_display.py --headless
    ```

## Auto-start on Raspberry Pi 4 Boot (Desktop Environment)

To make the application launch automatically when your Raspberry Pi 4 boots into its graphical desktop environment:

1.  **Create Autostart Directory:** Ensure the autostart directory exists:
    ```bash
    mkdir -p ~/.config/autostart
    ```

2.  **Create Desktop Entry File:** Create a `.desktop` file for the application using a text editor like `nano`:
    ```bash
    nano ~/.config/autostart/weather-display.desktop
    ```

3.  **Add Content:** Paste the following content into the file. **Crucially, adjust the `Exec` and `Path` lines** to match the actual location where you cloned/placed the project (`/home/alex/weather_claude` in this case) and the path to your Python 3 interpreter (often `/usr/bin/python3` or the path within your virtual environment like `/home/alex/weather_claude/weather_venv/bin/python`). Also, ensure the `ACCUWEATHER_API_KEY` environment variable is set system-wide or within this execution context if not using the `--api-key` argument here.

    ```ini
    [Desktop Entry]
    Type=Application
    Name=Weather Display
    Comment=Displays time, date, and weather information
    # --- Choose ONE Exec line ---
    # Option 1: Rely on environment variable set elsewhere (e.g., in ~/.profile) and system python
    # Exec=/usr/bin/python3 /home/alex/weather_claude/run_weather_display.py
    # Option 2: Rely on environment variable and python from virtual env
    Exec=/home/alex/weather_claude/weather_venv/bin/python /home/alex/weather_claude/run_weather_display.py
    # Option 3: Use 'env' command to set variable just for this launch (using virtual env python)
    # Exec=env ACCUWEATHER_API_KEY="YOUR_KEY" /home/alex/weather_claude/weather_venv/bin/python /home/alex/weather_claude/run_weather_display.py
    # Option 4: Provide API key directly via argument (less secure, using virtual env python)
    # Exec=/home/alex/weather_claude/weather_venv/bin/python /home/alex/weather_claude/run_weather_display.py --api-key "YOUR_KEY"

    # Set the working directory for the application
    Path=/home/alex/weather_claude/
    Terminal=false
    StartupNotify=false
    ```
    *Choose **one** `Exec` line method that best suits your setup.* Using the virtual environment's Python (Option 2 or 3) is generally recommended. Using `env` (Option 3) is often a good balance for autostart scripts if the environment variable isn't set globally.

4.  **Save and Exit:** Save the file (Ctrl+O in nano, then Enter) and exit (Ctrl+X).

5.  **Make Executable (Optional but Recommended):**
    ```bash
    chmod +x ~/.config/autostart/weather-display.desktop
    ```

The application should now attempt to start automatically the next time you boot into the Raspberry Pi OS desktop environment. Check the `weather_display.log` file in the project directory if it doesn't start.

## Customization

Modify the `weather_display/config.py` file to tailor the application:

*   `LOCATION`: Set the target location for AccuWeather (e.g., "London,UK", "Paris,France", "10001"). AccuWeather uses this to find a unique location key.
*   `IMS_STATION_NAME`: Set the exact name of the desired Israel Meteorological Service station (e.g., "En Hahoresh", "Tel Aviv Coast"). Run `python weather_display/services/ims_lasthour.py --list` to see available station names from the feed.
*   `LANGUAGE`: Change the display language ('en', 'ru' supported currently). Requires corresponding translations in `localization.py`.
*   `ACCUWEATHER_UPDATE_INTERVAL_MINUTES`: How often (in minutes) to fetch new AccuWeather data (forecast, AQI). Be mindful of API call limits.
*   `IMS_UPDATE_INTERVAL_MINUTES`: How often (in minutes) to fetch new IMS data (local temp/humidity). Can be more frequent.
*   `FULLSCREEN`: Set the default mode (`True` for fullscreen, `False` for windowed). Can be overridden by `--windowed`.
*   `DARK_MODE`: Toggle between dark (`True`) and light (`False`) themes.
*   `FONT_FAMILY`, Font Sizes, Paddings, Colors: Adjust UI appearance details.
*   `USE_MOCK_DATA`: Set to `True` to use mock data by default (can be overridden by `--mock`).

## Troubleshooting

*   **No Data / Errors:**
    *   Check `weather_display.log` in the project directory for detailed error messages.
    *   **AccuWeather:** Verify your `ACCUWEATHER_API_KEY` is correct and provided (via environment variable or `--api-key`). Check your usage limits on the AccuWeather developer portal. Ensure your plan supports requested data (like AQI).
    *   **IMS:** Verify the `IMS_STATION_NAME` in `config.py` exactly matches a station name from the IMS feed (check with `python weather_display/services/ims_lasthour.py --list`). The IMS feed might occasionally be unavailable.
    *   **Connection:** Confirm your Raspberry Pi has a stable internet connection. The app displays status indicators.
*   **GUI Fails to Start:**
    *   Ensure you are running in a graphical desktop environment (not Lite OS without a desktop).
    *   Check if the `DISPLAY` environment variable is set correctly (usually `:0` or `:0.0`). Run `echo $DISPLAY` in the terminal.
    *   Try running with `--windowed` first.
    *   Check `weather_display.log` for specific Tkinter or display-related errors (e.g., "no display name", "TclError").
*   **Incorrect Location (AccuWeather):** Double-check the `LOCATION` string in `config.py`. Use a format AccuWeather recognizes (City, Country; Zip Code; etc.). Check the `location_cache.json` file - deleting it might force a fresh lookup.
*   **Mock Data Not Working:** Ensure `USE_MOCK_DATA = True` in `config.py` or you are using the `--mock` flag when running.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
