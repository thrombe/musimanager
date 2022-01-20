

import subprocess
import os

def build_and_move():

    commands = '''
    cd ./musiplayer
    cargo build --release
    '''

    try:
        subprocess.check_output(
            [commands, ],
            shell=True,
            # stderr=subprocess.STDOUT # mutes output
        )
    except:
        raise Exception("failed to compile musiplayer")
    
    path1 = "./musiplayer/target/release/libmusiplayer.so"
    res_path = "./src/musiplayer.so"

    if os.path.exists(path1):
        if os.path.exists(res_path): os.remove(res_path)
        os.rename(path1, res_path)
        