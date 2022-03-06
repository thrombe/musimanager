
import logging

import py_cui

import opts
import cui_widgets

if opts.LUUNIX_X86_64: import ueberzug.lib.v0 as ueberzug

pycui = None

class CUI_handle:
    def __init__(self):
        self.pycui = None
        self.player_widget = None
        self.browser_widget = None

    def setup(self):
        if opts.ANDROID_64:
            self.pycui = py_cui.PyCUI(4, 1)
        else:
            self.pycui = py_cui.PyCUI(1, 2)
        global pycui 
        pycui = self.pycui # to make it accessible globally
        self.pycui.toggle_unicode_borders()
        self.pycui.set_title('cuisiman')
        # self.master.enable_logging(logging_level=logging.ERROR)
        # self.master.toggle_live_debug_mode()
        self.pycui.set_refresh_timeout(0.7)
        self.pycui.set_on_draw_update_func(self.refresh)


        # TODO: try these
            # picui.set_border_color()
            # picui.set_focus_border_color()

        if opts.ANDROID_64:
            self.player_widget = cui_widgets.PlayerWidget(
                self.pycui.add_scroll_menu('Player', row=0, column=0, row_span=1, column_span=1, padx = 1, pady = 0)
                )
            self.browser_widget = cui_widgets.BrowserWidget(
                self.pycui.add_scroll_menu('Browser',  row=1, column=0, row_span=3, column_span=1, padx = 1, pady = 0),
                self.player_widget,
                )
        else:
            self.player_widget = cui_widgets.PlayerWidget(
                self.pycui.add_scroll_menu('Player', 0, 1, row_span=1, column_span=1, padx = 1, pady = 0)
                )
            self.browser_widget = cui_widgets.BrowserWidget(
                self.pycui.add_scroll_menu('Browser',  0, 0, row_span=1, column_span=1, padx = 1, pady = 0),
                self.player_widget,
                )

        self.player_widget.setup()
        self.browser_widget.setup()

    def safe_start(self):
        try:
            self.start()
        except Exception:
            import traceback
            self.browser_widget.save()
            print(traceback.format_exc())
            quit()

    def start(self):
        if getattr(self, "pycui", None) is None: self.setup()

        if opts.LUUNIX_X86_64 and not opts.ASCII_ART:
            with ueberzug.Canvas() as canvas:
                self.player_widget.image_placement = canvas.create_placement('album_art', scaler=ueberzug.ScalerOption.FIT_CONTAIN.value)
                self.player_widget.image_placement.visibility = ueberzug.Visibility.INVISIBLE
                self.pycui.start()
        else:
            self.pycui.start()

    def refresh(self):
        self.browser_widget.refresh()
        if not self.pycui._in_focused_mode: self.pycui.move_focus(self.browser_widget.scroll_menu) # hacky way to force focus on browser widget
