"""
Weather Icon Handler for the Weather Display application.

This module provides functionality to map weather conditions to appropriate icon files.
"""

import os
import logging
import requests
from datetime import datetime
from PIL import Image
import customtkinter as ctk
from .. import config

logger = logging.getLogger(__name__)

class WeatherIconHandler:
    """
    Handles retrieving and mapping weather icons based on weather conditions.
    
    This class manages the mapping between AccuWeather icon codes and 
    the corresponding icon files in the assets directory.
    """
    
    # Base directory for weather icons
    ICON_DIR = os.path.join("weather_display", "assets", "weather_icons")
    
    # AccuWeather icon codes and their descriptions
    # Reference: https://developer.accuweather.com/weather-icons
    ICON_MAPPING = {
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
        # Create the icon directory if it doesn't exist
        os.makedirs(self.ICON_DIR, exist_ok=True)
        self.icon_cache = {}  # Cache loaded icons
        
    def get_icon_path(self, icon_code):
        """
        Get the file path for a weather icon based on the AccuWeather icon code.
        
        Args:
            icon_code (int): AccuWeather icon code (1-44)
            
        Returns:
            str: Path to the icon file or None if not found
        """
        if not icon_code or icon_code not in self.ICON_MAPPING:
            logger.warning(f"Unknown icon code: {icon_code}, using default icon")
            # Default to sunny/clear icon
            icon_code = 1 if 6 <= datetime.now().hour < 18 else 33  # Day/night based on time
        
        icon_info = self.ICON_MAPPING.get(icon_code)
        icon_name = icon_info["name"]
        
        # Construct filename with icon code for reference
        filename = f"{icon_code:02d}_{icon_name}.png"
        icon_path = os.path.join(self.ICON_DIR, filename)
        
        # If icon doesn't exist, download from AccuWeather
        if not os.path.exists(icon_path):
            self._download_icon(icon_code, icon_path)
            
        return icon_path if os.path.exists(icon_path) else None
    
    def get_icon_by_condition(self, condition_text):
        """
        Get the icon path based on a weather condition text description.
        
        Args:
            condition_text (str): Weather condition text (e.g., "Sunny", "Partly Cloudy")
            
        Returns:
            str: Path to the icon file or None if not found
        """
        # Convert condition text to lowercase for case-insensitive matching
        condition_lower = condition_text.lower()
        
        # Find matching icon code based on description
        for code, info in self.ICON_MAPPING.items():
            if info["description"].lower() == condition_lower:
                return self.get_icon_path(code)
        
        # Try partial matching for more flexibility
        for code, info in self.ICON_MAPPING.items():
            if condition_lower in info["description"].lower():
                return self.get_icon_path(code)
        
        logger.warning(f"No icon found for condition: {condition_text}, using default")
        return self.get_icon_path(1)  # Default to sunny
    
    def load_icon(self, icon_code, size=(64, 64)):
        """
        Load and return a weather icon as a CTkImage.
        
        Args:
            icon_code (int): AccuWeather icon code
            size (tuple): Size to resize the icon to (width, height)
            
        Returns:
            ctk.CTkImage: CustomTkinter-compatible image or None if failed
        """
        # Check cache first
        cache_key = f"{icon_code}_{size[0]}x{size[1]}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        # Get icon path
        icon_path = self.get_icon_path(icon_code)
        if not icon_path or not os.path.exists(icon_path):
            logger.error(f"Icon path not found for code: {icon_code}")
            return None
        
        try:
            # Use CTkImage for better HighDPI support
            icon = ctk.CTkImage(
                light_image=Image.open(icon_path),
                dark_image=Image.open(icon_path),
                size=size
            )
            # Cache the loaded icon
            self.icon_cache[cache_key] = icon
            return icon
        except Exception as e:
            logger.error(f"Failed to load icon {icon_path}: {e}")
            return None
    
    def _download_icon(self, icon_code, save_path):
        """
        Download an AccuWeather icon.
        
        Args:
            icon_code (int): AccuWeather icon code
            save_path (str): Path to save the downloaded icon
            
        Returns:
            bool: True if download successful, False otherwise
        """
        # Format icon code with leading zero if needed
        icon_str = f"{icon_code:02d}"
        # Construct AccuWeather icon URL
        icon_url = f"https://developer.accuweather.com/sites/default/files/{icon_str}-s.png"
        
        try:
            response = requests.get(icon_url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded weather icon: {os.path.basename(save_path)}")
            return True
        except Exception as e:
            logger.error(f"Failed to download icon {icon_url}: {e}")
            return False

    def download_all_icons(self):
        """
        Download all AccuWeather icons.
        
        Returns:
            int: Number of successfully downloaded icons
        """
        success_count = 0
        for icon_code in self.ICON_MAPPING.keys():
            icon_info = self.ICON_MAPPING[icon_code]
            filename = f"{icon_code:02d}_{icon_info['name']}.png"
            icon_path = os.path.join(self.ICON_DIR, filename)
            
            if not os.path.exists(icon_path):
                if self._download_icon(icon_code, icon_path):
                    success_count += 1
        
        logger.info(f"Downloaded {success_count} weather icons")
        return success_count
