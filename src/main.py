
import opts
from manager import manager

def main():
    mag = manager()
    # mag.new()
    mag.load()

    mag.download_new_from_newpipe_db()
    mag.check_songs()
    # try: mag.check_songs()
    # except Exception as e:
    #     print(e)

    mag.save()


def add_keywords_from_ild_musisorter():
    import json
    old_path = "/sdcard/BKUP/newpipe/musisorter.json"
    with open(old_path, "r") as f:
        old_json = json.load(f)
    with open(opts.musisorter_path, "r") as f:
        new_json = json.load(f)
    
    for key, val in new_json.items():
        for bhal in old_json.get(key, [key]):
            val["keywords"].append(bhal)
    
    with open(opts.musisorter_path, "w") as f:
        json.dump(new_json, f, indent=4)
    

if __name__ == "__main__":
    main()
    # add_keywords_from_ild_musisorter()