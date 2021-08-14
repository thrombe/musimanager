
import ytmusicapi

import opts
ytmusic = ytmusicapi.YTMusic(opts.ytmusic_headers_path)

class Artist:
    def __init__(self, name, key):
        self.name = name
        if type(key) == type(["key"]): self.keys = set(key)
        else: self.keys = set([key])
        self.check_stat = True
        self.use_get_artist = False
        self.name_confirmation_status = False
        self.known_albums = {} # id: name
        self.known_songs = {} # id: name # do i even need to check these? album trackcount?
    
    def __str__(self):
        return f"{self.keys} {self.name}"
    
    def __hash__(self):
        return hash(self.name+f"{list(self.keys).sort()}")
    
    def __eq__(self, other):
        #if not isinstance(other, type(self)): return False
        return list(self.keys).sort() == list(other.keys).sort() # sorting to eliminate position probs
    
    def get_songs(self, album_key):
        album = ytmusic.get_album(album_key)
        songs = {}
        for song in album["tracks"]:
            if "(Instrumental)" in song["title"]: continue
            if None == song["videoId"]:
                print("no ids")
                pprint(song)
                continue
            songs[song["videoId"]] = song["title"]
        return songs
    
    def get_albums_using_artist_id(self):
        now_albums = {}
        for key in self.keys:
            albums_data = ytmusic.get_artist(key)["albums"]["results"]
            for album in albums_data:
                now_albums[album["browseId"]] = album["title"]
        return now_albums
    
    def get_albums(self): # this fails with artists like lisa tho
        if self.use_get_artist: return self.get_albums_using_artist_id()
        albums = ytmusic.search(self.name, filter="albums", limit=search_limit, ignore_spelling=True)
        now_albums = {}
        for album in albums:
            for artist in album["artists"]:
                if artist["id"] in self.keys:
                    now_albums[album["browseId"]] = album["title"]
                    # same album can go in multiple artists if album has multiple artists
        return now_albums
    
    def get_new_albums(self, now_albums):
        #now_albums = self.get_albums()
        new_albums = {}
        for album_key, album_name in now_albums.items():
            if album_key not in self.known_albums:
                new_albums[album_key] = album_name
                self.known_albums[album_key] = album_name
        return new_albums
    
    def get_new_songs(self, now_albums):
        new_songs = {}
        for album_key, album_name in now_albums.items():
            now_album_songs = self.get_songs(album_key)
            for song_key, song_name in now_album_songs.items():
                if song_key not in self.known_songs:
                    new_songs[song_key] = song_name
                    self.known_songs[song_key] = song_name
        return new_songs
