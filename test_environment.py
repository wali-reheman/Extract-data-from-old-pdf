#!/usr/bin/env python3
"""
Environment Diagnostic Tool
Run this to check if all dependencies are properly installed
"""

import sys
print("=" * 60)
print("PDF EXTRACTOR - ENVIRONMENT DIAGNOSTIC")
print("=" * 60)
print()

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Python Path: {sys.path[:3]}")
print()

print("=" * 60)
print("TESTING REQUIRED PACKAGES")
print("=" * 60)
print()

packages = {
    'streamlit': 'Streamlit (Web UI)',
    'pdfplumber': 'PDF Plumber (PDF extraction)',
    'pandas': 'Pandas (Data processing)',
    'openpyxl': 'OpenPyXL (Excel export)',
    'PIL': 'Pillow (Image processing)',
    'cv2': 'OpenCV (Computer Vision)',
    'pytesseract': 'PyTesseract (OCR)',
    'pdf2image': 'PDF2Image (PDF to image)'
}

success_count = 0
failed = []

for module, description in packages.items():
    try:
        imported = __import__(module)
        location = getattr(imported, '__file__', 'built-in')
        print(f"✓ {description:35} INSTALLED")
        print(f"  Location: {location}")
        success_count += 1
    except ImportError as e:
        print(f"✗ {description:35} NOT FOUND")
        print(f"  Error: {str(e)}")
        failed.append(module)
    except Exception as e:
        print(f"⚠ {description:35} ERROR")
        print(f"  Error: {str(e)}")
        failed.append(module)
    print()

print("=" * 60)
print("TESTING CUSTOM MODULES")
print("=" * 60)
print()

try:
    from extract_universal import try_pdfplumber, smart_parse_table
    print("✓ extract_universal.py: IMPORTED SUCCESSFULLY")
    print(f"  Functions: try_pdfplumber, smart_parse_table")
except ImportError as e:
    print("✗ extract_universal.py: IMPORT FAILED")
    print(f"  Error: {str(e)}")
    failed.append('extract_universal')
except Exception as e:
    print("⚠ extract_universal.py: ERROR")
    print(f"  Error: {str(e)}")
    failed.append('extract_universal')
print()

print("=" * 60)
print("SUMMARY")
print("=" * 60)
print()
print(f"✓ Installed: {success_count}/{len(packages)}")

if failed:
    print(f"✗ Failed: {len(failed)}")
    print(f"  Missing packages: {', '.join(failed)}")
    print()
    print("TO FIX:")
    print(f"  pip3 install {' '.join(failed)}")
else:
    print("✓ All packages installed successfully!")
    print()
    print("You can now run the app with:")
    print("  streamlit run app.py")

print()
print("=" * 60)
