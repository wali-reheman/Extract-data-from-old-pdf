import os

import requests
import time
from pdf2image import convert_from_path

# set up url and its district,religion table, language table index
base_path="https://www.pbs.gov.pk/sites/default/files/population/2017/results/"
district = ["%.3d" % i for i in range(124,136)]
print(district)
religion = "09"
language = "11"

for i in district:
    pdf_link= base_path+i+religion+".pdf"
    response = requests.get(pdf_link,verify=False)
    if response.status_code == 200:
        with open(i+religion+".pdf", "wb") as f:
            f.write(response.content)
            time.sleep(3)
    else:
        print("Failed to download PDF")

print("DOWNLOAD MISSION COMPLETE")

file_path = "/Users/..." #Your path
file_list = os.listdir(file_path)
print(file_list)

for file in file_list:
    try:
        images = convert_from_path(file)
        for i in range(len(images)):
            images[i].save(file.strip(".pdf") + str(i) + '.jpg', 'JPEG')
    except:
        pass

print("CONVERT MISSION COMPLETE")

