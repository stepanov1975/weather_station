"""CustomTkinter split-board display for the clock, IMS readings and forecast."""

import logging
import tkinter as tk
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
from pathlib import Path

from PIL import Image

import customtkinter as ctk

# Local application imports
# Use 'config' directly for accessing settings
from .. import config
from ..utils.localization import (
    get_translation,
    translate_weather_condition,
)
from ..utils.icon_handler import WeatherIconHandler
from ..utils.helpers import get_day_name

logger = logging.getLogger(__name__)

# --- Global UI Setup (Theme and Appearance) ---
# Set appearance mode based on config *before* AppWindow instantiation
ctk.set_appearance_mode("dark" if config.DARK_MODE else "light")


class AppWindow(ctk.CTk):
    """Fullscreen weather board with a clock, local observations and three forecast rows."""

    def __init__(self):
        """Initializes the AppWindow, setting up layout and widgets based on config."""
        super().__init__()
        logger.info("Initializing AppWindow...")

        self.title(get_translation('app_title', config.LANGUAGE))
        self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
        self.configure(fg_color=self._get_color("background")) # Set main window background

        self._fonts: dict[str, ctk.CTkFont] = {}
        self.icon_handler = WeatherIconHandler()
        logger.debug("WeatherIconHandler initialized.")

        self._configure_fullscreen()
        self._setup_layout()
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
        if font_key in self._fonts:
            return self._fonts[font_key]
        font_config = config.FONTS.get(font_key)
        if not font_config:
            logger.warning(f"Font key '{font_key}' not found in config. Using default.")
            # Fallback to a default font if key is missing
            return ctk.CTkFont(family=config.DEFAULT_FONT_FAMILY, size=12, weight="normal")

        family, size, weight = font_config
        self._fonts[font_key] = ctk.CTkFont(
            family=family or config.DEFAULT_FONT_FAMILY, # Use default if None
            size=size,
            weight=weight
        )
        return self._fonts[font_key]

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
        """Lay out the board in proportions of the active kiosk window."""
        mast = ctk.CTkFrame(self, fg_color="transparent")
        mast.place(relx=.034, rely=.013, relwidth=.932, relheight=.073)
        station = config.IMS_STATION_NAME
        if station == "Hadera Port" and config.LANGUAGE == "ru":
            station = "Хадера · Порт"
        self._label(mast, station.upper(), "station").place(relx=0, rely=.58, anchor="w")
        with Image.open(Path(__file__).resolve().parents[1] / "assets/interference_waves.png") as image:
            self.wave_image = ctk.CTkImage(light_image=image.copy(), size=(446, 56))
        ctk.CTkLabel(mast, text="", image=self.wave_image).place(relx=1, rely=.5, anchor="e")

        for y in (.091, .515):
            self._rule(self).place(relx=.034, rely=y, relwidth=.932)
        self.time_date_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.time_date_frame.place(relx=.034, rely=.10, relwidth=.932, relheight=.405)
        self.time_label = self._label(self.time_date_frame, "00:00", "time", "accent")
        self.time_label.place(relx=0, rely=.5, anchor="w")
        self._rule(self.time_date_frame).place(relx=.525, rely=.10, relheight=.8)
        date_frame = ctk.CTkFrame(self.time_date_frame, fg_color="transparent")
        date_frame.place(relx=.555, rely=.5, anchor="w")
        self.weekday_label = self._label(date_frame, "", "weekday")
        self.day_label = self._label(date_frame, "", "day_number")
        self.month_year_label = self._label(date_frame, "", "month_year", "text_secondary")
        for label in (self.weekday_label, self.day_label, self.month_year_label):
            label.pack(anchor="w")

        self.current_conditions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.current_conditions_frame.place(relx=.034, rely=.728, relwidth=.399, anchor="w")
        self.temp_title, self.temp_value = self._reading("temperature", "temp", "--°C", 0)
        self.humidity_title = self.humidity_value = None
        if config.OPTIONAL_ELEMENTS.get("show_current_humidity", True):
            self.humidity_title, self.humidity_value = self._reading("humidity", "humidity", "--%", 1)

        self.forecast_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.forecast_frame.place(relx=.452, rely=.728, relwidth=.514, anchor="w")
        self.forecast_frame.grid_columnconfigure(0, weight=1)
        self._create_forecast_region()

        self.status_bar_frame = None
        if config.OPTIONAL_ELEMENTS.get("show_status_bar", True):
            self.status_bar_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.status_bar_frame.place(relx=.034, rely=.975, relwidth=.932, anchor="sw")
            self.status_bar_frame.grid_columnconfigure(0, weight=1)
            pending = get_translation("status_pending", config.LANGUAGE)
            self.network_status_label = self._label(self.status_bar_frame, pending, "status_indicator")
            self.network_status_label.grid(row=0, column=0, sticky="w")
            self.api_status_label = self._label(self.status_bar_frame, pending, "status_indicator")
            self.api_status_label.grid(row=0, column=1, sticky="e")

    def _label(self, parent, text, font, color="text"):
        return ctk.CTkLabel(parent, text=text, font=self._get_font(font), height=1, width=1,
                            text_color=self._get_color(color), anchor="w", justify="left")

    def _rule(self, parent):
        # A native frame preserves a one-pixel rule at kiosk scaling.
        return tk.Frame(parent, width=1, height=1, borderwidth=0, highlightthickness=0,
                        background=self._get_color("divider"))

    def _reading(self, key, font_prefix, initial_value, column):
        parent = self.current_conditions_frame
        title = self._label(parent, get_translation(key, config.LANGUAGE),
                            f"current_{font_prefix}_title", "text_secondary")
        title.grid(row=0, column=column, sticky="sw", padx=(0, 12))
        value = self._label(parent, initial_value, f"current_{font_prefix}_value")
        value.grid(row=1, column=column, sticky="nw", padx=(0, 12))
        parent.grid_columnconfigure(column, weight=1)
        return title, value

    def _create_forecast_region(self):
        self._forecast_icon_size = config.FORECAST_ICON_SIZE
        self.forecast_day_frames: List[Dict[str, Any]] = []
        for index in range(3):
            row = ctk.CTkFrame(self.forecast_frame, fg_color="transparent")
            row.grid(row=index, column=0, sticky="nsew")
            row.grid_columnconfigure(1, weight=1)
            row.grid_rowconfigure((1, 2), weight=1)
            self._rule(row).grid(row=0, column=0, columnspan=3, sticky="ew")
            day = self._label(row, "", "forecast_day")
            day.grid(row=1, column=1, sticky="sw")
            icon = self._label(row, "", "forecast_day")
            icon.grid(row=1, column=0, rowspan=2, padx=(0, 5))
            condition = self._label(row, "", "forecast_condition", "text_secondary")
            condition.grid(row=2, column=1, sticky="nw")
            temp = self._label(row, "", "forecast_temp")
            temp.grid(row=1, column=2, rowspan=2, sticky="e")
            self.forecast_day_frames.append(dict(frame=row, day=day, icon=icon,
                                                 condition=condition, temp=temp))

    def _setup_bindings(self):
        """Sets up keyboard bindings."""
        logger.debug("Setting up keyboard bindings...")
        self.bind("<Configure>", self._resize_content, add="+")
        self.bind("<Escape>", self.exit_fullscreen)
        logger.debug("'<Escape>' key bound to exit_fullscreen.")

    def _resize_content(self, event):
        if event.widget is not self:
            return
        scale = min(event.width / 1440, event.height / 810)
        for key, font in self._fonts.items():
            size = max(1, round(config.FONTS[key][1] * scale))
            if size != font.cget("size"):
                font.configure(size=size)
        wave_size = (max(1, round(446 * scale)), max(1, round(56 * scale)))
        if self.wave_image.cget("size") != wave_size:
            self.wave_image.configure(size=wave_size)
        icon_width, icon_height = config.FORECAST_ICON_SIZE
        size = (max(1, round(icon_width * scale)), max(1, round(icon_height * scale)))
        if size != self._forecast_icon_size:
            self._forecast_icon_size = size
            self.icon_handler.icon_cache.clear()
            for card in self.forecast_day_frames:
                if card.get("icon_code") is not None:
                    self._set_forecast_icon(card, card["icon_code"])
        for index, card in enumerate(self.forecast_day_frames):
            self.forecast_frame.grid_rowconfigure(index, minsize=max(1, round(90 * scale)))
            card["condition"].configure(wraplength=max(1, int(event.width * .29)))
        for title in (self.temp_title, self.humidity_title):
            if title:
                title.configure(wraplength=max(1, int(event.width * .17)))

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
        """Updates the weekday, large day and month, and year."""
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
                    if config.LANGUAGE == "ru":
                        month = month.lower()
                    self.day_label.configure(text=f"{day} {month}")
                    self.month_year_label.configure(text=year)
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
             return

        na_text = get_translation('not_available', config.LANGUAGE)

        stale_fields = weather_result.get("stale_fields", current_data if weather_result.get("stale") else ())
        for key, title in (("temperature", self.temp_title), ("humidity", self.humidity_title)):
            if title:
                text = get_translation(key, config.LANGUAGE)
                if key in stale_fields:
                    text += f" ({get_translation('stale_reading', config.LANGUAGE)})"
                title.configure(text=text)

        # Update Temperature (Always shown)
        temp = current_data.get('temperature')
        temp_text = f"{int(round(temp))}°C" if temp is not None else na_text
        if self.temp_value:
            self.temp_value.configure(text=temp_text)
        logger.debug(f"Temperature updated to: {temp_text}")

        # Update Humidity (If shown)
        if self.humidity_value:
            humidity = current_data.get('humidity')
            humidity_text = f"{humidity}%" if humidity is not None else na_text
            self.humidity_value.configure(text=humidity_text)
            logger.debug(f"Humidity updated to: {humidity_text}")

    def _set_forecast_icon(self, card, code):
        card["icon_code"] = code
        image = self.icon_handler.load_icon(code, self._forecast_icon_size) if code is not None else None
        if image:
            card["icon"].configure(image=image, text="")
            card["icon"].grid()
        else:
            card["icon"].grid_remove()

    def update_forecast(self, forecast_result: Dict[str, Any]):
        """
        Updates the multi-day forecast display section.

        Note: This method does NOT update the main status indicators itself.
        The controller records each service's API status, combines the statuses,
        and centrally schedules publication through `update_status_indicators`.
        """
        logger.debug(f"Updating forecast display. API Status: {forecast_result.get('api_status')}")
        # We don't update the main status bar from here, as it's handled centrally

        forecast_data: List[Dict[str, Any]] = forecast_result.get('data', [])
        na_text = get_translation('not_available', config.LANGUAGE)

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
                self._set_forecast_icon(day_widgets, icon_code)

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
                self._set_forecast_icon(day_widgets, None)
                day_widgets['condition'].configure(text="")
                day_widgets['temp'].configure(text="")

    def update_status_indicators(self, connection_status: bool, api_status: Optional[str], last_success_time: Optional[float]):
        """
        Updates the persistent status indicator labels for network and API status.

        Args:
            connection_status (bool): The current internet connection status.
            api_status (Optional[str]): The status of the last relevant API call
                                        ('ok', 'error', 'mock', 'offline', None).
                                        None might indicate an initial state or IMS-only update.
            last_success_time (Optional[float]): The timestamp (time.time()) of the
                                                 last successful forecast API call.
                                                 None if no successful call yet or if the
                                                 update is only for IMS.
        """
        # Only proceed if status bar is enabled and widgets exist
        if not self.status_bar_frame or not self.network_status_label or not self.api_status_label:
            return

        logger.debug(f"Updating status indicators: Connection={connection_status}, API Status='{api_status}', Last Success Time={last_success_time}")

        # --- Update Network Status Label ---
        network_label = get_translation('network_status', config.LANGUAGE)
        api_label = get_translation('api_status', config.LANGUAGE)
        ok_text = get_translation('status_ok', config.LANGUAGE)
        offline_text = get_translation('status_offline', config.LANGUAGE)
        error_text = get_translation('status_error', config.LANGUAGE)
        mock_text = get_translation('status_mock', config.LANGUAGE)
        pending_text = get_translation('status_pending', config.LANGUAGE)
        network_text = f"{network_label}: {ok_text if connection_status else offline_text}"
        network_color = self._get_color("status_ok_text") if connection_status else self._get_color("status_error_text")
        self.network_status_label.configure(text=network_text, text_color=network_color)

        # --- Update API Status Label ---
        api_text = f"{api_label}: {pending_text}"
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
            api_text = f"{api_label}: {ok_text}{time_suffix}"
            api_color = self._get_color("status_ok_text")
        elif api_status == 'error':
            api_text = f"{api_label}: {error_text} ({success_time_str})"
            api_color = self._get_color("status_error_text")
        elif api_status == 'mock':
            api_text = f"{api_label}: {mock_text}"
            api_color = self._get_color("status_text") # Neutral color
        elif api_status == 'offline':
             api_text = f"{api_label}: {offline_text} ({success_time_str})"
             api_color = self._get_color("status_error_text")
        elif api_status is None and last_success_time is None:
             api_text = f"{api_label}: {pending_text}"
             api_color = self._get_color("status_text")
        elif api_status is None and last_success_time is not None:
             api_text = f"{api_label}: {ok_text} ({success_time_str})"
             api_color = self._get_color("status_ok_text")
        else:
             # Catch any unexpected api_status values
             api_text = f"{api_label}: {api_status} ({success_time_str})"
             api_color = self._get_color("status_text")

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
