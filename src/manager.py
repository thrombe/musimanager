# download, sort and do managing stuff with music files

import os
import copy

import opts
from newpipe_db_handler import NewpipeDBHandler
from song import Song, SongInfo
from tracker import Tracker
from artist import Artist

class Manager:
    def __init__(self, tracker=None):
        self.musi_path = opts.musi_path
        self.np_playlists = opts.newpipe_playlists
        self.musisorter_path = opts.musisorter_path
        self.musicache_path = opts.musicache_path

        if tracker is None:
            self.tracker = Tracker()
        else:
            self.tracker = tracker

    def new(self):
        self.tracker.new()

    def load(self):
        self.tracker.load()
    
    def save(self):
        self.tracker.save()

    def download_new_from_newpipe_db(self):
        # self.tracker.gen_extra_data() # to make sure data is updated

        np_db = NewpipeDBHandler()
        playlists = np_db.extract_from_zip()
        for songs_data in playlists.values():
            for song_data in songs_data:
                song = Song(song_data[0], song_data[2], song_data[1])
                if song.key in self.tracker.all_song_keys: continue
                path = song.find_path()
                if path is None: song.download()
                song.sort_using_tracker(self.tracker) # sets the correct artist name and adds self to tracker
                print("")

    # check if any song removed and notify user + handle that in tracker +
    # check if sorted correctly(eg if i change some stuff in artist keywords and stuff)
    def check_songs(self): 
        musidata = {}
        for directory, _, files in os.walk(opts.musi_path):
            if files == []: continue
            artist_name = os.path.basename(directory)
            songs = [Song(None, file[0:-len(".m4a")], artist_name) for file in files]
            musidata[artist_name] = songs
        
        artists_copy = self.tracker.artists.copy()
        for artist in artists_copy:
            # yeet empty artists
            if not artist.songs and not artist.ignore_no_songs:
                self.tracker.artists.remove(artist)
                continue
            
            songs_copy = artist.songs.copy()
            for song in songs_copy:
                found = False
                for _, songs_t in musidata.items():
                    songs_t_copy = songs_t.copy()
                    for song_t in songs_t_copy:
                        if song.key != song_t.key: continue
                        found = True
                        song_t.title = song.title # new songs wont have a title
                        
                        # more suitable artist stuff
                        besto_artisto = song.get_suitable_artist_using_tracker(self.tracker)
                        # if not besto_artisto: print(f"NO ARTIST FOUND -- {song}, {song_t}")
                        
                        # either the actual song isnt in the best directory, or this is a new best artist
                        if song.artist_name != besto_artisto.name:
                            print(f"AAAAAAAAAAAA {song} ----- {besto_artisto}")##########
                            artist.remove_song(song)
                            song.artist_name = besto_artisto.name
                            song.tag()
                            song.sort()
                            besto_artisto.add_song(song)
                        elif song_t.artist_name != besto_artisto.name:
                            song.tag()
                            song.sort()
                        
                        # next song in tracker
                        break
                    if found: break
                if found: continue
                # song removed from directory but in tracker
                print(f"song not found in directory - {song}")
                print("removing the song from db")
                artist.remove_song(song)
                
        # only newly added songs left without a title
        for name, songs in musidata.items():
            for song in songs:
                if song.title: continue
                found = False
                song.get_info()
                song.tag()
                song.title = song.info.titles[0]
                for artist in self.tracker.artists:
                    if song.artist_name == artist.name:
                        artist.add_song(song)
                        found = True
                if found: continue

                # artist not found
                artist = Artist(song.artist_name, song.info.channel_id)
                artist.name_confirmation_status = True
                artist.add_song(song)
                self.tracker.add_artist(artist)
            
        # removing empty directories in the main dir
        for directory, subdirs, files in os.walk(opts.musi_path):
            if files == [] and subdirs == []:
                print(f"removing empty directory {directory}")
                if not opts.debug_no_edits_to_stored:
                    os.rmdir(directory)

    def update_unsorted_db(self):
        _, song_paths = get_directory(opts.musi_path)
        songs = []
        for path in song_paths:
            key = path.split(os.path.sep)[-1].split(".")[0]
            song = Song(None, key, None)
            song.get_info_from_tags()
            # song.title = song.info.titles[0]
            # song.artist_name = song.info.artist_names[0]
            songs.append(song)
        
        self.tracker.load()
        known_artist_names = [artist.name for artist in self.tracker.artists]
        for song in songs:
            if song.key in self.tracker.all_song_keys: continue
            song_clone = copy.copy(song)
            song_clone.get_info(force=True)
            if song.info.album != "": song_clone.info.album = song.info.album
            song_clone.title = song.title
            if song.artist_name is not None: song_clone.artist_name = song.artist_name
            song = song_clone
            self.tracker.all_song_keys.add(song.key)
            if song.artist_name in known_artist_names:
                for artist in self.tracker.artists:
                    if artist.name == song.artist_name:
                        artist.add_song(song)
                        break
            else:
                # print(song_clone.info.channel_id/)
                artist = Artist(song.artist_name, song.info.channel_id)
                artist.add_song(song)
                # print(artist)
                self.tracker.add_artist(artist)
                known_artist_names.append(song.artist_name)


def get_directory(dir: str, ext: list=['mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg']) -> tuple[list, list]:
    # https://stackoverflow.com/a/59803793
    subfolders, files = [], []

    for f in os.scandir(dir):
        if f.is_dir():
            subfolders.append(f.path)
        if f.is_file():
            if os.path.splitext(f.name)[1].lower().replace('.', "") in ext:  # NOSONAR
                files.append(f.path)

    for dir in list(subfolders):
        sf, f = get_directory(dir, ext)
        subfolders.extend(sf)
        files.extend(f)

    return subfolders, files