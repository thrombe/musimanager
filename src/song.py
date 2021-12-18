
# import youtube_dl as ytdl
import yt_dlp as ytdl
import serde
import phrydy as tagg
import requests
import os
from PIL import Image
import io

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
            "quiet": opts.ytdl_quiet,
            "outtmpl": self.path + "%(id)s.%(ext)s",
            "verbose": False,
            "no_warnings": True,
            "noprogress": True,
            "geo_bypass": True,
            # "geo_bypass_country": "JP",
            # "skip_playlist_after_errors": 5,
            "extract_flat": "in_playlist", # dont recursively seek for every video when in playlist
        }
        self.ytd = ytdl.YoutubeDL(options)
        self.ytm_url = "https://music.youtube.com/watch?v="
        # self.yt_url = "https://www.youtube.com/watch?v="

# global ytdl for all songs to use    
ytdl = YTdl(opts.musi_path, opts.musi_download_ext)
musicache = None

class SongInfo(serde.Model): # all metadata that i might care about
    titles: serde.fields.List(serde.fields.Str())
    video_id: serde.fields.Str()
    tags: serde.fields.List(serde.fields.Str())
    thumbnail_url: serde.fields.Str()
    album: serde.fields.Optional(serde.fields.Str())
    artist_names: serde.fields.List(serde.fields.Str())
    channel_id: serde.fields.Str()
    uploader_id: serde.fields.Str()

    def empty():
        return SongInfo(
            titles = [""],
            video_id = "",
            tags = [],
            thumbnail_url = "",
            album = "",
            artist_names = [""],
            channel_id = "",
            uploader_id = "",
        )

    def load(ytdl_data):
        # theres also track and alt_title in case of ytm
        titles = [ # priority acc to index (low index is better) maybe check if in english?
            ytdl_data.get("track", None),
            ytdl_data.get("alt_title", None),
            ytdl_data["title"], # if this isnt there, something is wrong
            ]
        titles = [name for name in titles if name != None]

        video_id = ytdl_data["id"]
        tags = ytdl_data.get("tags", [])
        thumbnail_url = ytdl_data["thumbnail"]
        album = ytdl_data.get("album", "")
        
        artist_names = [ # priority acc to index (low index is better) maybe check if in english?
            ytdl_data.get("artist", None), # aimer
            ytdl_data.get("uploader", None), # aimer - topic
            ytdl_data.get("creator", None), #???
            ytdl_data["channel"], # aimer official youtube
        ]
        artist_names = [name for name in artist_names if name != None]

        # donno whats diff here
        channel_id = ytdl_data["channel_id"]
        uploader_id = ytdl_data["uploader_id"]
        return SongInfo(titles=titles, video_id=video_id, tags=tags, thumbnail_url=thumbnail_url, album=album,
                        artist_names=artist_names, channel_id=channel_id, uploader_id=uploader_id)

class Song(serde.Model):
    title: serde.fields.Optional(serde.fields.Str())
    key: serde.fields.Optional(serde.fields.Str())
    artist_name: serde.fields.Optional(serde.fields.Str())
    info: serde.fields.Optional(serde.fields.Nested(SongInfo))
    last_known_path: serde.fields.Optional(serde.fields.Str())
    title_lock: serde.fields.Optional(serde.fields.Bool())

    def new(title, key, artist_name, path=None):
        return Song(
            title = title,
            key = key, # youtube videoid
            artist_name = artist_name,
            info = None,
            last_known_path = path,
            title_lock = False,
        )
        
    def get_path(self):
        pass
    
    def download(self):
        ytdl.ytd.download([self.url()])
        self.last_known_path = f"{ytdl.path}{self.key}.{ytdl.ext}"

    def download_and_get_info(self):
        ytdl_data = ytdl.ytd.extract_info(self.url(), download=True)
        self.last_known_path = f"{ytdl.path}{self.key}.{ytdl.ext}"
        return self.get_info_ytdl_data(ytdl_data)

    def temporary_download(self):
        ytdl_data = ytdl.ytd.extract_info(self.url(), download=True)
        self.get_info_ytdl_data(ytdl_data)
        temp_path1 = f"{ytdl.path}{self.key}.{ytdl.ext}"
        temp_path2 = f"{opts.temp_dir}{self.key}.{ytdl.ext}"
        os.rename(temp_path1, temp_path2)
        return temp_path2

    def tag(self, path=None, img_bytes=None):
        if path is None:
            path = self.last_known_path
        else:
            self.last_known_path = path
        mf = tagg.MediaFile(path)
        mf.album = self.info.album
        mf.artist = self.artist_name
        mf.title = self.title

        if img_bytes is None: return
        mf.images = [tagg.mediafile.Image(data=img_bytes)]

    def download_cover_image(self):
        img = requests.get(self.info.thumbnail_url).content
        imaag = io.BytesIO()
        Image.open(io.BytesIO(img)).convert("RGB").save(imaag, "jpeg")
        return imaag.getvalue()

    def get_cover_image_from_metadata(self):
        mf = tagg.MediaFile(self.last_known_path)
        if len(mf.images) == 0: return None
        return bytes(mf.images[0].data)

    def set_musicache_refrence(tracker):
        global musicache
        musicache = tracker.musicache

    def from_key(key):
        s = Song.new(None, key, None)
        s.get_info()
        s.title = s.info.titles[0]
        s.artist_name = s.info.artist_names[0]
        return s

    # TODO: how to confirm if filename is key?
    def from_file(path):
        s = Song.new(None, path.split(os.path.sep)[-1].split(".")[0], None, path=path)
        mf = tagg.MediaFile(path)
        s.title = mf.title
        s.artist_name = mf.artist
        s.info = SongInfo.empty()
        s.info.album = mf.album
        return s

    def url(self):
        return f"{ytdl.ytm_url}{self.key}"

    def get_info(self):
        if musicache is not None:
            info = musicache.get(f"{self.key}", None)
            if info is not None:
                self.info = SongInfo.load(info)
                return self.info
        return self.get_info_yt()

    def get_info_yt(self):
        ytdl_data = ytdl.ytd.extract_info(self.url(), download=False)
        return self.get_info_ytdl_data(ytdl_data)
    
    def get_info_ytdl_data(self, ytdl_data):
        if musicache is not None:
            musicache[f"{self.key}"] = ytdl_data
        self.info = SongInfo.load(ytdl_data)
        if self.artist_name is None: self.artist_name = self.info.artist_names[0]
        if self.title is None: self.title = self.info.titles[0]
        if self.key is None: self.key = self.info.key
        return self.info
