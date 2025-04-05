#!/usr/bin/env python3
"""
Download all AccuWeather icons script.

This standalone script downloads all AccuWeather weather icons and saves them 
to the weather_display/assets/weather_icons directory.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path to allow importing from weather_display
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import our icon handler
from weather_display.utils.icon_handler import WeatherIconHandler

def main():
    """Download all weather icons."""
    logger.info("Starting weather icon download process...")
    
    # Create the icon handler instance
    icon_handler = WeatherIconHandler()
    
    # Download all icons
    count = icon_handler.download_all_icons()
    
    logger.info(f"Downloaded {count} weather icons successfully")
    logger.info(f"Icons saved to: {icon_handler.ICON_DIR}")
    
    # Print the list of downloaded icons
    logger.info("Available weather icons:")
    for icon_code, info in WeatherIconHandler.ICON_MAPPING.items():
        filename = f"{icon_code:02d}_{info['name']}.png"
        filepath = os.path.join(icon_handler.ICON_DIR, filename)
        if os.path.exists(filepath):
            logger.info(f"  {icon_code:2d}: {info['description']} - {filename}")

if __name__ == "__main__":
    main()
