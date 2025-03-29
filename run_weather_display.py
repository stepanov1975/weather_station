#!/usr/bin/env python3
"""
Launcher script for the Weather Display application.

This script serves as the entry point for the Weather Display application.
It ensures the script is executable and launches the main application.

Usage:
    python run_weather_display.py [--api-key KEY] [--mock] [--windowed]

Options:
    --api-key KEY    WeatherAPI.com API key for weather data
    --mock          Use mock data instead of real API calls
    --windowed      Run in windowed mode instead of fullscreen
"""

import os
import sys
from weather_display.main import main

if __name__ == "__main__":
    # Make the script executable
    os.chmod(__file__, 0o755)
    
    # Run the main function
    main()
