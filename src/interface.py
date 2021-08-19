
import opts
from tracker import Tracker
from song import kinda_similar, Song
from album import Album
from ytmusic import yt_plist, search_for_artists_on_ytmusic_albums
from artist import Artist
from tracker import Tracker


class Interface:
    def __init__(self):
        self.tracker = Tracker()
        self.plist = yt_plist()

    def load(self):
        self.plist.get_plist_id()
        self.tracker.load()

    def save(self):
        self.tracker.save()

    def append_new_albums_to_plist(self, skip_perm=False):
        new_albums = self.tracker.get_new_albums()
        self.append_albums_to_plist(albums, skip_perm=skip_perm)

    def append_albums_to_plist(self, albums, skip_perm=False):
        self.plist.clear_items_with_permission(skip_perm=False)
        print()
        for album in albums:
            print(album)
            songs = "-songs--->"
            for song in album.get_songs():
                songs += f"{song}, "
            print(songs)
            print()
            if not skip_perm: perm = input("want this album in playlist? y/n: ")
            else: perm = "y"
            if perm == "y":
                self.plist.append_album(album)

    def append_albums_manual(self):
        name = input("name plz: ")
        artists = [artist for artist in self.tracker.artists if kinda_similar(name, artist.name) and artist.check_stat]
        if name == "": artists = self.tracker.artists
        for i, artist in enumerate(artists): print(i, artist.name)
        print()
        indices = input("artist indices plz: ").split(", ")
        indices = [int(index) for index in indices]
        artists = [artists[index] for index in indices]
        new_albums = []
        for artist in artists:
            for album in artist.get_new_albums(self.tracker.all_artist_keys):
                new_albums.append(album)
        if new_albums:
            skip_perms = input("wanna skip the permission thing for each album? y/n: ")
            if skip_perms == "y": skip_perms = True
            else: skip_perms = False
            self.append_albums_to_plist(new_albums, skip_perm=skip_perms)
        else: print("no new albums found")

    def add_songs_to_plist_using_song_key(self):
        key = input("song key plz: ")
        song = Song(None, key, None)
        song.get_info()
        # artist_key = song.info.channel_id
        for i, name in enumerate(song.info.artist_names): print(i, name)
        index_or_name = input("choose name or enter your own index/name: ")
        try:
            index = int(index_or_name)
            name = song.info.artist_names[index]
        except:
            name = index_or_name
        artist = Artist(name, song.info.channel_id)
        albums = artist.get_albums()
        self.plist.clear_items_with_permission()
        self.append_albums_to_plist(albums, skip_perm=True)

    def append_all_albums_to_plist_for_an_artist(self):
        name = input("name plz: ")
        artists = [artist for artist in self.tracker.artists if kinda_similar(name, artist.name) and artist.check_stat]
        if name == "": artists = self.tracker.artists
        for i, artist in enumerate(artists): print(i, artist.name)
        print()
        index = int(input("artist index plz: "))
        artist = artists[index]
        albums = artist.get_albums()
        # self.plist.clear_items_with_permission()
        self.append_albums_to_plist(albums, skip_perm=True)

    def get_artist_using_search(self):
        name = input("name plz(this will be used as the artist name): ")
        artists = list(search_for_artists_on_ytmusic_albums(name))
        # yeet the albums that are definitely not from the required artist
        artists = [artist for artist in artists if kinda_similar(name, artist.name)]
        for i, artist in enumerate(artists): print(i, artist)
        print()
        indices = input("artist indices plz: ").split(", ")
        indices = [int(index) for index in indices]
        artist = artists[indices.pop(0)]
        print([album.name for album in artist.get_albums_using_artist_id()])
        print()
        corr = input("this correct? y/n: ")
        if corr != "y":
            self.add_artist_using_search()
            return
        artist.name = name
        artist.name_confirmation_status = True
        artist.ignore_no_songs = True
        for index in indices:
            try: print([album.name for album in artists[index].get_albums_using_artist_id()])
            except Exception as e:
                print(f"index {index} failed", "\n", e)
                continue
            print()
            corr = input("this correct? y/n: ")
            if corr == "y":
                artist.keys.add(artists[index].keys)
        return artist
        
    def add_artist_using_search(self):
        artist = self.get_artist_using_search()
        self.tracker.add_artist(artist)

    def add_alt_keys_to_artist(self):
        name = input("artist name: ")
        # look for artist with similar name
        artists = [artist for artist in tracker.artists if kinda_similar(name, artist.name)]
        for i, artist in enumerate(artists): print(i, artist.name)
        index = int(input("\nwhat index?: "))
        artist = artists[index]
        print(artist)
        print()
        
        artists = list(search_for_artists_on_ytmusic_albums(artist.name))
        artists = [artist for artist in artists if kinda_similar(name, artist.name)]
        for i, artist in enumerate(artists): print(i, artist)
        print()
        indices = input("artist indices plz: ").split(", ")
        indices = [int(index) for index in indices]
        for index in indices:
            # show artist to user and confirm to add
            try: print([album.name for album in artists[index].get_albums_using_artist_id()])
            except Exception as e:
                print(f"index {index} failed")
                print(e)
                continue
            print()
            rep = input("this correct? y/n: ")
            if rep == "n": continue
            
            for key in artists[index].keys:
                artist.keys.add(key)
