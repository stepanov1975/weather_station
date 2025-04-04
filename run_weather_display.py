#!/usr/bin/env python3
"""
Entry point script for the Weather Display application.

This script simply imports and calls the main() function from weather_display.main.
It ensures the package directory is in the Python path.
"""

import os
import sys

# Ensure the weather_display package can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the main function from the application logic module
from weather_display.main import main

if __name__ == "__main__":
    main()
