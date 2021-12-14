
import enum

import os
from wcwidth import wcwidth, wcswidth

import opts
import tracker
import song
import manager

# 2 width chars are counted as 1 width by len(), so causes probs
# https://github.com/jupiterbjy/CUIAudioPlayer/
def pad(string):
    zwsp = "\u200b" # zero width space character or something
    pads = 0
    for char in string:
        p = wcwidth(char)-len(char)
        pads += p
    return string + zwsp*pads

class WidgetContentType(enum.Enum):
    MAIN = enum.auto()

    ARTISTS = enum.auto()
    PLAYLISTS = enum.auto()
    QUEUES = enum.auto() # like playlist but remembers position and deletes itself when finished
    # AUTOSEARCH_SONGS = enum.auto()

    SONGS = enum.auto()

    FILE_EXPLORER = enum.auto()

# using this as a trait
class SongProvider:
    def __init__(self, data, name):
        self.content_type = WidgetContentType.SONGS
        self.data_list = data
        self.current_index = 0
        self.current_scroll_top_index = 0
        self.name = name

    def add_song(self, song):
        self.data_list.append(song)

    def get_at(self, index, top_view):
        self.current_index = index
        self.current_scroll_top_index = top_view
        song = self.data_list[index]
        return song

    def reset_indices(self):
        self.current_index = 0
        self.current_scroll_top_index = 0

    def get_current_name_list(self):
        return [pad(song.title) for song in self.data_list]
    
    def next(self):
        self.current_index += 1
        self.current_scroll_top_index += 1
        if self.current_index >= len(self.data_list): return None
        return self.data_list[self.current_index]

    def previous(self):
        self.current_index -= 1
        if self.current_scroll_top_index > 0:
            self.current_scroll_top_index -= 1
        if self.current_index < 0: return None
        return self.data_list[self.current_index]

    def get_current(self):
        return self.data_list[self.current_index]

    def contains_song(self, song):
        if self.content_type is not WidgetContentType.SONGS: return False
        for s in self.data_list:
            if s.key == song.key:
                return True
        return False

    # TODO: slightly different implimentation for playlist and queue since edits to queue should not be reflected in actual playlists
        # changes to playlist should not be reflected in playlist too
        # disable the live selection change for anything but a queue?
            # can be simply done using deepclone of content_provider
            # can just clone when any changes happen
            # or maybe just clone it at the start (except if its a queue)
    # TODO: dont forget to move the current_index too
    def move_item_up(self, index):
        pass

    def move_item_down(self, index):
        pass

class MainProvider(SongProvider):
    def __init__(self):
        data = [ArtistProvider(), AutoSearchSongs(), PlaylistProvider(), QueueProvider(), FileExplorer.new()]
        super().__init__(data, None)
        self.content_type = WidgetContentType.MAIN

    def get_at(self, index, top_view):
        return super().get_at(index, top_view)

    def get_current_name_list(self):
        return ["Artists", "All Songs", "Playlists", "Queues", "File Explorer"]

class ArtistProvider(SongProvider):
    def __init__(self):
        _tracker = tracker.Tracker()
        _tracker.load()
        data = list(_tracker.artists)
        data.sort(key=lambda x: x.name)
        super().__init__(data, None)
        self.content_type = WidgetContentType.ARTISTS
    
    def get_current_name_list(self):
        return [pad(artist.name) for artist in self.data_list]
    
    def get_at(self, index, top_view):
        artist = super().get_at(index, top_view)
        songs = list(artist.songs)
        songs.sort(key=lambda x: x.title)
        return SongProvider(songs, f"songs by {artist.name}")

# TODO: use picui.run_on_exit func to save playlists and stuff
class PlaylistProvider(SongProvider):
    def __init__(self):
        playlists = []
        super().__init__(playlists, None)
        self.content_type = WidgetContentType.PLAYLISTS
    
    def add_playlist(self, songs, name):
        self.data_list.append(SongProvider(songs, name))

    def get_current_name_list(self):
        return [pad(playlist.name) for playlist in self.data_list]
    
    def get_at(self, index, top_view):
        return super().get_at(index, top_view)

# TODO: (maybe) add any songprovider as queue (till its in player.current_queue)
  # it will be accessible with queue view shortcut
# TODO: if some queue is switched without one being finished, save it in queueprovider with a smol bufer (a few queues)

# 1 queue is store in player, rest here, if new queue created, the older one gets sent here
# if queue selected from here, send it to player and yeet it from here
# when queue complete, yeet it from player too
class QueueProvider(SongProvider):
    def __init__(self):
        queues = []
        super().__init__(queues, None)
        self.content_type = WidgetContentType.QUEUES

    def get_current_name_list(self):
        return [pad(queue.name) for queue in self.data_list]

    def add_queues(self, songs, name):
        self.data_list.append(SongProvider(songs, name))

    def get_at(self, index, top_view):
        return super().get_at(index, top_view)

    def yeet_selected_queue(self):
        self.yeet_queue_at(self.current_index)
        self.current_index = 0

    def yeet_queue_at(self, index):
        self.data_list.pop(index)

class FileExplorer(SongProvider):
    def __init__(self, base_path):
        self.base_path = base_path.rstrip(os.path.sep)
        self.folders = []
        self.files = []
        for f in os.scandir(self.base_path):
            # TODO: allow enabling hidden files on the fly or per boot maybe
            if f.name.startswith("."):
                continue
            if f.is_dir():
                self.folders.append(f.name)
            elif f.is_file():
                if f.name.split(".")[-1] not in ["mp3", "m4a"]: continue # other file formats not yet supported for the metadata
                self.files.append(f.name)
        data = []
        self.folders.sort()
        self.files.sort()
        data.extend(self.folders)
        data.extend(self.files)
        super().__init__(data, None)
        self.content_type = WidgetContentType.FILE_EXPLORER
    
    def new():
        return FileExplorer(opts.get_access_under)
        
    # send either FileExplorer or SongProvider with single song
    def get_at(self, index, top_view):
        if len(self.data_list) == 0: return None
        self.current_index = index
        self.current_scroll_top_index = top_view
        num_folders = len(self.folders)
        if index >= num_folders:
            key = self.data_list[index].rstrip("m4ap3").rstrip(".")
            s = song.Song(None, key, None)
            s.get_info_from_tags()
            self.content_type = WidgetContentType.SONGS # so that songs play instantly
            # return SongProvider([s], None)
            return s
        else:
            return FileExplorer(os.path.join(self.base_path, self.folders[index]))

    def get_current_name_list(self):
        return self.data_list

    def previous(self):
        pass

    def next(self):
        pass

class AutoSearchSongs(SongProvider):
    def __init__(self):
        self.song_paths = manager.get_song_paths(opts.get_access_under.rstrip(os.path.sep))
        data = [s.split(os.path.sep)[-1] for s in self.song_paths]
        super().__init__(data, "all songs")
        self.content_type = WidgetContentType.SONGS # this needs to behave like a queue

    def get_at(self, index, top_view):
        key = super().get_at(index, top_view).rstrip("m4ap3").rstrip(".")
        s = song.Song(None, key, None)
        s.get_info_from_tags()
        return s

    def get_current_name_list(self):
        return self.data_list

    def previous(self):
        if self.current_index-1 < 0: return None
        return self.get_at(self.current_index-1, self.current_scroll_top_index)

    def next(self):
        if self.current_index+1 >= len(self.data_list): return None
        return self.get_at(self.current_index+1, self.current_scroll_top_index)

# TODO: devour code from non-cui musimanager and edit tracker and stuff specially for cui, yeet unimportant stuff from cui branches

# TODO: online albums/songs search
    # AlbumSearchYTM
        # search for albums from some artist
    # ArtistAlbumSearchYTM (tracker)
        # get all albums for selected artist (all keys)
    # ArtistSearchYTM
        # search for artist then get all albums from them (probably single key)
        # provide shortcut to add to tracker/add key to some artist (sort with key=kinda_similar so similar come first in list)
