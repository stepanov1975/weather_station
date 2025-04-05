"""
Utility helper functions for the Weather Display application.

This module provides common utility functions used across the application,
including network requests with retries, image handling (downloading, loading),
text formatting, and internet connectivity checks.
"""

# Standard library imports
import os
import logging
import socket
import time
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# Third-party imports
import requests
from PIL import Image
import customtkinter as ctk

# Local application imports
from .. import config
from .localization import (
    get_translation,
    get_day_name_localized,
    get_air_quality_text_localized
)

# Attempt to import ImageTk, handle gracefully if unavailable (for non-GUI contexts)
try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None  # Will be None if Pillow is not fully installed or in use

# --- Logging Setup ---
# NOTE: It's generally better practice to configure logging once in the main
# application entry point (e.g., main.py or run_weather_display.py) rather
# than in a utility module. Leaving it here for now based on original structure.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('weather_display.log')
    ]
)
logger = logging.getLogger(__name__)

# --- Network Functions ---

def fetch_with_retry(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    timeout: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON data from a URL with exponential backoff retry logic.

    Handles common request exceptions and timeouts. Includes specific handling
    for AccuWeather's 'ServiceUnavailable' error, often indicating API limits.

    Args:
        url: The URL to fetch data from.
        params: Optional dictionary of URL parameters.
        max_retries: Maximum number of retry attempts.
        timeout: Request timeout in seconds.

    Returns:
        A dictionary containing the JSON response if successful,
        a specific error dictionary if AccuWeather limit is hit,
        or None if all retries fail or another error occurs.
    """
    retry_count = 0
    while retry_count < max_retries:
        response: Optional[requests.Response] = None
        try:
            # Construct the full URL with parameters for logging purposes
            full_url = url
            if params:
                # Ensure API key isn't logged if present (optional security)
                log_params = params.copy()
                if 'apikey' in log_params:
                    log_params['apikey'] = '***REDACTED***'
                full_url += '?' + urllib.parse.urlencode(log_params)
            logger.info(f"Making API request to: {full_url}")

            response = requests.get(url, params=params, timeout=timeout)

            # Check for specific AccuWeather API limit error *before* raise_for_status.
            # Common HTTP status codes for rate limiting/service issues.
            if response.status_code in [403, 429, 503]:
                try:
                    error_data = response.json()
                    # Check if the response JSON matches AccuWeather's known error format
                    if isinstance(error_data, dict) and error_data.get('Code') == 'ServiceUnavailable':
                        logger.warning(
                            f"AccuWeather API request limit likely exceeded "
                            f"(HTTP {response.status_code}). "
                            f"Response: {error_data.get('Message')}"
                        )
                        # Return the specific error structure for the caller to handle
                        return error_data
                except requests.exceptions.JSONDecodeError:
                    # If the error response body isn't JSON, proceed to general error handling
                    logger.warning(
                        f"Received HTTP {response.status_code} but response "
                        f"was not valid JSON. Body: {response.text[:100]}..."
                    )
                    # Fall through to raise_for_status

            # If no specific error was caught, check for other HTTP errors
            response.raise_for_status()
            return response.json()

        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            error_message = f"{e}"
            if response is not None:
                # Include status code in error if available
                error_message = f"HTTP {response.status_code}: {e}"

            retry_count += 1
            if retry_count >= max_retries:
                logger.error(
                    f"Failed to fetch {url} after {max_retries} attempts: "
                    f"{error_message}"
                )
                return None  # Failed after all retries

            # Exponential backoff: wait 1s, 2s, 4s... before retrying
            wait_time = 2 ** (retry_count - 1)
            logger.warning(
                f"Request failed ({error_message}). Retrying {retry_count}/"
                f"{max_retries} after {wait_time}s..."
            )
            time.sleep(wait_time)

    return None  # Should not be reached if loop condition is correct, but acts as fallback


def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    """
    Check for a basic internet connection by attempting a socket connection.

    Tries to connect to a known reliable host (like Google's public DNS server)
    on a standard port (like DNS port 53).

    Args:
        host: The hostname or IP address to connect to.
        port: The port number to connect to.
        timeout: Connection timeout in seconds.

    Returns:
        True if the connection attempt is successful, False otherwise.
    """
    try:
        socket.setdefaulttimeout(timeout)
        # Create a socket, connect, and immediately close it.
        # AF_INET = IPv4, SOCK_STREAM = TCP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
        return True
    except (socket.error, socket.timeout) as e:
        logger.debug(f"Internet connection check failed: {e}")
        return False


# --- Image Handling Functions ---

def download_image(url: str, cache_dir: str, filename: Optional[str] = None) -> Optional[str]:
    """
    Download an image from a URL and save it to a local cache directory.

    Skips download if the file already exists in the cache. Handles URLs
    that might be missing the 'https:' prefix.

    Args:
        url: The URL of the image to download.
        cache_dir: The directory path where the image should be saved.
        filename: Optional specific filename to use. If None, extracts from URL.

    Returns:
        The full path to the cached image file if successful, otherwise None.
    """
    os.makedirs(cache_dir, exist_ok=True)

    # Prepend 'https:' if the URL starts with '//'
    if url.startswith('//'):
        url = f"https:{url}"

    # Determine the filename if not provided
    if not filename:
        try:
            # Extract filename from the URL path
            filename = os.path.basename(urllib.parse.urlparse(url).path)
            if not filename: # Handle cases like 'domain.com/'
                 raise ValueError("Could not determine filename from URL path")
        except Exception as e:
             logger.error(f"Could not determine filename from URL '{url}': {e}")
             # Fallback filename or return None? Returning None is safer.
             return None


    cache_path = os.path.join(cache_dir, filename)

    # Check if the image is already cached
    if os.path.exists(cache_path):
        logger.debug(f"Image already cached: {cache_path}")
        return cache_path

    # Download the image
    try:
        logger.info(f"Downloading image from {url} to {cache_path}")
        response = requests.get(url, stream=True, timeout=15) # Added timeout
        response.raise_for_status()

        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Successfully downloaded image: {filename}")
        return cache_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download image {url}: {e}")
        # Clean up potentially incomplete file if download failed
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except OSError as remove_error:
                logger.error(f"Could not remove incomplete file {cache_path}: {remove_error}")
        return None
    except Exception as e: # Catch other potential errors (e.g., file writing)
        logger.error(f"An unexpected error occurred downloading {url}: {e}")
        return None


def load_image(path: str, size: Optional[Tuple[int, int]] = None) -> Optional[ctk.CTkImage]:
    """
    Load an image file using PIL and prepare it as a CTkImage for CustomTkinter.

    Optionally resizes the image. Uses CTkImage for better HighDPI support
    compared to standard Tkinter PhotoImage.

    Args:
        path: The file path to the image.
        size: Optional tuple (width, height) to resize the image to.

    Returns:
        A CTkImage object if successful, otherwise None.
    """
    if not os.path.exists(path):
        logger.error(f"Image file not found at path: {path}")
        return None
    try:
        # Open the image using PIL
        img_light = Image.open(path)
        # For CTkImage, dark_image can be the same if no separate dark version exists
        img_dark = img_light.copy()

        # Create the CTkImage object
        ctk_image = ctk.CTkImage(
            light_image=img_light,
            dark_image=img_dark,
            size=size if size else (img_light.width, img_light.height) # Use original size if None
        )
        return ctk_image
    except FileNotFoundError:
        # This case is technically handled above, but kept for robustness
        logger.error(f"Image file not found during loading: {path}")
        return None
    except Exception as e:
        logger.error(f"Failed to load image {path}: {e}", exc_info=True)
        return None


# --- Formatting Functions ---

def format_temperature(temp: Optional[float]) -> str:
    """
    Format a temperature value (Celsius) into a display string.

    Rounds the temperature to the nearest integer and appends "°C".
    Returns a localized "N/A" string if the input temperature is None.

    Args:
        temp: The temperature in Celsius, or None.

    Returns:
        Formatted temperature string (e.g., "23°C") or a localized "N/A".
    """
    if temp is None:
        # Use translation function for "Not Available" text
        return get_translation('not_available', config.LANGUAGE)
    return f"{int(round(temp))}°C"


# --- Localization Wrappers ---
# These functions simply wrap the localization functions for convenience,
# potentially allowing for easier modification or extension later.

# TODO: Review if get_air_quality_text is still used. The comment suggests
#       it might be based on an old API index and could be deprecated/removed.
def get_air_quality_text(index: int) -> str:
    """
    Convert air quality index to descriptive text (potentially deprecated).

    Note: The docstring comment indicates this might be based on an old,
          unused index system. Verify usage before relying on this function.

    Args:
        index: Air quality index value.

    Returns:
        Localized descriptive text for the air quality.
    """
    return get_air_quality_text_localized(index, config.LANGUAGE)


def get_day_name(date_str: str) -> str:
    """
    Get the localized day name from a date string.

    Assumes the input date string is in 'YYYY-MM-DD' format.

    Args:
        date_str: Date string in 'YYYY-MM-DD' format.

    Returns:
        Localized full day name (e.g., 'Monday', 'Понедельник').
    """
    return get_day_name_localized(date_str, config.LANGUAGE)
