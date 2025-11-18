#!/bin/bash
# Creates a simple macOS Automator-style .app wrapper
# No dependencies bundling, but easier to create and smaller size

APP_NAME="PDF Data Extractor"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================================================"
echo "Creating Simple macOS App Wrapper"
echo "========================================================================"
echo ""

# Create app bundle structure
APP_PATH="${SCRIPT_DIR}/${APP_NAME}.app"
mkdir -p "${APP_PATH}/Contents/MacOS"
mkdir -p "${APP_PATH}/Contents/Resources"

# Create Info.plist
cat > "${APP_PATH}/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
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
</dict>
</plist>
EOF

# Create launcher script
cat > "${APP_PATH}/Contents/MacOS/launcher" << 'EOF'
#!/bin/bash
# Get the directory where the app is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../../.. && pwd )"

# Open a new Terminal window and run the app
osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "cd '$SCRIPT_DIR' && bash launch_app.sh"
end tell
APPLESCRIPT
EOF

# Make launcher executable
chmod +x "${APP_PATH}/Contents/MacOS/launcher"

echo "✓ App bundle created: ${APP_NAME}.app"
echo ""
echo "To use:"
echo "  1. Double-click '${APP_NAME}.app'"
echo "  2. A Terminal window will open and launch the app"
echo "  3. Your browser will open automatically"
echo ""
echo "Note: This app requires Python and dependencies installed"
echo "For a fully standalone app, use: bash build_macos_app.sh"
echo ""
