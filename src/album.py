
from song import Song
from ytmusic import ytmusic

class Album:
    def __init__(self, name, key, artist_key):
        self.name = name
        self.key = key
        self.playlist_id = None
        self.artist_key = artist_key
    
    def __str__(self):
        return f"{self.name} {self.key} {self.artist_key}"
    
    def __hash__(self):
        return hash(self.__str__())
    
    def __eq__(self, other):
        return self.__str__() == other.__str__()

    # def get_songs(self):
    #     album = ytmusic.get_album(self.key)
    #     songs = {}
    #     for song in album["tracks"]:
    #         if "(Instrumental)" in song["title"]: continue
    #         if None == song["videoId"]:
    #             print("no ids")
    #             pprint(song)
    #             continue
    #         songs[song["videoId"]] = song["title"]
    #     return songs

    def get_playlist_id(self, id=None): # if we add album to a yt_playlist, we need this
        if id:
            self.playlist_id = id
            return self.playlist_id
        if self.playlist_id: return self.playlist_id
        self.playlist_id = ytmusic.get_album(album_key)["playlistId"]
        return self.playlist_id

    