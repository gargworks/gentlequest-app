"""
Nucleus Brain - Setup Script
=============================
pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="nucleus-brain",
    version="0.1.0",
    description="The Brain for AI Agents - One Brain, Many Interfaces",
    author="GentleQuest",
    author_email="hello@gentlequest.app",
    packages=find_packages(include=["nucleus", "nucleus.*"]),
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.0",
        "sqlalchemy>=1.4",
    ],
    extras_require={
        "telegram": ["python-telegram-bot>=20.0"],
        "mcp": ["mcp>=0.1"],
    },
    entry_points={
        "console_scripts": [
            "nucleus=nucleus.clients.cli.nucleus_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
