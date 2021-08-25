
import requests
import os
from mutagen.mp4  import MP4, MP4Cover
from mutagen.id3 import ID3, APIC, TALB, TIT2, TPE1
import youtube_dl
from difflib import SequenceMatcher

import opts

def kinda_similar(str1, str2, threshold=0.4):
    # this func is terrible, use a different one
    perc = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    if perc >= threshold: return True
    else: return False

class Ytdl:
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
        self.ytd = youtube_dl.YoutubeDL(options)
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
        if other == None:
            return self.album == None
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
        return f"{self.title} {self.key} {self.artist_name}"
    
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
        if before: return path_before_sort
        if after: return path_after_sort
        return None

    def find_path(self):
        for dir, subdir, files in os.walk(ytdl.path):
            for file in files:
                key = file[0:-len(".m4a")]
                if key == self.key:
                    return os.path.join(dir, file)
        return None

    def download(self):
        print(f"downloading {self}")
        ytdl.ytd.download([self.url()])
    
    def get_info(self, force=False):
        if self.info != None and not force: return self.info
        self.info = song_info()
        self.info.load(ytdl.ytd.extract_info(self.url(), download=False))
        return self.info
    
    def get_info_from_tags_m4a(self):
        vid = MP4(self.path())
        self.title = vid.tags["\xa9nam"][0]
        self.info = song_info()
        self.info.album = vid.tags.get("\xa9alb", " ")[0]

    def get_info_from_tags(self):
        if ytdl.ext == "m4a": self.get_info_from_tags_m4a()
        elif ytdl.ext == "mp3": self.get_info_from_tags_mp3()

    def tag(self):
        print(f"tagging {self}")
        self.get_info()
        if not self.title_lock: self.title = self.info.titles[0]

        if opts.debug_no_edits_to_stored: return

        if ytdl.ext == "m4a": self.tag_m4a()
        elif ytdl.ext == "mp3": self.tag_mp3()

    def tag_m4a(self):
        video = MP4(self.path())
        img = requests.get(self.info.thumbnail_url).content
        video["\xa9nam"] = self.title
        video["\xa9ART"] = self.artist_name
        video["\xa9alb"] = self.info.album
        video["covr"] = [MP4Cover(img, imageformat=MP4Cover.FORMAT_JPEG)]
        video.save()
        
    def tag_mp3(self):
        audio = ID3(self.path())
        img = requests.get(self.info.thumbnail_url).content
        audio['TIT2'] = TIT2(encoding=3, text=self.title)
        audio['TPE1'] = TPE1(encoding=3, text=self.artist_name)
        audio['TALB'] = TALB(encoding=3, text=self.info.album)
        audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img)
        audio.save()

    # moves song with some basic checks/error prints
    def move(self, from_path, to_path, quiet=False):
        if not os.path.exists(from_path):
            print(f"file not here {from_path}")
            return
        new_dir = to_path.replace(os.path.basename(to_path), "")
        if not quiet: print(f"moving {self.title} in {new_dir}")
        if not os.path.exists(new_dir):
            print(f"making a directory {new_dir}")#{self.artist_name}")
            if not opts.debug_no_edits_to_stored:
                os.mkdir(new_dir)
        if not opts.debug_no_edits_to_stored:
            os.rename(from_path, to_path)
    
    # moves song from current path to path with correct artist_name
    def sort(self):
        current_path = self.find_path()
        path = self.path(after=True)
        if os.path.exists(path):
            print(f"song {self.key} already present")
            return
        print(f"sorting {self.title} in {self.artist_name}")
        self.move(current_path, path, quiet=True)

    def get_suitable_artist_using_tracker(self, tracker):
        try: self.get_info()
        except Exception as e:
            print(f"{e}", self)
            self.get_info_from_tags()
        
        # video unavailable
        if self.info.channel_id == None:
            for artist in tracker.artists:
                if artist.name == self.artist_name: return artist

        threshold = 0.75
        for artist in tracker.artists:
            if self.key in artist.keywords:
                return artist
        for artist in tracker.artists:
            if self.info.channel_id in artist.keys:
                return artist
        for artist in tracker.artists:
            # if any(kinda_similar(self.title.lower(), key.lower(), threshold) for key in artist.keywords):
            if any(kinda_similar(word.lower(), name.lower(), threshold) for name in self.info.artist_names for word in artist.keywords):
                return artist
        for artist in tracker.artists:
            if any([
                # any(kinda_similar(word.lower(), name.lower(), threshold) for name in self.info.artist_names for word in artist.keywords),
                any(kinda_similar(word.lower(), tag.lower(), threshold) for tag in self.info.tags for word in artist.keywords),
                any(kinda_similar(word.lower(), title.lower(), threshold) for title in self.info.titles for word in artist.keywords),
                ]):
                return artist
        
        return None

    # assumes that the song is newly added
    def sort_using_tracker(self, tracker):
        artist = self.get_suitable_artist_using_tracker(tracker)

        from artist import Artist

        if not artist:
            # new artist ig
            for char in "/:*.":
                self.artist_name.replace(char, "  ")            
            artist = Artist(self.artist_name, self.info.channel_id)
            tracker.artists.add(artist)

        self.artist_name = artist.name
        self.tag()
        self.sort()
        artist.add_song(self)

    def choose_better_title(self):
        print(self)
        import pprint
        pprint.pprint(self.info.__dict__)
        print("")
        title = input("title plz")
        self.title = title
        self.title_lock = True
        self.tag()

def get_song(key):
    song = Song(None, key, None)
    song.get_info()
    song.title = song.info.titles[0]
    song.arrtist_name = song.info.artist_names[0]
    return song