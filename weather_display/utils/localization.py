"""
Localization module for the Weather Display application.

Provides functions for translating text keys, formatting dates,
and translating specific weather data (conditions, AQI categories)
based on the selected language defined in `config.py`.
"""

import logging
import locale
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ==============================================================================
# Language Definitions and Translations
# ==============================================================================

# Dictionary mapping language codes to their display names (optional)
LANGUAGES: Dict[str, str] = {
    'en': 'English',
    'ru': 'Russian'
}

# Master dictionary holding all translations, keyed by language code.
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'en': {
        # App title
        'app_title': 'Weather Display',

        # Weather sections/labels
        'current_weather': 'Current Weather',
        'temperature': 'Temperature',
        'humidity': 'Humidity',
        'air_quality': 'Air Quality',

        # Air quality levels (map keys for AccuWeather categories)
        'air_good': 'Good',
        'air_moderate': 'Moderate',
        'air_unhealthy_sensitive': 'Unhealthy for Sensitive Groups',
        'air_unhealthy': 'Unhealthy',
        'air_very_unhealthy': 'Very Unhealthy',
        'air_hazardous': 'Hazardous',
        'air_unknown': 'Unknown AQI', # More specific than just 'Unknown'

        # General UI text
        'not_available': 'N/A',
        'icon_missing': 'Icon Missing',
        'day': 'Day', # Used in forecast frame titles if needed
        'unknown': 'Unknown', # General unknown value
        'no_internet': 'No Internet Connection',
        'api_limit_reached': 'API Limit Reached',
        'api_error': 'API Error', # Added for general API errors

        # Day names (full) - Used by get_formatted_date, get_day_name_localized
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
        'saturday': 'Saturday',
        'sunday': 'Sunday',

        # Month names (full) - Used by get_formatted_date
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

        # Weather conditions (map keys for API responses)
        # Note: This list should cover expected phrases from the weather API.
        # It might need expansion based on observed API responses.
        'sunny': 'Sunny',
        'partly_cloudy': 'Partly Cloudy', # Covers "Partly cloudy"
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
    },
    'ru': {
        # App title
        'app_title': 'Прогноз Погоды',

        # Weather sections/labels
        'current_weather': 'Текущая Погода',
        'temperature': 'Температура',
        'humidity': 'Влажность',
        'air_quality': 'Качество Воздуха',

        # Air quality levels
        'air_good': 'Хорошее',
        'air_moderate': 'Умеренное',
        'air_unhealthy_sensitive': 'Вредно для чувствительных групп',
        'air_unhealthy': 'Вредное',
        'air_very_unhealthy': 'Очень вредное',
        'air_hazardous': 'Опасное',
        'air_unknown': 'Качество неизвестно',

        # General UI text
        'not_available': 'Н/Д',
        'icon_missing': 'Нет иконки',
        'day': 'День',
        'unknown': 'Неизвестно',
        'no_internet': 'Нет подключения к Интернету',
        'api_limit_reached': 'Достигнут лимит API',
        'api_error': 'Ошибка API', # Added for general API errors

        # Day names (full)
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье',

        # Month names (genitive case for Russian date format)
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

        # Weather conditions
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
        'sleet': 'Мокрый снег',
        'freezing_rain': 'Ледяной дождь',
        'rain_and_snow': 'Дождь со снегом',
        'hot': 'Жарко',
        'cold': 'Холодно',
        'windy': 'Ветрено',
        'hazy_moonlight': 'Луна в дымке',
    }
}

# ==============================================================================
# Manual Date/Time Name Mappings
# ==============================================================================
# NOTE: Using locale.setlocale and datetime.strftime with locale-specific
# format codes (like %A for weekday, %B for month) might be a more robust
# alternative if the required locales are reliably available on the system.
# However, manual mapping provides explicit control.

# Day name mapping (0=Monday, 6=Sunday, matching datetime.weekday())
# Defined directly with strings to avoid module-level function calls during import.
DAY_NAMES: Dict[str, Dict[int, str]] = {
    'en': {
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
        4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    },
    'ru': {
        0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг',
        4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'
    }
}

# Month name mapping (1=January, 12=December)
# Defined directly with strings.
MONTH_NAMES: Dict[str, Dict[int, str]] = {
    'en': {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May',
        6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October',
        11: 'November', 12: 'December'
    },
    'ru': { # Using genitive case for Russian format "DD Month YYYY"
        1: 'Января', 2: 'Февраля', 3: 'Марта', 4: 'Апреля', 5: 'Мая',
        6: 'Июня', 7: 'Июля', 8: 'Августа', 9: 'Сентября', 10: 'Октября',
        11: 'Ноября', 12: 'Декабря'
    }
}

# ==============================================================================
# Translation Functions
# ==============================================================================

def get_translation(key: str, language: str = 'en') -> str:
    """
    Retrieve translation for a given key in the specified language.

    Falls back to English if the specified language is not found.
    Returns the key itself if the key is not found in the target language.

    Args:
        key: The translation key (string).
        language: The target language code (e.g., 'en', 'ru'). Defaults to 'en'.

    Returns:
        The translated string, or the key if no translation exists.
    """
    if language not in TRANSLATIONS:
        logger.warning(
            f"Language '{language}' not supported in TRANSLATIONS. "
            f"Falling back to English."
        )
        language = 'en'

    # Get the dictionary for the target language (or English as fallback)
    lang_dict = TRANSLATIONS.get(language, TRANSLATIONS['en'])
    translation = lang_dict.get(key, key) # Return key if not found

    if translation == key and key not in TRANSLATIONS['en'].get(key, key):
         # Log if key is missing in both target and fallback language
         logger.warning(f"Translation key '{key}' not found for language '{language}' or fallback 'en'.")

    return translation

# ==============================================================================
# Specific Data Translation Maps and Functions
# ==============================================================================

# --- Air Quality Index (AQI) ---

# Mapping from AccuWeather API AQI Category strings to our internal translation keys
# This allows decoupling API response values from our translation structure.
ACCUWEATHER_AQI_CATEGORY_MAP: Dict[str, str] = {
    "Good": "air_good",
    "Moderate": "air_moderate",
    "Unhealthy for Sensitive Groups": "air_unhealthy_sensitive",
    "Unhealthy": "air_unhealthy",
    "Very Unhealthy": "air_very_unhealthy",
    "Hazardous": "air_hazardous",
    "Excellent": "air_good", # Added mapping for "Excellent" category
    # Add more mappings here if AccuWeather uses other category names
}

def translate_aqi_category(category: Optional[str], language: str = 'en') -> str:
    """
    Translate an AccuWeather AQI category string into the specified language.

    Uses the ACCUWEATHER_AQI_CATEGORY_MAP to find the appropriate translation key.

    Args:
        category: AQI category text from AccuWeather API (e.g., "Good", "Moderate").
                  Can be None if data is unavailable.
        language: The target language code. Defaults to 'en'.

    Returns:
        The translated AQI category string, or a localized "Unknown AQI" string
        if the category is None or not found in the map.
    """
    if category is None:
        return get_translation('air_unknown', language)

    # Find the translation key corresponding to the API category string
    translation_key = ACCUWEATHER_AQI_CATEGORY_MAP.get(category, 'air_unknown')
    return get_translation(translation_key, language)

# --- Weather Conditions ---

# Mapping from common weather condition phrases (expected from API)
# to our internal translation keys. Case-insensitive matching is used.
# This map might need expansion based on actual API responses.
WEATHER_CONDITION_MAP: Dict[str, str] = {
    # General
    'sunny': 'sunny',
    'partly cloudy': 'partly_cloudy', # Covers "Partly cloudy"
    'cloudy': 'cloudy',
    'overcast': 'overcast',
    'mist': 'mist',
    'fog': 'fog',
    'clear': 'clear', # Often used for night
    'rain': 'rain',
    'snow': 'snow',
    'windy': 'windy',
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
    't-storms': 't_storms', # Abbreviation
    # AccuWeather specific / Other
    'mostly sunny': 'mostly_sunny',
    'intermittent clouds': 'intermittent_clouds',
    'hazy sunshine': 'hazy_sunshine',
    'mostly cloudy': 'mostly_cloudy',
    'dreary': 'dreary',
    'ice': 'ice',
    'hot': 'hot',
    'cold': 'cold',
    'hazy moonlight': 'hazy_moonlight',
    # Add more conditions as observed from API responses
}

def translate_weather_condition(condition: Optional[str], language: str = 'en') -> str:
    """
    Translate a weather condition phrase into the specified language.

    Performs a case-insensitive search for the condition phrase within the
    WEATHER_CONDITION_MAP keys. Returns the original condition if no match is found.

    Args:
        condition: Weather condition text from the API (e.g., "Sunny", "Partly cloudy").
                   Can be None.
        language: The target language code. Defaults to 'en'.

    Returns:
        The translated weather condition string, or the original condition string
        if no translation key is found, or a localized "Unknown" string if input is None.
    """
    if condition is None:
        return get_translation('unknown', language)

    condition_lower = condition.lower()

    # Search for the best match in the map keys (case-insensitive)
    # This simple approach might need refinement if conditions are ambiguous
    # (e.g., "Patchy light rain" vs "Light rain").
    # Consider prioritizing longer matches or using regex if needed.
    matched_key = None
    for map_key_lower, translation_key in WEATHER_CONDITION_MAP.items():
        if map_key_lower in condition_lower:
            # Basic check: if we already found a match, prefer the longer one
            if matched_key is None or len(map_key_lower) > len(matched_key):
                 matched_key = map_key_lower

    if matched_key:
        translation_key = WEATHER_CONDITION_MAP[matched_key]
        return get_translation(translation_key, language)
    else:
        logger.warning(
            f"No translation mapping found for weather condition: '{condition}'. "
            f"Returning original."
        )
        # Return the original, untranslated condition if no match
        return condition

# ==============================================================================
# Date/Time Formatting Functions (using manual maps)
# ==============================================================================

def get_formatted_date(language: str = 'en') -> str:
    """
    Get the current date formatted according to the specified language.

    Uses the manually defined DAY_NAMES and MONTH_NAMES dictionaries.

    Args:
        language: The target language code. Defaults to 'en'.

    Returns:
        Formatted date string (e.g., "Thursday, 27 March 2025" or
        "Четверг, 27 Марта 2025").
    """
    now = datetime.now()
    day_names_dict = DAY_NAMES.get(language, DAY_NAMES['en'])
    month_names_dict = MONTH_NAMES.get(language, MONTH_NAMES['en'])

    day_name = day_names_dict.get(now.weekday(), get_translation('unknown', language))
    month_name = month_names_dict.get(now.month, get_translation('unknown', language))

    # Format based on language convention (simple example)
    if language == 'ru':
        # Russian format: "Weekday, DD Month(genitive) YYYY"
        return f"{day_name}, {now.day} {month_name} {now.year}"
    else:
        # Default/English format: "Weekday, DD Month YYYY"
        return f"{day_name}, {now.day} {month_name} {now.year}"


def get_day_name_localized(date_str: str, language: str = 'en') -> str:
    """
    Get the localized day name from a date string ('YYYY-MM-DD').

    Uses the manually defined DAY_NAMES dictionary.

    Args:
        date_str: Date string in 'YYYY-MM-DD' format.
        language: The target language code. Defaults to 'en'.

    Returns:
        Localized full day name (e.g., 'Monday', 'Понедельник'), or a
        localized "Unknown" string if parsing fails or the day is invalid.
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = date_obj.weekday()  # 0 = Monday, 6 = Sunday

        day_names_dict = DAY_NAMES.get(language, DAY_NAMES['en'])
        return day_names_dict.get(weekday, get_translation('unknown', language))
    except (ValueError, TypeError) as e:
        logger.error(f"Could not parse date string '{date_str}' to get day name: {e}")
        return get_translation('unknown', language)


# ==============================================================================
# Deprecated/Unused Functions (Marked for Review)
# ==============================================================================

def get_air_quality_text_localized(index: int, language: str = 'en') -> str:
    """
    Convert air quality index to localized descriptive text (DEPRECATED?).

    NOTE: This mapping is based on the old WeatherAPI.com index (1-6).
          It is likely unused as AccuWeather provides category names directly,
          which are translated by `translate_aqi_category`.
          Review usage and consider removing this function.

    Args:
        index: Air quality index (1-6).
        language: The target language code. Defaults to 'en'.

    Returns:
        Localized descriptive text for the air quality.
    """
    # Mapping based on WeatherAPI.com AQI index (1-6)
    aqi_keys = {
        1: 'air_good',
        2: 'air_moderate',
        3: 'air_unhealthy_sensitive',
        4: 'air_unhealthy',
        5: 'air_very_unhealthy',
        6: 'air_hazardous'
    }
    logger.warning("Call to potentially deprecated function: get_air_quality_text_localized")
    key = aqi_keys.get(index, 'air_unknown')
    return get_translation(key, language)
