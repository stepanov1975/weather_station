#!/usr/bin/env python3
"""
Test script for the Weather Display application.

This script tests the Weather Display application with mock data.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add the parent directory to the path so we can import the weather_display package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weather_display.services.weather_api import WeatherAPIClient
from weather_display.services.time_service import TimeService


class TestWeatherDisplay(unittest.TestCase):
    """Test cases for the Weather Display application."""
    
    def test_weather_api_mock_data(self):
        """Test that the WeatherAPI client returns mock data when configured to do so."""
        # Create a client with no API key (should use mock data)
        client = WeatherAPIClient(api_key=None)
        
        # Verify that use_mock_data is True
        self.assertTrue(client.use_mock_data)
        
        # Get current weather
        current_weather = client.get_current_weather()
        
        # Verify that we got mock data
        self.assertIsNotNone(current_weather)
        self.assertIn('temperature', current_weather)
        self.assertIn('humidity', current_weather)
        self.assertIn('condition', current_weather)
        
        # Get forecast
        forecast = client.get_forecast(days=3)
        
        # Verify that we got mock data
        self.assertIsNotNone(forecast)
        self.assertEqual(len(forecast), 3)
        for day in forecast:
            self.assertIn('date', day)
            self.assertIn('max_temp', day)
            self.assertIn('min_temp', day)
            self.assertIn('condition', day)
    
    def test_time_service(self):
        """Test that the TimeService returns valid time and date strings."""
        time_service = TimeService()
        
        # Get current time
        time_str = time_service.get_current_time()
        
        # Verify that we got a valid time string
        self.assertIsNotNone(time_str)
        self.assertRegex(time_str, r'^\d{2}:\d{2}:\d{2}$')
        
        # Get current date
        date_str = time_service.get_current_date()
        
        # Verify that we got a valid date string
        self.assertIsNotNone(date_str)
        self.assertRegex(date_str, r'^[A-Za-z]+, \d{2} [A-Za-z]+ \d{4}$')
        
        # Get current datetime
        time_str, date_str = time_service.get_current_datetime()
        
        # Verify that we got valid time and date strings
        self.assertIsNotNone(time_str)
        self.assertRegex(time_str, r'^\d{2}:\d{2}:\d{2}$')
        self.assertIsNotNone(date_str)
        self.assertRegex(date_str, r'^[A-Za-z]+, \d{2} [A-Za-z]+ \d{4}$')


if __name__ == '__main__':
    unittest.main()
