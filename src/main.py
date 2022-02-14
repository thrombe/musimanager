# import test

import musiplayer_setup
musiplayer_setup.build_and_move()

import opts
opts.load_ytmusic() # stores ytmusic in global variable

import cui_handle
cui_handle.CUI_handle().safe_start()
