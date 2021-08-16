
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

    def __init__(self):
        self.titles = None
        self.video_id = None
        self.tags = None
        self.thumbnail_url = None
        self.album = None
        self.artist_names = None
        self.channel_id = None
        self.uploader_id = None

    def __str__(self):
        return f"{self.__dict__}"
    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

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
        self.title = title # local one
        self.key = key # videoid
        self.artist_name = artist_name # the local name - i.e the folder name
        self.title_lock = False
        self.info = None
    
    def __str__(self):
        return f"{self.name} {self.key} {self.artist_name}"
    
    def __hash__(self):
        return hash(self.__str__())
    
    def __eq__(self, other):
        #if not isinstance(other, type(self)): return False
        return self.__str__() == other.__str__() # sorting to eliminate position probs

    def url(self):
        return f"{ytdl.ytm_url}{self.key}"

    def path(self, before=False, after=False):
        path_before_sort = f"{ytdl.path}{self.key}.{ytdl.ext}"
        path_after_sort = f"{ytdl.path}{self.artist_name}{os.path.sep}{self.key}.{ytdl.ext}"
        if after: return path_after_sort
        if before: return path_before_sort
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
        print("downloading {self}")
        ytdl.ytd.download([self.url()])
    
    def get_info(self, force=False):
        if self.info != None and not force: return self.info
        self.info = song_info()
        self.info.load(ytdl.ytd.extract_info(self.url(), download=False))
        return self.info
    
    def tag(self):
        print(f"tagging {self}")
        self.get_info()
        if not self.title_lock: self.title = self.info.titles[0]

        if opts.debug_no_edits_to_stored: return

        if ytdl.ext == "m4a": self.tag_m4a()
        elif ytdl.ext == "mp3": self.tag_mp3()

    def tag_m4a(self):
        video = MP4(self.path())
        img = requests.get(self.info.thumbnail).content
        video["\xa9nam"] = self.title
        video["\xa9ART"] = self.artist_name
        video["\xa9alb"] = self.info.album
        video["covr"] = [MP4Cover(img, imageformat=MP4Cover.FORMAT_JPEG)]
        video.save()
        
    def tag_mp3(self):
        audio = ID3(self.path())
        img = requests.get(self.info.thumbnail).content
        audio['TIT2'] = TIT2(encoding=3, text=self.title)
        audio['TPE1'] = TPE1(encoding=3, text=self.artist_name)
        audio['TALB'] = TALB(encoding=3, text=self.info.album)
        audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img)
        audio.save()

    def sort(self, current_path=None):
        if current_path: self.tag() # the need of passing current_path means that its in a different artist folder

        path = self.path(after=True)
        if os.path.exists(path):
            print(f"song {self.key} already present")
            return
        print(f"sorting {self.title} in {self.artist_name}")
        pardir = os.path.join(path, os.pardir)
        if not os.path.exists(pardir):
            print(f"making a directory {self.artist_name}")
            if not opts.debug_no_edits_to_stored:
                os.mkdir(pardir)
        if not opts.debug_no_edits_to_stored:
            if not current_path: os.rename(self.path(before=True), path)
            else: os.rename(current_path, path)

    # assumes that the song is newly added
    def sort_using_tracker(self, tracker):
        self.get_info()
        
        def found(song, artist):
            song.artist_name = artist.name
            artist.songs.add(song)
            artist.keys.add(song.get_info().channel_id)
            song.tag()
            song.sort()

        for artist in tracker.artists:
            if self.key in artist.keywords:
                found(self, artist)
                return
        for artist in tracker.artists:
            if self.info.channel_id in artist.keys:
                found(self, artist)
                return
        for artist in tracker.artists:
            if any(
                any(artist.name.lower() in name.lower() for name in song.info.artist_names),
                any(artist.name.lower() in tag.lower() for tag in song.info.tags),
                any(artist.name.lower() in title.lower() for title in song.info.titles),
                ):
                found(self, artist)
                return
        
        # new artist ig
        for char in "/:*.":
            self.artist_name.replace(char, "  ")
        
        artist = Artist(self.artist_name, self.info.channel_id)
        tracker.artists.add(artist)
        found(self, artist)

    def check_if_in_tracker(self, tracker):
        return any(self.key == song.key for artist in tracker.artists for song in artist.songs)
    
    def choose_better_title(self):
        print(self)
        import pprint
        pprint.pprint(self.info.__dict__)
        print()
        title = input("title plz")
        self.title = title
        self.title_lock = True
        self.tag()

    """
    def json_load(self, dict): # not sure, gotta try
        self.__dict__.update(dict)
    """

def get_song(key):
    song = Song(None, key, None)
    song.get_info()
    song.title = song.info.titles[0]
    song.arrtist_name = song.info.artist_names[0]
    return song