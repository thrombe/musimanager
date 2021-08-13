import requests
import os
import json
from mutagen.mp4  import MP4, MP4Cover
from mutagen.id3 import ID3, APIC, TALB, TIT2, TPE1
import youtube_dl

def innit(PATH):
    ## OPTIONS
    #PATH = "/sdcard/Documents"
    EXT = "m4a"
    ytdl_opts = {
        "format": "bestaudio",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            #'preferredquality': '160',
        }],
        "noplaylist": True,
        "quiet": True,
        #"download_archive": PATH + os.path.sep + "dl.archive",
        #"verbose": True
    }
    
    YTM_URL = "https://music.youtube.com/watch?v={_id}"
    YT_URL = "https://www.youtube.com/watch?v={_id}"
    
    ytdl_opts["postprocessors"][0]['preferredcodec'] = EXT
    ytdl_opts["outtmpl"] = PATH + os.path.sep + "%(id)s.%(ext)s"
    YTD = youtube_dl.YoutubeDL(ytdl_opts)
    return EXT, YTD, YTM_URL

def ytdl_get_info(_id, YTD, URL, down):
    _data = YTD.extract_info(URL.format(_id=_id), download = down)
    if _data.get('artist', '') != '': artists = _data.get('artist')#.split(',')
    else: artists = _data['channel']
    #print(_data.keys())
    #print(_data['channel'])
    return _data, {"artists": artists, "name": _data['title'], "album": _data.get('album', ''), "thumbnail": _data['thumbnail']}

def tag_m4a(_file, _data, img):
    video = MP4(_file)
    video["\xa9nam"] = _data['name'] # title
    video["\xa9ART"] = _data['artists']
    if _data.get('album', '') != '':
        video["\xa9alb"] = _data['album']
    video["covr"] = [MP4Cover(img, imageformat=MP4Cover.FORMAT_JPEG)]
    video.save()

def tag_mp3(_file, _data, img):
    audio = ID3(_file)
    audio['TPE1'] = TPE1(encoding=3, text=_data['artists'])
    audio['TIT2'] = TIT2(encoding=3, text=_data['name'])
    if _data.get('album', '') != '':
        audio['TALB'] = TALB(encoding=3, text=_data["album"])
    audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img)
    audio.save()

def download_and_tag(_id, PATH, tag = True, download = ''):
    EXT, YTD, URL = innit(PATH)
    # print(PATH, os.path.sep, _id, EXT)######
    _file = PATH + os.path.sep + _id + "." + EXT
    
    truthness = not os.path.exists(_file) # if file exists, dont download and tag, else do both
    if download != '': truthness = download
    if download != False: print(f"[I]{' NOT'*(not truthness)} DOWNLOADING: {_id}")
    alldata, _data = ytdl_get_info(_id, YTD, URL, truthness)
    
    img = requests.get(_data['thumbnail']).content

    if not tag: return alldata, _file, _data, img, EXT # if tag variable if False, dont tag
    if EXT == 'mp3': tag_mp3(_file, _data, img)
    elif EXT == 'm4a': tag_m4a(_file, _data, img)

if __name__ == "__main__":
    download_and_tag('uIsuD8odKtI', "/sdcard/Documents")    