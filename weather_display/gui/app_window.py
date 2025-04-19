"""
Main Application Window (GUI) for the Weather Display using CustomTkinter.

This module defines the `AppWindow` class, which inherits from `customtkinter.CTk`
and constitutes the main graphical user interface of the Weather Display application.
It is responsible for:
- Setting up the main window's appearance (title, size, fullscreen).
- Defining the layout structure using grid geometry management.
- Creating and arranging all visual widgets (labels, frames) to display:
    - Current time and date.
    - Current weather conditions (temperature, humidity, air quality).
    - Multi-day weather forecast (day name, icon, condition, temperature range).
    - Status indicators for internet connection and API health.
- Providing public methods (`update_time`, `update_date`, etc.) that are called
  by the main application controller (`WeatherDisplayApp`) to refresh the
  displayed data.
- Handling basic user interactions like exiting fullscreen mode via the Escape key.
"""

import logging
from typing import Dict, List, Any, Optional
import os

import customtkinter as ctk
from PIL import Image

# Local application imports
from .. import config # Access configuration settings (fonts, colors, etc.)
from ..utils.localization import (
    get_translation, # For translating static UI text
    translate_weather_condition, # For translating dynamic weather conditions
    translate_aqi_category # For translating AQI categories
)
from ..utils.icon_handler import WeatherIconHandler # For loading weather icons
from ..utils.helpers import get_day_name # For getting localized day names from dates

# Attempt to import ImageTk for type hinting, handle if Pillow isn't fully installed
try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None # Define as None if import fails

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

# --- Global UI Setup (Theme and Appearance) ---
# Set the global appearance mode (dark/light) and color theme for CustomTkinter.
# This should be done once, ideally before the AppWindow is instantiated.
ctk.set_appearance_mode("dark" if config.DARK_MODE else "light")
ctk.set_default_color_theme("blue") # Example theme, could be configurable


class AppWindow(ctk.CTk):
    """
    Represents the main graphical window of the Weather Display application.

    This class manages the entire UI, including layout definition, widget creation,
    and dynamic updates based on data received from external services via the
    main application controller. It uses the CustomTkinter library for modern
    Tkinter widgets.

    Attributes:
        icon_handler (WeatherIconHandler): Handles loading and caching of weather icons.
        connection_frame (ctk.CTkFrame): Top-most frame holding status indicators.
        top_frame (ctk.CTkFrame): Main upper frame containing time, date, and current weather.
        bottom_frame (ctk.CTkFrame): Main lower frame containing the weather forecast.
        connection_indicator (ctk.CTkLabel): Label indicating internet connection status.
        api_limit_indicator (ctk.CTkLabel): Label indicating AccuWeather API limit reached.
        api_error_indicator (ctk.CTkLabel): Label indicating a general API error.
        time_label (ctk.CTkLabel): Displays the current time (HH:MM).
        weekday_label (ctk.CTkLabel): Displays the current day of the week.
        day_label (ctk.CTkLabel): Displays the current day of the month (numeric).
        month_year_label (ctk.CTkLabel): Displays the current month and year.
        current_weather_frame (ctk.CTkFrame): Container for current weather details.
        temp_frame (ctk.CTkFrame): Sub-frame for temperature display.
        temp_title (ctk.CTkLabel): Title label ("Temperature").
        temp_value (ctk.CTkLabel): Displays the current temperature value.
        humidity_frame (ctk.CTkFrame): Sub-frame for humidity display.
        humidity_title (ctk.CTkLabel): Title label ("Humidity").
        humidity_value (ctk.CTkLabel): Displays the current humidity value.
        air_quality_frame (ctk.CTkFrame): Sub-frame for Air Quality Index (AQI) display.
        air_quality_title (ctk.CTkLabel): Title label ("Air Quality").
        air_quality_value (ctk.CTkLabel): Displays the current AQI category/value.
        forecast_frames (List[Dict[str, ctk.CTkLabel]]): A list of dictionaries,
            each holding the widgets (frame, day, icon, condition, temp labels)
            for one day of the forecast.
    """

    def __init__(self):
        """
        Initializes the AppWindow instance.

        Sets up the window title, geometry, icon handler, configures fullscreen,
        defines the layout structure, creates all necessary widgets, and sets up
        keyboard bindings.
        """
        super().__init__() # Call the parent class (ctk.CTk) initializer

        logger.info("Initializing AppWindow...")
        self.title(get_translation('app_title', config.LANGUAGE))
        # Set initial geometry; fullscreen might override this later
        self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")

        # Instantiate the icon handler for loading forecast icons efficiently
        self.icon_handler = WeatherIconHandler()
        logger.debug("WeatherIconHandler initialized.")

        # Configure fullscreen based on settings in config.py
        self._configure_fullscreen()

        # Define the main layout grid and create container frames
        self._setup_layout()

        # Create all individual widgets within the frames
        self._create_widgets()

        # Set up any necessary event bindings (e.g., keyboard shortcuts)
        self._setup_bindings()

        logger.info("AppWindow initialized successfully.")

    def _configure_fullscreen(self):
        """
        Configures the window for fullscreen mode based on `config.FULLSCREEN`.

        Attempts various platform-specific methods to achieve fullscreen or maximized
        state if `config.FULLSCREEN` is True. Includes fallbacks if primary methods fail.
        Logs the outcome or any errors encountered.
        """
        if config.FULLSCREEN:
            logger.info("Attempting to enable fullscreen mode...")
            try:
                # Primary method using Tkinter attributes
                self.attributes("-fullscreen", True)
                # Some platforms might need additional steps or checks
                # Example fallback: Remove window decorations (more aggressive)
                # if not self.winfo_viewable(): # Check if window is actually visible
                #     self.overrideredirect(True)
                #     self.state('normal') # Ensure state is normal before setting geometry
                #     self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

                # Another fallback: Use 'zoomed' state (platform-dependent)
                # if not self.winfo_viewable():
                #     state = 'zoomed' if os.name == 'nt' else 'normal' # 'zoomed' on Windows
                #     self.state(state)
                #     self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

                logger.info("Fullscreen mode enabled (or attempted).")
            except Exception as e:
                logger.error(f"Error setting fullscreen mode: {e}. Attempting fallback.")
                # Fallback to maximized window state if fullscreen fails
                try:
                    state = 'zoomed' if os.name == 'nt' else 'normal'
                    self.state(state)
                    # Explicitly set geometry to screen size as state might not be enough
                    self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
                    logger.info("Fallback to maximized state successful.")
                except Exception as fallback_e:
                     logger.error(f"Error setting fallback maximized state: {fallback_e}")
                     # Last resort: use configured size if maximization also fails
                     self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
                     logger.warning("Using configured window size as last resort.")
        else:
            logger.info("Fullscreen mode is disabled in configuration.")


    def _setup_layout(self):
        """
        Configures the main grid layout of the window and creates primary frames.

        Divides the window into rows for the status bar, top section (time/date/current),
        and bottom section (forecast). Configures row/column weights to control resizing
        behavior. Creates and places the main container frames (`connection_frame`,
        `top_frame`, `bottom_frame`) within this grid.
        """
        logger.debug("Setting up main window layout...")
        # --- Configure Root Window Grid ---
        # Single main column that expands to fill window width
        self.grid_columnconfigure(0, weight=1)
        # Row 0: Connection status bar - fixed height, no vertical expansion
        self.grid_rowconfigure(0, weight=0)
        # Row 1: Top Frame (Time/Date/Current) - takes 1/3 of remaining space
        self.grid_rowconfigure(1, weight=1) # 1/3 of remaining space
        # Row 2: Bottom Frame (Forecast) - takes 2/3 of remaining space
        self.grid_rowconfigure(2, weight=2) # 2/3 of remaining space

        # --- Create Main Container Frames ---
        # Connection Status Bar (at the very top)
        self.connection_frame = ctk.CTkFrame(
            self,
            corner_radius=0, # No rounded corners for a bar
            height=config.CONNECTION_FRAME_HEIGHT # Fixed height from config
        )
        self.connection_frame.grid(row=0, column=0, sticky="ew") # Span horizontally
        # Configure columns within the status bar:
        # Column 0 expands, pushing indicators to the right.
        self.connection_frame.grid_columnconfigure(0, weight=1)
        # Columns for indicators have fixed width (weight 0).
        self.connection_frame.grid_columnconfigure(1, weight=0) # Connection
        self.connection_frame.grid_columnconfigure(2, weight=0) # API Limit
        self.connection_frame.grid_columnconfigure(3, weight=0) # API Error
        # Prevent the frame from shrinking to fit its content if content is small
        self.connection_frame.grid_propagate(False)
        logger.debug("Connection frame created.")

        # Top Section Frame (holds Time, Date, Current Weather)
        self.top_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.top_frame.grid(row=1, column=0, sticky="nsew") # Fill available space
        # Configure grid within top_frame:
        # Column 0 (Time) takes more horizontal space than Column 1 (Date).
        self.top_frame.grid_columnconfigure(0, weight=2)
        self.top_frame.grid_columnconfigure(1, weight=1)
        # Row 0 (Time/Date) expands vertically.
        self.top_frame.grid_rowconfigure(0, weight=1)
        # Row 1 (Current Weather) expands vertically more.
        self.top_frame.grid_rowconfigure(1, weight=2)
        logger.debug("Top frame created.")

        # Bottom Section Frame (holds Forecast)
        self.bottom_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.bottom_frame.grid(
            row=2, column=0, sticky="nsew",
            padx=config.SECTION_PADDING_X, pady=config.SECTION_PADDING_Y # Padding around forecast
        )
        # Configure 3 equal columns for the 3 forecast days.
        self.bottom_frame.grid_columnconfigure((0, 1, 2), weight=1)
        # Single row containing the forecast day frames expands vertically.
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        logger.debug("Bottom frame created.")
        logger.debug("Main layout setup complete.")

    def _create_widgets(self):
        """
        Creates and places all individual UI widgets.

        Calls helper methods to create widgets for each section of the UI:
        status bar, time display, date display, current weather, and forecast.
        """
        logger.debug("Creating UI widgets...")
        self._create_status_bar()
        self._create_time_display()
        self._create_date_display()
        self._create_current_weather_display()
        self._create_forecast_display()
        logger.debug("UI widget creation complete.")

    def _create_status_bar(self):
        """Creates the labels used as status indicators in the top connection bar."""
        logger.debug("Creating status bar indicators...")
        # --- Connection Indicator ---
        self.connection_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('no_internet', config.LANGUAGE), # Text shown when visible
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.STATUS_INDICATOR_FONT_SIZE),
            fg_color=config.NO_CONNECTION_COLOR, # Background color from config
            text_color=config.STATUS_TEXT_COLOR, # Text color from config
            corner_radius=config.STATUS_INDICATOR_CORNER_RADIUS # Rounded corners
        )
        # Place in grid column 1 (right side, before API indicators)
        self.connection_indicator.grid(
            row=0, column=1, sticky="e", # Align to the right edge of its cell
            padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y
        )
        self.connection_indicator.grid_remove() # Hide initially until needed
        logger.debug("Connection indicator created.")

        # --- API Limit Indicator ---
        self.api_limit_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('api_limit', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.STATUS_INDICATOR_FONT_SIZE),
            fg_color=config.API_LIMIT_COLOR,
            text_color=config.STATUS_TEXT_COLOR,
            corner_radius=config.STATUS_INDICATOR_CORNER_RADIUS
        )
        # Place in grid column 2
        self.api_limit_indicator.grid(
            row=0, column=2, sticky="e",
            padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y
        )
        self.api_limit_indicator.grid_remove() # Hide initially
        logger.debug("API limit indicator created.")

        # --- API Error Indicator ---
        self.api_error_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('api_error', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.STATUS_INDICATOR_FONT_SIZE),
            fg_color=config.API_ERROR_COLOR,
            text_color=config.STATUS_TEXT_COLOR,
            corner_radius=config.STATUS_INDICATOR_CORNER_RADIUS
        )
        # Place in grid column 3 (right-most)
        self.api_error_indicator.grid(
            row=0, column=3, sticky="e",
            padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y
        )
        self.api_error_indicator.grid_remove() # Hide initially
        logger.debug("API error indicator created.")

    def _create_time_display(self):
        """Creates the large label for displaying the current time (HH:MM)."""
        logger.debug("Creating time display label...")
        self.time_label = ctk.CTkLabel(
            self.top_frame,
            text="00:00", # Initial placeholder text
            font=ctk.CTkFont(
                family=config.FONT_FAMILY,
                # Combine base size and increase from config for large font
                size=config.TIME_FONT_SIZE_BASE + config.TIME_FONT_SIZE_INCREASE,
                weight="bold" # Make time bold
            ),
            anchor="center",
            justify="center"
        )
        # Place in the top-left grid cell of the top_frame, allowing it to expand
        self.time_label.grid(
            row=0, column=0, sticky="nsew", # Fill the cell
            # Add padding based on config
            padx=(config.SECTION_PADDING_X, config.ELEMENT_PADDING_X),
            pady=config.SECTION_PADDING_Y
        )
        logger.debug("Time display label created.")

    def _create_date_display(self):
        """
        Creates the vertically stacked labels for displaying the date.

        Uses an outer frame for positioning within the main grid and an inner
        frame with `pack` geometry manager for simple vertical stacking of the
        weekday, day number, and month/year labels.
        """
        logger.debug("Creating date display labels...")
        # Outer frame to position the date block in the top_frame grid (top-right)
        self.date_display_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.date_display_frame.grid(
            row=0, column=1, sticky="ns", # Stick to top/bottom, center horizontally
            padx=(config.ELEMENT_PADDING_X, config.SECTION_PADDING_X),
            pady=config.SECTION_PADDING_Y
        )
        # Configure the outer frame's grid to center its content (the inner frame)
        self.date_display_frame.grid_columnconfigure(0, weight=1)
        self.date_display_frame.grid_rowconfigure(0, weight=1)

        # Inner frame to hold the actual labels, allowing easy stacking with pack
        inner_date_labels_frame = ctk.CTkFrame(self.date_display_frame, fg_color="transparent")
        # Place the inner frame in the center of the outer frame's single cell
        inner_date_labels_frame.grid(row=0, column=0, sticky="") # Empty sticky means center

        # --- Create and pack labels inside the inner frame ---
        # Weekday Label (Top)
        self.weekday_label = ctk.CTkLabel(
            inner_date_labels_frame, text="Weekday", # Placeholder
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.DATE_FONT_SIZE_BASE)
        )
        self.weekday_label.pack(pady=(0, config.TEXT_PADDING_Y)) # Padding below

        # Day Label (Middle, Large)
        self.day_label = ctk.CTkLabel(
            inner_date_labels_frame, text="00", # Placeholder
            font=ctk.CTkFont(
                family=config.FONT_FAMILY,
                size=config.DATE_FONT_SIZE_BASE + config.DATE_DAY_FONT_SIZE_INCREASE,
                weight="bold"
            )
        )
        self.day_label.pack(pady=0) # No extra padding

        # Month Year Label (Bottom)
        self.month_year_label = ctk.CTkLabel(
            inner_date_labels_frame, text="Month 0000", # Placeholder
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.DATE_FONT_SIZE_BASE)
        )
        self.month_year_label.pack(pady=(config.TEXT_PADDING_Y, 0)) # Padding above
        logger.debug("Date display labels created.")

    def _create_current_weather_display(self):
        """
        Creates the frames and labels for the current weather section.

        Includes sub-sections for Temperature, Humidity, and Air Quality, each
        within its own frame for visual separation and layout control.
        """
        logger.debug("Creating current weather display section...")
        # Main container frame for the current weather section
        self.current_weather_frame = ctk.CTkFrame(self.top_frame)
        self.current_weather_frame.grid(
            row=1, column=0, columnspan=2, # Span across both columns of top_frame
            sticky="nsew",
            padx=config.SECTION_PADDING_X, pady=config.SECTION_PADDING_Y
        )
        # Configure 3 equal columns within this frame for Temp, Humidity, AQI
        self.current_weather_frame.grid_columnconfigure((0, 1, 2), weight=1)
        # Single row for the content frames
        self.current_weather_frame.grid_rowconfigure(0, weight=1) # Changed from 1 to 0 as title row removed
        # Remove row 0 config as title row is gone
        # self.current_weather_frame.grid_rowconfigure(0, weight=0)
        # self.current_weather_frame.grid_rowconfigure(1, weight=1)

        # --- Temperature Sub-section ---
        logger.debug("Creating temperature display...")
        self.temp_frame = ctk.CTkFrame(self.current_weather_frame)
        self.temp_frame.grid(row=0, column=0, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)
        self.temp_frame.grid_rowconfigure(0, weight=0) # Title row
        self.temp_frame.grid_rowconfigure(1, weight=1) # Value row (expands)
        self.temp_frame.grid_columnconfigure(0, weight=1) # Single column expands
        self.temp_title = ctk.CTkLabel(
            self.temp_frame, text=get_translation('temperature', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.temp_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)
        self.temp_value = ctk.CTkLabel(
            self.temp_frame, text="--°C", # Placeholder
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE + 40, weight="bold") # Larger font for value
        )
        # Place value towards the top of its cell
        self.temp_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        # --- Humidity Sub-section ---
        logger.debug("Creating humidity display...")
        self.humidity_frame = ctk.CTkFrame(self.current_weather_frame)
        self.humidity_frame.grid(row=0, column=1, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)
        self.humidity_frame.grid_rowconfigure(0, weight=0) # Title
        self.humidity_frame.grid_rowconfigure(1, weight=1) # Value
        self.humidity_frame.grid_columnconfigure(0, weight=1) # Column
        self.humidity_title = ctk.CTkLabel(
            self.humidity_frame, text=get_translation('humidity', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.humidity_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)
        self.humidity_value = ctk.CTkLabel(
            self.humidity_frame, text="--%", # Placeholder
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE + 40, weight="bold")
        )
        self.humidity_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        # --- Air Quality Sub-section ---
        logger.debug("Creating air quality display...")
        self.air_quality_frame = ctk.CTkFrame(self.current_weather_frame)
        self.air_quality_frame.grid(row=0, column=2, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)
        self.air_quality_frame.grid_rowconfigure(0, weight=0) # Title
        self.air_quality_frame.grid_rowconfigure(1, weight=1) # Value
        self.air_quality_frame.grid_columnconfigure(0, weight=1) # Column
        self.air_quality_title = ctk.CTkLabel(
            self.air_quality_frame, text=get_translation('air_quality', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.air_quality_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)
        self.air_quality_value = ctk.CTkLabel(
            self.air_quality_frame, text="--", # Placeholder
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE + 10, weight="bold") # Reduced size
        )
        self.air_quality_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)
        logger.debug("Current weather display section created.")

    def _create_forecast_display(self):
        """
        Creates the frames and labels for the multi-day forecast section.

        Generates a specified number of forecast day frames (typically 3), each
        containing labels for the day name, weather icon, condition description,
        and temperature range. Stores references to these widgets in the
        `self.forecast_frames` list for later updates.
        """
        logger.debug("Creating forecast display section...")
        self.forecast_frames: List[Dict[str, ctk.CTkLabel]] = [] # Initialize list to store widget references
        na_text = get_translation('not_available', config.LANGUAGE) # Cache N/A text

        num_forecast_days = 3 # Define how many days to display

        for i in range(num_forecast_days):
            logger.debug(f"Creating forecast frame for day {i+1}...")
            # Create a frame for each forecast day
            frame = ctk.CTkFrame(self.bottom_frame)
            frame.grid(
                row=0, column=i, sticky="nsew", # Place in the bottom_frame grid
                padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y
            )
            # Configure grid layout within each forecast frame
            frame.grid_columnconfigure(0, weight=1) # Single column expands
            frame.grid_rowconfigure(0, weight=0) # Day name (fixed height)
            frame.grid_rowconfigure(1, weight=1) # Icon (takes vertical space)
            frame.grid_rowconfigure(2, weight=0) # Condition text (fixed height)
            frame.grid_rowconfigure(3, weight=0) # Temp range (fixed height)

            # --- Create widgets for this forecast day ---
            # Day Name Label
            day_label = ctk.CTkLabel(
                frame, text=f"Day {i+1}", # Placeholder text
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE, weight="bold")
            )
            day_label.grid(row=0, column=0, pady=(config.TEXT_PADDING_Y * 2, config.TEXT_PADDING_Y))

            # Icon Label (will hold the weather icon image)
            icon_label = ctk.CTkLabel(frame, text="", image=None) # No text, image set later
            icon_label.grid(row=1, column=0, pady=config.ELEMENT_PADDING_Y)

            # Condition Description Label
            condition_label = ctk.CTkLabel(
                frame, text=na_text, # Placeholder
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE)
                # Removed wraplength to prevent text wrapping
            )
            condition_label.grid(row=2, column=0, pady=config.TEXT_PADDING_Y)

            # Temperature Range Label
            temp_label = ctk.CTkLabel(
                frame, text="--° / --°", # Placeholder
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE)
            )
            temp_label.grid(row=3, column=0, pady=(config.TEXT_PADDING_Y, config.TEXT_PADDING_Y * 2))

            # Store references to the widgets for easy updating later
            self.forecast_frames.append({
                'frame': frame,
                'day': day_label,
                'icon': icon_label,
                'condition': condition_label,
                'temp': temp_label
            })
            logger.debug(f"Forecast frame {i+1} created.")
        logger.debug("Forecast display section created.")

    def _setup_bindings(self):
        """Sets up keyboard bindings for the application window."""
        logger.debug("Setting up keyboard bindings...")
        # Bind the Escape key to the exit_fullscreen method
        self.bind("<Escape>", self.exit_fullscreen)
        logger.debug("'<Escape>' key bound to exit_fullscreen.")

    # --- Public Update Methods ---
    # These methods are called from the main WeatherDisplayApp controller
    # to update the UI elements with new data.

    def update_time(self, time_str: str):
        """
        Updates the time display label with the provided time string.

        Formats the input time string (expected HH:MM:SS) to display only HH:MM.
        Handles potential errors during formatting.

        Args:
            time_str (str): The current time string, typically including seconds.
        """
        logger.debug(f"Updating time display with: {time_str}")
        try:
            # Extract HH:MM from HH:MM:SS
            time_parts = time_str.split(':')
            if len(time_parts) >= 2:
                formatted_time = f"{time_parts[0]}:{time_parts[1]}"
                self.time_label.configure(text=formatted_time)
            else:
                # Log a warning if format is unexpected, but display raw string
                logger.warning(f"Received unexpected time format: '{time_str}'. Displaying raw.")
                self.time_label.configure(text=time_str)
        except Exception as e:
             logger.error(f"Error updating time display: {e}")
             self.time_label.configure(text="Error") # Indicate error on the UI

    def update_date(self, date_str: str):
        """
        Updates the multi-part date display labels (weekday, day, month/year).

        Parses the input date string, which is expected to be fully formatted and
        localized (e.g., "Sunday, 21 April 2024"). Extracts the components and
        updates the corresponding labels. Includes fallback if parsing fails.

        Args:
            date_str (str): The full, localized date string.
        """
        logger.debug(f"Updating date display with: {date_str}")
        try:
            # Attempt to parse based on the common format "Weekday, DD Month YYYY"
            parts = date_str.split(', ') # Split weekday from the rest
            if len(parts) == 2:
                weekday = parts[0]
                date_parts = parts[1].split(' ') # Split day, month, year
                if len(date_parts) == 3:
                    day = date_parts[0].lstrip('0') # Remove leading zero from day (e.g., '05' -> '5')
                    month = date_parts[1]
                    year = date_parts[2]

                    # Update the individual date labels
                    self.weekday_label.configure(text=weekday)
                    self.day_label.configure(text=day)
                    self.month_year_label.configure(text=f"{month} {year}")
                    return # Exit function on successful update

            # If parsing failed (string didn't match expected format)
            logger.warning(f"Could not parse date string: '{date_str}'. Displaying raw string as fallback.")
            # Display the raw string in the top label as a fallback
            self.weekday_label.configure(text=date_str)
            # Clear the other labels
            self.day_label.configure(text="")
            self.month_year_label.configure(text="")

        except Exception as e:
            logger.error(f"Error updating date display for '{date_str}': {e}")
            # Display fallback text like "N/A" or "Error" on exception
            na_text = get_translation('not_available', config.LANGUAGE)
            self.weekday_label.configure(text=na_text)
            self.day_label.configure(text="")
            self.month_year_label.configure(text="")

    def update_current_weather(self, weather_result: Dict[str, Any]):
        """
        Updates the current weather display section (Temperature, Humidity, AQI).

        Receives a dictionary containing the latest weather data and status info.
        Updates the status indicators first, then extracts temperature, humidity,
        and air quality data to update the respective labels. Handles missing data
        by displaying a "not available" text.

        Args:
            weather_result (Dict[str, Any]): A dictionary typically returned by a
                weather service client's `get_current_weather` method. Expected keys:
                'data' (dict): Contains 'temperature', 'humidity', 'air_quality_category', etc.
                'connection_status' (bool): Internet connection status during fetch.
                'api_status' (str): Status of the API call ('ok', 'error', 'limit_reached', 'mock').
        """
        logger.debug(f"Updating current weather display. API Status: {weather_result.get('api_status')}")
        # Update status indicators based on the result payload
        connection_status = weather_result.get('connection_status', False)
        api_status = weather_result.get('api_status', 'error')
        self.update_status_indicators(connection_status, api_status)

        # Extract the actual weather data dictionary; default to empty if missing
        current_data = weather_result.get('data', {})
        # Get localized "Not Available" text for fallback
        na_text = get_translation('not_available', config.LANGUAGE)

        # --- Update Temperature ---
        temp = current_data.get('temperature')
        temp_text = f"{int(round(temp))}°C" if temp is not None else na_text
        self.temp_value.configure(text=temp_text)
        logger.debug(f"Temperature updated to: {temp_text}")

        # --- Update Humidity ---
        humidity = current_data.get('humidity')
        humidity_text = f"{humidity}%" if humidity is not None else na_text
        self.humidity_value.configure(text=humidity_text)
        logger.debug(f"Humidity updated to: {humidity_text}")

        # --- Update Air Quality ---
        aqi_category = current_data.get('air_quality_category')
        aqi_value = current_data.get('air_quality_index') # Numeric value (optional)
        aqi_text = na_text # Default to N/A

        if aqi_category is not None:
            # Translate the category (e.g., "Good", "Moderate") using the localization utility
            translated_aqi = translate_aqi_category(aqi_category, config.LANGUAGE)
            # Format the display text (e.g., just category, or category + value)
            # Example: Show only translated category for simplicity
            aqi_text = translated_aqi
            # Example: Include value if available:
            # aqi_text = f"{translated_aqi} ({aqi_value})" if aqi_value is not None else translated_aqi
        else:
            # If category is None, display N/A
             aqi_text = na_text

        self.air_quality_value.configure(text=aqi_text)
        logger.debug(f"Air Quality updated to: {aqi_text}")

        # Note: Current weather icon display was previously removed. If needed,
        # logic similar to forecast icon handling would be added here.

    def update_forecast(self, forecast_result: Dict[str, Any]):
        """
        Updates the multi-day forecast display section.

        Iterates through the forecast data provided and updates the widgets
        (day name, icon, condition, temperature) for each corresponding forecast
        day frame stored in `self.forecast_frames`. Handles cases where fewer
        days of data are available than frames exist.

        Args:
            forecast_result (Dict[str, Any]): A dictionary typically returned by a
                weather service client's `get_forecast` method. Expected keys:
                'data' (List[Dict]): A list of dictionaries, each representing one
                                     forecast day with keys like 'date', 'max_temp',
                                     'min_temp', 'condition', 'icon_code'.
                'connection_status' (bool): Connection status during fetch.
                'api_status' (str): Status of the API call ('ok', 'error', etc.).
        """
        logger.debug(f"Updating forecast display. API Status: {forecast_result.get('api_status')}")
        # Update status indicators based on forecast fetch status (optional, might rely on current weather status)
        # connection_status = forecast_result.get('connection_status', False)
        # api_status = forecast_result.get('api_status', 'error')
        # self.update_status_indicators(connection_status, api_status) # Decide if forecast status should override

        # Extract the list of forecast day data; default to empty list if missing
        forecast_data: List[Dict[str, Any]] = forecast_result.get('data', [])
        na_text = get_translation('not_available', config.LANGUAGE)

        # Iterate through the forecast frames and update them with data
        for i, day_frame_widgets in enumerate(self.forecast_frames):
            if i < len(forecast_data):
                # Data available for this day
                day_data = forecast_data[i]
                logger.debug(f"Updating forecast day {i+1} with data: {day_data}")

                # Extract data points for the day
                date_str = day_data.get('date') # ISO format date string (e.g., "2024-04-21T07:00:00+03:00")
                max_temp = day_data.get('max_temp')
                min_temp = day_data.get('min_temp')
                condition = day_data.get('condition') # Text description (e.g., "Mostly sunny")
                icon_code = day_data.get('icon_code') # Numeric code for the icon

                # --- Update Day Name Label ---
                # Use helper function to get localized day name from date string
                day_name = get_day_name(date_str) if date_str else na_text
                day_frame_widgets['day'].configure(text=day_name)

                # --- Update Icon Label ---
                # Load the icon using the handler (returns a CTkImage or None)
                icon_image = self.icon_handler.load_icon(icon_code, config.FORECAST_ICON_SIZE)
                if icon_image:
                    # Configure the label to show the image and no text
                    day_frame_widgets['icon'].configure(image=icon_image, text="")
                else:
                    # If icon loading fails, show N/A text and no image
                    day_frame_widgets['icon'].configure(image=None, text=na_text)
                    logger.warning(f"Failed to load forecast icon for code: {icon_code}")

                # --- Update Condition Text Label ---
                # Translate the weather condition text if available
                translated_condition = translate_weather_condition(condition, config.LANGUAGE) if condition else na_text
                day_frame_widgets['condition'].configure(text=translated_condition)

                # --- Update Temperature Range Label ---
                temp_text = na_text # Default to N/A
                # Format temperature string carefully, handling None values
                if max_temp is not None and min_temp is not None:
                    temp_text = f"{int(round(max_temp))}° / {int(round(min_temp))}°"
                elif max_temp is not None: # Only max temp available
                    temp_text = f"{int(round(max_temp))}° / --°"
                elif min_temp is not None: # Only min temp available
                    temp_text = f"--° / {int(round(min_temp))}°"
                day_frame_widgets['temp'].configure(text=temp_text)

            else:
                # No data available for this forecast frame index
                logger.debug(f"No forecast data available for day {i+1}. Clearing frame.")
                # Clear the widgets in this frame or set to N/A
                day_frame_widgets['day'].configure(text=na_text)
                day_frame_widgets['icon'].configure(image=None, text="") # Clear icon
                day_frame_widgets['condition'].configure(text="") # Clear condition
                day_frame_widgets['temp'].configure(text="") # Clear temp

    def update_status_indicators(self, connection_status: bool, api_status: str):
        """
        Controls the visibility of the status indicators in the top bar.

        Shows or hides the 'No Internet', 'API Limit', and 'API Error' labels
        based on the provided connection and API status. Only one indicator
        (or none if status is OK) should be visible at a time.

        Args:
            connection_status (bool): True if internet connection is detected, False otherwise.
            api_status (str): The status string from the latest API interaction
                                ('ok', 'limit_reached', 'error', 'mock', etc.).
        """
        logger.debug(f"Updating status indicators: Connection={connection_status}, API Status='{api_status}'")

        # --- Handle Connection Status First ---
        if not connection_status:
            # If no internet, show only the connection error indicator
            logger.debug("Showing 'No Internet' indicator.")
            self.connection_indicator.grid() # Make visible
            self.connection_indicator.lift() # Ensure it's on top if overlapping
            # Hide API-related indicators as they are irrelevant without connection
            self.api_limit_indicator.grid_remove()
            self.api_error_indicator.grid_remove()
            return # Stop processing here if offline

        # --- Handle API Status (if Connected) ---
        # If connected, ensure the connection indicator is hidden
        logger.debug("Hiding 'No Internet' indicator (connection OK).")
        self.connection_indicator.grid_remove()

        # Now check the API status and show the relevant indicator (or none)
        if api_status == 'limit_reached':
            logger.debug("Showing 'API Limit' indicator.")
            self.api_limit_indicator.grid()
            self.api_limit_indicator.lift()
            self.api_error_indicator.grid_remove() # Hide error indicator
        elif api_status == 'error':
            logger.debug("Showing 'API Error' indicator.")
            self.api_error_indicator.grid()
            self.api_error_indicator.lift()
            self.api_limit_indicator.grid_remove() # Hide limit indicator
        else: # Covers 'ok', 'mock', or any other non-error/limit status
            logger.debug("API status is OK/Mock/Other. Hiding API indicators.")
            # Hide both API indicators if status is OK or mock
            self.api_limit_indicator.grid_remove()
            self.api_error_indicator.grid_remove()

    def exit_fullscreen(self, event=None):
        """
        Callback function to exit fullscreen mode.

        Typically bound to the Escape key press event. Attempts to revert the
        window from fullscreen/maximized state back to a normal windowed state.

        Args:
            event: The event object passed by Tkinter (optional, unused here).
        """
        try:
            logger.info("Attempting to exit fullscreen mode (Escape key pressed)...")
            # Revert fullscreen attributes/states
            self.attributes("-fullscreen", False)
            # Ensure window decorations (title bar, borders) are restored
            self.overrideredirect(False)
            # Set state back to normal
            self.state('normal')
            # Optionally restore configured size, or let the window manager decide
            # self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
            logger.info("Exited fullscreen mode successfully.")
        except Exception as e:
            logger.error(f"Error encountered while exiting fullscreen mode: {e}")
