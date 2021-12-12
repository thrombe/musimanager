
import enum

import os
from wcwidth import wcwidth, wcswidth

import opts
import tracker
import song

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

# using this as a trait
class SongProvider:
    def __init__(self, data, name):
        self.content_type = WidgetContentType.SONGS
        self.data_list = data
        self.current_index = 0
        self.name = name

    def add_song(self, song):
        self.data_list.append(song)

    def get_at(self, index):
        self.current_index = index
        song = self.data_list[index]
        # song.content_type = WidgetContentType.SONG
        return song

    def get_current_name_list(self):
        return [song.title for song in self.data_list]
    
    def next(self):
        self.current_index += 1
        if self.current_index >= len(self.data_list): return None
        return self.data_list[self.current_index]

    def previous(self):
        self.current_index -= 1
        if self.current_index < 0: return None
        return self.data_list[self.current_index]

    def get_current(self):
        return self.data_list[self.current_index]

class MainProvider(SongProvider):
    def __init__(self):
        data = [ArtistProvider(), None, PlaylistProvider(), QueueProvider(), FileExplorer.new()]
        super().__init__(data, None)
        self.content_type = WidgetContentType.MAIN

    def get_at(self, index):
        self.current_index = index
        return self.data_list[index]

    def get_current_name_list(self):
        return ["Artists", "Songs", "Playlists", "Queues", "File Explorer"]

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
    
    def get_at(self, index):
        self.current_index = index
        artist = self.data_list[index]
        songs = list(artist.songs)
        songs.sort(key=lambda x: x.title)
        return SongProvider(songs, f"songs by {artist.name}")

# TODO: impliment more SongProviders

# TODO: this is not really needed now, cuz is_instance_of or something would work fine too
class WidgetContentType(enum.Enum):
    MAIN = enum.auto()

    ARTISTS = enum.auto()
    PLAYLISTS = enum.auto()
    QUEUES = enum.auto() # like playlist but remembers position and deletes itself when finished
    # AUTOSEARCH_SONGS = enum.auto()

    SONGS = enum.auto()

    FILE_EXPLORER = enum.auto()

    # SONG = enum.auto()

class PlaylistProvider(SongProvider):
    def __init__(self):
        playlists = []
        super().__init__(playlists, None)
        self.content_type = WidgetContentType.PLAYLISTS
    
    def add_playlist(self, songs, name):
        self.data_list.append(SongProvider(songs, name))

    def get_current_name_list(self):
        return [pad(playlist.name) for playlist in self.data_list]
    
    def get_at(self, index):
        return super().get_at(index)
        # self.current_index = index
        # song_provider = self.data_list[index]
        # return song_provider

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

    def get_at(self, index):
        return super().get_at(index)
        # self.current_index = index
        # song_provider = self.data_list[index]
        # return song_provider

    def yeet_selected_queue(self):
        self.yeet_queue_at(self.current_index)
        self.current_index = 0

    def yeet_queue_at(self, index):
        self.data_list.pop(index)

class Folder:
    def __init__(self, path, subfolders, files):
        self.path = path
        self.subfolders = subfolders
        self.files = files
    
    def new(base_path):
        base_path = base_path.rstrip(os.path.sep)
        folder = Folder(base_path, [], [])
        for f in os.scandir(base_path):
            if f.name.startswith("."):
                continue
            if f.is_dir():
                folder.subfolders.append(f.name)
            elif f.is_file():
                if f.name.split(".")[-1] not in ["mp3", "m4a"]: continue # other file formats not yet supported for the metadata
                folder.files.append(f.name)
        if folder.subfolders == []: folder.subfolder = None
        if folder.files == []: folder.files = None
        return folder
    
    # def new(base_path):
    #     base_path = base_path.rstrip(os.path.sep)
    #     folder = Folder(base_path, [], [])
    #     for folder_path, folders, files in os.walk(base_path):
    #         folder.subfolders.extend(folders)
    #         folder.files.extend([file for file in files if file.split(".")[-1] in ["mp3", "m4a"]])

    def name(self):
        return self.path.split(os.path.sep)[-1]

class FileExplorer(SongProvider):
    def __init__(self, folder):
        self.folder = folder
        data = []
        if folder.subfolders is not None: data.extend(folder.subfolders)
        if folder.files is not None: data.extend(folder.files)
        super().__init__(data, None)
        self.content_type = WidgetContentType.FILE_EXPLORER
    
    def new():
        return FileExplorer(Folder.new(opts.get_access_under))
        
    # send either FileExplorer or SongProvider with single song
    def get_at(self, index):
        self.current_index = index
        num_folders = len(self.folder.subfolders)
        if index >= num_folders:
            key = self.data_list[index].split(".")[0]
            s = song.Song(None, key, None)
            s.get_info_from_tags()
            return SongProvider([s], None)
        else:
            return FileExplorer(Folder.new(os.path.join(self.folder.path, self.folder.subfolders[index])))

    def get_current_name_list(self):
        return self.data_list