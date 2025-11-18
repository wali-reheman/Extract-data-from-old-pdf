"""Setup script for PDF Data Extractor"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="pdf-data-extractor",
    version="1.0.0",
    author="Wali Reheman",
    author_email="rw8143a@american.edu",
    description="Extract structured data from census and election PDFs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wali-reheman/Extract-data-from-old-pdf",
    project_urls={
        "Bug Tracker": "https://github.com/wali-reheman/Extract-data-from-old-pdf/issues",
        "Documentation": "https://github.com/wali-reheman/Extract-data-from-old-pdf#readme",
        "Source Code": "https://github.com/wali-reheman/Extract-data-from-old-pdf",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pdf-extract=pdf_data_extractor.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="pdf ocr data-extraction census election tesseract",
)
