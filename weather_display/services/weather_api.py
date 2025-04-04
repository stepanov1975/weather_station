"""
Weather API service for fetching weather data from AccuWeather.

Handles fetching current conditions, forecast, and AQI data.
Includes caching and mock data capabilities.
"""

import time
import random
import logging
from datetime import datetime, timedelta

from ..utils.helpers import fetch_with_retry, download_image, check_internet_connection, format_temperature
# Import the new AQI translation function
from ..utils.localization import get_translation, translate_aqi_category
from .. import config

logger = logging.getLogger(__name__)

class AccuWeatherClient:
    """Client for interacting with the AccuWeather API."""

    def __init__(self, api_key=None, location_query=None):
        """
        Initialize the AccuWeather client.

        Args:
            api_key (str | None): AccuWeather API key. Reads from config if None.
            location_query (str | None): Location query (e.g., "City,Country"). Reads from config if None.
        """
        self.api_key = api_key or config.ACCUWEATHER_API_KEY
        self.location_query = location_query or config.LOCATION
        # Log the final location query being used by the client instance
        logger.info(f"AccuWeatherClient initialized with location_query: '{self.location_query}'")
        self.base_url = config.ACCUWEATHER_BASE_URL
        self.language = config.LANGUAGE

        # Cache to store data
        self.cache = {
            'location_key': None,
            'location_key': None,
            'current': None, # Will now include AQI data
            'forecast': None,
            'last_location_check': None,
            'last_weather_update': None,
            'last_aqi_update': None # Separate timestamp for AQI cache
        }

        # Flag to use mock data if no API key is provided or explicitly set
        self.use_mock_data = config.USE_MOCK_DATA or not self.api_key

        # Internet connection status
        self._connection_status = check_internet_connection()

        if self.use_mock_data:
            logger.warning("Using mock weather data (no API key provided or USE_MOCK_DATA=True)")
        elif not self.api_key:
             logger.error("AccuWeather API key is missing!")


    @property
    def connection_status(self):
        """Get the current internet connection status."""
        # Update the connection status
        self._connection_status = check_internet_connection()
        return self._connection_status

    def _get_location_key(self, force_refresh=False):
        """
        Get the AccuWeather location key for the configured location query.

        Args:
            force_refresh (bool): Force refresh from API, ignoring cache. Defaults to False.

        Returns:
            str | None: Location key string if successful, otherwise None.
        """
        current_time = time.time()
        # Check cache first (valid for 1 day)
        if (not force_refresh and
            self.cache['location_key'] and
            self.cache['last_location_check'] and
            current_time - self.cache['last_location_check'] < 24 * 60 * 60):
            return self.cache['location_key']

        if self.use_mock_data or not self.connection_status:
            logger.info("Using mock location key (mock data or no connection)")
            # Return a plausible mock key for testing mock data functions
            self.cache['location_key'] = "mock_key_12345"
            self.cache['last_location_check'] = current_time
            return self.cache['location_key']

        if not self.api_key:
            logger.error("Cannot get location key without API key.")
            return None

        try:
            url = f"{self.base_url}/locations/v1/cities/search"
            params = {
                'apikey': self.api_key,
                'q': self.location_query,
                'language': self.language
            }
            logger.info(f"Fetching location key for: {self.location_query}")
            data = fetch_with_retry(url, params)

            # Log the raw search results for debugging
            logger.debug(f"Raw location search results for '{self.location_query}': {data}")

            if data and isinstance(data, list) and len(data) > 0:
                # Log all found locations before selecting the first one
                for i, loc in enumerate(data):
                    key = loc.get('Key')
                    name = loc.get('LocalizedName')
                    country = loc.get('Country', {}).get('LocalizedName')
                    admin_area = loc.get('AdministrativeArea', {}).get('LocalizedName')
                    logger.info(f"  Result {i}: Key={key}, Name={name}, AdminArea={admin_area}, Country={country}")

                # Assume the first result is the correct one
                selected_location = data[0]
                location_key = selected_location.get('Key')
                location_name = selected_location.get('LocalizedName')
                country = selected_location.get('Country', {}).get('LocalizedName')
                logger.info(f"Selected location key: {location_key} for {location_name}, {country} (using first result)")
                self.cache['location_key'] = location_key
                self.cache['last_location_check'] = current_time
                return location_key
            else:
                logger.error(f"Could not find location key for query: {self.location_query}. Response: {data}")
                self.cache['location_key'] = None # Invalidate cache on failure
                return None
        except Exception as e:
            logger.error(f"Error fetching location key: {e}")
            # Don't invalidate cache on temporary network error, just return current value or None
            return self.cache.get('location_key')

    def _get_current_aqi(self, location_key):
        """
        Fetch current Air Quality Index (AQI) data using the Indices API.

        Args:
            location_key (str): The AccuWeather location key.

        Returns:
            dict | None: AQI data containing 'Value' and 'Category' if successful, otherwise None.
        """
        # Note: Caching for AQI is currently tied to the main weather update interval
        # via get_current_weather's cache check. A separate AQI cache timer is not implemented here.
        current_time = time.time()
        # Check cache first (valid for ~1 hour, adjust as needed)
        # Note: We are checking cache here, but the main call is within get_current_weather
        # which has its own cache check. This internal check might be redundant
        # depending on how often get_current_weather is called vs AQI update frequency.
        # Keeping it simple for now.

        if self.use_mock_data or not self.connection_status:
             # Return mock AQI if needed, handled by get_current_weather caller
            return None

        if not self.api_key:
            logger.error("Cannot get AQI without API key.")
            return None

        try:
            # Using the 1-day Indices API, requesting index 31 (Air Quality)
            # See AccuWeather docs for index details.
            url = f"{self.base_url}/indices/v1/daily/1day/{location_key}/31"
            params = {
                'apikey': self.api_key,
                'language': self.language,
            }
            logger.info(f"Fetching AQI (Index 31) for location key: {location_key}")
            data = fetch_with_retry(url, params)

            if data and isinstance(data, list) and len(data) > 0:
                # AQI data is usually the first item in the list
                aqi_data = data[0]
                aqi_value = aqi_data.get('Value')
                aqi_category = aqi_data.get('Category')
                logger.info(f"Found AQI: Value={aqi_value}, Category='{aqi_category}'")
                # Update cache timestamp if needed (though maybe better tied to main weather update)
                # self.cache['last_aqi_update'] = current_time
                return {'Value': aqi_value, 'Category': aqi_category}
            else:
                logger.warning(f"Could not find AQI data for location key: {location_key}. Response: {data}")
                return None
        except Exception as e:
            logger.error(f"Error fetching AQI data: {e}")
            return None


    def get_current_weather(self, force_refresh=False):
        """
        Get current weather data from AccuWeather.

        Args:
            force_refresh (bool): Force refresh from API, ignoring cache. Defaults to False.

        Returns:
            dict: Current weather data including temperature, humidity, condition,
                  icon details, AQI (if available), observation time, and connection status.
                  Returns mock data if configured or if API calls fail without cached data.
        """
        current_time = time.time()
        has_connection = self.connection_status

        # Check cache validity
        if (not force_refresh and
            self.cache['current'] and
            self.cache['last_weather_update'] and
            current_time - self.cache['last_weather_update'] < config.WEATHER_UPDATE_INTERVAL_MINUTES * 60):
            result = self.cache['current'].copy()
            result['connection_status'] = has_connection
            logger.debug("Returning cached current weather data.")
            return result

        # Use mock data if configured or no internet connection
        if self.use_mock_data or not has_connection:
            if not has_connection:
                logger.warning("No internet connection, using mock or cached current weather data")
            result = self._get_mock_current_weather()
            result['connection_status'] = has_connection
            # Update cache with mock data if no real data exists yet
            if not self.cache['current']:
                 cache_data = result.copy()
                 del cache_data['connection_status']
                 self.cache['current'] = cache_data
                 # Don't set last_weather_update for mock data to allow real fetch later
            return result

        # Get location key (required for API call)
        location_key = self._get_location_key()
        if not location_key:
            logger.error("Failed to get location key, cannot fetch current weather.")
            # Return previous cache or mock data if location key fails
            if self.cache['current']:
                result = self.cache['current'].copy()
                result['connection_status'] = False # Indicate issue
                return result
            else:
                result = self._get_mock_current_weather()
                result['connection_status'] = False # Indicate issue
                return result

        # Fetch new data from AccuWeather
        try:
            url = f"{self.base_url}/currentconditions/v1/{location_key}"
            params = {
                'apikey': self.api_key,
                'language': self.language,
                'details': 'true'  # Get humidity, etc.
            }
            logger.info(f"Fetching current weather for location key: {location_key}")
            data = fetch_with_retry(url, params)

            if not data or not isinstance(data, list) or len(data) == 0:
                logger.error(f"Failed to fetch or parse current weather data. Response: {data}")
                # Use cache or mock data on failure
                if self.cache['current']:
                    result = self.cache['current'].copy()
                    result['connection_status'] = False # API call failed
                    return result
                else:
                    result = self._get_mock_current_weather()
                    result['connection_status'] = False # API call failed
                    return result

            # Parse the API response (usually a list with one item)
            current = data[0]
            temp_data = current.get('Temperature', {}).get('Metric', {})
            icon_number = current.get('WeatherIcon')
            icon_url = None
            icon_path = None

            if icon_number:
                # Format icon number with leading zero if needed (e.g., 1 -> 01)
                icon_str = f"{icon_number:02d}"
                icon_filename = f"{icon_str}-s.png"
                # Construct AccuWeather icon URL
                accu_icon_url = f"https://developer.accuweather.com/sites/default/files/{icon_filename}"
                # Use helper to download/cache
                icon_path = download_image(accu_icon_url, 'weather_display/assets/icons', filename=icon_filename)
                # Store the original URL for reference if needed, or the path
                icon_url = accu_icon_url # Or potentially icon_path if preferred

            parsed_data = {
                'temperature': temp_data.get('Value'),
                'humidity': current.get('RelativeHumidity'),
                'condition': current.get('WeatherText'),
                'icon_url': icon_url, # URL or path to the downloaded icon
                'icon_path': icon_path, # Path to the downloaded icon
                'observation_time': current.get('LocalObservationDateTime'),
                'observation_time': current.get('LocalObservationDateTime'),
                # AQI will be fetched separately
                'air_quality_index': None, # The numeric value
                'air_quality_category': None, # The category text (e.g., "Good")
                'connection_status': True
            }

            # --- Fetch AQI Data ---
            aqi_data = self._get_current_aqi(location_key)
            if aqi_data:
                parsed_data['air_quality_index'] = aqi_data.get('Value')
                parsed_data['air_quality_category'] = aqi_data.get('Category')
            # --- End Fetch AQI ---


            # Update cache
            cache_data = parsed_data.copy()
            del cache_data['connection_status']
            self.cache['current'] = cache_data
            self.cache['last_weather_update'] = current_time
            logger.debug("Successfully fetched and parsed current weather.")

            return parsed_data

        except Exception as e:
            logger.error(f"Error fetching current weather: {e}", exc_info=True)
            # Return cached data or mock data on exception
            if self.cache['current']:
                result = self.cache['current'].copy()
                result['connection_status'] = False # Exception occurred
                return result
            else:
                result = self._get_mock_current_weather()
                result['connection_status'] = False # Exception occurred
                return result

    def get_forecast(self, days=1, force_refresh=False):
        """
        Get forecast data from AccuWeather.
        Note: Free tier typically allows 1-day or 5-day forecasts. Using 1-day here.

        Args:
            days (int): Number of days requested (used for mock data generation). Defaults to 1.
                        Note: The API call always uses the 5-day endpoint.
            force_refresh (bool): Force refresh from API, ignoring cache. Defaults to False.

        Returns:
            dict: Dictionary containing 'forecast' (a list of daily forecast dicts for up to 5 days)
                  and 'connection_status' (bool). Returns mock data if configured or on failure.
        """
        # Use the requested number of days, but AccuWeather endpoint is 5day
        requested_days = days
        endpoint_days = 5 # Use the 5-day endpoint
        current_time = time.time()
        has_connection = self.connection_status

        # Check cache validity
        if (not force_refresh and
            self.cache['forecast'] and
            self.cache['last_weather_update'] and # Use same timestamp as current weather
            current_time - self.cache['last_weather_update'] < config.WEATHER_UPDATE_INTERVAL_MINUTES * 60):
            result = {
                'forecast': self.cache['forecast'],
                'connection_status': has_connection
            }
            logger.debug("Returning cached forecast data.")
            return result

        # Use mock data if configured or no internet connection
        if self.use_mock_data or not has_connection:
            if not has_connection:
                logger.warning("No internet connection, using mock or cached forecast data")
            result = {
                'forecast': self._get_mock_forecast(days),
                'connection_status': has_connection
            }
             # Update cache with mock data if no real data exists yet
            if not self.cache['forecast']:
                 self.cache['forecast'] = result['forecast']
                 # Don't set last_weather_update for mock data
            return result

        # Get location key
        location_key = self._get_location_key()
        if not location_key:
            logger.error("Failed to get location key, cannot fetch forecast.")
            # Return previous cache or mock data
            if self.cache['forecast']:
                 return {'forecast': self.cache['forecast'], 'connection_status': False}
            else:
                 return {'forecast': self._get_mock_forecast(days), 'connection_status': False}


        # Fetch new data
        try:
            # Using 5-day forecast endpoint
            url = f"{self.base_url}/forecasts/v1/daily/{endpoint_days}day/{location_key}"
            params = {
                'apikey': self.api_key,
                'language': self.language,
                'details': 'true', # Include details like RealFeel, wind, etc.
                'metric': 'true'  # Use metric units (Celsius)
            }
            logger.info(f"Fetching {endpoint_days}-day forecast for location key: {location_key}")
            data = fetch_with_retry(url, params)

            if not data or 'DailyForecasts' not in data:
                logger.error(f"Failed to fetch or parse forecast data. Response: {data}")
                 # Use cache or mock data on failure
                if self.cache['forecast']:
                    return {'forecast': self.cache['forecast'], 'connection_status': False}
                else:
                    return {'forecast': self._get_mock_forecast(days), 'connection_status': False}

            # Parse the API response
            forecast_days = []
            for day_data in data.get('DailyForecasts', []):
                temp_info = day_data.get('Temperature', {})
                day_info = day_data.get('Day', {})
                # night_info = day_data.get('Night', {}) # Can use night info if needed

                day_icon_num = day_info.get('Icon')
                day_icon_path = None
                day_icon_url = None
                if day_icon_num:
                    icon_str = f"{day_icon_num:02d}"
                    icon_filename = f"{icon_str}-s.png"
                    accu_icon_url = f"https://developer.accuweather.com/sites/default/files/{icon_filename}"
                    day_icon_path = download_image(accu_icon_url, 'weather_display/assets/icons', filename=icon_filename)
                    day_icon_url = accu_icon_url


                forecast_days.append({
                    'date': day_data.get('Date'),
                    'max_temp': temp_info.get('Maximum', {}).get('Value'),
                    'min_temp': temp_info.get('Minimum', {}).get('Value'),
                    'condition': day_info.get('IconPhrase'), # Using day phrase
                    'icon_url': day_icon_url, # URL or path
                    'icon_path': day_icon_path # Path
                })

            # Update cache
            self.cache['forecast'] = forecast_days
            # Use the same timestamp as current weather if fetched together,
            # or update if fetched separately. Assuming fetched together for now.
            if not self.cache['last_weather_update'] or force_refresh:
                 self.cache['last_weather_update'] = current_time

            logger.debug(f"Successfully fetched and parsed {len(forecast_days)}-day forecast.")

            return {
                'forecast': forecast_days,
                'connection_status': True
            }

        except Exception as e:
            logger.error(f"Error fetching forecast: {e}", exc_info=True)
            # Return cached data or mock data on exception
            if self.cache['forecast']:
                return {'forecast': self.cache['forecast'], 'connection_status': False}
            else:
                return {'forecast': self._get_mock_forecast(days), 'connection_status': False}


    def _get_mock_current_weather(self):
        """
        Generate mock current weather data for testing.

        Returns:
            dict: Mock current weather data structure.
        """
        logger.debug("Generating mock current weather.")
        mock_icon_num = random.choice([1, 2, 3, 4, 6, 7]) # Example AccuWeather icon numbers
        mock_icon_path = f"weather_display/assets/icons/{mock_icon_num:02d}-s.png" # Mock path
        return {
            'temperature': round(random.uniform(15, 28), 1),
            'humidity': random.randint(40, 80),
            'condition': random.choice(['Sunny', 'Mostly Sunny', 'Partly Cloudy', 'Intermittent Clouds', 'Cloudy', 'Mostly Cloudy']),
            'icon_url': f"https://developer.accuweather.com/sites/default/files/{mock_icon_num:02d}-s.png",
            'icon_path': mock_icon_path,
            'observation_time': datetime.now().isoformat(),
            'observation_time': datetime.now().isoformat(),
            # Add mock AQI data
            'air_quality_index': random.randint(10, 150), # Example value range
            'air_quality_category': random.choice(["Good", "Moderate", "Unhealthy for Sensitive Groups"]), # Example categories
            # connection_status added by caller
        }

    def _get_mock_forecast(self, days=1):
        """
        Generate mock forecast data for testing.

        Args:
            days (int): Number of mock forecast days to generate. Defaults to 1.

        Returns:
            list: List of mock daily forecast data dictionaries.
        """
        # Keep mock data generation flexible based on requested days
        logger.debug(f"Generating mock forecast for {days} day(s).")
        base_date = datetime.now()
        forecast = []
        conditions = ['Sunny', 'Mostly Sunny', 'Partly Cloudy', 'Intermittent Clouds', 'Hazy Sunshine', 'Mostly Cloudy', 'Cloudy']
        icon_nums = [1, 2, 3, 4, 5, 6, 7]

        for i in range(days):
            date = base_date + timedelta(days=i)
            condition_index = random.randint(0, len(conditions) - 1)
            mock_icon_num = icon_nums[condition_index]
            mock_icon_path = f"weather_display/assets/icons/{mock_icon_num:02d}-s.png" # Mock path

            forecast.append({
                'date': date.strftime('%Y-%m-%dT%H:%M:%S%z'), # Mock ISO format
                'max_temp': round(25.0 + random.uniform(-3, 3), 1),
                'min_temp': round(18.0 + random.uniform(-2, 2), 1),
                'condition': conditions[condition_index],
                'icon_url': f"https://developer.accuweather.com/sites/default/files/{mock_icon_num:02d}-s.png",
                'icon_path': mock_icon_path
            })
        return forecast
