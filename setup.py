#! /usr/bin/env python3

from setuptools import setup

setup(
    name="xsgit",
    version="1.0",
    packages=["xsgit"],
    entry_points={"console_scripts": ["xsgit = xsgit.cli:main"]},
)
