
import json

import opts
from artist import Artist
from album import Album
from song import Song, get_song, song_info
from opts import ytmusic

def to_json(obj):
    if type(obj) == type(set()): return list(obj)
    return obj.__dict__

class Tracker:
    def __init__(self):
        self.artists = set()

        # do i even need these?
        self.all_artist_keys = set() # handled by get_albums
        self.all_song_keys = set() # gen on load(if song in artists.songs, then we already have the artist) # so that only new songs are tested for artist
    
    def add_artist(self, artist):
        self.artists.add(artist)
        # for key in artist.keys:
        #     self.all_artist_keys.add(key)
       
    def save(self):
        if opts.debug_no_edits_to_db: return

        self.save_sorter()
        dikt = self.__dict__
        # dikt.pop("all_artist_keys")
        dikt.pop("all_song_keys")
        with open(opts.musitracker_path, "w") as f:
            json.dump(dikt, f, indent=4, default=to_json)
    
    def save_sorter(self):
        if opts.debug_no_edits_to_db: return
        
        dikt = {}
        for artist in self.artists:
            artist.keywords.add(artist.name)
            dikt[artist.name] = {"check_stat": artist.check_stat, "keywords": list(artist.keywords), "keys": list(artist.keys)}
        with open(opts.musisorter_path, "w") as f:
            json.dump(dikt, f, indent=4)
    
    def new(self):
        pass

    def load(self):
        with open(opts.musitracker_path, "r") as f:
            celf = json.load(f)
        self.all_artist_keys = set(celf["all_artist_keys"])
        self.artists = set()
        for json_artist in celf["artists"]:
            artist = Artist(json_artist["name"], json_artist["keys"])
            artist.check_stat = json_artist["check_stat"]
            artist.ignore_no_songs = json_artist["ignore_no_songs"]
            artist.name_confirmation_status = json_artist["name_confirmation_status"]

            for json_album in json_artist["known_albums"]:
                album = Album("", "", "", "")
                album.__dict__ = json_album
                artist.known_albums.add(album)

            for song_data in json_artist["songs"]:
                song = Song(song_data["title"], song_data["key"], song_data["artist_name"])
                song.title_lock = song_data["title_lock"]
                song.info = song_info()
                song.info.__dict__ = song_data["info"]
                artist.songs.add(song)
            artist.keywords = set(json_artist["keywords"])
            self.artists.add(artist)

        self.gen_extra_data()
        self.load_sorter()
    
    def load_sorter(self):
        with open(opts.musisorter_path, "r") as f:
            dikt = json.load(f)
        # dont change all 3 in one go
        for artist in self.artists:
            data = dikt.get(artist.name, None)
            if not data:
                for key, val in dikt.items():
                    if any(
                        list(artist.keys).sort() == val["keys"].sort(),
                        list(artist.keywords).sort() == val["keywords"].sort(),
                        ):
                        data = val
                        artist.set_new_name(key)
                        break
            artist.keys = set(data["keys"])
            artist.keywords = set(data["keywords"])
            artist.check_stat = data["check_stat"]
    
    def gen_extra_data(self):
        for artist in self.artists:
            # for key in artist.keys:
            #     self.all_artist_keys.add(key)
            for song in artist.songs:
                self.all_song_keys.add(song.key)
    
    def confirm_artist_names(self):
        for artist in self.artists:
            if artist.name_confirmation_status: continue
            artist.confirm_name()


    def get_new_albums(self):
        new_albums = set()
        for artist in self.artists:
            if not artist.check_stat: continue
            for album in artist.get_new_albums(all_artist_keys=self.all_artist_keys):
                new_albums.add(album)
        return new_albums