
import requests
import os
from mutagen.mp4  import MP4, MP4Cover
from mutagen.id3 import ID3, APIC, TALB, TIT2, TPE1
import youtube_dl

import opts

class Ytdl:
    def __init__(self, path, ext):
        self.ext = ext
        self.path = path
        opts = {
            "format": "bestaudio",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                #'preferredquality': '160', # youtube caps at 160
                "preferredcodec": self.ext
            }],
            "noplaylist": True,
            "quiet": opts.ytdl_quiet, #True,
            "outtmpl": self.path + "%(id)s.%(ext)s"
            #"verbose": True
        }
        self.ytd = youtube_dl.YoutubeDL(opts)
        self.ytm_url = "https://music.youtube.com/watch?v="
        # self.yt_url = "https://www.youtube.com/watch?v="

# global ytdl for all songs to use    
ytdl = Ytdl(opts.musi_path, opts.musi_ext)

class song_info: # all metadata that i might care about
    def __init__(self, ytdl_data):
        # theres also track and alt_title in case of ytm
        self.titles = [ # priority acc to index (low index is better) maybe check if in english?
            ytdl_data.get("track", None),
            ytdl_data.get("alt_title", None),
            ytdl_data["title"], # if this isnt there, something is wrong
            ]
        self.title = [name for name in self.titles if name != None]

        self.video_id = ytdl_data["id"]
        self.tags = ytdl_data.get("tags", [])
        self.thumbnail_url = ytdl_data["thumbnail"]
        self.album = ytdl_data.get("album", "")
        
        self.artist_names = [ # priority acc to index (low index is better) maybe check if in english?
            ytdl_data.get("artist", None), # aimer
            ytdl_data.get("uploader", None), # aimer - topic
            ytdl_data.get("creator", None), #???
            ytdl_data["channel"], # aimer official youtube
        ]
        self.artist_names = [name for name in self.artist_names if name != None]

        # donno whats diff here
        self.channel_id = ytdl_data["channel_id"]
        self.uploader_id = ytdl_data["uploader_id"]
    

class Song:
    def __init__(self, title, key):
        self.title = title
        self.key = key # videoid
        self.artist_name = artist_name # the local name - i.e the folder name
        # self.path = "" # ???
        self.info = None
    
    def url(self):
        return f"{ytdl.ytm_url}{self.key}"

    def path(self):
        path_before_sort = f"{ytdl.path}{self.key}.{ytdl.ext}"
        path_after_sort = f"{ytdl.path}{self.artist_name}{os.path.sep}{self.key}.{ytdl.ext}"
        before = os.path.exists(path_before_sort)
        after = os.path.exists(path_after_sort)
        if before and after:
            print(f"something wrong, both files present {self.key}")
            return
        if before and not after: return path_before_sort
        if after and not before: return path_after_sort
        if not before and not after: return path_before_sort
        # all cases should be covered here

    def download(self):
        ytdl.ytd.download([self.url()])
    
    def get_info(self, force=False):
        if self.info != None and not force: return self.info
        self.info = song_info(ytdl.ytd.extract_info(self.url(), download=False))
        return self.info
    
    def tag(self):
        if ytdl.ext == "m4a": self.tag_m4a()
        elif ytdl.ext == "mp3": self.tag_mp3()

    def tag_m4a(self):
        video = MP4(self.path())
        self.get_info()
        img = requests.get(self.info.thumbnail).content
        video["\xa9nam"] = self.title
        video["\xa9ART"] = self.artist_name
        video["\xa9alb"] = self.info.album
        video["covr"] = [MP4Cover(img, imageformat=MP4Cover.FORMAT_JPEG)]
        video.save()
        
    def tag_mp3(self):
        audio = ID3(self.path())
        self.get_info()
        img = requests.get(self.info.thumbnail).content
        audio['TIT2'] = TIT2(encoding=3, text=self.title)
        audio['TPE1'] = TPE1(encoding=3, text=self.artist_name)
        audio['TALB'] = TALB(encoding=3, text=self.info.album)
        audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img)
        audio.save()

    def json_load(self, dict): # not sure, gotta try
        self.__dict__.update(dict)
        !lol