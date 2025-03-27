"""
Time service for handling time and date functionality.
"""

import time
from datetime import datetime
import logging
from .. import config
from ..utils.localization import get_formatted_date

logger = logging.getLogger(__name__)

class TimeService:
    """Service for handling time and date functionality."""
    
    @staticmethod
    def get_current_time():
        """
        Get the current time in 24-hour format.
        
        Returns:
            str: Current time in HH:MM:SS format
        """
        return datetime.now().strftime('%H:%M:%S')
    
    @staticmethod
    def get_current_date():
        """
        Get the current date.
        
        Returns:
            str: Current date in full format (e.g., "Thursday, 27 March 2025")
        """
        return get_formatted_date(config.LANGUAGE)
    
    @staticmethod
    def get_current_datetime():
        """
        Get the current date and time.
        
        Returns:
            tuple: (time_str, date_str)
        """
        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')
        date_str = get_formatted_date(config.LANGUAGE)
        return time_str, date_str
