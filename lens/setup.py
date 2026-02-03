"""Setup configuration for Lens."""

from setuptools import find_packages, setup

setup(
    name="lens",
    version="0.1.0",
    description="CI Analytics and Visualization Tool",
    author="Argos Project",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "lens=lens.cli.main:main",
        ],
    },
    python_requires=">=3.8",
)
