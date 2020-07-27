#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-forecast-v2",
    version="0.1.0",
    description="Singer.io tap for extracting data",
    author="Stitch",
    url="http://singer.io",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_forecast-v2"],
    install_requires=[
        "singer-python>=5.0.12",
        "requests",
    ],
    entry_points="""
    [console_scripts]
    tap-forecast-v2=tap_forecastapp:main
    """,
    packages=["tap_forecastapp"],
    package_data = {
        "schemas": ["tap_forecastapp/schemas/*.json"]
    },
    include_package_data=True,
)
