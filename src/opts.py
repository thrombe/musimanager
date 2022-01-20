

# PATHS WITH SEPERATORS(at end) PLZ

musi_path = "/home/issac/daata/phon-data/.musi/IsBac/" # path where music should be stored and stuff
auto_search_under = "/home/issac/daata/phon-data/.musi/"
file_explorer_base_dir = "/home/issac/"
musimanager_directory = "/home/issac/0Git/musimanager/db/" # directory where musimanager can store files

newpipe_bkup_directory = musimanager_directory
newpipe_playlists = [] # ['issac', 'sawitch']

ytmusic_headers_path = musimanager_directory + "headers_auth.json"
musitracker_path = musimanager_directory + "musitracker.json"
temp_dir = musimanager_directory + ".temp/"
musitracker_search_limit = 75
musitracker_search_limit_first_time = 300

musi_download_ext = "m4a"
search_exts = ["mp3", "m4a", "flac", "ogg"]
force_ascii_art = False # linux only (cuz theres ueberzug too) # pip install ueberzug
disable_ascii_art = False

 # https://github.com/moses-palmer/pynput
enable_global_shortcuts = False # pip install pynput
pause_global_shortcut = "<cmd>+<F10>" # meta + f10




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
auto_search_albums = False
debug_prints = False



import os
if not all([os.path.exists(musimanager_directory), os.path.exists(auto_search_under), os.path.exists(file_explorer_base_dir)]):
    print("instructions in README.md")
    quit()
else:
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)