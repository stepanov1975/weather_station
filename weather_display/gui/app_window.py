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
        self.connection_frame = ctk.CTkFrame(self, corner_radius=0, height=30)
        self.connection_frame.grid(row=0, column=0, sticky="ew")
        self.connection_frame.grid_columnconfigure(0, weight=1)
        self.connection_frame.grid_propagate(False)  # Prevent frame from resizing to fit content
        
        self.top_frame = ctk.CTkFrame(self, corner_radius=0)
        self.top_frame.grid(row=1, column=0, sticky="nsew")
        
        self.bottom_frame = ctk.CTkFrame(self, corner_radius=0)
        self.bottom_frame.grid(row=2, column=0, sticky="nsew")
        
        # Configure frame grid layout
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_rowconfigure(0, weight=1)  # Time
        self.top_frame.grid_rowconfigure(1, weight=1)  # Date
        self.top_frame.grid_rowconfigure(2, weight=2)  # Current weather
        
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
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14),
            fg_color="#FF5555",  # Red background for no connection
            text_color="#FFFFFF",  # White text
            corner_radius=5
        )
        self.connection_indicator.grid(row=0, column=0, sticky="e", padx=(10, 5), pady=5)
        self.connection_indicator.grid_remove()  # Hide by default

        # API Limit status indicator
        self.api_limit_indicator = ctk.CTkLabel(
            self.connection_frame,
            text=get_translation('api_limit_reached', config.LANGUAGE), # Need to add this translation
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=14),
            fg_color="#FFA500",  # Orange background for API limit
            text_color="#FFFFFF",  # White text
            corner_radius=5
        )
        self.api_limit_indicator.grid(row=0, column=1, sticky="e", padx=(5, 10), pady=5)
        self.api_limit_indicator.grid_remove() # Hide by default

        # Time display
        self.time_label = ctk.CTkLabel(
            self.top_frame,
            text="00:00:00",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.TIME_FONT_SIZE, weight="bold")
        )
        self.time_label.grid(row=0, column=0, sticky="s", padx=20, pady=(20, 0))
        
        # Date display
        self.date_label = ctk.CTkLabel(
            self.top_frame,
            text="Day, 00 Month 0000",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.DATE_FONT_SIZE)
        )
        self.date_label.grid(row=1, column=0, sticky="n", padx=20, pady=(0, 20))
        
        # Current weather frame
        self.current_weather_frame = ctk.CTkFrame(self.top_frame)
        self.current_weather_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=20)
        
        # Configure current weather frame
        self.current_weather_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.current_weather_frame.grid_rowconfigure(0, weight=0)  # Title
        self.current_weather_frame.grid_rowconfigure(1, weight=1)  # Content
        
        # Current weather title
        self.current_weather_title = ctk.CTkLabel(
            self.current_weather_frame,
            text=get_translation('current_weather', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.current_weather_title.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        
        # Temperature frame
        self.temp_frame = ctk.CTkFrame(self.current_weather_frame)
        self.temp_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.temp_frame.grid_rowconfigure(0, weight=0)  # Title
        self.temp_frame.grid_rowconfigure(1, weight=1)  # Value
        
        self.temp_title = ctk.CTkLabel(
            self.temp_frame,
            text=get_translation('temperature', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.temp_title.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        self.temp_value = ctk.CTkLabel(
            self.temp_frame,
            text="--°C",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE+16, weight="bold")
        )
        self.temp_value.grid(row=1, column=0, sticky="n", padx=10, pady=10)
        
        # Humidity frame
        self.humidity_frame = ctk.CTkFrame(self.current_weather_frame)
        self.humidity_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        self.humidity_frame.grid_rowconfigure(0, weight=0)  # Title
        self.humidity_frame.grid_rowconfigure(1, weight=1)  # Value
        
        self.humidity_title = ctk.CTkLabel(
            self.humidity_frame,
            text=get_translation('humidity', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.humidity_title.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        self.humidity_value = ctk.CTkLabel(
            self.humidity_frame,
            text="--%",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE+16, weight="bold")
        )
        self.humidity_value.grid(row=1, column=0, sticky="n", padx=10, pady=10)
        
        # Air Quality frame
        self.air_quality_frame = ctk.CTkFrame(self.current_weather_frame)
        self.air_quality_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        
        self.air_quality_frame.grid_rowconfigure(0, weight=0)  # Title
        self.air_quality_frame.grid_rowconfigure(1, weight=1)  # Value
        
        self.air_quality_title = ctk.CTkLabel(
            self.air_quality_frame,
            text=get_translation('air_quality', config.LANGUAGE),
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE, weight="bold")
        )
        self.air_quality_title.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        self.air_quality_value = ctk.CTkLabel(
            self.air_quality_frame,
            text="--",
            font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.WEATHER_FONT_SIZE+16, weight="bold")
        )
        self.air_quality_value.grid(row=1, column=0, sticky="n", padx=10, pady=10)
        
        # Forecast frames
        self.forecast_frames = []
        for i in range(3):
            forecast_frame = ctk.CTkFrame(self.bottom_frame)
            forecast_frame.grid(row=0, column=i, sticky="nsew", padx=20, pady=20)
            
            forecast_frame.grid_rowconfigure(0, weight=0)  # Day
            forecast_frame.grid_rowconfigure(1, weight=1)  # Icon
            forecast_frame.grid_rowconfigure(2, weight=0)  # Condition
            forecast_frame.grid_rowconfigure(3, weight=0)  # Temp
            
            day_label = ctk.CTkLabel(
                forecast_frame,
                text=f"{get_translation('day', config.LANGUAGE)} {i+1}",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE, weight="bold")
            )
            day_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            # Placeholder for weather icon
            icon_label = ctk.CTkLabel(forecast_frame, text="")
            # Removed sticky="nsew" to prevent image distortion
            icon_label.grid(row=1, column=0, sticky="", padx=10, pady=10)

            condition_label = ctk.CTkLabel(
                forecast_frame,
                text="--",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE)
            )
            condition_label.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
            
            temp_label = ctk.CTkLabel(
                forecast_frame,
                text="--°C / --°C",
                font=ctk.CTkFont(family=config.FONT_FAMILY, size=config.FORECAST_FONT_SIZE)
            )
            temp_label.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
            
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
        self.time_label.configure(text=time_str)
    
    def update_date(self, date_str):
        """
        Update the date display.
        
        Args:
            date_str (str): Date string
        """
        self.date_label.configure(text=date_str)
    
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
                icon_image = self.icon_handler.load_icon(day_data['icon_code'], size=(96, 96))
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
