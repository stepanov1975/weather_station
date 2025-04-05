#!/usr/bin/env python3
"""
Executable entry point script for the Weather Display application.

This script serves as a simple way to run the application. It imports and
executes the `main` function from the `weather_display.main` module.

To run the application, execute this script from the project's root directory:
    python run_weather_display.py [arguments]

Alternatively, run the main module directly:
    python -m weather_display.main [arguments]
"""

# Standard library imports
# (No sys.path manipulation needed if run correctly or package installed)

# Local application imports
try:
    from weather_display.main import main
except ImportError as e:
    print(f"Error importing main function: {e}")
    print("Please ensure the script is run from the project root directory or the package is installed.")
    import sys
    sys.exit(1)


if __name__ == "__main__":
    # Call the main function defined in weather_display/main.py
    main()
