#!/usr/bin/env python3
"""
Weather Icons Demonstration Script using CustomTkinter.

This script creates a graphical window displaying all available weather icons
managed by the `WeatherIconHandler`, categorized into Day and Night sections.
It helps visualize the icons and verify their appearance.
"""

# Standard library imports
import os
import sys
import logging
from typing import Tuple

# Third-party imports
import customtkinter as ctk
from PIL import Image # Required by CTkImage, even if not used directly here

# Local application imports
try:
    # Assumes script is run from project root or package is installed
    from weather_display.utils.icon_handler import WeatherIconHandler
except ImportError:
    print("Error: Unable to import WeatherIconHandler.")
    print("Please run this script from the project root directory or ensure the package is installed.")
    # Attempt path adjustment as a fallback
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from weather_display.utils.icon_handler import WeatherIconHandler
    except ImportError:
         print("Path adjustment failed. Exiting.")
         sys.exit(1)


# --- Constants ---
WINDOW_TITLE = "Weather Icons Demo"
WINDOW_GEOMETRY = "900x700" # Adjusted size for better fit
MAX_COLS = 5 # Number of columns in the icon grid
ICON_SIZE: Tuple[int, int] = (64, 64) # Display size for icons
PAD_X = 10 # Horizontal padding
PAD_Y = 10 # Vertical padding

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeatherIconsDemo(ctk.CTk):
    """
    CustomTkinter application window for demonstrating weather icons.

    Displays icons in a scrollable grid, separated into Day and Night categories.
    """

    def __init__(self):
        """Initialize the demo application window and widgets."""
        super().__init__()

        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_GEOMETRY)

        # Create the icon handler instance
        try:
            self.icon_handler = WeatherIconHandler()
        except Exception as e:
            logger.critical(f"Failed to initialize WeatherIconHandler: {e}", exc_info=True)
            # Optionally display an error message in the GUI
            error_label = ctk.CTkLabel(self, text=f"Error initializing Icon Handler:\n{e}", text_color="red")
            error_label.pack(pady=20, padx=20)
            return # Stop initialization if handler fails

        # Create the main UI structure
        self._create_widgets()

    def _create_widgets(self):
        """Create the main UI elements: title and scrollable icon grid."""
        # --- Title ---
        title_label = ctk.CTkLabel(
            self,
            text="AccuWeather Icon Set Demonstration",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=PAD_Y)

        # --- Scrollable Frame for Icons ---
        scroll_frame = ctk.CTkScrollableFrame(self) # Let it determine size
        scroll_frame.pack(pady=PAD_Y, padx=PAD_X, fill="both", expand=True)

        # --- Populate Icon Grid ---
        self._populate_icon_grid(scroll_frame)

    def _populate_icon_grid(self, parent_frame: ctk.CTkFrame):
        """Create and arrange the icon widgets within the parent frame."""
        row, col = 0, 0

        # Separate icon codes into day (1-32) and night (33-44) based on AccuWeather standard
        day_icons = sorted([code for code in self.icon_handler.ICON_MAPPING if 1 <= code <= 32])
        night_icons = sorted([code for code in self.icon_handler.ICON_MAPPING if 33 <= code <= 44])

        # --- Day Icons Section ---
        day_section_label = ctk.CTkLabel(
            parent_frame,
            text="Day Icons (Codes 1-32)",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w" # Align left
        )
        day_section_label.grid(row=row, column=0, columnspan=MAX_COLS, sticky="ew", pady=(PAD_Y, 5), padx=PAD_X)
        row += 1
        col = 0

        for icon_code in day_icons:
            self._create_icon_widget(parent_frame, icon_code, row, col)
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

        # --- Night Icons Section ---
        # Ensure night section starts on a new row
        if col != 0:
            row += 1
            col = 0

        night_section_label = ctk.CTkLabel(
            parent_frame,
            text="Night Icons (Codes 33-44)",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w" # Align left
        )
        night_section_label.grid(row=row, column=0, columnspan=MAX_COLS, sticky="ew", pady=(PAD_Y * 2, 5), padx=PAD_X)
        row += 1
        col = 0

        for icon_code in night_icons:
            self._create_icon_widget(parent_frame, icon_code, row, col)
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

    def _create_icon_widget(self, parent: ctk.CTkFrame, icon_code: int, grid_row: int, grid_col: int):
        """
        Create a single widget containing an icon, its code, and description.

        Args:
            parent: The parent frame (the scrollable frame).
            icon_code: The AccuWeather icon code to display.
            grid_row: The grid row position for this widget.
            grid_col: The grid column position for this widget.
        """
        try:
            icon_info = self.icon_handler.ICON_MAPPING[icon_code]
        except KeyError:
            logger.error(f"Icon code {icon_code} not found in ICON_MAPPING.")
            # Optionally display an error placeholder in the grid
            error_frame = ctk.CTkFrame(parent, border_color="red", border_width=1)
            error_frame.grid(row=grid_row, column=grid_col, padx=PAD_X, pady=PAD_Y, sticky="nsew")
            error_label = ctk.CTkLabel(error_frame, text=f"Error:\nCode {icon_code}\nnot found", text_color="red")
            error_label.pack(padx=5, pady=5)
            return

        # Create a frame for this icon entry
        icon_widget_frame = ctk.CTkFrame(parent)
        icon_widget_frame.grid(row=grid_row, column=grid_col, padx=PAD_X, pady=PAD_Y, sticky="nsew")
        icon_widget_frame.grid_columnconfigure(0, weight=1) # Allow labels to center/wrap

        # Load the icon image
        icon_image = self.icon_handler.load_icon(icon_code, size=ICON_SIZE)

        # Display Icon (or placeholder)
        if icon_image:
            icon_label = ctk.CTkLabel(icon_widget_frame, image=icon_image, text="")
            icon_label.pack(pady=(PAD_Y // 2, 0)) # Add some top padding
        else:
            # Placeholder if icon loading failed (handler should log error)
            icon_label = ctk.CTkLabel(icon_widget_frame, text="[No Icon]", width=ICON_SIZE[0], height=ICON_SIZE[1])
            icon_label.pack(pady=(PAD_Y // 2, 0))

        # Display Icon Code
        code_label = ctk.CTkLabel(icon_widget_frame, text=f"Code: {icon_code}", font=ctk.CTkFont(size=10))
        code_label.pack(pady=2)

        # Display Icon Description
        desc_label = ctk.CTkLabel(
            icon_widget_frame,
            text=icon_info.get("description", "N/A"),
            font=ctk.CTkFont(size=12),
            wraplength=parent.winfo_width() // MAX_COLS - (PAD_X * 2) # Estimate wrap length
        )
        desc_label.pack(padx=5, pady=(0, PAD_Y // 2))


def main():
    """Set up theme and run the Weather Icons Demo application."""
    # Set theme (optional, can be controlled by system/user settings too)
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    logger.info("Starting Weather Icons Demo...")
    app = WeatherIconsDemo()
    app.mainloop()
    logger.info("Weather Icons Demo finished.")


if __name__ == "__main__":
    main()
