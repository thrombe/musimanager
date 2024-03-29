
import io
import os
from PIL import Image
import py_cui
import copy
import threading

import opts
import cui_content_providers
import cui_handle
import helpers

# musiplayer_setup.py puts a musiplayer.so file (compiled from rust) in current folder that gets imported here
import musiplayer

if opts.enable_global_shortcuts: import pynput
if opts.ASCII_ART: import ascii_magic
if opts.LUUNIX_X86_64: import ueberzug.lib.v0 as ueberzug

class Player:
    def __init__(self):
        self.current_song = None # musimanager song
        self.current_queue = None
        self.playback_handle = musiplayer.Player()

    def play(self, song):
        self.current_song = song
        song_path = f"file://{song.last_known_path}" if song.last_known_path is not None and os.path.exists(song.last_known_path) else song.get_uri()
        
        self.playback_handle.play(song_path)

    def toggle_pause(self):
        self.playback_handle.toggle_pause()

    def try_seek(self, secs):
        self.playback_handle.seek(secs)

    def seek_n_secs_forward(self):
        self.try_seek(opts.seek_interval)

    def seek_n_secs_behind(self):
        self.try_seek(-opts.seek_interval)

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
        elif opts.LUUNIX_X86_64: self.image_refresh()
        if self.player.current_song is not None:
            self.print_song_metadata(self.player.current_song)

    def image_refresh(self):
        # disable ueberzug album art while popups are up (as the image sits on top of the ui)
        if not opts.LUUNIX_X86_64 or opts.ASCII_ART: return
        if self.image_placement.path is None: return
        if cui_handle.pycui._popup is not None:
            if self.image_placement.visibility == ueberzug.Visibility.VISIBLE:
                self.image_placement.visibility = ueberzug.Visibility.INVISIBLE
            return

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

        if opts.hide_ueberzug_album_art and self.image_placement.visibility == ueberzug.Visibility.VISIBLE:
            self.image_placement.visibility = ueberzug.Visibility.INVISIBLE
        elif (not opts.hide_ueberzug_album_art) and self.image_placement.visibility == ueberzug.Visibility.INVISIBLE:
            self.image_placement.visibility = ueberzug.Visibility.VISIBLE
        elif opts.hide_ueberzug_album_art and self.image_placement.visibility == ueberzug.Visibility.INVISIBLE:
            return

    def ascii_image_refresh(self):
        if self.player.current_song is None: return
        img_path = opts.temp_dir + "img.png"
        if not os.path.exists(img_path): return
        x_blank = self.x_blank()
        center = lambda text: int((x_blank-len(text))/2)*" "+text
        img = Image.open(img_path)
        columns = min(
            x_blank,
            round(2.2 * (self.y_blank() - self.lines_of_song_info + 1)),
        )
        textimg = ascii_magic.from_image(img, mode=ascii_magic.Modes.ASCII, columns=columns)
        for line in textimg.splitlines():
            self.scroll_menu.add_item(center(line))

    def play(self, song):
        self.player.playback_handle.stop() # to prevent the auto_next from triggering multiple times
        def execute():
            # cui_handle.pycui.show_loading_icon_popup("loading song", "song loading")
            self.player.play(song)
            self.replace_album_art(song)
            self.print_song_metadata(song)
            # cui_handle.pycui.stop_loading_popup()
        # execute()
        threading.Thread(target=execute, args=()).start()

    def play_next(self):
        if self.player.current_queue is None: return False
        if self.set_current_queue_index_to_playing_song() is None:
            if self.player.current_queue.current_index >= 0:
                self.player.current_queue.current_index -= 1
                self.player.current_queue.current_scroll_top_index -= 1
        next = self.player.current_queue.next()
        if next is not None:
            self.play(next)
            return True
        else:
            return False

    def play_prev(self):
        if self.player.current_queue is None: return False
        if self.set_current_queue_index_to_playing_song() is None:
            if self.player.current_queue.current_index == len(self.player.current_queue.data_list):
                self.player.current_queue.current_index += 1 # so that if current element is deleted, correct prev song plays
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
            if s == self.player.current_song:
                i = j
                break
        if i is not None: self.player.current_queue.current_index = i
        return i

    def set_queue(self, queue):
        if self.player.current_queue is not None and self.player.current_song is not None:
            self.set_current_queue_index_to_playing_song()
        self.player.current_queue = queue

    def replace_album_art(self, song):
        img = song.get_cover_image_from_metadata() if song.last_known_path is not None and os.path.exists(song.last_known_path) else song.download_cover_image()
        if img is None:
            img = Image.open(opts.default_album_art)
        else:
            img = helpers.chop_image_into_square(img)
            img = Image.open(io.BytesIO(img))
            
        img_path = opts.temp_dir + "img.png"
        img.save(img_path)

        if not opts.ASCII_ART and self.image_placement is not None:
            self.image_placement.path = img_path

    def print_song_metadata(self, song):
        x_blank = self.x_blank()
        # center = lambda text: int((x_blank-len(text))/2)*" "+text
        # right = lambda text: int(x_blank-int(len(text)))*" "+text
        center = lambda text: helpers.fit_text(x_blank, helpers.pad_zwsp(text), center=True)
        if opts.LUUNIX_X86_64 and not opts.ASCII_ART:
            blank = min(
                self.y_blank() - self.lines_of_song_info,
                int(1/2.1 * (x_blank)),
            ) + 1
            self.scroll_menu.add_item_list(list(" "*blank))
        # TODO: format this in a nicer way, perhaps bold and stuff
        self.scroll_menu.add_item(center(f"title: {song.title}"))
        self.scroll_menu.add_item(center(f"album: {song.info.album}"))
        self.scroll_menu.add_item(center(f"artist: {song.artist_name}"))
        self.scroll_menu.add_item(f"{'█' * round(x_blank * self.player.playback_handle.progress())}")
        # "█", "▄", "▀", "■", "▓", "│", "▌", "▐", "─", 

        if opts.debug_prints:
            self.scroll_menu.add_item(center(f"position: {self.player.playback_handle.position()}"))
            self.scroll_menu.add_item(center(f"duration: {self.player.playback_handle.duration()}"))
            self.scroll_menu.add_item(center(f"progress: {self.player.playback_handle.progress()}"))
            self.scroll_menu.add_item(center(f"is_finished: {self.player.playback_handle.is_finished()}"))
            # self.scroll_menu.add_item(center(f"uri: {self.player.current_song.get_uri()}"))

    def x_blank(self): return self.scroll_menu._stop_x - self.scroll_menu._start_x - self.border_padding_x*2
    def y_blank(self): return self.scroll_menu._stop_y - self.scroll_menu._start_y - self.border_padding_y_top - self.border_padding_y_bottom

class BrowserWidget:
    def __init__(self, widget, player_widget: PlayerWidget):
        self.content_state_stack = [cui_content_providers.MainProvider.new()]
        self.scroll_menu = widget
        self.player_widget = player_widget # needs to be able to change songs at any time
        self.current_queue_view = False
        self.command_queue = []
        self.commands = []

    def setup(self):
        self.commands = [
            (py_cui.keys.KEY_Q_LOWER, self.save_quit),
            (py_cui.keys.KEY_Q_UPPER, self.quit),
            (py_cui.keys.KEY_RIGHT_ARROW, self.try_load_right),
            (py_cui.keys.KEY_LEFT_ARROW, self.try_load_left),
            (py_cui.keys.KEY_P_LOWER, self.player_widget.player.toggle_pause),
            (py_cui.keys.KEY_I_LOWER, self.try_move_cursor_to_current_song),
            (py_cui.keys.KEY_J_LOWER, self.player_widget.player.seek_n_secs_behind),
            (py_cui.keys.KEY_K_LOWER, self.player_widget.player.seek_n_secs_forward),
            (py_cui.keys.KEY_H_LOWER, self.play_prev),
            (py_cui.keys.KEY_L_LOWER, self.play_next),
            (py_cui.keys.KEY_M_LOWER, self.view_down),
            (py_cui.keys.KEY_N_LOWER, self.view_up),
            (py_cui.keys.KEY_V_LOWER, self.move_item_down),
            (py_cui.keys.KEY_B_LOWER, self.move_item_up),
            (py_cui.keys.KEY_U_LOWER, self.toggle_queue_view),
            (py_cui.keys.KEY_S_LOWER, self.search),
            (py_cui.keys.KEY_G_LOWER, self.menu_for_selected),
            (py_cui.keys.KEY_G_UPPER, self.global_menu),
            (py_cui.keys.KEY_F_LOWER, self.filter),
            (py_cui.keys.KEY_F_UPPER, self.shuffle_if_current_queue),
        ]
        for k, c in self.commands:
            # default valued arguments capture the value instead of the refrence (lambda i=k: some(i))
            self.scroll_menu.add_key_command(k, lambda j=c: self.queue_command(j))
            # self.scroll_menu.add_key_command(k, c)
        self.scroll_menu.set_selected_color(py_cui.MAGENTA_ON_CYAN)
        self.scroll_menu.add_item_list(self.content_state_stack[0].get_current_name_list())
        threading.Thread(target=self.content_state_stack[0].load, args=()).start()

        if opts.enable_global_shortcuts:
            pynput.keyboard.GlobalHotKeys({
                opts.pause_global_shortcut: lambda: self.queue_command(self.player_widget.player.toggle_pause),
            }).start()

    def queue_command(self, cmd): # TODO: no need??
        # self.command_queue.append(cmd)

        cmd()
        if any([cmd.__name__ == f.__name__ for f in [self.global_menu, self.filter, self.menu_for_selected, self.search, self.play_next, self.play_prev]]):
            cui_handle.pycui._on_draw_update_func()

    def clear_commands_from_queue(self, cmds):
        i = 0
        while True:
            if len(self.command_queue) == 0 or len(self.command_queue) <= i: break
            if self.command_queue[i] in cmds:
                self.command_queue.pop(i)
            else:
                i += 1

    def save_quit(self):
        self.save()
        self.quit()

    def quit(self):
        self.player_widget.player.playback_handle.stop()
        cui_handle.pycui.stop()

    def save(self):
        if not opts.save_on_exit: return

        if self.player_widget.player.current_song is not None and self.player_widget.player.current_queue is not None:
            self.player_widget.set_current_queue_index_to_playing_song()
        
        mp = self.content_state_stack[0]

        # do not save the filtered/custom sorted data
        mp.artist_provider.try_undo_filter()
        for i in range(len(mp.artist_provider.data_list)):
            mp.artist_provider.get_at(i).try_undo_filter()

        mp.playlist_provider.try_undo_filter()
        for p in mp.playlist_provider.data_list:
            p.try_undo_filter()

        mp.queue_provider.try_undo_filter()
        for q in mp.queue_provider.data_list:
            q.try_undo_filter()
        
        mp.tracker.save()

    def refresh(self):
        self.content_state_stack[0].refresh()
        self.player_widget.refresh()
        content_provider = self.content_state_stack[-1]
        content_provider.current_index = self.scroll_menu.get_selected_item_index()
        content_provider.current_scroll_top_index = self.scroll_menu._top_view
        self.refresh_names(content_provider)

        self.auto_next()

        while len(self.command_queue) > 0:
            self.command_queue.pop(0)()
        
    def auto_next(self):
        # if current song ended, play next
        if self.player_widget.player.playback_handle.is_finished():
            self.clear_commands_from_queue([self.player_widget.player.seek_n_secs_forward])
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
        content_provider = self.content_state_stack[-1]
        content = content_provider.get_at(self.scroll_menu.get_selected_item_index())
        if content is None: return
        if content_provider.content_type is cui_content_providers.WidgetContentType.SONGS:
            # if content_provider is a queue, no need to copy the provider
            if self.current_queue_view or self.content_state_stack[-2].content_type == cui_content_providers.WidgetContentType.QUEUES:
                content_provider_maybe_copy = content_provider
            else:
                content_provider_maybe_copy = copy.deepcopy(content_provider)
                content_provider_maybe_copy.data_list = [s for s in content_provider.data_list] # making sure songs are not copied so that their info is set in playlist when played
            self.change_queue(content_provider_maybe_copy)
            self.player_widget.play(content_provider_maybe_copy.get_at(self.scroll_menu.get_selected_item_index())) # getting it again so playing song is the same as the one in song_provider
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
        if self.current_queue_view:
            self.toggle_queue_view()
            return

        content = self.content_state_stack[-1]
        if len(self.content_state_stack) == 1:
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
        frmat = lambda text: helpers.fit_text(x_blank-1, helpers.pad_zwsp(text)).rstrip(" ")
        if self.current_queue_view: self.scroll_menu.set_title(frmat(f"queue: {content.name}"))
        else: self.scroll_menu.set_title(frmat(content.name))
        name_list = content.get_current_name_list()
        if len(name_list) != 0 and type(name_list[0]) == type(("", "")):
            self.scroll_menu.add_item_list([
                helpers.text_on_both_sides(name[0], name[1], x_blank) for name in name_list
            ])
        else:
            self.scroll_menu.add_item_list([ # yes, pad is needed before and after fit_text (annoying 2 width chars)
                helpers.pad_zwsp(helpers.fit_text(x_blank, name)) for name in name_list
                ])

        self.player_widget.scroll_menu.set_title(f"{content.current_index+1}/{len(name_list)}")

        y_blank = self.player_widget.y_blank()

        # making sure that nothing is not selected
        if content.current_index >= len(content.data_list):
            content.current_index = len(content.data_list)-1

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
        queue_provider = self.content_state_stack[0].queue_provider
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

    def menu_for_selected(self):
        self.content_state_stack[-1].menu_for_selected(self.content_state_stack)
    
    def filter(self):
        def filter_func(filter_term):
            self.content_state_stack[-1].filter(filter_term)
            self.content_state_stack[-1].reset_indices()
            self.refresh_names(self.content_state_stack[-1])
        if len(self.content_state_stack[-1].unfiltered_data) != 0:
            filter_func(None)
            return
        cui_handle.pycui.show_text_box_popup("filter", filter_func)
    
    def shuffle_if_current_queue(self):
        if self.current_queue_view:
            self.player_widget.player.current_queue.shuffle()
            self.content_state_stack[-1].reset_indices()
            self.refresh_names(self.content_state_stack[-1])

    def try_move_cursor_to_current_song(self):
        if self.content_state_stack[-1].content_type != cui_content_providers.WidgetContentType.SONGS: return
        for i, s in enumerate(self.content_state_stack[-1].data_list):
            if s.title == self.player_widget.player.current_song.title:
                self.content_state_stack[-1].current_index = i
                self.refresh_names(self.content_state_stack[-1])
                return

    def global_menu(self):
        options = opts.opts["random_options"].keys()
        def toggle(x):
            exec("opts.%s = not opts.%s" %(x, x))
        cui_handle.pycui.show_menu_popup("toggle options", options, toggle)
        cui_handle.pycui._popup.set_selected_color(py_cui.MAGENTA_ON_CYAN)
