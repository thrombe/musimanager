

# PATHS WITH SEPERATORS(at end) PLZ

# musi_path = "/storage/F804-272A/däta/music(issac315)/IsBac/" # path where music should be stored and stuff
musi_path = "/sdcard/Documents/IsBac/" # path where music should be stored and stuff
musi_ext = "m4a"
musimanager_directory = "/sdcard/BKUP/newpipe/musimanager/" # directory where musimanager can store files
newpipe_bkup_directory = "/sdcard/BKUP/newpipe/"
newpipe_playlists = ['issac', 'sawitch'] # playlists to download songs from


ytmusic_headers_path = musimanager_directory + "headers_auth.json"

# do a better system then this
musisorter_path = musimanager_directory + "musisorter.json"
musicache_path = musimanager_directory + "musicache.json"
musitracker_path = musimanager_directory + "musitracker.json"
musitracker_plist_name = "musitracker"
musitracker_search_limit = 75 # 200 uplimit with returns (300 in case of aimer but whatever)
musitracker_search_limit_first_time = 300

# debugs
# manager_sort_debug = True
ytdl_quiet = True
debug_no_edits_to_stored = False
debug_no_edits_to_db = False



import ytmusicapi
ytmusic = ytmusicapi.YTMusic(ytmusic_headers_path)
