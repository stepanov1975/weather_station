#!/usr/bin/env python3
"""
Launcher script for the Weather Display application.
"""

import os
import sys
from weather_display.main import main

if __name__ == "__main__":
    # Make the script executable
    os.chmod(__file__, 0o755)
    
    # Run the main function
    main()
