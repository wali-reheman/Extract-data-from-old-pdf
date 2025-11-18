#!/bin/bash
# Build script for creating standalone macOS .app bundle
# Creates: PDF Data Extractor.app with all dependencies embedded

set -e  # Exit on error

echo "========================================================================"
echo "PDF DATA EXTRACTOR - macOS App Builder"
echo "========================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This script must be run on macOS${NC}"
    exit 1
fi

echo -e "${BLUE}[1/6] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"
echo ""

echo -e "${BLUE}[2/6] Installing py2app if needed...${NC}"
if ! python3 -c "import py2app" 2>/dev/null; then
    echo "Installing py2app..."
    pip3 install py2app
else
    echo "✓ py2app already installed"
fi
echo ""

echo -e "${BLUE}[3/6] Installing project dependencies...${NC}"
pip3 install -r requirements.txt -q
echo "✓ Dependencies installed"
echo ""

echo -e "${BLUE}[4/6] Cleaning previous build...${NC}"
rm -rf build dist
echo "✓ Cleaned"
echo ""

echo -e "${BLUE}[5/6] Building macOS app bundle...${NC}"
python3 setup_macos_app.py py2app

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ App built successfully!${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[6/6] Creating installer package...${NC}"
# Move app to current directory for easy access
if [ -d "dist/PDF Data Extractor.app" ]; then
    cp -R "dist/PDF Data Extractor.app" .
    echo -e "${GREEN}✓ App copied to current directory${NC}"
fi
echo ""

echo "========================================================================"
echo -e "${GREEN}BUILD COMPLETE!${NC}"
echo "========================================================================"
echo ""
echo "Your standalone app is ready:"
echo "  📱 PDF Data Extractor.app"
echo ""
echo "To use it:"
echo "  1. Double-click 'PDF Data Extractor.app' to launch"
echo "  2. Your browser will automatically open to the app"
echo ""
echo "To install:"
echo "  • Drag 'PDF Data Extractor.app' to your Applications folder"
echo "  • Or double-click it from anywhere"
echo ""
echo "Size: $(du -sh "PDF Data Extractor.app" 2>/dev/null | awk '{print $1}')"
echo ""
