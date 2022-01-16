

import subprocess
import os

def build_and_move():
    subprocess.run(["./musiplayer/build.sh", ], shell=True)

    path1 = "./musiplayer/musiplayer.so"
    res_path = "./src/musiplayer.so"

    if os.path.exists(path1):
        if os.path.exists(res_path): os.remove(res_path)
        os.rename(path1, res_path)