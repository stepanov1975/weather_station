#!/usr/bin/env python3
"""
Main Entry Point for the Weather Display Application.

This script serves as the primary executable for launching the Weather Display.
It is responsible for:
    - Parsing command-line arguments (e.g., mock, windowed, and headless mode).
- Setting up logging for monitoring application activity.
- Initializing core services:
    - TimeService: For retrieving and formatting the current time and date.
    - IMSLastHourWeather: For fetching data from the Israel Meteorological Service.
- IMSCityForecast: For fetching city forecasts from the IMS city portal.
- Optionally initializing the graphical user interface (GUI) using AppWindow,
  unless running in headless mode.
- Managing background threads for periodic tasks:
- Fetching current observations and forecasts from IMS at configured intervals.
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
import logging.handlers
import threading
import argparse
import signal
from typing import Any, Callable, Optional

# Local application imports
# Assuming the script is run from the project root or the package is installed
try:
    from weather_display import config
    from weather_display.gui.app_window import AppWindow
    from weather_display.services.time_service import TimeService
    from weather_display.services.ims_lasthour import IMSLastHourWeather
    from weather_display.services.ims_forecast import IMSCityForecast
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
        from weather_display.services.ims_forecast import IMSCityForecast
        from weather_display.utils.helpers import check_internet_connection
    except ImportError:
        print("Failed to import necessary modules even after path adjustment.")
        print("Please ensure the script is run correctly relative to the package structure or install the package.")
        sys.exit(1)


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO
logger = logging.getLogger(__name__)


def configure_logging() -> bool:
    formatter = logging.Formatter(LOG_FORMAT)
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(LOG_LEVEL)
    root_logger.addHandler(stream_handler)

    try:
        config.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(config.LOG_FILE_PATH),
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
    except OSError as exc:
        root_logger.error(
            "Failed to initialize file logging to %s: %s",
            config.LOG_FILE_PATH,
            exc,
        )
        return False

    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)
    root_logger.addHandler(file_handler)
    return True


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
        ims_forecast (Optional[IMSCityForecast]): An instance for fetching IMS city
                                                  portal forecast data.
        app_window (Optional[AppWindow]): The main GUI window instance. None if headless.
        last_connection_status (bool): Stores the last known internet connection state
                                       to detect changes (e.g., reconnection).
        _update_threads (List[threading.Thread]): A list holding the background threads
                                                  responsible for periodic updates.
        _time_update_job_id (Optional[str]): Stores the ID returned by Tkinter's `after`
                                             method for the scheduled time update,
                                             allowing it to be cancelled on shutdown.
    """

    def __init__(self, headless: bool = False):
        """
        Initializes the Weather Display application.

        Sets up core services (Time, IMS observations, IMS city forecast) and
        optionally creates the GUI window based on the headless flag.

        Args:
            headless (bool): If True, prevents GUI initialization. Defaults to False.
        """
        self.headless: bool = headless
        self.running: bool = False # Controls thread loops, set True in start()
        self._update_threads: list[threading.Thread] = []
        self._time_update_job_id: Optional[str] = None # For cancelling Tkinter 'after' job
        self._stop_lock = threading.Lock()
        self._status_lock = threading.Lock()
        self._current_api_status: str | None = None
        self._forecast_api_status: str | None = None

        logger.info("Initializing application components...")

        # Initialize core services
        self.time_service = TimeService()
        logger.debug("TimeService initialized.")

        # Initialize IMS weather service using station name from config
        self.ims_weather: Optional[IMSLastHourWeather] = None
        try:
            self.ims_weather = IMSLastHourWeather(station_name=config.IMS_STATION_NAME)
            logger.info(f"IMSLastHourWeather initialized for station: {config.IMS_STATION_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize IMSLastHourWeather: {e}", exc_info=True)
            # Decide if this is critical; for now, we might proceed without IMS

        # Initialize IMS city forecast client
        self.ims_forecast: Optional[IMSCityForecast] = None
        try:
            self.ims_forecast = IMSCityForecast(location_id=config.IMS_CITY_LOCATION_ID)
            logger.info("IMSCityForecast initialized for city location id: %s", config.IMS_CITY_LOCATION_ID)
        except Exception as e:
            logger.error(f"Failed to initialize IMSCityForecast: {e}", exc_info=True)

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

        # Store the timestamp of the last successful IMS city forecast call
        self.last_forecast_success_time: Optional[float] = None
        logger.debug("Initialized last_forecast_success_time storage.")

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
            if self.ims_forecast:
                self._initial_forecast_update() # Use cache-aware initial IMS forecast fetch

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
            if self.ims_weather:
                self._update_weather()
            if self.ims_forecast:
                self._initial_forecast_update()
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
        stop_lock = getattr(self, "_stop_lock", None)
        if stop_lock is None:
            self._stop_without_lock()
            return
        with stop_lock:
            self._stop_without_lock()

    def _stop_without_lock(self) -> None:
        """Performs shutdown cleanup. Caller is responsible for locking."""
        had_work = self.running or self._time_update_job_id or self._update_threads or self.app_window
        if not had_work:
            logger.info("Application stop() called but it was already stopped.")
            return

        logger.info("Stopping application gracefully...")
        self.running = False

        time.sleep(0.5)
        self._cancel_time_update()
        self._join_update_threads()
        self._destroy_window()
        logger.info("Application stopped successfully.")

    def _cancel_time_update(self) -> None:
        if not self.app_window or not self._time_update_job_id:
            return
        try:
            logger.debug("Cancelling scheduled time update job (ID: %s).", self._time_update_job_id)
            self.app_window.after_cancel(self._time_update_job_id)
            self._time_update_job_id = None
        except Exception as exc:
            logger.error("Error cancelling Tkinter time update job: %s", exc)

    def _join_update_threads(self) -> None:
        threads_to_join = [thread for thread in self._update_threads if thread.is_alive()]
        if not threads_to_join:
            self._update_threads = []
            return

        logger.debug("Waiting for %s background thread(s) to join...", len(threads_to_join))
        for thread in threads_to_join:
            try:
                thread.join(timeout=2.0)
                if thread.is_alive():
                    logger.warning("Thread '%s' did not join within the timeout.", thread.name)
            except Exception as exc:
                logger.error("Error joining thread '%s': %s", thread.name, exc)
        self._update_threads = []

    def _destroy_window(self) -> None:
        if not self.app_window:
            return
        logger.info("Destroying GUI window...")
        try:
            if self.app_window.winfo_exists():
                self.app_window.destroy()
            self.app_window = None
        except Exception as exc:
            logger.error("Error destroying GUI window: %s", exc)

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
        self.stop()
        # Exit cleanly after stopping
        sys.exit(0)

    # --- Background Update Logic ---

    def _start_update_threads(self):
        """
        Creates and starts the background threads for periodic updates.

        Initializes threads for:
        - IMS weather data fetching (`_weather_update_loop`)
        - IMS city forecast fetching (`_forecast_update_loop`), if client exists.
        - Internet connection monitoring (`_connection_monitoring_loop`).

        Note: Time updates are handled by the main GUI thread using Tkinter's `after`
        mechanism, not a separate thread, to avoid cross-thread GUI update issues.
        """
        logger.info("Starting background update threads...")
        self._update_threads = [] # Ensure list is clear before starting

        # IMS Weather Update Thread (if IMS client initialized)
        if self.ims_weather:
            self._create_update_thread(self._weather_update_loop, "IMSWeatherUpdateThread")
        else:
            logger.warning("IMS client not initialized, skipping IMS update thread.")

        # IMS Forecast Update Thread (if forecast client initialized)
        if self.ims_forecast:
            self._create_update_thread(self._forecast_update_loop, "IMSForecastUpdateThread")
        else:
            logger.warning("IMS forecast client not initialized, skipping forecast update thread.")

        # Connection Monitoring Thread (always run)
        self._create_update_thread(self._connection_monitoring_loop, "ConnectionMonitorThread")

        # Start all created threads
        for thread in self._update_threads:
            logger.debug(f"Starting thread: {thread.name}")
            thread.start()

        logger.info(f"Started {len(self._update_threads)} background update threads.")

    def _create_update_thread(self, target: Callable[[], None], name: str) -> None:
        self._update_threads.append(threading.Thread(target=target, name=name, daemon=True))

    def _start_one_off_update(self, target: Callable[[], None], name: str) -> None:
        thread = threading.Thread(target=target, name=name, daemon=True)
        self._update_threads.append(thread)
        thread.start()

    def _sleep_until_stop(self, seconds: int) -> bool:
        for _ in range(seconds):
            if not self.running:
                return False
            time.sleep(1)
        return self.running

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

            if not self._sleep_until_stop(int(interval_seconds)):
                break

            # Perform the actual weather update
            logger.debug("IMS loop: Interval finished, calling _update_weather().")
            self._update_weather()

        logger.debug("IMS weather update loop finished.")

    def _forecast_update_loop(self):
        """
        Background thread loop for periodically fetching IMS city forecast data.

        Runs continuously while `self.running` is True. Waits for the configured
        IMS forecast update interval, then calls `_update_forecast_data()` to
        fetch and process current city analysis and forecast. Handles the
        `self.running` flag check during sleep for quick shutdown.
        """
        if not self.ims_forecast:
            logger.error("IMS forecast update loop started but client is not initialized. Loop exiting.")
            return

        logger.debug("IMS forecast update loop started.")
        # Initial update handled by start()
        while self.running:
            interval_seconds = config.IMS_FORECAST_UPDATE_INTERVAL_MINUTES * 60
            logger.debug(f"IMS forecast loop: Sleeping for {interval_seconds} seconds until next update.")

            if not self._sleep_until_stop(int(interval_seconds)):
                break

            # Perform the actual forecast data update
            logger.debug("IMS forecast loop: Interval finished, calling _update_forecast_data().")
            self._update_forecast_data()

        logger.debug("IMS forecast update loop finished.")


    def _connection_monitoring_loop(self):
        """
        Background thread loop to periodically check internet connectivity.

        Runs continuously while `self.running` is True. Checks the internet
        connection status at a fixed interval. If the connection state changes
        (especially from disconnected to connected), it triggers immediate,
        one-off updates for both IMS current weather and forecast data in
        separate threads.
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
                        self._start_one_off_update(self._update_weather, "IMSImmediateUpdate")
                    if self.ims_forecast:
                        self._start_one_off_update(self._update_forecast_data, "IMSForecastImmediateUpdate")

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
                     self._schedule_status_update()
                else:
                     logger.debug(f"Connection status remains: {'Connected' if current_status else 'Disconnected'}")


                logger.debug(f"Connection loop: Sleeping for {check_interval_seconds} seconds.")
                if not self._sleep_until_stop(check_interval_seconds):
                    break

            except Exception as e:
                logger.error(f"Error in connection monitoring loop: {e}", exc_info=True)
                # Avoid crashing the loop; wait before retrying
                self._sleep_until_stop(check_interval_seconds)

        logger.debug("Connection monitoring loop finished.")

    # --- Data Update Actions ---

    def _record_api_status(self, source: str, status: str | None) -> None:
        if source not in {"current", "forecast"}:
            raise ValueError(f"Unknown API status source: {source}")
        with self._status_lock:
            if source == "current":
                self._current_api_status = status
            else:
                self._forecast_api_status = status

    def _combined_api_status(self) -> str | None:
        priority = {None: 0, "ok": 1, "mock": 2, "offline": 3, "error": 4}
        with self._status_lock:
            statuses = (self._current_api_status, self._forecast_api_status)
        return max(statuses, key=lambda status: priority.get(status, 4))

    def _schedule_status_update(self) -> None:
        if not self.app_window:
            return
        connection_status = self.last_connection_status
        api_status = self._combined_api_status()
        success_time = self.last_forecast_success_time
        self.app_window.after(
            0,
            lambda: self.app_window.update_status_indicators(
                connection_status,
                api_status,
                success_time,
            ),
        )

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


    def _update_weather(self) -> None:
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
        current_weather_data: dict[str, Any] = {} # Initialize empty data dict

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
                update_payload_snapshot = update_payload.copy()
                self.app_window.after(
                    0,
                    lambda payload=update_payload_snapshot: self.app_window.update_current_weather(payload)
                )

            elif self.headless:
                 # Log fetched data details clearly in headless mode
                 logger.info("Headless Weather Update (IMS):")
                 logger.info(f"  Data: {current_weather_data}")
                 logger.info(f"  Connection Status during fetch: {connection_status}")
                 logger.info(f"  API Status: {api_status}")

            self._record_api_status("current", api_status)
            self._schedule_status_update()

            logger.info("IMS weather data update cycle finished.")

        except Exception as e:
            logger.error(f"Unexpected error during IMS weather update cycle: {e}", exc_info=True)
            self._record_api_status("current", "error")
            self._schedule_status_update()

    def _update_forecast_data(self, force_refresh: bool = True):
        """
        Fetches IMS city forecast data and updates the GUI.

        Current station observations still come from `_update_weather`; this
        method updates only the forecast region and forecast API status.
        """
        if not self.ims_forecast:
            logger.debug("Skipping IMS forecast update: client not initialized.")
            return

        logger.info("Attempting to update IMS city forecast data...")
        try:
            forecast_result = self.ims_forecast.get_forecast(force_refresh=force_refresh)
            forecast_api_status = forecast_result.get('api_status', 'error')
            final_conn_status = bool(forecast_result.get('connection_status'))

            if forecast_api_status == 'ok':
                final_api_status = 'ok'
                if not forecast_result.get('cache_hit'):
                    self.last_forecast_success_time = time.time()
            elif forecast_api_status == 'mock':
                final_api_status = 'mock'
            elif forecast_api_status == 'offline':
                final_api_status = 'offline'
            else:
                final_api_status = 'error'

            logger.info(
                "IMS forecast update status: API=%s, Connection=%s, Forecast days=%s",
                final_api_status,
                final_conn_status,
                len(forecast_result.get('data', []))
            )

            if self.app_window:
                forecast_result_snapshot = forecast_result.copy()
                self.app_window.after(
                    0,
                    lambda res=forecast_result_snapshot: self.app_window.update_forecast(res)
                )
            elif self.headless:
                logger.info("Headless IMS Forecast Update:")
                logger.info(f"  Forecast Data Count: {len(forecast_result.get('data', []))}")
                logger.info(f"  Overall Status: API={final_api_status}, Connection={final_conn_status}")

            self._record_api_status("forecast", final_api_status)
            self._schedule_status_update()

        except Exception as e:
            logger.error(f"Unexpected error during IMS forecast update cycle: {e}", exc_info=True)
            self._record_api_status("forecast", "error")
            self._schedule_status_update()

        logger.info("IMS forecast data update cycle finished.")

    def _initial_forecast_update(self):
        """Fetches initial IMS forecast data, prioritizing valid in-memory cache."""
        self._update_forecast_data(force_refresh=False)


# --- Command Line Argument Parsing ---

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments provided when running the script.

    Defines and processes arguments for:
    - `--mock`: Enables mock data mode, preventing live API calls.
    - `--windowed`: Forces the application to run in a window, overriding the
                    `FULLSCREEN` setting in `config.py`.
    - `--headless`: Runs the application without a GUI, logging data instead.

    Returns:
        argparse.Namespace: An object containing the parsed argument values.
                            Access values like `args.mock`, `args.windowed`, etc.
    """
    parser = argparse.ArgumentParser(
        description='Weather Display Application - Fetches and displays weather information.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Shows default values in help
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

def main() -> None:
    """
    Main execution function for the Weather Display application.

    Orchestrates the application lifecycle:
    1. Parses command-line arguments.
    2. Overrides configuration settings based on arguments (mock, windowed).
    3. Logs initial network status without blocking Raspberry Pi boot.
    4. Initializes the main `WeatherDisplayApp` instance.
    5. Starts the application using `app.start()`, which enters the main loop
       (GUI or headless wait).
    6. Includes error handling for initialization failures and unexpected errors
       during runtime, attempting graceful shutdown via `app.stop()`.
    7. Ensures `app.stop()` is called in a `finally` block for cleanup.
    """
    configure_logging()
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
    # Do not block Raspberry Pi boot on network availability. Services can use
    # cached data immediately and retry live IMS calls in the background.
    if not config.USE_MOCK_DATA:
        if check_internet_connection():
            logger.info("Initial internet connection check succeeded.")
        else:
            logger.warning("Initial internet connection check failed; starting with cache/offline state.")
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
        logger.info(f"IMS City Location ID: '{config.IMS_CITY_LOCATION_ID}'")

        # Create the main application instance
        app = WeatherDisplayApp(headless=args.headless)

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
