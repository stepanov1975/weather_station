#!/usr/bin/env python3
"""
Main entry point for the Weather Display Application.

This script initializes the application, parses command-line arguments,
sets up services (Time, Weather API), configures the GUI (if not headless),
and manages the main update loops in background threads.
"""

# Standard library imports
import os
import sys
import time
import logging
import threading
import argparse
import signal
from typing import Optional, List # Ensure List is imported

# Local application imports
# Assuming the script is run from the project root or the package is installed
try:
    from weather_display import config
    from weather_display.gui.app_window import AppWindow
    from weather_display.services.time_service import TimeService
    # Import both IMS and AccuWeather services
    from weather_display.services.ims_lasthour import IMSLastHourWeather
    from weather_display.services.weather_api import AccuWeatherClient # Added AccuWeather
    from weather_display.utils.helpers import check_internet_connection
except ImportError as e:
    # Handle cases where the package structure might not be recognized immediately
    # (e.g., running the script directly without installing the package)
    print(f"Import Error: {e}. Attempting to adjust Python path.")
    # Add the parent directory to the path to find the 'weather_display' package
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    try:
        from weather_display import config
        from weather_display.gui.app_window import AppWindow
        from weather_display.services.time_service import TimeService
        # Import both IMS and AccuWeather services
        from weather_display.services.ims_lasthour import IMSLastHourWeather
        from weather_display.services.weather_api import AccuWeatherClient # Added AccuWeather
        from weather_display.utils.helpers import check_internet_connection
    except ImportError:
        print("Failed to import necessary modules even after path adjustment.")
        print("Please ensure the script is run correctly relative to the package structure or install the package.")
        sys.exit(1)


# --- Global Logger Setup ---
# Configure logging basic settings here. More advanced config could be in a separate file.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(), # Log to console
        logging.FileHandler('weather_display.log') # Log to file
    ]
)
logger = logging.getLogger(__name__) # Get logger for this module


class WeatherDisplayApp:
    """
    Main application class orchestrating services, GUI, and update loops.

    Attributes:
        headless (bool): Flag indicating if running without a GUI.
        running (bool): Flag to control the main loops of background threads.
        time_service (TimeService): Instance for getting time and date.
        ims_weather (IMSLastHourWeather): Instance for fetching IMS weather data.
        accuweather_client (Optional[AccuWeatherClient]): Instance for fetching AccuWeather data. # Added
        app_window (Optional[AppWindow]): Instance of the GUI window (None if headless).
        last_connection_status (bool): Tracks the last known internet connection state.
        _update_threads (List[threading.Thread]): List holding background update threads.
    """

    def __init__(self, headless: bool = False, api_key: Optional[str] = None): # Added api_key parameter
        """
        Initialize the Weather Display application services and optionally the GUI.

        Args:
            headless: If True, initializes without creating a GUI window.
        """
        self.headless: bool = headless
        self.running: bool = False # Controls thread loops
        self._update_threads: List[threading.Thread] = []
        self._time_update_job_id: Optional[str] = None # To store the 'after' job ID

        # Initialize services
        self.time_service = TimeService()
        # Initialize IMS weather service with station name from config
        self.ims_weather = IMSLastHourWeather(station_name=config.IMS_STATION_NAME)
        # Initialize AccuWeather client (API key/location handled internally)
        self.accuweather_client: Optional[AccuWeatherClient] = None
        try:
            # Check if necessary AccuWeather config exists before initializing
            if hasattr(config, 'ACCUWEATHER_BASE_URL'):
                 # Pass the provided api_key (from args or None) to the client constructor
                 # The client will handle falling back to config/env if api_key is None
                 self.accuweather_client = AccuWeatherClient(api_key=api_key)
                 logger.info("AccuWeather client initialized.")
                 # Log warning if no key was provided via args AND none found by client
                 if not api_key and not self.accuweather_client.api_key:
                     logger.warning("AccuWeather API key not found in args, config, or environment. Client will use mock data.")
                 elif api_key:
                     logger.info("Using AccuWeather API key from command line argument.")
            else:
                 logger.warning("AccuWeather base URL not found in config. AccuWeather client NOT initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize AccuWeatherClient: {e}", exc_info=True)
            # Continue without AccuWeather if initialization fails

        # Initialize GUI only if not in headless mode
        self.app_window: Optional[AppWindow] = None
        if not self.headless:
            logger.info("Initializing GUI...")
            # Check for display availability before creating window
            if not os.environ.get('DISPLAY'):
                 logger.error("No display environment detected (DISPLAY variable not set).")
                 raise RuntimeError("Cannot initialize GUI without a display environment. Try --headless.")
            try:
                self.app_window = AppWindow()
            except Exception as e:
                logger.error(f"Failed to initialize AppWindow: {e}", exc_info=True)
                raise RuntimeError("GUI initialization failed.") from e
        else:
            logger.info("Running in headless mode (no GUI).")

        # Track connection status for triggering immediate updates on reconnect
        # Initial check - fetch_data will update this later
        self.last_connection_status: bool = check_internet_connection()

        logger.info("Weather Display application initialized.")

    def start(self):
        """Start the application main loop (GUI or headless wait)."""
        if self.running:
            logger.warning("Application is already running.")
            return

        self.running = True
        logger.info("Starting application...")

        self._start_update_threads()

        if self.app_window:
            logger.info("Starting GUI main loop...")
            # Perform initial updates before starting loop
            self._update_time_and_date()
            self._update_weather() # Initial IMS update
            if self.accuweather_client:
                self._update_accuweather_data() # Initial AccuWeather update
            # Start the time update loop using Tkinter's 'after'
            self._update_time_and_date()
            self.app_window.mainloop() # Blocks until window is closed
            # After mainloop finishes (window closed), stop the app
            self.stop()
        elif self.headless:
            logger.info("Headless mode: Running update loops in background.")
            logger.info("Press Ctrl+C to stop.")
            # Setup signal handling for graceful shutdown in headless mode
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
            # Keep main thread alive while background threads run
            while self.running:
                time.sleep(1) # Keep alive, checking running flag
            logger.info("Headless run finished.")
        else:
             # Should not happen if __init__ logic is correct
             logger.error("Application state invalid: No GUI and not headless.")


    def stop(self):
        """Stop the application, signal threads, and destroy GUI if present."""
        if not self.running:
            logger.info("Application already stopped.")
            return

        logger.info("Stopping application...")
        self.running = False # Signal threads to exit their loops

        # Wait briefly for threads to potentially finish current cycle
        # Adjust sleep time if needed
        time.sleep(0.5)

        # Cancel the scheduled time update job if it exists
        if self.app_window and self._time_update_job_id:
            try:
                self.app_window.after_cancel(self._time_update_job_id)
                logger.debug("Cancelled scheduled time update job.")
                self._time_update_job_id = None
            except Exception as e:
                logger.error(f"Error cancelling time update job: {e}")

        # Join remaining background threads (weather, connection)
        threads_to_join = [t for t in self._update_threads if t.is_alive()]
        if threads_to_join:
            logger.debug(f"Waiting for {len(threads_to_join)} background thread(s) to join...")
            for thread in threads_to_join:
                thread.join(timeout=1.0) # Add timeout
                if thread.is_alive():
                     logger.warning(f"Thread {thread.name} did not join.")
            self._update_threads = [] # Clear the list

        # Destroy GUI window if it exists
        if self.app_window:
            logger.info("Destroying GUI window...")
            try:
                # No need to schedule with 'after' here, as stop() should be called
                # after mainloop exits (or during shutdown sequence initiated from main thread)
                self.app_window.destroy()
            except Exception as e:
                 logger.error(f"Error destroying GUI window: {e}")

        logger.info("Application stopped.")

    def _handle_signal(self, signum, frame):
        """Signal handler for SIGINT/SIGTERM in headless mode."""
        logger.warning(f"Received signal {signal.Signals(signum).name}. Initiating shutdown...")
        self.stop()

    # --- Background Update Logic ---

    def _start_update_threads(self):
        """Create and start background threads for weather and connection updates."""
        # Note: Time update is now handled by Tkinter's 'after' loop, not a separate thread.
        logger.info("Starting background update threads (IMS Weather, AccuWeather, Connection)...")
        self._update_threads = [
            # IMS Weather Update Thread
            threading.Thread(target=self._weather_update_loop, name="IMSWeatherUpdateThread", daemon=True),
            # Connection Monitoring Thread
            threading.Thread(target=self._connection_monitoring_loop, name="ConnectionMonitorThread", daemon=True)
        ]
        # Add AccuWeather thread only if client was initialized
        if self.accuweather_client:
            self._update_threads.append(
                threading.Thread(target=self._accuweather_update_loop, name="AccuWeatherUpdateThread", daemon=True)
            )
        else:
            logger.warning("AccuWeather client not initialized, skipping AccuWeather update thread.")

        for thread in self._update_threads:
            thread.start()
        logger.info("Background update threads started.")

    # Removed _time_update_loop method

    def _weather_update_loop(self):
        """Background loop to update IMS weather data periodically."""
        logger.debug("IMS weather update loop started.")
        # Initial update is handled by the start() method before the loop begins.
        # This loop handles subsequent updates after the interval.
        while self.running:
            # Sleep *before* the next update to respect the interval
            # Use the specific IMS interval from config
            interval_seconds = config.IMS_UPDATE_INTERVAL_MINUTES * 60
            # Allow loop to exit quickly if self.running becomes False during sleep
            for _ in range(int(interval_seconds)):
                 if not self.running: break
                 time.sleep(1)
            if not self.running: break # Exit if stopped during sleep
            self._update_weather() # Calls the IMS update function
        logger.debug("IMS weather update loop finished.")

    def _accuweather_update_loop(self):
        """Background loop to update AccuWeather data periodically."""
        if not self.accuweather_client:
            logger.error("AccuWeather update loop started but client is not initialized. Loop will exit.")
            return

        logger.debug("AccuWeather update loop started.")
        # Initial update handled by start()
        while self.running:
            # Sleep *before* the next update
            interval_seconds = config.ACCUWEATHER_UPDATE_INTERVAL_MINUTES * 60
            logger.debug(f"AccuWeather loop: Sleeping for {interval_seconds} seconds.")
            for _ in range(int(interval_seconds)):
                 if not self.running: break
                 time.sleep(1)
            if not self.running: break # Exit if stopped during sleep

            self._update_accuweather_data() # Call the AccuWeather update function

        logger.debug("AccuWeather update loop finished.")


    def _connection_monitoring_loop(self):
        """Background loop to monitor internet connection status."""
        logger.debug("Connection monitoring loop started.")
        check_interval_seconds = 30 # Check connection every 30 seconds
        while self.running:
            # Use the helper function directly for connection checks
            current_status = check_internet_connection()

            # If connection restored, trigger immediate updates for both services
            if not self.last_connection_status and current_status:
                logger.info("Internet connection restored. Triggering immediate weather updates (IMS & AccuWeather).")
                # Run IMS update in a separate thread
                ims_update_thread = threading.Thread(target=self._update_weather, name="IMSImmediateUpdate", daemon=True)
                ims_update_thread.start()
                # Run AccuWeather update in a separate thread (if client exists)
                if self.accuweather_client:
                    accu_update_thread = threading.Thread(target=self._update_accuweather_data, name="AccuWeatherImmediateUpdate", daemon=True)
                    accu_update_thread.start()

            # Log status change only if it actually changed
            if self.last_connection_status != current_status:
                 log_msg = f"Connection status changed: {'Connected' if current_status else 'Disconnected'}"
                 # Log differently based on mode (GUI updates indicators, headless needs log)
                 if self.headless:
                     logger.info(log_msg)
                 else:
                     logger.debug(log_msg + " (GUI indicators will update)")

            self.last_connection_status = current_status

            # Sleep until next check, allowing quick exit if stopped
            for _ in range(check_interval_seconds):
                 if not self.running: break
                 time.sleep(1)
            if not self.running: break # Exit if stopped during sleep
        logger.debug("Connection monitoring loop finished.")

    # --- Data Update Actions ---

    def _update_time_and_date(self):
        """Fetch current time/date and update GUI. Schedules the next update."""
        # This method now runs on the main GUI thread via 'after'
        if not self.running: # Check if app should stop
             return

        logger.debug("Updating time and date...")
        try:
            time_str, date_str = self.time_service.get_current_datetime()

            if self.app_window:
                # Directly update GUI elements since we are on the main thread
                self.app_window.update_time(time_str)
                self.app_window.update_date(date_str)

                # Schedule the next update
                # Convert interval to milliseconds for 'after'
                interval_ms = config.UPDATE_INTERVAL_SECONDS * 1000
                self._time_update_job_id = self.app_window.after(interval_ms, self._update_time_and_date)
            # No action needed for headless mode regarding time updates

        except Exception as e:
            logger.error(f"Error updating time and date: {e}", exc_info=True)
            # Optionally schedule retry even on error?
            if self.app_window and self.running:
                 interval_ms = config.UPDATE_INTERVAL_SECONDS * 1000
                 self._time_update_job_id = self.app_window.after(interval_ms, self._update_time_and_date)


    def _update_weather(self):
        """Fetch IMS weather data and update GUI or log if headless."""
        logger.info("Attempting to update weather data from IMS...")
        connection_status = False
        api_status = 'error' # Default to error
        current_weather_data = {} # Initialize empty data dict

        try:
            # Fetch data from IMS service
            # Use mock data setting if enabled (though IMS service doesn't have built-in mock)
            # For now, we always fetch live data unless USE_MOCK_DATA is True and handled elsewhere
            if config.USE_MOCK_DATA:
                 logger.warning("Mock data requested, but IMS service doesn't have built-in mock. Skipping fetch.")
                 # You might want to define mock IMS data here if needed
                 current_weather_data = {'temperature': 25, 'humidity': 60} # Example mock
                 connection_status = True
                 api_status = 'mock'
            else:
                success = self.ims_weather.fetch_data()
                connection_status = success # Fetch success implies connection
                if success:
                    api_status = 'ok'
                    measurements = self.ims_weather.get_all_measurements()
                    if measurements:
                        # Extract Temperature (TD) and Humidity (RH)
                        temp_data = measurements.get('TD')
                        humidity_data = measurements.get('RH')

                        current_weather_data['temperature'] = float(temp_data['value']) if temp_data else None
                        current_weather_data['humidity'] = int(humidity_data['value']) if humidity_data else None
                        logger.info(f"IMS Data Fetched: Temp={current_weather_data['temperature']}, Humidity={current_weather_data['humidity']}")
                    else:
                        logger.warning("IMS data fetched successfully, but no measurements found.")
                        api_status = 'error' # Treat as error if no measurements
                else:
                    logger.error("Failed to fetch data from IMS.")
                    api_status = 'error'

            # Prepare result structure for GUI update
            update_payload = {
                'data': current_weather_data,
                'connection_status': connection_status,
                'api_status': api_status # 'ok', 'error', 'mock'
            }

            # Update GUI if it exists
            if self.app_window:
                # Schedule GUI updates on the main Tkinter thread
                self.app_window.after(0, lambda payload=update_payload.copy(): self.app_window.update_current_weather(payload))
                # No forecast update needed
            elif self.headless:
                 # Log fetched data details in headless mode
                 logger.info(f"Headless Weather Update (IMS):")
                 logger.info(f"  Data: {current_weather_data}")
                 logger.info(f"  Connection Status: {connection_status}")
                 logger.info(f"  API Status: {api_status}")

            # Update internal connection status tracker
            if self.last_connection_status != connection_status:
                 logger.debug(f"Connection status updated to: {'Connected' if connection_status else 'Disconnected'}")
                 self.last_connection_status = connection_status

            logger.info("IMS weather data update cycle finished.")

        except Exception as e:
            logger.error(f"Unexpected error during IMS weather update cycle: {e}", exc_info=True)
            # Attempt to update status indicators in GUI to show error state
            if self.app_window:
                # Assume connection failed or other error occurred
                self.app_window.after(0, lambda: self.app_window.update_status_indicators(False, 'error'))
            # Update internal status if possible
            if self.last_connection_status:
                 logger.warning("Connection status changed: Disconnected (due to update error)")
                 self.last_connection_status = False

    def _update_accuweather_data(self):
        """Fetch AccuWeather data (current & forecast) and log."""
        if not self.accuweather_client:
            logger.debug("Skipping AccuWeather update: client not initialized.")
            return

        logger.info("Attempting to update AccuWeather data (current & forecast)...")
        try:
            # Fetch current weather (includes AQI if available)
            # Force refresh to ensure it respects the loop interval, not just cache
            current_result = self.accuweather_client.get_current_weather(force_refresh=True)
            current_data = current_result.get('data', {})
            current_api_status = current_result.get('api_status', 'error')
            current_conn_status = current_result.get('connection_status', False) # Should be true if fetch attempted

            # Fetch forecast
            # Force refresh for the same reason
            forecast_result = self.accuweather_client.get_forecast(force_refresh=True)
            forecast_data = forecast_result.get('data', [])
            forecast_api_status = forecast_result.get('api_status', 'error')
            # forecast_conn_status = forecast_result.get('connection_status', False) # Less critical

            # Log results (especially for headless mode)
            logger.info(f"AccuWeather Update Cycle Finished:")
            logger.info(f"  Current Weather Status: {current_api_status} (Connection: {current_conn_status})")
            logger.debug(f"  Current Data: {current_data}") # Debug level for potentially large data
            logger.info(f"  Forecast Status: {forecast_api_status}")
            logger.debug(f"  Forecast Data Count: {len(forecast_data)}") # Debug level

            # --- Schedule GUI Updates ---
            if self.app_window:
                 # Update current weather section (which now includes AQI)
                 # Note: IMS update_current_weather only updates temp/humidity.
                 # This call will update AQI based on AccuWeather data.
                 # We pass the *current_result* which contains the necessary structure.
                 self.app_window.after(0, lambda res=current_result.copy(): self.app_window.update_current_weather(res))

                 # Update the forecast section
                 self.app_window.after(0, lambda res=forecast_result.copy(): self.app_window.update_forecast(res))
                 logger.debug("Scheduled AccuWeather GUI updates (Current Weather AQI & Forecast).")

        except Exception as e:
            logger.error(f"Unexpected error during AccuWeather update cycle: {e}", exc_info=True)
            # Optionally update GUI status indicators if an error occurs during the fetch
            if self.app_window:
                 # Determine overall status - prioritize error/limit from either fetch
                 final_api_status = 'ok'
                 if current_api_status in ['error', 'limit_reached'] or forecast_api_status in ['error', 'limit_reached']:
                     final_api_status = 'error' if 'error' in [current_api_status, forecast_api_status] else 'limit_reached'

                 # Use the determined status to update indicators
                 self.app_window.after(0, lambda status=final_api_status: self.app_window.update_status_indicators(True, status))


# --- Command Line Argument Parsing ---

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the application."""
    parser = argparse.ArgumentParser(description='Weather Display Application')
    # Restore API key argument for AccuWeather
    parser.add_argument(
        '--api-key',
        help='AccuWeather API key (overrides environment variable/config)'
    ) # Correctly closed parenthesis
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock data instead of live API calls'
    )
    parser.add_argument(
        '--windowed',
        action='store_true',
        help='Run in windowed mode (overrides FULLSCREEN config)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run without GUI (logs data to console/file)'
    )
    return parser.parse_args()


# --- Main Execution ---

def wait_for_internet(max_wait_seconds: int = 60, check_interval: int = 5) -> bool:
    """
    Wait for internet connection for a maximum duration.

    Args:
        max_wait_seconds: Maximum time to wait in seconds.
        check_interval: How often to check the connection in seconds.

    Returns:
        True if connection is established within the time limit, False otherwise.
    """
    start_time = time.time()
    logger.info("Waiting for internet connection...")
    while time.time() - start_time < max_wait_seconds:
        if check_internet_connection():
            logger.info("Internet connection established.")
            return True
        logger.info(f"No connection. Retrying in {check_interval} seconds...")
        time.sleep(check_interval)
    logger.error(f"No internet connection after {max_wait_seconds} seconds.")
    return False

def main():
    """Main entry point: parses args, configures, creates, and starts the app."""
    args = parse_arguments()

    # --- Configuration Override ---
    # Apply command-line arguments to override config settings
    # Note: API key is passed directly to the constructor, not overriding config globally here
    if args.mock:
        logger.info("Enabling mock data mode via command line argument.")
        config.USE_MOCK_DATA = True
    if args.windowed:
        logger.info("Disabling fullscreen mode via command line argument.")
        config.FULLSCREEN = False

    # --- Pre-run Checks ---
    # API key check is handled implicitly by AccuWeatherClient initialization below
    # (it logs errors/warnings if no key is found and mock data is not enabled)

    # Wait for internet connection if not using mock data
    if not config.USE_MOCK_DATA:
        if not wait_for_internet():
            logger.critical("Exiting due to lack of internet connection.")
            sys.exit(1)

    # --- Application Initialization and Start ---
    app: Optional[WeatherDisplayApp] = None
    try:
        logger.info(f"Using location: '{config.LOCATION}'")
        logger.info(f"Headless mode: {args.headless}")
        logger.info(f"Mock data mode: {config.USE_MOCK_DATA}")
        logger.info(f"Using IMS Station: '{config.IMS_STATION_NAME}'")
        if app and app.accuweather_client: # Check if client was initialized
             logger.info(f"Using AccuWeather Location: '{app.accuweather_client.location_query}'")
             logger.info(f"AccuWeather Language: '{app.accuweather_client.language}'")
        else:
             logger.warning("AccuWeather client not available.")


        app = WeatherDisplayApp(
            headless=args.headless,
            api_key=args.api_key # Pass API key from args
        )
        app.start() # Starts GUI mainloop or headless wait loop

    except RuntimeError as e:
         # Catch specific errors like missing display during init
         logger.critical(f"Application initialization failed: {e}")
         sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping application...")
        if app:
            app.stop()
    except Exception as e:
        logger.critical(f"An unexpected error occurred in main: {e}", exc_info=True)
        if app:
            app.stop() # Attempt graceful shutdown
        sys.exit(1)
    finally:
        # Ensure stop is called even if mainloop/headless loop exits unexpectedly
        if app and app.running:
            logger.warning("Main loop exited unexpectedly. Ensuring application stops.")
            app.stop()
        logger.info("Application shutdown complete.")


if __name__ == "__main__":
    main()
