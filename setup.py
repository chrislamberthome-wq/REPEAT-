"""Setup configuration for REPEAT-HD."""

from setuptools import setup, find_packages

setup(
    name="repeat-hd",
    version="0.1.0",
    description="REPEAT-HD: A simple encoding/verification CLI",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "test": ["pytest>=7.0.0"],
    },
)
