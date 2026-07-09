#!/usr/bin/env python3
"""
Tests for the WeatherIconHandler class.

This script tests the functionality of the WeatherIconHandler class:
- Getting icon paths based on local weather icon codes
- Getting icons based on condition text
- Verifying bundled icons
"""

import logging
import os
import unittest
from unittest.mock import patch

# Import our icon handler
from weather_display.utils.icon_handler import WeatherIconHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TestWeatherIconHandler(unittest.TestCase):
    """Test cases for the WeatherIconHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.icon_handler = WeatherIconHandler()
    
    def test_get_icon_path(self):
        """Test getting an icon path from a code."""
        # Test a valid icon code
        path = self.icon_handler.get_icon_path(1)  # Sunny
        assert path is not None
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path) or path.endswith("01_sunny.png"))
        
        # Test getting an icon path with a nonexistent code
        with patch('logging.Logger.warning') as mock_warning:
            path = self.icon_handler.get_icon_path(999)  # Invalid code
            mock_warning.assert_called_once()

    def test_icon_directory_uses_packaged_assets(self):
        """Test icons are loaded from package data, not the old top-level asset copy."""
        expected_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "weather_display", "assets", "weather_icons")
        )

        with patch("os.makedirs") as mock_makedirs:
            icon_handler = WeatherIconHandler()

        mock_makedirs.assert_not_called()
        self.assertEqual(os.path.abspath(icon_handler.icon_dir), expected_dir)
        self.assertEqual(icon_handler.verify_all_icons(), len(icon_handler.ICON_MAPPING))
    
    def test_get_icon_by_condition(self):
        """Test getting an icon path from a condition text."""
        # Test exact match
        path = self.icon_handler.get_icon_by_condition("Sunny")
        assert path is not None
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path) or path.endswith("01_sunny.png"))
        
        # Test case-insensitive match
        path = self.icon_handler.get_icon_by_condition("sunny")
        assert path is not None
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path) or path.endswith("01_sunny.png"))
        
        # Test partial match
        path = self.icon_handler.get_icon_by_condition("Cloudy with some Showers")
        self.assertIsNotNone(path)
        
        # Test nonexistent condition
        with patch('logging.Logger.warning') as mock_warning:
            path = self.icon_handler.get_icon_by_condition("Not a real weather condition")
            self.assertIsNotNone(path)
            self.assertGreaterEqual(mock_warning.call_count, 1)
    
    def test_verify_all_icons(self):
        """Test verifying bundled icons."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            count = self.icon_handler.verify_all_icons()
            self.assertEqual(count, len(self.icon_handler.ICON_MAPPING))
    
    def test_load_icon(self):
        """Test loading an icon as a CTkImage."""
        # This test requires CustomTkinter and PIL, so we'll just
        # mock the dependencies to avoid test failures
        with patch('customtkinter.CTkImage') as mock_ctk_image, \
             patch('PIL.Image.open') as mock_pil_open, \
             patch.object(self.icon_handler, 'get_icon_path') as mock_get_path, \
             patch('os.path.exists') as mock_exists:
            
            # Set up our mocks
            mock_get_path.return_value = "fake_path.png"
            mock_exists.return_value = True  # Mock that the file exists
            mock_pil_open.return_value = "fake_pil_image"
            mock_ctk_image.return_value = "fake_ctk_image"
            
            # Test loading an icon
            icon = self.icon_handler.load_icon(1)
            self.assertEqual(icon, "fake_ctk_image")
            mock_get_path.assert_called_once_with(1)
            
            # Test cache works
            self.icon_handler.load_icon(1)  # Should use cache
            mock_get_path.assert_called_once()  # Should not call again

if __name__ == "__main__":
    unittest.main()
