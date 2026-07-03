"""
Weather Icon Handling Utility for the Weather Display Application.

This module provides the `WeatherIconHandler` class, which is responsible for
managing weather icons used in the application's GUI. It handles:
- Mapping weather icon codes to descriptive names and local filenames.
- Determining the correct local path for an icon based on its code.
- Loading icon images from files into `customtkinter.CTkImage` objects suitable
  for display, handling resizing.
- Caching loaded `CTkImage` objects in memory to improve performance and avoid
  redundant disk I/O and image processing.
- Providing fallback logic for unknown or missing icon codes (defaulting to a
  sunny or clear night icon based on the time of day).
"""

# Standard library imports
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

# Third-party imports
import customtkinter as ctk # For the CTkImage object used in the GUI

# Local application imports
# No direct config needed, but relies on helpers for loading
# from ..utils.helpers import load_image # Import moved inside method to avoid circular dependency if helpers imports this

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

class WeatherIconHandler:
    """
    Manages weather icons: mapping codes, loading, and caching.

    This class centralizes all logic related to weather icons. It uses a predefined
    mapping (`ICON_MAPPING`) from numeric weather icon codes to internal names and
    provides loaded `CTkImage` objects suitable for the CustomTkinter GUI,
    complete with caching.

    Attributes:
        ICON_MAPPING (Dict[int, Dict[str, str]]): A class-level dictionary mapping
            weather icon codes (int) to dictionaries containing an internal
            'name' (used for filenames) and a 'description' (for reference).
        icon_dir (str): The absolute path to the local directory where weather
                        icon image files (.png) are stored.
        icon_cache (Dict[str, ctk.CTkImage]): An in-memory cache storing loaded
            `CTkImage` objects. Keys are strings combining the icon code and
            requested size (e.g., "1_64x64") to allow caching of different sizes.
    """

    # Define the base directory relative to this file's location where icons are stored.
    # Assumes icon_handler.py is in weather_display/utils/
    _MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    _PACKAGE_DIR = os.path.dirname(_MODULE_DIR)
    _ICON_BASE_DIR = os.path.join(_PACKAGE_DIR, "assets", "weather_icons")
    logger.debug(f"Icon base directory set to: {_ICON_BASE_DIR}")

    # --- Weather Icon Code Mapping ---
    # These codes match the bundled local icon filenames and are used as the
    # display's internal icon vocabulary.
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

    def __init__(self) -> None:
        """
        Initializes the WeatherIconHandler.

        Sets the icon directory path and ensures it exists. Initializes an empty
        dictionary to cache loaded `CTkImage` objects.
        """
        self.icon_dir: str = self._ICON_BASE_DIR
        # Ensure the icon directory exists, creating it if necessary.
        try:
            os.makedirs(self.icon_dir, exist_ok=True)
            logger.info(f"Icon directory set to: {self.icon_dir}")
        except OSError as e:
            logger.error(f"Failed to create icon directory '{self.icon_dir}': {e}. Icons may fail to load.")
            # Proceed, but loading might fail later.

        # Initialize cache for loaded CTkImage objects to avoid redundant loading.
        self.icon_cache: Dict[str, ctk.CTkImage] = {}
        logger.debug("Initialized empty icon cache.")

    def get_icon_path(self, icon_code: Optional[int]) -> Optional[str]:
        """
        Gets the absolute file path for a weather icon based on its code.

        Handles unknown or None codes by defaulting to a sunny (day) or clear
        (night) icon based on the current time. Icons are loaded only from the
        bundled local asset directory.

        Args:
            icon_code (Optional[int]): The numeric weather icon code (1-44), or None.

        Returns:
            Optional[str]: The absolute path to the local icon file (.png) if it exists.
                           Returns None if the file is missing.
        """
        original_code = icon_code # Store for logging purposes

        # --- Determine Effective Icon Code (Handle None/Unknown) ---
        if icon_code is None or icon_code not in self.ICON_MAPPING:
            # Default logic: Choose sunny (1) or clear night (33) based on time
            is_day = 6 <= datetime.now().hour < 18
            default_code = 1 if is_day else 33
            logger.warning(
                f"Icon code '{original_code}' is unknown or None. "
                f"Defaulting to {'day (Sunny)' if is_day else 'night (Clear)'} icon "
                f"(code: {default_code})."
            )
            icon_code = default_code # Use the default code for further processing

        # --- Get Icon Info and Construct Path ---
        icon_info = self.ICON_MAPPING.get(icon_code)
        # This check is a safeguard; should always succeed due to default logic above.
        if not icon_info:
             logger.error(f"CRITICAL: Failed to find icon info even for default code: {icon_code}. Cannot proceed.")
             return None
        icon_name = icon_info["name"]

        # Construct the expected filename (e.g., "01_sunny.png")
        filename = f"{icon_code:02d}_{icon_name}.png" # Pad code with leading zero
        icon_path = os.path.join(self.icon_dir, filename)
        logger.debug(f"Determined icon path for code {icon_code}: {icon_path}")

        # --- Check Existence ---
        if not os.path.exists(icon_path):
            logger.error(f"Icon file '{filename}' not found locally at {icon_path}.")
            return None

        logger.debug(f"Icon file exists at: {icon_path}")
        return icon_path

    def get_icon_by_condition(self, condition_text: Optional[str]) -> Optional[str]:
        """
        Gets the icon path based on a weather condition text description (experimental).

        Attempts to find a matching icon code by comparing the input `condition_text`
        (case-insensitive) against the 'description' field in the `ICON_MAPPING`.
        It prioritizes exact matches first, then falls back to checking if the input
        text is a substring of any known description. This method might be less
        reliable than using direct icon codes from the API.

        Args:
            condition_text (Optional[str]): The weather condition text description
                                            (e.g., "Sunny", "Partly Cloudy").

        Returns:
            Optional[str]: The absolute path to the corresponding icon file if a match
                           is found (using `get_icon_path` which handles defaults).
                           Returns the path to a default icon if no match is found, or
                           None if the default icon process also fails.
        """
        if not condition_text:
            logger.warning("get_icon_by_condition called with no condition text. Using default icon.")
            # Delegate to get_icon_path with None code for default handling
            return self.get_icon_path(None)

        condition_lower = condition_text.lower().strip()
        logger.debug(f"Attempting to find icon for condition text: '{condition_text}'")

        # --- Pass 1: Exact Match ---
        for code, info in self.ICON_MAPPING.items():
            if info["description"].lower() == condition_lower:
                logger.debug(f"Found exact description match for '{condition_text}': code {code}")
                return self.get_icon_path(code)

        # --- Pass 2: Partial Match (Substring) ---
        # Be cautious with this, as it might lead to incorrect matches (e.g., "Cloudy" matching "Mostly Cloudy")
        # Consider refining this logic if needed (e.g., prioritize longer matches).
        logger.debug("No exact match found, trying partial description match...")
        for code, info in self.ICON_MAPPING.items():
            if condition_lower in info["description"].lower():
                 logger.debug(f"Found partial description match for '{condition_text}' in '{info['description']}': code {code}")
                 return self.get_icon_path(code)

        # --- Fallback: No Match Found ---
        logger.warning(
            f"No icon mapping (exact or partial) found for condition text: '{condition_text}'. "
            f"Using default day/night icon."
        )
        # Delegate to get_icon_path with None code for default handling
        return self.get_icon_path(None)

    def load_icon(
        self,
        icon_code: Optional[int],
        size: Tuple[int, int] = (64, 64) # Default size if not specified
    ) -> Optional[ctk.CTkImage]:
        """
        Loads and returns a weather icon as a `CTkImage` object for GUI display.

        Checks an internal cache (`self.icon_cache`) for an already loaded icon
        matching the code and size. If not found:
        1. Gets the icon's file path using `get_icon_path` (handles defaults).
        2. Loads the image from the path using the `load_image` helper function.
        3. Caches the resulting `CTkImage` object.
        4. Returns the `CTkImage`.

        Args:
            icon_code (Optional[int]): The numeric weather icon code (1-44), or None
                                       (will trigger default icon logic).
            size (Tuple[int, int]): The desired (width, height) tuple for the icon image.
                                    Defaults to (64, 64).

        Returns:
            Optional[ctk.CTkImage]: A `CTkImage` object ready for display in a
                                    CustomTkinter widget, resized to the specified `size`.
                                    Returns None if the icon cannot be found or loaded.
        """
        # Determine the effective code for caching (handles None/invalid input)
        effective_code = icon_code
        if icon_code is None or icon_code not in self.ICON_MAPPING:
            is_day = 6 <= datetime.now().hour < 18
            effective_code = 1 if is_day else 33
            logger.debug(f"load_icon using effective code {effective_code} for input {icon_code}")
        else:
             logger.debug(f"load_icon called for code {icon_code} with size {size}")


        # Generate a unique cache key based on the effective code and requested size
        cache_key = f"{effective_code}_{size[0]}x{size[1]}"

        # --- 1. Check Cache ---
        if cache_key in self.icon_cache:
            logger.debug(f"Returning cached CTkImage for key: {cache_key}")
            return self.icon_cache[cache_key]

        # --- 2. Get Icon Path (Handles Defaults) ---
        logger.debug(f"Icon not in cache. Getting path for original code: {icon_code}")
        icon_path = self.get_icon_path(icon_code)
        if not icon_path:
            # get_icon_path already logged the error
            logger.error(f"Failed to get icon path for code {icon_code}. Cannot load icon.")
            return None

        # --- 3. Load Image using Helper ---
        # Import dynamically to potentially avoid circular dependency if helpers imports this module
        try:
            from ..utils.helpers import load_image as load_image_helper
        except ImportError:
             logger.critical("CRITICAL: Could not import load_image from weather_display.utils.helpers. Cannot load icons.")
             return None

        logger.debug(f"Loading image from path '{icon_path}' with size {size}...")
        icon_image: Optional[ctk.CTkImage] = load_image_helper(icon_path, size=size)

        # --- 4. Cache and Return ---
        if icon_image:
            logger.debug(f"Successfully loaded icon. Caching with key: {cache_key}")
            self.icon_cache[cache_key] = icon_image # Add to cache
            return icon_image
        else:
            # load_image_helper should have logged the error
            logger.error(f"Failed to load CTkImage from path: {icon_path}")
            return None


    def verify_all_icons(self) -> int:
        """
        Verifies local icons defined in `ICON_MAPPING`.

        The app is IMS-only and uses bundled local assets, so icon management
        is a local packaging check rather than a network download step.

        Returns:
            int: The number of expected icon files found locally.
        """
        found_count = 0
        logger.info(f"Verifying bundled icons in directory: {self.icon_dir}...")

        for icon_code, icon_info in self.ICON_MAPPING.items():
            filename = f"{icon_code:02d}_{icon_info['name']}.png"
            icon_path = os.path.join(self.icon_dir, filename)
            if os.path.exists(icon_path):
                found_count += 1
            else:
                logger.warning(f"Bundled icon missing: {filename}")

        logger.info(f"Finished icon verification. Found {found_count} bundled icons.")
        return found_count

# Example usage (if run directly)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # Enable detailed logging for testing
    print("--- Testing WeatherIconHandler ---")
    handler = WeatherIconHandler()

    print(f"\nIcon Directory: {handler.icon_dir}")

    print("\n--- Testing get_icon_path ---")
    path_sunny = handler.get_icon_path(1)
    print(f"Path for code 1 (Sunny): {path_sunny}")
    path_unknown = handler.get_icon_path(999) # Unknown code
    print(f"Path for code 999 (Unknown): {path_unknown}")
    path_none = handler.get_icon_path(None) # None code
    print(f"Path for code None: {path_none}")

    print("\n--- Testing get_icon_by_condition ---")
    path_cond_sunny = handler.get_icon_by_condition("Sunny")
    print(f"Path for condition 'Sunny': {path_cond_sunny}")
    path_cond_rain = handler.get_icon_by_condition("Light Rain Shower") # Partial match?
    print(f"Path for condition 'Light Rain Shower': {path_cond_rain}")
    path_cond_unknown = handler.get_icon_by_condition("Weird Weather")
    print(f"Path for condition 'Weird Weather': {path_cond_unknown}")

    # Note: Testing load_icon requires a running Tkinter instance usually.
    # print("\n--- Testing load_icon (requires GUI environment) ---")
    # try:
    #     # This might fail if run without a display server
    #     root = ctk.CTk() # Need a root window for CTkImage
    #     icon_obj = handler.load_icon(1, size=(32, 32))
    #     print(f"Loaded CTkImage for code 1 (32x32): {icon_obj}")
    #     icon_obj_cached = handler.load_icon(1, size=(32, 32))
    #     print(f"Loaded CTkImage from cache: {icon_obj_cached}")
    #     icon_obj_none = handler.load_icon(999)
    #     print(f"Loaded CTkImage for code 999: {icon_obj_none}")
    #     root.destroy()
    # except Exception as e:
    #     print(f"Could not test load_icon directly: {e}")

    print("\n--- Testing verify_all_icons ---")
    # found_count = handler.verify_all_icons()
    # print(f"Found {found_count} bundled icons.")

    print("\n--- Test Finished ---")
