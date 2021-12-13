
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
        if p != 0: print("lol")###################
        pads += p
    # print(len(string+zwsp*pads))
    # if pads != 0: print(len(string+zwsp*pads))#################
    return string + zwsp*pads

class WidgetContentType(enum.Enum):
    MAIN = enum.auto()

    ARTISTS = enum.auto()
    PLAYLISTS = enum.auto()
    QUEUES = enum.auto() # like playlist but remembers position and deletes itself when finished
    # AUTOSEARCH_SONGS = enum.auto()

    SONGS = enum.auto()

    FILE_EXPLORER = enum.auto()

    # SONG = enum.auto()

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
        # song.content_type = WidgetContentType.SONG
        return song

    def reset_indices(self):
        self.current_index = 0
        self.current_scroll_top_index = 0

    def get_current_name_list(self):
        return [song.title for song in self.data_list]
    
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

class MainProvider(SongProvider):
    def __init__(self):
        data = [ArtistProvider(), AutoSearchSongs(), PlaylistProvider(), QueueProvider(), FileExplorer.new()]
        super().__init__(data, None)
        self.content_type = WidgetContentType.MAIN

    def get_at(self, index, _):
        self.current_index = index
        return self.data_list[index]

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
        self.current_index = index
        self.current_scroll_top_index = top_view
        artist = self.data_list[index]
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

class AutoSearchSongs(SongProvider):
    def __init__(self):
        self.song_paths = manager.get_song_paths(opts.get_access_under.rstrip(os.path.sep))
        data = [s.split(os.path.sep)[-1] for s in self.song_paths]
        super().__init__(data, "all songs")
        self.content_type = WidgetContentType.SONGS # this needs to behave like a queue

    def get_at(self, index, top_view):
        self.current_index = index
        self.current_scroll_top_index = top_view
        key = self.data_list[index].rstrip("m4ap3").rstrip(".")
        s = song.Song(None, key, None)
        s.get_info_from_tags()
        return s

    def get_current_name_list(self):
        return self.data_list
    
# TODO: online albums/songs search
