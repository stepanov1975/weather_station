#!/usr/bin/env python3
"""
Weather Display Application for Raspberry Pi 5 touchscreen.

This application displays the current time, date, and weather information
for Hadera, Israel on a Raspberry Pi 5 touchscreen.
"""

import os
import sys
import time
import logging
import threading
import argparse

# Add the parent directory to the path so we can import the weather_display package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_display import config
from weather_display.gui.app_window import AppWindow
from weather_display.services.time_service import TimeService
from weather_display.services.weather_api import WeatherAPIClient

logger = logging.getLogger(__name__)

class WeatherDisplayApp:
    """Main application class for the Weather Display."""
    
    def __init__(self, api_key=None):
        """
        Initialize the Weather Display application.
        
        Args:
            api_key (str, optional): WeatherAPI.com API key
        """
        self.api_key = api_key
        self.running = False
        self.time_service = TimeService()
        self.weather_client = WeatherAPIClient(api_key=self.api_key)
        
        # Initialize the GUI
        self.app_window = None
        
        # Track connection status
        self.last_connection_status = False
        
        logger.info("Weather Display application initialized")
    
    def start(self):
        """Start the application."""
        self.running = True
        
        # Create and configure the application window
        self.app_window = AppWindow()
        
        # Start the update threads
        self._start_update_threads()
        
        # Initial updates
        self._update_time_and_date()
        self._update_weather()
        
        # Start the main loop
        logger.info("Starting main loop")
        self.app_window.mainloop()
    
    def stop(self):
        """Stop the application."""
        self.running = False
        if self.app_window:
            self.app_window.destroy()
        logger.info("Application stopped")
    
    def _start_update_threads(self):
        """Start the update threads."""
        # Time update thread
        time_thread = threading.Thread(target=self._time_update_loop, daemon=True)
        time_thread.start()
        
        # Weather update thread
        weather_thread = threading.Thread(target=self._weather_update_loop, daemon=True)
        weather_thread.start()
        
        # Connection monitoring thread
        connection_thread = threading.Thread(target=self._connection_monitoring_loop, daemon=True)
        connection_thread.start()
        
        logger.info("Update threads started")
    
    def _time_update_loop(self):
        """Time update loop."""
        while self.running:
            self._update_time_and_date()
            time.sleep(config.UPDATE_INTERVAL_SECONDS)
    
    def _connection_monitoring_loop(self):
        """Connection monitoring loop that checks internet connectivity every 30 seconds."""
        while self.running:
            # Get current connection status
            current_status = self.weather_client.connection_status
            
            # If connection was down but is now up, update weather immediately
            if not self.last_connection_status and current_status:
                logger.info("Internet connection restored. Updating weather data immediately.")
                self._update_weather()
            
            # Update the connection status in the UI
            if self.app_window:
                self.app_window.after(0, lambda: self.app_window.update_connection_status(current_status))
            
            # Store current status for next check
            self.last_connection_status = current_status
            
            # Wait 30 seconds before checking again
            time.sleep(30)
    
    def _weather_update_loop(self):
        """Weather update loop."""
        while self.running:
            self._update_weather()
            # Sleep for the configured interval (convert minutes to seconds)
            time.sleep(config.WEATHER_UPDATE_INTERVAL_MINUTES * 60)
    
    def _update_time_and_date(self):
        """Update the time and date display."""
        try:
            time_str, date_str = self.time_service.get_current_datetime()
            
            # Update the GUI (must be done in the main thread)
            if self.app_window:
                self.app_window.after(0, lambda: self.app_window.update_time(time_str))
                self.app_window.after(0, lambda: self.app_window.update_date(date_str))
        except Exception as e:
            logger.error(f"Error updating time and date: {e}")
    
    def _update_weather(self):
        """Update the weather display."""
        try:
            # Get current weather
            current_weather = self.weather_client.get_current_weather()
            
            # Get forecast
            forecast = self.weather_client.get_forecast(days=3)
            
            # Update the GUI (must be done in the main thread)
            if self.app_window:
                self.app_window.after(0, lambda: self.app_window.update_current_weather(current_weather))
                self.app_window.after(0, lambda: self.app_window.update_forecast(forecast))
            
            # Check connection status from current weather data
            if 'connection_status' in current_weather:
                logger.info(f"Internet connection status: {'Connected' if current_weather['connection_status'] else 'Disconnected'}")
            
            logger.info("Weather data updated")
        except Exception as e:
            logger.error(f"Error updating weather: {e}")
            # If there's an exception, assume there's no internet connection
            if self.app_window:
                self.app_window.after(0, lambda: self.app_window.update_connection_status(False))


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Weather Display for Raspberry Pi')
    parser.add_argument('--api-key', help='WeatherAPI.com API key')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of API')
    parser.add_argument('--windowed', action='store_true', help='Run in windowed mode instead of fullscreen')
    return parser.parse_args()


def wait_for_internet_connection():
    """
    Wait for internet connection, checking every 10 seconds.
    
    Returns:
        bool: True when connection is established
    """
    from weather_display.utils.helpers import check_internet_connection
    
    while True:
        if check_internet_connection():
            logger.info("Internet connection established")
            return True
        
        logger.info("No internet connection. Waiting 10 seconds before checking again...")
        time.sleep(10)

def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('weather_display.log')
        ]
    )
    
    # Override config settings from command line arguments
    if args.api_key:
        config.WEATHER_API_KEY = args.api_key
    
    if args.mock:
        config.USE_MOCK_DATA = True
    
    if args.windowed:
        config.FULLSCREEN = False
    
    # Wait for internet connection before starting the application
    # Skip waiting if using mock data
    if not config.USE_MOCK_DATA:
        logger.info("Checking for internet connection...")
        wait_for_internet_connection()
    
    # Create and start the application
    app = WeatherDisplayApp(api_key=config.WEATHER_API_KEY)
    
    try:
        app.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        app.stop()


if __name__ == "__main__":
    main()
