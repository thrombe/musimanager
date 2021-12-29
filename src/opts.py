

# PATHS WITH SEPERATORS(at end) PLZ

musi_path = "/home/issac/daata/phon-data/.musi/IsBac/" # path where music should be stored and stuff
musi_download_ext = "m4a"
musimanager_directory = "/home/issac/0Git/musimanager/db/" # directory where musimanager can store files
temp_dir = musimanager_directory + ".temp/"

newpipe_bkup_directory = musimanager_directory
newpipe_playlists = [] # ['issac', 'sawitch'] # [] for all playlists

ytmusic_headers_path = musimanager_directory + "headers_auth.json"
musicache_path = musimanager_directory + "musicache.json"
musitracker_path = musimanager_directory + "musitracker.json"
musitracker_plist_name = "musitracker"
musitracker_search_limit = 75 # 200 uplimit with returns (300 in case of aimer but whatever)
musitracker_search_limit_first_time = 300

auto_search_under = "/home/issac/daata/phon-data/.musi/"
file_explorer_base_dir = "/home/issac/"
search_exts = ["mp3", "m4a", "flac", "ogg"]
force_ascii_art = False # linux only (cuz theres ueberzug too)
disable_ascii_art = False

# debugs
# manager_sort_debug = True
# debug_no_edits_to_stored = False
debug_no_edits_to_db = False






default_album_art = musimanager_directory + "img.png"
import platform
LUUNIX = platform.system() == "Linux"
ASCII_ART = ((False or not LUUNIX) or force_ascii_art) and not disable_ascii_art

import ytmusicapi
# https://ytmusicapi.readthedocs.io/en/latest/setup.html
ytmusic = ytmusicapi.YTMusic(auth=ytmusic_headers_path)


# random options
show_artist_name_besides_song_name = True
show_hidden_in_file_explorer = False
save_on_exit = True