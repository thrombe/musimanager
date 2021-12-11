
import logging

import py_cui

import opts
import cui_widgets

if opts.LUUNIX: import ueberzug.lib.v0 as ueberzug

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

        self.player_widget = cui_widgets.PlayerWidget(self.pycui.add_scroll_menu('Player', 0, 1, row_span=1, column_span=1, padx = 1, pady = 0))
        self.browser_widget = cui_widgets.BrowserWidget(
            self.pycui.add_scroll_menu('Browser',  0, 0, row_span=1, column_span=1, padx = 1, pady = 0),
            self.player_widget,
            )

        self.player_widget.setup()
        self.browser_widget.setup()

    def start(self):
        if getattr(self, "pycui", None) is None: self.setup()

        if opts.LUUNIX and not opts.ASCII_ART:
            with ueberzug.Canvas() as canvas:
                # TODO: crop the pic to be square so things are predictable (album art is generally square too)
                self.player_widget.image_placement = canvas.create_placement('album_art', scaler=ueberzug.ScalerOption.FIT_CONTAIN.value)
                self.player_widget.image_placement.visibility = ueberzug.Visibility.INVISIBLE
                self.pycui.start()
        else:
            self.pycui.start()

    def refresh(self):
        self.player_widget.refresh()
