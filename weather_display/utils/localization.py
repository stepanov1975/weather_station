"""
Localization Utilities for the Weather Display Application.

This module centralizes all functionality related to multi-language support.
It provides:
- A master dictionary (`TRANSLATIONS`) holding text translations for various UI
  elements and messages, keyed by language code (e.g., 'en', 'ru').
- Mappings for translating specific data received from APIs (like AccuWeather
  AQI categories and weather condition phrases) into standardized internal keys,
  which are then used to look up translations in `TRANSLATIONS`.
- Functions to retrieve translations (`get_translation`).
- Functions to translate specific data types (`translate_aqi_category`,
  `translate_weather_condition`).
- Functions for formatting dates according to language conventions, using
  manually defined mappings for day and month names (`get_formatted_date`,
  `get_day_name_localized`).

The application's display language is determined by the `LANGUAGE` setting in
`config.py`.
"""

import logging
import locale # Standard library for locale-specific operations (currently unused but potentially useful)
from datetime import datetime
from typing import Dict, Optional

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

# ==============================================================================
# Language Definitions and Translations
# ==============================================================================

# Dictionary mapping supported language codes to their display names (optional, for reference)
LANGUAGES: Dict[str, str] = {
    'en': 'English',
    'ru': 'Russian'
    # Add other supported languages here
}

# Master dictionary holding all translations.
# Structure: TRANSLATIONS[language_code][translation_key] = translated_string
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # --- English Translations ---
    'en': {
        # App Info
        'app_title': 'Weather Display',

        # UI Labels / Sections
        'current_weather': 'Current Weather',
        'temperature': 'Temperature',
        'humidity': 'Humidity',
        'air_quality': 'Air Quality',
        'forecast': 'Forecast', # Added forecast title if needed

        # Air Quality Index (AQI) Levels (Keys match ACCUWEATHER_AQI_CATEGORY_MAP values)
        'air_good': 'Good',
        'air_moderate': 'Moderate',
        'air_unhealthy_sensitive': 'Unhealthy for Sensitive Groups',
        'air_unhealthy': 'Unhealthy',
        'air_very_unhealthy': 'Very Unhealthy',
        'air_hazardous': 'Hazardous',
        'air_unknown': 'Unknown AQI', # Specific key for unknown/missing AQI

        # General UI Text & Statuses
        'not_available': 'N/A',
        'icon_missing': 'Icon Missing',
        'day': 'Day', # Generic 'Day' label
        'unknown': 'Unknown', # General unknown value fallback
        'no_internet': 'No Internet Connection',
        'api_limit_reached': 'API Limit Reached',
        'api_error': 'API Error', # General API error status

        # Day Names (Full) - Used by date formatting functions
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
        'saturday': 'Saturday',
        'sunday': 'Sunday',

        # Month Names (Full) - Used by date formatting functions
        'january': 'January',
        'february': 'February',
        'march': 'March',
        'april': 'April',
        'may': 'May',
        'june': 'June',
        'july': 'July',
        'august': 'August',
        'september': 'September',
        'october': 'October',
        'november': 'November',
        'december': 'December',

        # Weather Condition Phrases (Keys match WEATHER_CONDITION_MAP values)
        # These should cover expected phrases from the weather API (e.g., AccuWeather).
        # Expand this list based on observed API responses.
        'sunny': 'Sunny',
        'partly_cloudy': 'Partly Cloudy',
        'cloudy': 'Cloudy',
        'overcast': 'Overcast',
        'mist': 'Mist',
        'fog': 'Fog',
        'light_rain': 'Light Rain',
        'moderate_rain': 'Moderate Rain',
        'heavy_rain': 'Heavy Rain',
        'patchy_rain': 'Patchy Rain',
        'patchy_rain_nearby': 'Patchy Rain Nearby',
        'light_snow': 'Light Snow',
        'moderate_snow': 'Moderate Snow',
        'heavy_snow': 'Heavy Snow',
        'patchy_snow': 'Patchy Snow',
        'thunderstorm': 'Thunderstorm',
        'clear': 'Clear', # Often used for night conditions
        'mostly_sunny': 'Mostly Sunny',
        'intermittent_clouds': 'Intermittent Clouds',
        'hazy_sunshine': 'Hazy Sunshine',
        'mostly_cloudy': 'Mostly Cloudy',
        'dreary': 'Dreary', # AccuWeather specific?
        'showers': 'Showers', # AccuWeather specific?
        't_storms': 'T-Storms', # AccuWeather specific?
        'rain': 'Rain', # General rain
        'flurries': 'Flurries', # AccuWeather specific?
        'snow': 'Snow', # General snow
        'ice': 'Ice', # AccuWeather specific?
        'sleet': 'Sleet', # AccuWeather specific?
        'freezing_rain': 'Freezing Rain', # AccuWeather specific?
        'rain_and_snow': 'Rain and Snow', # AccuWeather specific?
        'hot': 'Hot', # AccuWeather specific?
        'cold': 'Cold', # AccuWeather specific?
        'windy': 'Windy', # AccuWeather specific?
        'hazy_moonlight': 'Hazy Moonlight', # AccuWeather specific?
        # Add night variations if needed, or handle day/night logic elsewhere
        # e.g., 'partly_cloudy_night': 'Partly Cloudy Night'
    },
    # --- Russian Translations ---
    'ru': {
        # App Info
        'app_title': 'Прогноз Погоды',

        # UI Labels / Sections
        'current_weather': 'Текущая Погода',
        'temperature': 'Температура',
        'humidity': 'Влажность',
        'air_quality': 'Качество Воздуха',
        'forecast': 'Прогноз',

        # Air Quality Index (AQI) Levels
        'air_good': 'Хорошее',
        'air_moderate': 'Умеренное',
        'air_unhealthy_sensitive': 'Вредно для чувствительных групп',
        'air_unhealthy': 'Вредное',
        'air_very_unhealthy': 'Очень вредное',
        'air_hazardous': 'Опасное',
        'air_unknown': 'Качество неизвестно',

        # General UI Text & Statuses
        'not_available': 'Н/Д', # Not Available abbreviation
        'icon_missing': 'Нет иконки',
        'day': 'День',
        'unknown': 'Неизвестно',
        'no_internet': 'Нет подключения к Интернету',
        'api_limit_reached': 'Достигнут лимит API',
        'api_error': 'Ошибка API',

        # Day Names (Full)
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье',

        # Month Names (Genitive case for Russian date format "DD Month YYYY")
        'january': 'Января',
        'february': 'Февраля',
        'march': 'Марта',
        'april': 'Апреля',
        'may': 'Мая',
        'june': 'Июня',
        'july': 'Июля',
        'august': 'Августа',
        'september': 'Сентября',
        'october': 'Октября',
        'november': 'Ноября',
        'december': 'Декабря',

        # Weather Condition Phrases
        'sunny': 'Солнечно',
        'partly_cloudy': 'Переменная облачность',
        'cloudy': 'Облачно',
        'overcast': 'Пасмурно',
        'mist': 'Дымка', # More common than Туман for light fog
        'fog': 'Туман', # For denser fog
        'light_rain': 'Небольшой дождь',
        'moderate_rain': 'Умеренный дождь',
        'heavy_rain': 'Сильный дождь',
        'patchy_rain': 'Местами дождь',
        'patchy_rain_nearby': 'Местами дождь поблизости',
        'light_snow': 'Небольшой снег',
        'moderate_snow': 'Умеренный снег',
        'heavy_snow': 'Сильный снег',
        'patchy_snow': 'Местами снег',
        'thunderstorm': 'Гроза',
        'clear': 'Ясно',
        'mostly_sunny': 'В основном солнечно',
        'intermittent_clouds': 'Временами облачно',
        'hazy_sunshine': 'Солнечно, дымка',
        'mostly_cloudy': 'В основном облачно',
        'dreary': 'Пасмурно', # Mapping Dreary (Overcast)
        'showers': 'Ливни',
        't_storms': 'Грозы',
        'rain': 'Дождь',
        'flurries': 'Снежные заряды',
        'snow': 'Снег',
        'ice': 'Лед',
        'sleet': 'Мокрый снег', # Often used for sleet in Russian
        'freezing_rain': 'Ледяной дождь',
        'rain_and_snow': 'Дождь со снегом',
        'hot': 'Жарко',
        'cold': 'Холодно',
        'windy': 'Ветрено',
        'hazy_moonlight': 'Луна в дымке',
    }
    # Add other languages here...
}

# ==============================================================================
# Manual Date/Time Name Mappings (Alternative to locale)
# ==============================================================================
# Using manual dictionaries provides explicit control over day/month names,
# avoiding potential issues with locale availability or inconsistent formatting
# across different systems, especially relevant for embedded devices like RPi.

# Day name mapping: datetime.weekday() (0=Monday) -> localized string
DAY_NAMES: Dict[str, Dict[int, str]] = {
    'en': {
        0: TRANSLATIONS['en']['monday'], 1: TRANSLATIONS['en']['tuesday'],
        2: TRANSLATIONS['en']['wednesday'], 3: TRANSLATIONS['en']['thursday'],
        4: TRANSLATIONS['en']['friday'], 5: TRANSLATIONS['en']['saturday'],
        6: TRANSLATIONS['en']['sunday']
    },
    'ru': {
        0: TRANSLATIONS['ru']['monday'], 1: TRANSLATIONS['ru']['tuesday'],
        2: TRANSLATIONS['ru']['wednesday'], 3: TRANSLATIONS['ru']['thursday'],
        4: TRANSLATIONS['ru']['friday'], 5: TRANSLATIONS['ru']['saturday'],
        6: TRANSLATIONS['ru']['sunday']
    }
}

# Month name mapping: datetime.month (1=January) -> localized string
MONTH_NAMES: Dict[str, Dict[int, str]] = {
    'en': {
        1: TRANSLATIONS['en']['january'], 2: TRANSLATIONS['en']['february'],
        3: TRANSLATIONS['en']['march'], 4: TRANSLATIONS['en']['april'],
        5: TRANSLATIONS['en']['may'], 6: TRANSLATIONS['en']['june'],
        7: TRANSLATIONS['en']['july'], 8: TRANSLATIONS['en']['august'],
        9: TRANSLATIONS['en']['september'], 10: TRANSLATIONS['en']['october'],
        11: TRANSLATIONS['en']['november'], 12: TRANSLATIONS['en']['december']
    },
    'ru': { # Using genitive case for Russian format "DD Month YYYY"
        1: TRANSLATIONS['ru']['january'], 2: TRANSLATIONS['ru']['february'],
        3: TRANSLATIONS['ru']['march'], 4: TRANSLATIONS['ru']['april'],
        5: TRANSLATIONS['ru']['may'], 6: TRANSLATIONS['ru']['june'],
        7: TRANSLATIONS['ru']['july'], 8: TRANSLATIONS['ru']['august'],
        9: TRANSLATIONS['ru']['september'], 10: TRANSLATIONS['ru']['october'],
        11: TRANSLATIONS['ru']['november'], 12: TRANSLATIONS['ru']['december']
    }
}

# ==============================================================================
# Core Translation Function
# ==============================================================================

def get_translation(key: str, language: str = 'en') -> str:
    """
    Retrieves the translation for a given key in the specified language.

    Looks up the `key` in the `TRANSLATIONS` dictionary for the target `language`.
    If the `language` itself is not found in `TRANSLATIONS`, it falls back to 'en'.
    If the `key` is not found within the selected language dictionary (or the
    English fallback), the original `key` string is returned as a last resort,
    and a warning is logged.

    Args:
        key (str): The unique identifier for the text to be translated (e.g.,
                   'app_title', 'temperature', 'air_good').
        language (str): The target language code (e.g., 'en', 'ru'). Defaults to 'en'.

    Returns:
        str: The translated string corresponding to the key in the specified
             language (or English fallback), or the key itself if no translation
             is found anywhere.
    """
    # Determine the language dictionary to use (target or fallback to English)
    lang_dict = TRANSLATIONS.get(language)
    if lang_dict is None:
        logger.warning(
            f"Language code '{language}' not found in TRANSLATIONS. "
            f"Falling back to English ('en')."
        )
        lang_dict = TRANSLATIONS.get('en', {}) # Use English or empty dict if even 'en' is missing

    # Look up the key in the selected language dictionary
    translation = lang_dict.get(key)

    # If key not found in target language, try fallback English
    if translation is None and language != 'en':
        logger.debug(f"Key '{key}' not found for language '{language}'. Trying English fallback.")
        lang_dict_fallback = TRANSLATIONS.get('en', {})
        translation = lang_dict_fallback.get(key)

    # If key is still not found, return the key itself and log a warning
    if translation is None:
         logger.warning(f"Translation key '{key}' not found for language '{language}' or fallback 'en'. Returning the key itself.")
         return key # Return the original key as the ultimate fallback

    return translation

# ==============================================================================
# Specific Data Translation Maps and Functions
# ==============================================================================

# --- Air Quality Index (AQI) Category Translation ---

# This map translates the category strings received directly from the AccuWeather API
# (e.g., "Good", "Moderate") into the internal translation keys used in the
# `TRANSLATIONS` dictionary (e.g., "air_good", "air_moderate"). This decouples
# the API's specific wording from the application's internal translation system.
ACCUWEATHER_AQI_CATEGORY_MAP: Dict[str, str] = {
    # Case-sensitive keys matching expected API responses
    "Good": "air_good",
    "Moderate": "air_moderate",
    "Unhealthy for Sensitive Groups": "air_unhealthy_sensitive",
    "Unhealthy": "air_unhealthy",
    "Very Unhealthy": "air_very_unhealthy",
    "Hazardous": "air_hazardous",
    "Excellent": "air_good", # Map "Excellent" to the same key as "Good"
    # Add more mappings here if other categories are observed from AccuWeather API
}

def translate_aqi_category(category: Optional[str], language: str = 'en') -> str:
    """
    Translates an AccuWeather AQI category string into the specified language.

    Uses the `ACCUWEATHER_AQI_CATEGORY_MAP` to find the internal translation key
    corresponding to the API's category string, then uses `get_translation`
    to retrieve the text in the target language.

    Args:
        category (Optional[str]): The AQI category string received from the
                                  AccuWeather API (e.g., "Good", "Moderate").
                                  Can be None if AQI data is unavailable.
        language (str): The target language code (e.g., 'en', 'ru'). Defaults to 'en'.

    Returns:
        str: The translated AQI category string (e.g., "Хорошее"). Returns a
             localized "Unknown AQI" string if the input `category` is None.
             Returns the original `category` string if it's not found in the
             `ACCUWEATHER_AQI_CATEGORY_MAP`.
    """
    if category is None:
        # Handle cases where AQI data might be missing entirely
        logger.debug("translate_aqi_category called with None category. Returning 'unknown'.")
        return get_translation('air_unknown', language)

    # Find the internal translation key corresponding to the API category string
    translation_key = ACCUWEATHER_AQI_CATEGORY_MAP.get(category)

    if translation_key:
        # If a mapping exists, get the translation for that key
        translated_text = get_translation(translation_key, language)
        logger.debug(f"Translated AQI category '{category}' (key: '{translation_key}') to '{translated_text}' for language '{language}'.")
        return translated_text
    else:
        # If the category string from the API is not in our map, log a warning
        # and return the original, untranslated string. This helps identify
        # new or unexpected categories from the API.
        logger.warning(
            f"No translation mapping found in ACCUWEATHER_AQI_CATEGORY_MAP for "
            f"AQI category: '{category}'. Returning the original string."
        )
        return category

# --- Weather Condition Phrase Translation ---

# This map attempts to translate common weather condition phrases (expected from API)
# into internal translation keys. Matching is case-insensitive and currently uses
# a simple substring check, which might need refinement for more complex conditions.
# Keys should be lowercase for consistent matching.
WEATHER_CONDITION_MAP: Dict[str, str] = {
    # General
    'sunny': 'sunny',
    'partly cloudy': 'partly_cloudy', # Covers "Partly cloudy" and variations
    'cloudy': 'cloudy',
    'overcast': 'overcast',
    'mist': 'mist',
    'fog': 'fog',
    'clear': 'clear', # Often used for night
    'rain': 'rain', # General rain, might be overridden by more specific types
    'snow': 'snow', # General snow
    'windy': 'windy',
    # Rain variations
    'light rain': 'light_rain',
    'moderate rain': 'moderate_rain',
    'heavy rain': 'heavy_rain',
    'patchy rain': 'patchy_rain',
    'patchy rain nearby': 'patchy_rain_nearby',
    'showers': 'showers', # Often used by AccuWeather
    'freezing rain': 'freezing_rain',
    # Snow variations
    'light snow': 'light_snow',
    'moderate snow': 'moderate_snow',
    'heavy snow': 'heavy_snow',
    'patchy snow': 'patchy_snow',
    'flurries': 'flurries', # AccuWeather specific?
    'sleet': 'sleet',
    'rain and snow': 'rain_and_snow',
    # Storms
    'thunderstorm': 'thunderstorm',
    't-storms': 't_storms', # Abbreviation often used by AccuWeather
    # AccuWeather specific / Other
    'mostly sunny': 'mostly_sunny',
    'intermittent clouds': 'intermittent_clouds',
    'hazy sunshine': 'hazy_sunshine',
    'mostly cloudy': 'mostly_cloudy',
    'dreary': 'dreary', # AccuWeather specific?
    'ice': 'ice',
    'hot': 'hot',
    'cold': 'cold',
    'hazy moonlight': 'hazy_moonlight',
    # Add more conditions as observed from API responses (e.g., night variations if needed)
    # 'partly cloudy night': 'partly_cloudy_night', # Example
}

def translate_weather_condition(condition: Optional[str], language: str = 'en') -> str:
    """
    Translates a weather condition phrase (from API) into the specified language.

    Performs a case-insensitive search for the best match of the input `condition`
    phrase within the keys of the `WEATHER_CONDITION_MAP`. If a match is found,
    it retrieves the corresponding translation key and returns the translated text
    using `get_translation`. If no match is found, it returns the original condition
    string.

    Note: The current matching logic is basic (substring check, preferring longer
    matches). It might require refinement for complex or ambiguous condition phrases.

    Args:
        condition (Optional[str]): The weather condition text received from the API
                                   (e.g., "Sunny", "Partly cloudy", "Showers").
                                   Can be None.
        language (str): The target language code (e.g., 'en', 'ru'). Defaults to 'en'.

    Returns:
        str: The translated weather condition string (e.g., "Солнечно"). Returns the
             original `condition` string if no translation key is found in the map.
             Returns a localized "Unknown" string if the input `condition` is None.
    """
    if condition is None:
        logger.debug("translate_weather_condition called with None condition. Returning 'unknown'.")
        return get_translation('unknown', language)

    condition_lower = condition.lower().strip()
    logger.debug(f"Attempting to translate weather condition: '{condition}' (lowercase: '{condition_lower}')")

    # --- Find Best Match in Map ---
    # Simple strategy: iterate through map, find if key is a substring of the condition,
    # prefer the longest matching key found.
    best_match_key: Optional[str] = None
    for map_key_lower in WEATHER_CONDITION_MAP.keys():
        # Check if the map key (e.g., 'partly cloudy') is present in the input condition
        if map_key_lower in condition_lower:
            # If this is the first match, or a longer match than previously found, store it.
            if best_match_key is None or len(map_key_lower) > len(best_match_key):
                 best_match_key = map_key_lower
                 logger.debug(f"  Potential match found: map key '{map_key_lower}' in condition '{condition_lower}'. Current best match.")

    # --- Translate Using Best Match or Return Original ---
    if best_match_key:
        translation_key = WEATHER_CONDITION_MAP[best_match_key]
        translated_text = get_translation(translation_key, language)
        logger.info(f"Translated condition '{condition}' (matched key: '{best_match_key}', translation key: '{translation_key}') to '{translated_text}' for language '{language}'.")
        return translated_text
    else:
        # If no key in our map was found within the input condition string
        logger.warning(
            f"No translation mapping found in WEATHER_CONDITION_MAP for weather condition: "
            f"'{condition}'. Returning the original string."
        )
        # Return the original, untranslated condition string from the API
        return condition

# ==============================================================================
# Date/Time Formatting Functions (Using Manual Mappings)
# ==============================================================================

def get_formatted_date(language: str = 'en') -> str:
    """
    Gets the current system date formatted into a string based on language conventions.

    Uses the manually defined `DAY_NAMES` and `MONTH_NAMES` dictionaries for
    localization, providing explicit control over the output format.

    Args:
        language (str): The target language code (e.g., 'en', 'ru'). Defaults to 'en'.

    Returns:
        str: A formatted date string according to the language's convention.
             Examples:
             - 'en': "Thursday, 4 May 2023"
             - 'ru': "Четверг, 4 Мая 2023"
             Returns an error string if names are missing.
    """
    now = datetime.now()
    logger.debug(f"Formatting date for language: {language}")

    # Get the appropriate name dictionaries, falling back to English if needed
    day_names_dict = DAY_NAMES.get(language, DAY_NAMES.get('en', {}))
    month_names_dict = MONTH_NAMES.get(language, MONTH_NAMES.get('en', {}))

    # Get the localized names using the current date's weekday/month numbers
    day_name = day_names_dict.get(now.weekday()) # 0=Monday
    month_name = month_names_dict.get(now.month) # 1=January

    # Handle cases where names might be missing from the dictionaries
    if day_name is None:
        logger.error(f"Missing day name for weekday {now.weekday()} in language '{language}'.")
        day_name = get_translation('unknown', language)
    if month_name is None:
        logger.error(f"Missing month name for month {now.month} in language '{language}'.")
        month_name = get_translation('unknown', language)

    # Construct the final formatted string based on language conventions
    # Add more language-specific formats here if needed.
    if language == 'ru':
        # Russian format: "Weekday, DD Month(genitive) YYYY"
        formatted_date = f"{day_name}, {now.day} {month_name} {now.year}"
    else:
        # Default/English format: "Weekday, DD Month YYYY"
        formatted_date = f"{day_name}, {now.day} {month_name} {now.year}"

    logger.debug(f"Formatted date: {formatted_date}")
    return formatted_date


def get_day_name_localized(date_str: Optional[str], language: str = 'en') -> str:
    """
    Gets the localized full day name (e.g., "Monday") from a date string.

    Parses the input date string, attempting common formats (ISO 8601 with 'T',
    or simple 'YYYY-MM-DD'). Uses the manually defined `DAY_NAMES` dictionary
    for translation based on the `language` code.

    Args:
        date_str (Optional[str]): A date string, ideally in ISO 8601 format
                                  (e.g., "2023-10-27T10:00:00+03:00") or simple
                                  "YYYY-MM-DD" format. Can be None.
        language (str): The target language code (e.g., 'en', 'ru'). Defaults to 'en'.

    Returns:
        str: The localized full name of the day of the week (e.g., 'Monday',
             'Понедельник'). Returns a localized "Unknown" string if the input
             is None or the date string cannot be parsed into a valid date.
    """
    if date_str is None:
        logger.debug("get_day_name_localized called with None date_str.")
        return get_translation('unknown', language)

    try:
        # Handle full ISO 8601 timestamp by extracting only the date part before parsing
        date_part = date_str.split('T')[0]
        # Parse the date part into a datetime object
        date_obj = datetime.strptime(date_part, '%Y-%m-%d')
        # Get the weekday number (0=Monday, 6=Sunday)
        weekday_index = date_obj.weekday()

        # Get the appropriate day names dictionary, falling back to English
        day_names_dict = DAY_NAMES.get(language, DAY_NAMES.get('en', {}))
        # Look up the day name using the index
        day_name = day_names_dict.get(weekday_index)

        if day_name:
            logger.debug(f"Determined day name for '{date_str}' in '{language}': {day_name}")
            return day_name
        else:
            # This should only happen if DAY_NAMES dictionary is incomplete
            logger.error(f"Day name not found in dictionary for index {weekday_index}, language '{language}'.")
            return get_translation('unknown', language)

    except (ValueError, TypeError) as e:
        # Log error if the date string cannot be parsed
        logger.error(f"Could not parse date string '{date_str}' to determine day name: {e}")
        return get_translation('unknown', language)


# ==============================================================================
# Deprecated/Unused Functions (Marked for Review/Removal)
# ==============================================================================

def get_air_quality_text_localized(index: int, language: str = 'en') -> str:
    """
    DEPRECATED: Converts an old AQI index (1-6) to localized descriptive text.

    WARNING: This function uses a mapping based on the old WeatherAPI.com index
             system (1-6). The application now primarily uses category strings
             (e.g., "Good", "Moderate") from AccuWeather, which are translated
             by the `translate_aqi_category` function. This function is likely
             unused and should be removed after verifying it's not called anywhere.

    Args:
        index (int): Air quality index (expected 1-6 based on old system).
        language (str): The target language code. Defaults to 'en'.

    Returns:
        str: Localized descriptive text for the air quality index.
    """
    # Mapping based on the old WeatherAPI.com AQI index (1-6)
    aqi_keys_deprecated = {
        1: 'air_good',
        2: 'air_moderate',
        3: 'air_unhealthy_sensitive',
        4: 'air_unhealthy',
        5: 'air_very_unhealthy',
        6: 'air_hazardous'
    }
    logger.warning("Call to DEPRECATED function: get_air_quality_text_localized. This likely needs removal.")
    # Find the translation key based on the old index
    key = aqi_keys_deprecated.get(index, 'air_unknown')
    # Return the translation using the standard function
    return get_translation(key, language)
