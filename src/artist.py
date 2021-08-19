
from album import Album
from opts import ytmusic
import opts

class Artist:
    def __init__(self, name, key):
        self.name = name
        if type(key) == type(["key"]): self.keys = set(key)
        elif type(key) == type("string"): self.keys = set([key])
        else: self.keys = None
        self.check_stat = True
        self.ignore_no_songs = False # wont be removed from db even if no songs in it (only tracking for new albums)
        self.use_artist_id_for_albums = False
        self.name_confirmation_status = False
        
        self.known_albums = set()
        self.songs = set() # downloaded songs
        self.keywords = set() # keywords for sort
    
    def __str__(self):
        return f"{self.keys} {self.name}"
    
    def __hash__(self):
        return hash(self.name+f"{list(self.keys).sort()}")
    
    def __eq__(self, other):
        #if not isinstance(other, type(self)): return False
        return list(self.keys).sort() == list(other.keys).sort() # sorting to eliminate position probs
        
    def add_song(self, song):
        self.songs.add(song)
        self.add_key(song.get_info().channel_id, song.info.artist_names)
    
    def remove_song(self, song):
        # remove song and also remove key from keys if no other songs contribute the same key
          # not removing keys cuz i already manually checked if keys belong to the artist
        self.songs.remove(song)
        key = song.info.channel_id
        # if not any(key == song.info.channel_id for song in self.songs):
        #     print(f"removing a key from artist - {self.name}, {song.info.channel_id} - {song.info.artist_names}")
        #     self.keys.remove(key)
        print(f"not removing a key of removed song from artist - {song.title}, {song.key}, {self.name}, {song.info.channel_id} - {song.info.artist_names}")

    # artist_names only for printing
    def add_key(self, key, artist_names):
        if key == None: return
        if self.keys == None: self.keys = set()
        print(f"adding key {key} to {self.name}, artist names - {artist_names}")
        self.keys.add(key)

    # new name means new artist local folder name
    def set_new_name(self, name):
        self.name = name
        self.keywords.add(name)
        for song in self.songs:
            song.artist_name = name
            song.sort()
        for album in known_albums:
            album.artist_name = name

    def confirm_name(self):
        print(self)
        name = input("enter name/y to confirm name: ")
        if name != "y": self.set_new_name(name)
        self.name_confirmation_status = True
        print("name confirmed")
        print(self)

    def get_albums_using_artist_id(self):
        now_albums = set()
        for key in self.keys:
            albums_data = ytmusic.get_artist(key)["albums"]["results"]
            for album_data in albums_data:
                album = Album(album_data["title"], album_data["browseId"], self.name, key)
                # album.playlist_id = album_data["playlistId"] # cant get playlist_id from here
                now_albums.add(album)
        return now_albums
    
    def get_albums(self, all_artist_keys=None):
        if self.use_artist_id_for_albums: return self.get_albums_using_artist_id()

        if all_artist_keys == None:
            search_limit = opts.musitracker_search_limit_first_time
        elif any(key not in all_artist_keys for key in self.keys):
            search_limit = opts.musitracker_search_limit_first_time
            for key in self.keys:
                if key not in all_artist_keys: all_artist_keys.add(key)
        else: search_limit = opts.musitracker_search_limit

        albums_data = ytmusic.search(self.name, filter="albums", limit=search_limit, ignore_spelling=True)
        now_albums = set()
        for album_data in albums_data:
            for artist_data in album_data["artists"]:
                if artist_data["id"] in self.keys:
                    album = Album(album_data["title"], album_data["browseId"], self.name, artist_data["id"])
                    now_albums.add(album)
                    # album.playlist_id = album_data["playlistId"] # cant get playlist_id from here
                    # same album can go in multiple artists if album has multiple artists
        return now_albums
    
    # return and add new albums to artist
    def get_new_albums(self, all_artist_keys=None):
        now_albums = self.get_albums(all_artist_keys)
        new_albums = set()
        for album in now_albums:
            if album not in self.known_albums:
                new_albums.add(album)
                self.known_albums.add(album)
        if not self.known_albums: self.known_albums.add(Album("no albums", "no albums", self.name, "no albums"))
        return new_albums
