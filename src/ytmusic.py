

from song import Song
from album import Album
import opts
from opts import ytmusic

class yt_plist:
    def __init__(self):
        self.name = opts.musitracker_plist_name
        self.playlist_id = None

    def get_plist_id(self, force=False):
        if self.playlist_id and not force: return self.playlist_id

        plists = ytmusic.get_library_playlists()
        for plist in plists:
            if plist["title"] == self.name:
                self.playlist_id = plist["playlistId"]
                return self.playlist_id
        return self.create_playlist()

    def create(self):
        self.playlist_id = ytmusic.create_playlist(plist_name, "", privacy_status="UNLISTED")
        return self.playlist_id

    def delete(self):
        ytmusic.delete_playlist(self.playlist_id)

    def add_songs(self, keys):
        if type(keys) == type(["key"]): pass
        elif type(keys) == type("key"): keys = [keys]
        ytmusic.add_playlist_items(self.playlist_id, keys, duplicates=False)

    def get_songs(self):
        plist = ytmusic.get_playlist(key, limit=2000)
        # plist- tracks, title, trackCount
        songs = [Song(track["title"], track["videoId"], None) for track in plist["tracks"]] #setvideoid required for editing songs or something
        return songs

    def append_album(self, album):
        ytmusic.edit_playlist(self.playlist_id, addPlaylistId=album.get_playlist_id())

    def clear_items_with_permission(self, skip_perm=False):
        if skip_perm or input("wanna clear old items from ytplist? y/n: ") == "n": return
        plist = ytmusic.get_playlist(self.playlist_id, limit=2000)
        songs = [{"videoId": track["videoId"], "setVideoId": track["setVideoId"]} for track in plist["tracks"]] #setvideoid required for editing songs or something
        if songs: ytmusic.remove_playlist_items(self.playlist_id, songs)



def search_for_artists_on_ytmusic_albums(name):
    albums = ytmusic.search(name, filter="albums", limit=opts.musitracker_search_limit, ignore_spelling=False)
    artists = set()
    for album in albums:
        for artist in album["artists"]:
            artist = Artist(artist["name"], artist["id"])
            artists.add(artist)
    return artists
