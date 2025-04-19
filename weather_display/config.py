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
# Theme mode for the application ('dark' or 'light').
# Affects the overall color scheme used by CustomTkinter widgets.
DARK_MODE = True

# Default font family to be used for most text elements in the UI.
# Ensure this font is available on the target system (e.g., Raspberry Pi).
FONT_FAMILY = "Helvetica"

# --- Font Sizes (in points) ---
# Base font size for the main time display (HH:MM).
TIME_FONT_SIZE_BASE = 270
# Additional points added to the base size for a larger time display effect.
TIME_FONT_SIZE_INCREASE = 40

# Base font size for date elements like weekday and month/year.
DATE_FONT_SIZE_BASE = 40
# Additional points added to the base size for the large day number display.
DATE_DAY_FONT_SIZE_INCREASE = 100

# Font size for current weather information labels (e.g., "Temperature", "25°C").
WEATHER_FONT_SIZE = 40
# Font size for text within the forecast sections (day, temp range).
FORECAST_FONT_SIZE = 45
# Font size for the small status indicators (e.g., "API OK", "No Connection").
STATUS_INDICATOR_FONT_SIZE = 14

# --- Padding (in pixels) ---
# Horizontal padding between major UI sections (e.g., time frame, weather frame).
SECTION_PADDING_X = 5
# Vertical padding between major UI sections.
SECTION_PADDING_Y = 5

# Horizontal padding around elements within a section (e.g., inside current weather).
ELEMENT_PADDING_X = 5
# Vertical padding around elements within a section.
ELEMENT_PADDING_Y = 5

# Fine-grained horizontal padding specifically around text labels.
TEXT_PADDING_X = 5
# Fine-grained vertical padding specifically around text labels.
TEXT_PADDING_Y = 2

# --- Sizes (in pixels) ---
# Dimensions (width, height) for the weather icons displayed in the forecast.
FORECAST_ICON_SIZE = (96, 96)
# Height of the top frame used to display connection and API status indicators.
CONNECTION_FRAME_HEIGHT = 30

# --- Colors ---
# Note: Many colors are handled by the CustomTkinter theme (DARK_MODE).
# These specific color definitions are primarily for custom elements like
# status indicators or can serve as fallbacks if theming is disabled.

# General background color (primarily used if not using CTk themes).
BG_COLOR = "#1E1E1E"
# General text color (primarily used if not using CTk themes).
TEXT_COLOR = "#FFFFFF"
# Accent color for highlighting elements (usage may vary).
ACCENT_COLOR = "#3498DB"
# Background color for secondary elements or sub-frames.
SECONDARY_BG_COLOR = "#2D2D2D"

# Specific colors for status indicators:
# Background color for the 'No Internet Connection' indicator.
NO_CONNECTION_COLOR = "#FF5555"  # Reddish
# Background color for the 'AccuWeather API Limit Reached' indicator.
API_LIMIT_COLOR = "#FFA500"  # Orange
# Background color for a general 'API Error' indicator.
API_ERROR_COLOR = "#FF0000"  # Bright Red
# Text color used within the status indicator labels.
STATUS_TEXT_COLOR = "#FFFFFF"  # White

# --- Corner Radii (in pixels) ---
# Defines how rounded the corners of the status indicator boxes are.
STATUS_INDICATOR_CORNER_RADIUS = 5

# ==============================================================================
# Mock Data Settings
# ==============================================================================
# If True, the application will use predefined mock data instead of making
# live calls to the weather APIs. Useful for UI development and testing
# without consuming API quotas or requiring an internet connection.
# Set to False for normal operation.
USE_MOCK_DATA = False
