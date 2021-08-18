
import opts
from tracker import Tracker
from song import kinda_similar, Song
from album import Album
from ytmusic import yt_plist
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
        self.plist.clear_items_with_permission(skip_perm=False)#skip_perm)
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


""" useful but not needed rn
!!def add_artist_from_input():
    tracker = Tracker()
    tracker.load(opts.musitracker_path)

    name = input("name plz(this will be used as the artist name in db): ")
    artists = list(get_artists(name))
    # yeet the albums that are definitely not from the required artist
    artists = [artist for artist in artists if kinda_similar(name, artist.name)]
    for i, artist in enumerate(artists): print(i, artist)
    print()
    indices = input("artist indices plz: ").split(", ")
    indices = [int(index) for index in indices]
    artist = artists[indices.pop(0)]
    print(artist.get_albums_using_artist_id())
    print()
    corr = input("this correct? y/n: ")
    if not corr:
        add_artist_user_input()
        return
    artist.name = name
    artist.name_confirmation_status = True
    for index in indices:
        try: print(artists[index].get_albums_using_artist_id())
        except Exception as e:
            print(f"index {index} failed", "\n", e)
            continue
        print()
        corr = input("this correct? y/n: ")
        if not corr:
            artist.keys.add(artists[index].keys)
    tracker.add_artist(artist)
    
    tracker.save(opts.musitracker_path)
"""
""" useful but not needed rn
!!def add_alts_to_artist():
    tracker = Tracker()
    tracker.load(opts.musitracker_path)
    
    name = input("artist name: ")
    # look for artist with similar name
    artists = [artist for artist in tracker.artists if kinda_similar(name, artist.name)]
    for i, artist in enumerate(artists): print(i, artist.name)
    index = int(input("\nwhat index?: "))
    artist = artists[index]
    print(artist)
    print()
    
    artists = list(get_artists(artist.name))
    artists = [artist for artist in artists if kinda_similar(name, artist.name)]
    for i, artist in enumerate(artists): print(i, artist)
    print()
    indices = input("artist indices plz: ").split(", ")
    indices = [int(index) for index in indices]
    for index in indices:
        # show artist to user and confirm to add
        try: print([name for key, name in artists[index].get_albums_using_artist_id().items()])
        except Exception as e:
            print(f"index {index} failed")
            print(e)
            continue
        print()
        rep = input("this correct? y/n: ")
        if rep == "n": continue
        
        artist.keys.add(artists[index].keys)
        tracker.all_artist_keys.add(artists[index].keys)
    tracker.save(opts.musitracker_path)
"""
