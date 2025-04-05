#!/usr/bin/env python3
"""
Standalone script to verify downloaded AccuWeather weather icons.

This script checks all icons expected according to the WeatherIconHandler mapping.
It verifies if each file exists and attempts to open it using PIL to ensure
it's a valid image file. It reports missing or invalid icons.
"""

# Standard library imports
import os
import sys
import logging
from typing import Tuple

# Third-party imports
from PIL import Image, UnidentifiedImageError

# Local application imports
try:
    # Assumes script is run from project root or package is installed
    from weather_display.utils.icon_handler import WeatherIconHandler
except ImportError:
    print("Error: Unable to import WeatherIconHandler.")
    print("Please run this script from the project root directory or ensure the package is installed.")
    # Attempt path adjustment as a fallback
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from weather_display.utils.icon_handler import WeatherIconHandler
    except ImportError:
         print("Path adjustment failed. Exiting.")
         sys.exit(1)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] # Log only to console
)
logger = logging.getLogger(__name__)


def verify_icon_file(icon_filepath: str) -> bool:
    """
    Verify that a given file path points to a valid image file.

    Attempts to open the image using PIL and logs basic image info if successful.

    Args:
        icon_filepath: The full path to the icon image file.

    Returns:
        True if the file is a valid, readable image, False otherwise.
    """
    icon_filename = os.path.basename(icon_filepath)
    try:
        # Use 'with' to ensure the file handle is closed properly
        with Image.open(icon_filepath) as img:
            # Verify read by accessing properties (forces loading some data)
            img.load()
            width, height = img.size
            format_name = img.format
            mode = img.mode
            logger.info(
                f"✓ Valid icon: {icon_filename} "
                f"({width}x{height}, {format_name}, {mode})"
            )
            return True
    except FileNotFoundError:
        # This case is handled in main, but included for completeness
        logger.error(f"✗ File not found: {icon_filename}")
        return False
    except UnidentifiedImageError:
        logger.error(f"✗ Invalid format: {icon_filename} - Cannot identify image file.")
        return False
    except Exception as e:
        logger.error(f"✗ Error opening {icon_filename}: {e}", exc_info=True)
        return False


def main() -> int:
    """
    Verify all expected weather icons based on WeatherIconHandler mapping.

    Checks for existence and validity of each icon file.

    Returns:
        0 if all icons are present and valid, 1 otherwise.
    """
    logger.info("Starting weather icon verification process...")
    exit_code = 0 # Assume success initially
    valid_icon_count = 0
    missing_icon_count = 0
    invalid_icon_count = 0

    try:
        icon_handler = WeatherIconHandler()
        icon_directory = icon_handler.icon_dir
        logger.info(f"Verifying icons in directory: {icon_directory}")

        # Iterate through all defined icons in the mapping
        for icon_code, info in sorted(icon_handler.ICON_MAPPING.items()):
            icon_name = info.get("name", f"unknown_{icon_code}") # Use name from mapping
            expected_filename = f"{icon_code:02d}_{icon_name}.png"
            icon_filepath = os.path.join(icon_directory, expected_filename)

            if not os.path.exists(icon_filepath):
                logger.error(f"✗ Missing icon file: {expected_filename}")
                missing_icon_count += 1
                exit_code = 1 # Mark as failure
                continue # Skip verification for missing file

            # Verify the existing file
            if verify_icon_file(icon_filepath):
                valid_icon_count += 1
            else:
                invalid_icon_count += 1
                exit_code = 1 # Mark as failure

    except Exception as e:
        logger.critical(f"An unexpected error occurred during verification setup: {e}", exc_info=True)
        return 1 # Indicate failure

    # --- Print Summary ---
    total_checked = valid_icon_count + missing_icon_count + invalid_icon_count
    logger.info("-" * 30)
    logger.info("Icon Verification Summary:")
    logger.info(f"  Total Icons Expected: {len(WeatherIconHandler.ICON_MAPPING)}")
    logger.info(f"  Valid Icons Found:    {valid_icon_count}")
    logger.info(f"  Missing Icon Files:   {missing_icon_count}")
    logger.info(f"  Invalid Image Files:  {invalid_icon_count}")
    logger.info("-" * 30)

    if exit_code == 0:
        logger.info("All expected icons are present and valid.")
    else:
        logger.warning("Verification failed for one or more icons.")
        if missing_icon_count > 0:
             logger.warning("Try running 'download_weather_icons.py' to fetch missing icons.")
        if invalid_icon_count > 0:
             logger.warning("Invalid icons might need to be deleted and re-downloaded.")

    return exit_code


if __name__ == "__main__":
    # Exit the script with the return code from main()
    sys.exit(main())
