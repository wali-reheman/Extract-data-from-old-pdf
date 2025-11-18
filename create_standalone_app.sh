#!/bin/bash
# Creates a standalone macOS app with embedded Python environment
# This creates a self-contained app that includes all dependencies

set -e

APP_NAME="PDF Data Extractor"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_PATH="${SCRIPT_DIR}/${APP_NAME}.app"

echo "========================================================================"
echo "PDF DATA EXTRACTOR - Standalone App Creator"
echo "========================================================================"
echo ""
echo "This will create: ${APP_NAME}.app"
echo "with embedded Python virtual environment and all dependencies"
echo ""

# Clean previous build
if [ -d "${APP_PATH}" ]; then
    echo "Removing previous app..."
    rm -rf "${APP_PATH}"
fi

# Create app bundle structure
echo "[1/7] Creating app bundle structure..."
mkdir -p "${APP_PATH}/Contents/MacOS"
mkdir -p "${APP_PATH}/Contents/Resources"
mkdir -p "${APP_PATH}/Contents/Frameworks"
echo "✓ Structure created"
echo ""

# Create Info.plist
echo "[2/7] Creating Info.plist..."
cat > "${APP_PATH}/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>PDF_Data_Extractor</string>
    <key>CFBundleIdentifier</key>
    <string>com.pdfextractor.app</string>
    <key>CFBundleName</key>
    <string>PDF Data Extractor</string>
    <key>CFBundleDisplayName</key>
    <string>PDF Data Extractor</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.productivity</string>
</dict>
</plist>
EOF
echo "✓ Info.plist created"
echo ""

# Create embedded Python virtual environment
echo "[3/7] Creating embedded Python virtual environment..."
python3 -m venv "${APP_PATH}/Contents/Frameworks/python-venv"
echo "✓ Virtual environment created"
echo ""

# Activate and install dependencies
echo "[4/7] Installing dependencies in embedded environment..."
source "${APP_PATH}/Contents/Frameworks/python-venv/bin/activate"
pip install --upgrade pip -q
# Install numpy first to avoid import conflicts
pip install --no-cache-dir numpy -q
# Then install all requirements
pip install --no-cache-dir -r requirements.txt -q
deactivate
echo "✓ Dependencies installed"
echo ""

# Copy application files
echo "[5/7] Copying application files..."
cp -r app.py "${APP_PATH}/Contents/Resources/"
cp -r extract_universal.py "${APP_PATH}/Contents/Resources/"
cp -r requirements.txt "${APP_PATH}/Contents/Resources/"
cp -r README.md "${APP_PATH}/Contents/Resources/" 2>/dev/null || true
echo "✓ Application files copied"
echo ""

# Create launcher script
echo "[6/7] Creating launcher script..."
cat > "${APP_PATH}/Contents/MacOS/PDF_Data_Extractor" << 'LAUNCHER_EOF'
#!/bin/bash

# Get the app bundle path
BUNDLE_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
RESOURCES_PATH="${BUNDLE_PATH}/Resources"
PYTHON_VENV="${BUNDLE_PATH}/Frameworks/python-venv"

# Change to Resources directory - this is where app.py and extract_universal.py are
cd "${RESOURCES_PATH}"

# Clear any environment variables that might interfere with package imports
unset PYTHONPATH
unset PYTHONHOME

# Activate the embedded Python environment
source "${PYTHON_VENV}/bin/activate"

# Function to check if port is in use
port_in_use() {
    lsof -i :8501 >/dev/null 2>&1
}

# Kill any existing Streamlit processes on port 8501
if port_in_use; then
    echo "Port 8501 is in use, stopping existing process..."
    lsof -ti :8501 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start Streamlit from Resources directory
echo "Starting PDF Data Extractor..."
python -m streamlit run app.py \
    --server.headless true \
    --server.port 8501 \
    --browser.gatherUsageStats false &

STREAMLIT_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Open browser
open "http://localhost:8501"

# Create a simple dialog
osascript <<APPLESCRIPT
display dialog "PDF Data Extractor is running!

The app has opened in your browser at:
http://localhost:8501

Click OK to stop the application." buttons {"OK"} default button "OK" with title "PDF Data Extractor" with icon note
APPLESCRIPT

# Stop Streamlit when dialog is closed
kill $STREAMLIT_PID 2>/dev/null || true

# Cleanup
deactivate
LAUNCHER_EOF

chmod +x "${APP_PATH}/Contents/MacOS/PDF_Data_Extractor"
echo "✓ Launcher created"
echo ""

# Create PkgInfo
echo "[7/7] Finalizing app bundle..."
echo -n "APPL????" > "${APP_PATH}/Contents/PkgInfo"
echo "✓ App bundle finalized"
echo ""

# Get app size
APP_SIZE=$(du -sh "${APP_PATH}" | awk '{print $1}')

echo "========================================================================"
echo "✓ STANDALONE APP CREATED SUCCESSFULLY!"
echo "========================================================================"
echo ""
echo "App Details:"
echo "  Name: ${APP_NAME}.app"
echo "  Location: ${APP_PATH}"
echo "  Size: ${APP_SIZE}"
echo ""
echo "What's included:"
echo "  ✓ Embedded Python virtual environment"
echo "  ✓ All required dependencies"
echo "  ✓ Application code"
echo "  ✓ No external installations needed"
echo ""
echo "To use:"
echo "  1. Double-click '${APP_NAME}.app'"
echo "  2. App will open in your browser automatically"
echo "  3. Click OK in the dialog to stop the app"
echo ""
echo "To install:"
echo "  • Drag '${APP_NAME}.app' to Applications folder"
echo "  • Or run from anywhere"
echo ""
echo "Note: First launch may be slow due to macOS security checks"
echo "========================================================================"
