"""
Weather Icon Handler for the Weather Display application.

This module provides the `WeatherIconHandler` class, responsible for mapping
AccuWeather icon codes to local image files, downloading missing icons,
and loading icons for display in the GUI.
"""

# Standard library imports
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

# Third-party imports
import requests
from PIL import Image
import customtkinter as ctk

# Local application imports
# (No direct config needed here, settings like size are passed in)

logger = logging.getLogger(__name__)

class WeatherIconHandler:
    """
    Manages weather icons based on AccuWeather icon codes.

    Handles mapping codes to local file paths, downloading missing icons from
    AccuWeather, caching loaded CTkImage objects, and providing methods to
    retrieve icon paths or loaded images.

    Attributes:
        ICON_MAPPING (Dict[int, Dict[str, str]]): Class attribute mapping
            AccuWeather icon codes (int) to dictionaries containing 'name'
            (for filename) and 'description' (unused here, but for reference).
        icon_dir (str): Path to the local directory where icons are stored.
        icon_cache (Dict[str, ctk.CTkImage]): Cache for loaded CTkImage objects
            to avoid reloading from disk. Keys are formatted like "code_WxH".
    """

    # Base directory relative to the project root where icons are stored.
    _ICON_BASE_DIR = os.path.join("weather_display", "assets", "weather_icons")

    # AccuWeather icon codes mapping.
    # Reference: https://developer.accuweather.com/weather-icons
    # Maps API icon code (int) to internal name and description.
    ICON_MAPPING: Dict[int, Dict[str, str]] = {
        1: {"name": "sunny", "description": "Sunny"},
        2: {"name": "mostly_sunny", "description": "Mostly Sunny"},
        3: {"name": "partly_sunny", "description": "Partly Sunny"},
        4: {"name": "intermittent_clouds", "description": "Intermittent Clouds"},
        5: {"name": "hazy_sunshine", "description": "Hazy Sunshine"},
        6: {"name": "mostly_cloudy", "description": "Mostly Cloudy"},
        7: {"name": "cloudy", "description": "Cloudy"},
        8: {"name": "dreary", "description": "Dreary (Overcast)"},
        11: {"name": "fog", "description": "Fog"},
        12: {"name": "showers", "description": "Showers"},
        13: {"name": "mostly_cloudy_with_showers", "description": "Mostly Cloudy with Showers"},
        14: {"name": "partly_sunny_with_showers", "description": "Partly Sunny with Showers"},
        15: {"name": "t_storms", "description": "Thunderstorms"},
        16: {"name": "mostly_cloudy_with_t_storms", "description": "Mostly Cloudy with Thunderstorms"},
        17: {"name": "partly_sunny_with_t_storms", "description": "Partly Sunny with Thunderstorms"},
        18: {"name": "rain", "description": "Rain"},
        19: {"name": "flurries", "description": "Flurries"},
        20: {"name": "mostly_cloudy_with_flurries", "description": "Mostly Cloudy with Flurries"},
        21: {"name": "partly_sunny_with_flurries", "description": "Partly Sunny with Flurries"},
        22: {"name": "snow", "description": "Snow"},
        23: {"name": "mostly_cloudy_with_snow", "description": "Mostly Cloudy with Snow"},
        24: {"name": "ice", "description": "Ice"},
        25: {"name": "sleet", "description": "Sleet"},
        26: {"name": "freezing_rain", "description": "Freezing Rain"},
        29: {"name": "rain_and_snow", "description": "Rain and Snow"},
        30: {"name": "hot", "description": "Hot"},
        31: {"name": "cold", "description": "Cold"},
        32: {"name": "windy", "description": "Windy"},
        33: {"name": "clear_night", "description": "Clear (Night)"},
        34: {"name": "mostly_clear_night", "description": "Mostly Clear (Night)"},
        35: {"name": "partly_cloudy_night", "description": "Partly Cloudy (Night)"},
        36: {"name": "intermittent_clouds_night", "description": "Intermittent Clouds (Night)"},
        37: {"name": "hazy_moonlight", "description": "Hazy Moonlight"},
        38: {"name": "mostly_cloudy_night", "description": "Mostly Cloudy (Night)"},
        39: {"name": "partly_cloudy_with_showers_night", "description": "Partly Cloudy with Showers (Night)"},
        40: {"name": "mostly_cloudy_with_showers_night", "description": "Mostly Cloudy with Showers (Night)"},
        41: {"name": "partly_cloudy_with_t_storms_night", "description": "Partly Cloudy with Thunderstorms (Night)"},
        42: {"name": "mostly_cloudy_with_t_storms_night", "description": "Mostly Cloudy with Thunderstorms (Night)"},
        43: {"name": "mostly_cloudy_with_flurries_night", "description": "Mostly Cloudy with Flurries (Night)"},
        44: {"name": "mostly_cloudy_with_snow_night", "description": "Mostly Cloudy with Snow (Night)"}
    }

    def __init__(self):
        """Initialize the WeatherIconHandler."""
        self.icon_dir = self._ICON_BASE_DIR
        # Ensure the icon directory exists.
        os.makedirs(self.icon_dir, exist_ok=True)
        # Initialize cache for loaded CTkImage objects.
        self.icon_cache: Dict[str, ctk.CTkImage] = {}

    def get_icon_path(self, icon_code: Optional[int]) -> Optional[str]:
        """
        Get the file path for a weather icon based on the AccuWeather icon code.

        If the code is unknown or None, it defaults to a sunny (day) or
        clear (night) icon based on the current time. Downloads the icon
        if it's not found locally.

        Args:
            icon_code: AccuWeather icon code (integer 1-44) or None.

        Returns:
            The absolute path to the icon file, or None if the icon cannot
            be found or downloaded.
        """
        original_code = icon_code # Keep track for logging if needed

        # Handle unknown or missing icon codes by defaulting
        if icon_code is None or icon_code not in self.ICON_MAPPING:
            # Determine day (6 AM to 6 PM) or night
            is_day = 6 <= datetime.now().hour < 18
            default_code = 1 if is_day else 33 # 1: Sunny, 33: Clear Night
            logger.warning(
                f"Icon code '{original_code}' is unknown or None. "
                f"Defaulting to {'day' if is_day else 'night'} icon "
                f"(code: {default_code})."
            )
            icon_code = default_code

        # Retrieve icon details from the mapping
        icon_info = self.ICON_MAPPING.get(icon_code)
        # This check should ideally not fail due to the default logic above,
        # but added for robustness.
        if not icon_info:
             logger.error(f"Failed to find icon info even for default code: {icon_code}")
             return None
        icon_name = icon_info["name"]

        # Construct the expected filename (e.g., "01_sunny.png")
        filename = f"{icon_code:02d}_{icon_name}.png"
        icon_path = os.path.join(self.icon_dir, filename)

        # Download the icon if it doesn't exist locally
        if not os.path.exists(icon_path):
            logger.info(f"Icon '{filename}' not found locally. Attempting download.")
            if not self._download_icon(icon_code, icon_path):
                logger.error(f"Failed to download icon {icon_code} to {icon_path}.")
                return None # Download failed

        # Verify again after potential download attempt
        if os.path.exists(icon_path):
            return icon_path
        else:
            # Should ideally not happen if download reported success, but check anyway
            logger.error(f"Icon path {icon_path} still does not exist after download attempt.")
            return None

    def get_icon_by_condition(self, condition_text: Optional[str]) -> Optional[str]:
        """
        Get the icon path based on a weather condition text description.

        Tries to find an icon code by matching the condition text (case-insensitive)
        against the descriptions in ICON_MAPPING. Prioritizes exact matches,
        then falls back to partial matches.

        Args:
            condition_text: Weather condition text (e.g., "Sunny", "Partly Cloudy").

        Returns:
            Path to the corresponding icon file, or path to a default icon
            if no match is found, or None if the default icon also fails.
        """
        if not condition_text:
            logger.warning("No condition text provided to get_icon_by_condition. Using default.")
            return self.get_icon_path(None) # Use default logic

        condition_lower = condition_text.lower()

        # Prioritize exact description match
        for code, info in self.ICON_MAPPING.items():
            if info["description"].lower() == condition_lower:
                logger.debug(f"Exact match found for '{condition_text}': code {code}")
                return self.get_icon_path(code)

        # Fallback to partial description match (substring check)
        # This might be less accurate if descriptions overlap significantly.
        for code, info in self.ICON_MAPPING.items():
            if condition_lower in info["description"].lower():
                 logger.debug(f"Partial match found for '{condition_text}': code {code}")
                 return self.get_icon_path(code)

        # If no match found, use the default icon logic
        logger.warning(
            f"No icon mapping found for condition: '{condition_text}'. "
            f"Using default icon."
        )
        return self.get_icon_path(None) # Default logic handles day/night

    def load_icon(
        self,
        icon_code: Optional[int],
        size: Tuple[int, int] = (64, 64)
    ) -> Optional[ctk.CTkImage]:
        """
        Load and return a weather icon as a CTkImage object, suitable for GUI display.

        Checks an internal cache first. If not cached, retrieves the icon path
        (downloading if necessary), loads the image using PIL, creates a
        CTkImage, caches it, and returns it.

        Args:
            icon_code: AccuWeather icon code (integer 1-44) or None.
            size: Tuple (width, height) to resize the icon to.

        Returns:
            A CTkImage object ready for display, or None if the icon cannot
            be found, downloaded, or loaded.
        """
        # Generate a cache key based on code and size
        # Use a default code if None is passed, consistent with get_icon_path
        effective_code = icon_code if icon_code is not None and icon_code in self.ICON_MAPPING else (1 if 6 <= datetime.now().hour < 18 else 33)
        cache_key = f"{effective_code}_{size[0]}x{size[1]}"

        # Check cache first
        if cache_key in self.icon_cache:
            logger.debug(f"Returning cached icon for key: {cache_key}")
            return self.icon_cache[cache_key]

        # Get the icon file path (handles defaults and downloads)
        icon_path = self.get_icon_path(icon_code)
        if not icon_path: # get_icon_path already logged errors
            return None

        # Load the image using the helper function from helpers.py
        # This assumes the load_image function exists and works correctly.
        # If helpers.py is removed or changed, this needs adjustment.
        try:
            # We need the load_image function from helpers for CTkImage creation
            from ..utils.helpers import load_image as load_image_helper
            icon = load_image_helper(icon_path, size=size)

            if icon:
                # Cache the successfully loaded icon
                logger.debug(f"Caching new icon for key: {cache_key}")
                self.icon_cache[cache_key] = icon
                return icon
            else:
                # load_image_helper should log its own errors
                return None
        except ImportError:
             logger.error("Could not import load_image from helpers. Cannot load icon.")
             return None
        except Exception as e:
            # Catch any unexpected error during loading/caching
            logger.error(f"Unexpected error loading icon {icon_path}: {e}", exc_info=True)
            return None


    def _download_icon(self, icon_code: int, save_path: str) -> bool:
        """
        Internal helper to download a specific AccuWeather icon image.

        Constructs the URL based on the icon code and saves the image to the
        specified path.

        Args:
            icon_code: The AccuWeather icon code (1-44).
            save_path: The full local file path to save the downloaded image.

        Returns:
            True if download and save were successful, False otherwise.
        """
        # Format icon code with leading zero if needed (e.g., 1 -> 01)
        icon_str = f"{icon_code:02d}"
        # Construct the expected AccuWeather icon URL
        # Using the '-s' suffix for standard size icons.
        icon_url = f"https://developer.accuweather.com/sites/default/files/{icon_str}-s.png"

        try:
            logger.info(f"Downloading icon from {icon_url} to {save_path}")
            # Use stream=True for potentially large files, add timeout
            response = requests.get(icon_url, stream=True, timeout=15)
            response.raise_for_status() # Check for HTTP errors (4xx, 5xx)

            # Write the content to the file
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Successfully downloaded weather icon: {os.path.basename(save_path)}")
            return True

        except requests.exceptions.Timeout:
             logger.error(f"Timeout occurred while downloading icon {icon_url}")
             return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download icon {icon_url}: {e}")
            # Clean up potentially incomplete file if download failed
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                    logger.debug(f"Removed incomplete file: {save_path}")
                except OSError as remove_error:
                    logger.error(f"Could not remove incomplete file {save_path}: {remove_error}")
            return False
        except IOError as e:
             logger.error(f"Failed to save icon to {save_path}: {e}")
             return False
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred downloading icon {icon_url}: {e}", exc_info=True)
            return False

    def download_all_icons(self) -> int:
        """
        Attempt to download all icons defined in ICON_MAPPING if they don't exist locally.

        Iterates through all known icon codes and calls the internal download
        helper for each missing icon.

        Returns:
            The number of icons that were successfully downloaded in this run.
        """
        success_count = 0
        logger.info(f"Checking and downloading all missing icons to {self.icon_dir}...")
        for icon_code, icon_info in self.ICON_MAPPING.items():
            filename = f"{icon_code:02d}_{icon_info['name']}.png"
            icon_path = os.path.join(self.icon_dir, filename)

            if not os.path.exists(icon_path):
                if self._download_icon(icon_code, icon_path):
                    success_count += 1
                # _download_icon logs errors on failure

        logger.info(f"Finished icon download process. Successfully downloaded {success_count} new icons.")
        return success_count
