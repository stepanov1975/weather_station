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
ACCUWEATHER_LANGUAGE = "en-us"  # Language code for AccuWeather API
APP_WIDTH = 1440  # Initial window width in pixels
APP_HEIGHT = 810  # Initial window height in pixels
FULLSCREEN = True  # Run in fullscreen mode if True
# Update interval for the time display (affects clock refresh rate)
UPDATE_INTERVAL_SECONDS = 1
# Update interval for fetching new weather data from the IMS API
IMS_UPDATE_INTERVAL_MINUTES = 10
# Update interval for fetching new weather data from the AccuWeather API
ACCUWEATHER_UPDATE_INTERVAL_MINUTES = 120

# ==============================================================================
# Location Settings
# ==============================================================================
# Location query string (retained for potential future use or display)
LOCATION = "Hadera,Israel"

# ==============================================================================
# API Settings (IMS - Israel Meteorological Service)
# ==============================================================================
# Station name for the IMS service (e.g., "En Hahoresh", "Tel Aviv Coast")
IMS_STATION_NAME = "En Hahoresh"
# IMS service URL (defined within the service class, but kept here for reference)
# IMS_URL = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"

# ==============================================================================
# API Settings (AccuWeather)
# ==============================================================================
# Base URL for the AccuWeather API endpoints
ACCUWEATHER_BASE_URL = "http://dataservice.accuweather.com"
# AccuWeather API Key - **IMPORTANT**: Best practice is to set this via environment
# variable (ACCUWEATHER_API_KEY) rather than hardcoding it here.
# The AccuWeatherClient will prioritize the key passed via command line (--api-key),
# then this config value, then the environment variable.
ACCUWEATHER_API_KEY = os.environ.get('ACCUWEATHER_API_KEY') # Read from environment


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
# Note: Mock data structure might need adjustment for IMS service
USE_MOCK_DATA = False
