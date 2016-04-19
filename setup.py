"""
Setup for ag980

Setup script for building ag980 package.
"""

from setuptools import find_packages, setup

setup_params = dict(
    name="ag980",
    description="control TEAC AG-980 receiver via RS232C",
    packages=find_packages(),
    version = "0.1.0",
    author = "Pete Hollobon",
    author_email = "pete@hollobon.com",
    url="https://github.com/hollobon/ag980",
    classifiers=["License :: OSI Approved :: MIT License"],
)

if __name__ == '__main__':
    setup(**setup_params)
