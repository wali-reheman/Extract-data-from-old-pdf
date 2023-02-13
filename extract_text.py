import os
import re
import cv2
import pytesseract
import pandas as pd
import logging

# configure logging
logging.basicConfig(filename="logfile.log", level=logging.ERROR)

# Trim titles of the page
def delete_to_k(lst, strings_to_search_for):
    for i, elem in enumerate(lst):
        for string in strings_to_search_for:
            if isinstance(elem, str) and string in elem:
                del lst[:i]
                return lst
    return lst

strings_to_search_for=['DISTRICT', 'TEHSIL', 'DIVISION', 'AGENCY', 'TALUKA','FR']


extracted = pd.DataFrame()

path = "/Users/wali/Documents/GA/Pakistan/Religion"
file_list = os.listdir(path)
print(file_list)

# Load the PDF as an image
for i in file_list:
    full_path = os.path.join(path, i)
    try:
        image = cv2.imread(full_path, cv2.IMREAD_GRAYSCALE)
        image = cv2.resize(image, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
        text = pytesseract.image_to_string(image, config="--psm 6")
        lines = text.strip().split("\n")
        lines = [line for line in lines if line.strip() and line not in ['OVERALL', 'RURAL', 'URBAN']]
        delete_to_k(lines,strings_to_search_for)
        data = []
        if "a" in lines:
            lines.remove("a")
        matchers = ['ALL', 'DISTRICT', 'TEHSIL', 'DIVISION', 'AGENCY', 'TALUKA']
        matching = [s for s in lines if any(lines in s for lines in matchers)]
        region = []
        result = []
        for j, line in enumerate(matching):
            if any(keyword in line for keyword in ['DISTRICT', 'TEHSIL', 'DIVISION', 'AGENCY', 'TALUKA']):
                region.append(line)
                try:
                    result.append(matching[j + 1])
                except IndexError:
                    logging.error(f"An error occurred while processing {i}")
                    pass
        for r in result:
            r = re.sub(r"( SEXE.|SEXE.)", "", r)
            data.append(r)
        dataset = []
        for w in data:
            dataset.append(w.split(" "))
        if len(dataset[0]) == 7:
            df = pd.DataFrame(dataset, columns=['SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN', "HINDU", 'QADIANI/AHMADI',
                                                'CASTE/SCHEDULED'])
        elif len(dataset[0])==8:
            df = pd.DataFrame(dataset, columns=['SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN', "HINDU", 'QADIANI/AHMADI',
                                                'CASTE/SCHEDULED', 'OTHERS'])
        elif len(dataset[0])==9:
            df = pd.DataFrame(dataset, columns=['SEX', 'TOTAL', 'MUSLIM', 'CHRISTIAN', "HINDU", 'QADIANI/AHMADI',
                                                'CASTE/SCHEDULED', 'OTHERS','EXTRACOL'])
        df['REGION'] = region
        df['FILE_NAME'] = i
        extracted = pd.concat([extracted, df], axis=0)
    except Exception as e:
        logging.error(f"An error occurred while processing the file {i}: {e}")

extracted.to_excel("Pakistan_religion.xlsx",index=False)