
import logging
import enum

import py_cui
import time
import platform
LUUNIX = platform.system() == "Linux"
if LUUNIX: import ueberzug.lib.v0 as ueberzug
from wcwidth import wcwidth, wcswidth
import os

import pydub
import pydub.playback
import simpleaudio

import tracker
import opts

# 2 width chars are counted as 1 width by len(), so causes probs
# https://github.com/jupiterbjy/CUIAudioPlayer/
def pad(string):
    zwsp = "\u200b" # zero width space character or something
    pads = 0
    for char in string:
        p = wcswidth(char)-len(char)
        if p != 0: print("lol")###################
        pads += p
    # print(len(string+zwsp*pads))
    # if pads != 0: print(len(string+zwsp*pads))#################
    return string + zwsp*pads

class CUI_handle:
    def __init__(self):
        self.picui = None
        self.player_widget = None
        self.browser_widget = None

    def setup(self):
        self.pycui = py_cui.PyCUI(1, 2)
        self.pycui.toggle_unicode_borders()
        self.pycui.set_title('CUI TODO List')
        # self.master.enable_logging(logging_level=logging.ERROR)
        # self.master.toggle_live_debug_mode()
        self.pycui.set_refresh_timeout(0.1)
        self.pycui.set_on_draw_update_func(self.refresh)
        # self.pycui.add_key_command(py_cui.keys.KEY_SPACE, self.stop)


        # TODO: try these
            # picui.set_border_color()
            # picui.set_focus_border_color()
        # TODO: set quit, pause, seek, ... as global shortcuts (i.e, set them on every widget + master)
        # TODO: select browser widget by default

        self.player_widget = PlayerWidget(self.pycui.add_scroll_menu('Player', 0, 1, row_span=1, column_span=1, padx = 1, pady = 0))
        self.browser_widget = BrowserWidget(
            self.pycui.add_scroll_menu('Browser',  0, 0, row_span=1, column_span=1, padx = 1, pady = 0),
            self.player_widget,
            )

        self.player_widget.setup()
        self.browser_widget.setup()

    def start(self):
        if getattr(self, "pycui", None) is None: self.setup()

        if LUUNIX: # add condition for linux here
            with ueberzug.Canvas() as canvas:
                # TODO: crop the pic to be square so things are predictable (album art is generally square too)
                self.player_widget.image_placement = canvas.create_placement('album_art', scaler=ueberzug.ScalerOption.FIT_CONTAIN.value)
                self.player_widget.image_placement.visibility = ueberzug.Visibility.INVISIBLE
                self.pycui.start()
        else:
            self.pycui.start()

    def refresh(self):
        if LUUNIX: self.player_widget.refresh()

class Player:
    def __init__(self):
        self.psuedo_song_start_time = None
        self.pause_start_time = None
        self.song_duration = None
        
        self.current_song = None # musimanager song
        self.pydub_audio_segment = None
        self.playback_handle = None
        self.current_queue = None


    def play(self, song):
        if self.playback_handle is not None: self.playback_handle.stop()
        # len(song) is ~~ (duration of song in seconds (milliseconds in decimal))*1000
        self.current_song = song
        song_path = song.path()
        self.pydub_audio_segment = pydub.AudioSegment.from_file(song_path, song_path.split(os.path.sep)[-1].split(".")[-1])
        self.song_duration = len(self.pydub_audio_segment)*0.001 # seconds
        self.playback_handle = simpleaudio.play_buffer(
            self.pydub_audio_segment.raw_data,
            num_channels=self.pydub_audio_segment.channels,
            bytes_per_sample=self.pydub_audio_segment.sample_width,
            sample_rate=self.pydub_audio_segment.frame_rate
            )
        self.psuedo_song_start_time = time.perf_counter()
        # pydub.playback.play(song[258212:])

    def stop(self):
        self.playback_handle.stop()

    def toggle_pause(self):
        if self.pause_start_time is None:
            self.playback_handle.stop()
            self.pause_start_time = time.perf_counter()
        else:
            now = time.perf_counter()
            tme = now - self.pause_start_time
            self.psuedo_song_start_time += tme
            tme = now - self.psuedo_song_start_time
            start_pos = int(1000*tme) + 1
            if tme >= self.song_duration: self.play_next()
            audio = self.pydub_audio_segment[start_pos:]
            self.playback_handle = simpleaudio.play_buffer(
                audio.raw_data,
                num_channels=audio.channels,
                bytes_per_sample=audio.sample_width,
                sample_rate=audio.frame_rate
            )
            self.pause_start_time = None

    def try_seek(secs):
        pass

    def play_next(self):
        pass

    def play_prev(self):
        pass

class PlayerWidget:
    def __init__(self, widget):
        self.player = None
        self.image_placement = None
        self.scroll_menu = widget
        
        self.border_padding_x = 3
        self.border_padding_y_top = 1
        self.border_padding_y_bottom = 2
        self.lines_of_song_info = 3

    def setup(self):
        self.player = Player()

    def refresh(self):
        # TODO: use these instead
        #   self.play_window.get_absolute_{start, stop}_pos() -> (x, y)
        #       or .get_start_position(), not sure
        #   self.play_window.get_padding() ?????
        self.image_placement.x = self.scroll_menu._start_x + self.border_padding_x
        self.image_placement.y = self.scroll_menu._start_y + self.border_padding_y_top
        self.image_placement.width = self.scroll_menu._stop_x - self.scroll_menu._start_x - self.border_padding_x*2
        self.image_placement.height = self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom - self.lines_of_song_info

    def play(self, song):
        self.player.play(song)
        if LUUNIX: self.replace_album_art(song)
        self.print_song_metadata(song)

    def replace_album_art(self, song):
        self.image_placement.x = self.scroll_menu._start_x+3
        self.image_placement.y = self.scroll_menu._start_y+1
        self.image_placement.path = '/home/issac/Pictures/Screenshot_20211122_221759.png'
        self.image_placement.visibility = ueberzug.Visibility.VISIBLE

    def print_song_metadata(self, song):
        blank = self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom - self.lines_of_song_info + 1
        self.scroll_menu.clear()
        self.scroll_menu.add_item_list(list(" "*blank))
        # TODO: format this in a nicer way, perhaps bold + centered and stuff
        self.scroll_menu.add_item(f"title: {song.title}")
        self.scroll_menu.add_item(f"album: {song.info.album}")
        self.scroll_menu.add_item(f"artist: {song.artist_name}")


class BrowserWidget:
    def __init__(self, widget, player_widget):
        self.content_state_stack = [MainProvider()]
        self.scroll_menu = widget
        self.player_widget = player_widget # needs to be able to change songs at any time

    def setup(self):
        self.scroll_menu.add_key_command(py_cui.keys.KEY_RIGHT_ARROW, self.try_load_right)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_LEFT_ARROW, self.try_load_left)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_P_LOWER, self.player_widget.player.toggle_pause)
        # self.scroll_menu.add_key_command(py_cui.keys.KEY_ENTER, self.play)
        self.scroll_menu.set_selected_color(py_cui.MAGENTA_ON_CYAN)

        self.scroll_menu.add_item_list(self.content_state_stack[0].get_current_name_list())


    def try_load_right(self):
        content = self.content_state_stack[-1].get_at(self.scroll_menu.get_selected_item_index())
        if content.content_type is WidgetContentType.SONG:
            self.player_widget.play(content)
            return
        self.content_state_stack.append(content)
        self.refresh_names(content)

    def try_load_left(self):
        content = self.content_state_stack[-1].get_at(self.scroll_menu.get_selected_item_index())
        if content.content_type is WidgetContentType.MAIN:
            return
        self.content_state_stack.pop()
        self.refresh_names(self.content_state_stack[-1])

    def refresh_names(self, content):
        self.scroll_menu.clear()
        name_list = content.get_current_name_list()
        self.scroll_menu.add_item_list(name_list)
        for _ in range(content.current_index): self.scroll_menu._scroll_down(min(3, len(name_list)-1))

# using this as a trait
class SongProvider:
    def __init__(self, data):
        self.content_type = WidgetContentType.SONGS
        self.data_list = data
        self.current_index = 0

    def get_at(self, index):
        self.current_index = index
        song = self.data_list[index]
        song.content_type = WidgetContentType.SONG
        return song

    def get_current_name_list(self):
        return [song.title for song in self.data_list]

class MainProvider(SongProvider):
    def __init__(self):
        data = [ArtistProvider(), 0, 0, 0, 0]
        super().__init__(data)
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
        super().__init__(data)
        self.content_type = WidgetContentType.ARTISTS
    
    def get_current_name_list(self):
        return [pad(artist.name) for artist in self.data_list]
    
    def get_at(self, index):
        self.current_index = index
        artist = self.data_list[index]
        songs = list(artist.songs)
        songs.sort(key=lambda x: x.title)
        return SongProvider(songs)

class WidgetContentType(enum.Enum):
    MAIN = enum.auto()

    ARTISTS = enum.auto()
    PLAYLISTS = enum.auto()
    QUEUES = enum.auto() # like playlist but remembers position and deletes itself when finished
    AUTOSEARCH_SONGS = enum.auto()

    SONGS = enum.auto()

    FILE_EXPLORER = enum.auto()

    SONG = enum.auto()