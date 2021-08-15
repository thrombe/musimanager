
import ytmusicapi
import json
from difflib import SequenceMatcher
import os

import opts
from artist import Artist
from ytmusic import ytmusic

search_limit = 200 #200 uplimit with returns (300 in case of aimer but whatever)
tracker_path = opts.musitracker_path
musisorter_path = opts.musisorter_path
musipath = opts.musi_path
plist_name = opts.musitracker_plist_name
#test_musi_data = {"artist": ["b_sBD-j2IpE", "ICCmbFT7rMQ", "0HVbR8eP3k4", "WwyDpKXG83A", "_IkopJwRDKU", "XMaI3U4ducQ", "KiO4kdv1FfM",]}

def to_json(obj):
    if type(obj) == type(set()): return list(obj)
    return obj.__dict__

def kinda_similar(str1, str2):
    # this func is terrible, use a different one
    perc = SequenceMatcher(None, str1, str2).ratio()
    if perc >= 0.4: return True
    else: return False

class Tracker:
    def __init__(self):
        self.artists = set()
        self.all_keys = set() # gen on load
        self.got_artist_from_these_songs = set() # gen on load(if song in artists.songs, then we already have the artist) # so that only new songs are tested for artist
    
    def add_artist(self, artist):
        self.artists.add(artist)
        for key in artist.keys:
            self.all_keys.add(key)
    
    def add_artists_from_musidata(self, musidata):
        for name, song_keys in musidata.items():
            artist = Artist(name, "temp")
            for song_key in song_keys:
                if song_key in self.got_artist_from_these_songs: continue
                artist_details = ytmusic.get_song(song_key)
                try: artist_details = artist_details["videoDetails"]
                except Exception as e:
                    print(artist_details, "\n", e)
                    continue
                artist.keys.add(artist_details["channelId"])
                self.got_artist_from_these_songs.add(song_key)
            artist.keys.remove("temp")
            artist.name_confirmation_status = True
            if artist not in self.artists:
                self.add_artist(artist)
            else: print(f"artist {artist} already in")
    
    def add_artists_from_song_keys(self, keys):
        for key in keys:
            if key in self.got_artist_from_these_songs: continue
            artist_details = ytmusic.get_song(key)
            try: artist_details = artist_details["videoDetails"]
            except:
                print(artist_details)
                continue
            artist = Artist(artist_details["author"], artist_details["channelId"])
            self.got_artist_from_these_songs.add(key)
            if artist not in self.artists:
                self.add_artist(artist) # how do i remove alt ids and put them in same artist?
   
    def save(self, path):
        if opts.debug_no_edits_to_db: return

        self.save_artist_keywords()
        dikt = self.__dict__
        dikt.remove("all_keys")
        dikt.remove("got_artist_from_these_songs")
        with open(path, "w") as f:
            json.dump(dikt, f, indent=4, default=to_json)
    
    def load(self, path):
        with open(path, "r") as f:
            celf = json.load(f)
        self.artists = set()
        for json_artist in celf["artists"]:
            artist = Artist(json_artist["name"], json_artist["keys"])
            artist.check_stat = json_artist["check_stat"]
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
            # artist.keywords # ignore the keywords from here
            self.artists.add(artist)

        self.load_artist_keywords()
        self.gen_extra_data()
        # self.gen_all_keys()
        # self.gen_got_artist_from_these_songs()
    
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

