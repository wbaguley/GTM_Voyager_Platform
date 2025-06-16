from setuptools import setup, find_packages
import os

# Try to read README.md, but don't fail if it's not found
long_description = ""
readme_path = "README.md"
if os.path.exists(readme_path):
    try:
        with open(readme_path, "r", encoding="utf-8") as fh:
            long_description = fh.read()
    except Exception:
        long_description = "GTM Voyager Platform - Voice-First Business Automation"
else:
    long_description = "GTM Voyager Platform - Voice-First Business Automation"

setup(
    name="gtm-voyager",
    version="0.1.0",
    author="GTM Planetary LLC",
    author_email="support@gtmplanetary.com",
    description="Voice-First Business Automation Platform for Trade Industries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gtm-planetary/gtm-voyager-platform",
    packages=find_packages(where="src" ),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "openai>=1.3.0",
        "redis>=5.0.0",
        "psycopg2-binary>=2.9.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
        ],
    },
)
