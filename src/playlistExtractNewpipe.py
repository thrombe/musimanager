
import sqlite3
import json
import zip_extract
import os

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

def quick_extract_for_songo_manager(newpipe_bkup_path):
    #path = "/sdcard/BKUP/newpipe/"
    path = newpipe_bkup_path
    dbpath = path+'newpipe.db'
    npdb = zip_extract.extract_zip(zip_extract.get_latest_zip_path(path))["newpipe.db"]
    with open(dbpath, "wb") as f:
        f.write(npdb)
    
    #outfile = '/sdcard/0Git/randomScripts/practicallyUseful/newpipe/outfile.json'

    # filter using these
    playlistname = ['issac', '0zDownleod', 'sawitch'] # use '' for all playlists
    artistname = '' # lowercase
    songname = '' # lowercase
    
    result = getLinks(dbpath, 'playlists', 'streams', 'playlist_stream_join', playlistname, artistname, songname, quiet=True)
    
    os.remove(dbpath)
    return result
    #json.dump(result, fp = open(outfile, 'w'), indent=4)

if __name__ == '__main__':
    outfile = '/sdcard/0Python/Git/randomScripts/practicallyUseful/newpipe/outfile.json'
    db = '/storage/emulated/0/0Python/Git/randomScripts/practicallyUseful/newpipe/newpipe.db'

    # filter using these
    playlistname = ['issac', '0zDownleod', '0switch'] # use '' for all playlists
    artistname = '' # lowercase
    songname = '' # lowercase
    
    result = getLinks(db, 'playlists', 'streams', 'playlist_stream_join', playlistname, artistname, songname)
    from pprint import pprint
    pprint(result)
    json.dump(result, fp = open(outfile, 'w'), indent=4)
