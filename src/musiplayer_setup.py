

import subprocess
import os
import opts

def build_and_move():
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir)
    
    musiplayer_path = os.path.join(dir_path, "musiplayer")
    if not os.path.exists(musiplayer_path):
        print("musiplayer code not found")
        quit()

    if not opts.compile_on_every_boot:
        if os.path.exists(os.path.join(dir_path, "src/musiplayer.so")):
            return

    commands = f'''
    cd {musiplayer_path}
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
    
    path1 = os.path.join(dir_path, "musiplayer/target/release/libmusiplayer.so")
    res_path = os.path.join(dir_path, "src/musiplayer.so")
    if os.path.exists(path1):
        if os.path.exists(res_path): os.remove(res_path)
        os.rename(path1, res_path)
        