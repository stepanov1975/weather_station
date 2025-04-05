"""
Main application window (GUI) for the Weather Display using CustomTkinter.

Displays time, date, current weather, forecast, and connection status.
"""

import logging
import customtkinter as ctk
# Removed unused os import
from PIL import Image
# Import the new AQI translation function as well
from ..utils.localization import get_translation, translate_weather_condition, translate_aqi_category
try:
    from PIL import ImageTk
except ImportError:
    # This should not happen when running the GUI, but we'll handle it gracefully
    ImageTk = None
    logging.error("ImageTk is not available. GUI will not work properly.")

from .. import config
# Removed unused load_image import
# Import the WeatherIconHandler
from ..utils.icon_handler import WeatherIconHandler

logger = logging.getLogger(__name__)

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark" if config.DARK_MODE else "light")
ctk.set_default_color_theme("blue")

class AppWindow(ctk.CTk):
    """Main application window for the Weather Display."""
    
    def __init__(self):
        """Initialize the application window."""
        super().__init__()
        
        # Configure window
        self.title(get_translation('app_title', config.LANGUAGE))
        self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")

        # Instantiate the icon handler
        self.icon_handler = WeatherIconHandler()

        if config.FULLSCREEN:
            # Try multiple approaches for fullscreen
            try:
                # First approach: -fullscreen attribute
                self.attributes("-fullscreen", True)
                
                # Second approach: overrideredirect
                if not self.winfo_viewable():  # If not visible yet
                    self.overrideredirect(True)
                    self.state('normal')  # Set to normal state
                    # Maximize using geometry
                    self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
                
                # Third approach: maximize window
                if not self.winfo_viewable():  # If still not visible
                    # 'zoomed' is only valid on Windows, use 'normal' on Linux
                    self.state('normal')
                    # Try to maximize using geometry instead
                    self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
                
                logger.info("Fullscreen mode enabled")
            except Exception as e:
                logger.error(f"Error setting fullscreen mode: {e}")
                # Fallback to maximized window
                # 'zoomed' is only valid on Windows, use 'normal' on Linux
                self.state('normal')
                # Try to maximize using geometry instead
                self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Connection status frame
        self.grid_rowconfigure(1, weight=1)  # Top frame
        self.grid_rowconfigure(2, weight=1)  # Bottom frame

        # Create frames
        self.connection_frame = ctk.CTkFrame(self, corner_radius=0, height=config.CONNECTION_FRAME_HEIGHT) # Use config
        self.connection_frame.grid(row=0, column=0, sticky="ew")
        self.connection_frame.grid_columnconfigure(0, weight=1)
        self.connection_frame.grid_propagate(False)  # Prevent frame from resizing to fit content
        
        self.top_frame = ctk.CTkFrame(self, corner_radius=0)
        self.top_frame.grid(row=1, column=0, sticky="nsew")

        self.bottom_frame = ctk.CTkFrame(self, corner_radius=0)
        self.bottom_frame.grid(row=2, column=0, sticky="nsew")

        # Configure frame grid layout
        # Top frame: 2/3 for time (col 0), 1/3 for date (col 1)
        self.top_frame.grid_columnconfigure(0, weight=2)
        self.top_frame.grid_columnconfigure(1, weight=1)
        # Set weight=1 for row 0 to allow vertical expansion for centering
        self.top_frame.grid_rowconfigure(0, weight=1)
        self.top_frame.grid_rowconfigure(1, weight=2)  # Row for Current weather

        # Bottom frame for forecast
        self.bottom_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        
        # Initialize widgets
        self._create_widgets()
        
        # Set up key bindings
        self.bind("<Escape>", self.exit_fullscreen)
        
        logger.info("Application window initialized")
    
    def _create_widgets(self):
        """Create and configure widgets."""
        # Connection status indicator
        self.connection_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('no_internet', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.STATUS_INDICATOR_FONT_SIZE), # Use config
            fg_color=config.NO_CONNECTION_COLOR,  # Use config
            text_color=config.STATUS_TEXT_COLOR,  # Use config
            corner_radius=config.STATUS_INDICATOR_CORNER_RADIUS # Use config
        )
        # Use config padding
        self.connection_indicator.grid(row=0, column=0, sticky="e", padx=(config.ELEMENT_PADDING_X * 2, config.ELEMENT_PADDING_X), pady=config.ELEMENT_PADDING_Y)
        self.connection_indicator.grid_remove()  # Hide by default

        # API Limit status indicator
        self.api_limit_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('api_limit_reached', config.LANGUAGE), # Need to add this translation
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.STATUS_INDICATOR_FONT_SIZE), # Use config
            fg_color=config.API_LIMIT_COLOR,  # Use config
            text_color=config.STATUS_TEXT_COLOR,  # Use config
            corner_radius=config.STATUS_INDICATOR_CORNER_RADIUS # Use config
        )
        # Use config padding
        self.api_limit_indicator.grid(row=0, column=1, sticky="e", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)
        self.api_limit_indicator.grid_remove() # Hide by default

        # --- Time Display (Left 2/3) ---
        # Place time label directly in top_frame
        self.time_label = ctk.CTkLabel(
            self.top_frame, # Parent is now top_frame
            text="00:00", # Format changed
            # Use config font sizes
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.TIME_FONT_SIZE_BASE + config.TIME_FONT_SIZE_INCREASE, weight="bold")
        )
        # Center the label widget itself within the grid cell (0,0) - Use config padding
        self.time_label.grid(row=0, column=0, sticky="", padx=(config.SECTION_PADDING_X, config.ELEMENT_PADDING_X), pady=config.SECTION_PADDING_Y)

        # --- Date Display Frame (Right 1/3) ---
        # Keep this frame for vertical stacking of date components
        self.date_display_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        # Make frame fill vertically in its cell - Use config padding
        self.date_display_frame.grid(row=0, column=1, sticky="ns", padx=(config.ELEMENT_PADDING_X, config.SECTION_PADDING_X), pady=config.SECTION_PADDING_Y)
        self.date_display_frame.grid_columnconfigure(0, weight=1)
        # Configure rows for vertical stacking and centering
        self.date_display_frame.grid_rowconfigure(0, weight=1) # Weekday
        self.date_display_frame.grid_rowconfigure(1, weight=2) # Day (larger)
        self.date_display_frame.grid_rowconfigure(2, weight=1) # Month Year

        # Weekday Label
        self.weekday_label = ctk.CTkLabel(
            self.date_display_frame,
            text="Weekday",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.DATE_FONT_SIZE_BASE) # Use config
        )
        self.weekday_label.grid(row=0, column=0, sticky="s", pady=(0, config.TEXT_PADDING_Y)) # Use config padding

        # Day Label (Large)
        self.day_label = ctk.CTkLabel(
            self.date_display_frame,
            text="00",
            # Use config font sizes
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.DATE_FONT_SIZE_BASE + config.DATE_DAY_FONT_SIZE_INCREASE, weight="bold")
        )
        self.day_label.grid(row=1, column=0, sticky="", pady=0) # Centered

        # Month Year Label
        self.month_year_label = ctk.CTkLabel(
            self.date_display_frame,
            text="Month 0000",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.DATE_FONT_SIZE_BASE) # Use config
        )
        self.month_year_label.grid(row=2, column=0, sticky="n", pady=(config.TEXT_PADDING_Y, 0)) # Use config padding

        # --- Current Weather Frame (Below Time/Date) ---
        self.current_weather_frame = ctk.CTkFrame(self.top_frame)
        # Place in row 1, spanning both columns - Use config padding
        self.current_weather_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=config.SECTION_PADDING_X, pady=config.SECTION_PADDING_Y)

        # Configure current weather frame grid
        self.current_weather_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.current_weather_frame.grid_rowconfigure(0, weight=0)  # Title
        self.current_weather_frame.grid_rowconfigure(1, weight=1)  # Content
        
        # Current weather title
        self.current_weather_title = ctk.CTkLabel(
            self.current_weather_frame,
            text=get_translation('current_weather', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold") # Use config
        )
        # Use config padding
        self.current_weather_title.grid(row=0, column=0, columnspan=3, sticky="ew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        # Temperature frame
        self.temp_frame = ctk.CTkFrame(self.current_weather_frame)
        # Use config padding
        self.temp_frame.grid(row=1, column=0, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        self.temp_frame.grid_rowconfigure(0, weight=0)  # Title
        self.temp_frame.grid_rowconfigure(1, weight=1)  # Value
        
        self.temp_title = ctk.CTkLabel(
            self.temp_frame,
            text=get_translation('temperature', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold") # Use config
        )
        # Use config padding
        self.temp_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)

        self.temp_value = ctk.CTkLabel(
            self.temp_frame,
            text="--°C",
            # Use config font size (adjust if needed, maybe WEATHER_FONT_SIZE + 10?)
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE + 10, weight="bold")
        )
        # Use config padding
        self.temp_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        # Humidity frame
        self.humidity_frame = ctk.CTkFrame(self.current_weather_frame)
        # Use config padding
        self.humidity_frame.grid(row=1, column=1, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        self.humidity_frame.grid_rowconfigure(0, weight=0)  # Title
        self.humidity_frame.grid_rowconfigure(1, weight=1)  # Value
        
        self.humidity_title = ctk.CTkLabel(
            self.humidity_frame,
            text=get_translation('humidity', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold") # Use config
        )
        # Use config padding
        self.humidity_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)

        self.humidity_value = ctk.CTkLabel(
            self.humidity_frame,
            text="--%",
            # Use config font size (adjust if needed)
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE + 10, weight="bold")
        )
        # Use config padding
        self.humidity_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        # Air Quality frame
        self.air_quality_frame = ctk.CTkFrame(self.current_weather_frame)
        # Use config padding
        self.air_quality_frame.grid(row=1, column=2, sticky="nsew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        self.air_quality_frame.grid_rowconfigure(0, weight=0)  # Title
        self.air_quality_frame.grid_rowconfigure(1, weight=1)  # Value
        
        self.air_quality_title = ctk.CTkLabel(
            self.air_quality_frame,
            text=get_translation('air_quality', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold") # Use config
        )
        # Use config padding
        self.air_quality_title.grid(row=0, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)

        self.air_quality_value = ctk.CTkLabel(
            self.air_quality_frame,
            text="--",
            # Use config font size (adjust if needed)
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE + 10, weight="bold")
        )
        # Use config padding
        self.air_quality_value.grid(row=1, column=0, sticky="n", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

        # Forecast frames
        self.forecast_frames = []
        for i in range(3):
            forecast_frame = ctk.CTkFrame(self.bottom_frame)
            # Use config padding
            forecast_frame.grid(row=0, column=i, sticky="nsew", padx=config.SECTION_PADDING_X, pady=config.SECTION_PADDING_Y)

            forecast_frame.grid_rowconfigure(0, weight=0)  # Day
            forecast_frame.grid_rowconfigure(1, weight=1)  # Icon
            forecast_frame.grid_rowconfigure(2, weight=0)  # Condition
            forecast_frame.grid_rowconfigure(3, weight=0)  # Temp
            
            day_label = ctk.CTkLabel(
                forecast_frame,
                text=f"{get_translation('day', config.LANGUAGE)} {i+1}",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE, weight="bold") # Use config
            )
            # Use config padding
            day_label.grid(row=0, column=0, sticky="ew", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

            # Placeholder for weather icon
            icon_label = ctk.CTkLabel(forecast_frame, text="")
            # Removed sticky="nsew" to prevent image distortion - Use config padding
            icon_label.grid(row=1, column=0, sticky="", padx=config.ELEMENT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

            condition_label = ctk.CTkLabel(
                forecast_frame,
                text="--",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE) # Use config
            )
            # Use config padding
            condition_label.grid(row=2, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.TEXT_PADDING_Y)

            temp_label = ctk.CTkLabel(
                forecast_frame,
                text="--°C / --°C",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE) # Use config
            )
            # Use config padding
            temp_label.grid(row=3, column=0, sticky="ew", padx=config.TEXT_PADDING_X, pady=config.ELEMENT_PADDING_Y)

            self.forecast_frames.append({
                'frame': forecast_frame,
                'day': day_label,
                'icon': icon_label,
                'condition': condition_label,
                'temp': temp_label
            })
    
    def update_time(self, time_str):
        """
        Update the time display.
        
        Args:
            time_str (str): Time string in HH:MM:SS format
        """
        # Format time to HH:MM
        time_parts = time_str.split(':')
        if len(time_parts) >= 2:
            formatted_time = f"{time_parts[0]}:{time_parts[1]}"
            self.time_label.configure(text=formatted_time)
        else:
            self.time_label.configure(text=time_str) # Fallback

    def update_date(self, date_str):
        """
        Update the multi-part date display.

        Args:
            date_str (str): Date string (e.g., "Sunday, 04 May 2025")
                            Assumes the format includes Weekday, Day, Month, Year.
        """
        try:
            # Attempt to parse the date string to extract components reliably
            # Example parsing assuming format like "Weekday, DD Month YYYY"
            # This might need adjustment based on the actual format from main.py
            # Using strptime requires knowing the exact format including locale.
            # A simpler string split might be more robust if the format is consistent.

            parts = date_str.split(', ') # -> ["Sunday", "04 May 2025"]
            if len(parts) == 2:
                weekday = parts[0]
                date_parts = parts[1].split(' ') # -> ["04", "May", "2025"]
                if len(date_parts) == 3:
                    day = date_parts[0].lstrip('0') # Remove leading zero if present
                    month = date_parts[1]
                    year = date_parts[2]

                    self.weekday_label.configure(text=weekday)
                    self.day_label.configure(text=day)
                    self.month_year_label.configure(text=f"{month} {year}")
                    return # Success

            # Fallback if parsing fails - display the raw string in weekday label
            logger.warning(f"Could not parse date string: '{date_str}'. Displaying raw.")
            self.weekday_label.configure(text=date_str)
            self.day_label.configure(text="")
            self.month_year_label.configure(text="")

        except Exception as e:
            logger.error(f"Error updating date display for '{date_str}': {e}")
            # Display fallback text on error
            self.weekday_label.configure(text=get_translation('not_available', config.LANGUAGE))
            self.day_label.configure(text="")
            self.month_year_label.configure(text="")


    def update_current_weather(self, weather_data):
        """
        Update the current weather display.
        
        Args:
            weather_data (dict): Current weather data dictionary from AccuWeatherClient.
                                 Expected keys: 'temperature', 'humidity', 'air_quality_category',
                                 Expected structure: {'data': dict, 'connection_status': bool, 'api_status': str}.
                                 The 'data' dict expects: 'temperature', 'humidity', 'air_quality_category',
                                 'air_quality_index' (optional).
        """
        # Update status indicators first
        connection_status = weather_data.get('connection_status', False)
        api_status = weather_data.get('api_status', 'error')
        self.update_status_indicators(connection_status, api_status)

        # Extract the actual weather data
        current_data = weather_data.get('data', {})

        # Update temperature
        if 'temperature' in current_data and current_data['temperature'] is not None:
            self.temp_value.configure(text=f"{int(round(current_data['temperature']))}°C")
        else:
            self.temp_value.configure(text=get_translation('not_available', config.LANGUAGE))

        # Update humidity
        if 'humidity' in current_data and current_data['humidity'] is not None:
            self.humidity_value.configure(text=f"{current_data['humidity']}%")
        else:
            self.humidity_value.configure(text=get_translation('not_available', config.LANGUAGE))

        # Update air quality using the new category field and translation function
        if 'air_quality_category' in current_data and current_data['air_quality_category'] is not None:
            # Translate the AQI category (e.g., "Good", "Moderate")
            translated_aqi = translate_aqi_category(current_data['air_quality_category'], config.LANGUAGE)
            # Optionally include the index value if available
            aqi_index = current_data.get('air_quality_index')
            display_text = translated_aqi
            if aqi_index is not None:
                 display_text = f"{translated_aqi} ({aqi_index})" # e.g., "Good (25)"
            self.air_quality_value.configure(text=display_text)
        else:
            # Display N/A if air quality data is not available
            self.air_quality_value.configure(text=get_translation('not_available', config.LANGUAGE))

        # Removed unused icon logic for current weather display

    def update_forecast(self, forecast_result):
        """
        Update the forecast display.

        Args:
            forecast_result (dict): Forecast result dictionary from AccuWeatherClient.
                                    Expected structure: {'data': list[dict], 'connection_status': bool, 'api_status': str}.
                                    Each dict in the 'data' list expects: 'date', 'icon_path',
                                    'condition', 'max_temp', 'min_temp'.
        """
        # Update status indicators first
        connection_status = forecast_result.get('connection_status', False)
        api_status = forecast_result.get('api_status', 'error')
        self.update_status_indicators(connection_status, api_status)

        # Extract the actual forecast data list
        forecast_days = forecast_result.get('data', [])

        # Update forecast frames
        for i, day_data in enumerate(forecast_days):
            if i >= len(self.forecast_frames):
                break
            
            frame_info = self.forecast_frames[i]
            frame_widget = frame_info['frame']
            frame_widget.grid() # Make sure the frame is visible

            # Update day
            if 'date' in day_data:
                from ..utils.helpers import get_day_name
                # AccuWeather date format is like '2025-04-05T07:00:00+03:00'
                # Extract just the date part for get_day_name
                date_part = day_data['date'].split('T')[0]
                day_name = get_day_name(date_part)
                frame_info['day'].configure(text=day_name)

            # Update icon using the WeatherIconHandler and icon_code
            if 'icon_code' in day_data and day_data['icon_code'] is not None:
                # Use config icon size
                icon_image = self.icon_handler.load_icon(day_data['icon_code'], size=config.FORECAST_ICON_SIZE)
                if icon_image:
                    frame_info['icon'].configure(image=icon_image, text="") # Clear text if image loads
                    # Keep a reference to prevent garbage collection
                    frame_info['icon'].image = icon_image
                else:
                    # Clear image if loading fails (handler logs error)
                    frame_info['icon'].configure(image=None, text=get_translation('icon_missing', config.LANGUAGE))
            else:
                 # Clear image if icon code is missing or None
                 frame_info['icon'].configure(image=None, text=get_translation('icon_missing', config.LANGUAGE))


            # Update condition
            if 'condition' in day_data and day_data['condition'] is not None:
                translated_condition = translate_weather_condition(day_data['condition'], config.LANGUAGE)
                frame_info['condition'].configure(text=translated_condition)
            else:
                frame_info['condition'].configure(text=get_translation('not_available', config.LANGUAGE))


            # Update temperature
            if 'max_temp' in day_data and day_data['max_temp'] is not None and \
               'min_temp' in day_data and day_data['min_temp'] is not None:
                max_temp = int(round(day_data['max_temp']))
                min_temp = int(round(day_data['min_temp']))
                frame_info['temp'].configure(text=f"{max_temp}°C / {min_temp}°C")
            else:
                frame_info['temp'].configure(text=get_translation('not_available', config.LANGUAGE))


        # Hide unused forecast frames if fewer than 3 days are received
        for i in range(len(forecast_days), len(self.forecast_frames)):
             self.forecast_frames[i]['frame'].grid_remove()


    def update_status_indicators(self, connection_status, api_status):
        """
        Update the connection and API limit status indicators.

        Args:
            connection_status (bool): True if internet connection is available.
            api_status (str): Status from the API client ('ok', 'limit_reached', 'error', 'offline', 'mock').
        """
        # Handle connection indicator
        if not connection_status:
            self.connection_indicator.grid()
            self.connection_indicator.lift()
            logger.warning("No internet connection detected")
        else:
            self.connection_indicator.grid_remove()

        # Handle API limit indicator (only show if connected)
        if connection_status and api_status == 'limit_reached':
            self.api_limit_indicator.grid()
            self.api_limit_indicator.lift()
            logger.warning("API request limit reached")
        else:
            self.api_limit_indicator.grid_remove()

    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode."""
        try:
            # Disable all fullscreen methods
            self.attributes("-fullscreen", False)
            self.overrideredirect(False)
            self.state('normal')
            self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
            logger.info("Exited fullscreen mode")
        except Exception as e:
            logger.error(f"Error exiting fullscreen mode: {e}")
