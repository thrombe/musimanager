
# import youtube_dl as ytdl
import yt_dlp as yt_dl
import serde
import phrydy as tagg
import requests
import os
import subprocess
import ffmpeg
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
            # "skip_playlist_after_errors": 5,
            "extract_flat": "in_playlist", # dont recursively seek for every video when in playlist
            # "concurrent_fragment_downloads": 100,
        }
        self.ytd = yt_dl.YoutubeDL(options)
        self.yt_url = "https://youtu.be/"
        # self.yt_url = "https://music.youtube.com/watch?v="
        # self.yt_url = "https://www.youtube.com/watch?v="

# global ytdl for all songs to use    
ytdl = YTdl(opts.musi_path, opts.musi_download_ext)
temp_ytdl = YTdl(opts.temp_dir, "flac")
musicache = None

class SongInfo(serde.Model): # all metadata that i might care about
    titles: serde.fields.List(serde.fields.Str())
    video_id: serde.fields.Str()
    duration: serde.fields.Optional(serde.fields.Float())
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
            duration = None,
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
        duration = float(ytdl_data["duration"])
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
        return SongInfo(titles=titles, video_id=video_id, duration=duration, tags=tags, thumbnail_url=thumbnail_url,
                        album=album, artist_names=artist_names, channel_id=channel_id, uploader_id=uploader_id)

class Song(serde.Model):
    title: serde.fields.Optional(serde.fields.Str())
    key: serde.fields.Optional(serde.fields.Str())
    artist_name: serde.fields.Optional(serde.fields.Str())
    info: serde.fields.Nested(SongInfo)
    last_known_path: serde.fields.Optional(serde.fields.Str())

    def new(title, key, artist_name, path=None):
        return Song(
            title = title,
            key = key, # youtube videoid
            artist_name = artist_name,
            info = SongInfo.empty(),
            last_known_path = path,
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
        temp_path = f"{temp_ytdl.path}{self.key}.{temp_ytdl.ext}"
        download = not os.path.exists(temp_path)
        ytdl_data = temp_ytdl.ytd.extract_info(self.url(), download=download)

        # ytdl_data = ytdl.ytd.extract_info(self.url(), download=False)
        self.get_info_ytdl_data(ytdl_data)

        # temp_path = f"{opts.temp_dir}{self.key}.flac"
        # if os.path.exists(temp_path2): return temp_path

        # # youtube-dl -f bestaudio VIDEO_URL -o - 2>/dev/null | ffplay -nodisp -autoexit -i - &>/dev/null
        # proc = subprocess.Popen(f"yt-dlp --quiet -f bestaudio {self.url()} -o - ", shell=True, stdout=subprocess.PIPE)
        # i = ffmpeg.input("pipe:", f="webm", loglevel="panic").output(temp_path, f="flac").run_async(pipe_stdin=True)
        # while True:
        #     a = proc.stdout.read(512)
        #     if not a: break
        #     i.stdin.write(a)

        self.tag(path=temp_path, img_bytes=self.download_cover_image())

        return temp_path

    def tag(self, path=None, img_bytes=None):
        if path is None:
            path = self.last_known_path
        else:
            self.last_known_path = path
        mf = tagg.MediaFile(path)
        mf.album = self.info.album
        mf.artist = self.artist_name
        mf.title = self.title

        if img_bytes is not None: 
            mf.images = [tagg.mediafile.Image(data=img_bytes)]
        
        mf.save()

    def download_cover_image(self):
        img = requests.get(self.info.thumbnail_url).content
        imaag = io.BytesIO()
        Image.open(io.BytesIO(img)).save(imaag, "png")
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
        return s

    # TODO: how to confirm if filename is key?
    def from_file(path):
        s = Song.new(None, path.split(os.path.sep)[-1].split(".")[0], None, path=path)
        mf = tagg.MediaFile(path)
        s.title = mf.title
        s.artist_name = mf.artist
        s.info.album = mf.album
        s.info.duration = mf.length
        return s

    def get_duration(self, path=None):
        if self.info.duration is not None:
            return self.info.duration
        if path is None and self.last_known_path is not None:
            path = self.last_known_path
        mf = tagg.MediaFile(path)
        self.info.duration = mf.length
        return self.info.duration

    def url(self):
        return f"{ytdl.yt_url}{self.key}"

    def get_info(self, force_offline_only=False):
        if musicache is not None:
            info = musicache.get(f"{self.key}", None)
            if info is not None:
                return self.get_info_ytdl_data(info)
        if force_offline_only: return None
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
