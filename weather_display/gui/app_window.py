"""
Main Application Window (GUI) for the Weather Display using CustomTkinter.

This module defines the `AppWindow` class, which inherits from `customtkinter.CTk`
and constitutes the main graphical user interface of the Weather Display application.
It implements a component-based architecture driven by configuration settings.

Responsibilities:
- Setting up the main window's appearance based on config (title, size, fullscreen).
- Defining the layout structure with configurable region heights using grid geometry.
- Creating and arranging visual widgets within distinct regions:
    - Status Bar (Optional)
    - Time and Date Region
    - Current Conditions Region (Temperature, Humidity, Air Quality - optional)
    - Forecast Region (Multi-day forecast)
- Applying fonts, colors, padding, margins, and corner radii from config.
- Providing public methods (`update_time`, `update_date`, etc.) for data refresh.
- Handling basic user interactions (e.g., exiting fullscreen).
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import os
from datetime import datetime # Added for timestamp formatting

import customtkinter as ctk
from PIL import Image

# Local application imports
# Use 'config' directly for accessing settings
from .. import config
from ..utils.localization import (
    get_translation,
    translate_weather_condition,
    translate_aqi_category
)
from ..utils.icon_handler import WeatherIconHandler
from ..utils.helpers import get_day_name

# Attempt to import ImageTk for type hinting
try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None

logger = logging.getLogger(__name__)

# --- Global UI Setup (Theme and Appearance) ---
# Set appearance mode based on config *before* AppWindow instantiation
ctk.set_appearance_mode("dark" if config.DARK_MODE else "light")
# Note: Default color theme ('blue', 'green', etc.) can be set globally,
# but we'll primarily rely on ACTIVE_COLORS for specific widget styling.
# ctk.set_default_color_theme(config.ctk_theme_name) # Optional: sets the base theme


class AppWindow(ctk.CTk):
    """
    Represents the main graphical window, managing UI layout and widgets based on config.

    Attributes:
        icon_handler (WeatherIconHandler): Handles loading weather icons.
        # --- Main Region Frames ---
        status_bar_frame (Optional[ctk.CTkFrame]): Top frame for status indicators.
        time_date_frame (ctk.CTkFrame): Frame for time and date display.
        current_conditions_frame (ctk.CTkFrame): Frame for current weather details.
        forecast_frame (ctk.CTkFrame): Frame for the multi-day forecast.
        # --- Status Bar Widgets (Optional) ---
        connection_indicator (Optional[ctk.CTkLabel]): Internet status label.
        network_status_label (Optional[ctk.CTkLabel]): Persistent network status label.
        api_status_label (Optional[ctk.CTkLabel]): Persistent API status label with last success time.
        # --- Time/Date Widgets ---
        time_label (ctk.CTkLabel): Displays current time.
        date_display_frame (ctk.CTkFrame): Container for date elements.
        weekday_label (ctk.CTkLabel): Displays current day of the week.
        day_label (ctk.CTkLabel): Displays current day of the month.
        month_year_label (ctk.CTkLabel): Displays current month and year.
        # --- Current Conditions Widgets ---
        temp_frame (Optional[ctk.CTkFrame]): Sub-frame for temperature.
        temp_title (Optional[ctk.CTkLabel]): "Temperature" label.
        temp_value (Optional[ctk.CTkLabel]): Current temperature value.
        humidity_frame (Optional[ctk.CTkFrame]): Sub-frame for humidity.
        humidity_title (Optional[ctk.CTkLabel]): "Humidity" label.
        humidity_value (Optional[ctk.CTkLabel]): Current humidity value.
        air_quality_frame (Optional[ctk.CTkFrame]): Sub-frame for AQI.
        air_quality_title (Optional[ctk.CTkLabel]): "Air Quality" label.
        air_quality_value (Optional[ctk.CTkLabel]): Current AQI value/category.
        # --- Forecast Widgets ---
        forecast_day_frames (List[Dict[str, ctk.CTkLabel]]): List holding widgets
            for each forecast day (frame, day, icon, condition, temp labels).
    """

    def __init__(self):
        """Initializes the AppWindow, setting up layout and widgets based on config."""
        super().__init__()
        logger.info("Initializing AppWindow...")

        self.title(get_translation('app_title', config.LANGUAGE))
        self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
        self.configure(fg_color=self._get_color("background")) # Set main window background

        self.icon_handler = WeatherIconHandler()
        logger.debug("WeatherIconHandler initialized.")

        self._configure_fullscreen()
        self._setup_layout()
        self._create_widgets()
        self._setup_bindings()

        logger.info("AppWindow initialized successfully.")

    # --- Helper Methods ---

    def _get_font(self, font_key: str) -> ctk.CTkFont:
        """
        Retrieves font settings from config and returns a CTkFont object.

        Args:
            font_key (str): The key corresponding to the desired font in config.FONTS.

        Returns:
            ctk.CTkFont: The configured font object.
        """
        font_config = config.FONTS.get(font_key)
        if not font_config:
            logger.warning(f"Font key '{font_key}' not found in config. Using default.")
            # Fallback to a default font if key is missing
            return ctk.CTkFont(family=config.DEFAULT_FONT_FAMILY, size=12, weight="normal")

        family, size, weight = font_config
        return ctk.CTkFont(
            family=family or config.DEFAULT_FONT_FAMILY, # Use default if None
            size=size,
            weight=weight
        )

    def _get_color(self, color_key: str, default: str = "#FF00FF") -> str:
        """
        Retrieves a color hex code from the active color theme in config.

        Args:
            color_key (str): The key for the desired color in config.ACTIVE_COLORS.
            default (str): A fallback color hex code if the key is not found.

        Returns:
            str: The hex color code.
        """
        color = config.ACTIVE_COLORS.get(color_key, default)
        if color == default:
             logger.warning(f"Color key '{color_key}' not found in config.ACTIVE_COLORS. Using default '{default}'.")
        return color

    # --- Initialization Steps ---

    def _configure_fullscreen(self):
        """Configures fullscreen mode based on `config.FULLSCREEN`."""
        if config.FULLSCREEN:
            logger.info("Binding fullscreen application to <Map> event...")
            # Bind to the <Map> event, which fires when the window becomes visible
            self.bind("<Map>", self._apply_fullscreen_event, add='+')
        else:
            logger.info("Fullscreen mode is disabled in configuration.")

    def _apply_fullscreen_event(self, event=None):
        """Event handler called when the window is mapped to apply fullscreen."""
        # Unbind after first trigger to prevent multiple calls if window is hidden/shown
        self.unbind("<Map>")
        logger.info("Window mapped, attempting to apply fullscreen mode now...")
        self._apply_fullscreen() # Call the original logic

    def _apply_fullscreen(self):
        """Applies the fullscreen attribute, called after a short delay."""
        logger.info("Attempting to apply fullscreen mode now...")
        try:
            self.attributes("-fullscreen", True)
            logger.info("Fullscreen mode applied successfully.")
        except Exception as e:
            logger.error(f"Error applying fullscreen mode: {e}. Attempting fallback.")
            try:
                # Fallback to maximized state
                state = 'zoomed' if os.name == 'nt' else 'normal'
                self.state(state)
                self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
                logger.info("Fallback to maximized state successful.")
            except Exception as fallback_e: # Corrected indentation
                logger.error(f"Error setting fallback maximized state: {fallback_e}")
                # Apply configured size as last resort if fallback fails
                self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
                logger.warning("Using configured window size as last resort.")

    def _setup_layout(self):
        """
        Configures the main window grid layout and creates the primary region frames.

        Uses `config.REGION_HEIGHT_WEIGHTS` to distribute vertical space among
        the status bar (if shown), time/date, current conditions, and forecast regions.
        """
        logger.debug("Setting up main window layout...")
        self.grid_columnconfigure(0, weight=1) # Single column expands horizontally

        # --- Configure Row Weights based on Config ---
        row_index = 0
        if config.OPTIONAL_ELEMENTS.get("show_status_bar", True):
            self.grid_rowconfigure(row_index, weight=config.REGION_HEIGHT_WEIGHTS.get("status", 0))
            row_index += 1
        self.grid_rowconfigure(row_index, weight=config.REGION_HEIGHT_WEIGHTS.get("time_date", 4))
        row_index += 1
        self.grid_rowconfigure(row_index, weight=config.REGION_HEIGHT_WEIGHTS.get("current_conditions", 3))
        row_index += 1
        self.grid_rowconfigure(row_index, weight=config.REGION_HEIGHT_WEIGHTS.get("forecast", 5))

        # --- Create Main Region Frames ---
        current_row = 0

        # Status Bar Frame (Optional)
        self.status_bar_frame = None
        if config.OPTIONAL_ELEMENTS.get("show_status_bar", True):
            self.status_bar_frame = ctk.CTkFrame(
                self,
                height=config.CONNECTION_FRAME_HEIGHT,
                corner_radius=0, # Typically no radius for a top bar
                fg_color=self._get_color("frame_background") # Use theme color
            )
            self.status_bar_frame.grid(row=current_row, column=0, sticky="ew")
            # Configure columns for status indicators (push to right)
            self.status_bar_frame.grid_columnconfigure(0, weight=1) # Spacer
            self.status_bar_frame.grid_columnconfigure(1, weight=0) # Network Status
            self.status_bar_frame.grid_columnconfigure(2, weight=0) # API Status
            self.status_bar_frame.grid_propagate(False) # Prevent shrinking
            logger.debug("Status bar frame created.")
            current_row += 1
        else:
            logger.debug("Status bar is disabled in config.")

        # Time and Date Region Frame
        self.time_date_frame = ctk.CTkFrame(
            self,
            corner_radius=config.FRAME_CORNER_RADIUS,
            fg_color="transparent" # Often transparent to show window background
            # fg_color=self._get_color("frame_background") # Or use frame color
        )
        self.time_date_frame.grid(
            row=current_row, column=0, sticky="nsew",
            padx=config.ELEMENT_MARGINS['padx'], # Use margins between regions
            pady=config.ELEMENT_MARGINS['pady']
        )
        # Configure internal grid for time/date elements (e.g., 2 columns)
        self.time_date_frame.grid_columnconfigure(0, weight=2) # Time column wider
        self.time_date_frame.grid_columnconfigure(1, weight=1) # Date column
        self.time_date_frame.grid_rowconfigure(0, weight=1)    # Single row expands
        logger.debug("Time/Date frame created.")
        current_row += 1

        # Current Conditions Region Frame
        self.current_conditions_frame = ctk.CTkFrame(
            self,
            corner_radius=config.FRAME_CORNER_RADIUS,
            fg_color=self._get_color("frame_background")
        )
        self.current_conditions_frame.grid(
            row=current_row, column=0, sticky="nsew",
            padx=config.ELEMENT_MARGINS['padx'],
            pady=config.ELEMENT_MARGINS['pady']
        )
        # Configure internal grid for temp, humidity, aqi (e.g., 3 columns)
        num_current_cols = 1 # Start with temp
        if config.OPTIONAL_ELEMENTS.get("show_current_humidity", True): num_current_cols += 1
        if config.OPTIONAL_ELEMENTS.get("show_current_air_quality", True): num_current_cols += 1
        if num_current_cols > 0:
            self.current_conditions_frame.grid_columnconfigure(tuple(range(num_current_cols)), weight=1)
        self.current_conditions_frame.grid_rowconfigure(0, weight=1) # Single row expands
        logger.debug("Current Conditions frame created.")
        current_row += 1

        # Forecast Region Frame
        self.forecast_frame = ctk.CTkFrame(
            self,
            corner_radius=config.FRAME_CORNER_RADIUS,
            fg_color=self._get_color("frame_background")
        )
        self.forecast_frame.grid(
            row=current_row, column=0, sticky="nsew",
            padx=config.ELEMENT_MARGINS['padx'],
            pady=config.ELEMENT_MARGINS['pady']
        )
        # Configure internal grid for forecast days (e.g., 3 columns)
        num_forecast_days = 3 # Assuming 3 days for now
        self.forecast_frame.grid_columnconfigure(tuple(range(num_forecast_days)), weight=1)
        self.forecast_frame.grid_rowconfigure(0, weight=1) # Single row expands
        logger.debug("Forecast frame created.")

        logger.debug("Main layout setup complete.")

    def _create_widgets(self):
        """Creates and places all UI widgets within their respective region frames."""
        logger.debug("Creating UI widgets...")
        if self.status_bar_frame:
            self._create_status_bar()
        self._create_time_date_region()
        self._create_current_conditions_region()
        self._create_forecast_region()
        logger.debug("UI widget creation complete.")

    def _create_status_bar(self):
        """Creates the status indicator labels in the status bar frame."""
        if not self.status_bar_frame: return # Should not happen if called correctly
        logger.debug("Creating status bar indicators...")

        indicator_font = self._get_font('status_indicator')
        text_color = self._get_color('status_text')
        padx = config.ELEMENT_PADDING['padx'] // 2 # Use smaller padding for persistent labels
        pady = config.ELEMENT_PADDING['pady'] // 2

        # --- Network Status Label ---
        self.network_status_label = ctk.CTkLabel(
            self.status_bar_frame,
            text="Network: Pending", # Initial text
            font=indicator_font,
            text_color=text_color,
            anchor="e"
        )
        self.network_status_label.grid(row=0, column=1, sticky="e", padx=padx, pady=pady)
        logger.debug("Network status label created.")

        # --- API Status Label ---
        self.api_status_label = ctk.CTkLabel(
            self.status_bar_frame,
            text="API: Pending", # Initial text
            font=indicator_font,
            text_color=text_color,
            anchor="e"
        )
        self.api_status_label.grid(row=0, column=2, sticky="e", padx=padx, pady=pady)
        logger.debug("API status label created.")

    def _create_time_date_region(self):
        """Creates widgets for the time and date display region."""
        logger.debug("Creating time/date region widgets...")
        parent_frame = self.time_date_frame
        text_color = self._get_color('text')
        region_padx = config.REGION_PADDING['padx']
        region_pady = config.REGION_PADDING['pady']
        element_padx = config.ELEMENT_PADDING['padx']
        element_pady = config.ELEMENT_PADDING['pady']
        text_pady = config.TEXT_PADDING['pady']

        # --- Time Display ---
        self.time_label = ctk.CTkLabel(
            parent_frame,
            text="00:00",
            font=self._get_font('time'),
            text_color=text_color,
            anchor="center",
            justify="center"
        )
        self.time_label.grid(
            row=0, column=0, sticky="nsew",
            padx=(region_padx, element_padx), # Region padding left, element padding right
            pady=region_pady
        )
        logger.debug("Time display label created.")

        # --- Date Display ---
        # Outer frame for positioning date block
        self.date_display_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.date_display_frame.grid(
            row=0, column=1, sticky="nsew", # Changed sticky to fill vertically
            padx=(element_padx, region_padx), # Element padding left, region padding right
            pady=region_pady
        )
        # Center the inner content frame
        self.date_display_frame.grid_columnconfigure(0, weight=1)
        self.date_display_frame.grid_rowconfigure(0, weight=1)

        # Inner frame for stacking labels
        inner_date_labels_frame = ctk.CTkFrame(self.date_display_frame, fg_color="transparent")
        inner_date_labels_frame.grid(row=0, column=0, sticky="") # Center

        # Weekday Label
        self.weekday_label = ctk.CTkLabel(
            inner_date_labels_frame, text="Weekday",
            font=self._get_font('weekday'),
            text_color=text_color
        )
        self.weekday_label.pack(pady=(0, text_pady))

        # Day Label
        self.day_label = ctk.CTkLabel(
            inner_date_labels_frame, text="00",
            font=self._get_font('day_number'),
            text_color=text_color
        )
        self.day_label.pack(pady=0)

        # Month Year Label
        self.month_year_label = ctk.CTkLabel(
            inner_date_labels_frame, text="Month 0000",
            font=self._get_font('month_year'),
            text_color=text_color
        )
        self.month_year_label.pack(pady=(text_pady, 0))
        logger.debug("Date display labels created.")

    def _create_current_conditions_region(self):
        """Creates widgets for the current conditions (Temp, Humidity, AQI)."""
        logger.debug("Creating current conditions region widgets...")
        parent_frame = self.current_conditions_frame
        text_color = self._get_color('text')
        title_color = self._get_color('text_secondary', text_color) # Use secondary if available
        region_padx = config.REGION_PADDING['padx']
        region_pady = config.REGION_PADDING['pady']
        element_padx = config.ELEMENT_PADDING['padx']
        element_pady = config.ELEMENT_PADDING['pady']
        text_padx = config.TEXT_PADDING['padx']
        text_pady = config.TEXT_PADDING['pady']
        frame_radius = config.FRAME_CORNER_RADIUS
        frame_color = self._get_color("background") # Use main background for sub-frames

        current_col = 0

        # --- Temperature Sub-section ---
        logger.debug("Creating temperature display...")
        self.temp_frame = ctk.CTkFrame(
            parent_frame,
            corner_radius=frame_radius,
            fg_color=frame_color
        )
        self.temp_frame.grid(
            row=0, column=current_col, sticky="nsew",
            padx=element_padx, pady=element_pady
        )
        self.temp_frame.grid_rowconfigure(0, weight=0) # Title row
        self.temp_frame.grid_rowconfigure(1, weight=1) # Value row (expands)
        self.temp_frame.grid_columnconfigure(0, weight=1) # Single column expands

        self.temp_title = ctk.CTkLabel(
            self.temp_frame, text=get_translation('temperature', config.LANGUAGE),
            font=self._get_font('current_temp_title'),
            text_color=title_color
        )
        self.temp_title.grid(row=0, column=0, sticky="ew", padx=text_padx, pady=(text_pady*2, text_pady))

        self.temp_value = ctk.CTkLabel(
            self.temp_frame, text="--°C",
            font=self._get_font('current_temp_value'),
            text_color=text_color
        )
        self.temp_value.grid(row=1, column=0, sticky="n", padx=element_padx, pady=element_pady)
        current_col += 1

        # --- Humidity Sub-section (Optional) ---
        self.humidity_frame = None
        self.humidity_title = None
        self.humidity_value = None
        if config.OPTIONAL_ELEMENTS.get("show_current_humidity", True):
            logger.debug("Creating humidity display...")
            self.humidity_frame = ctk.CTkFrame(
                parent_frame,
                corner_radius=frame_radius,
                fg_color=frame_color
            )
            self.humidity_frame.grid(
                row=0, column=current_col, sticky="nsew",
                padx=element_padx, pady=element_pady
            )
            self.humidity_frame.grid_rowconfigure(0, weight=0) # Title
            self.humidity_frame.grid_rowconfigure(1, weight=1) # Value
            self.humidity_frame.grid_columnconfigure(0, weight=1) # Column

            self.humidity_title = ctk.CTkLabel(
                self.humidity_frame, text=get_translation('humidity', config.LANGUAGE),
                font=self._get_font('current_humidity_title'),
                text_color=title_color
            )
            self.humidity_title.grid(row=0, column=0, sticky="ew", padx=text_padx, pady=(text_pady*2, text_pady))

            self.humidity_value = ctk.CTkLabel(
                self.humidity_frame, text="--%",
                font=self._get_font('current_humidity_value'),
                text_color=text_color
            )
            self.humidity_value.grid(row=1, column=0, sticky="n", padx=element_padx, pady=element_pady)
            current_col += 1
        else:
            logger.debug("Humidity display is disabled in config.")

        # --- Air Quality Sub-section (Optional) ---
        self.air_quality_frame = None
        self.air_quality_title = None
        self.air_quality_value = None
        if config.OPTIONAL_ELEMENTS.get("show_current_air_quality", True):
            logger.debug("Creating air quality display...")
            self.air_quality_frame = ctk.CTkFrame(
                parent_frame,
                corner_radius=frame_radius,
                fg_color=frame_color
            )
            self.air_quality_frame.grid(
                row=0, column=current_col, sticky="nsew",
                padx=element_padx, pady=element_pady
            )
            self.air_quality_frame.grid_rowconfigure(0, weight=0) # Title
            self.air_quality_frame.grid_rowconfigure(1, weight=1) # Value
            self.air_quality_frame.grid_columnconfigure(0, weight=1) # Column

            self.air_quality_title = ctk.CTkLabel(
                self.air_quality_frame, text=get_translation('air_quality', config.LANGUAGE),
                font=self._get_font('current_aqi_title'),
                text_color=title_color
            )
            self.air_quality_title.grid(row=0, column=0, sticky="ew", padx=text_padx, pady=(text_pady*2, text_pady))

            self.air_quality_value = ctk.CTkLabel(
                self.air_quality_frame, text="--",
                font=self._get_font('current_aqi_value'),
                text_color=text_color
            )
            self.air_quality_value.grid(row=1, column=0, sticky="n", padx=element_padx, pady=element_pady)
            current_col += 1
        else:
             logger.debug("Air quality display is disabled in config.")

        logger.debug("Current conditions region widgets created.")


    def _create_forecast_region(self):
        """Creates the frames and labels for the multi-day forecast region."""
        logger.debug("Creating forecast region widgets...")
        parent_frame = self.forecast_frame
        text_color = self._get_color('text')
        region_padx = config.REGION_PADDING['padx']
        region_pady = config.REGION_PADDING['pady']
        element_padx = config.ELEMENT_PADDING['padx']
        element_pady = config.ELEMENT_PADDING['pady']
        text_pady = config.TEXT_PADDING['pady']
        frame_radius = config.FRAME_CORNER_RADIUS
        frame_color = self._get_color("background") # Use main background for sub-frames

        self.forecast_day_frames: List[Dict[str, ctk.CTkLabel]] = []
        na_text = get_translation('not_available', config.LANGUAGE)
        num_forecast_days = 3 # Hardcoded for now, could be configurable

        for i in range(num_forecast_days):
            logger.debug(f"Creating forecast frame for day {i+1}...")
            day_frame = ctk.CTkFrame(
                parent_frame,
                corner_radius=frame_radius,
                fg_color=frame_color
            )
            day_frame.grid(
                row=0, column=i, sticky="nsew",
                padx=element_padx, pady=element_pady
            )
            # Configure internal grid layout for each forecast day
            day_frame.grid_columnconfigure(0, weight=1) # Single column expands
            day_frame.grid_rowconfigure(0, weight=0) # Day name
            day_frame.grid_rowconfigure(1, weight=1) # Icon (takes space)
            day_frame.grid_rowconfigure(2, weight=0) # Condition
            day_frame.grid_rowconfigure(3, weight=0) # Temp

            # --- Create widgets for this forecast day ---
            day_label = ctk.CTkLabel(
                day_frame, text=f"Day {i+1}",
                font=self._get_font('forecast_day'),
                text_color=text_color
            )
            day_label.grid(row=0, column=0, pady=(text_pady * 2, text_pady))

            icon_label = ctk.CTkLabel(day_frame, text="", image=None)
            icon_label.grid(row=1, column=0, pady=element_pady)

            condition_label = ctk.CTkLabel(
                day_frame, text=na_text,
                font=self._get_font('forecast_condition'),
                text_color=text_color
            )
            condition_label.grid(row=2, column=0, pady=text_pady)

            temp_label = ctk.CTkLabel(
                day_frame, text="--° / --°",
                font=self._get_font('forecast_temp'),
                text_color=text_color
            )
            temp_label.grid(row=3, column=0, pady=(text_pady, text_pady * 2))

            self.forecast_day_frames.append({
                'frame': day_frame, # Keep ref to frame if needed later
                'day': day_label,
                'icon': icon_label,
                'condition': condition_label,
                'temp': temp_label
            })
            logger.debug(f"Forecast frame {i+1} created.")
        logger.debug("Forecast region widgets created.")

    def _setup_bindings(self):
        """Sets up keyboard bindings."""
        logger.debug("Setting up keyboard bindings...")
        self.bind("<Escape>", self.exit_fullscreen)
        logger.debug("'<Escape>' key bound to exit_fullscreen.")

    # --- Public Update Methods ---

    def update_time(self, time_str: str):
        """Updates the time display label (HH:MM)."""
        logger.debug(f"Updating time display with: {time_str}")
        try:
            time_parts = time_str.split(':')
            formatted_time = f"{time_parts[0]}:{time_parts[1]}" if len(time_parts) >= 2 else time_str
            self.time_label.configure(text=formatted_time)
        except Exception as e:
             logger.error(f"Error updating time display: {e}")
             self.time_label.configure(text="Error")

    def update_date(self, date_str: str):
        """Updates the date display labels (weekday, day, month/year)."""
        logger.debug(f"Updating date display with: {date_str}")
        try:
            parts = date_str.split(', ')
            if len(parts) == 2:
                weekday = parts[0]
                date_parts = parts[1].split(' ')
                if len(date_parts) == 3:
                    day = date_parts[0].lstrip('0')
                    month = date_parts[1]
                    year = date_parts[2]
                    self.weekday_label.configure(text=weekday)
                    self.day_label.configure(text=day)
                    self.month_year_label.configure(text=f"{month} {year}")
                    return
            # Fallback if parsing fails
            logger.warning(f"Could not parse date string: '{date_str}'. Displaying raw.")
            self.weekday_label.configure(text=date_str)
            self.day_label.configure(text="")
            self.month_year_label.configure(text="")
        except Exception as e:
            logger.error(f"Error updating date display for '{date_str}': {e}")
            na_text = get_translation('not_available', config.LANGUAGE)
            self.weekday_label.configure(text=na_text)
            self.day_label.configure(text="")
            self.month_year_label.configure(text="")

    def update_current_weather(self, weather_result: Dict[str, Any]):
        """Updates the current weather display section."""
        logger.debug(f"Updating current weather display. Received data keys: {list(weather_result.keys())}")

        # Status indicators are updated separately by calls from main.py
        # Do not call self.update_status_indicators from here.

        current_data = weather_result.get('data', {})
        if not current_data:
             logger.warning("Received empty 'data' dictionary in update_current_weather. Cannot update labels.")
             # Optionally set labels to NA here if desired, but they should retain previous value otherwise.
             # return # Or return early

        na_text = get_translation('not_available', config.LANGUAGE)

        # Update Temperature (Always shown)
        temp = current_data.get('temperature')
        temp_text = f"{int(round(temp))}°C" if temp is not None else na_text
        if self.temp_value: self.temp_value.configure(text=temp_text)
        logger.debug(f"Temperature updated to: {temp_text}")

        # Update Humidity (If shown)
        if self.humidity_value:
            humidity = current_data.get('humidity')
            humidity_text = f"{humidity}%" if humidity is not None else na_text
            self.humidity_value.configure(text=humidity_text)
            logger.debug(f"Humidity updated to: {humidity_text}")

        # Update Air Quality (If shown)
        if self.air_quality_value:
            aqi_category = current_data.get('air_quality_category')
            aqi_value = current_data.get('air_quality_index')
            aqi_text = na_text
            if aqi_category is not None:
                translated_aqi = translate_aqi_category(aqi_category, config.LANGUAGE)
                # aqi_text = f"{translated_aqi} ({aqi_value})" if aqi_value is not None else translated_aqi
                aqi_text = translated_aqi # Keep it simple for now
            self.air_quality_value.configure(text=aqi_text)
            logger.debug(f"Air Quality updated to: {aqi_text}") # Corrected indentation

    def update_forecast(self, forecast_result: Dict[str, Any]):
        """
        Updates the multi-day forecast display section.

        Note: This method does NOT update the main status indicators itself.
        Status updates are handled by `update_current_weather` (for IMS) and
        the AccuWeather update cycle in `main.py` which calls
        `update_status_indicators` directly.
        """
        logger.debug(f"Updating forecast display. API Status: {forecast_result.get('api_status')}")
        # We don't update the main status bar from here, as it's handled centrally

        forecast_data: List[Dict[str, Any]] = forecast_result.get('data', [])
        na_text = get_translation('not_available', config.LANGUAGE)
        icon_size = config.FORECAST_ICON_SIZE

        for i, day_widgets in enumerate(self.forecast_day_frames):
            if i < len(forecast_data):
                day_data = forecast_data[i]
                logger.debug(f"Updating forecast day {i+1} with data: {day_data}")

                date_str = day_data.get('date')
                max_temp = day_data.get('max_temp')
                min_temp = day_data.get('min_temp')
                condition = day_data.get('condition')
                icon_code = day_data.get('icon_code')

                # Update Day Name
                day_name = get_day_name(date_str) if date_str else na_text
                day_widgets['day'].configure(text=day_name)

                # Update Icon
                icon_image = self.icon_handler.load_icon(icon_code, icon_size)
                if icon_image:
                    day_widgets['icon'].configure(image=icon_image, text="")
                else:
                    day_widgets['icon'].configure(image=None, text=na_text)
                    logger.warning(f"Failed to load forecast icon for code: {icon_code}")

                # Update Condition Text
                translated_condition = translate_weather_condition(condition, config.LANGUAGE) if condition else na_text
                day_widgets['condition'].configure(text=translated_condition)

                # Update Temperature Range
                temp_text = na_text
                if max_temp is not None and min_temp is not None:
                    temp_text = f"{int(round(max_temp))}° / {int(round(min_temp))}°"
                elif max_temp is not None:
                    temp_text = f"{int(round(max_temp))}° / --°"
                elif min_temp is not None:
                    temp_text = f"--° / {int(round(min_temp))}°"
                day_widgets['temp'].configure(text=temp_text)

            else:
                # No data for this frame, clear it
                logger.debug(f"No forecast data available for day {i+1}. Clearing frame.")
                day_widgets['day'].configure(text=na_text)
                day_widgets['icon'].configure(image=None, text="")
                day_widgets['condition'].configure(text="")
                day_widgets['temp'].configure(text="")

    def update_status_indicators(self, connection_status: bool, api_status: Optional[str], last_success_time: Optional[float]):
        """
        Updates the persistent status indicator labels for network and API status.

        Args:
            connection_status (bool): The current internet connection status.
            api_status (Optional[str]): The status of the last relevant API call
                                        ('ok', 'limit_reached', 'error', 'mock', 'offline', None).
                                        None might indicate an initial state or IMS-only update.
            last_success_time (Optional[float]): The timestamp (time.time()) of the
                                                 last successful AccuWeather API call.
                                                 None if no successful call yet or if the
                                                 update is only for IMS.
        """
        # Only proceed if status bar is enabled and widgets exist
        if not self.status_bar_frame or not self.network_status_label or not self.api_status_label:
            return

        logger.debug(f"Updating status indicators: Connection={connection_status}, API Status='{api_status}', Last Success Time={last_success_time}")

        # --- Update Network Status Label ---
        network_text = "Network: OK" if connection_status else "Network: Offline"
        # TODO: Add localization for network status text
        # TODO: Add color coding based on status (e.g., green for OK, red for Offline)
        network_color = self._get_color("status_ok_text") if connection_status else self._get_color("status_error_text")
        self.network_status_label.configure(text=network_text, text_color=network_color)

        # --- Update API Status Label ---
        api_text = "API: Pending" # Default
        api_color = self._get_color("status_text") # Default color

        # Format the last success time if available
        success_time_str = "--:--"
        if last_success_time:
            try:
                success_time_str = datetime.fromtimestamp(last_success_time).strftime('%H:%M')
            except Exception as e:
                logger.error(f"Error formatting last success timestamp {last_success_time}: {e}")
                success_time_str = "??:??" # Indicate formatting error

        # Determine API status text and color
        if api_status == 'ok':
            # If last_success_time is None, it might be an IMS 'ok' status
            time_suffix = f" ({success_time_str})" if last_success_time else ""
            api_text = f"API: OK{time_suffix}"
            api_color = self._get_color("status_ok_text")
        elif api_status == 'limit_reached':
            api_text = f"API: Limit ({success_time_str})"
            api_color = self._get_color("status_warning_text") # Use a warning color
        elif api_status == 'error':
            api_text = f"API: Error ({success_time_str})"
            api_color = self._get_color("status_error_text")
        elif api_status == 'mock':
            api_text = "API: Mock" # No time needed for mock
            api_color = self._get_color("status_text") # Neutral color
        elif api_status == 'offline': # This might be set by AccuWeatherClient if connection drops mid-fetch
             api_text = f"API: Offline ({success_time_str})"
             api_color = self._get_color("status_error_text")
        elif api_status is None and last_success_time is None:
             api_text = "API: Pending" # Initial state before first fetch
             api_color = self._get_color("status_text")
        elif api_status is None and last_success_time is not None:
             # This case might occur if IMS update happens after a successful AccuWeather update
             # Keep showing the last known AccuWeather status time
             api_text = f"API: OK ({success_time_str})" # Assume OK if time exists but status is None
             api_color = self._get_color("status_ok_text")
        else:
             # Catch any unexpected api_status values
             api_text = f"API: {api_status} ({success_time_str})"
             api_color = self._get_color("status_text")

        # TODO: Add localization for API status prefixes ("API: OK", "API: Limit", etc.)
        self.api_status_label.configure(text=api_text, text_color=api_color)

    def exit_fullscreen(self, event=None):
        """Callback to exit fullscreen mode."""
        try:
            logger.info("Attempting to exit fullscreen mode (Escape key pressed)...")
            self.attributes("-fullscreen", False)
            self.overrideredirect(False) # Restore decorations if removed
            self.state('normal')
            # Optionally restore configured size
            # self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
            logger.info("Exited fullscreen mode successfully.")
        except Exception as e:
            logger.error(f"Error encountered while exiting fullscreen mode: {e}")

# --- Color Configuration (Placeholder - Define these in config.py) ---
# Add placeholder color keys to config.ACTIVE_COLORS if they don't exist
# Example additions to config.py's COLOR_THEME dictionaries:
# 'status_ok_text': ('#00C853', '#4CAF50'),      # Greenish for OK
# 'status_warning_text': ('#FFAB00', '#FFB300'), # Amber/Orange for Warning/Limit
# 'status_error_text': ('#D50000', '#F44336'),   # Reddish for Error/Offline
