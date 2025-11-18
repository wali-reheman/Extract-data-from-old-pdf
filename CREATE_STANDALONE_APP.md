# Creating a Standalone macOS Application

This guide explains how to create a **double-clickable macOS app** with **all dependencies embedded**, so users don't need to install anything.

## 🎯 Goal

Create `PDF Data Extractor.app` that:
- ✅ Works with a simple double-click
- ✅ Includes all Python dependencies
- ✅ Doesn't require any installation
- ✅ Opens automatically in the browser
- ✅ Can be dragged to Applications folder

---

## 🚀 Quick Start (Recommended)

### Option 1: Fully Standalone App (Easiest for End Users)

This creates an app with an **embedded Python environment** and all dependencies.

```bash
# Run this command:
bash create_standalone_app.sh
```

**What you get:**
- `PDF Data Extractor.app` (~150-250 MB)
- Completely self-contained
- No dependencies needed
- Works on any Mac with macOS 10.14+

**How to use:**
1. Double-click `PDF Data Extractor.app`
2. Browser opens automatically to http://localhost:8501
3. Click OK in dialog to stop the app

**To distribute:**
- Zip the .app and share it
- Users just unzip and double-click
- Optionally: Drag to Applications folder

---

### Option 2: py2app Bundle (Smaller Size)

Uses `py2app` to create a more compact bundle.

```bash
# Install py2app first
pip3 install py2app

# Build the app
bash build_macos_app.sh
```

**What you get:**
- `PDF Data Extractor.app` (~50-100 MB)
- More compact than Option 1
- Still includes all dependencies

---

### Option 3: Simple Wrapper (Requires Dependencies)

Creates a lightweight app wrapper that launches the existing scripts.

```bash
bash create_automator_app.sh
```

**What you get:**
- `PDF Data Extractor.app` (~1 KB)
- Very small
- **Requires**: Python and dependencies already installed

---

## 📋 Comparison

| Feature | Standalone | py2app | Wrapper |
|---------|-----------|---------|---------|
| **Size** | 150-250 MB | 50-100 MB | <1 KB |
| **Dependencies** | ✅ Included | ✅ Included | ❌ Required |
| **Setup Time** | ~2-3 min | ~2-3 min | ~10 sec |
| **Portability** | ✅ High | ✅ High | ❌ Low |
| **Best For** | Distribution | Distribution | Personal use |

---

## 🛠️ Detailed Instructions

### Option 1: Standalone App (Full Details)

#### Step 1: Run the build script

```bash
cd /path/to/Extract-data-from-old-pdf
bash create_standalone_app.sh
```

#### What happens:
1. ✓ Creates `.app` bundle structure
2. ✓ Creates embedded Python virtual environment
3. ✓ Installs all dependencies inside the app
4. ✓ Copies application files
5. ✓ Creates launcher script
6. ✓ Finalizes app bundle

#### Step 2: Test the app

```bash
# Double-click in Finder, or:
open "PDF Data Extractor.app"
```

#### Step 3: Distribute

**For personal use:**
```bash
# Move to Applications
mv "PDF Data Extractor.app" /Applications/
```

**To share with others:**
```bash
# Create a zip file
zip -r "PDF-Data-Extractor-v1.0.zip" "PDF Data Extractor.app"
```

Recipients just need to:
1. Unzip the file
2. Double-click the app
3. (First time only) Right-click → Open to bypass Gatekeeper

---

### Option 2: py2app (Full Details)

#### Prerequisites

```bash
pip3 install py2app
```

#### Build Process

```bash
# Clean previous builds
rm -rf build dist "PDF Data Extractor.app"

# Build
python3 setup_macos_app.py py2app

# App will be in dist/ folder
```

#### Customization

Edit `setup_macos_app.py` to customize:

```python
OPTIONS = {
    'iconfile': 'app_icon.icns',  # Add custom icon
    'plist': {
        'CFBundleDisplayName': 'Your App Name',
        # ... other settings
    }
}
```

---

### Option 3: Simple Wrapper (Full Details)

#### Create the wrapper

```bash
bash create_automator_app.sh
```

#### Important Notes

- **Requires**: Python 3.8+ and dependencies installed
- **Not portable**: Won't work on other machines without setup
- **Good for**: Personal use, development, testing

---

## 🎨 Adding a Custom Icon

### 1. Create an Icon File

You need a `.icns` file for macOS icons.

**Using online converter:**
1. Create a 1024x1024 PNG image
2. Convert to .icns using:
   - https://cloudconvert.com/png-to-icns
   - Or use the `iconutil` command on macOS

**Using iconutil (macOS only):**

```bash
# Create icon set directory
mkdir AppIcon.iconset

# Add your PNG at different sizes:
# AppIcon.iconset/icon_512x512.png
# AppIcon.iconset/icon_512x512@2x.png
# ... etc

# Convert to .icns
iconutil -c icns AppIcon.iconset -o AppIcon.icns
```

### 2. Use the Icon

**For standalone app:**
```bash
# Copy icon to app bundle
cp AppIcon.icns "PDF Data Extractor.app/Contents/Resources/AppIcon.icns"
```

**For py2app:**
Edit `setup_macos_app.py`:
```python
OPTIONS = {
    'iconfile': 'AppIcon.icns',
    # ...
}
```

---

## 🔐 Code Signing (Optional)

To distribute outside the Mac App Store:

### 1. Get a Developer ID

Sign up at: https://developer.apple.com

### 2. Sign the app

```bash
codesign --force --deep --sign "Developer ID Application: Your Name" \
    "PDF Data Extractor.app"
```

### 3. Notarize (for macOS 10.15+)

```bash
# Create a zip
ditto -c -k --keepParent "PDF Data Extractor.app" "PDF Data Extractor.zip"

# Submit for notarization
xcrun notarytool submit "PDF Data Extractor.zip" \
    --apple-id "your@email.com" \
    --team-id "TEAMID" \
    --password "app-specific-password"

# Staple the notarization
xcrun stapler staple "PDF Data Extractor.app"
```

---

## 🐛 Troubleshooting

### "App is damaged and can't be opened"

This is macOS Gatekeeper. Fix:

```bash
# Remove quarantine flag
xattr -cr "PDF Data Extractor.app"
```

Or right-click → Open (first time only)

### App won't start

Check Console app for errors:
```
Applications → Utilities → Console
```

### Dependencies not found

For standalone app, rebuild:
```bash
rm -rf "PDF Data Extractor.app"
bash create_standalone_app.sh
```

### Port 8501 already in use

Kill existing Streamlit:
```bash
lsof -ti :8501 | xargs kill -9
```

### "Python not found" (Wrapper app only)

Install Python 3.8+:
```bash
brew install python@3.11
```

---

## 📦 Distribution Checklist

Before sharing your app:

- [ ] Test on a clean macOS system
- [ ] Verify all features work
- [ ] Check app size is reasonable
- [ ] Include README or documentation
- [ ] (Optional) Code sign the app
- [ ] (Optional) Notarize for macOS 10.15+
- [ ] Create a DMG or ZIP file
- [ ] Test installation process

### Creating a DMG (Recommended)

```bash
# Create a DMG file
hdiutil create -volname "PDF Data Extractor" \
    -srcfolder "PDF Data Extractor.app" \
    -ov -format UDZO \
    "PDF-Data-Extractor-v1.0.dmg"
```

Users can then:
1. Download the DMG
2. Open it
3. Drag app to Applications folder
4. Eject and delete DMG

---

## 🔄 Updates and Maintenance

### Updating the app

1. Pull latest code
2. Rebuild the app:
   ```bash
   bash create_standalone_app.sh
   ```
3. Increment version in `Info.plist`
4. Redistribute

### Version numbering

Edit the build script or `Info.plist`:
```xml
<key>CFBundleVersion</key>
<string>1.0.1</string>
```

---

## 💡 Tips

### Reduce app size

**For standalone app:**
- Remove unnecessary packages from `requirements.txt`
- Use `--no-cache-dir` when installing pip packages
- Exclude dev dependencies

**For py2app:**
- Add more packages to `excludes` in `setup_macos_app.py`
- Use `--strip` option

### Faster builds

```bash
# Use cached dependencies
pip3 install -r requirements.txt --cache-dir ~/.pip-cache
```

### Testing without rebuilding

For quick tests:
```bash
# Just run the app normally
streamlit run app.py
```

---

## 📚 Additional Resources

- **py2app documentation**: https://py2app.readthedocs.io/
- **macOS Bundle structure**: https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html
- **Code signing guide**: https://developer.apple.com/support/code-signing/
- **Streamlit deployment**: https://docs.streamlit.io/

---

## 🆘 Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Review Console app logs
3. Open an issue on GitHub
4. Include:
   - macOS version
   - Python version
   - Error messages
   - Steps to reproduce

---

**Happy distributing! 🎉**
