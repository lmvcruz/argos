"""
Setup configuration for Verdict package.
"""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="verdict",
    version="1.0.0",
    description="Generic test validation framework for comparing actual vs expected outputs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Argos Team",
    author_email="",
    url="https://github.com/lmvcruz/argos/tree/main/verdict",
    packages=find_packages(exclude=["tests", "examples"]),
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "isort>=5.10",
            "flake8>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "verdict=verdict.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
    ],
)
