import os  # Used for operating system interaction, such as listing files in a directory
import requests  # Allows you to send HTTP requests to download files
import time  # Used for pausing the execution of the script (time.sleep)
from pdf2image import convert_from_path  # Converts PDF files to images

# URL setup for downloading the PDFs
base_path = "https://www.pbs.gov.pk/sites/default/files/population/2017/results/"
districts = ["%.3d" % i for i in range(1, 136)]  # Generate district codes from 001 to 135
print(districts)  # Print the list of district codes
religion = "09"  # Suffix for the religion-specific PDF files
language = "11"  # Suffix for the language-specific PDF files (unused in this script)

# Download PDFs for each district
for district_code in districts:
    pdf_link = f"{base_path}{district_code}{religion}.pdf"  # Create the full URL to download the PDF
    response = requests.get(pdf_link, verify=False)  # Send a request to download the PDF, ignoring SSL verification

    # Check if the PDF was downloaded successfully
    if response.status_code == 200:
        with open(f"{district_code}{religion}.pdf", "wb") as f:
            f.write(response.content)  # Write the content to a PDF file locally
            time.sleep(3)  # Wait for 3 seconds before making the next request to avoid overloading the server
    else:
        print(f"Failed to download PDF for district {district_code}")  # Print an error message if download fails

print("DOWNLOAD MISSION COMPLETE")  # Indicate that all downloads are complete

# Directory where the downloaded PDFs are stored
file_path = "/Users/..."  # Replace with the actual path to your directory
file_list = os.listdir(file_path)  # List all files in the specified directory
print(file_list)  # Print the list of files found in the directory

# Convert each PDF file to JPEG images
for file in file_list:
    try:
        images = convert_from_path(os.path.join(file_path, file))  # Convert the PDF file to a list of images
        for i, image in enumerate(images):
            image.save(file.strip(".pdf") + str(i) + '.jpg', 'JPEG')  # Save each page as a JPEG file
    except Exception as e:
        print(f"Error converting {file}: {str(e)}")  # Print an error message if conversion fails

print("CONVERSION MISSION COMPLETE")  # Indicate that all conversions are complete
