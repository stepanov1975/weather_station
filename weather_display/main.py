#!/usr/bin/env python3
"""
Weather Display Application for Raspberry Pi 5 touchscreen using AccuWeather API.

This application displays the current time, date, and weather information
(including current conditions, forecast, and AQI) for a configured location.
It supports running with a GUI or in headless mode for testing.
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
# Use the new AccuWeather client
from weather_display.services.weather_api import AccuWeatherClient

logger = logging.getLogger(__name__)

# Import necessary modules for headless mode
import signal

class WeatherDisplayApp:
    """Main application class for the Weather Display."""

    def __init__(self, api_key=None, headless=False):
        """
        Initialize the Weather Display application.

        Args:
            api_key (str | None): AccuWeather API key. Reads from config if None.
            headless (bool): Run without GUI if True. Defaults to False.
        """
        self.api_key = api_key
        self.headless = headless
        self.running = False
        self.time_service = TimeService()
        # Instantiate the new client
        self.weather_client = AccuWeatherClient(api_key=self.api_key)

        # Initialize the GUI only if not headless
        self.app_window = None
        if not self.headless:
            # Import GUI class only when needed
            from weather_display.gui.app_window import AppWindow
            self.app_window = AppWindow()
        else:
            logger.info("Running in headless mode.")

        # Track connection status
        self.last_connection_status = False
        
        logger.info("Weather Display application initialized")
    
    def start(self):
        """Start the application with the GUI. Requires a display environment."""
        if self.headless:
            logger.error("Cannot start GUI in headless mode. Use run_headless().")
            return

        if not self.app_window:
             logger.error("AppWindow not initialized. Cannot start GUI.")
             return

        self.running = True
        logger.info("Starting GUI application...")

        # Start the update threads
        self._start_update_threads()
        
        # Initial updates
        self._update_time_and_date()
        self._update_weather()
        
        # Start the main loop
        logger.info("Starting Tkinter main loop")
        self.app_window.mainloop() # This blocks until the window is closed

    def run_headless(self):
        """
        Run the application logic without the GUI.

        Starts background threads for updates and logs fetched data.
        Waits for SIGINT or SIGTERM to stop. Useful for testing or running
        in environments without a display.
        """
        if not self.headless:
            logger.error("Cannot run headless if not initialized in headless mode.")
            return

        self.running = True
        logger.info("Starting headless application...")

        # Start update threads
        self._start_update_threads()

        # Keep the main thread alive, waiting for a signal to stop
        # This allows background threads to run
        logger.info("Headless mode running. Press Ctrl+C to stop.")
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # Wait indefinitely until self.running becomes False
        while self.running:
            time.sleep(1)

        logger.info("Headless run finished.")


    def _handle_signal(self, signum, frame):
        """Signal handler for SIGINT and SIGTERM to stop gracefully."""
        logger.warning(f"Received signal {signum}. Stopping application...")
        self.stop()

    def stop(self):
        """Stop the application, signal threads, and destroy GUI if present."""
        logger.info("Stopping application...")
        self.running = False # Signal threads to stop
        # Wait a moment for threads to potentially finish current work
        time.sleep(0.5)
        if self.app_window:
            # Schedule the window destruction on the main Tkinter thread
             self.app_window.after(0, self.app_window.destroy)
        logger.info("Application stopped")

    def _start_update_threads(self):
        """Start background threads for time, weather, and connection updates."""
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
        """Background loop to update time/date periodically."""
        while self.running:
            self._update_time_and_date()
            time.sleep(config.UPDATE_INTERVAL_SECONDS)
    
    def _connection_monitoring_loop(self):
        """Background loop to monitor internet connection status."""
        while self.running:
            # Get current connection status
            current_status = self.weather_client.connection_status
            
            # If connection was down but is now up, update weather immediately
            if not self.last_connection_status and current_status:
                logger.info("Internet connection restored. Updating weather data immediately.")
                self._update_weather()
            
            # Update the connection status in the UI only if GUI exists
            if self.app_window:
                self.app_window.after(0, lambda cs=current_status: self.app_window.update_connection_status(cs))
            elif self.last_connection_status != current_status: # Log change in headless
                 logger.info(f"Connection status changed: {'Connected' if current_status else 'Disconnected'}")


            # Store current status for next check
            self.last_connection_status = current_status
            
            # Wait 30 seconds before checking again
            time.sleep(30)
    
    def _weather_update_loop(self):
        """Background loop to update weather data periodically."""
        while self.running:
            self._update_weather()
            # Sleep for the configured interval (convert minutes to seconds)
            time.sleep(config.WEATHER_UPDATE_INTERVAL_MINUTES * 60)
    
    def _update_time_and_date(self):
        """Fetch current time/date and update GUI or log if headless."""
        try:
            time_str, date_str = self.time_service.get_current_datetime()

            if self.app_window:
                # Update the GUI (must be done in the main thread)
                self.app_window.after(0, lambda ts=time_str: self.app_window.update_time(ts))
                self.app_window.after(0, lambda ds=date_str: self.app_window.update_date(ds))
            elif self.headless:
                 # Log time/date in headless mode (optional)
                 # logger.debug(f"Time: {time_str}, Date: {date_str}")
                 pass # Avoid excessive logging unless needed

        except Exception as e:
            logger.error(f"Error updating time and date: {e}")
    
    def _update_weather(self):
        """Fetch current weather/forecast and update GUI or log if headless."""
        try:
            # Get current weather
            current_weather = self.weather_client.get_current_weather()

            # Get forecast (Request 3 days, API client fetches 5 but returns all)
            forecast = self.weather_client.get_forecast(days=3)

            if self.app_window:
                # Update the GUI (must be done in the main thread)
                # Use arguments directly in lambda to capture current value
                self.app_window.after(0, lambda cw=current_weather: self.app_window.update_current_weather(cw))
                self.app_window.after(0, lambda fc=forecast: self.app_window.update_forecast(fc))
            elif self.headless:
                 # Log fetched data in headless mode
                 logger.info(f"Headless Weather Update: Current={current_weather}, Forecast={forecast}")


            # Log connection status change if not using GUI
            conn_status = current_weather.get('connection_status', False)
            if not self.app_window and self.last_connection_status != conn_status:
                 logger.info(f"Connection status: {'Connected' if conn_status else 'Disconnected'}")
                 self.last_connection_status = conn_status # Update status if logged here

            logger.info("Weather data updated")
        except Exception as e:
            logger.error(f"Error updating weather: {e}")
            # If there's an exception, assume there's no internet connection
            # Update GUI status if it exists
            if self.app_window:
                self.app_window.after(0, lambda: self.app_window.update_connection_status(False))
            elif self.last_connection_status: # Log change in headless
                 logger.warning("Connection status changed: Disconnected (due to error)")
                 self.last_connection_status = False


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Weather Display for Raspberry Pi')
    # Update help text for API key
    parser.add_argument('--api-key', help='AccuWeather API key')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of API')
    parser.add_argument('--windowed', action='store_true', help='Run in windowed mode instead of fullscreen.')
    # Add headless argument for testing without GUI
    parser.add_argument('--headless', action='store_true', help='Run without GUI (logs data to console/file).')
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
        # Use the correct config variable
        config.ACCUWEATHER_API_KEY = args.api_key

    if args.mock:
        config.USE_MOCK_DATA = True
    
    if args.windowed:
        config.FULLSCREEN = False
    
    # Wait for internet connection before starting the application
    # Skip waiting if using mock data
    # Check for API key if not using mock data
    if not config.USE_MOCK_DATA and not config.ACCUWEATHER_API_KEY:
        logger.critical("AccuWeather API key is missing!")
        logger.critical("Please set the ACCUWEATHER_API_KEY environment variable or use the --api-key argument.")
        logger.critical("Alternatively, run with --mock to use mock data.")
        sys.exit(1) # Exit if key is missing and mock is not enabled

    # Log the location value from config before using it
    logger.info(f"Using location from config: '{config.LOCATION}'")

    # Wait for internet connection before starting the application
    # Skip waiting if using mock data
    if not config.USE_MOCK_DATA:
        logger.info("Checking for internet connection...")
        wait_for_internet_connection()

    # Create the application instance, passing the headless flag
    app = WeatherDisplayApp(api_key=config.ACCUWEATHER_API_KEY, headless=args.headless)

    try:
        # Start the appropriate run method based on the headless flag
        if args.headless:
            app.run_headless()
        else:
            # Check for display availability before starting GUI
            if not os.environ.get('DISPLAY'):
                 logger.error("No display environment detected. Cannot start GUI.")
                 logger.error("Try running with --headless for non-GUI operation.")
                 sys.exit(1)
            app.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping...")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        app.stop()


if __name__ == "__main__":
    main()
