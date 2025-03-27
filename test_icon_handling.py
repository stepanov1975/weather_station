#!/usr/bin/env python3
"""
Test script to verify the icon handling logic in the weather display application.
"""

import os
import sys
from weather_display.utils.helpers import download_image

def test_icon_handling():
    """Test the icon handling logic."""
    # Create the icons directory if it doesn't exist
    os.makedirs('weather_display/assets/icons', exist_ok=True)
    
    # Test URLs
    day_icon_url = '//cdn.weatherapi.com/weather/64x64/day/113.png'  # Sunny day
    night_icon_url = '//cdn.weatherapi.com/weather/64x64/night/113.png'  # Clear night
    
    # Download the icons
    print(f"Downloading day icon: {day_icon_url}")
    day_icon_path = download_image(day_icon_url, 'weather_display/assets/icons')
    print(f"Downloaded to: {day_icon_path}")
    
    print(f"Downloading night icon: {night_icon_url}")
    night_icon_path = download_image(night_icon_url, 'weather_display/assets/icons')
    print(f"Downloaded to: {night_icon_path}")
    
    # List the icons directory
    print("\nContents of icons directory:")
    for filename in os.listdir('weather_display/assets/icons'):
        if filename.endswith('.png'):
            print(f"  {filename}")
    
    # Verify the icon filenames
    expected_day_filename = 'day_113.png'
    expected_night_filename = 'night_113.png'
    
    day_icon_exists = os.path.exists(os.path.join('weather_display/assets/icons', expected_day_filename))
    night_icon_exists = os.path.exists(os.path.join('weather_display/assets/icons', expected_night_filename))
    
    print(f"\nDay icon '{expected_day_filename}' exists: {day_icon_exists}")
    print(f"Night icon '{expected_night_filename}' exists: {night_icon_exists}")
    
    if day_icon_exists and night_icon_exists:
        print("\nSUCCESS: Both day and night icons were downloaded with the correct filenames.")
        return True
    else:
        print("\nFAILURE: One or both icons were not downloaded with the correct filenames.")
        return False

if __name__ == "__main__":
    # Activate the virtual environment
    activate_script = os.path.join('weather_venv', 'bin', 'activate_this.py')
    if os.path.exists(activate_script):
        with open(activate_script) as f:
            exec(f.read(), {'__file__': activate_script})
    
    # Run the test
    success = test_icon_handling()
    sys.exit(0 if success else 1)
