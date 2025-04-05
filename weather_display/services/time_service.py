"""
Time Service for the Weather Display application.

Provides methods to retrieve the current time and date, formatted according
to the application's localization settings.
"""

import logging
from datetime import datetime
from typing import Tuple

# Local application imports
from .. import config
from ..utils.localization import get_formatted_date

logger = logging.getLogger(__name__)

class TimeService:
    """
    A service class providing static methods for time and date retrieval.

    This class encapsulates the logic for getting the current time and date,
    ensuring consistent formatting and leveraging the localization module.
    """

    @staticmethod
    def get_current_time() -> str:
        """
        Get the current time formatted as HH:MM:SS.

        Returns:
            The current time string (e.g., "14:35:02").
        """
        return datetime.now().strftime('%H:%M:%S')

    @staticmethod
    def get_current_date() -> str:
        """
        Get the current date, formatted according to the configured language.

        Uses the `get_formatted_date` utility function for localization.

        Returns:
            The formatted date string (e.g., "Thursday, 04 May 2025" or
            "Четверг, 4 Мая 2025").
        """
        return get_formatted_date(config.LANGUAGE)

    @staticmethod
    def get_current_datetime() -> Tuple[str, str]:
        """
        Get both the current time and the formatted current date.

        Returns:
            A tuple containing the time string (HH:MM:SS) and the
            localized date string.
        """
        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')
        # Reuse get_current_date for consistency
        date_str = TimeService.get_current_date()
        return time_str, date_str
