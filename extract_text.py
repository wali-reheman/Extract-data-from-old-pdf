import os  # Used for operating system dependent functionality like reading files
import re  # Regular expression library for text matching and manipulation
import cv2  # OpenCV library for handling image operations
import pytesseract  # OCR library to convert image text to string data
import pandas as pd  # Pandas library for data manipulation and analysis
import logging  # Used for logging error messages in a file

# Configure logging to capture errors in a logfile
logging.basicConfig(filename="logfile.log", level=logging.ERROR)

# Function to remove unnecessary text up to a specified keyword
def delete_to_k(lst, strings_to_search_for):
    for t, elem in enumerate(lst):
        for string in strings_to_search_for:
            if string in elem:
                del lst[:t]  # Delete all elements in the list before the keyword
                return lst  # Return the trimmed list
    return lst  # Return the original list if no keyword is found

# List of keywords to start processing text data
strings_to_search_for = ['FR','DISTRICT', 'TEHSIL', 'DIVISION', 'AGENCY','TALUKA','MUSAKHEL','DE-EXCLUDED','F.R' ]

# DataFrame to store all extracted information
extracted = pd.DataFrame()

# Directory containing images to be processed
path = "your_path/Pakistan/Religion"
file_list = os.listdir(path)  # List of all files in the specified directory
print(file_list)

# Loop through each image file for processing
for i in file_list:
    print(i)  # Print the current file being processed
    full_path = os.path.join(path, i)  # Create full path to the image file
    try:
        # Read the image in grayscale to enhance OCR accuracy
        image = cv2.imread(full_path, cv2.IMREAD_GRAYSCALE)
        # Resize the image to make the text more clear for OCR
        image = cv2.resize(image, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
        # Use OCR to extract text from the image
        text = pytesseract.image_to_string(image, config="--psm 6 --oem 1")
        # Split text into lines and remove empty or irrelevant lines
        lines = text.strip().split("\n")
        lines = [line for line in lines if line.strip() and line not in ['OVERALL', 'RURAL', 'URBAN']]
        print(lines)
        # Trim lines up to the first relevant keyword
        delete_to_k(lines, strings_to_search_for)
        data = []
        # Further cleaning of lines
        if "a" in lines:
            lines.remove("a")
        matchers = ['ALL'] + strings_to_search_for
        # Match lines that contain any of the specified keywords
        matching = [s for s in lines if any(x in s for x in matchers)]
        print(matching)
        region = []
        result = []
        # Extract region data and corresponding results
        for j, line in enumerate(matching):
            if any(keyword in line for keyword in strings_to_search_for):
                region.append(line)
                try:
                    result.append(matching[j + 1])
                except IndexError:
                    logging.error(f"An error occurred while processing {i}")
        # Clean up extracted results
        for r in result:
            r = re.sub(r"( SEXE.|SEXE.)", "", r)
            data.append(r)
        dataset = [w.split(" ") for w in data]
        max_columns = max(len(row) for row in dataset)  # Determine the max number of columns
        # Define column headers based on the number of columns detected
        if max_columns == 7:
            columns = ['SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN', "HINDU", 'QADIANI/AHMADI', 'CASTE/SCHEDULED']
        elif max_columns == 8:
            columns = ['SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN', "HINDU", 'QADIANI/AHMADI', 'CASTE/SCHEDULED', 'OTHERS']
        elif max_columns == 9:
            columns = ['SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN', "HINDU", 'QADIANI/AHMADI', 'CASTE/SCHEDULED', 'OTHERS', 'EXTRACOL']
        # Create a DataFrame from the dataset
        df = pd.DataFrame(dataset, columns=columns)
        df['REGION'] = region
        df['FILE_NAME'] = i
        # Append this DataFrame to the main extracted DataFrame
        extracted = pd.concat([extracted, df], axis=0)
    except Exception as e:
        logging.error(f"An error occurred while processing the file {i}: {e}")

# Save the compiled data to an Excel file
extracted.to_excel("Pakistan_religion.xlsx", index=False)
