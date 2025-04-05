"""
Utilities Package for Weather Display.

This package contains various helper modules for tasks such as localization,
API request handling, image processing, icon management, etc.
"""

# Optionally expose specific utility classes/functions at the package level.
# Example: Making WeatherIconHandler available as `from weather_display.utils import WeatherIconHandler`
# However, direct imports like `from weather_display.utils.icon_handler import WeatherIconHandler`
# are often clearer. Decide based on package usage patterns.
from .icon_handler import WeatherIconHandler

# You could add other commonly used utilities here if desired, e.g.:
# from .helpers import fetch_with_retry
# from .localization import get_translation
