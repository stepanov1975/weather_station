"""
General Utility Helper Functions for the Weather Display Application.

This module provides a collection of common, reusable utility functions used
across different parts of the application. These functions encapsulate logic
for tasks such as:
- Making network requests with retry mechanisms (`fetch_with_retry`).
- Checking for internet connectivity (`check_internet_connection`).
- Downloading and caching images (`download_image`).
- Loading images for use with CustomTkinter (`load_image`).
- Formatting data for display (e.g., temperature `format_temperature`).
- Wrapping localization functions for convenience (`get_day_name`).

Keeping these utilities separate promotes code reuse and maintainability.
"""

# Standard library imports
import os
import logging
import socket
import time
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, Union, List # Added Union and List

# Third-party imports
import requests
from PIL import Image # For image loading/processing
import customtkinter as ctk # For CTkImage type

# Local application imports
from .. import config # Access application configuration (e.g., LANGUAGE)
from .localization import (
    get_translation, # For general translations (e.g., "N/A")
    get_day_name_localized, # For localized day names
    # get_air_quality_text_localized # This seems unused/deprecated, commented out
)

# Attempt to import ImageTk, handle gracefully if unavailable (e.g., server-side use)
try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None # Define as None if Pillow is not fully installed

# --- Logging Setup ---
# Get a logger instance specific to this module
logger = logging.getLogger(__name__)
# Note: Basic logging configuration should ideally happen once in the main entry point.


# --- Network Functions ---

def fetch_with_retry(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    timeout: int = 15 # Increased default timeout
) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    Fetches JSON data from a URL with exponential backoff retry logic.

    Attempts to retrieve data from the specified URL. If the request fails due
    to common network errors (timeouts, connection errors) or specific HTTP
    status codes indicating temporary issues, it retries the request up to
    `max_retries` times with increasing delays between attempts (exponential backoff).

    Handles specific AccuWeather 'ServiceUnavailable' errors (often indicating
    API rate limits) by returning a specific dictionary structure instead of None,
    allowing the caller to differentiate rate limit issues from other errors.

    Args:
        url (str): The URL endpoint to fetch data from.
        params (Optional[Dict[str, Any]]): A dictionary of URL parameters to include
                                           in the request. Defaults to None.
        max_retries (int): The maximum number of times to retry the request after
                           a failure. Defaults to 3.
        timeout (int): The request timeout in seconds for both connection and read.
                       Defaults to 15.

    Returns:
        Optional[Union[Dict[str, Any], List[Any]]]:
            - A dictionary or list containing the parsed JSON response if successful.
            - A specific dictionary `{'Code': 'ServiceUnavailable', ...}` if an
              AccuWeather API limit error is detected.
            - None if all retry attempts fail due to network errors, timeouts,
              or unhandled HTTP errors.
    """
    retry_count = 0
    last_exception: Optional[Exception] = None # Store last exception for logging

    while retry_count < max_retries:
        response: Optional[requests.Response] = None
        try:
            # Construct the full URL with parameters for logging, redacting API key
            full_url_log = url
            if params:
                log_params = params.copy()
                if 'apikey' in log_params:
                    log_params['apikey'] = '***REDACTED***'
                full_url_log += '?' + urllib.parse.urlencode(log_params)
            logger.info(f"Attempt {retry_count + 1}/{max_retries}: Requesting data from {full_url_log}")

            response = requests.get(url, params=params, timeout=timeout)

            # --- Handle Specific AccuWeather API Limit Error ---
            # Check common rate limit/service issue status codes *before* raise_for_status
            if response.status_code in [403, 429, 503]:
                try:
                    error_data = response.json()
                    # Check if the response JSON matches AccuWeather's known error format
                    if isinstance(error_data, dict) and error_data.get('Code') == 'ServiceUnavailable':
                        logger.warning(
                            f"AccuWeather API request limit likely exceeded or service unavailable "
                            f"(HTTP {response.status_code}). Response: {error_data.get('Message', 'No message')}"
                        )
                        # Return the specific error structure for the caller to handle distinctly
                        return error_data
                except requests.exceptions.JSONDecodeError:
                    # If the error response body isn't JSON, log and fall through to general error handling
                    logger.warning(
                        f"Received HTTP {response.status_code} (potential limit/error) but response "
                        f"was not valid JSON. Body: {response.text[:150]}..." # Log start of body
                    )
                    # Fall through to raise_for_status which will likely raise an error

            # --- Handle General HTTP Errors ---
            # If no specific error was caught above, check for other HTTP errors (4xx, 5xx)
            response.raise_for_status() # Raises HTTPError for bad status codes

            # --- Process Successful Response ---
            # If no exceptions were raised, parse the JSON response
            logger.debug(f"Request successful (HTTP {response.status_code}). Parsing JSON response.")
            # The response could be a dict or a list depending on the API endpoint
            json_response = response.json()
            return json_response

        except requests.exceptions.Timeout as e:
            last_exception = e
            logger.warning(f"Request timed out ({timeout}s): {e}")
            # Fall through to retry logic
        except requests.exceptions.ConnectionError as e:
             last_exception = e
             logger.warning(f"Connection error: {e}")
             # Fall through to retry logic
        except requests.exceptions.HTTPError as e:
             last_exception = e
             # Log HTTP errors that weren't the specific AccuWeather limit case
             logger.warning(f"HTTP error occurred: {e}")
             # Fall through to retry logic (might retry on 5xx errors)
        except requests.exceptions.RequestException as e:
            last_exception = e
            # Catch other potential request-related errors
            logger.warning(f"General request error: {e}")
            # Fall through to retry logic
        except requests.exceptions.JSONDecodeError as e:
             last_exception = e
             logger.error(f"Failed to decode JSON response from {url}. Status: {response.status_code if response else 'N/A'}. Error: {e}")
             # Don't retry on JSON decode errors, as the response is likely malformed
             return None # Return None immediately

        # --- Retry Logic ---
        retry_count += 1
        if retry_count < max_retries:
            # Exponential backoff: wait 1s, 2s, 4s... before retrying
            wait_time = 2 ** (retry_count - 1)
            logger.warning(
                f"Request failed. Retrying {retry_count}/{max_retries} after {wait_time}s..."
            )
            time.sleep(wait_time)
        else:
            # All retries failed
            logger.error(
                f"Failed to fetch data from {url} after {max_retries} attempts. "
                f"Last error: {last_exception}"
            )
            return None # Return None after all retries are exhausted

    # Fallback return (should theoretically not be reached if loop logic is correct)
    logger.error(f"fetch_with_retry loop completed unexpectedly for {url}.")
    return None


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
        # Set a default timeout for socket operations
        socket.setdefaulttimeout(timeout)
        # Create a socket (AF_INET = IPv4, SOCK_STREAM = TCP)
        # Use a 'with' statement for automatic socket closing
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Attempt to connect to the specified host and port
            sock.connect((host, port))
        # If connect succeeds without exception, connection is likely available
        logger.debug(f"Internet connection check successful (connected to {host}:{port}).")
        return True
    except (socket.error, socket.timeout) as e:
        # Log the specific error encountered during the connection attempt
        logger.debug(f"Internet connection check failed: Cannot connect to {host}:{port}. Error: {e}")
        return False
    except Exception as e: # Catch any other unexpected socket errors
         logger.error(f"Unexpected error during internet connection check: {e}", exc_info=True)
         return False


# --- Image Handling Functions ---

def download_image(url: str, cache_dir: str, filename: Optional[str] = None) -> Optional[str]:
    """
    Downloads an image from a URL and saves it to a local cache directory.

    Checks if the file already exists in the cache directory first. If not, it
    downloads the image using the `requests` library. Handles URLs that might
    be missing the 'https:' prefix (common in some APIs). Determines filename
    from URL if not explicitly provided.

    Args:
        url (str): The full URL of the image to download.
        cache_dir (str): The directory path where the image should be saved/cached.
                         The directory will be created if it doesn't exist.
        filename (Optional[str]): An optional specific filename to use when saving
                                  the image. If None, the filename is extracted
                                  from the last part of the URL path.

    Returns:
        Optional[str]: The full path to the locally cached image file if the download
                       is successful or if the file already exists in the cache.
                       Returns None if the download fails, the URL is invalid,
                       or a filename cannot be determined.
    """
    if not url:
        logger.warning("download_image called with empty URL.")
        return None

    try:
        # Ensure the cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # Prepend 'https:' if the URL starts with '//' (protocol-relative URL)
        if url.startswith('//'):
            url = f"https:{url}"

        # Determine the filename if not explicitly provided
        if not filename:
            try:
                # Parse the URL to extract the path component
                parsed_url = urllib.parse.urlparse(url)
                # Get the last part of the path as the filename
                filename = os.path.basename(parsed_url.path)
                if not filename: # Handle cases like 'domain.com/' where path is empty or '/'
                     # Attempt to generate a fallback name based on URL hash or similar?
                     # For now, log error and return None if filename is indeterminable.
                     raise ValueError("Could not determine a valid filename from URL path.")
            except Exception as e:
                 logger.error(f"Failed to determine filename from URL '{url}': {e}")
                 return None # Cannot proceed without a filename

        # Construct the full path for the cached file
        cache_path = os.path.join(cache_dir, filename)

        # Check if the image is already cached
        if os.path.exists(cache_path):
            logger.debug(f"Image already exists in cache: {cache_path}")
            return cache_path

        # --- Download the image ---
        logger.info(f"Downloading image from {url} to {cache_path}")
        response = requests.get(url, stream=True, timeout=20) # Use stream=True for large files, increased timeout
        response.raise_for_status() # Check for HTTP errors

        # Write the image content to the cache file chunk by chunk
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): # Process in 8KB chunks
                f.write(chunk)

        logger.info(f"Successfully downloaded and cached image: {filename}")
        return cache_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Network or HTTP error downloading image {url}: {e}")
        # Clean up potentially incomplete file if download failed mid-way
        if 'cache_path' in locals() and os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                logger.debug(f"Removed incomplete download file: {cache_path}")
            except OSError as remove_error:
                logger.error(f"Could not remove incomplete file {cache_path}: {remove_error}")
        return None
    except IOError as e:
         logger.error(f"File I/O error saving image to {cache_path if 'cache_path' in locals() else 'N/A'}: {e}")
         return None
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred downloading image {url}: {e}", exc_info=True)
        return None


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

# DEPRECATED? - This function seems based on an old index system and is likely unused.
# Verify if get_air_quality_text_localized is still relevant before removing.
# def get_air_quality_text(index: int) -> str:
#     """
#     DEPRECATED? Convert air quality index to localized descriptive text.
#
#     Note: This function's relevance is questionable as AQI is now typically
#           handled by category strings from AccuWeather, not numeric indices
#           in this specific way. It wraps `get_air_quality_text_localized`.
#
#     Args:
#         index (int): Air quality index value (system may be deprecated).
#
#     Returns:
#         str: Localized descriptive text for the air quality index.
#     """
#     logger.warning("get_air_quality_text helper function may be deprecated.")
#     # return get_air_quality_text_localized(index, config.LANGUAGE)
#     return "AQI Deprecated" # Return placeholder


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
