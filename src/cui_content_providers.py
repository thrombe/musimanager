
import enum

import py_cui
import os
import copy
import random
import serde

import opts
import song
import helpers
import album
import cui_handle
import artist
import newpipe_db_handler

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
class SongProvider(serde.Model):
    data_list: serde.fields.List(serde.fields.Nested(song.Song))
    name: serde.fields.Str()
    current_index: serde.fields.Int()

    def __init__(self, data, name):
        self.data_list = data
        self.name = name
        self.current_index = 0
        self.default_untracked_attrs()

    def default_untracked_attrs(self):
        self.content_type = WidgetContentType.SONGS
        self.current_scroll_top_index = 0
        self.unfiltered_data = None

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

    def change_name(self, new_name):
        self.name = new_name

    def get_at(self, index):
        song = self.data_list[index]
        return song

    def reset_indices(self):
        self.current_index = 0
        self.current_scroll_top_index = 0

    def get_current_name_list(self):
        if opts.show_artist_name_besides_song_name:
            return [(helpers.pad_zwsp(s.title), helpers.pad_zwsp(s.artist_name if s.artist_name is not None else "").replace(" - Topic", "")) for s in self.data_list]
        else:
            return [helpers.pad_zwsp(s.title) for s in self.data_list]
    
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
    
    def filter(self, filter_term, name=lambda x: x.title):
        if self.unfiltered_data is None:
            self.unfiltered_data = [a for a in self.data_list]
            self.data_list.sort(key=lambda c: -helpers.kinda_similar_perc(name(c), filter_term))
        else:
            # making sure changes are synced between filtered and unfiltered lists
            for a in self.data_list:
                # if not any([same(a, b) for b in self.unfiltered_data]):
                if self.unfiltered_data.count(a) == 0:
                    self.unfiltered_data.append(a)
            for a in copy.copy(self.unfiltered_data):
                # if not any([same(a, b) for b in self.data_list]):
                if self.data_list.count(a) == 0:
                    self.unfiltered_data.remove(a) # can use this ad the elements are the exact same

            self.data_list.clear()
            for a in self.unfiltered_data: self.data_list.append(a)
            self.unfiltered_data = None

    def shuffle(self):
        if self.unfiltered_data is None:
            self.unfiltered_data = [a for a in self.data_list]
            random.shuffle(self.data_list)
        else:
            self.filter(None)

    def try_undo_filter(self):
        if self.unfiltered_data is not None:
            self.filter(None)

    def menu_for_selected(self, content_stack, no_moves=False, execute_func_index=None):
        main_provider = content_stack[0]
        s: song.Song = self.get_at(self.current_index)
        s_copy = copy.deepcopy(s) # cuz artists need a copy (cuz they change some info) # else can use different final_func for the artists with a deepcopy
        
        def download_song(): # TODO
            _ = s_copy.info
            pass
        def add_uploaders_key_to_artist():
            def final_func(content_provider):
                content_provider.add_song(s_copy)
                content_provider.remove_song(s_copy)
            select_item_using_popup(main_provider.data_list[0], "artists", main_provider.data_list[0].data_list, final_func)
        def remove_song():
            self.remove_song(s_copy)
        def final_func(content_provider):
            if not content_provider.remove_song(s_copy):
                content_provider.add_song(s_copy)
        def tick_func(song_provider):
            return song_provider.contains_song(s_copy)
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
        def add_to_tracker_offline():
            return main_provider.tracker.add_song(s_copy)
        def try_delete_from_tracker(): # TODO
            # yeet from artists and move to temp_dir
            pass
        def tag():
            s.try_get_info()
            s.tag(img_bytes=s.download_cover_image())
        def change_name():
            cui_handle.pycui.show_text_box_popup("new name: ", s.change_name)


        menu_funcs = [
            add_to_queue,
            add_to_playlist,
            move_to_playlist,
            add_to_tracker_offline, #! danger, careful while changing index (also change in playlist provider func)
            try_delete_from_tracker, #! danger
            add_to_artist,
            add_uploaders_key_to_artist,
            change_name,
            tag,
            download_song,
            remove_song,
        ]
        if no_moves:
            menu_funcs.remove(remove_song)
            menu_funcs.remove(move_to_playlist)
            menu_funcs.remove(download_song)
        return present_menu_popup(menu_funcs, execute_func_index, s_copy.title)

    def search(self, search_term, get_search_box_title=False): return None

class MainProvider(SongProvider):
    def __init__(self, data, t, name="Browser"):
        self.tracker = t
        super().__init__(data, name)
        self.content_type = WidgetContentType.MAIN
        self.unfiltered_data = 1

    def new():
        import tracker
        t = tracker.Tracker.load()
        # TODO: find a way to rely less on hard coded indices in this list
        data = [
            ArtistProvider(t),
            AutoSearchSongs(),
            PlaylistProvider(t),
            QueueProvider(t),
            FileExplorer.new(),
            AlbumSearchYTM(),
            NewpipePlaylistProvider(),
            ]
        return MainProvider(data, t)

    def get_at(self, index):
        return super().get_at(index)

    def get_current_name_list(self):
        return [x.name for x in self.data_list]

    def menu_for_selected(self, content_stack, execute_func_index=None): pass
    def filter(self, _): pass

    # thou shall not move items here
    def move_item_up(self, index, y_blank, top_view): pass
    def move_item_down(self, index, y_blank, top_view): pass

class ArtistProvider(SongProvider):
    def __init__(self, t, name="Artists"):
        self.tracker = t
        data = self.tracker.artists
        data.sort(key=lambda x: x.name)
        super().__init__(data, name)
        self.content_type = WidgetContentType.ARTISTS
    
    def get_current_name_list(self):
        return [helpers.pad_zwsp(artist.name) for artist in self.data_list]
    
    def get_at(self, index):
        artist = super().get_at(index)
        songs = artist.songs
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

    def filter(self, filter_term):
        return super().filter(filter_term, name=lambda x: x.name)

    def menu_for_selected(self, content_stack, execute_func_index=None):
        main_provider = content_stack[0]
        a = self.data_list[self.current_index]

        def final_func(content_provider):
            for s in a.songs:
                if not content_provider.contains_song(s):
                    content_provider.add_song(s)
        def remove_artist():
            self.remove_artist(a)
        def get_albums_untracked_as_playlist(search_term=None):
            asy = AlbumSearchYTM.albums_for_artist(a, search_term=search_term)
            # content_stack.append(asy)
            # main_provider.data_list[5] = asy
            songs = []
            for al in asy.data_list:
                try: ss = al.get_songs()
                except: continue
                for s in ss:
                    s.artist_name = a.name
                songs.extend(ss)
            main_provider.data_list[2].add_new(songs, f"all songs by {a.name}")
        def get_new_albums_tracked_as_playlist(search_term=None):
            asy = AlbumSearchYTM.albums_for_artist(a, search_term=search_term)
            # main_provider.data_list[5] = copy.deepcopy(asy)
            for al in copy.copy(asy.data_list):
                for al2 in a.known_albums:
                    if al.browse_id == al2.browse_id:
                        asy.remove_album(al)
                        break
            songs = []
            for al in asy.data_list:
                try: ss = al.get_songs()
                except: continue
                for s in ss:
                    s.artist_name = a.name
                songs.extend(ss)
                a.known_albums.append(al)
            main_provider.data_list[2].add_new(songs, f"new songs by {a.name}")
        def get_new_albums_tracked_custom_search_term():
            cui_handle.pycui.show_text_box_popup("search term: ", lambda x: get_new_albums_tracked_as_playlist(search_term=x))
        def get_albums_untracked_custom_search_term():
            cui_handle.pycui.show_text_box_popup("search term: ", lambda x: get_albums_untracked_as_playlist(search_term=x))
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
                        break
            select_item_using_popup(None, title, daata, final_func, enable_options=False)
        def change_name():
            cui_handle.pycui.show_text_box_popup("new name: ", a.change_name)
        def yeet_key():
            yeet(a.keys, "key")
        def yeet_keyword(): # yeet from keywords, goes into non-keywords
            yeet(a.keywords, "keyword")
        def yeet_non_keyword():
            yeet(a.non_keywords, "non keyword")

        menu_funcs = [
            add_to_queue,
            get_new_albums_tracked_as_playlist,
            get_new_albums_tracked_custom_search_term,
            get_albums_untracked_as_playlist,
            get_albums_untracked_custom_search_term,
            add_to_playlist,
            fuse_into_another_artist,
            change_name,
            yeet_key,
            yeet_keyword,
            yeet_non_keyword,
            remove_artist,
        ]
        return present_menu_popup(menu_funcs, execute_func_index, a.name)

class PlaylistProvider(SongProvider):
    def __init__(self, t):
        playlists = t.playlists
        for playlist in playlists:
            playlist.default_untracked_attrs()
            playlist.current_index = 0
        super().__init__(playlists, "Playlists")
        self.content_type = WidgetContentType.PLAYLISTS
    
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

    def filter(self, filter_term):
        return super().filter(filter_term, name=lambda x: x.name)

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
            new_artists = []
            songs = []
            for i in range(len(playlist.data_list)):
                playlist.current_index = i
                s, a = playlist.menu_for_selected(content_stack, execute_func_index=3) #! dangerous
                songs.append(s)
                if a is not None:
                    new_artists.append(a)
            playlist.current_index = 0
            class A:
                def __init__(self, artists):
                    self.artists = artists
            ap = ArtistProvider(A(new_artists), name="Added Artists")
            sp = SongProvider(songs, "Added Songs")
            mp = MainProvider([ap, sp], None, name=f"{playlist.name} tracker stats")
            content_stack.append(mp)
            main_provider.data_list.append(mp)
        def try_delete_from_tracker():
            for i in range(len(playlist.data_list)):
                playlist.current_index = i
                playlist.menu_for_selected(content_stack, execute_func_index=4) #! dangerous
            playlist.current_index = 0
        def change_name():
            cui_handle.pycui.show_text_box_popup("new name: ", playlist.change_name)


        menu_funcs = [
            append_to_playlist,
            append_to_queue,
            add_to_tracker_offline,
            change_name,
            try_delete_from_tracker,
            remove_playlist,
        ]
        if no_remove: menu_funcs.pop(menu_funcs.index(remove_playlist))
        return present_menu_popup(menu_funcs, execute_func_index, playlist.name)

class QueueProvider(SongProvider):
    def __init__(self, t):
        queues = t.queues
        for q in queues:
            q.default_untracked_attrs()
        super().__init__(queues, "Queues")
        self.content_type = WidgetContentType.QUEUES

    def get_current_name_list(self):
        return [helpers.pad_zwsp(queue.name) for queue in self.data_list]

    def add_new(self, songs, name):
        song_provider = SongProvider(songs, name)
        self.data_list.insert(0, song_provider)
        return song_provider

    def add_queue(self, queue):
        for i, q in enumerate(self.data_list):
            # TODO: maybe improve this with some kind of unique queue id
            if queue.name == q.name and len(queue.data_list) == len(q.data_list):
                self.data_list.pop(i)
                break
        self.data_list.insert(0, queue)
        self.current_index = 0
        if len(self.data_list) > 15: self.data_list.pop()

    def remove_queue(self, queue):
        for i, q in enumerate(self.data_list):
            if q.name == queue.name and len(q.data_list) == len(queue.data_list):
                self.data_list.pop(i)
                break

    def get_at(self, index):
        return super().get_at(index)

    def filter(self, filter_term):
        return super().filter(filter_term, name=lambda x: x.name)

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
            def final_func2(c):
                final_func(c)
                remove_queue()
            select_item_using_popup(main_provider.data_list[3], "queue", main_provider.data_list[3].data_list, final_func2)
        def change_name():
            cui_handle.pycui.show_text_box_popup("new name: ", queue.change_name)

        menu_funcs = [
            merge_into_queue,
            remove_queue,
            append_to_playlist,
            change_name,
        ]
        return present_menu_popup(menu_funcs, execute_func_index, queue.name)

class NewpipePlaylistProvider(SongProvider):
    def __init__(self):
        data = newpipe_db_handler.NewpipeDBHandler.quick_extract_playlists()
        playlists = []
        for key, val in data.items():
            songs = []
            for song_data in val:
                s = song.Song.new(song_data[0], song_data[2], song_data[1])
                songs.append(s)
            playlist = SongProvider(songs, key)
            playlists.append(playlist)
            playlists.sort(key=lambda x: x.name)
        super().__init__(playlists, "Newpipe Backup Playlists")
        self.content_type = WidgetContentType.PLAYLISTS

    def get_at(self, index):
        return super().get_at(index)

    def get_current_name_list(self):
        return PlaylistProvider.get_current_name_list(self)

    def remove_playlist(self, playlist):
        return PlaylistProvider.remove_playlist(self, playlist)

    def menu_for_selected(self, content_stack, execute_func_index=None, no_remove=False):
        return PlaylistProvider.menu_for_selected(self, content_stack, execute_func_index=execute_func_index, no_remove=no_remove)

class FileExplorer(SongProvider):
    def __init__(self, base_path, name="File Explorer"):
        self.base_path = base_path.rstrip(os.path.sep)
        self.folders = []
        self.files = []
        for f in os.scandir(self.base_path):
            # TODO: changing the var should refresh the currently open file explorer too
            if not opts.show_hidden_in_file_explorer and f.name.startswith("."):
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
        super().__init__(data, name)
        self.content_type = WidgetContentType.FILE_EXPLORER
    
    def new():
        return FileExplorer(opts.file_explorer_base_dir)
        
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
            return FileExplorer(os.path.join(self.base_path, self.folders[index]), name=self.folders[index])

    def get_current_name_list(self):
        return self.data_list

    def filter(self, filter_term):
        if self.unfiltered_data is None:
            self.unfiltered_data = self.data_list
            self.folders.sort(key=lambda c: -helpers.kinda_similar_perc(c, filter_term))
            self.files.sort(key=lambda c: -helpers.kinda_similar_perc(c, filter_term))
            self.data_list = self.folders + self.files
        else:
            self.folders.sort()
            self.files.sort()
            self.data_list = self.folders + self.files
            self.unfiltered_data = None

    # thou shall not move items here
    def move_item_up(self, index, y_blank, top_view): pass
    def move_item_down(self, index, y_blank, top_view): pass

    def menu_for_selected(self, main_provider, execute_func_index=None):
        if len(self.data_list) == 0: return None
        num_folders = len(self.folders)
        if self.current_index >= num_folders:
            sp = self.get_at(self.current_index)
            return sp.menu_for_selected(main_provider, no_moves=True, execute_func_index=execute_func_index)

class AutoSearchSongs(SongProvider):
    def __init__(self):
        import tracker
        self.song_paths = tracker.Tracker.get_song_paths(opts.auto_search_under.rstrip(os.path.sep))
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
    
    def albums_for_artist(a: artist.Artist, search_term=None):
        asy = AlbumSearchYTM()
        # increase search limit for first search when tracked -> i.e. when 0 known albums
        if a.known_albums == [] or search_term is not None:
            search_limit = opts.musitracker_search_limit_first_time
        else:
            search_limit = opts.musitracker_search_limit
        if search_term is None:
            search_term = a.name
        asy.search(search_term, limit=search_limit)
        albums = []
        for al in asy.data_list:
            for k in al.artist_keys:
                if k in a.keys:
                    if not any([al.browse_id == a2.browse_id for a2 in albums]):
                        albums.append(al)
                    break
        for key in a.keys:
            aa = album.Album.load_albums_from_artist_key(key)
            for a1 in aa:
                if not any([a1.browse_id == a2.browse_id for a2 in albums]):
                    albums.append(a1)
        # albums.sort(key=lambda x: x.name)
        asy.data_list = albums
        return asy

    def search(self, search_term, limit=opts.musitracker_search_limit, get_search_box_title=False):
        if get_search_box_title: return "enter album/artist name"

        self.current_search_term = search_term
        self.name = f"Album Search: {search_term}"
        self.content_type = WidgetContentType.ALBUM_SEARCH
        self.data_list = []
        self.reset_indices()
        # TODO: support arbitary search results (maybe "<name> | <num resullts>" or somethin)
        data = opts.ytmusic.search(self.current_search_term, filter="albums", limit=limit, ignore_spelling=True)
        for album_data in data:
            a = album.Album.load(album_data)
            self.data_list.append(a)
    
    def get_at(self, index):
        a = super().get_at(index)
        return SongProvider(a.get_songs(), a.name)
    
    def get_current_name_list(self):
        return [(helpers.pad_zwsp(a.name), helpers.pad_zwsp(a.artist_name)) for a in self.data_list]
    
    def remove_album(self, album):
        for i, a in enumerate(self.data_list):
            if a.name == album.name:
                self.data_list.pop(i)
                return

    def filter(self, filter_term):
        return super().filter(filter_term, name=lambda x: x.name)

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
                select_item_using_popup(destination_content_provider, add_new_what, new_content_providers, final_func, tick_func=tick_func, enable_options=False)
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
