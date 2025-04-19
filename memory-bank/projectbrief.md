# Project Brief: Weather Claude (Raspberry Pi Weather Display)

## 1. Project Goal

To create a dedicated, always-on weather display application optimized for Raspberry Pi 4 (or similar Linux systems), potentially with a touchscreen. The application aggregates data from multiple sources (IMS for local Israeli conditions, AccuWeather for forecasts/AQI) and presents it in a highly configurable graphical user interface.

## 2. Core Requirements

- **Dual API Integration:** Fetch current weather (temp/humidity) from Israel Meteorological Service (IMS) and forecast/AQI data from AccuWeather.
- **Comprehensive Display:** Show current time, date, temperature, humidity, air quality index (category), and a multi-day forecast (day name, icon, condition, temp range).
- **Configurable GUI:** Provide a graphical user interface (using CustomTkinter) where layout (region sizes), styling (fonts, colors, padding, margins, radii), and optional elements (status bar, humidity, AQI) can be extensively customized via a configuration file (`config.py`).
- **Localization:** Support multiple languages for UI text and weather descriptions (currently English and Russian).
- **Status Monitoring:** Display indicators for internet connection status and API health (e.g., AccuWeather limits).
- **Platform Optimization:** Suitable for continuous operation on a Raspberry Pi 4, supporting fullscreen mode.

## 3. Scope

- **In Scope:**
    - Integration with IMS and AccuWeather APIs.
    - Display of time, date, current conditions (temp, humidity, AQI), and 3-day forecast.
    - Highly configurable GUI layout and appearance via `config.py`.
    - Background data refresh loops.
    - Status indicators.
    - Localization (EN, RU).
    - Fullscreen support.
- **Out of Scope (Currently):** Advanced meteorological data (wind, pressure beyond basic display), historical weather, user accounts, complex map integrations, GUI-based configuration editor.

## 4. Target Audience

Users who want a dedicated, customizable weather station display, particularly for use on a Raspberry Pi 4 in a home or office setting. Users may range from those wanting a simple setup to those desiring fine-grained control over the UI appearance.

## 5. Success Metrics

- Application successfully fetches and displays accurate, combined data from IMS and AccuWeather.
- GUI is clear, readable, and accurately reflects the settings in `config.py`.
- Application is stable for continuous operation on a Raspberry Pi 4.
- Configuration options are well-documented and allow for significant UI customization without code changes.
