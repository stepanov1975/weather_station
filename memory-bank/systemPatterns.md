# System Patterns: Weather Claude

## 1. Overall Architecture (Inferred)

The application appears to follow a modular design, separating concerns into distinct components:

```mermaid
graph TD
    A[User Interface (GUI - CustomTkinter)] --> B(Application Logic / Main);
    B --> C{Configuration (`config.py`)};
    B --> D[Service Layer (IMS, AccuWeather)];
    D --> E{External APIs (IMS XML, AccuWeather REST)};
    B --> F[Utilities (Localization, Icons, Helpers)];
    B --> G[Background Threads];
    G --> D;
    G --> A;

    subgraph weather_display
        direction LR
        subgraph gui
            A
        end
        subgraph services
            D
        end
        subgraph utils
            F
        end
        B
        C
    end

    style gui fill:#f9f,stroke:#333,stroke-width:2px
    style services fill:#ccf,stroke:#333,stroke-width:2px
    style utils fill:#cfc,stroke:#333,stroke-width:2px
```

- **GUI (`weather_display/gui/app_window.py`):** Handles user interaction and presentation using the **CustomTkinter** library. It's designed to be **configuration-driven**, with layout, styling, and optional elements defined in `config.py`. It receives data updates from the main application logic.
- **Application Logic (`weather_display/main.py`):** Orchestrates the application. Initializes the GUI, services, and configuration. Manages **background threads** for periodic data fetching (IMS, AccuWeather, Time/Date), tracks the last successful AccuWeather update time, and schedules GUI updates (including status) using `app.after()`.
- **Configuration (`weather_display/config.py`):** Central hub for all settings: API keys/URLs, location, language, update intervals, and detailed UI parameters (layout weights, fonts, colors, padding, margins, optional elements).
- **Service Layer (`weather_display/services/`):** Encapsulates logic for fetching and processing data from external sources:
    - `ims_lasthour.py`: Fetches and parses local weather data from IMS XML feed.
    - `weather_api.py`: Handles interactions with the AccuWeather API (location lookup, current conditions/AQI, forecast). Implements **persistent file caching** for location key, current weather, and forecast data, alongside in-memory caching. Performs conditional AQI fetching based on config.
    - `time_service.py`: Provides current time and date strings.
- **Utilities (`weather_display/utils/`):** Provides shared helper functions:
    - `localization.py`: Handles translation of UI text and weather data based on `config.LANGUAGE`.
    - `icon_handler.py`: Loads and caches weather icons.
    - `helpers.py`: General utility functions (e.g., getting day name).
- **Assets (`weather_display/assets/`):** Stores static weather icons.
- **Background Threads:** Separate threads managed by `main.py` handle polling the IMS and AccuWeather services at configured intervals, preventing the GUI from freezing during network requests.

## 2. Key Technical Decisions

- **Python Language:** Core application language.
- **GUI Library:** **CustomTkinter** chosen for modern appearance and theming capabilities.
- **Configuration-Driven Design:** Prioritizing configuration (`config.py`) over hardcoded values, especially for UI layout and styling, enhancing flexibility.
- **Dual API Strategy:** Combining frequent local updates (IMS) with broader forecast/AQI data (AccuWeather).
- **Background Data Fetching:** Using Python's `threading` module to perform network requests asynchronously.
- **Scheduled GUI Updates:** Using `app.after()` to safely update CustomTkinter widgets from background threads.
- **Caching Strategy:** Multi-level caching (persistent file cache + in-memory cache) for AccuWeather data (location key, current, forecast) to reduce API calls and improve resilience. Conditional fetching of optional data (AQI).
- **Modularity:** Code organized into distinct packages (`gui`, `services`, `utils`).
- **Packaging:** Standard Python packaging (`setup.py`, `requirements.txt`).

## 3. Design Patterns

- **Separation of Concerns:** Clear division between UI (`gui`), data fetching/processing (`services`), application control (`main`), configuration (`config`), and shared utilities (`utils`).
- **Service Layer:** Abstracting external data interactions.
- **Configuration Management:** Centralized settings in `config.py`.
- **Caching:** Persistent file caching and in-memory caching patterns applied in `weather_api.py`.
- **Observer Pattern (Implicit):** `main.py` observes data fetched by background threads and notifies the `gui` to update.
- **Strategy Pattern (Potential):** Could be used if more weather providers were added to the `services` layer.

## 4. Component Relationships

- `main.py` initializes and coordinates all other components.
- `main.py` starts background threads that use `services` to fetch data.
- Background threads (via `main.py`'s `app.after`) trigger update methods in the `gui.AppWindow`, passing fetched data and status information (including last success time for AccuWeather).
- `gui.AppWindow` reads settings extensively from `config.py` for layout and styling. It updates its display based on data received from `main.py`.
- `services` use `config.py` for API keys, URLs, location settings, and optional feature flags (like AQI display).
- `utils` are used by `gui`, `services`, and `main`.

## 5. Critical Implementation Paths

- **Configuration Loading & Application:** Correctly reading and applying the diverse settings from `config.py` throughout the application, especially in the GUI.
- **Background Threading & GUI Updates:** Safely managing background data fetches and updating the CustomTkinter GUI without causing race conditions or errors.
- **Service Reliability:** Robust handling of potential errors (network issues, API errors, unexpected data formats) within the `services` modules. Includes persistent caching as a fallback mechanism.
- **GUI Rendering & Responsiveness:** Ensuring the CustomTkinter GUI renders correctly based on configuration and remains responsive despite background activity. Includes applying fullscreen mode based on the window's `<Map>` event for better compatibility across platforms.
