"""
Utility helper functions for the Weather Display application.
"""

import os
import logging
import requests
import time
from datetime import datetime
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
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            retry_count += 1
            if retry_count >= max_retries:
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
        str: Path to the cached image or None if failed
    """
    os.makedirs(cache_dir, exist_ok=True)
    
    # Add https: prefix if missing
    if url.startswith('//'):
        url = f"https:{url}"
    
    # Use the URL's filename if none provided, but preserve day/night distinction
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
        str: Formatted temperature string
    """
    if temp is None:
        return "N/A"
    return f"{int(round(temp))}°C"

def get_air_quality_text(index):
    """
    Convert air quality index to descriptive text.
    
    Args:
        index (int): Air quality index (1-6)
        
    Returns:
        str: Descriptive text for the air quality
    """
    return get_air_quality_text_localized(index, config.LANGUAGE)

def get_day_name(date_str):
    """
    Get the day name from a date string.
    
    Args:
        date_str (str): Date string in format 'YYYY-MM-DD'
        
    Returns:
        str: Day name (e.g., 'Monday')
    """
    return get_day_name_localized(date_str, config.LANGUAGE)
