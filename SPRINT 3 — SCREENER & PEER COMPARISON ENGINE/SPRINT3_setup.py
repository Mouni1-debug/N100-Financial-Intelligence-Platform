#!/usr/bin/env python
"""Setup configuration for N100 Sprint 3 - Screener & Peer Comparison Engine."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="n100-sprint3-screener-peer-engine",
    version="1.0.0",
    author="Bluestock Fintech",
    author_email="dev@bluestock.in",
    description="Financial screener and peer comparison system for Nifty 100 companies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bluestock/n100-sprint3-screener-peer-engine",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "openpyxl>=3.6.0",
        "xlsxwriter>=3.0.0",
        "scikit-learn>=0.24.0",
        "matplotlib>=3.4.0",
        "plotly>=5.0.0",
        "pyyaml>=5.4.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0",
            "pytest-mock>=3.6.0",
            "flake8>=3.9.0",
            "black>=21.0",
        ],
        "dashboard": [
            "streamlit>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "n100-screener=scripts.run_screener:main",
            "n100-peer-report=scripts.generate_peer_report:main",
            "n100-radar-charts=scripts.generate_radar_charts:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
