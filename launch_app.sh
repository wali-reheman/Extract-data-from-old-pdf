#!/bin/bash
# PDF Data Extractor - MacOS Launcher
# Double-click this file to start the web interface

echo "========================================="
echo "  PDF Census Data Extractor"
echo "  Starting web interface..."
echo "========================================="
echo ""

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo ""
    echo "Please install Python 3 from:"
    echo "https://www.python.org/downloads/macos/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Setting up virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "========================================="
echo "  ✓ Setup complete!"
echo "========================================="
echo ""
echo "🚀 Starting web interface..."
echo ""
echo "The app will open in your browser at:"
echo "👉 http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================="
echo ""

# Launch Streamlit
streamlit run app.py

# Deactivate virtual environment on exit
deactivate
