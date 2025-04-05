#!/usr/bin/env python3
"""
Weather Icons Demonstration

This script creates a visual demo of all available weather icons
using a CustomTkinter GUI grid.
"""

import os
import sys
import logging
import customtkinter as ctk
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import our icon handler
from weather_display.utils.icon_handler import WeatherIconHandler

class WeatherIconsDemo(ctk.CTk):
    """Weather Icons Demonstration Application"""
    
    def __init__(self):
        """Initialize the demo application."""
        super().__init__()
        
        # Configure the window
        self.title("Weather Icons Demo")
        self.geometry("800x600")
        
        # Create the icon handler
        self.icon_handler = WeatherIconHandler()
        
        # Create a scrollable frame for the icons
        self.create_widgets()
    
    def create_widgets(self):
        """Create the demo UI widgets."""
        # Title label
        title_label = ctk.CTkLabel(
            self, 
            text="Weather Icons", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Create a scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self, width=750, height=500)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Create a grid of icons
        row, col = 0, 0
        max_cols = 4
        
        # Sort icon codes for better presentation
        day_icons = sorted([code for code in self.icon_handler.ICON_MAPPING.keys() 
                           if code < 33])
        night_icons = sorted([code for code in self.icon_handler.ICON_MAPPING.keys() 
                             if code >= 33])
        
        # Day icons section
        section_label = ctk.CTkLabel(
            scroll_frame, 
            text="Day Icons", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_label.grid(row=row, column=0, columnspan=max_cols, sticky="w", pady=(10, 5))
        row += 1
        col = 0
        
        # Add day icons
        for icon_code in day_icons:
            self.create_icon_widget(scroll_frame, icon_code, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Night icons section
        if col > 0:  # Move to next row if not already at beginning
            row += 1
            col = 0
            
        section_label = ctk.CTkLabel(
            scroll_frame, 
            text="Night Icons", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_label.grid(row=row, column=0, columnspan=max_cols, sticky="w", pady=(20, 5))
        row += 1
        
        # Add night icons
        for icon_code in night_icons:
            self.create_icon_widget(scroll_frame, icon_code, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def create_icon_widget(self, parent, icon_code, row, col):
        """Create a widget displaying a weather icon with its description."""
        info = self.icon_handler.ICON_MAPPING[icon_code]
        
        # Create a frame for this icon
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Load the icon
        icon = self.icon_handler.load_icon(icon_code, size=(64, 64))
        
        # Icon display
        if icon:
            icon_label = ctk.CTkLabel(frame, image=icon, text="")
            icon_label.pack(padx=5, pady=5)
        
        # Icon code
        code_label = ctk.CTkLabel(frame, text=f"Code: {icon_code}")
        code_label.pack()
        
        # Icon name
        name_label = ctk.CTkLabel(
            frame, 
            text=info["description"], 
            wraplength=150
        )
        name_label.pack(padx=5, pady=5)

def main():
    """Run the weather icons demo."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = WeatherIconsDemo()
    app.mainloop()

if __name__ == "__main__":
    main()
