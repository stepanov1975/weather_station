"""Centralized configuration for the weather display application."""

import os
from pathlib import Path
# ==============================================================================
# Application Settings
# ==============================================================================
# The title displayed in the application window's title bar.
APP_TITLE = "Weather Display"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_xdg_state_home = os.environ.get("XDG_STATE_HOME")
USER_STATE_DIR = (
    Path(_xdg_state_home)
    if _xdg_state_home and Path(_xdg_state_home).is_absolute()
    else Path.home() / ".local" / "state"
)
APP_STATE_DIR = USER_STATE_DIR / "weather_display"
LOG_FILE_PATH = APP_STATE_DIR / "weather_display.log"
IMS_FORECAST_CACHE_PATH = APP_STATE_DIR / "forecast_cache.json"

# Language code for UI text localization (e.g., 'en', 'he', 'ru').
# Affects translations provided by the localization utility.
LANGUAGE = "ru"


# Initial width of the application window in pixels when not in fullscreen.
APP_WIDTH = 1440
# Initial height of the application window in pixels when not in fullscreen.
APP_HEIGHT = 810

# If True, the application attempts to launch in fullscreen mode.
# If False, it uses APP_WIDTH and APP_HEIGHT.
FULLSCREEN = True

# How often (in seconds) the displayed time and date should refresh.
# Lower values provide a more real-time clock update.
UPDATE_INTERVAL_SECONDS = 1

# How often (in minutes) to fetch updated weather data from the IMS service.
IMS_UPDATE_INTERVAL_MINUTES = 10

# How often (in minutes) to fetch updated forecast data from the IMS city portal.
IMS_FORECAST_UPDATE_INTERVAL_MINUTES = 120

# ==============================================================================
# Location Settings
# ==============================================================================
# IMS city portal location id for Hadera.
IMS_CITY_LOCATION_ID = 18

# ==============================================================================
# API Settings (IMS - Israel Meteorological Service)
# ==============================================================================
# The specific weather station name used by the IMS service.
# The exact name must match one available from the IMS data source.
# Examples: "En Hahoresh", "Tel Aviv Coast", "Jerusalem Centre".
IMS_STATION_NAME = "En Hahoresh"

# The URL for the IMS last hour data feed (XML format).
# Defined here for reference, but typically used directly within the IMS service class.
# IMS_URL = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"

# ==============================================================================
# UI Settings (CustomTkinter Theming and Appearance)
# ==============================================================================

# --- Theme and Colors ---
# Theme mode for the application ('dark' or 'light').
# This sets the base theme for CustomTkinter widgets.
DARK_MODE = True

# Define explicit color palettes for light and dark modes.
# These can override or supplement the default CTk theme colors.
# Colors are used for backgrounds, text, accents, etc.
# Format: (CTk Default Name, Hex Color Light, Hex Color Dark)
# See CTk documentation for default theme color names.
COLOR_THEME = {
    "primary": ("blue", "#3B8ED0", "#1F6AA5"), # Example primary color
    "secondary": ("green", "#2CC985", "#2FA572"), # Example secondary color
    "background": ("gray", "#E5E5E5", "#102722"), # Main window background
    "frame_background": ("gray", "#DBDBDB", "#2B2B2B"), # Frame background
    "text": ("black", "#101010", "#F4F3EB"), # Default text color
    "text_secondary": ("gray", "#606060", "#D5E3D7"), # Less prominent text
    "accent": ("mint", "#205F48", "#C9EDD5"),
    "divider": ("green", "#90A59A", "#4A6961"),
    "status_text": ("white", "#303030", "#FFFFFF"), # Default/fallback status text color
    # Specific Status Text Colors (used by AppWindow.update_status_indicators)
    "status_ok_text": ("green", "#00584D", "#B8DBC0"),      # Greenish for OK
    "status_error_text": ("red", "#9B2420", "#E57373"),   # Reddish for Error/Offline
}

# Select the active color palette based on DARK_MODE
ACTIVE_COLORS = {name: colors[2] if DARK_MODE else colors[1] for name, colors in COLOR_THEME.items()}

# --- Fonts ---
# Default font family used if a specific element doesn't define its own.
DEFAULT_FONT_FAMILY = "Helvetica"

# Font configurations for different UI elements.
# Format: (Family, Size, Weight) - Weight can be "normal" or "bold".
# Use DEFAULT_FONT_FAMILY if family is None.
FONTS = {
    "station": (None, 22, "bold"),
    "time": (None, 252, "bold"),
    "weekday": (None, 46, "normal"),
    "day_number": (None, 86, "bold"),
    "month_year": (None, 40, "normal"),
    "current_temp_value": (None, 108, "bold"),
    "current_temp_title": (None, 26, "normal"),
    "current_humidity_value": (None, 84, "bold"),
    "current_humidity_title": (None, 26, "normal"),
    "forecast_day": (None, 35, "bold"),
    "forecast_condition": (None, 27, "normal"),
    "forecast_temp": (None, 34, "normal"),
    "status_indicator": (None, 19, "normal"),
}

FORECAST_ICON_SIZE = (140, 84)

# --- Optional Elements ---
# Flags to control the visibility of certain UI components.
# Set to True to show, False to hide.
OPTIONAL_ELEMENTS = {
    "show_status_bar": True,
    "show_current_humidity": True,
    # Add more flags here as needed, e.g., "show_forecast_condition_text"
}

# ==============================================================================
# Mock Data Settings
# ==============================================================================
# If True, the application will use predefined mock data instead of making
# live calls to IMS. Useful for UI development and testing without requiring
# an internet connection.
# Set to False for normal operation.
USE_MOCK_DATA = False
