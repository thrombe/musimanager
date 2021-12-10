
import logging
import enum

import platform
LUUNIX = platform.system() == "Linux"
if LUUNIX: import ueberzug.lib.v0 as ueberzug

import io
import os
from PIL import Image
import py_cui
import pydub
import pydub.playback
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame.mixer as mixer

from wcwidth import wcwidth, wcswidth

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


        # TODO: try these
            # picui.set_border_color()
            # picui.set_focus_border_color()
        # TODO: set quit, pause, seek, ... as global shortcuts (i.e, set them on every widget + master)
        # TODO: select browser widget by default

        # TODO: add a queue widget + shortcut to disable it
        # TODO: shortcut to send songs to queue
        # TODO: shortcuts to quickly navigate to other widgets (without escape button)
        
        self.player_widget = PlayerWidget(self.pycui.add_scroll_menu('Player', 0, 1, row_span=1, column_span=1, padx = 1, pady = 0))
        self.browser_widget = BrowserWidget(
            self.pycui.add_scroll_menu('Browser',  0, 0, row_span=1, column_span=1, padx = 1, pady = 0),
            self.player_widget,
            )

        self.player_widget.setup()
        self.browser_widget.setup()

    def start(self):
        if getattr(self, "pycui", None) is None: self.setup()

        if LUUNIX:
            with ueberzug.Canvas() as canvas:
                # TODO: crop the pic to be square so things are predictable (album art is generally square too)
                self.player_widget.image_placement = canvas.create_placement('album_art', scaler=ueberzug.ScalerOption.FIT_CONTAIN.value)
                self.player_widget.image_placement.visibility = ueberzug.Visibility.INVISIBLE
                self.pycui.start()
        else:
            self.pycui.start()

    def refresh(self):
        self.player_widget.refresh()

class Player:
    def __init__(self):
        self.is_paused = True
        
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
        if self.is_paused:
            self.playback_handle.unpause()
            self.is_paused = False
        else:
            self.playback_handle.pause()
            self.is_paused = True

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
        if LUUNIX: self.image_refresh()
        if self.player.current_song is not None: self.print_song_metadata(self.player.current_song)

    def image_refresh(self):
        # TODO: use these instead
        #   self.play_window.get_absolute_{start, stop}_pos() -> (x, y)
        #       or .get_start_position(), not sure
        #   self.play_window.get_padding() ?????
        # TODO: center the image in the y axis ????
        self.image_placement.y = self.scroll_menu._start_y + self.border_padding_y_top
        self.image_placement.width = self.scroll_menu._stop_x - self.scroll_menu._start_x - self.border_padding_x*2
        self.image_placement.height = self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom - self.lines_of_song_info - 2
        a = self.image_placement.width - 2.1*self.image_placement.height
        if round(a/2) > 2: self.image_placement.x = round(a/2) + self.scroll_menu._start_x + self.border_padding_x - 1
        else: self.image_placement.x = self.scroll_menu._start_x + self.border_padding_x

    def play(self, song):
        self.player.play(song)
        if LUUNIX: self.replace_album_art(song)
        self.print_song_metadata(song)

    def replace_album_art(self, song):
        img_path = opts.musimanager_directory + "img.jpeg"
        img = song.get_album_art_as_jpeg_bytes()
        img = Image.open(io.BytesIO(img))
        
        # crop image into a square
        x, y = img.size
        a = (x-y)/2
        if a > 0: box = (a, 0, x - a, y)
        else: box = (0, -a, x, y+a)
        img = img.crop(box)
        img.save(img_path)

        self.image_placement.path = img_path
        self.image_placement.visibility = ueberzug.Visibility.VISIBLE

    def print_song_metadata(self, song):
        self.scroll_menu.clear()
        x_blank = self.scroll_menu._stop_x - self.scroll_menu._start_x - self.border_padding_x*2
        center = lambda text: int((x_blank-len(text))/2)*" "+text
        right = lambda text: int(x_blank-int(len(text)))*" "+text
        if LUUNIX:
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

# TODO: impliment more SongProviders

class WidgetContentType(enum.Enum):
    MAIN = enum.auto()

    ARTISTS = enum.auto()
    PLAYLISTS = enum.auto()
    QUEUES = enum.auto() # like playlist but remembers position and deletes itself when finished
    AUTOSEARCH_SONGS = enum.auto()

    SONGS = enum.auto()

    FILE_EXPLORER = enum.auto()

    SONG = enum.auto()