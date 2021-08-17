

from tracker import Tracker
from song import kinda_similar

def get_musidata(path):
    musidata = {}
    for directory, _, files in os.walk(path):
        if files == []: continue
        artist_name = os.path.basename(directory)
        songs = [file[0:-len(".m4a")] for file in files]
        musidata[artist_name] = songs
    return musidata

def update_data_from_musisorter():
    tracker_now = Tracker()
    # take artist names from folder names, and auto add alts!!
    tracker_now.add_artists_from_musidata(get_musidata(opts.musi_path))
    #tracker_now.add_artists_from_songs(test_musi_data)
    try:
        tracker = Tracker()
        tracker.load(opts.musitracker_path)
        for artist in tracker_now.artists:
            if not all(key in tracker.all_keys for key in artist.keys):
                tracker.add_artist(artist)
        tracker.got_artist_from_these_songs.update(tracker_now.got_artist_from_these_songs)
        tracker.save(opts.musitracker_path)
    except:
        tracker_now.save(opts.musitracker_path)

def add_artist_from_musisorter():
    tracker_now = Tracker()
    musidata = get_musidata(opts.musi_path)
    name = input("name plz: ")
    musinames = [key for key, _ in musidata.items() if kinda_similar(name, key)]
    for i, name in enumerate(musinames): print(i, name)
    index = int(input("index plz: "))
    tracker_now.add_artists_from_musidata({musinames[index]: musidata[musinames[index]]})
    #tracker_now.add_artists_from_songs(test_musi_data)
    try:
        tracker = Tracker()
        tracker.load(opts.musitracker_path)
        for artist in tracker_now.artists:
            if not all(key in tracker.all_keys for key in artist.keys):
                tracker.add_artist(artist)
            else: print("artist is already be in database")
        tracker.got_artist_from_these_songs.update(tracker_now.got_artist_from_these_songs)
        tracker.save(opts.musitracker_path)
    except:
        tracker_now.save(opts.musitracker_path)

def check_updates(songs: bool):
    tracker = Tracker()
    tracker.load(opts.musitracker_path)
    new_albums = {}
    new_songs = {}
    for artist in tracker.artists:
        now_albums = artist.get_albums()
        new_albums.update(artist.get_new_albums(now_albums))
        if songs: new_songs.update(artist.get_new_songs(now_albums))
    tracker.save(opts.musitracker_path)
    
    if new_albums == new_songs: return #both empty
    
    # add to playlist on yt, or send link to discord
    create_playlist_if_not_there()
    ytplist_clear_old_with_permission() # ask user if ckearing is ok
    ytplist_add_albums(new_albums)
    
    pprint(new_albums)
    print()
    pprint(new_songs)
    print()

def add_artist_from_input():
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

def add_alts_to_artist():
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
        tracker.all_keys.add(artists[index].keys)
    tracker.save(opts.musitracker_path)

def testing2():
    song = ytmusic.get_song("b_sBD-j2IpE") #"1MkrNVic7pw")
    pprint(song)

#test_musi_data = {"artist": ["b_sBD-j2IpE", "ICCmbFT7rMQ", "0HVbR8eP3k4", "WwyDpKXG83A", "_IkopJwRDKU", "XMaI3U4ducQ", "KiO4kdv1FfM",]}

if __name__ == "__main__":
    #update_data_from_musisorter()
    #add_artist_from_musisorter() # to add a single artist from musisorter
    #check_updates(songs=False)
    #add_artist_from_input()
    #add_alts_to_artist()
    #ytplist_clear_old_with_permission()
    
    #filp_album_from_key() # the lisa thing
    # done ig? update_artist_names_from_musisorter() # so i dont have to do this manually
    #update_artist_names() # print all names, and ask what names to change. save the confirmed ones.
    #combine_artists()
    
    #testing_playlist_stuff()
    # testing2()
    pass
