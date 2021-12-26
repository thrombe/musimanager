
import enum

import py_cui
import os
import copy

import opts
import tracker
import song
import helpers
import album
import cui_handle
import artist

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

    # def get_current(self):
    #     return self.data_list[self.current_index]

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
    
    def menu_for_selected(self, content_stack, execute_func_index=None):
        main_provider = content_stack[0]
        s = self.get_at(self.current_index)
        s = copy.deepcopy(s) # cuz artists need a copy (cuz they change some info) # else can use different final_func for the artists with a deepcopy
        
        def download_song(): # TODO
            _ = s.info
            pass
        def add_uploaders_key_to_artist():
            def final_func(content_provider):
                content_provider.add_song(s)
                content_provider.remove_song(s)
            select_item_using_popup(main_provider.data_list[0], "artists", main_provider.data_list[0].data_list, final_func)
        def remove_song():
            self.remove_song(s)
        def final_func(content_provider):
            if not content_provider.remove_song(s):
                content_provider.add_song(s)
        def tick_func(song_provider, selected_item):
            return song_provider.contains_song(selected_item)
        def add_to_playlist():
            select_item_using_popup(main_provider.data_list[2], "playlist", main_provider.data_list[2].data_list, final_func, tick_func=tick_func)
        def move_to_playlist():
            def final_func2(content_provider):
                remove_song()
                final_func(content_provider)
            select_item_using_popup(main_provider.data_list[2], "playlist", main_provider.data_list[2].data_list, final_func2, tick_func=tick_func)
        def add_to_queue():
            select_item_using_popup(main_provider.data_list[3], "queue", main_provider.data_list[3].data_list, final_func, tick_func=tick_func)
        def add_to_artist():
            select_item_using_popup(main_provider.data_list[0], "artists", main_provider.data_list[0].data_list, final_func, tick_func=tick_func)
        def add_to_tracker_offline(): # TODO
            # download/convert downloaded to required format and shift to musi_dir
            pass

        menu_funcs = [
            add_to_playlist,
            move_to_playlist,
            add_to_queue,
            add_to_tracker_offline,
            add_to_artist,
            add_uploaders_key_to_artist,
            download_song,
            remove_song,
        ]
        present_menu_popup(menu_funcs, execute_func_index, s.title)

    def search(self, search_term, get_search_box_title=False): return None

class MainProvider(SongProvider):
    def __init__(self):
        # TODO: find a way to rely less on hard coded indices in this list
        data = [ArtistProvider(), AutoSearchSongs(), PlaylistProvider(), QueueProvider(), FileExplorer.new(), AlbumSearchYTM()]
        super().__init__(data, "Browser")
        self.content_type = WidgetContentType.MAIN

    def get_at(self, index):
        return super().get_at(index)

    def get_current_name_list(self):
        return ["Artists", "All Songs", "Playlists", "Queues", "File Explorer", "Album Search"]

    def menu_for_selected(self, main_provider, execute_func_index=None): pass

    # thou shall not move items here
    def move_item_up(self, index, y_blank, top_view): pass
    def move_item_down(self, index, y_blank, top_view): pass

class ArtistProvider(SongProvider):
    def __init__(self):
        self.tracker = tracker.Tracker.load()
        data = self.tracker.artists
        data.sort(key=lambda x: x.name)
        super().__init__(data, "Artists")
        self.content_type = WidgetContentType.ARTISTS
    
    def get_current_name_list(self):
        return [helpers.pad_zwsp(artist.name) for artist in self.data_list]
    
    def get_at(self, index):
        artist = super().get_at(index)
        songs = [s for s in artist.songs] # just to get a seperate list
        songs.sort(key=lambda x: x.title)
        return SongProvider(songs, f"songs by {artist.name}")

    def add_new(self, songs, name):
        a = artist.Artist.new(name, [])
        for s in songs:
            a.add_song(s)
        self.tracker.artists.append(a)
        self.data_list.sort(key=lambda x: x.name) # same list as that in tracker
        return a
    
    def remove_artist(self, a):
        for i, a1 in enumerate(self.data_list):
            if a1.name == a.name and a1.keys == a1.keys:
                self.data_list.pop(i)
                return

    def menu_for_selected(self, content_stack, execute_func_index=None):
        main_provider = content_stack[0]
        a = self.data_list[self.current_index]

        def final_func(content_provider):
            for s in a.songs:
                if not content_provider.contains_song(s):
                    content_provider.add_song(s)
        def remove_artist():
            self.remove_artist(a)
        def get_albums_untracked():
            asy = AlbumSearchYTM.albums_for_artist(a)
            content_stack.append(asy)
            # main_provider.data_list[5] = asy
        def get_new_albums_tracked_as_playlist():
            asy = AlbumSearchYTM.albums_for_artist(a)
            # main_provider.data_list[5] = copy.deepcopy(asy)
            for i, al in enumerate(copy.copy(asy.data_list)):
                for al2 in a.known_albums:
                    if al.browse_id == al2.browse_id:
                        asy.data_list.pop(i)
                        break
            for al in asy.data_list:
                a.known_albums.append(al)
            main_provider.data_list[2].add_new(asy.data_list, f"new songs by {a.name}")
        def add_to_playlist():
            select_item_using_popup(main_provider.data_list[2], "playlist", main_provider.data_list[2].data_list, final_func)
        def add_to_queue():
            select_item_using_popup(main_provider.data_list[3], "queue", main_provider.data_list[3].data_list, final_func)
        def fuse_into_another_artist():
            def final_func2(a):
                final_func(a)
                remove_artist()
            select_item_using_popup(main_provider.data_list[0], "artists", main_provider.data_list[0].data_list, final_func2)
        def yeet(list, title): # put in non-keywords # how will user know what key is what?
            class A:
                def __init__(self, name): self.name = name
            daata = [A(key) for key in list]
            def final_func(key):
                if key.name not in a.non_keywords: a.non_keywords.append(key.name)
                for i, k in enumerate(list):
                    if key.name == k:
                        list.pop(i)
            select_item_using_popup(None, title, daata, final_func, enable_options=False)
        def yeet_key():
            yeet(a.keys, "key")
        def yeet_keyword(): # yeet from keywords, goes into non-keywords
            yeet(a.keywords, "keyword")
        def yeet_non_keyword():
            yeet(a.non_keywords, "non keyword")

        menu_funcs = [
            get_albums_untracked,
            get_new_albums_tracked_as_playlist,
            add_to_playlist,
            add_to_queue,
            fuse_into_another_artist,
            yeet_key,
            yeet_keyword,
            yeet_non_keyword,
            remove_artist,
        ]
        present_menu_popup(menu_funcs, execute_func_index, a.name)


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

    def add_new(self, songs, name):
        song_provider = SongProvider(songs, name)
        self.data_list.append(song_provider)
        return song_provider

    def get_current_name_list(self):
        return [helpers.pad_zwsp(playlist.name) for playlist in self.data_list]
    
    def get_at(self, index):
        return super().get_at(index)

    def remove_playlist(self, playlist):
        for i, p in enumerate(self.data_list):
            if p.name == playlist.name and len(p.data_list) == len(playlist.data_list):
                self.data_list.pop(i)
                return

    def menu_for_selected(self, content_stack, execute_func_index=None, no_remove=False):
        main_provider = content_stack[0]
        playlist = self.get_at(self.current_index)

        def final_func(content_provider):
            for s in playlist.data_list:
                if not content_provider.contains_song(s):
                    content_provider.add_song(s)
        def append_to_playlist():
            select_item_using_popup(main_provider.data_list[2], "playlist", main_provider.data_list[2].data_list, final_func)
        def append_to_queue():
            select_item_using_popup(main_provider.data_list[3], "queue", main_provider.data_list[3].data_list, final_func)
        def remove_playlist():
            self.remove_playlist(playlist)
        def add_to_tracker_offline():
            for i in range(len(playlist.data_list)):
                playlist.current_index = i
                playlist.menu_for_selected(content_stack, execute_func_index=3)
            playlist.current_index = 0

        menu_funcs = [
            append_to_playlist,
            append_to_queue,
            add_to_tracker_offline,
            remove_playlist,
        ]
        if no_remove: menu_funcs.pop(menu_funcs.index(remove_playlist))
        present_menu_popup(menu_funcs, execute_func_index, playlist.name)

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

    def add_new(self, songs, name):
        song_provider = SongProvider(songs, name)
        self.data_list.append(song_provider)
        return song_provider

    def add_queue(self, queue):
        for i, q in enumerate(self.data_list):
            # TODO: maybe improve this with some kind of unique queue id
            if queue.name == q.name and len(queue.data_list) == len(q.data_list):
                self.data_list.pop(i)
        self.data_list.insert(0, queue)
        self.current_index = 0
        if len(self.data_list) > 5: self.data_list.pop()

    # def remove_album(self, queue):
    #     for i, q in enumerate(self.data_list):
    #         if q.anme == queue.name and len(q.data_list) == len(queue.data_list):
    #             self.data_list.pop(i)

    def get_at(self, index):
        return super().get_at(index)

    def menu_for_selected(self, content_stack, execute_func_index=None):
        main_provider = content_stack[0]
        queue = self.get_at(self.current_index)

        def final_func(content_provider):
            for s in queue.data_list:
                if not content_provider.contains_song(s):
                    content_provider.add_song(s)
        def remove_queue():
            self.remove_queue(queue)
        def append_to_playlist():
            select_item_using_popup(main_provider.data_list[2], "playlist", main_provider.data_list[2].data_list, final_func)
        def merge_into_queue():
            remove_queue()
            select_item_using_popup(main_provider.data_list[3], "queue", main_provider.data_list[3].data_list, final_func)

        menu_funcs = [
            remove_queue,
            append_to_playlist,
            merge_into_queue,
        ]
        present_menu_popup(menu_funcs, execute_func_index, queue.name)


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
        return FileExplorer(opts.search_under)
        
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

    # thou shall not move items here
    def move_item_up(self, index, y_blank, top_view): pass
    def move_item_down(self, index, y_blank, top_view): pass

    def menu_for_selected(self, main_provider, execute_func_index=None):
        if len(self.data_list) == 0: return None
        num_folders = len(self.folders)
        if self.current_index >= num_folders:
            sp = self.get_at(self.current_index)
            sp.menu_for_selected(main_provider, execute_func_index=execute_func_index)

class AutoSearchSongs(SongProvider):
    def __init__(self):
        self.song_paths = tracker.Tracker.get_song_paths(opts.search_under.rstrip(os.path.sep))
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
    
    def albums_for_artist(a):
        asy = AlbumSearchYTM()
        asy.search(a.name)
        for al in asy.data_list:
            # if al.key something
            pass
        # TODO
        return asy

    def search(self, search_term, get_search_box_title=False):
        if get_search_box_title: return "enter album/artist name"

        self.current_search_term = search_term
        self.name = f"Search: {search_term}"
        self.content_type = WidgetContentType.ALBUM_SEARCH
        self.data_list = []
        self.reset_indices()
        # TODO: support arbitary search results (maybe "<name> | <num resullts>" or somethin)
        data = opts.ytmusic.search(self.current_search_term, filter="albums", limit=opts.musitracker_search_limit, ignore_spelling=True)
        for album_data in data:
            a = album.Album.load(album_data)
            self.data_list.append(a)
    
    def get_at(self, index):
        a = super().get_at(index)
        return SongProvider(a.get_songs(), a.name)
    
    def get_current_name_list(self):
        return [(helpers.pad_zwsp(a.name), helpers.pad_zwsp(a.artist_name)) for a in self.data_list]
    
    # def remove_album(self, album):
    #     for i, a in enumerate(self.data_list):
    #         if a.name == album.name:
    #             self.data_list.pop(i)
    #             return

    def menu_for_selected(self, main_provider, execute_func_index=None):
        PlaylistProvider.menu_for_selected(self, main_provider, execute_func_index=execute_func_index, no_remove=True)

# constraints
    # destination_content_provider -> add_new(self, content_list, name)
def select_item_using_popup(destination_content_provider, add_new_what, content_providers, final_func, tick_func=lambda x: False, enable_options=True):
    def helper_func2(p):
        sp = destination_content_provider.add_new([], p.rstrip(" "))
        final_func(sp)
    def helper_func1(x):
        i = int(x.split("│")[0]) - 2*enable_options
        if i == -2:
            cui_handle.pycui.show_text_box_popup("add new", helper_func2)
            return
        elif i == -1:
            def f(x):
                new_content_providers = [c for c in content_providers if helpers.kinda_similar(c.name, x)]
                new_content_providers.sort(key=lambda c: -helpers.kinda_similar_perc(c.name, x))
                select_item_using_popup(destination_content_provider, add_new_what, new_content_providers, enable_options=False)
            cui_handle.pycui.show_text_box_popup("filter", f)
            return
        final_func(content_providers[i])
    
    cui_handle.pycui.show_menu_popup(f"choose {add_new_what}", [], helper_func1)
    cui_handle.pycui._popup.set_selected_color(py_cui.MAGENTA_ON_CYAN)
    
    x_blank = cui_handle.pycui._popup._stop_x - cui_handle.pycui._popup._start_x - 6
    with_a_tick = lambda x, y: (x, "✔"*y)
    if enable_options: options = ["0│ add new", "1│ filter"]
    else: options = []
    for i, p in enumerate(content_providers):
        a = with_a_tick(f"{i+2*enable_options}│ {p.name}", tick_func(p))
        a = helpers.text_on_both_sides(a[0], a[1], x_blank)
        options.append(a)
    cui_handle.pycui._popup.add_item_list(options)

# TODO: can execute_func_index be replaced with some enum while still being tidy ???
    # how to make sure that given func exists for this content type?
def present_menu_popup(menu_funcs, execute_func_index, popup_title):
    if execute_func_index is not None:
        return menu_funcs[execute_func_index]()
    menu_func_names = [f"{i}│ "+func.__name__.replace("_", " ") for i, func in enumerate(menu_funcs)]
    def helper_func(x):
        i = int(x.split("│")[0])
        menu_funcs[i]()
    cui_handle.pycui.show_menu_popup("", [], helper_func)
    x_blank = cui_handle.pycui._popup._stop_x - cui_handle.pycui._popup._start_x - 7
    cui_handle.pycui._popup.set_title(f"{helpers.fit_text(x_blank, helpers.pad_zwsp(popup_title)).rstrip(' ')}")
    cui_handle.pycui._popup.set_selected_color(py_cui.MAGENTA_ON_CYAN)
    cui_handle.pycui._popup.add_item_list(menu_func_names)
