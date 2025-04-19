"""
Centralized Configuration for the Weather Display Application.

This module consolidates all user-configurable settings and constants required
for the Weather Display application. By centralizing these values, it simplifies
management, customization, and maintenance of the application's behavior.

Settings include:
- General application parameters (title, language, dimensions).
- API endpoint details and keys (AccuWeather, IMS).
- Data refresh intervals for different services.
- Location settings for weather data retrieval.
- User interface (UI) customizations (theme, fonts, colors, padding, sizes).
- Flags for enabling/disabling features like fullscreen or mock data usage.

It is recommended to configure sensitive information like API keys using
environment variables for better security practices, although defaults can be
set here.
"""
import os

# ==============================================================================
# Application Settings
# ==============================================================================
# The title displayed in the application window's title bar.
APP_TITLE = "Weather Display"

# Language code for UI text localization (e.g., 'en', 'he', 'ru').
# Affects translations provided by the localization utility.
LANGUAGE = "ru"

# Language code specifically for requests to the AccuWeather API.
# This determines the language of descriptive text returned by AccuWeather.
# Format examples: "en-us", "he-il".
ACCUWEATHER_LANGUAGE = "en-us"

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

# How often (in minutes) to fetch updated weather data (current, forecast, AQI)
# from the AccuWeather service. Note AccuWeather's free tier limits.
ACCUWEATHER_UPDATE_INTERVAL_MINUTES = 120

# ==============================================================================
# Location Settings
# ==============================================================================
# The geographical location for which to fetch weather data.
# This is primarily used by the AccuWeather service to find a location key.
# Format: "City,Country" or "City,State,Country".
LOCATION = "Hadera,Israel"

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
# API Settings (AccuWeather)
# ==============================================================================
# The base URL for all AccuWeather API requests.
ACCUWEATHER_BASE_URL = "http://dataservice.accuweather.com"

# Your AccuWeather Developer API Key.
# **SECURITY WARNING**: Avoid hardcoding the API key directly in the code.
# It is STRONGLY recommended to set this using the 'ACCUWEATHER_API_KEY'
# environment variable.
# The application prioritizes keys in this order:
# 1. Command-line argument (`--api-key`)
# 2. Environment variable (`ACCUWEATHER_API_KEY`)
# 3. This config file value (ACCUWEATHER_API_KEY) - Least preferred method.
ACCUWEATHER_API_KEY = os.environ.get('ACCUWEATHER_API_KEY')

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
    "background": ("gray", "#E5E5E5", "#242424"), # Main window background
    "frame_background": ("gray", "#DBDBDB", "#2B2B2B"), # Frame background
    "text": ("black", "#101010", "#DCE4EE"), # Default text color
    "text_secondary": ("gray", "#606060", "#A0A0A0"), # Less prominent text
    "accent": ("blue", "#3B8ED0", "#1F6AA5"), # Accent color for highlights
    # Status Indicator Colors (overriding specific values below if needed)
    "status_no_connection_bg": ("red", "#FF5555", "#C04040"),
    "status_api_limit_bg": ("orange", "#FFA500", "#D08000"),
    "status_api_error_bg": ("red", "#FF0000", "#A00000"),
    "status_text": ("white", "#FFFFFF", "#FFFFFF"), # Default/fallback status text color
    # Specific Status Text Colors (used by AppWindow.update_status_indicators)
    "status_ok_text": ("green", "#009688", "#4CAF50"),      # Greenish for OK
    "status_warning_text": ("orange", "#FF9800", "#FFB300"), # Amber/Orange for Warning/Limit
    "status_error_text": ("red", "#F44336", "#E57373"),   # Reddish for Error/Offline
}

# Select the active color palette based on DARK_MODE
ACTIVE_COLORS = {name: colors[2] if DARK_MODE else colors[1] for name, colors in COLOR_THEME.items()}

# Set the default CTk color theme based on the primary color choice
# Note: This sets the base theme; specific widget colors can still be overridden using ACTIVE_COLORS
ctk_theme_name = COLOR_THEME["primary"][0] # e.g., "blue"
# CTK_DEFAULT_COLOR_THEME = "blue" # Keep this simple for now, advanced theming can be complex

# --- Layout Structure ---
# Defines the relative height proportions of the main UI regions.
# Values represent weights for the grid rows.
# Order: [Status Bar, Time/Date Region, Current Conditions Region, Forecast Region]
# Status bar height is fixed by CONNECTION_FRAME_HEIGHT, so its weight is 0.
# The remaining weights distribute the available vertical space.
# Default: Time/Date=1/3, Current=1/4, Forecast=Remainder (~5/12)
# Example weights to approximate this: Time=4, Current=3, Forecast=5 (total 12)
REGION_HEIGHT_WEIGHTS = {
    "status": 0, # Fixed height
    "time_date": 4,
    "current_conditions": 3,
    "forecast": 5,
}

# --- Fonts ---
# Default font family used if a specific element doesn't define its own.
DEFAULT_FONT_FAMILY = "Helvetica"

# Font configurations for different UI elements.
# Format: (Family, Size, Weight) - Weight can be "normal" or "bold".
# Use DEFAULT_FONT_FAMILY if family is None.
FONTS = {
    "time": (None, 280, "bold"), # Large time display (HH:MM)
    "weekday": (None, 40, "normal"), # Day of the week (e.g., "Sunday")
    "day_number": (None, 140, "bold"), # Large day number (e.g., "21")
    "month_year": (None, 40, "normal"), # Month and year (e.g., "April 2024")
    "current_temp_value": (None, 80, "bold"), # Current temperature value
    "current_temp_title": (None, 30, "bold"), # "Temperature" label
    "current_humidity_value": (None, 80, "bold"), # Current humidity value
    "current_humidity_title": (None, 30, "bold"), # "Humidity" label
    "current_aqi_value": (None, 40, "bold"), # Air Quality Index value/category
    "current_aqi_title": (None, 30, "bold"), # "Air Quality" label
    "forecast_day": (None, 40, "bold"), # Day name in forecast (e.g., "Mon")
    "forecast_condition": (None, 35, "normal"), # Weather condition text in forecast
    "forecast_temp": (None, 35, "normal"), # Temperature range in forecast (e.g., "25° / 18°")
    "status_indicator": (None, 14, "normal"), # Small text in status bar indicators
}

# --- Padding and Margins (in pixels) ---
# Padding defines space *inside* a widget or frame border.
# Margin defines space *outside* a widget or frame border.

# Padding around the main content area within each major region frame.
REGION_PADDING = {"padx": 10, "pady": 10}

# Padding around individual elements *within* a region (e.g., labels in current weather).
ELEMENT_PADDING = {"padx": 5, "pady": 5}

# Padding specifically around text *inside* a label widget.
TEXT_PADDING = {"padx": 5, "pady": 2}

# Margins *between* elements within a layout (e.g., space between forecast day frames).
ELEMENT_MARGINS = {"padx": 5, "pady": 5}

# --- Sizes (in pixels) ---
# Dimensions (width, height) for the weather icons displayed in the forecast.
FORECAST_ICON_SIZE = (96, 96)
# Height of the top frame used to display connection and API status indicators.
CONNECTION_FRAME_HEIGHT = 30

# --- Corner Radii (in pixels) ---
# Defines how rounded the corners of frames and specific widgets are.
FRAME_CORNER_RADIUS = 8
STATUS_INDICATOR_CORNER_RADIUS = 5

# --- Optional Elements ---
# Flags to control the visibility of certain UI components.
# Set to True to show, False to hide.
OPTIONAL_ELEMENTS = {
    "show_status_bar": True,
    "show_current_humidity": True,
    "show_current_air_quality": True,
    # Add more flags here as needed, e.g., "show_forecast_condition_text"
}

# ==============================================================================
# Data Refresh Rates
# ==============================================================================
# How often (in seconds) the displayed time and date should refresh.
UPDATE_INTERVAL_TIME_DATE_SECONDS = 1

# How often (in minutes) to fetch updated weather data from the IMS service.
UPDATE_INTERVAL_IMS_MINUTES = 10

# How often (in minutes) to fetch updated weather data (current, forecast, AQI)
# from the AccuWeather service. Note AccuWeather's free tier limits.
UPDATE_INTERVAL_ACCUWEATHER_MINUTES = 120

# ==============================================================================
# Mock Data Settings
# ==============================================================================
# If True, the application will use predefined mock data instead of making
# live calls to the weather APIs. Useful for UI development and testing
# without consuming API quotas or requiring an internet connection.
# Set to False for normal operation.
USE_MOCK_DATA = False
