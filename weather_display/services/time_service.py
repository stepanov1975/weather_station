"""
Time Service for the Weather Display Application.

This module provides the `TimeService` class, which offers static methods
to retrieve the current system time and date. It ensures consistent formatting
and utilizes the application's localization settings for date representation.

The primary purpose is to centralize time/date retrieval logic, making it easy
to manage and potentially extend (e.g., adding timezone support if needed,
although currently relies on system time).
"""

import logging
from datetime import datetime
from typing import Tuple

# Local application imports
from .. import config # To access the configured LANGUAGE setting
from ..utils.localization import get_formatted_date # For localized date formatting

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

class TimeService:
    """
    Provides static methods for retrieving formatted current time and date.

    This class acts as a utility wrapper around standard datetime functions,
    integrating with the application's configuration and localization utilities
    to provide consistently formatted and potentially localized time/date strings.
    All methods are static, meaning an instance of the class is not required.
    """

    @staticmethod
    def get_current_time() -> str:
        """
        Gets the current system time formatted as HH:MM:SS.

        Uses the standard `datetime.now()` and formats it using `strftime`.

        Returns:
            str: The current time as a string in "HH:MM:SS" format (e.g., "14:35:02").
        """
        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')
        logger.debug(f"Retrieved current time: {time_str}")
        return time_str

    @staticmethod
    def get_current_date() -> str:
        """
        Gets the current system date, formatted according to the configured language.

        Delegates the formatting logic to the `get_formatted_date` utility function
        from the localization module, passing the language code defined in `config.py`.

        Returns:
            str: The current date formatted as a localized string (e.g., for 'en':
                 "Thursday, 04 May 2025"; for 'ru': "Четверг, 4 Мая 2025").
                 Format depends on the implementation in `utils.localization`.
        """
        language_code = config.LANGUAGE
        date_str = get_formatted_date(language_code)
        logger.debug(f"Retrieved formatted date for language '{language_code}': {date_str}")
        return date_str

    @staticmethod
    def get_current_datetime() -> Tuple[str, str]:
        """
        Gets both the current time (HH:MM:SS) and the formatted, localized current date.

        This is a convenience method that calls `get_current_time` and
        `get_current_date` to retrieve both values efficiently.

        Returns:
            Tuple[str, str]: A tuple containing:
                             - The current time string ("HH:MM:SS").
                             - The current localized date string.
        """
        # It's slightly more efficient to get datetime.now() once
        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')
        # Reuse the static method for date formatting to ensure consistency
        date_str = TimeService.get_current_date()
        logger.debug(f"Retrieved current datetime: Time='{time_str}', Date='{date_str}'")
        return time_str, date_str

# Example usage (if run directly)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # Enable logging for testing
    print("Testing TimeService...")
    current_time = TimeService.get_current_time()
    print(f"Current Time: {current_time}")
    current_date = TimeService.get_current_date()
    print(f"Current Date (Lang: {config.LANGUAGE}): {current_date}")
    time_tuple, date_tuple = TimeService.get_current_datetime()
    print(f"Current DateTime Tuple: ('{time_tuple}', '{date_tuple}')")
