import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    # Use distutils.core as a fallback.
    # We won't be able to build the Wheel file on Windows.
    from distutils.core import setup

if sys.version_info < (3, 7, 4):
    raise RuntimeError("lodis-py requires Python 3.7.4+")

version = "0.1.0"

requires = [
    "requests",
]

setup(
    name="lodis",
    version=version,
    author="Peter Ding",
    author_email="dfhayst@gmail.com",
    license="Apache 2.0",
    description="An synchronous Lodis python client",
    url="",
    install_requires=requires,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
)
