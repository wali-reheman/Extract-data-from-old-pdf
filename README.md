
# Pakistan Census Data Extraction

## Project Overview

This repository contains scripts for downloading and processing PDF files from the Pakistan census. The process involves extracting data from downloaded PDFs and converting this information into structured formats suitable for analysis. Note that extracting text from old pdf file could be very messy, if requires many times of adjustment to accommodate codes to random changes in the formats of pdf file.

The main components include:

1. `download_files.py` - This script downloads PDF files containing census data and converts them to JPEG images for easier processing.
2. `extract_text.py` - Uses Optical Character Recognition (OCR) to extract text from the converted JPEG images and saves the data into an Excel file.

## Prerequisites

Before running these scripts, ensure you have the following installed:
- Python 3.8 or higher
- Libraries: `requests`, `pdf2image`, `Pillow`, `opencv-python`, `pytesseract`, and `pandas`.
- Tesseract-OCR: This project uses Pytesseract, which is a wrapper for Google’s Tesseract-OCR Engine. It must be installed separately from the Python packages.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/your-repository.git
   ```
2. Navigate to the cloned directory:
   ```
   cd your-repository
   ```
3. Install the required Python libraries:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the download script:

```bash
python download_files.py
```
This script will download all PDFs specified within the script and convert each to JPEG format, storing them in the designated directory.

### Running the extraction script:

```bash
python extract_text.py
```
After converting the PDFs to images, this script will perform OCR on the images to extract text and save it in an Excel file named `Pakistan_religion.xlsx`.

## Configuration

- You may need to adjust the paths and specific URLs in the scripts to match your directory structure or to point to different data sources.
- OCR settings can be tuned in `extract_text.py` for better accuracy depending on the quality of the images.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.

## Contact

For support or queries, contact [rw8143a@american.edu](mailto:rw8143a@american.edu).
