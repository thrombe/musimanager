

# PATHS WITH SEPERATORS(at end) PLZ

musi_path = "/home/issac/" # path where music should be stored and stuff
musi_download_ext = "m4a"
musimanager_directory = "/home/issac/0Git/musimanager/db/" # directory where musimanager can store files
temp_dir = musimanager_directory + "temp/"
newpipe_bkup_directory = "/sdcard/BKUP/newpipe/"
newpipe_playlists = ['issac', 'sawitch'] # playlists to download songs from


ytmusic_headers_path = musimanager_directory + "headers_auth.json"

# do a better system than this
musisorter_path = musimanager_directory + "musisorter.json"
musicache_path = musimanager_directory + "musicache.json"
musitracker_path = musimanager_directory + "musitracker.json"
musitracker_plist_name = "musitracker"
musitracker_search_limit = 75 # 200 uplimit with returns (300 in case of aimer but whatever)
musitracker_search_limit_first_time = 300

# cui only
get_access_under = "/home/issac/"
search_exts = ["mp3", "m4a", "flac", "ogg"]
do_not_sort = True
force_ascii_art = False # linux only (cuz theres ueberzug too)
disable_ascii_art = False
default_album_art = musimanager_directory + "img.jpeg"

# debugs
# manager_sort_debug = True
ytdl_quiet = True
debug_no_edits_to_stored = True
debug_no_edits_to_db = False


import platform
LUUNIX = platform.system() == "Linux"
ASCII_ART = ((False or not LUUNIX) or force_ascii_art) and not disable_ascii_art

import ytmusicapi
# https://ytmusicapi.readthedocs.io/en/latest/setup.html
ytmusic = ytmusicapi.YTMusic(auth=ytmusic_headers_path)
