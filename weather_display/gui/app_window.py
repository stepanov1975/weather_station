"""
Main application window (GUI) for the Weather Display using CustomTkinter.

This module defines the `AppWindow` class, which represents the main graphical
user interface of the application. It displays time, date, current weather,
forecast information, and connection status indicators.
"""

import logging
from typing import Dict, List, Any, Optional
import os

import customtkinter as ctk
from PIL import Image

# Local application imports
from .. import config
from ..utils.localization import (
    get_translation,
    translate_weather_condition,
    translate_aqi_category
)
from ..utils.icon_handler import WeatherIconHandler
# Import get_day_name here as it's used in update_forecast
from ..utils.helpers import get_day_name

# Attempt to import ImageTk (optional, primarily for type hinting if needed elsewhere)
try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None # Handle gracefully if Pillow is not fully installed

logger = logging.getLogger(__name__)

# --- Global UI Setup (Theme and Appearance) ---
# Set appearance mode and default color theme based on config
# This should ideally be done once at application startup.
ctk.set_appearance_mode("dark" if config.DARK_MODE else "light")
ctk.set_default_color_theme("blue") # Or load from config if desired


class AppWindow(ctk.CTk):
    """
    Main application window class using CustomTkinter.

    Manages the layout, widgets, and updates for displaying weather information.

    Attributes:
        icon_handler (WeatherIconHandler): Instance for loading weather icons.
        connection_frame (ctk.CTkFrame): Top bar for status indicators.
        top_frame (ctk.CTkFrame): Upper section containing time, date, current weather.
        bottom_frame (ctk.CTkFrame): Lower section containing the forecast.
        # Widget references (add type hints)
        connection_indicator (ctk.CTkLabel): Label for internet status.
        api_limit_indicator (ctk.CTkLabel): Label for API limit status.
        api_error_indicator (ctk.CTkLabel): Label for general API error status.
        time_label (ctk.CTkLabel): Label displaying the current time.
        weekday_label (ctk.CTkLabel): Label for the day of the week.
        day_label (ctk.CTkLabel): Label for the day of the month.
        month_year_label (ctk.CTkLabel): Label for the month and year.
        current_weather_frame (ctk.CTkFrame): Frame holding current weather details.
        current_weather_title (ctk.CTkLabel): Title label for current weather.
        temp_frame (ctk.CTkFrame): Frame for temperature display.
        temp_title (ctk.CTkLabel): Title for temperature.
        temp_value (ctk.CTkLabel): Value label for temperature.
        humidity_frame (ctk.CTkFrame): Frame for humidity display.
        humidity_title (ctk.CTkLabel): Title for humidity.
        humidity_value (ctk.CTkLabel): Value label for humidity.
        air_quality_frame (ctk.CTkFrame): Frame for AQI display.
        air_quality_title (ctk.CTkLabel): Title for AQI.
        air_quality_value (ctk.CTkLabel): Value label for AQI.
        forecast_frames (List[Dict[str, ctk.CTkLabel]]): List of dictionaries,
            each holding widget references for a single forecast day.
    """

    def __init__(self):
        """Initialize the application window, layout, and widgets."""
        super().__init__()

        self.title(get_translation('app_title', config.LANGUAGE))
        self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")

        # Instantiate the icon handler for loading forecast icons
        self.icon_handler = WeatherIconHandler()

        self._configure_fullscreen()
        self._setup_layout()
        self._create_widgets()
        self._setup_bindings()

        logger.info("Application window initialized.")

    def _configure_fullscreen(self):
        """Configure fullscreen mode based on config settings."""
        if config.FULLSCREEN:
            try:
                # Attempt multiple methods for cross-platform compatibility
                self.attributes("-fullscreen", True)
                # Fallback methods if the first doesn't work immediately
                if not self.winfo_viewable():
                    self.overrideredirect(True) # More forceful, removes window decorations
                    self.state('normal')
                    self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
                if not self.winfo_viewable(): # If still not working, try maximizing state
                    self.state('zoomed' if os.name == 'nt' else 'normal') # 'zoomed' on Windows
                    self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

                logger.info("Fullscreen mode enabled.")
            except Exception as e:
                logger.error(f"Error setting fullscreen mode: {e}. Falling back.")
                # Fallback to maximized window state
                try:
                    self.state('zoomed' if os.name == 'nt' else 'normal')
                    self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
                except Exception as fallback_e:
                     logger.error(f"Error setting fallback maximized state: {fallback_e}")
                     # Last resort: use configured size
                     self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")

    def _setup_layout(self):
        """Configure the main grid layout and create primary frames."""
        # Configure root window grid
        self.grid_columnconfigure(0, weight=1) # Single column stretches
        self.grid_rowconfigure(0, weight=0)  # Connection status bar (fixed height)
        self.grid_rowconfigure(1, weight=1)  # Top frame (time, date, current) - expands
        self.grid_rowconfigure(2, weight=1)  # Bottom frame (forecast) - expands

        # --- Create Main Frames ---
        # Connection Status Bar (Top)
        self.connection_frame = ctk.CTkFrame(
            self, corner_radius=0, height=config.CONNECTION_FRAME_HEIGHT
        )
        self.connection_frame.grid(row=0, column=0, sticky="ew")
        # Configure columns: 0 expands (spacer), 1, 2, 3 are for indicators
        self.connection_frame.grid_columnconfigure(0, weight=1) # Spacer column pushes indicators right
        self.connection_frame.grid_columnconfigure(1, weight=0) # Connection indicator
        self.connection_frame.grid_columnconfigure(2, weight=0) # API Limit indicator
        self.connection_frame.grid_columnconfigure(3, weight=0) # API Error indicator
        self.connection_frame.grid_propagate(False) # Prevent resizing by content

        # Top Section (Time, Date, Current Weather)
        self.top_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.top_frame.grid(row=1, column=0, sticky="nsew")
        # Configure top_frame grid: 2/3 for time (col 0), 1/3 for date (col 1)
        self.top_frame.grid_columnconfigure(0, weight=2)
        self.top_frame.grid_columnconfigure(1, weight=1)
        # Row 0 for Time/Date - allow vertical expansion for centering content
        self.top_frame.grid_rowconfigure(0, weight=1)
        # Row 1 for Current Weather - allow expansion
        self.top_frame.grid_rowconfigure(1, weight=2)

        # Bottom Section (Forecast)
        self.bottom_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="nsew")
        # Configure bottom_frame grid for 3 forecast days
        self.bottom_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.bottom_frame.grid_rowconfigure(0, weight=1) # Single row expands

    def _create_widgets(self):
        """Create and place all UI widgets by calling helper methods."""
        self._create_status_bar()
        self._create_time_display()
        self._create_date_display()
        self._create_current_weather_display()
        self._create_forecast_display()

    def _create_status_bar(self):
        """Create widgets for the connection status bar."""
        self.connection_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('no_internet', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.STATUS_INDICATOR_FONT_SIZE),
            fg_color=config.NO_CONNECTION_COLOR,
            text_color=config.STATUS_TEXT_COLOR,
            corner_radius=config.STATUS_INDICATOR_CORNER_RADIUS
        )
        # Place Connection Indicator in column 1
        self.connection_indicator.grid(
            row=0, column=1, sticky="e",
            padx=config.ELEMENT_PADDING_X, # Standard padding
            pady=config.ELEMENT_PADDING_Y
        )
        self.connection_indicator.grid_remove() # Hide initially

        # API Limit Indicator
        self.api_limit_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('api_limit_reached', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.STATUS_INDICATOR_FONT_SIZE),
            fg_color=config.API_LIMIT_COLOR,
            text_color=config.STATUS_TEXT_COLOR,
            corner_radius=config.STATUS_INDICATOR_CORNER_RADIUS
        )
        # Place API Limit Indicator in column 2
        self.api_limit_indicator.grid(
            row=0, column=2, sticky="e",
            padx=config.ELEMENT_PADDING_X,
            pady=config.ELEMENT_PADDING_Y
        )
        self.api_limit_indicator.grid_remove() # Hide initially

        # API Error Indicator
        self.api_error_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('api_error', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.STATUS_INDICATOR_FONT_SIZE),
            fg_color=config.API_ERROR_COLOR,
            text_color=config.STATUS_TEXT_COLOR,
            corner_radius=config.STATUS_INDICATOR_CORNER_RADIUS
        )
        # Place API Error Indicator in column 3
        self.api_error_indicator.grid(
            row=0, column=3, sticky="e",
            padx=config.ELEMENT_PADDING_X,
            pady=config.ELEMENT_PADDING_Y
        )
        self.api_error_indicator.grid_remove() # Hide initially

    def _create_time_display(self):
        """Create the large time display label."""
        self.time_label = ctk.CTkLabel(
            self.top_frame,
            text="00:00", # Initial text
            font=ctk.CTkFont(
                family=config.FONT_FAMILY,
                size=config.TIME_FONT_SIZE_BASE + config.TIME_FONT_SIZE_INCREASE,
                weight="bold"
            )
        )
        # Make the label fill the cell; text is centered by default within the label
        self.time_label.grid(
            row=0, column=0, sticky="nsew", # Fill cell, text defaults to center
            padx=(config.SECTION_PADDING_X, config.ELEMENT_PADDING_X),
            pady=config.SECTION_PADDING_Y
        )

    def _create_date_display(self):
        """Create the stacked date display labels."""
        # Frame to hold the stacked date elements
        self.date_display_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.date_display_frame.grid(
            row=0, column=1, sticky="ns", # Fill vertically, center horizontally
            padx=(config.ELEMENT_PADDING_X, config.SECTION_PADDING_X),
            pady=config.SECTION_PADDING_Y
        )
        # Configure the main date frame to have one expanding cell to center content
        self.date_display_frame.grid_columnconfigure(0, weight=1)
        self.date_display_frame.grid_rowconfigure(0, weight=1)

        # Create an inner frame to hold the actual labels, this inner frame will be centered
        inner_date_labels_frame = ctk.CTkFrame(self.date_display_frame, fg_color="transparent")
        inner_date_labels_frame.grid(row=0, column=0, sticky="") # Center the inner frame

        # --- Place labels inside the inner frame using pack for simple stacking ---
        # Weekday Label
        self.weekday_label = ctk.CTkLabel(
            inner_date_labels_frame, text="Weekday",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.DATE_FONT_SIZE_BASE)
        )
        self.weekday_label.pack(pady=(0, config.TEXT_PADDING_Y)) # Add padding below

        # Day Label (Large)
        self.day_label = ctk.CTkLabel(
            inner_date_labels_frame, text="00",
            font=ctk.CTkFont(
                family=config.FONT_FAMILY,
                size=config.DATE_FONT_SIZE_BASE + config.DATE_DAY_FONT_SIZE_INCREASE,
                weight="bold"
            )
        )
        self.day_label.pack(pady=0) # No extra padding around the main day number

        # Month Year Label
        self.month_year_label = ctk.CTkLabel(
            inner_date_labels_frame, text="Month 0000",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.DATE_FONT_SIZE_BASE)
        )
        self.month_year_label.pack(pady=(config.TEXT_PADDING_Y, 0)) # Add padding above

    def _create_current_weather_display(self):
        """Create frames and labels for the current weather section."""
        self.current_weather_frame = ctk.CTkFrame(self.top_frame)
        self.current_weather_frame.grid(
            row=1, column=0, columnspan=2, sticky="nsew",
            padx=config.SECTION_PADDING_X, pady=config.SECTION_PADDING_Y
        )
        # Configure grid for Temp, Humidity, AQI columns
        self.current_weather_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.current_weather_frame.grid_rowconfigure(0, weight=0)  # Title row
        self.current_weather_frame.grid_rowconfigure(1, weight=1)  # Content row

        # --- Temperature ---
        self.temp_frame = ctk.CTkFrame(self.current_weather_frame)
        self.temp_frame.grid(row=1, column=0, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)
        self.temp_frame.grid_rowconfigure(0, weight=0)
        self.temp_frame.grid_rowconfigure(1, weight=1)
        self.temp_title = ctk.CTkLabel(
            self.temp_frame, text=get_translation('temperature', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.temp_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)
        self.temp_value = ctk.CTkLabel(
            self.temp_frame, text="--°C",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE + 40, weight="bold")
        )
        self.temp_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        # --- Humidity ---
        self.humidity_frame = ctk.CTkFrame(self.current_weather_frame)
        self.humidity_frame.grid(row=1, column=1, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)
        self.humidity_frame.grid_rowconfigure(0, weight=0)
        self.humidity_frame.grid_rowconfigure(1, weight=1)
        self.humidity_title = ctk.CTkLabel(
            self.humidity_frame, text=get_translation('humidity', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.humidity_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)
        self.humidity_value = ctk.CTkLabel(
            self.humidity_frame, text="--%",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE + 40, weight="bold")
        )
        self.humidity_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        # --- Air Quality ---
        self.air_quality_frame = ctk.CTkFrame(self.current_weather_frame)
        self.air_quality_frame.grid(row=1, column=2, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)
        self.air_quality_frame.grid_rowconfigure(0, weight=0)
        self.air_quality_frame.grid_rowconfigure(1, weight=1)
        self.air_quality_title = ctk.CTkLabel(
            self.air_quality_frame, text=get_translation('air_quality', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.air_quality_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)
        self.air_quality_value = ctk.CTkLabel(
            self.air_quality_frame, text="--",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.air_quality_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

    def _create_forecast_display(self):
        """Create frames and labels for the 3-day forecast section."""
        self.forecast_frames: List[Dict[str, ctk.CTkLabel]] = []
        for i in range(3): # Assuming 3 forecast days
            forecast_frame = ctk.CTkFrame(self.bottom_frame)
            forecast_frame.grid(
                row=0, column=i, sticky="nsew",
                padx=config.SECTION_PADDING_X, pady=config.SECTION_PADDING_Y
            )
            # Configure rows within each forecast frame
            forecast_frame.grid_rowconfigure(0, weight=0)  # Day title
            forecast_frame.grid_rowconfigure(1, weight=1)  # Icon (expand vertically)
            forecast_frame.grid_rowconfigure(2, weight=0)  # Condition text
            forecast_frame.grid_rowconfigure(3, weight=0)  # Temperature text

            # Create labels for this day's forecast
            day_label = ctk.CTkLabel(
                forecast_frame, text=f"{get_translation('day', config.LANGUAGE)} {i+1}",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE, weight="bold")
            )
            day_label.grid(row=0, column=0, sticky="ew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

            icon_label = ctk.CTkLabel(forecast_frame, text="") # Placeholder for icon
            icon_label.grid(row=1, column=0, sticky="", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

            condition_label = ctk.CTkLabel(
                forecast_frame, text="--",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE)
            )
            condition_label.grid(row=2, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)

            temp_label = ctk.CTkLabel(
                forecast_frame, text="--°C / --°C",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE)
            )
            temp_label.grid(row=3, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

            # Store references to the labels for easy updating
            self.forecast_frames.append({
                'frame': forecast_frame, # Keep frame ref if needed for hiding
                'day': day_label,
                'icon': icon_label,
                'condition': condition_label,
                'temp': temp_label
            })

    def _setup_bindings(self):
        """Set up keyboard bindings."""
        self.bind("<Escape>", self.exit_fullscreen)

    # --- Update Methods ---

    def update_time(self, time_str: str):
        """
        Update the time display label (formats to HH:MM).

        Args:
            time_str: Time string, expected in HH:MM:SS format.
        """
        try:
            # Format time to HH:MM
            time_parts = time_str.split(':')
            if len(time_parts) >= 2:
                formatted_time = f"{time_parts[0]}:{time_parts[1]}"
                self.time_label.configure(text=formatted_time)
            else:
                logger.warning(f"Received unexpected time format: {time_str}")
                self.time_label.configure(text=time_str) # Fallback to raw string
        except Exception as e:
             logger.error(f"Error updating time display: {e}")
             self.time_label.configure(text="Error") # Show error state

    def update_date(self, date_str: str):
        """
        Update the multi-part date display labels.

        Parses the input date string to extract weekday, day, month, and year.
        Assumes a format like "Weekday, DD Month YYYY".

        Args:
            date_str: The full, localized date string.
        """
        try:
            # Attempt to parse based on expected format "Weekday, DD Month YYYY"
            parts = date_str.split(', ')
            if len(parts) == 2:
                weekday = parts[0]
                date_parts = parts[1].split(' ')
                if len(date_parts) == 3:
                    day = date_parts[0].lstrip('0') # Remove leading zero for display
                    month = date_parts[1]
                    year = date_parts[2]

                    # Update labels
                    self.weekday_label.configure(text=weekday)
                    self.day_label.configure(text=day)
                    self.month_year_label.configure(text=f"{month} {year}")
                    return # Success

            # Fallback if parsing fails
            logger.warning(f"Could not parse date string: '{date_str}'. Displaying raw.")
            self.weekday_label.configure(text=date_str) # Show full string in top label
            self.day_label.configure(text="")
            self.month_year_label.configure(text="")

        except Exception as e:
            logger.error(f"Error updating date display for '{date_str}': {e}")
            # Display fallback text on error
            na_text = get_translation('not_available', config.LANGUAGE)
            self.weekday_label.configure(text=na_text)
            self.day_label.configure(text="")
            self.month_year_label.configure(text="")

    def update_current_weather(self, weather_result: Dict[str, Any]):
        """
        Update the current weather display section (temp, humidity, AQI).

        Args:
            weather_result: The dictionary returned by `AccuWeatherClient.get_current_weather()`,
                            containing 'data', 'connection_status', and 'api_status'.
        """
        # Update status indicators first
        connection_status = weather_result.get('connection_status', False)
        api_status = weather_result.get('api_status', 'error')
        self.update_status_indicators(connection_status, api_status)

        # Extract the actual weather data dictionary
        current_data = weather_result.get('data', {})
        na_text = get_translation('not_available', config.LANGUAGE)

        # Update temperature
        temp = current_data.get('temperature')
        self.temp_value.configure(text=f"{int(round(temp))}°C" if temp is not None else na_text)

        # Update humidity
        humidity = current_data.get('humidity')
        self.humidity_value.configure(text=f"{humidity}%" if humidity is not None else na_text)

        # Update air quality
        aqi_category = current_data.get('air_quality_category')
        if aqi_category is not None:
            translated_aqi = translate_aqi_category(aqi_category, config.LANGUAGE)
            aqi_index = current_data.get('air_quality_index')
            display_text = f"{translated_aqi}" if aqi_index is not None else translated_aqi
            self.air_quality_value.configure(text=display_text)
        else:
            self.air_quality_value.configure(text=na_text)

        # Note: Current weather icon display was removed previously.

    def update_forecast(self, forecast_result: Dict[str, Any]):
        """
        Update the forecast display section (3 days).

        Args:
            forecast_result: The dictionary returned by `AccuWeatherClient.get_forecast()`,
                             containing 'data', 'connection_status', and 'api_status'.
        """
        # Update status indicators first
        connection_status = forecast_result.get('connection_status', False)
        api_status = forecast_result.get('api_status', 'error')
        self.update_status_indicators(connection_status, api_status)

        # Extract the list of daily forecast data
        forecast_days: List[Dict[str, Any]] = forecast_result.get('data', [])
        na_text = get_translation('not_available', config.LANGUAGE)
        icon_missing_text = get_translation('icon_missing', config.LANGUAGE)

        # Update forecast frames (up to the number of frames created)
        num_frames = len(self.forecast_frames)
        for i in range(num_frames):
            if i < len(forecast_days):
                day_data = forecast_days[i]
                frame_info = self.forecast_frames[i]
                frame_widget = frame_info['frame']
                frame_widget.grid() # Ensure frame is visible

                # Update day name
                date_iso = day_data.get('date')
                day_name_str = get_day_name(date_iso.split('T')[0]) if date_iso else na_text
                frame_info['day'].configure(text=day_name_str)

                # Update icon
                icon_code = day_data.get('icon_code')
                if icon_code is not None:
                    icon_image = self.icon_handler.load_icon(icon_code, size=config.FORECAST_ICON_SIZE)
                    if icon_image:
                        frame_info['icon'].configure(image=icon_image, text="")
                        frame_info['icon'].image = icon_image # Keep reference
                    else:
                        frame_info['icon'].configure(image=None, text=icon_missing_text)
                else:
                    frame_info['icon'].configure(image=None, text=icon_missing_text)

                # Update condition text
                condition = day_data.get('condition')
                translated_condition = translate_weather_condition(condition, config.LANGUAGE) if condition else na_text
                frame_info['condition'].configure(text=translated_condition)

                # Update temperature (Max / Min)
                max_temp = day_data.get('max_temp')
                min_temp = day_data.get('min_temp')
                if max_temp is not None and min_temp is not None:
                    temp_text = f"{int(round(max_temp))}°C / {int(round(min_temp))}°C"
                    frame_info['temp'].configure(text=temp_text)
                else:
                    frame_info['temp'].configure(text=na_text)

            else:
                # Hide unused forecast frames if API returns fewer days than expected
                self.forecast_frames[i]['frame'].grid_remove()

    def update_status_indicators(self, connection_status: bool, api_status: str):
        """
        Show or hide the connection and API limit status indicators.

        Args:
            connection_status: True if internet is connected, False otherwise.
            api_status: Status string from the API client ('ok', 'limit_reached', 'error', etc.).
        """
        # --- Handle Connection Status ---
        if not connection_status:
            # Show only connection error, hide others
            self.connection_indicator.grid()
            self.connection_indicator.lift()
            self.api_limit_indicator.grid_remove()
            self.api_error_indicator.grid_remove()
            return # No need to check API status if offline

        # --- Handle API Status (if connected) ---
        self.connection_indicator.grid_remove() # Hide connection error if connected

        # API Limit Indicator
        if api_status == 'limit_reached':
            self.api_limit_indicator.grid()
            self.api_limit_indicator.lift()
            self.api_error_indicator.grid_remove() # Hide error indicator
        # API Error Indicator
        elif api_status == 'error':
            self.api_error_indicator.grid()
            self.api_error_indicator.lift()
            self.api_limit_indicator.grid_remove() # Hide limit indicator
        # OK or Mock status - hide both API indicators
        else:
            self.api_limit_indicator.grid_remove()
            self.api_error_indicator.grid_remove()

    def exit_fullscreen(self, event=None):
        """Callback function to exit fullscreen mode (bound to Escape key)."""
        try:
            logger.info("Attempting to exit fullscreen mode...")
            self.attributes("-fullscreen", False)
            self.overrideredirect(False) # Ensure window decorations are back
            self.state('normal')
            # Optionally restore configured size, or let window manager decide
            # self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
            logger.info("Exited fullscreen mode.")
        except Exception as e:
            logger.error(f"Error exiting fullscreen mode: {e}")
