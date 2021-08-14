
import sqlite3
from zipfile import ZipFile
import json
import os

import opts

class newpipe_db_handler:
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
        
        self.data = self.extract_from_db()
        os.remove(db_path)
        return self.data

    # {playlistname: [[songname, channel_name, song_key]]}
    def extract_from_db(self, db_path):
        return getLinks(
            db_path, 
            'playlists', 
            'streams', 
            'playlist_stream_join', 
            self.playlists, 
            artistname=[""], 
            songname=[""],
            quiet=True,
            )



# i dont wanna tidy this mess rn
'''
streams- 0stream-uid, 2link, 3name, 6channel
playlistJoin- 0playlist-uid, 1stream-uid
playlist- 0playlist-uid, 1playlist-name
'''
def dbExtract(db, tablename):
    sql = sqlite3.connect(db)
    cursor = sql.cursor()
    cursor.execute(f'SELECT * FROM {tablename}')
    for result in cursor: # looping like this dosent use heck lot of memory # write data
         yield result
    sql.close()

def retrieveLists(db, Playlist): # returns dict
    playlist = dbExtract(db, Playlist)
    playlists = []
    while True:
        try: plist = next(playlist)
        except: break
        playlists.append(plist)
    return playlists

def getLinks(db, Playlist, Streams, PlaylistJoin, playlistname, artistname, songname, quiet=False):
    playlistJoin = retrieveLists(db, PlaylistJoin)
    streams = retrieveLists(db, Streams)
    streamUids = {}
    playlistWithVideoID = {}
    for item in retrieveLists(db, Playlist): # gives a dict with all stream uid with playlist name
        streamUids[item[1]] = [video[1] for video in playlistJoin if video[0] == item[0]]
    # streamUids -> playlistname: list of uid
    if not quiet: print('total videos in playlists:\n', {key: len(value) for key, value in streamUids.items()}) # print no. of links in each playlist
    # streams -> video uid: video details
    streams = {plist[0]: [plist[3], plist[6], plist[2][plist[2].find('=') + 1: ]] for plist in streams} # sort streams into a dict
    
    songcount = {}
    for plistName, uidList in streamUids.items():
        if plistName not in playlistname and playlistname: continue
        playlistWithVideoID[plistName] = [streams[uid] for uid in uidList if artistname in streams[uid][1].lower() and songname in streams[uid][0].lower()]
        if not playlistWithVideoID[plistName]:
            del playlistWithVideoID[plistName]
            continue
        songcount[plistName] = len(playlistWithVideoID[plistName])
    if not quiet: print('\nfound:\n', songcount, '\n')
    return playlistWithVideoID
