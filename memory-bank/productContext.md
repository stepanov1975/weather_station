# Product Context: Weather Display for Raspberry Pi 4

## 1. Problem Solved

Provides a dedicated, always-on display for essential time, date, and detailed weather information, suitable for a kiosk or desktop environment, particularly on a Raspberry Pi 4. It aggregates data from multiple sources (AccuWeather for forecasts/AQI, IMS for local Israeli conditions) for a comprehensive view without needing manual interaction with web browsers or mobile apps.

## 2. Core Functionality (Current State)

- **Time & Date Display:** Shows current time (HH:MM) and fully formatted, localized date (Weekday, Day Month Year).
- **Current Weather Display:**
    - Temperature (°C) - Primarily from IMS (Israel Meteorological Service) for frequent local updates.
    - Humidity (%) - Primarily from IMS.
    - Air Quality Index (AQI) - Category description (e.g., "Good", "Moderate") from AccuWeather (requires appropriate API plan).
- **Forecast Display:** Shows a 3-day forecast fetched from AccuWeather, including:
    - Localized day name.
    - Weather icon representing the day's conditions.
    - Localized weather condition description.
    - High/Low temperature range (°C).
- **Dual API Integration:** Fetches data from both AccuWeather and IMS services.
- **GUI:** Modular, configuration-driven interface using CustomTkinter. Features distinct regions for Time/Date, Current Conditions, and Forecast. Supports fullscreen and windowed modes.
- **Configuration:** Highly configurable via `config.py`. Allows setting:
    - API details (AccuWeather location, IMS station, keys).
    - Language and update intervals.
    - Detailed UI appearance: dark/light mode, specific colors, fonts for various elements, padding, margins, corner radii.
    - Layout structure: Relative heights of UI regions.
    - Optional elements: Show/hide status bar, humidity, AQI.
- **Status Indicators:** Persistently displays the current network connection status ("Network: OK" / "Network: Offline") and the status of the last AccuWeather API call ("API: OK", "API: Limit", "API: Error", etc.), including the time of the last successful call. Can be hidden via config (`OPTIONAL_ELEMENTS['show_status_bar']`).
- **Localization:** Supports English ('en') and Russian ('ru') for UI text, dates, and weather descriptions.

## 3. User Experience Goals

- **At-a-Glance Information:** Present key time, date, and weather data clearly and concisely.
- **Reliability:** Provide up-to-date information by combining frequent local updates (IMS) with broader forecasts (AccuWeather). Handle API errors and connection issues gracefully.
- **Deep Customization:** Allow users extensive control over location, language, data sources, UI layout (region sizes), appearance (fonts, colors, spacing), and optional elements via the configuration file.
- **Platform Suitability:** Optimized for running on a Raspberry Pi 4 with a touchscreen, potentially in a kiosk setup.
- **Low Friction:** Easy setup with clear instructions for API key handling and configuration, while offering advanced customization for those who want it.

## 4. Target User Journey

1.  User sets up the application on a Raspberry Pi 4 (or similar Linux system), providing an AccuWeather API key and configuring location/IMS station in `config.py`. Optionally, the user extensively customizes the UI layout, fonts, colors, and optional elements in `config.py`.
2.  User runs the application (potentially configured to auto-start on boot).
3.  Application launches (typically fullscreen) displaying the weather information according to the user's configuration.
4.  User glances at the display periodically to get time, date, current conditions, AQI, and forecast information.
5.  Application runs continuously, updating data in the background and showing status indicators if issues arise.
6.  (Optional) User exits fullscreen (Escape key) or stops the application if needed.
