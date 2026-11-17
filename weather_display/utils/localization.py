"""
Localization Utilities for the Weather Display Application.

This module centralizes all functionality related to multi-language support.
It provides:
- A master dictionary (`TRANSLATIONS`) holding text translations for various UI
  elements and messages, keyed by language code (e.g., 'en', 'ru').
- Mappings for translating weather condition phrases into standardized internal
  keys, which are then used to look up translations in `TRANSLATIONS`.
- Functions to retrieve translations (`get_translation`).
- Functions to translate weather condition text (`translate_weather_condition`).
- Functions for formatting dates according to language conventions, using
  manually defined mappings for day and month names (`get_formatted_date`,
  `get_day_name_localized`).

The application's display language is determined by the `LANGUAGE` setting in
`config.py`.
"""

import logging
import re
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
        'stale_reading': 'stale',
        'humidity': 'Humidity',
        'forecast': 'Forecast', # Added forecast title if needed

        # General UI Text & Statuses
        'not_available': 'N/A',
        'icon_missing': 'Icon Missing',
        'day': 'Day', # Generic 'Day' label
        'unknown': 'Unknown', # General unknown value fallback
        'no_internet': 'No Internet Connection',
        'api_error': 'API Error', # General API error status
        'network_status': 'Network',
        'api_status': 'API',
        'status_ok': 'OK',
        'status_offline': 'Offline',
        'status_error': 'Error',
        'status_mock': 'Mock',
        'status_pending': 'Pending',

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
        # These should cover expected phrases from weather sources.
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
        'dreary': 'Dreary',
        'showers': 'Showers',
        't_storms': 'T-Storms',
        'rain': 'Rain', # General rain
        'flurries': 'Flurries',
        'snow': 'Snow', # General snow
        'ice': 'Ice',
        'sleet': 'Sleet',
        'freezing_rain': 'Freezing Rain',
        'rain_and_snow': 'Rain and Snow',
        'hot': 'Hot',
        'cold': 'Cold',
        'windy': 'Windy',
        'muggy': 'Muggy',
        'hazy_moonlight': 'Hazy Moonlight',
        'sandstorms': 'Sandstorms',
        'dust': 'Dust',
        'frost': 'Frost',
        'stormy': 'Stormy',
        'rainy': 'Rainy',
        'cloudy_possible_rain': 'Cloudy, Possible Rain',
        'partly_cloudy_possible_rain': 'Partly Cloudy, Possible Rain',
        'cloudy_light_rain': 'Cloudy, Light Rain',
        'extremely_hot': 'Extremely Hot',
        'extremely_cold': 'Extremely Cold',
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
        'stale_reading': 'данные устарели',
        'humidity': 'Влажность',
        'forecast': 'Прогноз',

        # General UI Text & Statuses
        'not_available': 'Н/Д', # Not Available abbreviation
        'icon_missing': 'Нет иконки',
        'day': 'День',
        'unknown': 'Неизвестно',
        'no_internet': 'Нет подключения к Интернету',
        'api_error': 'Ошибка API',
        'network_status': 'Сеть',
        'api_status': 'API',
        'status_ok': 'OK',
        'status_offline': 'Офлайн',
        'status_error': 'Ошибка',
        'status_mock': 'Тест',
        'status_pending': 'Ожидание',

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
        'muggy': 'Душно',
        'hazy_moonlight': 'Луна в дымке',
        'sandstorms': 'Песчаные бури',
        'dust': 'Пыль',
        'frost': 'Мороз',
        'stormy': 'Шторм',
        'rainy': 'Дождливо',
        'cloudy_possible_rain': 'Облачно, возможен дождь',
        'partly_cloudy_possible_rain': 'Переменная облачность, возможен дождь',
        'cloudy_light_rain': 'Облачно, небольшой дождь',
        'extremely_hot': 'Очень жарко',
        'extremely_cold': 'Очень холодно',
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

# --- Weather Condition Phrase Translation ---

# This map attempts to translate common weather condition phrases (expected from API)
# into internal translation keys. Matching ignores case and repeated whitespace.
# Keys should be lowercase for consistent matching.
WEATHER_CONDITION_MAP: Dict[str, str] = {
    # Official IMS city portal phrases
    'partly cloudy, possible rain': 'partly_cloudy_possible_rain',
    'cloudy, possible rain': 'cloudy_possible_rain',
    'cloudy, light rain': 'cloudy_light_rain',
    'extremely hot': 'extremely_hot',
    'extremely cold': 'extremely_cold',
    'sandstorms': 'sandstorms',
    'stormy': 'stormy',
    'rainy': 'rainy',
    'frost': 'frost',
    'dust': 'dust',
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
    'muggy': 'muggy',
    # Rain variations
    'light rain': 'light_rain',
    'moderate rain': 'moderate_rain',
    'heavy rain': 'heavy_rain',
    'patchy rain': 'patchy_rain',
    'patchy rain nearby': 'patchy_rain_nearby',
    'showers': 'showers',
    'freezing rain': 'freezing_rain',
    # Snow variations
    'light snow': 'light_snow',
    'moderate snow': 'moderate_snow',
    'heavy snow': 'heavy_snow',
    'patchy snow': 'patchy_snow',
    'flurries': 'flurries',
    'sleet': 'sleet',
    'rain and snow': 'rain_and_snow',
    # Storms
    'thunderstorm': 'thunderstorm',
    'thunderstorms': 'thunderstorm',
    't-storms': 't_storms',
    # Other common phrases
    'mostly sunny': 'mostly_sunny',
    'intermittent clouds': 'intermittent_clouds',
    'hazy sunshine': 'hazy_sunshine',
    'mostly cloudy': 'mostly_cloudy',
    'dreary': 'dreary',
    'ice': 'ice',
    'hot': 'hot',
    'cold': 'cold',
    'hazy moonlight': 'hazy_moonlight',
    # Add more conditions as observed from API responses (e.g., night variations if needed)
    # 'partly cloudy night': 'partly_cloudy_night', # Example
}

def translate_weather_condition(condition: Optional[str], language: str = 'en') -> str:
    """Translate whole IMS phrases, preserving qualifiers in compound forecasts."""
    if condition is None:
        return get_translation('unknown', language)

    normalized = " ".join(condition.lower().split())
    if normalized in WEATHER_CONDITION_MAP:
        return get_translation(WEATHER_CONDITION_MAP[normalized], language)

    parts = re.split(r" with |,\s*| and ", normalized)
    if len(parts) > 1 and all(part in WEATHER_CONDITION_MAP for part in parts):
        translated = [get_translation(WEATHER_CONDITION_MAP[part], language) for part in parts]
        return ", ".join(translated).capitalize()

    # Keep the full description when any qualifier has no translation.
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
