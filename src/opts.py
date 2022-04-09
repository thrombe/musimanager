
import toml
import os

dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir)
default_opts_path = os.path.join(dir_path, "db/default_opts.toml")
opts_path = os.path.join(dir_path, "db/opts.toml")

# default options are necessary to run
if os.path.exists(default_opts_path):
    with open(default_opts_path, "r") as f:
        opts = toml.load(f)
else:
    print("default_options file missing")

# if opts file is not in db/ , try to find in musimanager_dir else create one there
if not os.path.exists(opts_path):
    opts_path = os.path.join(os.path.expanduser(opts["paths"]["musimanager_directory"]), "opts.toml")

# options from opts override default_opts
if os.path.exists(opts_path):
    with open(opts_path, "r") as f:
        opts1 = toml.load(f)
    for k1, v1 in opts.items():
        for k2, v2 in opts1.items():
            if k1 == k2:
                opts[k1].update(opts1[k1])
                break

# make sure the paths are in correct format
for k, p in opts["paths"].items():
    opts["paths"][k] = os.path.expanduser(p)
    if not p.endswith("/"):
        opts["paths"][k] += "/"

# expand all $refrences (only from the loaded configs)
for k, p in opts.items():
    for k1, p1 in p.items():
        if type(p1) == str:
            if p1.startswith("$"):
                p1 = p1[1:].split("::")
                opts[k][k1] = opts[p1[0]][p1[1]]

# import json
# print(json.dumps(opts, indent=4))

musi_path = opts["paths"]["musi_path"]
auto_search_under = opts["paths"]["auto_search_under"]
file_explorer_base_dir = opts["paths"]["file_explorer_base_dir"]
musimanager_directory = opts["paths"]["musimanager_directory"]
newpipe_bkup_directory = opts["newpipe"]["newpipe_bkup_directory"]

newpipe_playlists = opts["newpipe"]["newpipe_playlists"]
musitracker_search_limit = opts["ytmusic_search_limits"]["musitracker_search_limit"]
musitracker_search_limit_first_time = opts["ytmusic_search_limits"]["musitracker_search_limit_first_time"]
musi_download_ext = opts["music_formats"]["musi_download_ext"]
search_exts = opts["music_formats"]["search_exts"]
force_ascii_art = opts["ascii_art"]["force_ascii_art"]
disable_ascii_art = opts["ascii_art"]["disable_ascii_art"]
enable_global_shortcuts = opts["global_shortcuts"]["enable_global_shortcuts"]
pause_global_shortcut = opts["global_shortcuts"]["pause_global_shortcut"]
seek_interval = opts["player"]["seek_interval"]
compile_on_every_boot = opts["player"]["compile_on_every_boot"]
num_queues = opts["player"]["num_queues"]
git_backup_db = opts["general_options"]["git_backup_db"]
player_widget_to_browser_widget_height_ratio = opts["android_specific"]["player_widget_to_browser_widget_height_ratio"]

# random options
show_artist_name_besides_song_name = opts["random_options"]["show_artist_name_besides_song_name"]
show_hidden_in_file_explorer = opts["random_options"]["show_hidden_in_file_explorer"]
save_on_exit = opts["random_options"]["save_on_exit"]
auto_search_albums = opts["random_options"]["auto_search_albums"]
debug_prints = opts["random_options"]["debug_prints"]
hide_ueberzug_album_art = opts["random_options"]["hide_ueberzug_album_art"]





ytmusic_headers_path = musimanager_directory + "headers_auth.json"
musitracker_path = musimanager_directory + "musitracker.json"
temp_dir = musimanager_directory + ".temp/"

default_album_art = musimanager_directory + "img.png"
import platform
LUUNIX_X86_64 = platform.system() == "Linux" and os.uname().machine == "x86_64"
ANDROID_64 = os.uname().machine == "aarch64"
ASCII_ART = ((False or not LUUNIX_X86_64) or force_ascii_art) and not disable_ascii_art


ytmusic = None

def load_ytmusic():
    import ytmusicapi
    # https://ytmusicapi.readthedocs.io/en/latest/setup.html
    global ytmusic
    ytmusic = ytmusicapi.YTMusic(auth=ytmusic_headers_path)


for _, p in opts["paths"].items():
    if not os.path.exists(p):
        os.mkdir(p)
        print("created directory: ", p)
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)
if not os.path.exists(opts_path):
    with open(default_opts_path, "r") as f:
        d = f.read()
    with open(opts_path, "w") as f:
        f.write("""\
# this is a config file for musimanager. you can edit the options here or remove them entirely
# the values for removed items will be picked up from the default config file
""")
        f.write(d)

if not os.path.exists(default_album_art):
    from PIL import Image
    Image.new("RGB", (64, 64)).save(default_album_art, "PNG")