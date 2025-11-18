#!/usr/bin/env python3
"""
Setup script for creating standalone macOS .app bundle
Creates: PDF Data Extractor.app with all dependencies embedded

Usage:
    python3 setup_macos_app.py py2app

Requirements:
    pip install py2app
"""

from setuptools import setup
import os

APP = ['app.py']
DATA_FILES = [
    'extract_universal.py',
    'requirements.txt',
    'README.md',
]

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'streamlit',
        'pandas',
        'pdfplumber',
        'openpyxl',
        'PIL',
        'cv2',
        'pytesseract',
        'pdf2image',
    ],
    'includes': [
        'streamlit',
        'streamlit.runtime',
        'streamlit.web',
        'extract_universal',
    ],
    'excludes': [
        'matplotlib',
        'scipy',
        'numpy.distutils',
        'tkinter',
    ],
    'iconfile': None,  # Add custom icon here if available
    'plist': {
        'CFBundleName': 'PDF Data Extractor',
        'CFBundleDisplayName': 'PDF Data Extractor',
        'CFBundleGetInfoString': 'Extract census and election data from PDF files',
        'CFBundleIdentifier': 'com.pdfextractor.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'MIT License',
        'LSMinimumSystemVersion': '10.14',
        'LSApplicationCategoryType': 'public.app-category.productivity',
    }
}

setup(
    name='PDF Data Extractor',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
