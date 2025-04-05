"""
Configuration settings for the Weather Display application.

This module defines constants used throughout the application, such as API keys,
UI settings, and update intervals. Centralizing configuration makes it easier
to manage and modify application behavior.
"""
import os

# ==============================================================================
# Application Settings
# ==============================================================================
APP_TITLE = "Weather Display"
# Language code for translations: 'en' for English, 'ru' for Russian, etc.
LANGUAGE = "ru"
APP_WIDTH = 1440  # Initial window width in pixels
APP_HEIGHT = 810  # Initial window height in pixels
FULLSCREEN = True  # Run in fullscreen mode if True
# Update interval for the time display (affects clock refresh rate)
UPDATE_INTERVAL_SECONDS = 1
# Update interval for fetching new weather data from the API
WEATHER_UPDATE_INTERVAL_MINUTES = 60

# ==============================================================================
# Location Settings
# ==============================================================================
# Location query string used for the weather API (e.g., "City,Country")
LOCATION = "Hadera,Israel"

# ==============================================================================
# API Settings (AccuWeather)
# ==============================================================================
# Load API key from environment variable 'ACCUWEATHER_API_KEY'.
# Defaults to None if the environment variable is not set.
# Can be overridden by the --api-key command-line argument in main.py.
ACCUWEATHER_API_KEY = os.environ.get("ACCUWEATHER_API_KEY")
# Base URL for AccuWeather API endpoints.
ACCUWEATHER_BASE_URL = "http://dataservice.accuweather.com"
# Old settings for WeatherAPI.com (commented out for reference)
# WEATHER_API_KEY = ""
# WEATHER_API_URL = "https://api.weatherapi.com/v1"

# ==============================================================================
# UI Settings
# ==============================================================================
DARK_MODE = True  # Use dark theme if True, light theme otherwise
FONT_FAMILY = "Helvetica"  # Default font family for UI elements

# --- Font Sizes (in points) ---
TIME_FONT_SIZE_BASE = 270  # Base size for time display
TIME_FONT_SIZE_INCREASE = 40  # Amount added for the large time display
DATE_FONT_SIZE_BASE = 40  # Base size for date elements (weekday, month/year)
DATE_DAY_FONT_SIZE_INCREASE = 100  # Amount added for the large day number
WEATHER_FONT_SIZE = 40  # For current weather titles/values
FORECAST_FONT_SIZE = 45  # For forecast text elements
STATUS_INDICATOR_FONT_SIZE = 14  # For connection/API status labels

# --- Padding (in pixels) ---
# General padding between major sections (e.g., top/bottom frames)
SECTION_PADDING_X = 5
SECTION_PADDING_Y = 5
# Padding within sections/frames (e.g., around temp/humidity boxes)
ELEMENT_PADDING_X = 5
ELEMENT_PADDING_Y = 5
# Fine-grained padding specifically for text elements within their containers
TEXT_PADDING_X = 5
TEXT_PADDING_Y = 2

# --- Sizes (in pixels) ---
FORECAST_ICON_SIZE = (96, 96)  # (width, height) for forecast icons
CONNECTION_FRAME_HEIGHT = 30  # Height of the top connection status bar (Increased from 10)

# --- Colors ---
# Theme colors (Note: These might be overridden by CustomTkinter's theme)
BG_COLOR = "#1E1E1E"  # General background color (if not using theme)
TEXT_COLOR = "#FFFFFF"  # General text color
ACCENT_COLOR = "#3498DB"  # Accent color (e.g., for highlights)
SECONDARY_BG_COLOR = "#2D2D2D"  # Background for sub-frames/elements

# Specific UI element colors
NO_CONNECTION_COLOR = "#FF5555"  # Background for 'No Connection' indicator
API_LIMIT_COLOR = "#FFA500"  # Background for 'API Limit' indicator
API_ERROR_COLOR = "#FF0000"  # Background for 'API Error' indicator (e.g., red)
STATUS_TEXT_COLOR = "#FFFFFF"  # Text color for status indicators

# --- Corner Radii (in pixels) ---
STATUS_INDICATOR_CORNER_RADIUS = 5  # Corner radius for status indicators

# ==============================================================================
# Mock Data Settings
# ==============================================================================
# Use mock data for testing UI without making live API calls
USE_MOCK_DATA = False
