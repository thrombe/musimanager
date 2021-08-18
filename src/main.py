
import opts
from manager import manager
from opts import ytmusic
from interface import Interface
from song import kinda_similar

def regular_newpipe_and_sort_stuff():
    mag = manager()
    mag.load()

    mag.download_new_from_newpipe_db()
    mag.check_songs()
    # try: mag.check_songs()
    # except Exception as e:
    #     print(e)

    mag.save()

def append_albums():
    interface = Interface()
    interface.load()

    skip_perm = input("skip asking for permissions while adding songs to playlist? y/n: ")
    if skip_perm == "y": skip_perm = True
    else: skip_perm = False
    interface.append_new_albums_to_plist(skip_perm=skip_perm)

    interface.save()

def append_albums_from_few_artist():
    interface = Interface()
    interface.load()

    name = input("name plz: ")
    artists = [artist for artist in interface.tracker.artists if kinda_similar(name, artist.name) and artist.check_stat]
    if name == "": artists = interface.tracker.artists
    for i, artist in enumerate(artists): print(i, artist.name)
    print()
    indices = input("artist indices plz: ").split(", ")
    indices = [int(index) for index in indices]
    artists = [artists[index] for index in indices]
    new_albums = []
    for artist in artists:
        for album in artist.get_new_albums(interface.tracker.all_artist_keys):
            new_albums.append(album)
    if new_albums:
        skip_perms = input("wanna skip the permission thing for each album? y/n: ")
        if skip_perms == "y": skip_perms = True
        else: skip_perms = False
        interface.append_albums_to_plist(new_albums, skip_perm=skip_perms)
    else: print("no new albums found")

    interface.save()

"""
def add_keywords_from_ild_musisorter():
    import json
    old_path = "/sdcard/BKUP/newpipe/musisorter.json"
    with open(old_path, "r") as f:
        old_json = json.load(f)
    with open(opts.musisorter_path, "r") as f:
        new_json = json.load(f)
    
    for key, val in new_json.items():
        for bhal in old_json.get(key, [key]):
            val["keywords"].append(bhal)
    
    with open(opts.musisorter_path, "w") as f:
        json.dump(new_json, f, indent=4)
"""
def testing2():
    from pprint import pprint
    # song = ytmusic.get_song("b_sBD-j2IpE") #"1MkrNVic7pw")
    # data = ytmusic.get_artist("UCM3FfEkGhmE07vydCY4LUMQ")#["albums"]["results"]
    data = ytmusic.get_album("MPREb_67b9AFJrTqd")["playlistId"]
    pprint(data)

if __name__ == "__main__":
    # regular_newpipe_and_sort_stuff()
    # append_albums()
    append_albums_from_few_artist()
    # testing2()



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