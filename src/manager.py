# download, sort and do managing stuff with music files

import json
import os
import requests

import opts
from newpipe_db_handler import newpipe_db_handler
from song import Song
from tracker import Tracker

class manager:
    def __init__(self):
        self.musi_path = opts.musi_path
        self.np_playlists = opts.newpipe_playlists
        self.musisorter_path = opts.musisorter_path
        self.musicache_path = opts.musicache_path

        self.tracker = Tracker()
        self.tracker.load()

    def download_new_from_newpipe_db(self):
        np_db = newpipe_db_handler()
        playlists = np_db.extract_from_zip()
        for songs_data in playlists.values():
            for song_data in songs_data:
                song = Song(song_data[0], song_data[2], song_data[1])
                if song.check_if_in_tracker(self.tracker): continue
                song.download()
                song.sort_using_tracker(self.tracker) # sets the correct artist name and adds self to tracker
                song.tag()

    # check if any song removed and notify user + handle that in tracker +
    # check if sorted correctly(eg if i change some stuff in artist keywords and stuff)
    def check_songs(self): 
        musidata = {}
        for directory, _, files in os.walk(path):
            if files == []: continue
            artist_name = os.path.basename(directory)
            songs = [Song(None, file[0:-len(".m4a")], artist_name) for file in files]
            musidata[artist_name] = songs
        
        # check if all songs are sorted properly - ie if i change some artists name or something in json
        for songs in musidata.values():
            for song in songs:
                found = False
                for artist in self.tracker.artists:
                    for song_t in artist.songs:
                        if song.key == song_t.key:
                            found = True
                            song.title = song_t.title # notice that newly added songs (not in tracker) will not have a title
                            if song.artist_name != song_t.artist_name:
                                song_t.sort(current_path=song.path(after=True))
                                song.artist_name = song_t.artist_name
                            break
                    if found: break

        # check if a new songs in dir
        # check the dir name in artist keywords
        for songs in musidata.values():
            for song in songs:
                if song.title: continue
                current_path = song.path(after=True)
                # move it to parent folder as if it was newly downloaded
                print(f"song seems newly added, so moving it to parent dir for sorting - {song}")
                if not opts.debug_no_edits_to_stored:
                    os.rename(current_path, os.path.join(current_path, os.pardir, os.path.basename(current_path)))
                song.sort_using_tracker(tracker)

        # check if all items in tracker are in the dir
        for artist in self.tracker.artists:
            songs = artist.songs.copy()
            for song in songs:
                if not os.path.exists(song.path(after=True)):
                    print(f"song not found in directory - {song}")
                    print("removing the song from db")
                    artist.songs.remove(song)

        # removing empty directories in the main dir
        for directory, _, files in os.walk(path):
            if files == []:
                print(f"removing empty directory {os.path.basename(directory)}")
                if not opts.debug_no_edits_to_stored:
                    os.rmdir(directory)
