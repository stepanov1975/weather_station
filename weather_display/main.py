#!/usr/bin/env python3
"""
Main Entry Point for the Weather Display Application.

This script serves as the primary executable for launching the Weather Display.
It is responsible for:
- Parsing command-line arguments (e.g., API keys, headless mode).
- Setting up logging for monitoring application activity.
- Initializing core services:
    - TimeService: For retrieving and formatting the current time and date.
    - IMSLastHourWeather: For fetching data from the Israel Meteorological Service.
    - AccuWeatherClient: For fetching current conditions, forecasts, and AQI
      from AccuWeather.
- Optionally initializing the graphical user interface (GUI) using AppWindow,
  unless running in headless mode.
- Managing background threads for periodic tasks:
    - Fetching weather updates from IMS and AccuWeather at configured intervals.
    - Monitoring internet connectivity and triggering immediate updates upon
      reconnection.
- Handling graceful shutdown via signals (SIGINT, SIGTERM) or GUI closure.
- Coordinating data flow between services and the GUI.

Designed to be run on various platforms, including Raspberry Pi 4, for
displaying weather information.
"""

# Standard library imports
import os
import sys
import time
import logging
import threading
import argparse
import signal
from typing import Optional, List, Dict, Any # Ensure necessary types are imported

# Local application imports
# Assuming the script is run from the project root or the package is installed
try:
    from weather_display import config
    from weather_display.gui.app_window import AppWindow
    from weather_display.services.time_service import TimeService
    from weather_display.services.ims_lasthour import IMSLastHourWeather
    from weather_display.services.weather_api import AccuWeatherClient
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
        from weather_display.services.ims_lasthour import IMSLastHourWeather
        from weather_display.services.weather_api import AccuWeatherClient
        from weather_display.utils.helpers import check_internet_connection
    except ImportError:
        print("Failed to import necessary modules even after path adjustment.")
        print("Please ensure the script is run correctly relative to the package structure or install the package.")
        sys.exit(1)


# --- Global Logger Setup ---
# Configure basic logging. Logs to both console (StreamHandler) and a file
# ('weather_display.log'). The format includes timestamp, logger name, level,
# and the message. More advanced configuration could involve rotating file
# handlers or different formats per handler.
logging.basicConfig(
    level=logging.INFO, # Set the minimum logging level (e.g., DEBUG, INFO, WARNING)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(), # Output logs to the console
        logging.FileHandler('weather_display.log') # Output logs to a file
    ]
)
# Get a logger instance specific to this module (__name__ resolves to 'weather_display.main')
logger = logging.getLogger(__name__)


class WeatherDisplayApp:
    """
    Orchestrates the Weather Display application's components and lifecycle.

    This class acts as the central controller, initializing services (time, weather APIs),
    managing the GUI window (if not headless), and running background threads for
    periodic data updates and connection monitoring. It handles the main application
    loop and graceful shutdown procedures.

    Attributes:
        headless (bool): If True, the application runs without a graphical interface,
                         logging data instead of displaying it. Set via command-line.
        running (bool): A flag used to signal background threads whether they should
                        continue running. Set to False to initiate shutdown.
        time_service (TimeService): An instance providing current time and date.
        ims_weather (IMSLastHourWeather): An instance for fetching weather data from
                                          the Israel Meteorological Service (IMS).
        accuweather_client (Optional[AccuWeatherClient]): An instance for fetching
                                                          weather data from AccuWeather.
                                                          Can be None if initialization fails.
        app_window (Optional[AppWindow]): The main GUI window instance. None if headless.
        last_connection_status (bool): Stores the last known internet connection state
                                       to detect changes (e.g., reconnection).
        _update_threads (List[threading.Thread]): A list holding the background threads
                                                  responsible for periodic updates.
        _time_update_job_id (Optional[str]): Stores the ID returned by Tkinter's `after`
                                             method for the scheduled time update,
                                             allowing it to be cancelled on shutdown.
    """

    def __init__(self, headless: bool = False, api_key: Optional[str] = None):
        """
        Initializes the Weather Display application.

        Sets up core services (Time, IMS Weather, AccuWeather), configures the
        AccuWeather client with the provided API key (or falls back to config/env),
        and optionally creates the GUI window based on the headless flag.

        Args:
            headless (bool): If True, prevents GUI initialization. Defaults to False.
            api_key (Optional[str]): The AccuWeather API key provided via command line.
                                     If None, the AccuWeatherClient will attempt to find
                                     the key in the environment or config file.
        """
        self.headless: bool = headless
        self.running: bool = False # Controls thread loops, set True in start()
        self._update_threads: List[threading.Thread] = []
        self._time_update_job_id: Optional[str] = None # For cancelling Tkinter 'after' job

        logger.info("Initializing application components...")

        # Initialize core services
        self.time_service = TimeService()
        logger.debug("TimeService initialized.")

        # Initialize IMS weather service using station name from config
        try:
            self.ims_weather = IMSLastHourWeather(station_name=config.IMS_STATION_NAME)
            logger.info(f"IMSLastHourWeather initialized for station: {config.IMS_STATION_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize IMSLastHourWeather: {e}", exc_info=True)
            # Decide if this is critical; for now, we might proceed without IMS
            self.ims_weather = None # Ensure it's None if failed

        # Initialize AccuWeather client
        self.accuweather_client: Optional[AccuWeatherClient] = None
        try:
            # Check if necessary AccuWeather config exists before initializing
            # Primarily checks if the base URL is defined, assuming other parts exist.
            if hasattr(config, 'ACCUWEATHER_BASE_URL'):
                 # Pass the command-line api_key (if provided) to the client.
                 # The client itself handles the priority: cmd-line > env > config.
                 self.accuweather_client = AccuWeatherClient(api_key=api_key)
                 logger.info("AccuWeatherClient initialized.")
                 # Log a warning if no API key was ultimately found by the client.
                 if not self.accuweather_client.api_key:
                     logger.warning("AccuWeather API key not found in args, config, or environment. Client may use mock data or fail requests.")
                 elif api_key:
                     logger.info("Using AccuWeather API key provided via command line argument.")
                 # Log the location being used by AccuWeather
                 logger.info(f"AccuWeather client configured for location: '{self.accuweather_client.location_query}' and language: '{self.accuweather_client.language}'")
            else:
                 logger.warning("AccuWeather base URL (ACCUWEATHER_BASE_URL) not found in config. AccuWeather client NOT initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize AccuWeatherClient: {e}", exc_info=True)
            # Continue without AccuWeather if initialization fails

        # Initialize GUI only if not in headless mode
        self.app_window: Optional[AppWindow] = None
        if not self.headless:
            logger.info("Initializing Graphical User Interface (GUI)...")
            # Check for display availability (essential for GUI frameworks like Tkinter)
            if not os.environ.get('DISPLAY'):
                 logger.error("No display environment detected (DISPLAY variable not set). GUI cannot be created.")
                 # This is generally a fatal error for non-headless mode.
                 raise RuntimeError("Cannot initialize GUI without a display environment. Consider running with --headless.")
            try:
                # Create the main application window instance
                self.app_window = AppWindow()
                logger.info("AppWindow GUI initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize AppWindow: {e}", exc_info=True)
                # Propagate the error as GUI is critical for non-headless mode
                raise RuntimeError("GUI initialization failed.") from e
        else:
            logger.info("Running in headless mode (no GUI will be displayed).")

        # Track connection status for triggering immediate updates on reconnect
        # Perform an initial check; background thread will monitor continuously.
        self.last_connection_status: bool = check_internet_connection()
        logger.info(f"Initial internet connection status: {'Connected' if self.last_connection_status else 'Disconnected'}")

        # Store the last known valid Air Quality data from AccuWeather
        self.last_aqi_data: Optional[Dict[str, Any]] = None
        logger.debug("Initialized last_aqi_data storage.")

        # Store the timestamp of the last successful AccuWeather API call
        self.last_accuweather_success_time: Optional[float] = None
        logger.debug("Initialized last_accuweather_success_time storage.")

        logger.info("Weather Display application initialization complete.")

    def start(self):
        """
        Starts the application's main execution loop.

        Sets the `running` flag to True, starts background update threads,
        performs initial data fetches and GUI updates (if applicable), and
        then either enters the Tkinter main loop (for GUI mode) or waits
        indefinitely while background threads run (for headless mode).
        Handles signal trapping for graceful shutdown in headless mode.
        """
        if self.running:
            logger.warning("Application start() called but it is already running.")
            return

        self.running = True
        logger.info("Starting application...")

        # Start background threads for weather updates and connection monitoring
        self._start_update_threads()

        if self.app_window:
            logger.info("Performing initial GUI updates...")
            # Perform initial data fetches and GUI updates before starting the main loop
            self._update_time_and_date() # Initial time/date display
            if self.ims_weather:
                self._update_weather() # Initial IMS weather fetch and display
            if self.accuweather_client:
                self._update_accuweather_data() # Initial AccuWeather fetch and display

            logger.info("Starting GUI main loop (Tkinter)...")
            # Start the Tkinter main event loop. This call blocks until the window
            # is closed by the user or by a call to `app_window.destroy()`.
            self.app_window.mainloop()

            # Code here executes after the mainloop finishes (window closed)
            logger.info("GUI main loop exited.")
            # Ensure the application stops cleanly if the window is closed
            self.stop()

        elif self.headless:
            logger.info("Running in headless mode. Update loops active in background.")
            logger.info("Press Ctrl+C to stop the application.")
            # Set up signal handlers for graceful shutdown in headless mode
            # SIGINT (Ctrl+C) and SIGTERM are common termination signals.
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)

            # Keep the main thread alive while background threads do their work.
            # The loop checks the `running` flag, which is set to False by `stop()`.
            while self.running:
                try:
                    # Sleep prevents this loop from consuming 100% CPU.
                    time.sleep(1)
                except InterruptedError:
                    # Catch potential interruption if signal handling happens mid-sleep
                    logger.debug("Main headless loop sleep interrupted.")
                    continue # Re-check self.running status

            logger.info("Headless run finished.")
            # Stop might have already been called by signal handler, but ensure cleanup
            if self.running: # If loop exited for other reasons
                 self.stop()

        else:
             # This state should theoretically not be reachable if __init__ is correct.
             logger.error("Application state invalid: No GUI and not in headless mode. Stopping.")
             self.stop()


    def stop(self):
        """
        Stops the application gracefully.

        Sets the `running` flag to False to signal background threads to exit,
        cancels any scheduled Tkinter `after` jobs (like the time update),
        waits for background threads to join (finish), and destroys the GUI
        window if it exists.
        """
        if not self.running:
            logger.info("Application stop() called but it was already stopped.")
            return

        logger.info("Stopping application gracefully...")
        self.running = False # Signal all background loops to terminate

        # Allow a brief moment for threads to notice the flag change
        time.sleep(0.5)

        # Cancel the scheduled Tkinter time update job if it's running
        if self.app_window and self._time_update_job_id:
            try:
                logger.debug(f"Cancelling scheduled time update job (ID: {self._time_update_job_id}).")
                self.app_window.after_cancel(self._time_update_job_id)
                self._time_update_job_id = None
            except Exception as e:
                # Log error but continue shutdown; Tkinter might raise errors if window is closing
                logger.error(f"Error cancelling Tkinter time update job: {e}")

        # Wait for background threads (weather, connection) to finish
        threads_to_join = [t for t in self._update_threads if t.is_alive()]
        if threads_to_join:
            logger.debug(f"Waiting for {len(threads_to_join)} background thread(s) to join...")
            for thread in threads_to_join:
                try:
                    thread.join(timeout=2.0) # Wait max 2 seconds per thread
                    if thread.is_alive():
                         logger.warning(f"Thread '{thread.name}' did not join within the timeout.")
                except Exception as e:
                     logger.error(f"Error joining thread '{thread.name}': {e}")
            self._update_threads = [] # Clear the list after attempting to join

        # Destroy the GUI window if it exists and hasn't been destroyed already
        if self.app_window:
            logger.info("Destroying GUI window...")
            try:
                # Check if the window still exists before destroying
                # This avoids errors if it was closed manually already
                if self.app_window.winfo_exists():
                    self.app_window.destroy()
                self.app_window = None # Clear reference
            except Exception as e:
                 logger.error(f"Error destroying GUI window: {e}")

        logger.info("Application stopped successfully.")

    def _handle_signal(self, signum, frame):
        """
        Signal handler for SIGINT (Ctrl+C) and SIGTERM in headless mode.

        Initiates the graceful shutdown process by calling `stop()`.

        Args:
            signum: The signal number received.
            frame: The current stack frame (unused here).
        """
        signal_name = signal.Signals(signum).name
        logger.warning(f"Received signal {signal_name} ({signum}). Initiating shutdown...")
        # Set running to False immediately in case stop() takes time
        self.running = False
        # Call the main stop method to handle cleanup
        self.stop()
        # Exit cleanly after stopping
        sys.exit(0)

    # --- Background Update Logic ---

    def _start_update_threads(self):
        """
        Creates and starts the background threads for periodic updates.

        Initializes threads for:
        - IMS weather data fetching (`_weather_update_loop`)
        - AccuWeather data fetching (`_accuweather_update_loop`), if client exists.
        - Internet connection monitoring (`_connection_monitoring_loop`).

        Note: Time updates are handled by the main GUI thread using Tkinter's `after`
        mechanism, not a separate thread, to avoid cross-thread GUI update issues.
        """
        logger.info("Starting background update threads...")
        self._update_threads = [] # Ensure list is clear before starting

        # IMS Weather Update Thread (if IMS client initialized)
        if self.ims_weather:
            ims_thread = threading.Thread(
                target=self._weather_update_loop,
                name="IMSWeatherUpdateThread",
                daemon=True # Allows app to exit even if thread is running
            )
            self._update_threads.append(ims_thread)
        else:
            logger.warning("IMS client not initialized, skipping IMS update thread.")

        # AccuWeather Update Thread (if AccuWeather client initialized)
        if self.accuweather_client:
            accu_thread = threading.Thread(
                target=self._accuweather_update_loop,
                name="AccuWeatherUpdateThread",
                daemon=True
            )
            self._update_threads.append(accu_thread)
        else:
            logger.warning("AccuWeather client not initialized, skipping AccuWeather update thread.")

        # Connection Monitoring Thread (always run)
        conn_thread = threading.Thread(
            target=self._connection_monitoring_loop,
            name="ConnectionMonitorThread",
            daemon=True
        )
        self._update_threads.append(conn_thread)

        # Start all created threads
        for thread in self._update_threads:
            logger.debug(f"Starting thread: {thread.name}")
            thread.start()

        logger.info(f"Started {len(self._update_threads)} background update threads.")


    def _weather_update_loop(self):
        """
        Background thread loop for periodically fetching IMS weather data.

        Runs continuously while `self.running` is True. Waits for the configured
        IMS update interval, then calls `_update_weather()` to fetch and process
        the data. Handles the `self.running` flag check during sleep to allow
        for quick shutdown.
        """
        if not self.ims_weather:
            logger.error("IMS weather update loop started but IMS client is not initialized. Loop exiting.")
            return

        logger.debug("IMS weather update loop started.")
        # Initial update is handled by start() before this loop begins.
        # This loop handles subsequent periodic updates.
        while self.running:
            interval_seconds = config.IMS_UPDATE_INTERVAL_MINUTES * 60
            logger.debug(f"IMS loop: Sleeping for {interval_seconds} seconds until next update.")

            # Sleep in small increments to check `self.running` frequently
            for _ in range(int(interval_seconds)):
                 if not self.running:
                     break # Exit sleep early if stop signal received
                 time.sleep(1)

            if not self.running:
                break # Exit loop if stop signal received during sleep

            # Perform the actual weather update
            logger.debug("IMS loop: Interval finished, calling _update_weather().")
            self._update_weather()

        logger.debug("IMS weather update loop finished.")

    def _accuweather_update_loop(self):
        """
        Background thread loop for periodically fetching AccuWeather data.

        Runs continuously while `self.running` is True. Waits for the configured
        AccuWeather update interval, then calls `_update_accuweather_data()` to
        fetch and process current weather, forecast, and AQI. Handles the
        `self.running` flag check during sleep for quick shutdown.
        """
        if not self.accuweather_client:
            logger.error("AccuWeather update loop started but client is not initialized. Loop exiting.")
            return

        logger.debug("AccuWeather update loop started.")
        # Initial update handled by start()
        while self.running:
            interval_seconds = config.ACCUWEATHER_UPDATE_INTERVAL_MINUTES * 60
            logger.debug(f"AccuWeather loop: Sleeping for {interval_seconds} seconds until next update.")

            # Sleep in small increments to check `self.running` frequently
            for _ in range(int(interval_seconds)):
                 if not self.running:
                     break # Exit sleep early if stop signal received
                 time.sleep(1)

            if not self.running:
                break # Exit loop if stop signal received during sleep

            # Perform the actual AccuWeather data update
            logger.debug("AccuWeather loop: Interval finished, calling _update_accuweather_data().")
            self._update_accuweather_data()

        logger.debug("AccuWeather update loop finished.")


    def _connection_monitoring_loop(self):
        """
        Background thread loop to periodically check internet connectivity.

        Runs continuously while `self.running` is True. Checks the internet
        connection status at a fixed interval. If the connection state changes
        (especially from disconnected to connected), it triggers immediate,
        one-off updates for both IMS and AccuWeather data in separate threads.
        Updates the `self.last_connection_status` attribute.
        """
        logger.debug("Connection monitoring loop started.")
        check_interval_seconds = 30 # How often to check the connection status

        while self.running:
            try:
                current_status = check_internet_connection()

                # Detect if connection was just restored
                if not self.last_connection_status and current_status:
                    logger.info("Internet connection restored. Triggering immediate weather updates.")
                    # Trigger immediate updates in non-blocking threads
                    if self.ims_weather:
                        ims_update_thread = threading.Thread(target=self._update_weather, name="IMSImmediateUpdate", daemon=True)
                        ims_update_thread.start()
                    if self.accuweather_client:
                        accu_update_thread = threading.Thread(target=self._update_accuweather_data, name="AccuWeatherImmediateUpdate", daemon=True)
                        accu_update_thread.start()

                # Log status change only if it actually changed
                if self.last_connection_status != current_status:
                     status_text = 'Connected' if current_status else 'Disconnected'
                     log_msg = f"Connection status changed: {status_text}"
                     # Log differently based on mode (GUI updates indicators visually)
                     if self.headless:
                         logger.info(log_msg)
                     else:
                         logger.debug(log_msg + " (GUI indicators will reflect this)")
                     # Update the tracked status
                     self.last_connection_status = current_status
                else:
                     logger.debug(f"Connection status remains: {'Connected' if current_status else 'Disconnected'}")


                # Sleep until the next check interval
                logger.debug(f"Connection loop: Sleeping for {check_interval_seconds} seconds.")
                for _ in range(check_interval_seconds):
                     if not self.running:
                         break # Exit sleep early if stop signal received
                     time.sleep(1)

                if not self.running:
                    break # Exit loop if stop signal received during sleep

            except Exception as e:
                logger.error(f"Error in connection monitoring loop: {e}", exc_info=True)
                # Avoid crashing the loop; wait before retrying
                time.sleep(check_interval_seconds)

        logger.debug("Connection monitoring loop finished.")

    # --- Data Update Actions ---

    def _update_time_and_date(self):
        """
        Fetches the current time and date and updates the GUI.

        This method is designed to be called repeatedly by the Tkinter `after`
        scheduler, running on the main GUI thread. It gets formatted time and
        date strings from the TimeService and updates the corresponding labels
        in the AppWindow. It then schedules itself to run again after the
        configured interval.
        """
        # Check if the application should still be running before proceeding
        if not self.running:
             logger.debug("Skipping time update because application is stopping.")
             return

        logger.debug("Updating time and date display...")
        try:
            # Get formatted time and date strings
            time_str, date_str = self.time_service.get_current_datetime()

            if self.app_window:
                # Update the GUI labels directly (safe because this runs on the main thread)
                self.app_window.update_time(time_str)
                self.app_window.update_date(date_str)

                # Schedule the next call to this method
                interval_ms = config.UPDATE_INTERVAL_SECONDS * 1000
                # Store the job ID so it can be cancelled on stop()
                self._time_update_job_id = self.app_window.after(interval_ms, self._update_time_and_date)
            # No action needed for headless mode regarding time display

        except Exception as e:
            logger.error(f"Error updating time and date display: {e}", exc_info=True)
            # Attempt to reschedule even if an error occurred to maintain the loop
            if self.app_window and self.running:
                 try:
                     interval_ms = config.UPDATE_INTERVAL_SECONDS * 1000
                     self._time_update_job_id = self.app_window.after(interval_ms, self._update_time_and_date)
                 except Exception as schedule_e:
                     logger.error(f"Failed to reschedule time update after error: {schedule_e}")


    def _update_weather(self):
        """
        Fetches the latest weather data from the IMS service and updates the GUI.

        This method is called periodically by the `_weather_update_loop` thread or
        triggered immediately upon connection restoration. It interacts with the
        `IMSLastHourWeather` service, processes the results, and schedules GUI
        updates using `app_window.after(0, ...)` to ensure thread safety.
        Updates connection and API status indicators in the GUI.
        Logs data in headless mode.
        """
        if not self.ims_weather:
            logger.warning("Skipping IMS weather update: IMS client not initialized.")
            return

        logger.info("Attempting to update weather data from IMS...")
        connection_status = False # Assume disconnected initially
        api_status = 'error' # Default to error until success confirmed
        current_weather_data: Dict[str, Any] = {} # Initialize empty data dict

        try:
            # Check if mock data is enabled globally
            if config.USE_MOCK_DATA:
                 logger.warning("Mock data mode enabled. Skipping live IMS fetch.")
                 # Define mock IMS data structure (adjust as needed)
                 current_weather_data = {'temperature': 22.5, 'humidity': 55}
                 connection_status = True # Mock assumes connection is fine
                 api_status = 'mock'
            else:
                # Attempt to fetch live data from the IMS service
                success = self.ims_weather.fetch_data()
                connection_status = success # Fetch success implies connection worked at that moment

                if success:
                    api_status = 'ok' # Mark API as OK if fetch succeeded
                    measurements = self.ims_weather.get_all_measurements()
                    if measurements:
                        # Extract relevant measurements (Temperature 'TD', Humidity 'RH')
                        temp_data = measurements.get('TD')
                        humidity_data = measurements.get('RH')

                        # Safely extract values, converting to appropriate types
                        current_weather_data['temperature'] = float(temp_data['value']) if temp_data and temp_data.get('value') is not None else None
                        current_weather_data['humidity'] = int(humidity_data['value']) if humidity_data and humidity_data.get('value') is not None else None

                        logger.info(f"IMS Data Fetched: Temp={current_weather_data.get('temperature')}, Humidity={current_weather_data.get('humidity')}")

                        # --- Merge stored AQI data ---
                        if self.last_aqi_data:
                            logger.debug(f"Merging stored AQI data: {self.last_aqi_data}")
                            current_weather_data.update(self.last_aqi_data)
                        else:
                            logger.debug("No stored AQI data available to merge.")
                        # --- End Merge ---
                    else:
                        logger.warning("IMS data fetched successfully, but no measurements found in the response.")
                        api_status = 'error' # Treat as error if expected data is missing
                else:
                    logger.error("Failed to fetch data from IMS service.")
                    # Keep api_status as 'error', connection_status is already False

            # Update GUI if it exists, ensuring it runs on the main thread
            if self.app_window:
                # Prepare the payload for the main weather update
                update_payload = {
                    'data': current_weather_data,
                    'connection_status': connection_status,
                    'api_status': api_status # Status specific to this IMS fetch ('ok', 'error', 'mock')
                }
                # Use after(0, ...) to schedule the update on the main Tkinter event loop
                # Pass a copy of the payload to avoid potential race conditions if the dict is modified later
                self.app_window.after(0, lambda payload=update_payload.copy(): self.app_window.update_current_weather(payload))

                # Update the status indicators based *only* on this IMS fetch.
                # Pass None for the AccuWeather success time, as this update doesn't involve it.
                # The GUI method will need to handle this None value appropriately.
                self.app_window.after(0, lambda conn=connection_status, api=api_status: self.app_window.update_status_indicators(conn, api, None)) # Pass None for last_success_time

            elif self.headless:
                 # Log fetched data details clearly in headless mode
                 logger.info(f"Headless Weather Update (IMS):")
                 logger.info(f"  Data: {current_weather_data}")
                 logger.info(f"  Connection Status during fetch: {connection_status}")
                 logger.info(f"  API Status: {api_status}")

            # Update the application's overall connection status tracker if it changed
            if self.last_connection_status != connection_status:
                 logger.debug(f"Overall connection status updated based on IMS fetch: {'Connected' if connection_status else 'Disconnected'}")
                 self.last_connection_status = connection_status

            logger.info("IMS weather data update cycle finished.")

        except Exception as e:
            logger.error(f"Unexpected error during IMS weather update cycle: {e}", exc_info=True)
            # Attempt to update status indicators in GUI to show error state
            if self.app_window:
                # Schedule an update to show error status (assuming connection failed or other error)
                self.app_window.after(0, lambda: self.app_window.update_status_indicators(False, 'error'))
            # Update internal connection status tracker if an error implies disconnection
            if self.last_connection_status:
                 logger.warning("Connection status likely changed to Disconnected due to IMS update error.")
                 self.last_connection_status = False

    def _update_accuweather_data(self):
        """
        Fetches the latest data from AccuWeather (current, forecast, AQI) and updates GUI.

        Called periodically by the `_accuweather_update_loop` or immediately upon
        connection restoration. Interacts with the `AccuWeatherClient`, processes
        results, and schedules GUI updates using `app_window.after(0, ...)` for
        thread safety. Updates relevant status indicators. Logs data in headless mode.
        """
        if not self.accuweather_client:
            logger.debug("Skipping AccuWeather update: client not initialized.")
            return

        logger.info("Attempting to update AccuWeather data (current conditions, AQI, forecast)...")
        current_result: Dict[str, Any] = {}
        forecast_result: Dict[str, Any] = {}
        final_api_status = 'error' # Assume error until successful fetches
        final_conn_status = False # Assume disconnected until successful fetches

        try:
            # Fetch current weather (which includes AQI)
            # Use force_refresh=True to ensure it bypasses cache and respects the update interval.
            current_result = self.accuweather_client.get_current_weather(force_refresh=True)
            current_api_status = current_result.get('api_status', 'error')
            current_conn_status = current_result.get('connection_status', False)
            logger.info(f"AccuWeather current weather fetch status: {current_api_status}, Connection: {current_conn_status}")
            logger.debug(f"AccuWeather current data received: {current_result.get('data', {})}")

            # Fetch forecast data
            # Use force_refresh=True for consistency with update interval.
            forecast_result = self.accuweather_client.get_forecast(force_refresh=True)
            forecast_api_status = forecast_result.get('api_status', 'error')
            # forecast_conn_status = forecast_result.get('connection_status', False) # Connection status from current fetch is usually sufficient
            logger.info(f"AccuWeather forecast fetch status: {forecast_api_status}")
            logger.debug(f"AccuWeather forecast data count: {len(forecast_result.get('data', []))}")

            # Determine overall status based on both fetches
            final_conn_status = current_conn_status # Primarily based on current weather fetch attempt
            if current_api_status == 'ok' and forecast_api_status == 'ok':
                final_api_status = 'ok'
                # Update the last successful update time
                self.last_accuweather_success_time = time.time()
                logger.debug(f"Updated last AccuWeather success time to: {self.last_accuweather_success_time}")
            elif 'limit_reached' in [current_api_status, forecast_api_status]:
                final_api_status = 'limit_reached'
            elif 'mock' in [current_api_status, forecast_api_status]:
                 final_api_status = 'mock' # If either uses mock data
                 # Optionally clear success time if using mock? Or keep last real success? Keep for now.
            else:
                final_api_status = 'error' # If any fetch resulted in an error

            logger.info(f"AccuWeather overall update status: API={final_api_status}, Connection={final_conn_status}, Last Success Time: {self.last_accuweather_success_time}")

            # --- Store AQI data if fetch was successful ---
            if current_api_status == 'ok' and 'data' in current_result and current_result['data']:
                aqi_category = current_result['data'].get('air_quality_category')
                aqi_index = current_result['data'].get('air_quality_index')
                # Only update if at least category is present
                if aqi_category is not None:
                    self.last_aqi_data = {
                        'air_quality_category': aqi_category,
                        'air_quality_index': aqi_index # Store index even if None
                    }
                    logger.debug(f"Stored latest AQI data: {self.last_aqi_data}")
                else:
                    # If AQI data is missing in a successful fetch, clear the stored data
                    # to avoid showing stale AQI if it becomes unavailable later.
                    if self.last_aqi_data is not None:
                         logger.debug("Clearing stale AQI data as it was not present in the latest successful AccuWeather fetch.")
                         self.last_aqi_data = None
            elif current_api_status != 'ok' and current_api_status != 'mock':
                 # Optionally clear stored AQI if the fetch failed, to avoid showing stale data indefinitely.
                 # Decide based on desired behavior: show last known good AQI or clear on error.
                 # logger.debug("Clearing stored AQI data due to AccuWeather fetch failure.")
                 # self.last_aqi_data = None
                 pass # Current behavior: Keep last known good AQI even if fetch fails

            # --- Schedule GUI Updates (if GUI exists) ---
            if self.app_window:
                 # Update current weather section (includes AQI from AccuWeather)
                 # Pass the full result dictionary as update_current_weather expects it
                 # Note: The IMS update will handle merging AQI later if it runs after this.
                 self.app_window.after(0, lambda res=current_result.copy(): self.app_window.update_current_weather(res))

                 # Update the forecast section
                 # Pass the full forecast result dictionary
                 self.app_window.after(0, lambda res=forecast_result.copy(): self.app_window.update_forecast(res))

                 # Update the main status indicators based on the combined status, passing the success time
                 self.app_window.after(0, lambda conn=final_conn_status, api=final_api_status, success_time=self.last_accuweather_success_time: self.app_window.update_status_indicators(conn, api, success_time))

                 logger.debug("Scheduled AccuWeather GUI updates (Current Weather/AQI, Forecast, Status).")

            elif self.headless:
                 # Log summary in headless mode
                 logger.info(f"Headless AccuWeather Update:")
                 logger.info(f"  Current Data: {current_result.get('data', {})}")
                 logger.info(f"  Forecast Data Count: {len(forecast_result.get('data', []))}")
                 logger.info(f"  Overall Status: API={final_api_status}, Connection={final_conn_status}")

            # Update the application's overall connection status tracker
            if self.last_connection_status != final_conn_status:
                 logger.debug(f"Overall connection status updated based on AccuWeather fetch: {'Connected' if final_conn_status else 'Disconnected'}")
                 self.last_connection_status = final_conn_status

        except Exception as e:
            logger.error(f"Unexpected error during AccuWeather update cycle: {e}", exc_info=True)
            # Attempt to update GUI status indicators to reflect the error, passing the last known success time
            if self.app_window:
                 # Schedule update to show error status, but include the last success time if available
                 self.app_window.after(0, lambda success_time=self.last_accuweather_success_time: self.app_window.update_status_indicators(False, 'error', success_time))
            # Update internal connection status tracker if error implies disconnection
            if self.last_connection_status:
                 logger.warning("Connection status likely changed to Disconnected due to AccuWeather update error.")
                 self.last_connection_status = False

        logger.info("AccuWeather data update cycle finished.")


# --- Command Line Argument Parsing ---

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments provided when running the script.

    Defines and processes arguments for:
    - `--api-key`: Specifies the AccuWeather API key, overriding other sources.
    - `--mock`: Enables mock data mode, preventing live API calls.
    - `--windowed`: Forces the application to run in a window, overriding the
                    `FULLSCREEN` setting in `config.py`.
    - `--headless`: Runs the application without a GUI, logging data instead.

    Returns:
        argparse.Namespace: An object containing the parsed argument values.
                            Access values like `args.api_key`, `args.mock`, etc.
    """
    parser = argparse.ArgumentParser(
        description='Weather Display Application - Fetches and displays weather information.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Shows default values in help
    )
    # Argument for AccuWeather API Key
    parser.add_argument(
        '--api-key',
        type=str, # Expect a string value
        default=None, # Default is None, meaning client will check env/config
        help='AccuWeather API key. Overrides ACCUWEATHER_API_KEY environment variable and config file setting.'
    )
    # Argument to enable mock data mode
    parser.add_argument(
        '--mock',
        action='store_true', # Makes it a flag, value is True if present
        help='Use pre-defined mock data for testing instead of making live API calls.'
    )
    # Argument to force windowed mode
    parser.add_argument(
        '--windowed',
        action='store_true',
        help='Run in windowed mode, overriding the FULLSCREEN setting in config.py.'
    )
    # Argument to enable headless (no GUI) mode
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run without a graphical user interface. Logs data to console and file.'
    )

    args = parser.parse_args()
    logger.debug(f"Parsed command line arguments: {args}")
    return args


# --- Main Execution Logic ---

def wait_for_internet(max_wait_seconds: int = 60, check_interval: int = 5) -> bool:
    """
    Waits for an active internet connection before proceeding.

    Checks for connectivity repeatedly at a specified interval until a maximum
    wait time is reached. This is useful at startup to ensure API calls can
    be made, unless mock data is being used.

    Args:
        max_wait_seconds (int): The maximum total time (in seconds) to wait for
                                a connection. Defaults to 60.
        check_interval (int): The time (in seconds) to wait between connection
                              checks. Defaults to 5.

    Returns:
        bool: True if an internet connection is detected within the time limit,
              False otherwise.
    """
    start_time = time.time()
    logger.info("Checking for internet connection...")
    while time.time() - start_time < max_wait_seconds:
        if check_internet_connection():
            logger.info("Internet connection established.")
            return True
        # Log message includes remaining wait time estimate
        remaining_time = max(0, int(max_wait_seconds - (time.time() - start_time)))
        logger.info(f"No connection detected. Retrying in {check_interval} seconds... (max wait remaining: ~{remaining_time}s)")
        time.sleep(check_interval)

    logger.error(f"Failed to establish internet connection after {max_wait_seconds} seconds.")
    return False

def main():
    """
    Main execution function for the Weather Display application.

    Orchestrates the application lifecycle:
    1. Parses command-line arguments.
    2. Overrides configuration settings based on arguments (mock, windowed).
    3. Waits for internet connection if not using mock data.
    4. Initializes the main `WeatherDisplayApp` instance, passing headless flag
       and API key argument.
    5. Starts the application using `app.start()`, which enters the main loop
       (GUI or headless wait).
    6. Includes error handling for initialization failures and unexpected errors
       during runtime, attempting graceful shutdown via `app.stop()`.
    7. Ensures `app.stop()` is called in a `finally` block for cleanup.
    """
    args = parse_arguments()
    logger.info("Weather Display Application starting...")

    # --- Configuration Overrides ---
    # Apply command-line arguments that modify behavior defined in config.py
    if args.mock:
        logger.info("OVERRIDE: Enabling mock data mode via command line argument (--mock).")
        config.USE_MOCK_DATA = True
    if args.windowed:
        logger.info("OVERRIDE: Forcing windowed mode via command line argument (--windowed).")
        config.FULLSCREEN = False # Override config setting

    # --- Pre-run Checks ---
    # Wait for internet connection before initializing services, unless using mock data.
    if not config.USE_MOCK_DATA:
        if not wait_for_internet(max_wait_seconds=120, check_interval=10): # Increased wait time
            logger.critical("Exiting: No internet connection available and not using mock data.")
            sys.exit(1) # Exit if no connection after waiting
    else:
        logger.info("Skipping internet connection check because mock data mode is enabled.")

    # --- Application Initialization and Start ---
    app: Optional[WeatherDisplayApp] = None # Initialize app variable
    try:
        # Log key configuration settings being used
        logger.info(f"Mode: {'Headless' if args.headless else 'GUI'}")
        logger.info(f"Mock Data: {config.USE_MOCK_DATA}")
        logger.info(f"Fullscreen (effective): {config.FULLSCREEN and not args.windowed and not args.headless}")
        logger.info(f"IMS Station: '{config.IMS_STATION_NAME}'")
        # AccuWeather details logged during its client initialization

        # Create the main application instance
        app = WeatherDisplayApp(
            headless=args.headless,
            api_key=args.api_key # Pass API key from args (can be None)
        )

        # Start the application (enters main loop)
        app.start()

    except RuntimeError as e:
         # Catch specific initialization errors (e.g., no display in GUI mode)
         logger.critical(f"Application initialization failed: {e}")
         sys.exit(1) # Exit with error code
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully (especially relevant for headless mode,
        # but good practice overall). The signal handler in headless mode
        # also calls stop(), but this catches it if it happens elsewhere.
        logger.info("Keyboard interrupt (Ctrl+C) received. Stopping application...")
        if app:
            app.stop()
        sys.exit(0) # Exit cleanly after stopping
    except Exception as e:
        # Catch any other unexpected exceptions during setup or runtime
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
        if app:
            logger.info("Attempting graceful shutdown after error...")
            app.stop() # Try to clean up resources
        sys.exit(1) # Exit with error code
    finally:
        # This block ensures cleanup happens even if the main loop exits unexpectedly
        # or an error occurs after `app` is initialized but before `stop` is called.
        if app and app.running:
            logger.warning("Main execution block finished unexpectedly while app was still marked as running. Ensuring stop().")
            app.stop()
        logger.info("Application shutdown sequence complete.")


# Standard Python entry point check:
# Ensures that the `main()` function is called only when the script is executed directly
# (not when it's imported as a module).
if __name__ == "__main__":
    main()
