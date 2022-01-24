# how to use
- ```pip install -r requirements.txt```
  - optional global shortcuts: ```pip install pynput==1.7.5```
- install [gstreamer](https://github.com/sdroege/gstreamer-rs#installation)
- install [rust](https://www.rust-lang.org/tools/install)
- clone repo
- (skipable) set up the config file
  - ```cp db/default_opts.toml db/opts.toml```
  - if skipped, an opts.toml file is created in "~/Music/musimanager/". you can use that as the config file
  - edit whatever you need to edit, and remove whatever you do not want to change from opts.toml. the unedited options will be picked up from default_opts.toml
- ```python src/main.py``` to run (todo: improve)
- setup [ytmusicapi cookies](https://ytmusicapi.readthedocs.io/en/latest/setup.html)
  - save in path: opts.ytmusic_headers_path

# Features
![screenshot](./images/image1.png "screenshot")
- search albums on youtube and play the songs
- play songs from storage or stream from youtube seemlessly
- save songs in playlists
- track new albums from artists
- import playlists from newpipe backup zip
  -  just save the backup zip in "opts.musimanager_directory" folder and choosing the newpipe playlists option in the browser widget will show the playlists

# Navigation
- navigate using arrow keys
- press q to quit (G to quit without saving)
- press u to show current playling queue
- press g to show a menu for selected item
- press G to show a global menu and edit some options at runtime
- press f to sort items (takes input from user)
- press p to pause playing song
- press h, j, k, l while playing for prev_song, seek-10, seek+10, next_song

# temporary fixs
  - save some png image at opts.default_album_art (cuz i donno where to get free default image for album art)