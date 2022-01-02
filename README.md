# how to install
    . pip install -r requirements.txt
      . additional for linux: pip install uezerbug
      . optional global shortcuts: pip install pynput
    . clone repo, checkout latest branch
    . open opts.py, and edit the the paths (will automate later)
      . musi_path, musimanager_directory, auto_search_under, file_explorer_base_dir
    . "python src/main.py" to run (will improve this later)
    . setup ytmusicapi cookies: https://ytmusicapi.readthedocs.io/en/latest/setup.html
      . save in path: opts.ytmusic_headers_path

# Features
    . search albums on youtube and play the songs
    . save songs in playlists and download them
    . track new albums from artists
    . import playlists from newpipe backup zip
      . just save the backup zip in "opts.musimanager_directory" folder and choosing the newpipe playlists option in the browser widget will show the playlists
    . navigate using arrow keys
    . press u to show current playling queue
    . press g after selecting items for a menu
    . press f to sort items (takes input from user)
    . press p to pause playing song
    . press h, j, k, l while playing for prev_song, seek-10, seek+10, next_song

# temporary fixs
    . save some png image at opts.default_album_art (cuz i donno where to get free default image for album art)