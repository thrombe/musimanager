
import io
import os
import pydub
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame.mixer as mixer
from PIL import Image
import py_cui
import time
import copy

import opts
import cui_content_providers
import cui_handle
import helpers

if opts.ASCII_ART: import ascii_magic
if opts.LUUNIX: import ueberzug.lib.v0 as ueberzug

class Player:
    def __init__(self):
        self.is_paused_since = None
        self.song_duration = None
        self.song_psuedo_start_time = None
        self.song_progress_bar = 0
        
        mixer.init()
        
        self.current_song = None # musimanager song
        self.pydub_audio_segment = None
        self.flac_filelike_copy = None
        self.playback_handle = None
        self.current_queue = None

    def play(self, song):
        if self.playback_handle is not None: self.playback_handle.stop()
        # len(song) is ~~ (duration of song in seconds (milliseconds in decimal))*1000
        self.current_song = song
        song_path = song.last_known_path # TODO: handle path properly
        self.pydub_audio_segment = pydub.AudioSegment.from_file(song_path, song_path.split(os.path.sep)[-1].split(".")[-1])
        self.song_duration = len(self.pydub_audio_segment)*0.001 # seconds
        self.song_psuedo_start_time = time.time()
        self.is_paused_since = None
        flac_filelike = io.BytesIO()
        self.playback_handle = mixer.music

        # maybe TODO: try switching back to simpleaudio cuz converting to flac is slower than wav (about a second faster maybe)
        convert_to = "flac"
        # convert_to = "wav"
        flac_filelike = self.pydub_audio_segment.export(flac_filelike, format=convert_to)
        self.flac_filelike_copy = copy.deepcopy(flac_filelike)
        flac_filelike.seek(0)
        self.playback_handle.load(flac_filelike, namehint=convert_to)
        self.playback_handle.play()
        
    # def stop(self):
    #     self.playback_handle.stop()
    #     self.is_paused_since = time.time()

    def toggle_pause(self):
        if self.is_paused_since is not None:
            self.playback_handle.unpause()
            self.song_psuedo_start_time += time.time() - self.is_paused_since
            self.is_paused_since = None
        else:
            self.playback_handle.pause()
            self.is_paused_since = time.time()

    # TODO: simplify this bs with self.playback_handle.get_pos()
    def try_seek(self, secs):
        tme = time.time() - self.song_psuedo_start_time
        if tme > self.song_duration:
            flac_filelike = copy.deepcopy(self.flac_filelike_copy)
            flac_filelike.seek(0)
            self.playback_handle.load(flac_filelike, namehint="flac")
            self.playback_handle.play()
        
        self.song_psuedo_start_time -= secs
        tme = time.time() - self.song_psuedo_start_time
        if tme > self.song_duration:
            tme = self.song_duration-0.1
            self.song_psuedo_start_time = time.time()-self.song_duration - 0.1
        elif tme < 0:
            tme = 0.1
            self.song_psuedo_start_time = time.time() + 0.1
        self.playback_handle.set_pos(tme)

    def seek_10_secs_forward(self):
        self.try_seek(10)

    def seek_10_secs_behind(self):
        self.try_seek(-10)

    def play_next(self):
        if self.current_queue is None: return False
        next = self.current_queue.next()
        if next is not None:
            self.play(next)
            return True
        else:
            self.current_queue = None
            return False

    def play_prev(self):
        if self.current_queue is None: return False
        prev = self.current_queue.previous()
        if prev is not None:
            self.play(prev)
            return True
        else:
            return False

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

    def setup(self):
        self.player = Player()

    def refresh(self):
        self.scroll_menu.clear()
        if opts.ASCII_ART: self.ascii_image_refresh()
        elif opts.LUUNIX: self.image_refresh()
        if self.player.current_song is not None: self.print_song_metadata(self.player.current_song)

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
        img = song.get_cover_image_from_metadata()
        if img is None:
            img = Image.open(opts.default_album_art)
        else:
            img = helpers.chop_image_into_square(img)
            img = Image.open(io.BytesIO(img))
            
        img_path = opts.musimanager_directory + "img.jpeg"
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
        # "█", "▄", "▀", "■", "▓", "│", "▌", "▐", "─", 

class BrowserWidget:
    def __init__(self, widget, player_widget):
        self.content_state_stack = [cui_content_providers.MainProvider()]
        self.scroll_menu = widget
        self.player_widget = player_widget # needs to be able to change songs at any time
        self.current_queue_view = False

    # TODO: provide shortcut to search (sort using kinda_similar)

    def setup(self):
        self.scroll_menu.add_key_command(py_cui.keys.KEY_Q_LOWER, cui_handle.pycui.stop)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_RIGHT_ARROW, self.try_load_right)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_LEFT_ARROW, self.try_load_left)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_P_LOWER, self.player_widget.player.toggle_pause)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_O_LOWER, self.try_add_song_to_playlist)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_J_LOWER, self.player_widget.player.seek_10_secs_behind)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_K_LOWER, self.player_widget.player.seek_10_secs_forward)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_H_LOWER, self.play_prev)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_L_LOWER, self.play_next)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_M_LOWER, self.view_down)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_N_LOWER, self.view_up)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_V_LOWER, self.move_item_down)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_B_LOWER, self.move_item_up)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_U_LOWER, self.toggle_queue_view)
        self.scroll_menu.set_selected_color(py_cui.MAGENTA_ON_CYAN)

        self.scroll_menu.add_item_list(self.content_state_stack[0].get_current_name_list())

    def refresh(self):
        self.player_widget.refresh()
        
        # if current song ended, play next
        if self.player_widget.player.song_psuedo_start_time is None: return
        tme = time.time() - self.player_widget.player.song_psuedo_start_time
        if tme > self.player_widget.player.song_duration: # playback_handle.get_pos() >= song_duration
            self.play_next()

    def view_down(self):
        content_provider = self.content_state_stack[-1]
        length = len(content_provider.data_list)
        content_provider.current_scroll_top_index += 1
        if content_provider.current_scroll_top_index >= length:
            content_provider.current_scroll_top_index = length-1
        self.refresh_names(content_provider)

    def view_up(self):
        content_provider = self.content_state_stack[-1]
        content_provider.current_scroll_top_index -= 1
        if content_provider.current_scroll_top_index < 0:
            content_provider.current_scroll_top_index = 0
        self.refresh_names(content_provider)

    def move_item_down(self):
        content_provider = self.content_state_stack[-1]
        y_blank = self.scroll_menu._stop_y - self.scroll_menu._start_y - self.player_widget.border_padding_y_top - self.player_widget.border_padding_y_bottom
        content_provider.move_item_down(self.scroll_menu.get_selected_item_index(), y_blank, self.scroll_menu._top_view)
        self.refresh_names(content_provider)

    def move_item_up(self):
        content_provider = self.content_state_stack[-1]
        y_blank = self.scroll_menu._stop_y - self.scroll_menu._start_y - self.player_widget.border_padding_y_top - self.player_widget.border_padding_y_bottom
        content_provider.move_item_up(self.scroll_menu.get_selected_item_index(), y_blank, self.scroll_menu._top_view)
        self.refresh_names(content_provider)

    def play_next(self):
        if self.player_widget.player.play_next():
            self.refresh_names(self.content_state_stack[-1])

    def play_prev(self):
        if self.player_widget.player.play_prev():
            self.refresh_names(self.content_state_stack[-1])

    def try_load_right(self):
        if self.current_queue_view:
            self.player_widget.play(self.player_widget.player.current_queue.get_at(self.scroll_menu.get_selected_item_index(), self.scroll_menu._top_view))
            return

        content_provider = self.content_state_stack[-1]
        content = content_provider.get_at(self.scroll_menu.get_selected_item_index(), self.scroll_menu._top_view)
        if content is None: return
        if content_provider.content_type is cui_content_providers.WidgetContentType.SONGS:
            self.player_widget.play(content)
            potential_queue_provider = self.content_state_stack[-2]
            if potential_queue_provider.content_type is cui_content_providers.WidgetContentType.QUEUES:
                potential_queue_provider.yeet_selected_queue()
            self.change_queue(copy.deepcopy(self.content_state_stack[-1]))
            return
        self.content_state_stack.append(content)
        self.refresh_names(content)

    def try_load_left(self):
        if self.current_queue_view: return

        content = self.content_state_stack[-1]
        if content.content_type is cui_content_providers.WidgetContentType.MAIN:
            return
        if self.content_state_stack[-2].content_type is not cui_content_providers.WidgetContentType.QUEUES:
            content.reset_indices()
        self.content_state_stack.pop()
        self.refresh_names(self.content_state_stack[-1])

    def refresh_names(self, content):
        self.scroll_menu.clear()
        name_list = content.get_current_name_list()
        x_blank = self.scroll_menu._stop_x - self.scroll_menu._start_x - self.player_widget.border_padding_x*2
        self.scroll_menu.add_item_list([ # yes, pad is needed before and after fit_text (annoying 2 width chars)
            helpers.pad_zwsp(py_cui.fit_text(x_blank, name)) for name in name_list
            ])

        self.scroll_menu.set_selected_item_index(content.current_index)
        self.scroll_menu._top_view = content.current_scroll_top_index

    def change_queue(self, queue):
        current_queue = self.player_widget.player.current_queue
        if current_queue is not None:
            queue_provider = self.content_state_stack[0].data_list[3]
            queue_provider.add_queue(current_queue)
        self.player_widget.set_queue(queue)

    def toggle_queue_view(self):
        if self.current_queue_view:
            self.current_queue_view = False
            self.content_state_stack.pop()
            self.scroll_menu.set_title("Browser")
            self.refresh_names(self.content_state_stack[-1])
        else:
            if self.player_widget.player.current_queue is None: return
            content_provider = self.content_state_stack[-1]
            content_provider.current_index = self.scroll_menu.get_selected_item_index()
            content_provider.current_scroll_top_index = self.scroll_menu._top_view
            self.current_queue_view = True
            self.content_state_stack.append(self.player_widget.player.current_queue)
            self.scroll_menu.set_title(f"current queue: {self.content_state_stack[-1].name}")
            self.refresh_names(self.content_state_stack[-1])

    def try_add_song_to_playlist(self):
        main_provider = self.content_state_stack[0]
        playlist_provider = main_provider.data_list[2]
        content_provider = self.content_state_stack[-1]
        song = content_provider.get_at(self.scroll_menu.get_selected_item_index(), self.scroll_menu._top_view)
        if content_provider.content_type is not cui_content_providers.WidgetContentType.SONGS: return
        # TODO: allow to remove the song from the playlists that already have it
            # how? the popups dont allow shortcuts
                # maybe another button to press to try remove?
                # only show the ones with tick
        
        helper_func2 = lambda p: playlist_provider.add_playlist([song], p.rstrip(" "))
        def helper_func1(x):
            i = int(x.split("│")[0]) - 1
            if i == -1:
                cui_handle.pycui.show_text_box_popup("add new", helper_func2)
                return
            playlist_provider.data_list[i].add_song(song)
        
        cui_handle.pycui.show_menu_popup("choose/create playlist", [], helper_func1)
        cui_handle.pycui._popup.set_selected_color(py_cui.MAGENTA_ON_CYAN)
        
        x_blank = cui_handle.pycui._popup._stop_x - cui_handle.pycui._popup._start_x - self.player_widget.border_padding_x*2
        with_a_tick = lambda x, y: (x, "✔"*y)
        options = ["0│ add new"]
        for i, pl in enumerate(playlist_provider.data_list):
            a = with_a_tick(f"{i+1}│ "+pl.name, pl.contains_song(song))
            a = text_on_both_sides(a[0], a[1], x_blank)
            options.append(a)
        cui_handle.pycui._popup.add_item_list(options)
        
def text_on_both_sides(x, y, x_blank):
    if len(x)+len(y) > x_blank-2:
        ex = len(x) > x_blank/2
        yae = len(y) > x_blank/2
        if ex and not yae:
            x = py_cui.fit_text(x_blank-2-len(y), x)
        elif not ex and yae:
            y = py_cui.fit_text(x_blank-2-len(x), y)
        elif ex and yae:
            x_blanke = (x_blank-2)/2
            x, y = py_cui.fit_text(x_blanke, x), py_cui.fit_text(x_blanke, y)
    return x + (x_blank - len(x) - len(y))*" " + y