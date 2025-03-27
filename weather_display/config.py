"""
Configuration settings for the Weather Display application.
"""

# Application settings
APP_TITLE = "Weather Display"
LANGUAGE = "ru"  # Language code: 'en' for English, 'ru' for Russian
APP_WIDTH = 1440
APP_HEIGHT = 810
FULLSCREEN = True
UPDATE_INTERVAL_SECONDS = 1  # For time display
WEATHER_UPDATE_INTERVAL_MINUTES = 30  # For weather data

# Location settings
LOCATION = "Hadera,Israel"

# API settings
WEATHER_API_KEY = ""  # To be filled by the user
WEATHER_API_URL = "https://api.weatherapi.com/v1"

# UI settings
DARK_MODE = True
FONT_FAMILY = "Helvetica"
TIME_FONT_SIZE = 100
DATE_FONT_SIZE = 40
WEATHER_FONT_SIZE = 28  # Increased from 18
FORECAST_FONT_SIZE = 32  # Increased from 24

# Colors (dark theme)
BG_COLOR = "#1E1E1E"
TEXT_COLOR = "#FFFFFF"
ACCENT_COLOR = "#3498DB"
SECONDARY_BG_COLOR = "#2D2D2D"

# Mock data for testing without API
USE_MOCK_DATA = False
