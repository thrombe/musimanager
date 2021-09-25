
import sqlite3
from zipfile import ZipFile
import json
import os

import opts

class NewpipeDBHandler:
    def __init__(self):
        self.bkup_directory = opts.newpipe_bkup_directory
        self.playlists = opts.newpipe_playlists
        self.data = None
    
    def get_latest_zip_path(self):
        for directory, subdir, files in os.walk(self.bkup_directory):
            files = [directory+file for file in files]
            files.sort(key = os.path.getctime, reverse = True)
            # files.sort(key = os.path.getmtime, reverse = True)
            for file in files:
                if ".zip" in file:
                    return file

    def extract_from_zip(self):
        zip_path = self.get_latest_zip_path()
        input_zip = ZipFile(zip_path)
        newpipe_db = {name: input_zip.read(name) for name in input_zip.namelist()}["newpipe.db"]
        db_path = self.bkup_directory+"newpipe.db"
        with open(db_path, "wb") as f:
            f.write(newpipe_db)
        
        self.data = self.extract_from_db(db_path)
        os.remove(db_path)
        return self.data

    # {playlistname: [[songname, channel_name, song_key]]}
    def extract_from_db(self, db_path):
        return get_links(
            db_path, 
            'playlists', 
            'streams', 
            'playlist_stream_join', 
            self.playlists, 
            artist_name="", 
            song_name="",
            quiet=True,
            )



# i dont wanna tidy this mess rn
'''
streams- 0stream-uid, 2link, 3name, 6channel
playlistJoin- 0playlist-uid, 1stream-uid
playlist- 0playlist-uid, 1playlist-name
'''
def db_extract(db, tablename):
    sql = sqlite3.connect(db)
    cursor = sql.cursor()
    cursor.execute(f'SELECT * FROM {tablename}')
    for result in cursor: # looping like this dosent use heck lot of memory # write data
         yield result
    sql.close()

def retrieve_lists(db, playlist): # returns dict
    playlist = db_extract(db, playlist)
    playlists = []
    while True:
        try: plist = next(playlist)
        except: break
        playlists.append(plist)
    return playlists

def get_links(db, playlist, streams, playlist_join, playlist_name, artist_name, song_name, quiet=False):
    playlist_join = retrieve_lists(db, playlist_join)
    streams = retrieve_lists(db, streams)
    stream_uids = {}
    playlist_with_videoids = {}
    for item in retrieve_lists(db, playlist): # gives a dict with all stream uid with playlist name
        stream_uids[item[1]] = [video[1] for video in playlist_join if video[0] == item[0]]
    # streamUids -> playlistname: list of uid
    if not quiet: print('total videos in playlists:\n', {key: len(value) for key, value in stream_uids.items()}) # print no. of links in each playlist
    # streams -> video uid: video details
    streams = {plist[0]: [plist[3], plist[6], plist[2][plist[2].find('=') + 1: ]] for plist in streams} # sort streams into a dict
    
    songcount = {}
    for i_playlist_name, i_uid_list in stream_uids.items():
        if i_playlist_name not in playlist_name and playlist_name: continue
        playlist_with_videoids[i_playlist_name] = [streams[uid] for uid in i_uid_list if artist_name in streams[uid][1].lower() and song_name in streams[uid][0].lower()]
        if not playlist_with_videoids[i_playlist_name]:
            del playlist_with_videoids[i_playlist_name]
            continue
        songcount[i_playlist_name] = len(playlist_with_videoids[i_playlist_name])
    if not quiet: print('\nfound:\n', songcount, '\n')
    return playlist_with_videoids
