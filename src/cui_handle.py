import py_cui
import logging

import ueberzug.lib.v0 as ueberzug
import time
from wcwidth import wcwidth, wcswidth


import tracker

# 2 width chars are counted as 1 width by len(), so causes probs
# https://github.com/jupiterbjy/CUIAudioPlayer/
def pad(string):
    zwsp = "\u200b"
    pads = 0
    for char in string: 
        if wcwidth(char)-len(char) == 1:
            pads += 1
    return string + zwsp*pads

class CUI_handle:

    def __init__(self):
        self.tracker = tracker.Tracker()
        self.tracker.load()
        
        def nene(art): return art.name
        self.artists = list(self.tracker.artists)
        self.artists.sort(key=nene)
        self.artist_names = [pad(artist.name) for artist in self.artists]
        self.curr_artist_index = 0
    
    def setup_cui(self):
        self.pycui = py_cui.PyCUI(1, 2)
        self.pycui.toggle_unicode_borders()
        self.pycui.set_title('CUI TODO List')
        # self.master.enable_logging(logging_level=logging.ERROR)
        # self.master.toggle_live_debug_mode()

        self.browse_window =  self.pycui.add_scroll_menu('In Progress',  0, 0, row_span=1, column_span=1, padx = 1, pady = 0)
        self.play_window = self.pycui.add_scroll_menu('Done', 0, 1, row_span=1, column_span=1, padx = 1, pady = 0)
        self.browse_window.add_key_command(py_cui.keys.KEY_RIGHT_ARROW, self.load_right)
        self.browse_window.add_key_command(py_cui.keys.KEY_LEFT_ARROW, self.load_left)
        self.browse_window.add_key_command(py_cui.keys.KEY_ENTER, self.play)
        self.browse_window.add_item_list(self.artist_names)
        self.browse_window.set_selected_color(py_cui.MAGENTA_ON_CYAN)

    def start(self):
        if getattr(self, "pycui", None) is None: self.setup_cui()
        
        with ueberzug.Canvas() as canvas:
            self.image_placement = canvas.create_placement('album_art', scaler=ueberzug.ScalerOption.FIT_CONTAIN.value, width=20, height=50)
            self.image_placement.visibility = ueberzug.Visibility.INVISIBLE
            self.pycui.set_refresh_timeout(0.1)
            self.pycui.set_on_draw_update_func(self.redraw)
            self.pycui.start()

    def redraw(self):
        self.image_placement.x = self.play_window._start_x+3
        self.image_placement.y = self.play_window._start_y+1

    def load_right(self):
        self.curr_artist_index = self.browse_window.get_selected_item_index()
        artist = self.artists[self.curr_artist_index]
        self.browse_window.clear()
        self.songs = [song for song in artist.songs]
        self.browse_window.add_item_list(pad(song.title) for song in self.songs)

    def load_left(self):
        self.browse_window.clear()
        self.browse_window.add_item_list(self.artist_names)
        # self.in_progress_scroll_cell.set_selected_item_index(self.curr_artist_index)
        for _ in range(self.curr_artist_index): self.browse_window._scroll_down(3)

    def play(self):
        self.play_window.clear()
        self.play_window.add_item_list(list(" "*15))
        song = self.songs[self.browse_window.get_selected_item_index()]
        self.play_window.add_item(f"title: {song.title}")
        self.play_window.add_item(f"album: {song.info.album}")
        self.play_window.add_item(f"artist: {song.artist_name}")

        image_path = '/home/issac/Pictures/Screenshot_20211122_221759.png'
        self.image_placement.x = self.play_window._start_x+3
        self.image_placement.y = self.play_window._start_y+1
        self.image_placement.path = image_path
        self.image_placement.visibility = ueberzug.Visibility.VISIBLE
            