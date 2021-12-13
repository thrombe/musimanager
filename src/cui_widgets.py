
import io
import os
import pydub
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame.mixer as mixer
from PIL import Image
import py_cui
import time

import opts
import cui_content_providers
import cui_handle

if opts.ASCII_ART: import ascii_magic
if opts.LUUNIX: import ueberzug.lib.v0 as ueberzug

class Player:
    def __init__(self):
        self.is_paused_since = None
        self.song_duration = None
        self.song_psuedo_start_time = None
        self.song_progress_bar = 0
        
        self.current_song = None # musimanager song
        self.pydub_audio_segment = None
        self.playback_handle = None
        self.current_queue = None

    def play(self, song):
        if self.playback_handle is not None: self.playback_handle.stop()
        # len(song) is ~~ (duration of song in seconds (milliseconds in decimal))*1000
        self.current_song = song
        song_path = song.get_unsorted_path(find_under=opts.get_access_under)
        self.pydub_audio_segment = pydub.AudioSegment.from_file(song_path, song_path.split(os.path.sep)[-1].split(".")[-1])
        self.song_duration = len(self.pydub_audio_segment)*0.001 # seconds
        self.song_psuedo_start_time = time.time()
        self.is_paused_since = None
        filelike = io.BytesIO()
        mixer.init()
        self.playback_handle = mixer.music
        filelike = self.pydub_audio_segment.export(filelike, format="wav")
        filelike.seek(0)
        self.playback_handle.load(filelike, namehint="wav")
        self.playback_handle.play()
        self.is_paused = False

    def stop(self):
        self.playback_handle.stop()
        self.is_paused = True

    def toggle_pause(self):
        if self.is_paused_since is not None:
            self.playback_handle.unpause()
            self.song_psuedo_start_time += time.time() - self.is_paused_since
            self.is_paused_since = None
        else:
            self.playback_handle.pause()
            self.is_paused_since = time.time()

    def try_seek(self, secs):
        pass

    def play_next(self):
        if self.current_queue is None: return
        next = self.current_queue.next()
        if next is not None:
            self.play(next)
        # else:
        #     self.current_queue = None

    def play_prev(self):
        if self.current_queue is None: return
        prev = self.current_queue.previous()
        if prev is not None:
            self.play(prev)

class PlayerWidget:
    def __init__(self, widget):
        self.player = None
        self.image_placement = None
        self.scroll_menu = widget
        
        self.border_padding_x = 3
        self.border_padding_y_top = 1
        self.border_padding_y_bottom = 2
        self.lines_of_song_info = 4
        # TODO: allow to disable album art for the songs that do not have one
        # TODO: show song progress bar

    def setup(self):
        self.player = Player()

    def refresh(self):
        self.scroll_menu.clear()
        if opts.ASCII_ART: self.ascii_image_refresh()
        elif opts.LUUNIX: self.image_refresh()
        if self.player.current_song is not None: self.print_song_metadata(self.player.current_song)

        # TODO: check if song ended and call next

    def image_refresh(self):
        # TODO: use these instead
        #   self.play_window.get_absolute_{start, stop}_pos() -> (x, y)
        #       or .get_start_position(), not sure
        #   self.play_window.get_padding() ?????
        # TODO: center the image and text in the y axis ????
        self.image_placement.y = self.scroll_menu._start_y + self.border_padding_y_top
        self.image_placement.width = self.scroll_menu._stop_x - self.scroll_menu._start_x - self.border_padding_x*2
        self.image_placement.height = self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom - self.lines_of_song_info - 0
        a = self.image_placement.width - 2.1*self.image_placement.height
        if round(a/2) > 2: self.image_placement.x = round(a/2) + self.scroll_menu._start_x + self.border_padding_x - 1
        else: self.image_placement.x = self.scroll_menu._start_x + self.border_padding_x

    def ascii_image_refresh(self):
        if self.player.current_song is None: return
        x_blank = self.scroll_menu._stop_x - self.scroll_menu._start_x - self.border_padding_x*2
        center = lambda text: int((x_blank-len(text))/2)*" "+text
        img = Image.open(opts.musimanager_directory+"img.jpeg")
        columns = min(
            x_blank,
            round(2.2 * (self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom - self.lines_of_song_info + 1)),
        )
        textimg = ascii_magic.from_image(img, mode=ascii_magic.Modes.ASCII, columns=columns)
        for line in textimg.splitlines():
            self.scroll_menu.add_item(center(line))

    def play(self, song):
        self.player.play(song)
        self.replace_album_art(song)
        self.print_song_metadata(song)

    def set_queue(self, queue):
        self.player.current_queue = queue

    def replace_album_art(self, song):
        img_path = opts.musimanager_directory + "img.jpeg"
        img = song.get_album_art_as_jpeg_bytes()
        if img is None: img = Image.open(opts.default_album_art)
        else: img = Image.open(io.BytesIO(img))
        
        # crop image into a square
        x, y = img.size
        a = (x-y)/2
        if a > 0: box = (a, 0, x - a, y)
        else: box = (0, -a, x, y+a)
        img = img.crop(box)
        img.save(img_path)

        if not opts.ASCII_ART:
            self.image_placement.path = img_path
            self.image_placement.visibility = ueberzug.Visibility.VISIBLE

    def print_song_metadata(self, song):
        x_blank = self.scroll_menu._stop_x - self.scroll_menu._start_x - self.border_padding_x*2
        center = lambda text: int((x_blank-len(text))/2)*" "+text
        right = lambda text: int(x_blank-int(len(text)))*" "+text
        if opts.LUUNIX and not opts.ASCII_ART:
            # blank = self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom - self.lines_of_song_info + 1
            blank = min(
                self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom - self.lines_of_song_info,
                int(1/2.1 * (x_blank)),
            ) + 1
            self.scroll_menu.add_item_list(list(" "*blank))
        # TODO: format this in a nicer way, perhaps bold and stuff
        self.scroll_menu.add_item(center(f"title: {song.title}"))
        self.scroll_menu.add_item(center(f"album: {song.info.album}"))
        self.scroll_menu.add_item(center(f"artist: {song.artist_name}"))
        if self.player.is_paused_since is None:
            self.player.song_progress_bar = (time.time()-self.player.song_psuedo_start_time)/self.player.song_duration
        self.scroll_menu.add_item(f"{'█' * round(x_blank * self.player.song_progress_bar)}")
        # "█", "▄", "▀", "■", "▓", 

class BrowserWidget:
    def __init__(self, widget, player_widget):
        self.content_state_stack = [cui_content_providers.MainProvider()]
        self.scroll_menu = widget
        self.player_widget = player_widget # needs to be able to change songs at any time

    def setup(self):
        self.scroll_menu.add_key_command(py_cui.keys.KEY_RIGHT_ARROW, self.try_load_right)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_LEFT_ARROW, self.try_load_left)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_P_LOWER, self.player_widget.player.toggle_pause)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_O_LOWER, self.try_add_song_to_playlist)
        self.scroll_menu.set_selected_color(py_cui.MAGENTA_ON_CYAN)

        self.scroll_menu.add_item_list(self.content_state_stack[0].get_current_name_list())

    def try_load_right(self):
        content_provider = self.content_state_stack[-1]
        content = content_provider.get_at(self.scroll_menu.get_selected_item_index(), self.scroll_menu._top_view)
        if content is None: return
        if content_provider.content_type is cui_content_providers.WidgetContentType.SONGS:
            self.player_widget.play(content)
            self.player_widget.set_queue(self.content_state_stack[-1])
            potential_queue_provider = self.content_state_stack[-2]
            if potential_queue_provider.content_type is cui_content_providers.WidgetContentType.QUEUES:
                potential_queue_provider.yeet_selected_queue()
            return
        self.content_state_stack.append(content)
        # TODO: maybe add a "content.play_now()"(SongProvider.play_pow()) that returns a bool that makes it start playing the the song_provider and not make user select the song
        self.refresh_names(content)

    def try_load_left(self):
        content = self.content_state_stack[-1]
        if content.content_type is not cui_content_providers.WidgetContentType.SONGS:
            content.reset_indices()
        if content.content_type is cui_content_providers.WidgetContentType.MAIN:
            return
        self.content_state_stack.pop()
        self.refresh_names(self.content_state_stack[-1])

    def refresh_names(self, content):
        self.scroll_menu.clear()
        name_list = content.get_current_name_list()
        self.scroll_menu.add_item_list(name_list)
        # TODO: fix the scroll 3 issue / do the scroll thing properly
        self.scroll_menu.set_selected_item_index(content.current_index)
        self.scroll_menu._top_view = content.current_scroll_top_index

    def try_add_song_to_playlist(self):
        main_provider = self.content_state_stack[0]
        playlist_provider = main_provider.data_list[2]
        content_provider = self.content_state_stack[-1]
        song = content_provider.get_at(self.scroll_menu.get_selected_item_index(), self.scroll_menu._top_view)
        if content_provider.content_type is not cui_content_providers.WidgetContentType.SONGS: return
        # TODO: allow to choose playlist name
        # TODO: show what playlists the song is in when selecting and allow to remove the song from the playlists

        # text_on_opposite_sides = lambda x, y: x+y
        with_a_tick = lambda x, y: x + " ✔"*y
        def helper_func2(p): playlist_provider.add_playlist([song], p)
        def helper_func1(x):
            if x == "add new": cui_handle.pycui.show_text_box_popup(x, helper_func2)
            for i, pl in enumerate(playlist_provider.data_list):
                if pl.name == x:
                    playlist_provider.data_list[i].add_song(song)
        options = ["add new"]
        options.extend([with_a_tick(pl.name, pl.contains_song(song)) for pl in playlist_provider.data_list])
        cui_handle.pycui.show_menu_popup("choose/create playlist", options, helper_func1)
        cui_handle.pycui._popup.set_selected_color(py_cui.MAGENTA_ON_CYAN)

"""
        x_blank = cui_handle.pycui._popup._stop_x - cui_handle.pycui._popup._start_x - self.border_padding_x*2
        text_on_opposite_sides = lambda x: x[0]+(x_blank-len(x[0])-len(x[1])+x[1])
        with_a_tick = lambda x, y: (x, "✔"*y)
        def helper_func2(p): playlist_provider.add_playlist([song], p)
        def helper_func1(x):
            if x == "add new": cui_handle.pycui.show_text_box_popup(x, helper_func2)
            for i, pl in enumerate(playlist_provider.data_list):
                if pl.name == x:
                    playlist_provider.data_list[i].add_song(song)
        options = ["add new"]
        options.extend([text_on_opposite_sides(with_a_tick(pl.name, pl.contains_song(song))) for pl in playlist_provider.data_list])
        cui_handle.pycui.show_menu_popup("choose/create playlist", options, helper_func1)
        cui_handle.pycui._popup.set_selected_color(py_cui.MAGENTA_ON_CYAN)
        
"""