"""
Utilities Package for the Weather Display Application.

This package aggregates various helper modules and utility functions that
support the core functionality of the application but don't belong to a
specific domain like 'gui' or 'services'.

Modules included provide functionalities such as:
- `helpers`: General-purpose helper functions (e.g., network checks, date parsing).
- `icon_handler`: Loading, caching, and managing weather icons.
- `localization`: Handling multi-language text translations and date formatting.

This `__init__.py` file marks the directory as a Python package. It can also
be used to selectively expose commonly used utilities at the package level for
convenience, although direct imports from the specific utility modules are often
preferred for clarity.
"""

# Example of exposing a class at the package level:
# This allows `from weather_display.utils import WeatherIconHandler`
from .icon_handler import WeatherIconHandler

# Other commonly used utilities could potentially be exposed here as well,
# but weigh convenience against the explicitness of direct module imports.
# e.g.,
# from .helpers import check_internet_connection
# from .localization import get_translation
