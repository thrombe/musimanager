
import serde

import song
import opts

albumcache = None

class Album(serde.Model):
    name: serde.fields.Str()
    browse_id: serde.fields.Str()
    playlist_id: serde.fields.Optional(serde.fields.Str())
    songs: serde.fields.List(serde.fields.Nested(song.Song))
    artist_name: serde.fields.Str()
    artist_keys: serde.fields.List(serde.fields.Str())

    def load(ytm_album_search_data):
        # self.artist_daata = artists # [{"name": "..", "id": ".."}, {..}, ..]
        artist_name = [artist["name"] for artist in ytm_album_search_data["artists"] if artist.get("name", None) is not None]
        if len(artist_name) == 0: artist_name = ""
        else: artist_name = ", ".join(artist_name)

        return Album(
            name=ytm_album_search_data["title"],
            browse_id=ytm_album_search_data["browseId"],
            playlist_id=None,
            songs=[],
            artist_name=artist_name,
            artist_keys=[artist["id"] for artist in ytm_album_search_data["artists"] if artist.get("id", None) is not None]
        )
    
    def load_albums_from_artist_key(key):
        artist_data = opts.ytmusic.get_artist(key)
        maybe_albums_data = artist_data.get("albums", None)
        if maybe_albums_data is None: return []
        albums_data = maybe_albums_data.get("results", None)
        if maybe_albums_data.get("params", None) is not None:
            albums_data = opts.ytmusic.get_artist_albums(key, maybe_albums_data["params"])
        if albums_data is None: return []
        albums = []
        for album_data in albums_data:
            albums.append(Album(
                name=album_data["title"],
                browse_id=album_data["browseId"],
                playlist_id=None,
                songs=[],
                artist_name=artist_data["name"],
                artist_keys=[key]
            ))
        return albums

    def set_albumcache_refrence(tracker):
        global albumcache
        albumcache = tracker.albumcache

    def get_playlist_id(self): # this is needed to access songs from ytdl (to get a url for this album) or to add its songs to a youtube playlist
        if self.playlist_id: return self.playlist_id
        album_data = self.get_album_data_ytmusic()
        self.playlist_id = album_data.get("playlistId", None)
        if self.playlist_id is None: self.playlist_id = album_data["audioPlaylistId"]
        return self.playlist_id

    def get_album_data_ytmusic(self):
        album_data = None
        if albumcache is not None:
            album_data = albumcache.get(self.browse_id, None)
        if album_data is None:
            album_data = opts.ytmusic.get_album(self.browse_id)
            if albumcache is not None:
                albumcache[self.browse_id] = album_data
        return album_data

    def get_album_data_ytdl(self):
        album_data = None
        if albumcache is not None:
            album_data = albumcache.get(self.get_playlist_id(), None)
        if album_data is None:
            album_data = song.ytdl.ytd.extract_info(self.get_playlist_id(), download=False)
            if albumcache is not None:
                albumcache[self.playlist_id] = album_data
        return album_data

    def get_songs(self):
        self.songs = self.get_songs_ytdl()
        # self.songs = self.get_songs_ytmusic()
        return self.songs

    def get_songs_ytdl(self):
        songs = []
        album = self.get_album_data_ytdl()
        for song_data in album["entries"]:
            if song_data["id"] is None: continue # songs without video id are no longer available
            songs.append(song.Song.new(song_data["title"], song_data["id"], None))
        return songs

    def get_songs_ytmusic(self):
        songs = []
        album = self.get_album_data_ytmusic()
        for song_data in album["tracks"]:
            if song_data["videoId"] is None: continue # songs without video id are no longer available
            songs.append(song.Song.new(song_data["title"], song_data["videoId"], None))
        return songs
    