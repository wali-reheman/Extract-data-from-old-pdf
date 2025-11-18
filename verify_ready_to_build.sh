#!/bin/bash
# Verification script - Run this before building the app
# Checks that all prerequisites are met

echo "========================================================================"
echo "PDF DATA EXTRACTOR - Pre-Build Verification"
echo "========================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Check 1: Running on macOS
echo -n "Checking operating system... "
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}✓ macOS${NC}"
else
    echo -e "${RED}✗ Not macOS${NC}"
    echo "  This script must be run on macOS"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: Python 3 installed
echo -n "Checking Python 3... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

    # Check Python version is 3.8+
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        echo "  Python version is suitable (3.8+)"
    else
        echo -e "  ${YELLOW}⚠ Python 3.8+ recommended${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}✗ Not found${NC}"
    echo "  Install Python 3: brew install python@3.11"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: pip available
echo -n "Checking pip... "
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ pip $PIP_VERSION${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo "  pip should come with Python"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: Required files exist
echo ""
echo "Checking required files..."

FILES=(
    "create_standalone_app.sh"
    "app.py"
    "extract_universal.py"
    "requirements.txt"
)

for file in "${FILES[@]}"; do
    echo -n "  $file... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Missing${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check 5: Disk space
echo ""
echo -n "Checking disk space... "
AVAILABLE=$(df -h . | tail -1 | awk '{print $4}' | sed 's/Gi//' | sed 's/G//')
if [ $(echo "$AVAILABLE > 1" | bc) -eq 1 ]; then
    echo -e "${GREEN}✓ ${AVAILABLE}GB available${NC}"
else
    echo -e "${YELLOW}⚠ Low disk space (${AVAILABLE}GB)${NC}"
    echo "  At least 500MB recommended"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 6: Internet connectivity (for downloading packages)
echo -n "Checking internet connectivity... "
if ping -c 1 pypi.org &> /dev/null; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${YELLOW}⚠ Cannot reach PyPI${NC}"
    echo "  Internet required to download packages"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 7: Port 8501 available
echo -n "Checking port 8501... "
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠ Port in use${NC}"
    echo "  Run: lsof -ti :8501 | xargs kill -9"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ Available${NC}"
fi

# Summary
echo ""
echo "========================================================================"
echo "VERIFICATION SUMMARY"
echo "========================================================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED!${NC}"
    echo ""
    echo "You're ready to build the app. Run:"
    echo "  bash create_standalone_app.sh"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS WARNING(S)${NC}"
    echo ""
    echo "You can proceed, but consider fixing warnings first."
    echo "To build anyway, run:"
    echo "  bash create_standalone_app.sh"
else
    echo -e "${RED}✗ $ERRORS ERROR(S)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS WARNING(S)${NC}"
    fi
    echo ""
    echo "Please fix errors before building."
fi

echo ""
echo "========================================================================"

# Return appropriate exit code
if [ $ERRORS -gt 0 ]; then
    exit 1
else
    exit 0
fi
