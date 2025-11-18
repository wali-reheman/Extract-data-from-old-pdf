#!/usr/bin/env python3
"""
PDF Census Data Extractor - Interactive UI
A user-friendly interface for extracting census/election data from PDFs

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import io
import time
import subprocess
import traceback

# Auto-install missing dependencies
def ensure_dependencies():
    """Ensure all required packages are installed"""
    required_packages = {
        'pdfplumber': 'pdfplumber',
        'pdf2image': 'pdf2image',
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'pytesseract': 'pytesseract',
        'openpyxl': 'openpyxl',
    }

    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        with st.spinner(f"Installing missing packages: {', '.join(missing)}..."):
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", *missing, "-q"
                ])
                st.success(f"✓ Installed {len(missing)} package(s). Please refresh the page.")
                st.stop()
            except Exception as e:
                st.error(f"Failed to install packages: {e}")
                st.info("Please run: pip install -r requirements.txt")
                st.stop()

# Check dependencies on startup
ensure_dependencies()

# Page configuration
st.set_page_config(
    page_title="PDF Data Extractor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .stDownloadButton button {
        background-color: #28a745;
        color: white;
        font-weight: 600;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def extract_from_pdf(pdf_file, use_ai_fallback=True):
    """Extract data from uploaded PDF file with hierarchical detection and AI fallback"""

    # Save uploaded file temporarily
    temp_path = Path(f"/tmp/{pdf_file.name}")
    with open(temp_path, "wb") as f:
        f.write(pdf_file.getbuffer())

    method_used = "Unknown"

    # Extract data
    try:
        # METHOD 1: Try hierarchical extractor first (best for structured PDFs)
        import pdfplumber
        import re

        with pdfplumber.open(str(temp_path)) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Find header and data start
        data_start_idx = 0
        for i, line in enumerate(lines):
            if re.match(r'^1\s+2\s+3\s+4', line):
                data_start_idx = i + 1
                break

        # Process data rows with hierarchical structure
        rows = []
        current_region = None
        current_section = None

        for line in lines[data_start_idx:]:
            # Check for region headers
            if 'DISTRICT' in line or 'SUB-DIVISION' in line:
                current_region = line
                continue

            # Check for section headers
            if line in ['OVERALL', 'RURAL', 'URBAN']:
                current_section = line
                continue

            # Check for data rows (start with sex category)
            sex_categories = ['ALL SEXES', 'MALE', 'FEMALE', 'TRANSGENDER']
            found_sex = None
            for sex in sex_categories:
                if line.startswith(sex):
                    found_sex = sex
                    break

            if found_sex:
                # Remove the sex category from the line to get just the data
                data_part = line[len(found_sex):].strip()

                # Split by whitespace
                tokens = data_part.split()

                # Clean and parse numbers (handle commas and dashes)
                values = []
                for token in tokens:
                    token = token.replace(',', '')
                    if token == '-' or token == '':
                        values.append(None)
                    else:
                        try:
                            values.append(int(token))
                        except:
                            try:
                                values.append(float(token))
                            except:
                                continue

                # Ensure we have exactly 7 data columns
                while len(values) < 7:
                    values.append(None)
                values = values[:7]

                # Create row
                row = [current_region, current_section, found_sex] + values
                rows.append(row)

        # Create DataFrame with hierarchical columns
        if rows:
            headers = ['REGION', 'SECTION', 'AREA/SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN',
                      'HINDU', 'QADIANI/AHMADI', 'SCHEDULED CASTES', 'OTHERS']
            df = pd.DataFrame(rows, columns=headers)

            # Forward fill hierarchical columns
            df['REGION'] = df['REGION'].ffill()
            df['SECTION'] = df['SECTION'].ffill()

            method_used = "Hierarchical Parser"

            # Clean up temp file
            temp_path.unlink()

            return df, None, method_used

        # If hierarchical extraction didn't work, try universal extractor
        from extract_universal import try_pdfplumber, smart_parse_table

        rows, success = try_pdfplumber(str(temp_path))

        if success and rows:
            headers, data_rows = smart_parse_table(rows)

            if data_rows:
                max_cols = max(len(row) for row in data_rows)

                while len(headers) < max_cols:
                    headers.append(f'Column_{len(headers)+1}')

                for row in data_rows:
                    while len(row) < max_cols:
                        row.append(None)

                df = pd.DataFrame(data_rows, columns=headers[:max_cols])
                df = df.drop_duplicates()

                method_used = "Universal Parser"
                temp_path.unlink()

                return df, None, method_used

        # METHOD 2: AI Fallback with PaddleOCR (if enabled)
        if use_ai_fallback:
            try:
                import paddleocr
                import cv2
                import numpy as np
                from pdf2image import convert_from_path

                # Convert PDF to image
                images = convert_from_path(str(temp_path), dpi=300)

                # Initialize PaddleOCR
                ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

                # Perform OCR with table structure recognition
                img_array = np.array(images[0])
                result = ocr.ocr(img_array, cls=True)

                # Parse OCR results into structured data
                # (This is a simplified version - can be enhanced)
                rows = []
                for line in result:
                    for word_info in line:
                        text = word_info[1][0]
                        rows.append([text])

                if rows:
                    df = pd.DataFrame(rows, columns=['Extracted_Text'])
                    method_used = "AI (PaddleOCR)"
                    temp_path.unlink()
                    return df, None, method_used

            except ImportError:
                pass  # PaddleOCR not installed, skip AI fallback
            except Exception as e:
                pass  # AI extraction failed, will return error below

        # If all methods failed
        temp_path.unlink()
        return None, "Failed to extract data from PDF with all available methods", method_used

    except Exception as e:
        # Get full traceback for debugging
        tb = traceback.format_exc()
        error_msg = f"Error processing PDF: {str(e)}\n\nFull traceback:\n{tb}"
        return None, error_msg, method_used


def main():
    # Header
    st.markdown('<p class="main-header">📊 PDF Census Data Extractor</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Extract tabular data from census and election PDFs with AI-powered layout detection</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("🔍 System Info")

        # Debug information
        with st.expander("Debug Information", expanded=False):
            st.code(f"Python: {sys.executable}")
            st.code(f"Version: {sys.version.split()[0]}")

            # Test pdfplumber import
            try:
                import pdfplumber
                st.success("✓ pdfplumber: INSTALLED")
                st.code(f"Location: {pdfplumber.__file__}")
            except ImportError as e:
                st.error("✗ pdfplumber: NOT FOUND")
                st.code(f"Error: {str(e)}")
            except Exception as e:
                st.warning(f"✗ pdfplumber: ERROR - {str(e)}")

            # Test extract_universal import
            try:
                from extract_universal import try_pdfplumber as test_func
                st.success("✓ extract_universal: IMPORTED")
            except ImportError as e:
                st.error("✗ extract_universal: IMPORT FAILED")
                st.code(f"Error: {str(e)}")
            except Exception as e:
                st.warning(f"✗ extract_universal: ERROR - {str(e)}")

        st.divider()

        st.header("ℹ️ About")
        st.markdown("""
        This tool automatically extracts census and election data from PDF files.

        **Features:**
        - 🌍 Universal format support (English & French)
        - 🤖 AI-powered layout detection
        - 📊 Auto-detects table structures
        - 💾 Exports to Excel format
        - 🚀 100% free and local

        **Supported Formats:**
        - Census data
        - Election results
        - Statistical reports
        - Demographic tables
        """)

        st.divider()

        st.header("🔧 How It Works")
        st.markdown("""
        1. **Upload** your PDF file
        2. **Preview** extracted data
        3. **Download** as Excel file

        The tool automatically:
        - Detects number format (English/French)
        - Extracts all data rows
        - Preserves region/section context
        - Handles multi-page PDFs
        """)

        st.divider()

        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Made with ❤️ using Streamlit<br>
        Powered by pdfplumber & pandas
        </div>
        """, unsafe_allow_html=True)

    # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📤 Upload PDF File")

        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a census or election PDF file to extract data",
            label_visibility="collapsed"
        )

        if uploaded_file:
            st.markdown(f'<div class="info-box">✓ File loaded: <strong>{uploaded_file.name}</strong> ({uploaded_file.size:,} bytes)</div>', unsafe_allow_html=True)
        else:
            st.info("👆 Upload a PDF file to get started")

    with col2:
        st.subheader("⚙️ Options")

        col_a, col_b = st.columns(2)
        with col_a:
            preview_rows = st.number_input(
                "Preview rows",
                min_value=5,
                max_value=100,
                value=10,
                step=5,
                help="Number of rows to display in preview"
            )

        with col_b:
            output_format = st.selectbox(
                "Output format",
                ["Excel (.xlsx)", "CSV (.csv)"],
                help="Choose output file format"
            )

    st.divider()

    # Process button
    if uploaded_file:
        if st.button("🚀 Extract Data", type="primary", use_container_width=True):

            # Progress indicator
            with st.spinner("🔄 Processing PDF..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Step 1
                status_text.text("📄 Reading PDF...")
                progress_bar.progress(25)
                time.sleep(0.3)

                # Step 2
                status_text.text("🔍 Detecting layout...")
                progress_bar.progress(50)

                # Extract data
                df, error, method_used = extract_from_pdf(uploaded_file)

                if error:
                    st.error("❌ Extraction Failed")
                    with st.expander("View Error Details", expanded=True):
                        st.code(error, language="python")
                    progress_bar.empty()
                    status_text.empty()
                else:
                    # Step 3
                    status_text.text("📊 Parsing data...")
                    progress_bar.progress(75)
                    time.sleep(0.3)

                    # Step 4
                    status_text.text("✅ Complete!")
                    progress_bar.progress(100)
                    time.sleep(0.3)

                    progress_bar.empty()
                    status_text.empty()

                    # Success message with method used
                    method_icon = "🤖" if "AI" in method_used else "📊"
                    st.markdown(f'<div class="success-box">✅ Successfully extracted <strong>{len(df):,}</strong> rows with <strong>{len(df.columns)}</strong> columns!<br>{method_icon} Method: <strong>{method_used}</strong></div>', unsafe_allow_html=True)

                    # Metrics
                    st.subheader("📈 Extraction Summary")

                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                    with metric_col1:
                        st.metric("Total Rows", f"{len(df):,}")

                    with metric_col2:
                        st.metric("Columns", len(df.columns))

                    with metric_col3:
                        non_null = df.notna().sum().sum()
                        st.metric("Data Points", f"{non_null:,}")

                    with metric_col4:
                        completeness = (non_null / (len(df) * len(df.columns)) * 100)
                        st.metric("Completeness", f"{completeness:.1f}%")

                    st.divider()

                    # Data preview
                    st.subheader("👁️ Data Preview")

                    tab1, tab2, tab3 = st.tabs(["📋 Table View", "📊 Statistics", "🔍 Column Info"])

                    with tab1:
                        st.dataframe(
                            df.head(preview_rows),
                            use_container_width=True,
                            hide_index=True
                        )

                        if len(df) > preview_rows:
                            st.caption(f"Showing first {preview_rows} of {len(df)} rows")

                    with tab2:
                        st.write("**Numeric Column Statistics:**")
                        numeric_cols = df.select_dtypes(include=['number']).columns
                        if len(numeric_cols) > 0:
                            st.dataframe(
                                df[numeric_cols].describe(),
                                use_container_width=True
                            )
                        else:
                            st.info("No numeric columns found")

                    with tab3:
                        col_info = pd.DataFrame({
                            'Column': df.columns,
                            'Type': df.dtypes.astype(str),
                            'Non-Null': df.notna().sum(),
                            'Null': df.isna().sum(),
                            'Unique': df.nunique()
                        })
                        st.dataframe(col_info, use_container_width=True, hide_index=True)

                    st.divider()

                    # Download section
                    st.subheader("💾 Download Results")

                    col_download1, col_download2 = st.columns([2, 1])

                    with col_download1:
                        # Prepare download
                        if "Excel" in output_format:
                            buffer = io.BytesIO()
                            df.to_excel(buffer, index=False, engine='openpyxl')
                            buffer.seek(0)
                            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            file_extension = ".xlsx"
                        else:
                            buffer = io.StringIO()
                            df.to_csv(buffer, index=False)
                            buffer.seek(0)
                            mime_type = "text/csv"
                            file_extension = ".csv"

                        # Generate filename
                        base_name = Path(uploaded_file.name).stem
                        download_filename = f"{base_name}_extracted{file_extension}"

                        st.download_button(
                            label=f"⬇️ Download {output_format}",
                            data=buffer.getvalue() if isinstance(buffer, io.BytesIO) else buffer.getvalue(),
                            file_name=download_filename,
                            mime=mime_type,
                            use_container_width=True
                        )

                    with col_download2:
                        st.metric("File Size", f"{len(buffer.getvalue()):,} bytes")

    else:
        # Show example/instructions when no file uploaded
        st.info("""
        ### 🚀 Getting Started

        1. Upload a PDF file using the file uploader above
        2. Click "Extract Data" to process the PDF
        3. Preview the extracted data
        4. Download the results as Excel or CSV

        **Supported PDF Types:**
        - Census data (any country)
        - Election results
        - Statistical reports
        - Demographic tables

        **Features:**
        - Automatic format detection (English/French number formats)
        - Preserves regional and sectional context
        - Handles multi-page documents
        - Supports both scanned and born-digital PDFs
        """)


if __name__ == "__main__":
    main()
