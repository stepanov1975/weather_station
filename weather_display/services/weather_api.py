"""
AccuWeather API Service for the Weather Display application.

This module provides the `AccuWeatherClient` class, responsible for fetching
current weather conditions, daily forecasts, and Air Quality Index (AQI) data
from the AccuWeather API. It includes features like caching, mock data generation
for testing, and handling API request limits.
"""

# Standard library imports
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

# Local application imports
from .. import config
from ..utils.helpers import fetch_with_retry, check_internet_connection
# Note: translate_aqi_category is used here, get_translation might be needed for error messages if desired
from ..utils.localization import get_translation, translate_aqi_category


logger = logging.getLogger(__name__)

# Define expected structure for cached data (for clarity/documentation)
# Using comments as TypedDict might be overly complex here.
# Cache Structure:
# {
#     'location_key': Optional[str],
#     'current': Optional[Dict[str, Any]], # See get_current_weather return 'data' structure
#     'forecast': Optional[List[Dict[str, Any]]], # See get_forecast return 'data' structure
#     'last_location_check': Optional[float], # Timestamp
#     'last_weather_update': Optional[float] # Timestamp for current/forecast
# }


class AccuWeatherClient:
    """
    Client for interacting with the AccuWeather weather API.

    Handles fetching location keys, current conditions, forecasts, and AQI.
    Implements caching to reduce API calls and provides mock data capabilities.

    Attributes:
        api_key (Optional[str]): The AccuWeather API key.
        location_query (str): The location string (e.g., "City,Country").
        base_url (str): The base URL for AccuWeather API endpoints.
        language (str): Language code for API responses.
        cache (Dict[str, Any]): Internal cache for API data and timestamps.
        use_mock_data (bool): Flag indicating whether to use mock data.
        _connection_status (bool): Internal flag for internet connection status.
    """

    # Cache validity durations (in seconds)
    _LOCATION_KEY_CACHE_DURATION = 24 * 60 * 60  # 1 day
    # Weather cache duration is based on config.WEATHER_UPDATE_INTERVAL_MINUTES

    def __init__(self, api_key: Optional[str] = None, location_query: Optional[str] = None):
        """
        Initialize the AccuWeather client.

        Args:
            api_key: AccuWeather API key. Reads from config/env if None.
            location_query: Location query (e.g., "City,Country"). Reads from config if None.
        """
        self.api_key: Optional[str] = api_key or config.ACCUWEATHER_API_KEY
        self.location_query: str = location_query or config.LOCATION
        self.base_url: str = config.ACCUWEATHER_BASE_URL
        self.language: str = config.ACCUWEATHER_LANGUAGE # Use language from config

        logger.info(f"AccuWeatherClient initialized for location: '{self.location_query}' with language '{self.language}'")

        # Initialize cache structure
        self.cache: Dict[str, Any] = {
            'location_key': None,
            'current': None,
            'forecast': None,
            'last_location_check': None,
            'last_weather_update': None,
            # 'last_aqi_update' is not explicitly tracked; AQI is fetched
            # alongside current weather and uses 'last_weather_update'.
        }

        # Determine if mock data should be used
        self.use_mock_data: bool = config.USE_MOCK_DATA or not self.api_key

        # Initial internet connection check
        self._connection_status: bool = check_internet_connection()

        if self.use_mock_data:
            logger.warning("Client configured to use MOCK weather data.")
        elif not self.api_key:
            logger.error(
                "AccuWeather API key is missing! Real data cannot be fetched. "
                "Set ACCUWEATHER_API_KEY environment variable or check config."
            )

    @property
    def connection_status(self) -> bool:
        """Check and return the current internet connection status."""
        # Re-check connection status each time property is accessed
        self._connection_status = check_internet_connection()
        if not self._connection_status:
             logger.debug("Internet connection check failed.")
        return self._connection_status

    def _is_cache_valid(self, cache_key: str, duration_seconds: float) -> bool:
        """Check if a specific cache entry is still valid."""
        return (
            self.cache.get(cache_key) is not None and
            self.cache.get(f"last_{cache_key}_update") is not None and
            (time.time() - self.cache[f"last_{cache_key}_update"]) < duration_seconds
        )

    def _get_location_key(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get the AccuWeather location key for the configured location query.

        Retrieves from cache if valid, otherwise fetches from the API.

        Args:
            force_refresh: If True, bypass cache and force API fetch.

        Returns:
            The location key string if successful, otherwise None.
        """
        current_time = time.time()
        cache_duration = self._LOCATION_KEY_CACHE_DURATION

        # Check cache first
        if (not force_refresh and
                self.cache['location_key'] and
                self.cache['last_location_check'] and
                (current_time - self.cache['last_location_check']) < cache_duration):
            logger.debug("Returning cached location key.")
            return self.cache['location_key']

        # Handle mock data or no connection
        if self.use_mock_data or not self.connection_status:
            logger.info("Using mock location key (mock data mode or no connection).")
            self.cache['location_key'] = "mock_location_key_12345" # Static mock key
            self.cache['last_location_check'] = current_time
            return self.cache['location_key']

        # Check for API key before making API call
        if not self.api_key:
            logger.error("Cannot fetch location key: AccuWeather API key is missing.")
            return None

        # Fetch from API
        try:
            url = f"{self.base_url}/locations/v1/cities/search"
            params = {
                'apikey': self.api_key,
                'q': self.location_query,
                'language': config.ACCUWEATHER_LANGUAGE # Use configured language
            }
            logger.info(f"Fetching location key from API for query: '{self.location_query}' (Lang: {self.language})")
            location_search_results = fetch_with_retry(url, params)

            # Handle potential API limit error returned by fetch_with_retry
            if isinstance(location_search_results, dict) and location_search_results.get('Code') == 'ServiceUnavailable':
                logger.error("Failed to get location key due to API limit or service issue.")
                self.cache['location_key'] = None # Invalidate cache on API limit
                self.cache['last_location_check'] = None
                return None

            # Process successful results
            if location_search_results and isinstance(location_search_results, list) and len(location_search_results) > 0:
                # Log details of the first few results for debugging ambiguity
                for i, loc in enumerate(location_search_results[:3]): # Log top 3 results
                    key = loc.get('Key')
                    name = loc.get('LocalizedName', 'N/A')
                    country = loc.get('Country', {}).get('LocalizedName', 'N/A')
                    admin_area = loc.get('AdministrativeArea', {}).get('LocalizedName', 'N/A')
                    logger.debug(f"  API Result {i}: Key={key}, Name={name}, AdminArea={admin_area}, Country={country}")

                # Assume the first result is the most relevant one
                selected_location = location_search_results[0]
                location_key = selected_location.get('Key')
                location_name = selected_location.get('LocalizedName', 'N/A')
                country = selected_location.get('Country', {}).get('LocalizedName', 'N/A')

                if location_key:
                    logger.info(f"Selected location key: {location_key} for {location_name}, {country}")
                    self.cache['location_key'] = location_key
                    self.cache['last_location_check'] = current_time
                    return location_key
                else:
                    logger.error(f"First location result for '{self.location_query}' missing 'Key'. Response: {selected_location}")
                    self.cache['location_key'] = None
                    self.cache['last_location_check'] = None
                    return None
            else:
                logger.error(f"Could not find any location for query: '{self.location_query}'. API Response: {location_search_results}")
                self.cache['location_key'] = None # Invalidate cache on failure
                self.cache['last_location_check'] = None
                return None
        except Exception as e:
            # Catch unexpected errors during the process
            logger.error(f"Unexpected error fetching location key: {e}", exc_info=True)
            # Don't invalidate cache on potentially temporary errors, return current state
            return self.cache.get('location_key')

    def _get_current_aqi(self, location_key: str) -> Optional[Dict[str, Any]]:
        """
        Internal helper to fetch current Air Quality Index (AQI) data.

        Uses the AccuWeather Indices API (Index 31 for Air Quality).
        Note: AQI caching is tied to the main weather update cycle.

        Args:
            location_key: The AccuWeather location key.

        Returns:
            A dictionary {'Value': int, 'Category': str} if successful, otherwise None.
        """
        if self.use_mock_data or not self.connection_status:
            # Mock data handled by the calling function (get_current_weather)
            return None

        if not self.api_key:
            logger.error("Cannot fetch AQI: AccuWeather API key is missing.")
            return None

        try:
            # AccuWeather Index 31 corresponds to Air Quality (AQI)
            aqi_index_id = 31
            url = f"{self.base_url}/indices/v1/daily/1day/{location_key}/{aqi_index_id}"
            params = {
                'apikey': self.api_key,
                'language': self.language,
            }
            logger.info(f"Fetching AQI (Index {aqi_index_id}) for location key: {location_key} (Lang: {self.language})")
            aqi_data_list = fetch_with_retry(url, params)
            logger.debug(f"Raw AQI API response: {aqi_data_list}") # Log the raw response

            # Handle potential API limit error
            if isinstance(aqi_data_list, dict) and aqi_data_list.get('Code') == 'ServiceUnavailable':
                logger.warning("Could not fetch AQI due to API limit or service issue.")
                return None

            # Process successful response (expected as a list)
            if aqi_data_list and isinstance(aqi_data_list, list) and len(aqi_data_list) > 0:
                # AQI data is typically the first item in the list for the 1-day index
                aqi_data = aqi_data_list[0]
                aqi_value = aqi_data.get('Value')
                aqi_category = aqi_data.get('Category')
                logger.info(f"AQI data received: Value={aqi_value}, Category='{aqi_category}'")
                # Basic validation
                if isinstance(aqi_value, (int, float)) and isinstance(aqi_category, str):
                     # No separate AQI cache timestamp; tied to 'last_weather_update'
                    return {'Value': aqi_value, 'Category': aqi_category}
                else:
                     logger.warning(f"Received unexpected AQI data format: {aqi_data}")
                     return None
            else:
                logger.warning(f"No valid AQI data found in response for location key {location_key}. Response: {aqi_data_list}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error fetching AQI data: {e}", exc_info=True)
            return None

    def get_current_weather(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get current weather conditions and AQI from AccuWeather.

        Handles caching, mock data, API limits, and combines results.

        Args:
            force_refresh: If True, bypass cache and force API fetch.

        Returns:
            A dictionary containing the fetch status and data:
            {
                'data': Dict[str, Any], # Weather data (see structure below) or mock data
                'connection_status': bool, # Current internet connection status
                'api_status': str # 'ok', 'limit_reached', 'error', 'offline', 'mock'
            }

            The 'data' dictionary structure:
            {
                'temperature': Optional[float], # Celsius
                'humidity': Optional[int], # Percentage
                'condition': Optional[str], # Weather text description
                'icon_url': Optional[str], # Original AccuWeather icon URL (unused by GUI now)
                'icon_path': Optional[str], # Local path to downloaded icon (unused by GUI now)
                'observation_time': Optional[str], # ISO 8601 format timestamp
                'air_quality_index': Optional[int], # AQI numeric value
                'air_quality_category': Optional[str] # AQI category text (e.g., "Good")
            }
        """
        current_time = time.time()
        has_connection = self.connection_status
        api_status = 'ok' # Default assumption

        # Check cache validity (uses WEATHER_UPDATE_INTERVAL_MINUTES from config)
        cache_duration = config.WEATHER_UPDATE_INTERVAL_MINUTES * 60
        if (not force_refresh and
                self.cache['current'] and
                self.cache['last_weather_update'] and
                (current_time - self.cache['last_weather_update']) < cache_duration):
            logger.debug("Returning cached current weather data.")
            # Return cached data; connection status is current, api_status assumes last fetch was ok
            return {
                'data': self.cache['current'].copy(), # Return a copy
                'connection_status': has_connection,
                'api_status': 'ok'
            }

        # Use mock data if configured or no internet connection
        if self.use_mock_data or not has_connection:
            if not has_connection:
                logger.warning("No internet connection; using mock or cached current weather.")
                api_status = 'offline'
            else: # use_mock_data is True
                logger.info("Using mock current weather data.")
                api_status = 'mock'

            mock_data = self._get_mock_current_weather()
            # Update cache with mock data only if no real data exists yet
            if not self.cache['current']:
                 self.cache['current'] = mock_data.copy()
                 # Do not set 'last_weather_update' for mock data to allow real fetch later
            return {
                'data': mock_data,
                'connection_status': has_connection,
                'api_status': api_status
            }

        # --- Fetch Real Data ---
        location_key = self._get_location_key()
        if not location_key:
            logger.error("Failed to get location key; cannot fetch current weather.")
            api_status = 'error'
            # Fallback to cache or mock data if location key fails
            fallback_data = self.cache['current'] or self._get_mock_current_weather()
            return {
                'data': fallback_data.copy(),
                'connection_status': has_connection, # Connection might be ok, but location failed
                'api_status': api_status
            }

        # Fetch current conditions
        try:
            url = f"{self.base_url}/currentconditions/v1/{location_key}"
            params = {
                'apikey': self.api_key,
                'language': self.language,
                'details': 'true'  # Include humidity, etc.
            }
            logger.info(f"Fetching current conditions for location key: {location_key}")
            current_conditions_list = fetch_with_retry(url, params)

            # Handle API limit error
            if isinstance(current_conditions_list, dict) and current_conditions_list.get('Code') == 'ServiceUnavailable':
                logger.error("Failed to fetch current weather due to API limit. Using cache/mock.")
                api_status = 'limit_reached'
                fallback_data = self.cache['current'] or self._get_mock_current_weather()
                return {
                    'data': fallback_data.copy(),
                    'connection_status': True, # Connection was ok
                    'api_status': api_status
                }

            # Validate response structure
            if not current_conditions_list or not isinstance(current_conditions_list, list) or len(current_conditions_list) == 0:
                logger.error(f"Invalid current conditions data received. Response: {current_conditions_list}")
                api_status = 'error'
                fallback_data = self.cache['current'] or self._get_mock_current_weather()
                return {
                    'data': fallback_data.copy(),
                    'connection_status': True, # Connection likely ok
                    'api_status': api_status
                }

            # --- Parse Current Conditions ---
            current_data = current_conditions_list[0]
            temp_metric = current_data.get('Temperature', {}).get('Metric', {})
            # Note: icon_url and icon_path are fetched but no longer used by the GUI
            icon_number = current_data.get('WeatherIcon')
            icon_url = f"https://developer.accuweather.com/sites/default/files/{icon_number:02d}-s.png" if icon_number else None
            # icon_path = download_image(...) # Download logic removed, handled by IconHandler if needed

            parsed_data = {
                'temperature': temp_metric.get('Value'),
                'humidity': current_data.get('RelativeHumidity'),
                'condition': current_data.get('WeatherText'),
                'icon_url': icon_url, # Keep for potential future use/debugging
                'icon_path': None, # No longer downloaded here
                'observation_time': current_data.get('LocalObservationDateTime'),
                'air_quality_index': None, # Fetched separately
                'air_quality_category': None # Fetched separately
            }

            # --- Fetch AQI Data ---
            # AQI fetch is best-effort; failure doesn't prevent returning weather data
            aqi_result = self._get_current_aqi(location_key)
            if aqi_result:
                parsed_data['air_quality_index'] = aqi_result.get('Value')
                parsed_data['air_quality_category'] = aqi_result.get('Category')
            # --- End Fetch AQI ---

            # Update cache with the combined data
            self.cache['current'] = parsed_data.copy()
            self.cache['last_weather_update'] = current_time # Update timestamp for successful fetch
            logger.info("Successfully fetched and parsed current weather and AQI.")

            return {
                'data': parsed_data,
                'connection_status': True,
                'api_status': 'ok'
            }

        except Exception as e:
            logger.error(f"Unexpected error fetching current weather: {e}", exc_info=True)
            api_status = 'error'
            fallback_data = self.cache['current'] or self._get_mock_current_weather()
            return {
                'data': fallback_data.copy(),
                'connection_status': has_connection, # Original connection status before error
                'api_status': api_status
            }

    def get_forecast(self, days: int = 1, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get daily forecast data from AccuWeather (up to 5 days).

        Handles caching, mock data, and API limits. Always fetches the 5-day
        forecast from the API if making a live call, but mock data generation
        respects the `days` parameter.

        Args:
            days: Number of forecast days requested (used for mock data).
                  API always fetches 5 days. Defaults to 1.
            force_refresh: If True, bypass cache and force API fetch.

        Returns:
            A dictionary containing the fetch status and data:
            {
                'data': List[Dict[str, Any]], # List of daily forecast dicts or mock data
                'connection_status': bool, # Current internet connection status
                'api_status': str # 'ok', 'limit_reached', 'error', 'offline', 'mock'
            }

            Each dictionary in the 'data' list structure:
            {
                'date': Optional[str], # ISO 8601 format timestamp for the forecast day
                'max_temp': Optional[float], # Max temperature Celsius
                'min_temp': Optional[float], # Min temperature Celsius
                'condition': Optional[str], # Day weather text description
                'icon_code': Optional[int] # AccuWeather icon code for the day
            }
        """
        requested_days = days # Keep requested days for mock data logic
        endpoint_days = 5 # AccuWeather API endpoint provides 5 days
        current_time = time.time()
        has_connection = self.connection_status
        api_status = 'ok'

        # Check cache validity (uses same timestamp as current weather)
        cache_duration = config.WEATHER_UPDATE_INTERVAL_MINUTES * 60
        if (not force_refresh and
                self.cache['forecast'] and
                self.cache['last_weather_update'] and
                (current_time - self.cache['last_weather_update']) < cache_duration):
            logger.debug("Returning cached forecast data.")
            return {
                'data': self.cache['forecast'], # Return cached list
                'connection_status': has_connection,
                'api_status': 'ok'
            }

        # Use mock data if configured or no internet connection
        if self.use_mock_data or not has_connection:
            if not has_connection:
                logger.warning("No internet connection; using mock or cached forecast.")
                api_status = 'offline'
            else:
                logger.info("Using mock forecast data.")
                api_status = 'mock'

            mock_data = self._get_mock_forecast(requested_days) # Generate requested days
            if not self.cache['forecast']:
                 self.cache['forecast'] = mock_data
                 # Do not set 'last_weather_update' for mock data
            return {
                'data': mock_data,
                'connection_status': has_connection,
                'api_status': api_status
            }

        # --- Fetch Real Data ---
        location_key = self._get_location_key()
        if not location_key:
            logger.error("Failed to get location key; cannot fetch forecast.")
            api_status = 'error'
            fallback_data = self.cache['forecast'] or self._get_mock_forecast(requested_days)
            return {
                'data': fallback_data,
                'connection_status': has_connection,
                'api_status': api_status
            }

        # Fetch 5-day forecast
        try:
            url = f"{self.base_url}/forecasts/v1/daily/{endpoint_days}day/{location_key}"
            params = {
                'apikey': self.api_key,
                'language': self.language,
                'details': 'true', # Include RealFeel, wind etc. (though not used currently)
                'metric': 'true'  # Request Celsius
            }
            logger.info(f"Fetching {endpoint_days}-day forecast for location key: {location_key}")
            forecast_response = fetch_with_retry(url, params)

            # Handle API limit error
            if isinstance(forecast_response, dict) and forecast_response.get('Code') == 'ServiceUnavailable':
                logger.error("Failed to fetch forecast due to API limit. Using cache/mock.")
                api_status = 'limit_reached'
                fallback_data = self.cache['forecast'] or self._get_mock_forecast(requested_days)
                return {
                    'data': fallback_data,
                    'connection_status': True,
                    'api_status': api_status
                }

            # Validate response structure
            if not forecast_response or 'DailyForecasts' not in forecast_response:
                logger.error(f"Invalid forecast data received. Response: {forecast_response}")
                api_status = 'error'
                fallback_data = self.cache['forecast'] or self._get_mock_forecast(requested_days)
                return {
                    'data': fallback_data,
                    'connection_status': True,
                    'api_status': api_status
                }

            # --- Parse Forecast Data ---
            parsed_forecast_days: List[Dict[str, Any]] = []
            for day_data in forecast_response.get('DailyForecasts', []):
                temp_info = day_data.get('Temperature', {})
                day_info = day_data.get('Day', {}) # Use daytime info for simplicity
                # night_info = day_data.get('Night', {}) # Available if needed

                day_icon_num = day_info.get('Icon') # Integer icon code

                parsed_forecast_days.append({
                    'date': day_data.get('Date'), # ISO 8601 format
                    'max_temp': temp_info.get('Maximum', {}).get('Value'),
                    'min_temp': temp_info.get('Minimum', {}).get('Value'),
                    'condition': day_info.get('IconPhrase'), # Text description for day
                    'icon_code': day_icon_num # Integer code for icon handler
                })

            # Update cache
            self.cache['forecast'] = parsed_forecast_days
            # Use the same timestamp as current weather if fetched together or forced refresh
            if not self.cache['last_weather_update'] or force_refresh:
                 self.cache['last_weather_update'] = current_time

            logger.info(f"Successfully fetched and parsed {len(parsed_forecast_days)}-day forecast.")

            return {
                'data': parsed_forecast_days,
                'connection_status': True,
                'api_status': 'ok'
            }

        except Exception as e:
            logger.error(f"Unexpected error fetching forecast: {e}", exc_info=True)
            api_status = 'error'
            fallback_data = self.cache['forecast'] or self._get_mock_forecast(requested_days)
            return {
                'data': fallback_data,
                'connection_status': has_connection,
                'api_status': api_status
            }

    # --- Mock Data Generation ---

    def _get_mock_current_weather(self) -> Dict[str, Any]:
        """Generate mock current weather data for testing."""
        logger.debug("Generating mock current weather data.")
        # Use icon codes consistent with AccuWeather mapping
        mock_icon_num = random.choice([1, 2, 3, 4, 6, 7, 12, 15, 18, 33, 34])
        # Note: icon_url and icon_path are included for potential debugging but not used by GUI
        mock_icon_url = f"mock://developer.accuweather.com/sites/default/files/{mock_icon_num:02d}-s.png"
        mock_icon_path = f"mock/path/to/{mock_icon_num:02d}-s.png"

        return {
            'temperature': round(random.uniform(5, 30), 1), # Wider range
            'humidity': random.randint(30, 90),
            'condition': random.choice([
                'Sunny', 'Mostly Sunny', 'Partly Cloudy', 'Cloudy', 'Showers',
                'Rain', 'Thunderstorms', 'Clear', 'Mostly Clear'
            ]),
            'icon_url': mock_icon_url,
            'icon_path': mock_icon_path,
            'observation_time': datetime.now().isoformat(),
            'air_quality_index': random.randint(10, 150),
            'air_quality_category': random.choice([
                "Good", "Moderate", "Unhealthy for Sensitive Groups"
            ]),
        }

    def _get_mock_forecast(self, days: int = 1) -> List[Dict[str, Any]]:
        """Generate a list of mock daily forecast data."""
        logger.debug(f"Generating mock forecast for {days} day(s).")
        forecast_list = []
        base_date = datetime.now()
        # Use a wider range of realistic conditions and corresponding icon codes
        mock_conditions = [
            ('Sunny', 1), ('Mostly Sunny', 2), ('Partly Cloudy', 3),
            ('Intermittent Clouds', 4), ('Mostly Cloudy', 6), ('Cloudy', 7),
            ('Showers', 12), ('T-Storms', 15), ('Rain', 18), ('Clear', 33),
            ('Mostly Clear', 34)
        ]

        for i in range(days):
            current_date = base_date + timedelta(days=i)
            condition_text, icon_code = random.choice(mock_conditions)
            max_temp = round(20.0 + random.uniform(-5, 10), 1)
            min_temp = round(max_temp - random.uniform(5, 10), 1)

            forecast_list.append({
                'date': current_date.strftime('%Y-%m-%dT%H:%M:%S%z'), # Mock ISO format
                'max_temp': max_temp,
                'min_temp': min_temp,
                'condition': condition_text,
                'icon_code': icon_code
            })
        return forecast_list
