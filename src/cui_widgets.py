
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
        song_path = song.last_known_path if song.last_known_path is not None else song.temporary_download()
        
        # TODO: any other way to get song_duration? mutagen? pydub is slow (and not needed) for flac files
        self.pydub_audio_segment = pydub.AudioSegment.from_file(song_path, song_path.split(os.path.sep)[-1].split(".")[-1])
        self.song_duration = len(self.pydub_audio_segment)*0.001 # seconds
        self.song_psuedo_start_time = time.time()
        self.is_paused_since = None
        flac_filelike = io.BytesIO()
        # with open(song_path, "rb") as f: flac_filelike = io.BytesIO(f.read())
        self.playback_handle = mixer.music

        # maybe TODO: try switching back to simpleaudio cuz converting to flac is slower than wav (about a second faster maybe)
        convert_to = "flac"
        # convert_to = "wav"
        if song_path.split(".")[-1] != convert_to: flac_filelike = self.pydub_audio_segment.export(flac_filelike, format=convert_to)
        else:
            with open(song_path, "rb") as f:
                flac_filelike.write(f.read())
        self.flac_filelike_copy = copy.deepcopy(flac_filelike)
        flac_filelike.seek(0)
        self.playback_handle.load(flac_filelike, namehint=convert_to)
        self.playback_handle.play()
        
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

class PlayerWidget:
    def __init__(self, widget):
        self.player = None
        self.image_placement = None
        self.scroll_menu = widget
        
        self.border_padding_x = 3
        self.border_padding_y_top = 1
        self.border_padding_y_bottom = 2
        self.lines_of_song_info = 4

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
        self.image_placement.width = self.x_blank()
        self.image_placement.height = self.y_blank() - self.lines_of_song_info - 0
        a = self.image_placement.width - 2.1*self.image_placement.height
        if round(a/2) > 2: self.image_placement.x = round(a/2) + self.scroll_menu._start_x + self.border_padding_x - 1
        else: self.image_placement.x = self.scroll_menu._start_x + self.border_padding_x

    def ascii_image_refresh(self):
        if self.player.current_song is None: return
        x_blank = self.x_blank()
        center = lambda text: int((x_blank-len(text))/2)*" "+text
        img = Image.open(opts.temp_dir+"img.jpeg")
        columns = min(
            x_blank,
            round(2.2 * (self.y_blank() - self.lines_of_song_info + 1)),
        )
        textimg = ascii_magic.from_image(img, mode=ascii_magic.Modes.ASCII, columns=columns)
        for line in textimg.splitlines():
            self.scroll_menu.add_item(center(line))

    def play(self, song):
        self.player.play(song)
        self.replace_album_art(song)
        self.print_song_metadata(song)

    def play_next(self):
        if self.player.current_queue is None: return False
        self.set_current_queue_index_to_playing_song()
        next = self.player.current_queue.next()
        if next is not None:
            self.play(next)
            return True
        else:
            self.player.current_queue = None
            return False

    def play_prev(self):
        if self.player.current_queue is None: return False
        self.set_current_queue_index_to_playing_song()
        prev = self.player.current_queue.previous()
        if prev is not None:
            self.play(prev)
            return True
        else:
            return False

    # to reset the index to whatever is playing
    def set_current_queue_index_to_playing_song(self):
        i = None
        for j, s in enumerate(self.player.current_queue.data_list):
            if s.key == self.player.current_song.key:
                i = j
                break
        if i is None: raise ValueError("song not found in queue")
        self.player.current_queue.current_index = i

    def set_queue(self, queue):
        self.player.current_queue = queue

    def replace_album_art(self, song):
        img = song.get_cover_image_from_metadata() if song.last_known_path is not None else song.download_cover_image()
        if img is None:
            img = Image.open(opts.default_album_art)
        else:
            img = helpers.chop_image_into_square(img)
            img = Image.open(io.BytesIO(img))
            
        img_path = opts.temp_dir + "img.jpeg"
        img.save(img_path)

        if not opts.ASCII_ART:
            self.image_placement.path = img_path
            self.image_placement.visibility = ueberzug.Visibility.VISIBLE

    def print_song_metadata(self, song):
        x_blank = self.x_blank()
        # center = lambda text: int((x_blank-len(text))/2)*" "+text
        # right = lambda text: int(x_blank-int(len(text)))*" "+text
        center = lambda text: py_cui.fit_text(x_blank, helpers.pad_zwsp(text), center=True)
        if opts.LUUNIX and not opts.ASCII_ART:
            blank = min(
                self.y_blank() - self.lines_of_song_info,
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

    def x_blank(self): return self.scroll_menu._stop_x - self.scroll_menu._start_x - self.border_padding_x*2
    def y_blank(self): return self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom

class BrowserWidget:
    def __init__(self, widget, player_widget):
        self.content_state_stack = [cui_content_providers.MainProvider()]
        self.scroll_menu = widget
        self.player_widget = player_widget # needs to be able to change songs at any time
        self.current_queue_view = False

    def setup(self):
        self.scroll_menu.add_key_command(py_cui.keys.KEY_Q_LOWER, cui_handle.pycui.stop)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_RIGHT_ARROW, self.try_load_right)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_LEFT_ARROW, self.try_load_left)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_P_LOWER, self.player_widget.player.toggle_pause)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_O_LOWER, self.add_song_to_playlist)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_I_LOWER, self.add_song_to_queue)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_J_LOWER, self.player_widget.player.seek_10_secs_behind)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_K_LOWER, self.player_widget.player.seek_10_secs_forward)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_H_LOWER, self.play_prev)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_L_LOWER, self.play_next)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_M_LOWER, self.view_down)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_N_LOWER, self.view_up)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_V_LOWER, self.move_item_down)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_B_LOWER, self.move_item_up)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_U_LOWER, self.toggle_queue_view)
        self.scroll_menu.add_key_command(py_cui.keys.KEY_S_LOWER, self.search)
        self.scroll_menu.set_selected_color(py_cui.MAGENTA_ON_CYAN)

        self.scroll_menu.add_item_list(self.content_state_stack[0].get_current_name_list())

    def refresh(self):
        self.player_widget.refresh()
        content_provider = self.content_state_stack[-1]
        content_provider.current_index = self.scroll_menu.get_selected_item_index()
        content_provider.current_scroll_top_index = self.scroll_menu._top_view
        self.refresh_names(content_provider)
        
        # if current song ended, play next
        if self.player_widget.player.song_psuedo_start_time is None: return
        if self.player_widget.player.is_paused_since is not None: return
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
        y_blank = self.player_widget.y_blank()
        content_provider.move_item_down(self.scroll_menu.get_selected_item_index(), y_blank, self.scroll_menu._top_view)
        self.refresh_names(content_provider)

    def move_item_up(self):
        content_provider = self.content_state_stack[-1]
        y_blank = self.player_widget.y_blank()
        content_provider.move_item_up(self.scroll_menu.get_selected_item_index(), y_blank, self.scroll_menu._top_view)
        self.refresh_names(content_provider)

    def play_next(self):
        if self.player_widget.play_next():
            self.refresh_names(self.content_state_stack[-1])

    def play_prev(self):
        if self.player_widget.play_prev():
            self.refresh_names(self.content_state_stack[-1])

    def try_load_right(self):
        if self.current_queue_view:
            self.player_widget.play(self.player_widget.player.current_queue.get_at(self.scroll_menu.get_selected_item_index()))
            return

        content_provider = self.content_state_stack[-1]
        content = content_provider.get_at(self.scroll_menu.get_selected_item_index())
        if content is None: return
        if content_provider.content_type is cui_content_providers.WidgetContentType.SONGS:
            self.player_widget.play(content)
            self.change_queue(copy.deepcopy(content_provider))
            return
        elif content.content_type is cui_content_providers.WidgetContentType.SEARCHER:
            self.content_state_stack.append(content)
            self.search()
            return
        elif content_provider.content_type is cui_content_providers.WidgetContentType.FILE_EXPLORER:
            if content.content_type is cui_content_providers.WidgetContentType.SONGS:
                song = content.get_at(content.current_index)
                self.player_widget.play(song)
                self.change_queue(content)
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

    def search(self):
        content_provider = self.content_state_stack[-1]
        search_box_title = content_provider.search(None, get_search_box_title=True)
        if search_box_title is None: return
        def helper_func(search_term):
            content_provider.search(search_term)
            self.refresh_names(content_provider)
        cui_handle.pycui.show_text_box_popup(search_box_title, helper_func)

    def refresh_names(self, content):
        self.scroll_menu.clear()
        x_blank = self.player_widget.x_blank()
        frmat = lambda text: py_cui.fit_text(x_blank-1, helpers.pad_zwsp(text)).rstrip(" ")
        if self.current_queue_view: self.scroll_menu.set_title(frmat(f"queue: {content.name}"))
        else: self.scroll_menu.set_title(frmat(content.name))
        name_list = content.get_current_name_list()
        if len(name_list) != 0 and type(name_list[0]) == type(("", "")):
            self.scroll_menu.add_item_list([
                helpers.text_on_both_sides(name[0], name[1], x_blank) for name in name_list
            ])
        else:
            self.scroll_menu.add_item_list([ # yes, pad is needed before and after fit_text (annoying 2 width chars)
                helpers.pad_zwsp(py_cui.fit_text(x_blank, name)) for name in name_list
                ])

        y_blank = self.player_widget.y_blank()

        # making sure some values arent hidden when theres empty space
        if len(name_list) <= y_blank:
            content.current_scroll_top_index = 0
        elif len(name_list)-content.current_scroll_top_index-1 < y_blank:
            content.current_scroll_top_index = len(name_list)-y_blank-1
        
        # making sure selected item is visible
        if content.current_index < content.current_scroll_top_index:
            content.current_scroll_top_index = content.current_index
        elif content.current_index > content.current_scroll_top_index + y_blank - 1:
            content.current_scroll_top_index = content.current_index - y_blank
        
        self.scroll_menu.set_selected_item_index(content.current_index)
        self.scroll_menu._top_view = content.current_scroll_top_index

    def change_queue(self, queue):
        queue_provider = self.content_state_stack[0].data_list[3]
        queue_provider.add_queue(queue)
        self.player_widget.set_queue(queue)

    def toggle_queue_view(self):
        if self.current_queue_view:
            self.current_queue_view = False
            self.content_state_stack.pop()
            self.refresh_names(self.content_state_stack[-1])
        else:
            if self.player_widget.player.current_queue is None: return
            self.current_queue_view = True
            self.content_state_stack.append(self.player_widget.player.current_queue)
            self.refresh_names(self.content_state_stack[-1])

    def add_song_to_playlist(self):
        self.add_song_to_something_using_popup(2, "playlist")

    def add_song_to_queue(self):
        self.add_song_to_something_using_popup(3, "queue")

    def add_song_to_something_using_popup(self, provider_index_in_main, add_new_what):
        destination_content_provider = self.content_state_stack[0].data_list[provider_index_in_main]
        content_providers = [content_provider for content_provider in destination_content_provider.data_list]
        source_content_provider = self.content_state_stack[-1]
        if source_content_provider.content_type is not cui_content_providers.WidgetContentType.SONGS: return
        song = source_content_provider.get_at(self.scroll_menu.get_selected_item_index())
        
        helper_func2 = lambda p: destination_content_provider.add_new_song_provider([song], p.rstrip(" "))
        def helper_func1(x):
            i = int(x.split("│")[0]) - 1
            if i == -1:
                cui_handle.pycui.show_text_box_popup("add new", helper_func2)
                return
            if not content_providers[i].remove_song(song):
                content_providers[i].add_song(song)
        
        cui_handle.pycui.show_menu_popup(f"choose/create {add_new_what}", [], helper_func1)
        cui_handle.pycui._popup.set_selected_color(py_cui.MAGENTA_ON_CYAN)
        
        x_blank = cui_handle.pycui._popup._stop_x - cui_handle.pycui._popup._start_x - self.player_widget.border_padding_x*2
        with_a_tick = lambda x, y: (x, "✔"*y)
        options = ["0│ add new"]
        for i, p in enumerate(content_providers):
            a = with_a_tick(f"{i+1}│ {p.name}", p.contains_song(song))
            a = helpers.text_on_both_sides(a[0], a[1], x_blank)
            options.append(a)
        cui_handle.pycui._popup.add_item_list(options)
