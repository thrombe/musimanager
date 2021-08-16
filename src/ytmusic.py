

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


def get_artists(name):
    albums = ytmusic.search(name, filter="albums", limit=opts.musitracker_search_limit, ignore_spelling=False)
    artists = set()
    for album in albums:
        for artist in album["artists"]:
            artist = Artist(artist["name"], artist["id"])
            # artist.known_albums[album["browseId"]] = album["title"]
            artists.add(artist)
    return artists
