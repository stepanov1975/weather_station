#!/usr/bin/env python3
"""
Setup script for the Weather Display application.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="weather-display",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Weather Display for Raspberry Pi 5 touchscreen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/weather-display",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "weather-display=weather_display.main:main",
        ],
    },
    include_package_data=True,
)
