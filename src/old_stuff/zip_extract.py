from zipfile import ZipFile
import os

def extract_zip(input_zip):
    input_zip = ZipFile(input_zip)
    return {name: input_zip.read(name) for name in input_zip.namelist()}

def get_latest_zip_path(path):
    for directory, subdir, files in os.walk(path):
        files = [directory+file for file in files]
        files.sort(key = os.path.getctime, reverse = True)
        # files.sort(key = os.path.getmtime, reverse = True)
        #print(files)
        for file in files:
            if ".zip" in file:
                return file


if __name__ == "__main__":
    path = "/sdcard/BKUP/newpipe/"
    db = extract_zip(get_latest_zip_path(path))["newpipe.db"]
    # print(type(zip_content))

    with open(path+"newpipe.db", "wb") as f:
        f.write(db)

    os.remove(path+"newpipe.db")