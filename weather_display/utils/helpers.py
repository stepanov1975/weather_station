"""
General Utility Helper Functions for the Weather Display Application.

This module provides common utility functions used across the application:
- Checking for internet connectivity (`check_internet_connection`).
- Loading images for use with CustomTkinter (`load_image`).
- Formatting values for display.
- Wrapping localization functions for convenience (`get_day_name`).

Keeping these utilities separate promotes code reuse and maintainability.
"""

# Standard library imports
import os
import logging
import socket
from typing import Optional, Tuple, Union

from PIL import Image # For image loading/processing
import customtkinter as ctk # For CTkImage type

# Local application imports
from .. import config # Access application configuration (e.g., LANGUAGE)
from .localization import (
    get_translation, # For general translations (e.g., "N/A")
    get_day_name_localized, # For localized day names
)

# --- Logging Setup ---
# Get a logger instance specific to this module
logger = logging.getLogger(__name__)
# Note: Basic logging configuration should ideally happen once in the main entry point.


def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    """
    Checks for a basic internet connection by attempting a socket connection.

    Tries to establish a TCP connection to a known reliable host (like Google's
    public DNS server 8.8.8.8) on a standard port (like DNS port 53). This is
    a lightweight way to quickly assess if network connectivity likely exists.

    Args:
        host (str): The hostname or IP address to connect to. Defaults to "8.8.8.8".
        port (int): The port number to connect to. Defaults to 53 (DNS).
        timeout (int): The connection timeout duration in seconds. Defaults to 3.

    Returns:
        bool: True if the socket connection attempt is successful within the timeout,
              False otherwise (indicating likely no internet connection or a firewall block).
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            logger.debug("Internet connection check succeeded for %s:%s", host, port)
        return True
    except (OSError, socket.timeout) as exc:
        logger.debug("Internet connection check failed for %s:%s: %s", host, port, exc)
        return False


def load_image(path: str, size: Optional[Tuple[int, int]] = None) -> Optional[ctk.CTkImage]:
    """
    Loads an image file using PIL and prepares it as a CTkImage object.

    This function is specifically designed for use with the CustomTkinter library.
    It opens an image file from the given path, optionally resizes it, and then
    wraps it in a `customtkinter.CTkImage` object, which handles light/dark mode
    variants (though currently uses the same image for both) and HighDPI scaling.

    Args:
        path (str): The absolute or relative file path to the image file.
        size (Optional[Tuple[int, int]]): An optional tuple specifying the desired
                                          (width, height) in pixels. If provided,
                                          the image will be resized accordingly by
                                          CTkImage. If None, the image's original
                                          dimensions are used.

    Returns:
        Optional[ctk.CTkImage]: A CTkImage object ready for use in a CustomTkinter
                                widget if loading is successful. Returns None if the
                                file is not found or if any error occurs during
                                image processing.
    """
    if not os.path.exists(path):
        logger.error(f"Cannot load image: File not found at path: {path}")
        return None
    try:
        logger.debug(f"Loading image from path: {path} with target size: {size}")
        # Open the image using Pillow (PIL)
        img_pil = Image.open(path)

        # Determine the size for CTkImage
        target_size = size if size else (img_pil.width, img_pil.height)

        # Create the CTkImage object.
        # For simplicity, we use the same PIL image for both light and dark modes.
        # If separate light/dark mode images were available, they would be passed
        # to light_image and dark_image respectively.
        ctk_image = ctk.CTkImage(
            light_image=img_pil,
            dark_image=img_pil, # Use the same image for dark mode
            size=target_size # CTkImage handles the resizing internally
        )
        logger.debug(f"Successfully loaded image '{os.path.basename(path)}' as CTkImage.")
        return ctk_image
    except FileNotFoundError:
        # This case is technically handled by the os.path.exists check above,
        # but kept as a safeguard.
        logger.error(f"Image file not found during PIL loading: {path}")
        return None
    except Exception as e:
        # Catch potential errors from PIL (e.g., corrupted file) or CTkImage creation
        logger.error(f"Failed to load or process image {path}: {e}", exc_info=True)
        return None


# --- Formatting Functions ---

def format_temperature(temp: Optional[Union[float, int]]) -> str:
    """
    Formats a temperature value (assumed Celsius) into a display string.

    Rounds the temperature to the nearest integer and appends the degree symbol
    and "C". Handles None input by returning a localized "Not Available" string.

    Args:
        temp (Optional[Union[float, int]]): The temperature value in Celsius,
                                             or None if the value is unavailable.

    Returns:
        str: A formatted temperature string like "23°C", or a localized "N/A"
             string if the input `temp` is None.
    """
    if temp is None:
        # Use the localization utility to get the appropriate "N/A" text
        return get_translation('not_available', config.LANGUAGE)
    try:
        # Round the temperature to the nearest integer and format
        return f"{int(round(float(temp)))}°C"
    except (ValueError, TypeError) as e:
         logger.warning(f"Could not format temperature value '{temp}': {e}")
         return get_translation('not_available', config.LANGUAGE)


# --- Localization Wrappers ---
# These functions provide a layer over the core localization utilities,
# potentially simplifying calls from other modules by automatically passing
# the configured language.

def get_day_name(date_str: Optional[str]) -> str:
    """
    Gets the localized full day name (e.g., "Monday") from a date string.

    Parses the input date string (expected ISO 8601 format like
    "YYYY-MM-DDTHH:MM:SS+ZZ:ZZ" or "YYYY-MM-DD") and returns the
    corresponding day name translated into the language specified in `config.py`.

    Args:
        date_str (Optional[str]): An ISO 8601 formatted date string, or a simple
                                  'YYYY-MM-DD' string. Can be None.

    Returns:
        str: The localized full name of the day of the week (e.g., 'Monday',
             'Понедельник'), or a localized "N/A" string if the input is None
             or cannot be parsed.
    """
    if date_str is None:
        return get_translation('not_available', config.LANGUAGE)
    # Pass the date string and configured language to the core localization function
    return get_day_name_localized(date_str, config.LANGUAGE)
