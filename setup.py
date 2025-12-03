"""Setup configuration for File Organizer."""

from setuptools import setup, find_packages

setup(
    name="file-organizer",
    version="0.1.0",
    description="A command-line tool for automating file management tasks",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "hypothesis>=6.92.0",
        "pytest>=7.4.0",
        "PyYAML>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "file-organizer=src.cli:main",
        ],
    },
)
