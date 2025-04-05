"""
Utility helper functions for the Weather Display application.

Includes functions for API requests, image handling, text formatting,
and checking internet connectivity.
"""

import os
import logging
import requests
import time
import socket
from datetime import datetime
import urllib.parse # Added for URL construction
from .. import config
from .localization import get_translation, get_day_name_localized, get_air_quality_text_localized
from PIL import Image
import customtkinter as ctk
try:
    from PIL import ImageTk
except ImportError:
    # ImageTk is not available, but we can still use Image
    # This is fine for non-GUI operations
    ImageTk = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('weather_display.log')
    ]
)

logger = logging.getLogger(__name__)

def fetch_with_retry(url, params=None, max_retries=3, timeout=10):
    """
    Fetch data from URL with retry logic.
    
    Args:
        url (str): URL to fetch data from
        params (dict, optional): URL parameters
        max_retries (int, optional): Maximum number of retry attempts
        timeout (int, optional): Request timeout in seconds
        
    Returns:
        dict: JSON response or None if failed
    """
    retry_count = 0
    while retry_count < max_retries:
        response = None # Initialize response to None
        try:
            # Construct the full URL with parameters for logging
            full_url = url
            if params:
                full_url += '?' + urllib.parse.urlencode(params)
            logger.info(f"Making API request to: {full_url}") # Log the full URL

            response = requests.get(url, params=params, timeout=timeout)

            # Check for specific AccuWeather API limit error *before* raise_for_status
            # Common codes for this might be 403, 429, 503
            if response.status_code in [403, 429, 503]:
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and error_data.get('Code') == 'ServiceUnavailable':
                        logger.warning(f"AccuWeather API request limit likely exceeded (HTTP {response.status_code}). Response: {error_data.get('Message')}")
                        # Return the specific error dictionary instead of None
                        return error_data
                except requests.exceptions.JSONDecodeError:
                    # If the body isn't JSON, proceed to raise_for_status
                    pass

            # If it wasn't the specific error, proceed with normal status check
            response.raise_for_status()
            return response.json()

        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            # Log the underlying error, including status code if available
            err_msg = f"{e}"
            if response is not None:
                err_msg = f"HTTP {response.status_code}: {e}"

            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Failed after {max_retries} attempts: {err_msg}")
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return None
            # Exponential backoff: 1s, 2s, 4s, etc.
            wait_time = 2 ** (retry_count - 1)
            logger.warning(f"Retry {retry_count} after {wait_time}s: {e}")
            time.sleep(wait_time)
    return None

def download_image(url, cache_dir, filename=None):
    """
    Download and cache an image.
    
    Args:
        url (str): URL of the image
        cache_dir (str): Directory to cache the image
        filename (str, optional): Filename to save the image as
        
    Returns:
        str | None: Path to the cached image if successful, otherwise None.
    """
    os.makedirs(cache_dir, exist_ok=True)

    # Add https: prefix if missing (common with some weather APIs)
    if url.startswith('//'):
        url = f"https:{url}"
    
        # Use the URL's filename if none provided.
        # Note: The old logic for day/night prefixes is less relevant for AccuWeather icons
        # but is kept for potential backward compatibility or other icon sources.
        # The AccuWeatherClient now passes an explicit filename anyway.
    if not filename:
        # Extract the day/night part and the actual filename
        url_parts = url.split('/')
        if len(url_parts) >= 2 and (url_parts[-2] == 'day' or url_parts[-2] == 'night'):
            # Use format like "day_113.png" or "night_113.png"
            filename = f"{url_parts[-2]}_{url_parts[-1]}"
        else:
            filename = os.path.basename(url)

    cache_path = os.path.join(cache_dir, filename)
    
    # Skip if already cached
    if os.path.exists(cache_path):
        return cache_path
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded image: {filename}")
        return cache_path
    except Exception as e:
        logger.error(f"Failed to download image {url}: {e}")
        return None

def load_image(path, size=None):
    """
    Load an image and optionally resize it.
    
    Args:
        path (str): Path to the image
        size (tuple, optional): Size to resize the image to (width, height)
        
    Returns:
        CTkImage: CustomTkinter-compatible image or None if failed
    """
    try:
        # Use CTkImage instead of ImageTk.PhotoImage for better HighDPI support
        return ctk.CTkImage(
            light_image=Image.open(path),
            dark_image=Image.open(path),
            size=size
        )
    except Exception as e:
        logger.error(f"Failed to load image {path}: {e}")
        return None

def format_temperature(temp):
    """
    Format temperature value.
    
    Args:
        temp (float): Temperature in Celsius
        
    Returns:
        str: Formatted temperature string (e.g., "23°C") or "N/A".
    """
    if temp is None:
        return get_translation('not_available', config.LANGUAGE) # Use translation for consistency
    return f"{int(round(temp))}°C"

def get_air_quality_text(index):
    """
    Convert air quality index to descriptive text.
    
    Args:
        index (int): Air quality index (1-6) - Note: Based on old WeatherAPI.com index. Unused.

    Returns:
        str: Descriptive text for the air quality.
    """
    return get_air_quality_text_localized(index, config.LANGUAGE)

def get_day_name(date_str):
    """
    Get the day name from a date string.
    
    Args:
        date_str (str): Date string, expected format 'YYYY-MM-DD'.

    Returns:
        str: Localized day name (e.g., 'Monday', 'Понедельник').
    """
    return get_day_name_localized(date_str, config.LANGUAGE)

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Check if there is an internet connection by trying to connect to Google's DNS.
    
    Args:
        host (str, optional): Host to connect to. Default is Google's DNS.
        port (int, optional): Port to connect to. Default is 53 (DNS).
        timeout (int, optional): Timeout in seconds. Default is 3.
        
    Returns:
        bool: True if internet connection is available, False otherwise.
    """
    try:
        # Try to create a socket connection to the specified host and port
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, socket.timeout):
        return False
