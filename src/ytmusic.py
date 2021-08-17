

import ytmusicapi

import opts
ytmusic = ytmusicapi.YTMusic(opts.ytmusic_headers_path)


class yt_plist:
    def __init__(self, name):
        self.name = name
        self.playlist_id = None

    def get_plist_id(self, force=False):
        if self.playlist_id and not force: return self.playlist_id

        plists = ytmusic.get_library_playlists()
        for plist in plists:
            if plist["title"] == self.name:
                self.playlist_id = plist["playlistId"]
                return self.playlist_id
        return self.create_playlist()

    def create_playlist(self):
        self.playlist_id = ytmusic.create_playlist(plist_name, "", privacy_status="UNLISTED")
        return self.playlist_id

    #ytmusic.delete_playlist(key)
    #ytmusic.add_playlist_items(key, ["b_sBD-j2IpE", "ICCmbFT7rMQ"], duplicates=False)

    #plist = ytmusic.get_playlist(key, limit=2000)
    # plist- tracks, title, trackCount
    #songs = [{"videoId": track["videoId"], "setVideoId": track["setVideoId"]} for track in plist["tracks"]] #setvideoid required for editing songs or something
    #ytmusic.remove_playlist_items(key, songs)

    #ytmusic.edit_playlist(key, title=plist_name, addPlaylistId=ytmusic.get_album("MPREb_lZxmeDzbB0M")["playlistId"]) # append playlist


def ytplist_add_albums(albums):
    plist_key = get_plist_key(plist_name)
    for album_key in albums:
        playlist_key = get_playlist_key_from_album(album_key)
        ytmusic.edit_playlist(plist_key, title=plist_name, addPlaylistId=playlist_key)

def ytplist_clear_old_with_permission():
    if input("wanna clear old items from ytplist? y/n: ") == "n": return
    plist_key = get_plist_key(plist_name)
    plist = ytmusic.get_playlist(plist_key, limit=2000)
    songs = [{"videoId": track["videoId"], "setVideoId": track["setVideoId"]} for track in plist["tracks"]] #setvideoid required for editing songs or something
    ytmusic.remove_playlist_items(plist_key, songs)

def get_artists(name):
    albums = ytmusic.search(name, filter="albums", limit=opts.musitracker_search_limit, ignore_spelling=False)
    artists = set()
    for album in albums:
        for artist in album["artists"]:
            artist = Artist(artist["name"], artist["id"])
            # artist.known_albums[album["browseId"]] = album["title"]
            artists.add(artist)
    return artists
