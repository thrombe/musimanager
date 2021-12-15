
import youtube_dl as ytdl
# import serde
import phrydy as tagg

import opts

class YTdl:
    def __init__(self, path, ext):
        self.ext = ext
        self.path = path
        options = {
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
        self.ytd = ytdl.YoutubeDL(options)
        self.ytm_url = "https://music.youtube.com/watch?v="
        # self.yt_url = "https://www.youtube.com/watch?v="

# global ytdl for all songs to use    
ytdl = YTdl(opts.musi_path, opts.musi_ext)

class SongInfo: # all metadata that i might care about

    def __init__(self):
        self.titles = None
        self.video_id = None
        self.tags = None
        self.thumbnail_url = None
        self.album = None
        self.artist_names = None
        self.channel_id = None
        self.uploader_id = None

    def load(self, ytdl_data):
        # theres also track and alt_title in case of ytm
        self.titles = [ # priority acc to index (low index is better) maybe check if in english?
            ytdl_data.get("track", None),
            ytdl_data.get("alt_title", None),
            ytdl_data["title"], # if this isnt there, something is wrong
            ]
        self.titles = [name for name in self.titles if name != None]

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
    def __init__(self, title, key, artist_name):
        self.title = title
        self.key = key # videoid
        self.artist_name = artist_name
        self.info = None
        self.last_known_path = None

        self.title_lock = False
    
    def from_key(key):
        pass

    def from_key_offline(key): #????????
        pass

    def url(self):
        return f"{ytdl.ytm_url}{self.key}"
