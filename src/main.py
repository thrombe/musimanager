
import argparse
import sys

import cui_handle
from manager import Manager
from ytmusic import search_albums_on_yt
from opts import ytmusic
from interface import Interface
from tracker import Tracker

class Launcher:
    def __init__(self):
        self.args = {}
        self.help_text = ""
        # set attributes with names related to method names of Launcher
        for func_name in [func for func in dir(self) if callable(getattr(self, func)) and not func.startswith("__")]:
            if func_name in ["launch"]: continue
            self.args[func_name] = False
    
        # get arguments
        parser  = argparse.ArgumentParser()
        for key in self.args:
            # parser.add_argument(f"--{key}".replace("_", "-"), action="store_true")
            self.help_text = ""
            exec(f"self.help_text = self.{key}(help_text=True)")
            parser.add_argument(f"--{key}".replace("_", "-"), action="store_true", help=self.help_text)
        self.args = parser.parse_args().__dict__
        
        if len(sys.argv) == 1: parser.print_help()
    
    def launch(self):
        for key, val in self.args.items():
            if val == True: exec(f"self.{key}()")
        #print(self.__dict__)
    
    # func names should only have lowercase and _ (at least)(maybe)
    # to call a func with args, --{func_name} but replace "_" with "-"
    
    def test(self, help_text=False):
        if help_text: return "help text yo"
        # from pprint import pprint
        # song = ytmusic.get_song("b_sBD-j2IpE") #"1MkrNVic7pw")
        # data = ytmusic.get_artist("UCM3FfEkGhmE07vydCY4LUMQ")#["albums"]["results"]
        # data = ytmusic.get_album("MPREb_67b9AFJrTqd")["playlistId"]
        # pprint(data)
        print("lol")
        pass
    
    def np_download_and_sort(self, help_text=False):
        if help_text: return "download and sort songs from newpipe db"
        manager = Manager()
        manager.load()

        manager.download_new_from_newpipe_db()
        manager.check_songs()
        # try: manager.check_songs()
        # except Exception as e:
        #     print(e)

        manager.save()

    def check_sort(self, help_text=False):
        if help_text: return "check if all songs are sorted properly and update the db"
        manager = Manager()
        manager.load()

        manager.check_songs()

        manager.save()

    def append_all_new_albums(self, help_text=False):
        if help_text: return "check and add all new available albums to yt playlist of all artists in db"
        interface = Interface()
        interface.load()

        skip_perm = input("skip asking for permissions while adding songs to playlist? y/n: ")
        if skip_perm == "y": skip_perm = True
        else: skip_perm = False
        interface.append_new_albums_to_plist(skip_perm=skip_perm)

        interface.save()

    def append_albums_manual(self, help_text=False):
        if help_text: return "append all new albums to yt playlist but from selected artists form db"
        interface = Interface()
        interface.load()

        interface.append_albums_manual()

        interface.save()

    def search_artist_and_append_albums(self, help_text=False):
        if help_text: return "search for artist, and add songs to yt playlist, no changes to db"
        interface = Interface()
        interface.load()
        artist = interface.get_artist_using_search()
        interface.append_albums_to_plist(artist.get_albums(), skip_perm=True)

    def search_albums_on_yt(self, help_text=False):
        if help_text: return "search albums on youtube music (and nothing else, just filter search)"
        name = input("name plz: ")
        search_albums_on_yt(name)

    # just to check out artist add all songs to plist but not to db
    def add_songs_to_plist_using_song_key(self, help_text=False):
        if help_text: return "enter song key, and all songs from the same channel wil appear in the yt playlist, no changes in db"
        interface = Interface()
        interface.load()

        interface.add_songs_to_plist_using_song_key()

        # interface.save()
    
    # this dosent get stored in the db
    def append_all_albums_to_plist_for_an_artist(self, help_text=False):
        if help_text: return "choose an artist from db and all the songs get added to the yt playlist but dosent affect db"
        interface = Interface()
        interface.load()

        interface.append_all_albums_to_plist_for_an_artist()

    # confirm the names of unconfirmed artist names
    def confirm_artist_names(self, help_text=False):
        if help_text: return "confirm the names of artists which are not confirmed"
        tracker = Tracker()
        tracker.load()

        tracker.confirm_artist_names()

        tracker.save()
    
    # search and choose artist + keys to add to db
    def add_artist_using_search(self, help_text=False):
        if help_text: return "search for artist on yt and add then to db for tracking"
        interface = Interface()
        interface.load()

        interface.add_artist_using_search()

        interface.save()

    def add_alt_keys_to_artist(self, help_text=False):
        if help_text: return "choose an artist form db and add more keys to it for tracking"
        interface = Interface()
        interface.load()

        interface.add_alt_keys_to_artist()

        interface.save()
    
    def launch_cui(self, help_text=False):
        if help_text: return "launches command line ui based on py_cui"
        cui = cui_handle.CUI_handle()
        cui.start()

    def update_unsorted_db(self, help_text=False):
        if help_text: return "update stored song db in unsorted mode"
        manager = Manager()
        manager.update_unsorted_db()
        manager.save()

    """
    # search songs and ask user to choose keys to add to artist + artist name
    def add_artist_using_song_key(self, help_text=False):
        if help_text: return "dosent do anything rn"
        pass
    
    def combine_artists(self, help_text=False):
        if help_text: return "dosent do anything rn"
        pass
    """

if __name__ == "__main__":
    Launcher().launch()