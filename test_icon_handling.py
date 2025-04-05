#!/usr/bin/env python3
"""
Tests for the WeatherIconHandler class.

This script tests the functionality of the WeatherIconHandler class:
- Getting icon paths based on AccuWeather codes
- Getting icons based on condition text
- Downloading icons
"""

import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path to allow importing from weather_display
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import our icon handler
from weather_display.utils.icon_handler import WeatherIconHandler

class TestWeatherIconHandler(unittest.TestCase):
    """Test cases for the WeatherIconHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.icon_handler = WeatherIconHandler()
    
    def test_get_icon_path(self):
        """Test getting an icon path from a code."""
        # Test a valid icon code
        path = self.icon_handler.get_icon_path(1)  # Sunny
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path) or path.endswith("01_sunny.png"))
        
        # Test getting an icon path with a nonexistent code
        with patch('logging.Logger.warning') as mock_warning:
            path = self.icon_handler.get_icon_path(999)  # Invalid code
            mock_warning.assert_called_once()
    
    def test_get_icon_by_condition(self):
        """Test getting an icon path from a condition text."""
        # Test exact match
        path = self.icon_handler.get_icon_by_condition("Sunny")
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path) or path.endswith("01_sunny.png"))
        
        # Test case-insensitive match
        path = self.icon_handler.get_icon_by_condition("sunny")
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path) or path.endswith("01_sunny.png"))
        
        # Test partial match
        path = self.icon_handler.get_icon_by_condition("Cloudy with some Showers")
        self.assertIsNotNone(path)
        
        # Test nonexistent condition
        with patch('logging.Logger.warning') as mock_warning:
            path = self.icon_handler.get_icon_by_condition("Not a real weather condition")
            mock_warning.assert_called_once()
    
    @patch('requests.get')
    def test_download_icon(self, mock_get):
        """Test downloading an icon."""
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        # Create a simple file-like object for the mock response content
        mock_response.iter_content.return_value = [b'test_image_content']
        mock_get.return_value = mock_response
        
        # Test downloading an icon
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            result = self.icon_handler._download_icon(1, "test_path.png")
            self.assertTrue(result)
            mock_file.assert_called_once_with("test_path.png", 'wb')
    
    def test_download_all_icons(self):
        """Test downloading all icons."""
        # Mock the _download_icon method to avoid actual downloads
        with patch.object(self.icon_handler, '_download_icon') as mock_download:
            mock_download.return_value = True
            count = self.icon_handler.download_all_icons()
            # Should call _download_icon for each icon in ICON_MAPPING
            self.assertEqual(count, len(mock_download.call_args_list))
    
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
