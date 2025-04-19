# Technical Context: Weather Claude

## 1. Core Technologies

- **Language:** Python (Version not specified, assume 3.x)
- **GUI Framework:** CustomTkinter (`customtkinter>=5.0.0`) - A modern UI toolkit based on Tkinter.
- **Image Handling:** Pillow (`pillow>=9.0.0`) - Used for image processing, likely for handling weather icons.
- **HTTP Requests:** Requests (`requests>=2.25.0`) - Used for making API calls to fetch weather data.
- **Timezone Handling:** Pytz (`pytz>=2023.3`) - Used for managing timezones, specifically noted for IMS (Israel Meteorological Service) data handling.

## 2. Development Environment & Tooling

- **Package Management:** `pip` with `requirements.txt` for application dependencies and `requirements-dev.txt` for development dependencies.
- **Testing Framework:** Pytest (`pytest>=7.0.0`) with code coverage via `pytest-cov>=4.0.0`.
- **Packaging:** Standard Python setuptools (`setup.py`, `MANIFEST.in`).
- **Version Control:** Git (implied by `.gitignore`).

## 3. Technical Constraints

- Requires Python installation.
- Depends on external libraries specified in `requirements.txt`.
- Network connectivity required to fetch live weather data.
- Potential reliance on specific API keys or endpoints (details likely in `config.py` or environment variables).

## 4. Dependencies

- **Runtime:** `customtkinter`, `pillow`, `pytz`, `requests`.
- **Development/Testing:** `pytest`, `pytest-cov`.

## 5. Tool Usage Patterns

- **Installation:** Likely `pip install -r requirements.txt` for runtime and `pip install -r requirements-dev.txt` for development.
- **Running:** Potentially via `python run_weather_display.py` or `python weather_display/main.py`.
- **Testing:** Likely `pytest` in the project root directory.
- **Packaging:** `python setup.py sdist bdist_wheel` (standard commands).
