"""
Weather API service for fetching weather data from WeatherAPI.com.
"""

import time
import random
from datetime import datetime, timedelta
import logging

from ..utils.helpers import fetch_with_retry, download_image, get_air_quality_text
from .. import config

logger = logging.getLogger(__name__)

class WeatherAPIClient:
    """Client for interacting with the WeatherAPI.com API."""
    
    def __init__(self, api_key=None, location=None):
        """
        Initialize the WeatherAPI client.
        
        Args:
            api_key (str, optional): WeatherAPI.com API key
            location (str, optional): Location to get weather for
        """
        self.api_key = api_key or config.WEATHER_API_KEY
        self.location = location or config.LOCATION
        self.base_url = config.WEATHER_API_URL
        
        # Cache to store data between updates
        self.cache = {
            'current': None,
            'forecast': None,
            'last_update': None
        }
        
        # Flag to use mock data if no API key is provided
        self.use_mock_data = config.USE_MOCK_DATA or not self.api_key
        
        if self.use_mock_data:
            logger.warning("Using mock weather data (no API key provided)")
    
    def get_current_weather(self, force_refresh=False):
        """
        Get current weather data.
        
        Args:
            force_refresh (bool, optional): Force refresh from API
            
        Returns:
            dict: Current weather data
        """
        current_time = time.time()
        
        # If cache is valid (less than 30 minutes old) and not forced refresh
        if (not force_refresh and 
            self.cache['current'] and 
            self.cache['last_update'] and 
            current_time - self.cache['last_update'] < config.WEATHER_UPDATE_INTERVAL_MINUTES * 60):
            return self.cache['current']
        
        # Use mock data if configured
        if self.use_mock_data:
            return self._get_mock_current_weather()
        
        # Otherwise, fetch new data
        try:
            url = f"{self.base_url}/current.json"
            params = {
                'key': self.api_key,
                'q': self.location,
                'aqi': 'yes'
            }
            
            data = fetch_with_retry(url, params)
            
            if not data:
                # If API call failed but we have cached data, use that
                if self.cache['current']:
                    logger.warning("Using cached weather data due to API failure")
                    return self.cache['current']
                # Otherwise use mock data
                return self._get_mock_current_weather()
            
            # Parse the API response
            current = data.get('current', {})
            
            # Download weather icon
            icon_url = current.get('condition', {}).get('icon')
            if icon_url:
                download_image(icon_url, 'weather_display/assets/icons')
            
            # Extract and format the data
            parsed_data = {
                'temperature': current.get('temp_c'),
                'humidity': current.get('humidity'),
                'condition': current.get('condition', {}).get('text'),
                'icon_url': icon_url,
                'air_quality_index': current.get('air_quality', {}).get('us-epa-index'),
                'air_quality_text': get_air_quality_text(
                    current.get('air_quality', {}).get('us-epa-index')
                )
            }
            
            # Update cache
            self.cache['current'] = parsed_data
            self.cache['last_update'] = current_time
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            # Return cached data if available, otherwise mock data
            return self.cache['current'] if self.cache['current'] else self._get_mock_current_weather()
    
    def get_forecast(self, days=3, force_refresh=False):
        """
        Get forecast data.
        
        Args:
            days (int, optional): Number of days to forecast
            force_refresh (bool, optional): Force refresh from API
            
        Returns:
            list: List of forecast data for each day
        """
        current_time = time.time()
        
        # If cache is valid (less than 30 minutes old) and not forced refresh
        if (not force_refresh and 
            self.cache['forecast'] and 
            self.cache['last_update'] and 
            current_time - self.cache['last_update'] < config.WEATHER_UPDATE_INTERVAL_MINUTES * 60):
            return self.cache['forecast']
        
        # Use mock data if configured
        if self.use_mock_data:
            return self._get_mock_forecast(days)
        
        # Otherwise, fetch new data
        try:
            url = f"{self.base_url}/forecast.json"
            params = {
                'key': self.api_key,
                'q': self.location,
                'days': days,
                'aqi': 'yes'
            }
            
            data = fetch_with_retry(url, params)
            
            if not data:
                # If API call failed but we have cached data, use that
                if self.cache['forecast']:
                    logger.warning("Using cached forecast data due to API failure")
                    return self.cache['forecast']
                # Otherwise use mock data
                return self._get_mock_forecast(days)
            
            # Parse the API response
            forecast_days = []
            for day_data in data.get('forecast', {}).get('forecastday', []):
                day = day_data.get('day', {})
                
                # Download weather icon
                icon_url = day.get('condition', {}).get('icon')
                if icon_url:
                    download_image(icon_url, 'weather_display/assets/icons')
                
                forecast_days.append({
                    'date': day_data.get('date'),
                    'max_temp': day.get('maxtemp_c'),
                    'min_temp': day.get('mintemp_c'),
                    'condition': day.get('condition', {}).get('text'),
                    'icon_url': icon_url
                })
            
            # Update cache
            self.cache['forecast'] = forecast_days
            self.cache['last_update'] = current_time
            
            return forecast_days
            
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            # Return cached data if available, otherwise mock data
            return self.cache['forecast'] if self.cache['forecast'] else self._get_mock_forecast(days)
    
    def _get_mock_current_weather(self):
        """
        Get mock current weather data for testing.
        
        Returns:
            dict: Mock current weather data
        """
        return {
            'temperature': 22.5,
            'humidity': 65,
            'condition': 'Partly cloudy',
            'icon_url': '//cdn.weatherapi.com/weather/64x64/day/116.png',
            'air_quality_index': 1,
            'air_quality_text': 'Good'
        }
    
    def _get_mock_forecast(self, days=3):
        """
        Get mock forecast data for testing.
        
        Args:
            days (int, optional): Number of days to forecast
            
        Returns:
            list: List of mock forecast data for each day
        """
        base_date = datetime.now()
        forecast = []
        
        conditions = ['Sunny', 'Partly cloudy', 'Cloudy', 'Patchy rain nearby', 'Light rain', 'Moderate rain']
        icons = [
            '//cdn.weatherapi.com/weather/64x64/day/113.png',  # Sunny
            '//cdn.weatherapi.com/weather/64x64/day/116.png',  # Partly cloudy
            '//cdn.weatherapi.com/weather/64x64/day/119.png',  # Cloudy
            '//cdn.weatherapi.com/weather/64x64/day/176.png',  # Patchy rain nearby
            '//cdn.weatherapi.com/weather/64x64/day/296.png',  # Light rain
            '//cdn.weatherapi.com/weather/64x64/day/302.png'   # Moderate rain
        ]
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            condition_index = random.randint(0, len(conditions) - 1)
            
            forecast.append({
                'date': date.strftime('%Y-%m-%d'),
                'max_temp': 25.0 + random.uniform(-3, 3),
                'min_temp': 18.0 + random.uniform(-2, 2),
                'condition': conditions[condition_index],
                'icon_url': icons[condition_index]
            })
        
        return forecast
