# -*- coding: utf-8 -*-
"""
       ______
|      |    |           ____
|      |____|    -     /
|      |         |    |
|___   |         |     \____


+ ------------------------------------------ +
|                  lpic                      |
+ ------------------------------------------ +
|                                            |
|   ++++++++++++++++++++++++++++++++++++++   |
|   ++++++++++++++++++++++++++++++++++++++   |
|   ++++++++++++++++++++++++++++++++++++++   |
|   ++++++++++++++++++++++++++++++++++++++   |
|   ++++++++++++++++++++++++++++++++++++++   |
|                                            |
|   A awesome terminal tool for image        |
|   hosting                                  |
|                                            |
|   Built with love by jlice                 |
|                                            |
+ ------------------------------------------ +

"""
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
about = {}

with open(os.path.join(here, "lpic", "__about__.py"), "r") as f:
    exec(f.read(), about)

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name=about["__title__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__author_email__"],
    url=about["__url__"],
    description=about["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=about["__license__"],
    packages=find_packages(),
    install_requires=[
        "pyperclip",
        "Pillow",
        "PyYAML",
        "oss2",
        "qiniu",
        "cos-python-sdk-v5",
    ],
    entry_points={"console_scripts": ["lpic = lpic.__main__:start"]},
    keywords=["image", "cli", "tool"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Chinese",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities",
    ],
)
