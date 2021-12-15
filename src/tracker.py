import os
import json

import opts
import song
import artist
import album

def to_json(obj):
    if type(obj) == type(set()): return list(obj)
    return obj.__dict__

class Tracker:
    def __init__(self):
        self.artists = set()

        # TODO: yeet these as not in use anymore
        # do i even need these?
        self.all_artist_keys = set() # handled by get_albums
        self.all_song_keys = set() # gen on load(if song in artists.songs, then we already have the artist) # so that only new songs are tested for artist
    
    def load(self):
        if not os.path.exists(opts.musitracker_path):
            if opts.debug_no_edits_to_db: return
            with open(opts.musitracker_path, "w") as f:
                f.write('{"all_artist_keys": [], "artists": [] }')
            return
            
        with open(opts.musitracker_path, "r") as f:
            celf = json.load(f)
        self.all_artist_keys = set(celf["all_artist_keys"])
        self.artists = set()
        for json_artist in celf["artists"]:
            artst = artist.Artist(json_artist["name"], json_artist["keys"])
            artst.check_stat = json_artist["check_stat"]
            artst.ignore_no_songs = json_artist["ignore_no_songs"]
            artst.name_confirmation_status = json_artist["name_confirmation_status"]

            for json_album in json_artist["known_albums"]:
                albm = album.Album("", "", "", "")
                albm.__dict__ = json_album
                artst.known_albums.add(albm)

            for song_data in json_artist["songs"]:
                sng = song.Song(song_data["title"], song_data["key"], song_data["artist_name"])
                sng.title_lock = song_data["title_lock"]
                sng.unsorted_path = song_data.get("unsorted_path", "")
                sng.info = song.SongInfo()
                sng.info.__dict__ = song_data["info"]
                artst.songs.add(sng)
            artst.keywords = set(json_artist["keywords"])
            self.artists.add(artst)

        self.gen_extra_data()
        self.load_sorter()
    
    def load_sorter(self):
        with open(opts.musisorter_path, "r") as f:
            dikt = json.load(f)
        # dont change all 3 in one go
        for artst in self.artists:
            data = dikt.get(artst.name, None)
            if not data:
                for key, val in dikt.items():
                    if any([
                        list(artst.keys).sort() == val["keys"].sort(),
                        list(artst.keywords).sort() == val["keywords"].sort(),
                    ]):
                        data = val
                        artst.set_new_name(key)
                        break
            artst.keys = set(data["keys"])
            artst.keywords = set(data["keywords"])
            artst.check_stat = data["check_stat"]
    
    def gen_extra_data(self):
        for artst in self.artists:
            # for key in artist.keys:
            #     self.all_artist_keys.add(key)
            for sng in artst.songs:
                self.all_song_keys.add(sng.key)
    
    def get_song_paths(dir: str, ext: list=['mp3', 'm4a']):
        song_paths = []
        for basepath, _, files in os.walk(dir):
            for f in files:
                if f.split(".")[-1] in ext:
                    song_paths.append(os.path.join(basepath, f))
        return song_paths
