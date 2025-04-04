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
WEATHER_UPDATE_INTERVAL_MINUTES = 30  # For weather data

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
