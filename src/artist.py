
from ytmusic import ytmusic
import opts

class Artist:
    def __init__(self, name, key):
        self.name = name
        if type(key) == type(["key"]): self.keys = set(key)
        else: self.keys = set([key])
        self.check_stat = True
        self.use_get_artist = False
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
        
    def get_albums_using_artist_id(self):
        now_albums = set()
        for key in self.keys:
            albums_data = ytmusic.get_artist(key)["albums"]["results"]
            for album_data in albums_data:
                album = Album(album_data["title"], album_data["browseId"], key)
                album.playlist_id = album_data["playlistId"]
                now_albums.add(album)
        return now_albums
    
    def get_albums(self): # this fails with artists like lisa tho
        if self.use_get_artist: return self.get_albums_using_artist_id()
        albums_data = ytmusic.search(self.name, filter="albums", limit=search_limit, ignore_spelling=True)
        now_albums = set()
        for album_data in albums_data:
            for artist_data in album_data["artists"]:
                if artist_data["id"] in self.keys:
                    album = Album(album_data["title"], album_data["browseId"], artist_data["id"])
                    album.playlist_id = album_data["playlistId"]
                    now_albums.add(album)
                    # same album can go in multiple artists if album has multiple artists
        return now_albums
    
    def get_new_albums(self, now_albums):
        new_albums = set()
        for album in now_albums:
            if album not in self.known_albums:
                new_albums.add(album)
                self.known_albums.add(album)
        return new_albums
    
    # OLD
    # def get_new_songs(self, now_albums):
    #     new_songs = {}
    #     for album_key, album_name in now_albums.items():
    #         now_album_songs = album.get_songs()
    #         for song_key, song_name in now_album_songs.items():
    #             if song_key not in self.known_songs:
    #                 new_songs[song_key] = song_name
    #                 self.known_songs[song_key] = song_name
    #     return new_songs
