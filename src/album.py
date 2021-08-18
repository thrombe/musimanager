
from song import Song
from opts import ytmusic
import opts

class Album:
    def __init__(self, name, key, artist_name, artist_key):
        self.name = name
        self.key = key
        self.playlist_id = None
        self.artist_name = artist_name
        self.artist_key = artist_key
    
    def __str__(self):
        return f"{self.name} {self.key} {self.artist_name} {self.artist_key}"
    
    def __hash__(self):
        return hash(self.__str__())
    
    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def get_playlist_id(self): # if we add album to a yt_playlist, we need this
        if self.playlist_id: return self.playlist_id
        self.playlist_id = ytmusic.get_album(self.key)["playlistId"]
        return self.playlist_id

    def get_artist_from_tracker(self, tracker):
        for artist in tracker.artists:
            if self.artist_key in artist.keys:
                return artist

    def get_songs(self):
        album = ytmusic.get_album(self.key)
        songs = []
        for song_data in album["tracks"]:
            if "(Instrumental)" in song_data["title"]: continue
            # if None == song["videoId"]:
            #     print("no ids")
            #     pprint(song)
            #     continue
            songs.append(Song(song_data["title"], song_data.get("videoId", ""), self.artist_name))#[] = 
        return songs
    