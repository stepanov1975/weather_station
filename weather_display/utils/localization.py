"""
Localization module for the Weather Display application.
"""

import logging
import locale
from datetime import datetime

logger = logging.getLogger(__name__)

# Available languages
LANGUAGES = {
    'en': 'English',
    'ru': 'Russian'
}

# Translations dictionary
TRANSLATIONS = {
    'en': {
        # App title
        'app_title': 'Weather Display',
        
        # Weather sections
        'current_weather': 'Current Weather',
        'temperature': 'Temperature',
        'humidity': 'Humidity',
        'air_quality': 'Air Quality',
        
        # Air quality levels
        'air_good': 'Good',
        'air_moderate': 'Moderate',
        'air_unhealthy_sensitive': 'Unhealthy for sensitive',
        'air_unhealthy': 'Unhealthy',
        'air_very_unhealthy': 'Very Unhealthy',
        'air_hazardous': 'Hazardous',
        'air_unknown': 'Unknown',
        
        # Day names
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
        'saturday': 'Saturday',
        'sunday': 'Sunday',
        
        # Month names
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
        
        # Weather conditions
        'sunny': 'Sunny',
        'partly_cloudy': 'Partly cloudy',
        'cloudy': 'Cloudy',
        'overcast': 'Overcast',
        'mist': 'Mist',
        'fog': 'Fog',
        'light_rain': 'Light rain',
        'moderate_rain': 'Moderate rain',
        'heavy_rain': 'Heavy rain',
        'patchy_rain': 'Patchy rain',
        'patchy_rain_nearby': 'Patchy rain nearby',
        'light_snow': 'Light snow',
        'moderate_snow': 'Moderate snow',
        'heavy_snow': 'Heavy snow',
        'patchy_snow': 'Patchy snow',
        'thunderstorm': 'Thunderstorm',
        'clear': 'Clear',
        
        # Other
        'day': 'Day',
        'unknown': 'Unknown'
    },
    'ru': {
        # App title
        'app_title': 'Прогноз Погоды',
        
        # Weather sections
        'current_weather': 'Текущая Погода',
        'temperature': 'Температура',
        'humidity': 'Влажность',
        'air_quality': 'Качество Воздуха',
        
        # Air quality levels
        'air_good': 'Хорошее',
        'air_moderate': 'Умеренное',
        'air_unhealthy_sensitive': 'Вредно для чувствительных',
        'air_unhealthy': 'Вредно',
        'air_very_unhealthy': 'Очень вредно',
        'air_hazardous': 'Опасно',
        'air_unknown': 'Неизвестно',
        
        # Day names
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье',
        
        # Month names
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
        'mist': 'Туман',
        'fog': 'Густой туман',
        'light_rain': 'Небольшой дождь',
        'moderate_rain': 'Умеренный дождь',
        'heavy_rain': 'Сильный дождь',
        'patchy_rain': 'Местами дождь',
        'patchy_rain_nearby': 'Местами дождь поблизости',
        'light_snow': 'Небольшой снег',
        'moderate_snow': 'Умеренный снег',
        'heavy_snow': 'Сильный снегопад',
        'patchy_snow': 'Местами снег',
        'thunderstorm': 'Гроза',
        'clear': 'Ясно',
        
        # Other
        'day': 'День',
        'unknown': 'Неизвестно'
    }
}

# Day name mapping
DAY_NAMES = {
    'en': {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    },
    'ru': {
        0: 'Понедельник',
        1: 'Вторник',
        2: 'Среда',
        3: 'Четверг',
        4: 'Пятница',
        5: 'Суббота',
        6: 'Воскресенье'
    }
}

# Month name mapping
MONTH_NAMES = {
    'en': {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    },
    'ru': {
        1: 'Января',
        2: 'Февраля',
        3: 'Марта',
        4: 'Апреля',
        5: 'Мая',
        6: 'Июня',
        7: 'Июля',
        8: 'Августа',
        9: 'Сентября',
        10: 'Октября',
        11: 'Ноября',
        12: 'Декабря'
    }
}

def get_translation(key, language='en'):
    """
    Get translation for a key in the specified language.
    
    Args:
        key (str): Translation key
        language (str): Language code (default: 'en')
        
    Returns:
        str: Translated text or key if translation not found
    """
    if language not in TRANSLATIONS:
        logger.warning(f"Language '{language}' not supported, falling back to English")
        language = 'en'
    
    return TRANSLATIONS[language].get(key, key)

def get_formatted_date(language='en'):
    """
    Get the current date formatted according to the specified language.
    
    Args:
        language (str): Language code (default: 'en')
        
    Returns:
        str: Formatted date string
    """
    now = datetime.now()
    day_name = DAY_NAMES.get(language, DAY_NAMES['en']).get(now.weekday(), 'Unknown')
    month_name = MONTH_NAMES.get(language, MONTH_NAMES['en']).get(now.month, 'Unknown')
    
    if language == 'ru':
        # Russian date format: "Четверг, 27 Марта 2025"
        return f"{day_name}, {now.day} {month_name} {now.year}"
    else:
        # English date format: "Thursday, 27 March 2025"
        return f"{day_name}, {now.day} {month_name} {now.year}"

def get_day_name_localized(date_str, language='en'):
    """
    Get the localized day name from a date string.
    
    Args:
        date_str (str): Date string in format 'YYYY-MM-DD'
        language (str): Language code (default: 'en')
        
    Returns:
        str: Localized day name
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = date_obj.weekday()  # 0 is Monday, 6 is Sunday
        
        day_names = DAY_NAMES.get(language, DAY_NAMES['en'])
        return day_names.get(weekday, get_translation('unknown', language))
    except Exception:
        return get_translation('unknown', language)

def get_air_quality_text_localized(index, language='en'):
    """
    Convert air quality index to localized descriptive text.
    
    Args:
        index (int): Air quality index (1-6)
        language (str): Language code (default: 'en')
        
    Returns:
        str: Localized descriptive text for the air quality
    """
    aqi_keys = {
        1: 'air_good',
        2: 'air_moderate',
        3: 'air_unhealthy_sensitive',
        4: 'air_unhealthy',
        5: 'air_very_unhealthy',
        6: 'air_hazardous'
    }
    
    key = aqi_keys.get(index, 'air_unknown')
    return get_translation(key, language)

def translate_weather_condition(condition, language='en'):
    """
    Translate a weather condition to the specified language.
    
    Args:
        condition (str): Weather condition text
        language (str): Language code (default: 'en')
        
    Returns:
        str: Translated weather condition
    """
    # Map common weather conditions to translation keys
    condition_map = {
        'Sunny': 'sunny',
        'Partly cloudy': 'partly_cloudy',
        'Cloudy': 'cloudy',
        'Overcast': 'overcast',
        'Mist': 'mist',
        'Fog': 'fog',
        'Light rain': 'light_rain',
        'Moderate rain': 'moderate_rain',
        'Heavy rain': 'heavy_rain',
        'Patchy rain': 'patchy_rain',
        'Patchy rain nearby': 'patchy_rain_nearby',
        'Light snow': 'light_snow',
        'Moderate snow': 'moderate_snow',
        'Heavy snow': 'heavy_snow',
        'Patchy snow': 'patchy_snow',
        'Thunderstorm': 'thunderstorm',
        'Clear': 'clear'
    }
    
    # Convert condition to lowercase for case-insensitive matching
    condition_lower = condition.lower() if condition else ''
    
    # Find the matching key
    for key, value in condition_map.items():
        if key.lower() in condition_lower:
            return get_translation(value, language)
    
    # If no match found, return the original condition
    return condition
