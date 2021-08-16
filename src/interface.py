

from difflib import SequenceMatcher

from tracker import Tracker


def kinda_similar(str1, str2):
    # this func is terrible, use a different one
    perc = SequenceMatcher(None, str1, str2).ratio()
    if perc >= 0.4: return True
    else: return False


search_limit = 200 #200 uplimit with returns (300 in case of aimer but whatever)
tracker_path = opts.musitracker_path
musisorter_path = opts.musisorter_path
musipath = opts.musi_path
plist_name = opts.musitracker_plist_name
#test_musi_data = {"artist": ["b_sBD-j2IpE", "ICCmbFT7rMQ", "0HVbR8eP3k4", "WwyDpKXG83A", "_IkopJwRDKU", "XMaI3U4ducQ", "KiO4kdv1FfM",]}

# def get_playlist_key_from_album(album_key):
#     return ytmusic.get_album(album_key)["playlistId"]

# def get_plist_key(name):
#     plists = ytmusic.get_library_playlists()
#     plist_key = ""
#     for plist in plists:
#         if plist["title"] == plist_name:
#             plist_key = plist["playlistId"]
#     return plist_key

def get_musidata(path):
    musidata = {}
    for directory, _, files in os.walk(path):
        if files == []: continue
        artist_name = os.path.basename(directory)
        songs = [file[0:-len(".m4a")] for file in files]
        musidata[artist_name] = songs
    return musidata

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

def update_data_from_musisorter():
    tracker_now = Tracker()
    # take artist names from folder names, and auto add alts!!
    tracker_now.add_artists_from_musidata(get_musidata(musipath))
    #tracker_now.add_artists_from_songs(test_musi_data)
    try:
        tracker = Tracker()
        tracker.load(tracker_path)
        for artist in tracker_now.artists:
            if not all(key in tracker.all_keys for key in artist.keys):
                tracker.add_artist(artist)
        tracker.got_artist_from_these_songs.update(tracker_now.got_artist_from_these_songs)
        tracker.save(tracker_path)
    except:
        tracker_now.save(tracker_path)

def add_artist_from_musisorter():
    tracker_now = Tracker()
    musidata = get_musidata(musipath)
    name = input("name plz: ")
    musinames = [key for key, _ in musidata.items() if kinda_similar(name, key)]
    for i, name in enumerate(musinames): print(i, name)
    index = int(input("index plz: "))
    tracker_now.add_artists_from_musidata({musinames[index]: musidata[musinames[index]]})
    #tracker_now.add_artists_from_songs(test_musi_data)
    try:
        tracker = Tracker()
        tracker.load(tracker_path)
        for artist in tracker_now.artists:
            if not all(key in tracker.all_keys for key in artist.keys):
                tracker.add_artist(artist)
            else: print("artist is already be in database")
        tracker.got_artist_from_these_songs.update(tracker_now.got_artist_from_these_songs)
        tracker.save(tracker_path)
    except:
        tracker_now.save(tracker_path)

def check_updates(songs: bool):
    tracker = Tracker()
    tracker.load(tracker_path)
    new_albums = {}
    new_songs = {}
    for artist in tracker.artists:
        now_albums = artist.get_albums()
        new_albums.update(artist.get_new_albums(now_albums))
        if songs: new_songs.update(artist.get_new_songs(now_albums))
    tracker.save(tracker_path)
    
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
    tracker.load(tracker_path)
    tracker.add_artist_user_input()
    tracker.save(tracker_path)

def add_alts_to_artist():
    tracker = Tracker()
    tracker.load(tracker_path)
    
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
    tracker.save(tracker_path)


def testing_playlist_stuff():
    #plist_name = "musitracker"
    #plist_name = "musimusi"
    #playlist = ytmusic.create_playlist(plist_name, "", privacy_status="UNLISTED")
    #print(playlist)
    #key = plist_key
    #ytmusic.delete_playlist(key)
    #ytmusic.add_playlist_items(key, ["b_sBD-j2IpE", "ICCmbFT7rMQ"], duplicates=False)
    #plist = ytmusic.get_playlist(key, limit=2000)
    # plist- tracks, title, trackCount
    #songs = [{"videoId": track["videoId"], "setVideoId": track["setVideoId"]} for track in plist["tracks"]] #setvideoid required for editing songs or something
    #ytmusic.remove_playlist_items(key, songs)
    #print(songs)
    #ytmusic.edit_playlist(key, title=plist_name, addPlaylistId=ytmusic.get_album("MPREb_lZxmeDzbB0M")["playlistId"]) # append playlist
    
    #get playlist key
    """
    plists = ytmusic.get_library_playlists()
    plist_key = ""
    for plist in plists:
        if plist["title"] == plist_name:
            plist_key = plist["playlistId"]
    print(plist_key)
    """

def testing2():
    song = ytmusic.get_song("b_sBD-j2IpE") #"1MkrNVic7pw")
    pprint(song)

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
    testing2()
