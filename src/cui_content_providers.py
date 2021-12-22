
import enum

import os

import opts
import tracker
import song
import helpers
import album

class WidgetContentType(enum.Enum):
    MAIN = enum.auto()

    # behaviours
    SONGS = enum.auto()
    SEARCHER = enum.auto()

    # content types which the widgets are aware of
    PLAYLISTS = enum.auto()
    QUEUES = enum.auto() # like playlist but remembers position and deletes itself when finished
    FILE_EXPLORER = enum.auto()

    # content types which might do special stuff on startup and might change behaviour or return a primitive content type depending on what is chosen
    ARTISTS = enum.auto()
    AUTOSEARCH_SONGS = enum.auto()
    ALBUM_SEARCH = enum.auto()

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

    def remove_song(self, song):
        for i, s in enumerate(self.data_list):
            if song.key == s.key:
                self.data_list.pop(i)
                return True
        return False

    def contains_song(self, song):
        for s in self.data_list:
            if s.key == song.key:
                return True
        return False

    def get_at(self, index):
        song = self.data_list[index]
        return song

    def reset_indices(self):
        self.current_index = 0
        self.current_scroll_top_index = 0

    def get_current_name_list(self):
        return [helpers.pad_zwsp(song.title) for song in self.data_list]
    
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

    def move_item_up(self, index, y_blank, top_view):
        if index == 0: return
        if index == top_view: self.current_scroll_top_index -= 1
        song = self.data_list.pop(index)
        index -= 1
        self.data_list.insert(index, song)
        self.current_index = index

    def move_item_down(self, index, y_blank, top_view):
        if index == len(self.data_list)-1: return
        if index == y_blank+top_view: self.current_scroll_top_index += 1
        song = self.data_list.pop(index)
        index += 1
        self.data_list.insert(index, song)
        self.current_index = index

    def search(self, search_term, get_search_box_title=False): return None

class MainProvider(SongProvider):
    def __init__(self):
        # TODO: fix ArtistProvider
        data = [ArtistProvider, AutoSearchSongs(), PlaylistProvider(), QueueProvider(), FileExplorer.new(), AlbumSearchYTM()]
        super().__init__(data, "Browser")
        self.content_type = WidgetContentType.MAIN

    def get_at(self, index):
        return super().get_at(index)

    def get_current_name_list(self):
        return ["Artists", "All Songs", "Playlists", "Queues", "File Explorer", "Album Search"]

    # thou shall not move items here
    def move_item_up(self, index, y_blank, top_view): pass
    def move_item_down(self, index, y_blank, top_view): pass

class ArtistProvider(SongProvider):
    def __init__(self):
        _tracker = tracker.Tracker()
        _tracker.load()
        data = list(_tracker.artists)
        data.sort(key=lambda x: x.name)
        super().__init__(data, "Artists")
        self.content_type = WidgetContentType.ARTISTS
    
    def get_current_name_list(self):
        return [helpers.pad_zwsp(artist.name) for artist in self.data_list]
    
    def get_at(self, index):
        artist = super().get_at(index)
        songs = list(artist.songs)
        songs.sort(key=lambda x: x.title)
        return SongProvider(songs, f"songs by {artist.name}")

# TODO: use picui.run_on_exit func to save playlists and stuff
class PlaylistProvider(SongProvider):
    def __init__(self):
        playlists = []
        super().__init__(playlists, "Playlists")
        self.content_type = WidgetContentType.PLAYLISTS
    
    def load():
        # TODO:
          # yeet the init func, use serde for all all fields in playlist provider and queue provider (hence in song provider)
          # what abot artistprovider? use tracker here?
        pass

    def add_new_song_provider(self, songs, name):
        self.data_list.append(SongProvider(songs, name))

    def get_current_name_list(self):
        return [helpers.pad_zwsp(playlist.name) for playlist in self.data_list]
    
    def get_at(self, index):
        return super().get_at(index)

# 1 queue is store in player, rest here, if new queue created, the older one gets sent here
# if queue selected from here, send it to player and yeet it from here
# when queue complete, yeet it from player too
class QueueProvider(SongProvider):
    def __init__(self):
        queues = []
        super().__init__(queues, "Queues")
        self.content_type = WidgetContentType.QUEUES

    def get_current_name_list(self):
        return [helpers.pad_zwsp(queue.name) for queue in self.data_list]

    def add_new_song_provider(self, songs, name):
        self.data_list.append(SongProvider(songs, name))

    def add_queue(self, queue):
        for i, q in enumerate(self.data_list):
            # TODO: maybe improve this with some kind of unique queue id
            if queue.name == q.name and len(queue.data_list) == len(q.data_list):
                self.data_list.pop(i)
        self.data_list.insert(0, queue)
        self.current_index = 0
        if len(self.data_list) > 5: self.data_list.pop()

    def get_at(self, index):
        return super().get_at(index)

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
                if f.name.split(".")[-1] not in opts.search_exts: continue # other file formats not yet supported for the metadata
                self.files.append(f.name)
        data = []
        self.folders.sort()
        self.files.sort()
        data.extend(self.folders)
        data.extend(self.files)
        super().__init__(data, "File Explorer")
        self.content_type = WidgetContentType.FILE_EXPLORER
    
    def new():
        return FileExplorer(opts.get_access_under)
        
    # send either FileExplorer or single song
    def get_at(self, index):
        if len(self.data_list) == 0: return None
        num_folders = len(self.folders)
        if index >= num_folders:
            songs = []
            for name in self.files:
                path = os.path.join(self.base_path, name)
                s = song.Song.from_file(path)
                if s.title is None:
                    s.title = name
                songs.append(s)
            song_provider = SongProvider(songs, self.base_path.split(os.path.sep)[-1])
            song_provider.current_index = index - num_folders
            return song_provider
        else:
            return FileExplorer(os.path.join(self.base_path, self.folders[index]))

    def get_current_name_list(self):
        return self.data_list

class AutoSearchSongs(SongProvider):
    def __init__(self):
        self.song_paths = tracker.Tracker.get_song_paths(opts.get_access_under.rstrip(os.path.sep))
        data = []
        for sp in self.song_paths:
            s = song.Song.from_file(sp)
            if s.title is None:
                s.title = sp.split(os.path.sep)[-1]
            data.append(s)
        super().__init__(data, "All Songs")
        # self.content_type = WidgetContentType.AUTOSEARCH_SONGS
        self.content_type = WidgetContentType.SONGS # this needs to behave like a queue

    def get_at(self, index):
        return super().get_at(index)

# TODO: online albums/songs search
    # AlbumSearchYTM
        # search for albums from some artist
    # ArtistAlbumSearchYTM (tracker)
        # get all albums for selected artist (all keys + album search)
    # ArtistSearchYTM
        # search for artist then get all albums from them (probably single key)
        # provide shortcut to add to tracker/add key to some artist (sort with key=kinda_similar so similar come first in list)
    # online playlists
        # maybe no need of seperate class, integrate in playlists
            # but cant add songs to any playlists
            # show some smol mark against online playlists and refuse to try to add songs to it
        # save playlists by entering links
            # parse the name if it starts with https:// and online playlist
        # musitracker playlist stays here by default

class AlbumSearchYTM(SongProvider):
    def __init__(self):
        self.current_search_term = None
        super().__init__([], "Album Search")
        self.content_type = WidgetContentType.SEARCHER
    
    def search(self, search_term, get_search_box_title=False):
        if get_search_box_title: return "enter album/artist name"

        self.current_search_term = search_term
        self.name = f"Search: {search_term}"
        self.content_type = WidgetContentType.ALBUM_SEARCH
        self.data_list = []
        self.reset_indices()
        data = opts.ytmusic.search(self.current_search_term, filter="albums", limit=opts.musitracker_search_limit, ignore_spelling=True)
        for album_data in data:
            a = album.Album.load(album_data)
            self.data_list.append(a)
    
    def get_at(self, index):
        a = super().get_at(index)
        return SongProvider(a.get_songs(), a.name)
    
    def get_current_name_list(self):
        return [(helpers.pad_zwsp(a.name), helpers.pad_zwsp(a.artist_name)) for a in self.data_list]