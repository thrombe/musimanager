# import test

import musiplayer_setup
musiplayer_setup.build_and_move()

import opts

import threading
# stores ytmusic in global variable
threading.Thread(target=opts.load_ytmusic, args=()).start()

import cui_handle
cui_handle.CUI_handle().safe_start()
