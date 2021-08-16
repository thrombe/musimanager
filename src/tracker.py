
import ytmusicapi
import json
import os

import opts
from artist import Artist
from song import Song, get_song
from ytmusic import ytmusic
from ui import kinda_similar

def to_json(obj):
    if type(obj) == type(set()): return list(obj)
    return obj.__dict__

class Tracker:
    def __init__(self):
        self.artists = set()
        self.all_keys = set() # gen on load
        self.got_artist_from_these_songs = set() # gen on load(if song in artists.songs, then we already have the artist) # so that only new songs are tested for artist
    
    def add_artist(self, artist):
        self.artists.add(artist)
        for key in artist.keys:
            self.all_keys.add(key)
       
    def save(self):
        if opts.debug_no_edits_to_db: return

        self.save_sorter()
        dikt = self.__dict__
        dikt.remove("all_keys")
        dikt.remove("got_artist_from_these_songs")
        with open(opts.musitracker_path, "w") as f:
            json.dump(dikt, f, indent=4, default=to_json)
    
    def save_sorter(self):
        if opts.debug_no_edits_to_db: return
        
        dikt = {}
        for artist in self.artists:
            dikt[artist.name] = {"keywords": list(artist.keywords), "keys": list(artist.keys)}
        with open(opts.musisorter_path, "w") as f:
            json.dump(dikt, f, indent=4)
    
    def load(self):
        with open(opts.musitracker_path, "r") as f:
            celf = json.load(f)
        self.artists = set()
        for json_artist in celf["artists"]:
            artist = Artist(json_artist["name"], json_artist["keys"])
            artist.check_stat = json_artist["check_stat"]
            artist.ignore_no_songs = json_artist["ignore_no_songs"]
            artist.use_get_artist = json_artist["use_get_artist"]
            artist.name_confirmation_status = json_artist["name_confirmation_status"]

            for json_album in json_artist["known_albums"]:
                album = Album("", "", "")
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
        # self.gen_all_keys()
        # self.gen_got_artist_from_these_songs()
    
    def load_sorter(self):
        with open(opts.musisorter, "r") as f:
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
                        break
            artist.keys = data["keys"]
            artist.keywords = data["keywords"]
    
    def gen_extra_data(self):
        for artist in self.artists:
            for key in artist.keys:
                self.all_keys.add(key)
            for song in artist.songs:
                self.got_artist_from_these_songs.add(song.key)
    
    # NOT NEEDED CUZ MANAGER ALREADY DOES THIS
    # def add_artists_from_musidata(self, musidata):
    #     for name, song_keys in musidata.items():
    #         artist = Artist(name, "temp")
    #         for song_key in song_keys:
    #             if song_key in self.got_artist_from_these_songs: continue
    #             song = get_song(song_key)
    #             artist.keys.add(song.info.channel_id)
    #             self.got_artist_from_these_songs.add(song_key)
    #         artist.keys.remove("temp")
    #         artist.name_confirmation_status = True
    #         if artist not in self.artists:
    #             self.add_artist(artist)
    #         else: print(f"artist {artist} already in")
    
    # assuming that song is downloaded???
    # def add_artists_from_song_keys(self, keys):
    #     for key in keys:
    #         if key in self.got_artist_from_these_songs: continue
    #         song = get_song(key)
    #         song.sort_using_tracker(self)

    def add_artist_user_input(self):
        name = input("name plz(this will be used as the artist name in db): ")
        artists = list(get_artists(name))
        # yeet the albums that are definitely not from the required artist
        artists = [artist for artist in artists if kinda_similar(name, artist.name)]
        for i, artist in enumerate(artists): print(i, artist)
        print()
        indices = input("artist indices plz: ").split(", ")
        indices = [int(index) for index in indices]
        artist = artists[indices.pop(0)]
        print(artist.get_albums_using_artist_id())
        print()
        corr = input("this correct? y/n: ")
        if not corr:
            add_artist_user_input()
            return
        artist.name = name
        artist.name_confirmation_status = True
        for index in indices:
            try: print(artists[index].get_albums_using_artist_id())
            except Exception as e:
                print(f"index {index} failed", "\n", e)
                continue
            print()
            corr = input("this correct? y/n: ")
            if not corr:
                artist.keys.add(artists[index].keys)
        self.add_artist(artist)

