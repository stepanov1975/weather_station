#!/usr/bin/env python3
"""
Setup script for the Weather Display application.
"""

from setuptools import setup, find_packages  # type: ignore[import-untyped]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="weather-display",
    version="0.1.0",
    author="Alex",
    description="Raspberry Pi touchscreen weather display using Israel Meteorological Service data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    keywords=[
        "weather",
        "raspberry-pi",
        "touchscreen",
        "kiosk",
        "ims",
        "israel-meteorological-service",
        "customtkinter",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Home Automation",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    package_data={
        "weather_display": [
            "assets/weather_icons/*.png",
            "py.typed",
        ],
    },
    entry_points={
        "console_scripts": [
            "weather-display=weather_display.main:main",
        ],
    },
    include_package_data=True,
)
