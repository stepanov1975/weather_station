"""
AccuWeather API Service Client for the Weather Display Application.

This module defines the `AccuWeatherClient` class, which serves as the primary
interface for retrieving weather data from the AccuWeather API. It encapsulates
the logic for making API requests, handling responses, managing API keys,
caching results, and providing mock data for testing or offline scenarios.

Key functionalities include:
- Fetching the AccuWeather-specific 'location key' based on a city/country query,
  utilizing both persistent file caching and in-memory caching for efficiency.
- Retrieving current weather conditions (temperature, humidity, text description).
- Fetching the Air Quality Index (AQI) using the AccuWeather Indices API.
- Retrieving multi-day forecasts (currently fetches 5 days from the API).
- Implementing time-based caching for weather and forecast data to minimize
  API calls and respect usage limits, based on intervals defined in `config.py`.
- Gracefully handling potential API errors, including rate limits ('ServiceUnavailable'),
  using a retry mechanism (`fetch_with_retry` helper).
- Checking for internet connectivity before attempting live API calls.
- Generating realistic mock data for current weather and forecasts when configured
  (`config.USE_MOCK_DATA`) or when the API key is missing.
- Returning data in a standardized dictionary format, including status indicators
  ('connection_status', 'api_status') alongside the actual weather 'data'.
"""

# Standard library imports
import time
import random
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

# Local application imports
from .. import config # Access API keys, URLs, intervals, language settings
from ..utils.helpers import fetch_with_retry, check_internet_connection # API call helper and connectivity check
# Import translation functions if needed for error messages or logging
from ..utils.localization import get_translation # Potentially for user-facing errors
# translate_aqi_category is used by the GUI, not directly here.

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

# --- Location Cache File Configuration ---
# Define the path for the persistent location key cache file.
# This file stores the last successfully fetched location key and timestamp
# to avoid repeated API calls for location searching, which often have stricter limits.
# It's placed in the project root directory (one level above 'weather_display' package).
try:
    _MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(_MODULE_DIR)) # Assumes services/ is inside weather_display/
    if not os.path.basename(_PROJECT_ROOT): # Handle edge case if running from root directly
         _PROJECT_ROOT = os.path.dirname(_MODULE_DIR)
    LOCATION_CACHE_FILE = os.path.join(_PROJECT_ROOT, "location_cache.json")
    logger.debug(f"Location cache file path set to: {LOCATION_CACHE_FILE}")
except Exception as e:
    logger.error(f"Error determining project root for location cache file: {e}. Using current dir as fallback.")
    LOCATION_CACHE_FILE = "location_cache.json" # Fallback path


# --- Expected Cache Structure (Informational) ---
# This describes the structure of the `self.cache` dictionary used for in-memory caching.
# {
#     'location_key': Optional[str],          # AccuWeather location key
#     'current': Optional[Dict[str, Any]],    # Parsed current weather data
#     'forecast': Optional[List[Dict[str, Any]]], # Parsed forecast data list
#     'last_location_check': Optional[float], # Timestamp of last location key fetch/check
#     'last_weather_update': Optional[float]  # Timestamp of last current/forecast fetch
# }


class AccuWeatherClient:
    """
    Client for interacting with the AccuWeather weather API endpoints.

    Manages API key handling, fetches location keys (with caching), retrieves
    current weather conditions, daily forecasts, and Air Quality Index (AQI).
    Implements in-memory caching for weather/forecast data based on configured
    update intervals and persistent file caching for the location key. Provides
    mock data generation capabilities for development and offline use.

    Handles API request retries and common error conditions like rate limits.

    Attributes:
        api_key (Optional[str]): The AccuWeather API key used for requests. Determined
            based on constructor argument, environment variable, or config file.
        location_query (str): The geographical location query string (e.g., "Hadera,Israel")
            used to find the AccuWeather location key.
        base_url (str): The base URL for AccuWeather API endpoints (from config).
        language (str): The language code (e.g., "en-us") requested for API responses
            (from config).
        cache (Dict[str, Any]): Internal dictionary holding cached data (location key,
            current weather, forecast) and their last update timestamps.
        use_mock_data (bool): If True, the client will generate and return mock data
            instead of making live API calls. Determined by `config.USE_MOCK_DATA`
            or if the `api_key` is missing.
        _connection_status (bool): Internal cache of the last known internet connection
            status. Refreshed via the `connection_status` property.
    """

    # Cache validity durations (in seconds)
    _LOCATION_KEY_CACHE_DURATION: int = 24 * 60 * 60  # 24 hours for location key cache

    def __init__(self, api_key: Optional[str] = None, location_query: Optional[str] = None):
        """
        Initializes the AccuWeatherClient instance.

        Sets up API credentials, location, base URL, language, and initializes
        the cache. Determines whether to operate in mock data mode.

        Args:
            api_key (Optional[str]): The AccuWeather API key. If provided, it takes
                precedence. If None, the client attempts to read it from the
                `ACCUWEATHER_API_KEY` environment variable or the `config.py` file.
            location_query (Optional[str]): The location query string (e.g., "City,Country").
                If None, reads the default location from `config.LOCATION`.
        """
        # Determine API Key: Constructor arg > Environment Var > Config File
        env_api_key = os.environ.get('ACCUWEATHER_API_KEY')
        self.api_key: Optional[str] = api_key or env_api_key or config.ACCUWEATHER_API_KEY
        if api_key:
             logger.info("Using AccuWeather API key provided via constructor argument.")
        elif env_api_key:
             logger.info("Using AccuWeather API key from ACCUWEATHER_API_KEY environment variable.")
        elif config.ACCUWEATHER_API_KEY:
             logger.info("Using AccuWeather API key from config.py file.")
        else:
             logger.warning("AccuWeather API key not found in args, environment, or config.")

        # Determine Location Query: Constructor arg > Config File
        self.location_query: str = location_query or config.LOCATION
        # Load other settings from config
        self.base_url: str = config.ACCUWEATHER_BASE_URL
        self.language: str = config.ACCUWEATHER_LANGUAGE

        logger.info(f"AccuWeatherClient initialized:")
        logger.info(f"  Location Query: '{self.location_query}'")
        logger.info(f"  API Language: '{self.language}'")
        logger.info(f"  API Key Present: {'Yes' if self.api_key else 'No'}")

        # Initialize in-memory cache structure
        self.cache: Dict[str, Any] = {
            'location_key': None,
            'current': None,
            'forecast': None,
            'last_location_check': None,
            'last_weather_update': None,
            # AQI is fetched with current weather, uses 'last_weather_update' timestamp
        }
        logger.debug("Initialized empty in-memory cache.")

        # Determine if mock data should be used (explicitly configured or no API key)
        self.use_mock_data: bool = config.USE_MOCK_DATA or not self.api_key
        if self.use_mock_data:
            mode = "explicitly enabled in config" if config.USE_MOCK_DATA else "API key is missing"
            logger.warning(f"AccuWeatherClient running in MOCK DATA mode ({mode}). No live API calls will be made.")

        # Perform an initial internet connection check
        self._connection_status: bool = check_internet_connection()
        logger.info(f"Initial internet connection status: {'Connected' if self._connection_status else 'Disconnected'}")

    @property
    def connection_status(self) -> bool:
        """
        Checks and returns the current internet connection status.

        This property re-evaluates the connection status each time it's accessed,
        providing a near real-time check.

        Returns:
            bool: True if an internet connection is detected, False otherwise.
        """
        # Re-check connection status dynamically
        self._connection_status = check_internet_connection()
        if not self._connection_status:
             logger.debug("Property access: Internet connection check failed.")
        return self._connection_status

    def _is_cache_valid(self, cache_key: str, duration_seconds: float) -> bool:
        """
        Checks if a specific entry in the in-memory cache is still valid based on time.

        Args:
            cache_key (str): The key of the cache entry to check (e.g., 'current', 'forecast').
                             It assumes a corresponding timestamp key exists named
                             `f"last_{cache_key}_update"`.
            duration_seconds (float): The maximum allowed age of the cache entry in seconds.

        Returns:
            bool: True if the cache entry exists, has a valid timestamp, and is within
                  the specified duration; False otherwise.
        """
        timestamp_key = f"last_{cache_key}_update" # Assumes naming convention
        cache_entry = self.cache.get(cache_key)
        last_update_time = self.cache.get(timestamp_key)

        if cache_entry is not None and last_update_time is not None:
            is_valid = (time.time() - last_update_time) < duration_seconds
            logger.debug(f"Cache check for '{cache_key}': Exists=True, Timestamp={last_update_time}, Duration={duration_seconds}, Valid={is_valid}")
            return is_valid
        else:
            logger.debug(f"Cache check for '{cache_key}': Exists=False or Timestamp=None. Invalid.")
            return False

    def _get_location_key(self, force_refresh: bool = False) -> Optional[str]:
        """
        Retrieves the AccuWeather location key for the configured `location_query`.

        Implements a multi-level caching strategy:
        1. Checks persistent file cache (`location_cache.json`).
        2. Checks in-memory cache (`self.cache['location_key']`).
        3. If no valid cache entry is found (or `force_refresh` is True), attempts
           to fetch the key from the AccuWeather Locations API.
        4. Saves successfully fetched keys to both caches.
        Handles mock data mode and lack of internet connection by returning a mock key.

        Args:
            force_refresh (bool): If True, bypasses all caches and forces a new
                                  API request. Defaults to False.

        Returns:
            Optional[str]: The AccuWeather location key string if found or generated
                           (mock), or None if fetching fails and no valid cache exists.
        """
        current_time = time.time()
        cache_duration = self._LOCATION_KEY_CACHE_DURATION

        # --- 1. Check Persistent File Cache ---
        if not force_refresh:
            logger.debug(f"Checking persistent location key cache file: {LOCATION_CACHE_FILE}")
            try:
                if os.path.exists(LOCATION_CACHE_FILE):
                    with open(LOCATION_CACHE_FILE, 'r') as f:
                        file_cache = json.load(f)
                    cached_key = file_cache.get('location_key')
                    cached_time = file_cache.get('timestamp')

                    # Validate file cache entry
                    if cached_key and cached_time and (current_time - cached_time) < cache_duration:
                        logger.info(f"Using location key '{cached_key}' from valid file cache.")
                        # Update in-memory cache as well for consistency
                        self.cache['location_key'] = cached_key
                        self.cache['last_location_check'] = cached_time
                        return cached_key
                    else:
                        logger.debug("Location key file cache expired or invalid content.")
                else:
                    logger.debug("Location key file cache does not exist.")
            except (IOError, json.JSONDecodeError, TypeError, KeyError) as e:
                logger.warning(f"Error reading or parsing location cache file '{LOCATION_CACHE_FILE}': {e}. Will check memory cache or fetch.")
                # Continue to check in-memory cache or fetch

        # --- 2. Check In-Memory Cache ---
        # This check runs if file cache was invalid, missing, errored, or refresh forced initially but file check skipped
        if not force_refresh and self.cache['location_key']:
             # Check timestamp validity for in-memory cache
             last_check = self.cache.get('last_location_check')
             if last_check and (current_time - last_check) < cache_duration:
                  logger.debug(f"Using location key '{self.cache['location_key']}' from valid in-memory cache.")
                  return self.cache['location_key']
             else:
                  logger.debug("In-memory location key cache expired.")

        # --- 3. Handle Mock Data / No Connection ---
        # If we reach here, no valid cache was found or refresh was forced
        if self.use_mock_data:
            logger.info("Using mock location key (mock data mode enabled).")
            mock_key = "mock_location_key_12345"
            self.cache['location_key'] = mock_key
            self.cache['last_location_check'] = current_time # Update timestamp even for mock
            return mock_key
        if not self.connection_status:
             logger.warning("No internet connection. Cannot fetch location key. Returning last known cached key or None.")
             # Return potentially stale cache key if available, otherwise None
             return self.cache.get('location_key')

        # --- 4. Fetch from API ---
        logger.info("Fetching location key from AccuWeather API...")
        if not self.api_key:
            logger.error("Cannot fetch location key: AccuWeather API key is missing.")
            return None # Cannot proceed without API key

        try:
            url = f"{self.base_url}/locations/v1/cities/search"
            params = {
                'apikey': self.api_key,
                'q': self.location_query,
                'language': self.language # Use configured language
            }
            logger.info(f"API Request: GET {url} with query='{self.location_query}', lang='{self.language}'")
            # Use helper function that handles retries and basic error checking
            location_search_results = fetch_with_retry(url, params)

            # Handle specific API limit error returned by fetch_with_retry
            if isinstance(location_search_results, dict) and location_search_results.get('Code') == 'ServiceUnavailable':
                logger.error("Failed to get location key: AccuWeather API limit reached or service unavailable.")
                # Invalidate caches on API limit error
                self.cache['location_key'] = None
                self.cache['last_location_check'] = None
                if os.path.exists(LOCATION_CACHE_FILE): # Remove potentially invalid file cache
                     try: os.remove(LOCATION_CACHE_FILE)
                     except OSError as e: logger.warning(f"Could not remove expired location cache file: {e}")
                return None

            # Process successful results (expected list)
            if location_search_results and isinstance(location_search_results, list) and len(location_search_results) > 0:
                # Log details of the first few results for debugging potential ambiguity
                log_limit = min(len(location_search_results), 3) # Log max 3 results
                logger.debug(f"API returned {len(location_search_results)} location(s). Top {log_limit}:")
                for i, loc in enumerate(location_search_results[:log_limit]):
                    key = loc.get('Key', 'N/A')
                    name = loc.get('LocalizedName', 'N/A')
                    country = loc.get('Country', {}).get('LocalizedName', 'N/A')
                    admin_area = loc.get('AdministrativeArea', {}).get('LocalizedName', 'N/A')
                    logger.debug(f"  Result {i}: Key={key}, Name='{name}', AdminArea='{admin_area}', Country='{country}'")

                # Assume the first result is the most relevant one
                selected_location = location_search_results[0]
                location_key = selected_location.get('Key')
                location_name = selected_location.get('LocalizedName', 'N/A') # For logging
                country = selected_location.get('Country', {}).get('LocalizedName', 'N/A') # For logging

                if location_key:
                    logger.info(f"Successfully fetched location key: '{location_key}' for '{location_name}, {country}'.")
                    # Update in-memory cache
                    self.cache['location_key'] = location_key
                    self.cache['last_location_check'] = current_time

                    # Save to persistent file cache
                    try:
                        cache_data_to_save = {'location_key': location_key, 'timestamp': current_time}
                        with open(LOCATION_CACHE_FILE, 'w') as f:
                            json.dump(cache_data_to_save, f, indent=4) # Add indent for readability
                        logger.info(f"Saved location key to persistent file cache: {LOCATION_CACHE_FILE}")
                    except IOError as e:
                        logger.error(f"Error writing location key to file cache '{LOCATION_CACHE_FILE}': {e}")

                    return location_key
                else:
                    # This case should be rare if the API returns results
                    logger.error(f"First location result for '{self.location_query}' is missing the 'Key' field. Response: {selected_location}")
                    self.cache['location_key'] = None # Invalidate cache
                    self.cache['last_location_check'] = None
                    return None
            else:
                # Handle cases where API returns empty list or unexpected format
                logger.error(f"Could not find any location matching query: '{self.location_query}'. API Response: {location_search_results}")
                self.cache['location_key'] = None # Invalidate cache
                self.cache['last_location_check'] = None
                return None
        except Exception as e:
            # Catch any other unexpected errors during the API call or processing
            logger.error(f"Unexpected error fetching location key: {e}", exc_info=True)
            # Don't invalidate cache on potentially temporary errors, return current cached value if available
            return self.cache.get('location_key')

    def _get_current_aqi(self, location_key: str) -> Optional[Dict[str, Any]]:
        """
        Internal helper method to fetch the current Air Quality Index (AQI).

        Uses the AccuWeather Indices API (specifically Index ID 31 for Air Quality)
        for the given location key. This is called internally by `get_current_weather`.
        AQI data shares the same caching timestamp as the main current weather data.

        Args:
            location_key (str): The AccuWeather location key for the desired location.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the AQI 'Value' (int/float)
                                      and 'Category' (str) if the fetch is successful.
                                      Returns None if mock data is enabled, no connection,
                                      API key is missing, fetch fails, or data is invalid.
        """
        # Skip if using mock data or no connection (handled by caller)
        if self.use_mock_data or not self.connection_status:
            logger.debug("Skipping AQI fetch (mock data or no connection).")
            return None

        if not self.api_key:
            logger.error("Cannot fetch AQI: AccuWeather API key is missing.")
            return None
        if not location_key: # Should not happen if called correctly
             logger.error("Cannot fetch AQI: Location key is missing.")
             return None

        logger.info(f"Fetching AQI data for location key: {location_key}")
        try:
            # AccuWeather Index 31 corresponds to Air Quality (AQI)
            aqi_index_id = 31
            # Use the 1-day daily indices endpoint
            url = f"{self.base_url}/indices/v1/daily/1day/{location_key}/{aqi_index_id}"
            params = {
                'apikey': self.api_key,
                'language': self.language, # Use configured language
            }
            logger.debug(f"API Request: GET {url} (Index: {aqi_index_id}, Lang: {self.language})")
            aqi_data_list = fetch_with_retry(url, params)
            logger.debug(f"Raw AQI API response received: {aqi_data_list}")

            # Handle potential API limit error returned by fetch_with_retry
            if isinstance(aqi_data_list, dict) and aqi_data_list.get('Code') == 'ServiceUnavailable':
                logger.warning("Could not fetch AQI due to API limit or service issue.")
                # Do not return data, let the main weather function handle overall status
                return None

            # Process successful response (expected as a list)
            if aqi_data_list and isinstance(aqi_data_list, list) and len(aqi_data_list) > 0:
                # AQI data is typically the first item in the list for the 1-day index endpoint
                aqi_data = aqi_data_list[0]
                aqi_value = aqi_data.get('Value')
                aqi_category = aqi_data.get('Category')
                logger.info(f"AQI data received: Value={aqi_value}, Category='{aqi_category}'")

                # Basic validation of received data types
                if isinstance(aqi_value, (int, float)) and isinstance(aqi_category, str):
                    # Return the relevant AQI information
                    return {'Value': aqi_value, 'Category': aqi_category}
                else:
                     logger.warning(f"Received unexpected AQI data format or types. Value: {aqi_value} (Type: {type(aqi_value)}), Category: {aqi_category} (Type: {type(aqi_category)}). Full data: {aqi_data}")
                     return None # Treat invalid format as failure
            else:
                # Handle cases where the response is empty or not the expected list format
                logger.warning(f"No valid AQI data found in the API response list for location key {location_key}. Response: {aqi_data_list}")
                return None
        except Exception as e:
            # Catch any other unexpected errors during the AQI fetch
            logger.error(f"Unexpected error fetching AQI data: {e}", exc_info=True)
            return None # Return None on error

    def get_current_weather(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Gets the current weather conditions, including AQI, from AccuWeather.

        Checks the in-memory cache first. If the cache is invalid or `force_refresh`
        is True, it attempts to fetch fresh data from the API. Handles mock data
        mode, lack of internet connection, missing location key, and API errors.
        Combines results from the current conditions endpoint and the AQI endpoint.

        Args:
            force_refresh (bool): If True, bypasses the cache check and forces a
                                  new API request. Defaults to False.

        Returns:
            Dict[str, Any]: A dictionary containing the fetch status and data:
            ```json
            {
                "data": {
                    "temperature": Optional[float],       # Celsius
                    "humidity": Optional[int],            # Percentage
                    "condition": Optional[str],           # Weather text description
                    "icon_url": Optional[str],            # Original AccuWeather icon URL (debug)
                    "icon_path": Optional[str],           # Local path (unused)
                    "observation_time": Optional[str],    # ISO 8601 timestamp
                    "air_quality_index": Optional[int],   # AQI numeric value
                    "air_quality_category": Optional[str] # AQI category text (e.g., "Good")
                },
                "connection_status": bool, # True if internet connected, False otherwise
                "api_status": str          # 'ok', 'limit_reached', 'error', 'offline', 'mock'
            }
            ```
            The 'data' dictionary will contain the latest successfully fetched or
            cached data, or mock data if applicable.
        """
        current_time = time.time()
        has_connection = self.connection_status # Check current connection status
        api_status = 'ok' # Assume OK initially

        # --- 1. Check Cache ---
        # Cache duration is based on the configured update interval
        cache_duration = config.ACCUWEATHER_UPDATE_INTERVAL_MINUTES * 60
        if not force_refresh and self._is_cache_valid('current', cache_duration):
            logger.debug("Returning cached current weather data.")
            # Return a copy of the cached data
            return {
                'data': self.cache['current'].copy(),
                'connection_status': has_connection, # Report current connection status
                'api_status': 'ok' # Assume last fetch was ok if cache is valid
            }

        # --- 2. Handle Mock Data / No Connection ---
        if self.use_mock_data:
            logger.info("Using mock current weather data (mock mode enabled).")
            api_status = 'mock'
            mock_data = self._get_mock_current_weather()
            # Update cache with mock data only if no real data exists yet
            # Avoid overwriting real cache with mock data unnecessarily
            if self.cache['current'] is None:
                 self.cache['current'] = mock_data.copy()
                 # Do not set 'last_weather_update' for mock data
            return {
                'data': mock_data,
                'connection_status': has_connection, # Report current connection status
                'api_status': api_status
            }
        if not has_connection:
            logger.warning("No internet connection. Returning last cached current weather or mock data.")
            api_status = 'offline'
            # Return stale cache if available, otherwise generate mock data
            fallback_data = self.cache.get('current') or self._get_mock_current_weather()
            return {
                'data': fallback_data.copy(),
                'connection_status': False,
                'api_status': api_status
            }

        # --- 3. Fetch Real Data ---
        logger.info("Fetching fresh current weather data from AccuWeather API...")
        # Get location key (uses its own caching logic)
        location_key = self._get_location_key(force_refresh=force_refresh) # Force refresh if main refresh forced
        if not location_key:
            logger.error("Failed to get location key; cannot fetch current weather.")
            api_status = 'error'
            # Fallback to cache or mock data if location key fails
            fallback_data = self.cache.get('current') or self._get_mock_current_weather()
            return {
                'data': fallback_data.copy(),
                'connection_status': True, # Connection might be ok, but location failed
                'api_status': api_status
            }

        # --- 4. Fetch Current Conditions API Endpoint ---
        try:
            url = f"{self.base_url}/currentconditions/v1/{location_key}"
            params = {
                'apikey': self.api_key,
                'language': self.language,
                'details': 'true'  # Request details like humidity
            }
            logger.info(f"API Request: GET {url} (Current Conditions)")
            current_conditions_list = fetch_with_retry(url, params)

            # Handle API limit error specifically
            if isinstance(current_conditions_list, dict) and current_conditions_list.get('Code') == 'ServiceUnavailable':
                logger.error("Failed to fetch current weather: API limit reached or service unavailable.")
                api_status = 'limit_reached'
                fallback_data = self.cache.get('current') or self._get_mock_current_weather()
                return {
                    'data': fallback_data.copy(),
                    'connection_status': True, # Connection was ok
                    'api_status': api_status
                }

            # Validate response structure (expecting a list with one item)
            if not current_conditions_list or not isinstance(current_conditions_list, list) or len(current_conditions_list) == 0:
                logger.error(f"Invalid or empty current conditions data received from API. Response: {current_conditions_list}")
                api_status = 'error'
                fallback_data = self.cache.get('current') or self._get_mock_current_weather()
                return {
                    'data': fallback_data.copy(),
                    'connection_status': True, # Connection likely ok, but data invalid
                    'api_status': api_status
                }

            # --- 5. Parse Current Conditions Data ---
            current_data = current_conditions_list[0] # Get the first item from the list
            temp_metric = current_data.get('Temperature', {}).get('Metric', {})
            icon_number = current_data.get('WeatherIcon')
            # Construct icon URL (though not directly used by GUI which uses IconHandler)
            icon_url = f"https://developer.accuweather.com/sites/default/files/{icon_number:02d}-s.png" if isinstance(icon_number, int) else None

            parsed_data = {
                'temperature': temp_metric.get('Value'),
                'humidity': current_data.get('RelativeHumidity'),
                'condition': current_data.get('WeatherText'),
                'icon_url': icon_url, # Keep for debugging/reference
                'icon_path': None, # Icon downloading is handled elsewhere if needed
                'observation_time': current_data.get('LocalObservationDateTime'), # ISO 8601 format
                'air_quality_index': None, # Placeholder, fetched next
                'air_quality_category': None # Placeholder, fetched next
            }
            logger.debug(f"Parsed current conditions: Temp={parsed_data['temperature']}, Humidity={parsed_data['humidity']}, Condition='{parsed_data['condition']}'")

            # --- 6. Fetch AQI Data (Best Effort) ---
            aqi_result = self._get_current_aqi(location_key)
            if aqi_result:
                parsed_data['air_quality_index'] = aqi_result.get('Value')
                parsed_data['air_quality_category'] = aqi_result.get('Category')
                logger.debug(f"Added AQI data: Index={parsed_data['air_quality_index']}, Category='{parsed_data['air_quality_category']}'")
            else:
                 logger.warning("AQI data could not be fetched or was invalid.")
                 # Keep AQI fields as None

            # --- 7. Update Cache and Return ---
            self.cache['current'] = parsed_data.copy() # Store a copy in cache
            self.cache['last_weather_update'] = current_time # Update timestamp
            logger.info("Successfully fetched and parsed current weather and AQI.")

            return {
                'data': parsed_data,
                'connection_status': True, # Connection was successful
                'api_status': 'ok' # API call was successful
            }

        except Exception as e:
            # Catch any other unexpected errors during the process
            logger.error(f"Unexpected error fetching current weather: {e}", exc_info=True)
            api_status = 'error'
            fallback_data = self.cache.get('current') or self._get_mock_current_weather()
            return {
                'data': fallback_data.copy(),
                'connection_status': has_connection, # Report connection status before the error
                'api_status': api_status
            }

    def get_forecast(self, days: int = 1, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Gets the daily weather forecast from AccuWeather.

        Checks the in-memory cache first. If invalid or `force_refresh` is True,
        fetches the 5-day forecast from the API (as the API endpoint provides 5 days).
        Handles mock data, connectivity, location key issues, and API errors.
        Note: The `days` parameter currently only influences mock data generation.

        Args:
            days (int): The number of forecast days requested (primarily for mock data).
                        The live API call always fetches 5 days. Defaults to 1.
            force_refresh (bool): If True, bypasses the cache check and forces a
                                  new API request. Defaults to False.

        Returns:
            Dict[str, Any]: A dictionary containing the fetch status and data:
            ```json
            {
                "data": [
                    { # List item for each forecast day
                        "date": Optional[str],         # ISO 8601 timestamp for the day
                        "max_temp": Optional[float],   # Max temperature Celsius
                        "min_temp": Optional[float],   # Min temperature Celsius
                        "condition": Optional[str],    # Day weather text description
                        "icon_code": Optional[int]     # AccuWeather icon code for the day
                    },
                    ...
                ],
                "connection_status": bool, # True if internet connected, False otherwise
                "api_status": str          # 'ok', 'limit_reached', 'error', 'offline', 'mock'
            }
            ```
            The 'data' list will contain the latest successfully fetched or cached
            forecast data (up to 5 days from API), or mock data for the requested `days`.
        """
        requested_days = days # Store requested days for mock generation if needed
        endpoint_days = 5 # AccuWeather API endpoint provides 5 days
        current_time = time.time()
        has_connection = self.connection_status
        api_status = 'ok'

        # --- 1. Check Cache ---
        # Forecast shares the same cache timestamp as current weather
        cache_duration = config.ACCUWEATHER_UPDATE_INTERVAL_MINUTES * 60
        if not force_refresh and self._is_cache_valid('forecast', cache_duration):
            logger.debug("Returning cached forecast data.")
            # Return a copy of the cached list
            return {
                'data': self.cache['forecast'], # Already a list
                'connection_status': has_connection,
                'api_status': 'ok'
            }

        # --- 2. Handle Mock Data / No Connection ---
        if self.use_mock_data:
            logger.info(f"Using mock forecast data for {requested_days} day(s) (mock mode enabled).")
            api_status = 'mock'
            mock_data = self._get_mock_forecast(requested_days)
            if self.cache['forecast'] is None:
                 self.cache['forecast'] = mock_data
                 # Do not set 'last_weather_update' for mock data
            return {
                'data': mock_data,
                'connection_status': has_connection,
                'api_status': api_status
            }
        if not has_connection:
            logger.warning("No internet connection. Returning last cached forecast or mock data.")
            api_status = 'offline'
            fallback_data = self.cache.get('forecast') or self._get_mock_forecast(requested_days)
            return {
                'data': fallback_data,
                'connection_status': False,
                'api_status': api_status
            }

        # --- 3. Fetch Real Data ---
        logger.info(f"Fetching fresh {endpoint_days}-day forecast data from AccuWeather API...")
        location_key = self._get_location_key(force_refresh=force_refresh)
        if not location_key:
            logger.error("Failed to get location key; cannot fetch forecast.")
            api_status = 'error'
            fallback_data = self.cache.get('forecast') or self._get_mock_forecast(requested_days)
            return {
                'data': fallback_data,
                'connection_status': True, # Connection might be ok
                'api_status': api_status
            }

        # --- 4. Fetch 5-Day Forecast API Endpoint ---
        try:
            # Always fetch the 5-day forecast endpoint
            url = f"{self.base_url}/forecasts/v1/daily/{endpoint_days}day/{location_key}"
            params = {
                'apikey': self.api_key,
                'language': self.language,
                'details': 'false', # Set details to false unless needed (reduces payload size)
                'metric': 'true'  # Request temperatures in Celsius
            }
            logger.info(f"API Request: GET {url} ({endpoint_days}-Day Forecast)")
            forecast_response = fetch_with_retry(url, params)

            # Handle API limit error
            if isinstance(forecast_response, dict) and forecast_response.get('Code') == 'ServiceUnavailable':
                logger.error("Failed to fetch forecast: API limit reached or service unavailable.")
                api_status = 'limit_reached'
                fallback_data = self.cache.get('forecast') or self._get_mock_forecast(requested_days)
                return {
                    'data': fallback_data,
                    'connection_status': True,
                    'api_status': api_status
                }

            # Validate response structure (expecting a dict with 'DailyForecasts' list)
            if not forecast_response or 'DailyForecasts' not in forecast_response or not isinstance(forecast_response['DailyForecasts'], list):
                logger.error(f"Invalid or missing 'DailyForecasts' in forecast response. Response: {forecast_response}")
                api_status = 'error'
                fallback_data = self.cache.get('forecast') or self._get_mock_forecast(requested_days)
                return {
                    'data': fallback_data,
                    'connection_status': True,
                    'api_status': api_status
                }

            # --- 5. Parse Forecast Data ---
            parsed_forecast_days: List[Dict[str, Any]] = []
            raw_forecasts = forecast_response.get('DailyForecasts', [])
            logger.debug(f"Parsing {len(raw_forecasts)} days from forecast response.")
            for day_data in raw_forecasts:
                temp_info = day_data.get('Temperature', {})
                # Use daytime info for icon/phrase for simplicity
                day_info = day_data.get('Day', {})
                # night_info = day_data.get('Night', {}) # Available if needed

                day_icon_num = day_info.get('Icon') # Integer icon code

                parsed_day = {
                    'date': day_data.get('Date'), # ISO 8601 format string
                    'max_temp': temp_info.get('Maximum', {}).get('Value'),
                    'min_temp': temp_info.get('Minimum', {}).get('Value'),
                    'condition': day_info.get('IconPhrase'), # Text description for day
                    'icon_code': day_icon_num # Integer code for icon handler
                }
                parsed_forecast_days.append(parsed_day)
                logger.debug(f"  Parsed forecast day: Date={parsed_day['date']}, Max={parsed_day['max_temp']}, Min={parsed_day['min_temp']}, Cond='{parsed_day['condition']}', Icon={parsed_day['icon_code']}")

            # --- 6. Update Cache and Return ---
            self.cache['forecast'] = parsed_forecast_days # Store the full list
            # Update the shared weather timestamp
            self.cache['last_weather_update'] = current_time
            logger.info(f"Successfully fetched and parsed {len(parsed_forecast_days)}-day forecast.")

            return {
                'data': parsed_forecast_days, # Return the full list fetched
                'connection_status': True,
                'api_status': 'ok'
            }

        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error fetching forecast: {e}", exc_info=True)
            api_status = 'error'
            fallback_data = self.cache.get('forecast') or self._get_mock_forecast(requested_days)
            return {
                'data': fallback_data,
                'connection_status': has_connection, # Report status before error
                'api_status': api_status
            }

    # --- Mock Data Generation Methods ---

    def _get_mock_current_weather(self) -> Dict[str, Any]:
        """
        Generates a dictionary containing mock current weather data.

        Used for testing the UI or running the application offline when
        `use_mock_data` is True or the API key is missing. Provides randomized
        but plausible values.

        Returns:
            Dict[str, Any]: A dictionary mimicking the structure of the 'data'
                            part of the `get_current_weather` return value.
        """
        logger.debug("Generating mock current weather data...")
        # Use realistic icon codes based on AccuWeather's common set
        mock_icon_num = random.choice([1, 2, 3, 4, 6, 7, 12, 15, 18, 33, 34, 35, 38])
        # Construct mock URLs/paths (not used by GUI but good for structure)
        mock_icon_url = f"mock://developer.accuweather.com/sites/default/files/{mock_icon_num:02d}-s.png"
        mock_icon_path = f"mock/path/to/{mock_icon_num:02d}-s.png" # Placeholder

        mock_data = {
            'temperature': round(random.uniform(5.0, 35.0), 1), # Plausible temp range C
            'humidity': random.randint(20, 95), # Plausible humidity range %
            'condition': random.choice([
                'Sunny', 'Mostly Sunny', 'Partly Cloudy', 'Cloudy', 'Intermittent Clouds',
                'Hazy Sunshine', 'Showers', 'Mostly Cloudy w/ Showers',
                'Rain', 'Thunderstorms', 'Clear', 'Mostly Clear', 'Partly Cloudy Night'
            ]),
            'icon_url': mock_icon_url, # Included for structural consistency
            'icon_path': mock_icon_path, # Included for structural consistency
            'observation_time': datetime.now().isoformat(), # Current time as ISO string
            'air_quality_index': random.randint(10, 180), # Plausible AQI range
            'air_quality_category': random.choice([
                "Good", "Moderate", "Unhealthy for Sensitive Groups", "Unhealthy"
            ]),
        }
        logger.debug(f"Generated mock current weather: {mock_data}")
        return mock_data

    def _get_mock_forecast(self, days: int = 1) -> List[Dict[str, Any]]:
        """
        Generates a list of dictionaries containing mock daily forecast data.

        Creates mock data for the specified number of days, starting from the
        current date. Uses randomized but plausible weather conditions,
        temperatures, and icon codes.

        Args:
            days (int): The number of mock forecast days to generate. Defaults to 1.

        Returns:
            List[Dict[str, Any]]: A list where each dictionary represents one
                                  mock forecast day, mimicking the structure of the
                                  'data' list in the `get_forecast` return value.
        """
        logger.debug(f"Generating mock forecast for {days} day(s)...")
        forecast_list: List[Dict[str, Any]] = []
        base_date = datetime.now() # Start forecast from today

        # Define pairs of plausible conditions and their corresponding AccuWeather icon codes
        mock_conditions_icons = [
            ('Sunny', 1), ('Mostly Sunny', 2), ('Partly Sunny', 3),
            ('Intermittent Clouds', 4), ('Hazy Sunshine', 5), ('Mostly Cloudy', 6),
            ('Cloudy', 7), ('Dreary (Overcast)', 8), ('Fog', 11), ('Showers', 12),
            ('Mostly Cloudy w/ Showers', 13), ('Partly Sunny w/ Showers', 14),
            ('T-Storms', 15), ('Mostly Cloudy w/ T-Storms', 16), ('Rain', 18),
            ('Clear', 33), ('Mostly Clear', 34), ('Partly Cloudy', 35),
            ('Intermittent Clouds Night', 36), ('Mostly Cloudy Night', 38)
        ]

        for i in range(days):
            current_date = base_date + timedelta(days=i)
            # Choose a random condition and its icon code
            condition_text, icon_code = random.choice(mock_conditions_icons)
            # Generate plausible temperature range
            max_temp = round(random.uniform(8.0, 38.0), 1) # Wider plausible max range
            min_temp = round(max_temp - random.uniform(4.0, 12.0), 1) # Min is lower than max

            mock_day_data = {
                # Format date as ISO string (mocking timezone as local offset)
                'date': current_date.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'max_temp': max_temp,
                'min_temp': min_temp,
                'condition': condition_text,
                'icon_code': icon_code
            }
            forecast_list.append(mock_day_data)
            logger.debug(f"  Generated mock forecast day {i+1}: {mock_day_data}")

        return forecast_list

# Example usage (if run directly)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # Enable detailed logging for testing
    print("--- Testing AccuWeatherClient ---")

    # Test cases can be added here, e.g.:
    # client = AccuWeatherClient() # Uses config/env API key
    # print("\n--- Getting Location Key ---")
    # key = client._get_location_key(force_refresh=True) # Force fetch
    # print(f"Location Key: {key}")

    # print("\n--- Getting Current Weather ---")
    # weather = client.get_current_weather(force_refresh=True)
    # print(json.dumps(weather, indent=2))

    # print("\n--- Getting Forecast ---")
    # forecast = client.get_forecast(days=3, force_refresh=True)
    # print(json.dumps(forecast, indent=2))

    print("\n--- Testing with Mock Data ---")
    # Force mock data by not providing API key (if not set in env/config)
    # Or explicitly set config.USE_MOCK_DATA = True before initializing
    mock_client = AccuWeatherClient(api_key=None) # Force mock if no env/config key
    mock_client.use_mock_data = True # Ensure mock mode

    print("\n--- Getting Mock Location Key ---")
    mock_key = mock_client._get_location_key()
    print(f"Mock Location Key: {mock_key}")

    print("\n--- Getting Mock Current Weather ---")
    mock_weather = mock_client.get_current_weather()
    print(json.dumps(mock_weather, indent=2))

    print("\n--- Getting Mock Forecast (3 days) ---")
    mock_forecast = mock_client.get_forecast(days=3)
    print(json.dumps(mock_forecast, indent=2))

    print("\n--- Test Finished ---")
