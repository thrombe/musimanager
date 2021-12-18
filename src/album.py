
import song
import opts

albumcache = None

class Album:
    def __init__(self, name, browse_id, artists):
        self.name = name
        self.browse_id = browse_id
        self.playlist_id = None
        self.songs = []
        # self.artist_daata = artists # [{"name": "..", "id": ".."}, {..}, ..]
        self.artist_name = [artist["name"] for artist in artists if artist.get("name", None) is not None]
        if len(self.artist_name) == 0: self.artist_name = ""
        else: self.artist_name = self.artist_name.join(", ")

    def load(ytm_album_search_data):
        # artist_data = ytm_album_search_data["artists"]
        # if artist_data is None or len(artist_data) == 0:
        #     artist_data = {"name": None, "id": None}
        # else:
        #     artist_data = artist_data[0]
        return Album(ytm_album_search_data["title"], ytm_album_search_data["browseId"], ytm_album_search_data["artists"])

    def set_albumcache_refrence(tracker):
        global albumcache
        albumcache = tracker.albumcache

    def get_playlist_id(self): # this is needed to access songs from ytdl (to get a url for this album) or to add its songs to a youtube playlist
        if self.playlist_id: return self.playlist_id
        album_data = self.get_album_data()
        self.playlist_id = album_data.get("playlistId", None)
        if self.playlist_id is None: self.playlist_id = album_data["audioPlaylistId"]
        return self.playlist_id

    def get_album_data(self):
        album_data = None
        if albumcache is not None:
            album_data = albumcache.get(self.browse_id, None)
        if album_data is None:
            album_data = opts.ytmusic.get_album(self.browse_id)
            if albumcache is not None:
                albumcache[self.browse_id] = album_data
        return album_data

    def get_songs(self):
        album = self.get_album_data()
        songs = []
        for song_data in album["tracks"]:
            if song_data["videoId"] is None: continue # songs without video id are no longer available
            songs.append(song.Song(song_data["title"], song_data["videoId"], None))
        self.songs = songs
        return songs
    