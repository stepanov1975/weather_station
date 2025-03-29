"""
Main application window for the Weather Display.
"""

import logging
import customtkinter as ctk
import os
from PIL import Image
from ..utils.localization import get_translation, translate_weather_condition
try:
    from PIL import ImageTk
except ImportError:
    # This should not happen when running the GUI, but we'll handle it gracefully
    ImageTk = None
    logging.error("ImageTk is not available. GUI will not work properly.")

from .. import config
from ..utils.helpers import load_image

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
        self.connection_indicator.grid(row=0, column=0, sticky="e", padx=10, pady=5)
        self.connection_indicator.grid_remove()  # Hide by default, will be shown when needed
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
            icon_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            
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
        Update the time display in the application window.
        
        Args:
            time_str (str): Time string in HH:MM:SS format to display
            
        Note:
            This method updates both the time and date labels in the top frame
            of the application window. The time is displayed in 24-hour format.
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
            weather_data (dict): Current weather data
        """
        # Check for connection status
        if 'connection_status' in weather_data:
            self.update_connection_status(weather_data['connection_status'])
        
        # Update temperature
        if 'temperature' in weather_data:
            self.temp_value.configure(text=f"{int(round(weather_data['temperature']))}°C")
        
        # Update humidity
        if 'humidity' in weather_data:
            self.humidity_value.configure(text=f"{weather_data['humidity']}%")
        
        # Update air quality
        if 'air_quality_text' in weather_data:
            # Translate air quality text
            translated_air_quality = translate_weather_condition(weather_data['air_quality_text'], config.LANGUAGE)
            self.air_quality_value.configure(text=translated_air_quality)
        
        # Update icon (if we add an icon to the current weather display in the future)
        if 'icon_url' in weather_data and weather_data['icon_url']:
            # Extract the day/night part and the actual filename for the icon
            url_parts = weather_data['icon_url'].split('/')
            if len(url_parts) >= 2 and (url_parts[-2] == 'day' or url_parts[-2] == 'night'):
                # Use format like "day_113.png" or "night_113.png"
                icon_filename = f"{url_parts[-2]}_{url_parts[-1]}"
            else:
                icon_filename = os.path.basename(weather_data['icon_url'])
    
    def update_forecast(self, forecast_data):
        """
        Update the forecast display.
        
        Args:
            forecast_data (dict or list): Forecast data with connection status
        """
        # Check for connection status
        if isinstance(forecast_data, dict) and 'connection_status' in forecast_data:
            self.update_connection_status(forecast_data['connection_status'])
            # Extract the actual forecast data
            if 'forecast' in forecast_data:
                forecast_days = forecast_data['forecast']
            else:
                # If no forecast data is available, return
                return
        else:
            # For backward compatibility, assume it's just a list of forecast days
            forecast_days = forecast_data
        
        # Update forecast frames
        for i, day_data in enumerate(forecast_days):
            if i >= len(self.forecast_frames):
                break
            
            frame = self.forecast_frames[i]
            
            # Update day
            if 'date' in day_data:
                from ..utils.helpers import get_day_name
                day_name = get_day_name(day_data['date'])
                frame['day'].configure(text=day_name)
            
            # Update icon
            if 'icon_url' in day_data and day_data['icon_url']:
                # Extract the day/night part and the actual filename for the icon
                url_parts = day_data['icon_url'].split('/')
                if len(url_parts) >= 2 and (url_parts[-2] == 'day' or url_parts[-2] == 'night'):
                    # Use format like "day_113.png" or "night_113.png"
                    icon_filename = f"{url_parts[-2]}_{url_parts[-1]}"
                else:
                    icon_filename = os.path.basename(day_data['icon_url'])
                
                icon_path = os.path.join('weather_display/assets/icons', icon_filename)
                if os.path.exists(icon_path):
                    icon_image = load_image(icon_path, size=(96, 96))  # Adjusted size for better display
                    if icon_image:
                        frame['icon'].configure(image=icon_image)
                        # Keep a reference to prevent garbage collection
                        frame['icon'].image = icon_image
            
            # Update condition
            if 'condition' in day_data:
                translated_condition = translate_weather_condition(day_data['condition'], config.LANGUAGE)
                frame['condition'].configure(text=translated_condition)
            
            # Update temperature
            if 'max_temp' in day_data and 'min_temp' in day_data:
                max_temp = int(round(day_data['max_temp']))
                min_temp = int(round(day_data['min_temp']))
                frame['temp'].configure(text=f"{max_temp}°C / {min_temp}°C")
    
    def update_connection_status(self, is_connected):
        """
        Update the connection status indicator.
        
        Args:
            is_connected (bool): True if internet connection is available, False otherwise
        """
        if is_connected:
            # Hide the indicator when connected
            self.connection_indicator.grid_remove()
        else:
            # Show the indicator when not connected
            self.connection_indicator.grid()
            # Make sure it's visible by bringing it to the front
            self.connection_indicator.lift()
            logger.warning("No internet connection detected")
    
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
