"""
Configuration settings for the Weather Display application.
"""
import os # Moved import to top

# Application settings
APP_TITLE = "Weather Display"
LANGUAGE = "ru"  # Language code: 'en' for English, 'ru' for Russian
APP_WIDTH = 1440
APP_HEIGHT = 810
FULLSCREEN = True
UPDATE_INTERVAL_SECONDS = 1  # For time display
WEATHER_UPDATE_INTERVAL_MINUTES = 60  # For weather data

# Location settings
# Reverted back to City,Country format
LOCATION = "Hadera,Israel"

# API settings (AccuWeather)
# Load API key from environment variable 'ACCUWEATHER_API_KEY', default to None if not found.
# Can be overridden by the --api-key command-line argument.
ACCUWEATHER_API_KEY = os.environ.get("ACCUWEATHER_API_KEY")
# Base URL for AccuWeather API endpoints.
ACCUWEATHER_BASE_URL = "http://dataservice.accuweather.com"
# WEATHER_API_KEY = ""  # Old key for WeatherAPI.com (commented out)
# WEATHER_API_URL = "https://api.weatherapi.com/v1" # Old URL for WeatherAPI.com (commented out)

# UI settings
DARK_MODE = True
FONT_FAMILY = "Helvetica"

# --- Font Sizes ---
TIME_FONT_SIZE_BASE = 300 # Base size for time (adjust as needed)
TIME_FONT_SIZE_INCREASE = 40 # Amount to add for the large time display
DATE_FONT_SIZE_BASE = 40 # Base size for date elements
DATE_DAY_FONT_SIZE_INCREASE = 100 # Amount to add for the large day number
WEATHER_FONT_SIZE = 20  # For current weather titles/values
FORECAST_FONT_SIZE = 25  # For forecast text
STATUS_INDICATOR_FONT_SIZE = 14 # For connection/API status

# --- Padding ---
# General padding between major sections
SECTION_PADDING_X = 10
SECTION_PADDING_Y = 10
# Padding within sections/frames
ELEMENT_PADDING_X = 5
ELEMENT_PADDING_Y = 5
# Fine-grained padding for text elements
TEXT_PADDING_X = 5
TEXT_PADDING_Y = 2

# --- Sizes ---
FORECAST_ICON_SIZE = (96, 96)
CONNECTION_FRAME_HEIGHT = 20

# --- Colors ---
# Theme colors (can be overridden by CustomTkinter theme)
BG_COLOR = "#1E1E1E"
TEXT_COLOR = "#FFFFFF" # General text color
ACCENT_COLOR = "#3498DB" # Accent color (e.g., for highlights)
SECONDARY_BG_COLOR = "#2D2D2D" # Background for sub-frames

# Specific UI element colors
NO_CONNECTION_COLOR = "#FF5555" # Red for no connection
API_LIMIT_COLOR = "#FFA500" # Orange for API limit
STATUS_TEXT_COLOR = "#FFFFFF" # Text color for status indicators

# --- Corner Radii ---
STATUS_INDICATOR_CORNER_RADIUS = 5

# Mock data for testing without API
USE_MOCK_DATA = False
