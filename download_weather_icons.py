#!/usr/bin/env python3
"""
Standalone script to download all AccuWeather weather icons.

This script initializes the `WeatherIconHandler` and calls its
`download_all_icons` method to fetch any missing icons defined in its mapping
and save them to the designated assets directory.
"""

# Standard library imports
import os
import sys
import logging

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
    handlers=[logging.StreamHandler()] # Log only to console for this script
)
logger = logging.getLogger(__name__)


def main():
    """
    Initialize the icon handler and trigger the download of all icons.
    Logs the outcome and the location of the downloaded icons.
    """
    logger.info("Starting AccuWeather icon download process...")

    try:
        # Create the icon handler instance
        icon_handler = WeatherIconHandler()
        logger.info(f"Icon directory: {icon_handler.icon_dir}")

        # Trigger the download of all missing icons
        downloaded_count = icon_handler.download_all_icons()

        if downloaded_count > 0:
            logger.info(f"Successfully downloaded {downloaded_count} new weather icon(s).")
        else:
            logger.info("No new icons needed or downloaded.")

        # Optionally, list available icons after download attempt
        logger.info("Verifying available icons in directory:")
        found_icons = 0
        missing_files = []
        for icon_code, info in icon_handler.ICON_MAPPING.items():
            filename = f"{icon_code:02d}_{info['name']}.png"
            filepath = os.path.join(icon_handler.icon_dir, filename)
            if os.path.exists(filepath):
                logger.debug(f"  Found: {filename} (Code: {icon_code}, Desc: {info['description']})")
                found_icons += 1
            else:
                missing_files.append(filename)

        logger.info(f"Found {found_icons} icon files in the directory.")
        if missing_files:
             logger.warning(f"Could not find/download the following icon files: {', '.join(missing_files)}")

    except Exception as e:
        logger.critical(f"An error occurred during the icon download process: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Icon download process finished.")


if __name__ == "__main__":
    main()
