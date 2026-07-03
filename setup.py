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
    description="IMS weather display for Raspberry Pi touchscreen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
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
