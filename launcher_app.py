#!/usr/bin/env python3
"""
Launcher script for standalone macOS app
This script starts Streamlit and opens the browser automatically
"""

import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path

def main():
    """Launch the Streamlit app and open browser"""

    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    app_file = script_dir / "app.py"

    print("Starting PDF Data Extractor...")
    print(f"App location: {app_file}")

    # Start Streamlit in background
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(app_file),
         "--server.headless", "true",
         "--server.port", "8501",
         "--browser.gatherUsageStats", "false"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(script_dir)
    )

    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)

    # Open browser
    print("Opening browser...")
    webbrowser.open("http://localhost:8501")

    # Keep running
    print("PDF Data Extractor is running!")
    print("Close this window to stop the application.")

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
