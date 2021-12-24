import os
import serde
import json

import opts
import song
import artist
import album

class Tracker(serde.Model):
    artists: serde.fields.List(serde.fields.Nested(artist.Artist))
    musicache: serde.fields.Dict()
    albumcache: serde.fields.Dict()

    def new():
        return Tracker(
            artists=[],
            musicache={},
            albumcache={},
        )
    
    def set_refs(self):
        song.Song.set_musicache_refrence(self)
        album.Album.set_albumcache_refrence(self)

    # TODO: save and load cache from different file so its easy to yeet
    # TODO: save playlists, queues, stuff
    def save(self):
        if opts.debug_no_edits_to_db: return
        with open(opts.musitracker_path, "w") as f:
            dikt = self.to_dict()
            json.dump(dikt, f, indent=4)

    def load():
        if not os.path.exists(opts.musitracker_path):
            if opts.debug_no_edits_to_db: return
            with open(opts.musitracker_path, "w") as f:
                t = Tracker.new()
                json.dump(t.to_dict(), f, indent=4)
            return t
            
        with open(opts.musitracker_path, "r") as f:
            t = Tracker.from_json(f.read())
        return t

    def get_song_paths(dir: str, ext: list=opts.search_exts):
        song_paths = []
        for basepath, _, files in os.walk(dir):
            for f in files:
                if f.split(".")[-1] in ext:
                    song_paths.append(os.path.join(basepath, f))
        return song_paths
