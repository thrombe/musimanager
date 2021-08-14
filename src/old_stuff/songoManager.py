from YtDl import download_and_tag, tag_mp3, tag_m4a, innit
import json
import os
import requests


def songoBongo(_id, PATH,  sorter, cache):
    alldata, _file, _data, img, EXT = download_and_tag(_id, PATH, tag=False)
    
    dataAll = {} # trim alldata for what is needed
    cacheAttrs = ['artist', 'channel', 'track', 'album', 'creator', 'alt_title', 'title', 'description', 'thumbnail']
    for key, value in alldata.items():
        if key in cacheAttrs:
            dataAll[key] = value
    cache[_id] = dataAll
    
    _data['artists'] = _data['artists'].replace('/', ',')
    _data['artists'] = _data['artists'].replace(':', ' ')
    _data['artists'] = _data['artists'].replace('*', '')
    _data['artists'] = _data['artists'].replace('.', '')
    try:
        # print(_data['artists'])#########
        dataAll['artist'] = dataAll['artist'].replace('/', ',')
        dataAll['artist'] = dataAll['artist'].replace(':', ' ')
        dataAll['artist'] = dataAll['artist'].replace('*', '')
        dataAll['artist'] = dataAll['artist'].replace('.', '')
        # print(dataAll['artist'])########
    except: pass

    if EXT == 'mp3': tag_mp3(_file, _data, img)
    elif EXT == 'm4a': tag_m4a(_file, _data, img)

    #os.rename(_file, PATH + os.path.sep + _data['artists'] + os.path.sep + _id + "." + EXT) # moving the  file

def tag(_file, _id, cache, artist, EXT):
    _data = cache[_id]
    #if _data.get('artist', '') != '': artists = _data.get('artist')#.split(',')
    #else: artists = _data['channel']
    #print(_data.keys())
    #print(_data['channel'])
    _data = {"artists": artist, "name": _data['title'], "album": _data.get('album', ''), "thumbnail": _data['thumbnail']}
    
    img = requests.get(_data['thumbnail']).content
    
    if EXT == 'mp3': tag_mp3(_file, _data, img)
    elif EXT == 'm4a': tag_m4a(_file, _data, img)

def sort(path, sorter, cache):
    EXT, _, _ = innit(path)
    songIDs = sorter['songIDs']

    savedIDs = [] # update savedIDs to whats actually saved
    for directory, subdir, files in os.walk(path):
        if not files and not subdir: os.rmdir(directory) # clean empty folders
        for filee in files:
            if not filee or ('.mp3' not in filee and '.m4a' not in filee): continue
            filee = filee.rstrip('m4ap3').rstrip('.')
            savedIDs.append(filee)
    loop = songIDs.copy()
    for song in loop:
        if song not in savedIDs:
            songIDs.remove(song)
            print(f'{song} removed from songIDs from the sorter cuz its not saved offline anymore')
    
    # sort music in correct folders
    for directory, subdir, files in os.walk(path):
        for filee in files:
            done = False
            if not filee or ('.mp3' not in filee and '.m4a' not in filee): continue
            filee = filee.rstrip('m4ap3').rstrip('.')
            for key, value in sorter.items():
                if key == 'songIDs': continue
                if filee in value: # if song key is in the json in some artist
                    #directoryN = os.path.join(directory, os.pardir) # gets parent directory
                    if not os.path.exists(os.path.join(path, key, f'{filee}.{EXT}')): # key is artist name
                        tag(os.path.join(directory, f'{filee}.{EXT}'), filee, cache, key, EXT)
                        #print(f'sorting {cache[filee]["track"]} in {os.path.join(path, key, f"{filee}.{EXT}")}')
                        print(f'sorting {cache[filee]["track"]} in {key}')
                        if not os.path.exists(path + os.path.sep + key): # /HELLO/ and /hello/ are same in linux
                            print(f"making new folder {key}")
                            os.mkdir(path + os.path.sep + key)
                        os.rename(os.path.join(directory, f'{filee}.{EXT}'), os.path.join(path, key, f'{filee}.{EXT}'))
                    done = True
                    break
            if done: continue
            data = cache.get(filee, '')
            if not data: data, _, _, _, _ = download_and_tag(filee, path, tag=False, download=False)
            for keyy in ['artist', 'creator', 'channel', 'track', 'alt_title', 'title']:
                item = data.get(keyy, '')
                if not item: continue
                for key, values in sorter.items():
                    if key == 'songIDs': continue
                    for val in values:
                        if val in item:
                            #directoryN = os.path.join(directory, os.pardir) # gets parent directory
                            if not os.path.exists(os.path.join(path, key, f'{filee}.{EXT}')):
                                #print(os.path.join(directory, f'{filee}.{EXT}'), os.path.join(directoryN, key, f'{filee}.{EXT}'))######$
                                tag(os.path.join(directory, f'{filee}.{EXT}'), filee, cache, key, EXT)
                                #print(f'sorting {cache[filee]["track"]} in {os.path.join(path, key, f"{filee}.{EXT}")}')
                                print(f'sorting {cache[filee]["track"]} in {key}')
                                if not os.path.exists(path + os.path.sep + key): # /HELLO/ and /hello/ are same in linux
                                    print(f"making new folder {key}")
                                    os.mkdir(path + os.path.sep + key)
                                os.rename(os.path.join(directory, f'{filee}.{EXT}'), os.path.join(path, key, f'{filee}.{EXT}'))
                            done = True
                            break
                    if done: break # maybe check for more if sorting is bad
                if done: break

    for directory, subdir, files in os.walk(path):
        if not files and not subdir: 
            print(f"removing empty directory {directory}")
            os.rmdir(directory) # clean empty folders

    # all forders must currespond to sorter.keys (except songIDs)
    dirs = [os.listdir(path)][0]
    loop = sorter.copy()
    for key in loop.keys():
        if key == 'songIDs': continue
        if key not in dirs:
            if len(sorter[key]) > 1: 
                print(f'sorter[key] {sorter[key]} is deleted')
            sorter.pop(key)
     
def everything(dict, playlists, PATH, sorterFile, cachefile):
    with open(sorterFile, 'r') as sorter: # sorter = {foldername(ie artistname): {keywords like artist names, channel name}}
        sorter = json.load(sorter)
    with open(cachefile, 'r') as cache:
        cache = json.load(cache)
        # if not cache: cache = {}
    songIDs = sorter['songIDs']
    
    sort(PATH, sorter, cache)
    try:
    # if True:
        for playlist in playlists:
            for song in dict[playlist]:
                if song[2] in songIDs: continue
                songoBongo(song[2], PATH,  sorter, cache)
                songIDs.append(song[2])
        sort(PATH, sorter, cache)
    except Exception as e:
        traceback.print_exc()
        print(e)
        print(f'error!!!!!!!!!!!!!!!!!!!!!!!!! while downloading {song} or while sorting')

    # sort(PATH, sorter, cache)##########


    if songIDs[0] == '' and len(songIDs) > 1: songIDs.remove('')
    json.dump(sorter, fp = open(sorterFile, 'w'), indent=4)
    json.dump(cache, fp = open(cachefile, 'w'), indent=4)
    
    
if __name__ == "__main__":
    import traceback
    # download_and_tag('uIsuD8odKtI')
    #with open('/sdcard/0Python/Git/randomScripts/practicallyUseful/newpipe/outfile.json', 'r') as f:
        #dict = json.load(f)
    from playlistExtractNewpipe import quick_extract_for_songo_manager
    dict = quick_extract_for_songo_manager("/sdcard/BKUP/newpipe/")
    #print(dict['sawitch'])####
    everything(dict,['issac', 'sawitch', ], "/storage/F804-272A/däta/music(issac315)/IsBac", '/sdcard/BKUP/newpipe/musisorter.json', '/sdcard/BKUP/newpipe/musicache.json')
    
    input("\n\npress enter to exit")
