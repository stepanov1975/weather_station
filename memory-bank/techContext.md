# Technical Context: Weather Claude

## 1. Core Technologies

- **Language:** Python (Version 3.7+ recommended based on dependencies like CustomTkinter).
- **GUI Framework:** CustomTkinter (`customtkinter>=5.0.0`) - A modern UI toolkit based on Tkinter.
- **Image Handling:** Pillow (`pillow>=9.0.0`) - Used for image processing, primarily for loading weather icons via `WeatherIconHandler`.
- **HTTP Requests:** Requests (`requests>=2.25.0`) - Used for making API calls to fetch weather data from AccuWeather and the IMS XML feed.
- **Timezone Handling:** Pytz (`pytz>=2023.3`) - Used for managing timezones, specifically for converting IMS observation times to the local Israel timezone.

## 2. Development Environment & Tooling

- **Package Management:** `pip` with `requirements.txt` for application dependencies and `requirements-dev.txt` for development dependencies. Virtual environment (`weather_venv`) recommended.
- **Testing Framework:** Pytest (`pytest>=7.0.0`) with code coverage via `pytest-cov>=4.0.0`. (Tests may need updating based on recent changes).
- **Packaging:** Standard Python setuptools (`setup.py`, `MANIFEST.in`).
- **Version Control:** Git (implied by `.gitignore`).
- **Documentation:** Docstrings added throughout the `weather_display` package (modules, classes, functions) following PEP 8 guidelines. `README.md` updated.

## 3. Technical Constraints & Considerations

- Requires Python 3.7+ installation.
- Depends on external libraries specified in `requirements.txt`.
- Network connectivity required to fetch live weather data (unless using `--mock`).
- Requires a valid AccuWeather API key (provided via environment variable or command-line) for forecast/AQI data. IMS feed is public.
- GUI operation requires a graphical desktop environment (e.g., Raspberry Pi OS Desktop, not Lite). `DISPLAY` environment variable must be set.
- Font availability (defined in `config.FONTS`, defaulting to `Helvetica`) on the target system is necessary for correct UI rendering.
- Potential API rate limits for AccuWeather free tier need to be considered (handled partially by caching and status indicators).
- The extensive UI configuration options in `config.py` require careful management to ensure valid settings.

## 4. Dependencies

- **Runtime:** `customtkinter`, `pillow`, `pytz`, `requests`.
- **Development/Testing:** `pytest`, `pytest-cov`.

## 5. Tool Usage Patterns

- **Installation:** `pip install -r requirements.txt` (ideally within a virtual environment).
- **Running:** `python run_weather_display.py [options]` from the project root directory. Requires `ACCUWEATHER_API_KEY` to be set or passed via `--api-key` for live AccuWeather data.
- **Testing:** `pytest` in the project root directory (tests might need review/updates).
- **Packaging:** `python setup.py sdist bdist_wheel` (standard commands).
- **Listing IMS Stations:** `python weather_display/services/ims_lasthour.py --list`

## 6. Recent Technical Changes (April 19, 2025)

- **Documentation:** Added comprehensive docstrings to all modules, classes, and functions within the `weather_display` package.
- **Bug Fix (`NameError`):** Resolved an issue in `utils/helpers.py` by adding `from typing import List`.
- **Bug Fix (`TypeError`):** Corrected the function call to `get_day_name` in `gui/app_window.py` to pass the correct number of arguments.
- **GUI Refactoring:**
    - Overhauled `gui/app_window.py` to use a modular, configuration-driven approach based on CustomTkinter.
    - Significantly expanded `config.py` with detailed UI settings (layout, fonts, colors, padding, margins, optional elements).
- **API Optimization & Caching (April 19, 2025 - Update 4):**
    - Implemented conditional fetching for AQI in `services/weather_api.py` based on `config.OPTIONAL_ELEMENTS`.
    - Added persistent file caching for current weather and forecast data in `services/weather_api.py` (`current_weather_cache.json`, `forecast_cache.json`).
- **Status Indicator Improvements (April 19, 2025 - Update 5):**
    - Modified `main.py` to track and pass the last successful AccuWeather update time.
    - Refactored status indicators in `gui/app_window.py` to be persistent, displaying network status and detailed API status (including last success time).
- **Bug Fixes (April 19, 2025 - Update 5):**
    - Corrected `TypeError` in `gui/app_window.py` caused by incorrect parameters passed to `update_status_indicators`.
    - Fixed indentation errors in `gui/app_window.py` related to fullscreen logic.
    - **Fullscreen Improvement (April 19, 2025 - Update 6):** Replaced delayed fullscreen application (`self.after()`) with event binding (`<Map>`) in `gui/app_window.py` for potentially better reliability on platforms like Raspberry Pi 4.
