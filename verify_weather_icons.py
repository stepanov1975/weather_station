#!/usr/bin/env python3
"""
Verify all weather icons.

This script checks that all downloaded AccuWeather icons are valid image files
and can be properly opened and processed.
"""

import os
import sys
import logging
from PIL import Image

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

def verify_icon(icon_path):
    """
    Verify that an icon file is a valid image by attempting to open it.
    
    Args:
        icon_path (str): Path to the icon file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Try to open the image
        with Image.open(icon_path) as img:
            # Get image details to ensure it's valid
            width, height = img.size
            format_name = img.format
            mode = img.mode
            
            logger.info(f"✓ Valid icon: {os.path.basename(icon_path)} - {width}x{height} {format_name} {mode}")
            return True
    except Exception as e:
        logger.error(f"✗ Invalid icon: {os.path.basename(icon_path)} - {e}")
        return False

def main():
    """Verify all weather icons."""
    logger.info("Starting weather icon verification...")
    
    # Create the icon handler instance
    icon_handler = WeatherIconHandler()
    
    # Count successful and failed verifications
    success_count = 0
    failed_count = 0
    
    # Check each icon in the mapping
    for icon_code, info in sorted(WeatherIconHandler.ICON_MAPPING.items()):
        filename = f"{icon_code:02d}_{info['name']}.png"
        filepath = os.path.join(icon_handler.ICON_DIR, filename)
        
        if not os.path.exists(filepath):
            logger.error(f"✗ Missing icon: {filename}")
            failed_count += 1
            continue
        
        if verify_icon(filepath):
            success_count += 1
        else:
            failed_count += 1
    
    # Print summary
    logger.info(f"Icon verification complete: {success_count} valid, {failed_count} invalid or missing")
    
    if failed_count > 0:
        logger.warning("Some icons failed verification. You may need to download them again.")
        return 1
    else:
        logger.info("All icons verified successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
