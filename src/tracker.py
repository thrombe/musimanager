import os
import serde
import json
import helpers

import opts
import song
import artist
import album
import cui_content_providers

class Tracker(serde.Model):
    artists: serde.fields.List(serde.fields.Nested(artist.Artist))
    auto_search_artists: serde.fields.List(serde.fields.Nested(artist.Artist))
    playlists: serde.fields.List(serde.fields.Nested(cui_content_providers.SongProvider))
    queues: serde.fields.List(serde.fields.Nested(cui_content_providers.SongProvider))
    # progress_history: serde.fields.Dict() # {key: watch_progress in range (0, 1)}
    musicache: serde.fields.Dict()
    albumcache: serde.fields.Dict()

    def new():
        return Tracker(
            artists=[],
            playlists=[],
            queues=[],
            musicache={},
            albumcache={},
        )
    
    def set_refs(self):
        song.Song.set_musicache_refrence(self)
        album.Album.set_albumcache_refrence(self)

    # TODO: save and load cache from different file so its easy to yeet
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

    def add_artist(self, a: artist.Artist):
        self.artists.append(a)

    def add_song(self, s: song.Song):
        s.try_get_info()
        a = self.get_suitable_artist_for_song(s)
        new = False
        if a is None:
            new = True
            a = artist.Artist.new(s.artist_name, [])
            # path = f"{opts.musi_path}{a.name}"
            # if not os.path.exists(path):
            #     os.mkdir(path)
            self.add_artist(a)
        if a.contains_song(s): return
        a.add_song(s)
        if s.last_known_path is None:
            s.download()
        s.tag(img_bytes=s.download_cover_image())
        s.move_to_artist_folder()
        return (s, a) if new else (s, None)

    def get_suitable_artist_for_song(self, s: song.Song):
        # threshold = 0.75
        for artist in self.artists:
            if s.key in artist.keywords:
                return artist
        for artist in self.artists:
            if s.info.channel_id in artist.keys:
                return artist
        # for artist in self.artists:
        #     # if any(kinda_similar(self.title.lower(), key.lower(), threshold) for key in artist.keywords):
        #     if any(helpers.kinda_similar(word.lower(), name.lower(), threshold) for name in s.info.artist_names for word in artist.keywords):
        #         return artist
        # for artist in self.artists:
        #     if any([
        #         # any(kinda_similar(word.lower(), name.lower(), threshold) for name in self.info.artist_names for word in artist.keywords),
        #         any(helpers.kinda_similar(word.lower(), tag.lower(), threshold) for tag in s.info.tags for word in artist.keywords),
        #         any(helpers.kinda_similar(word.lower(), title.lower(), threshold) for title in s.info.titles for word in artist.keywords),
        #         ]):
        #         return artist
        
        return None

    def remove_song(self, s: song.Song):
        for a in self.artists:
            for i, s1 in enumerate(a.songs):
                if s.key == s1.key:
                    a.songs.pop(i)
                    return
        new_path = f"{opts.temp_dir}{s.key}.{s.last_known_path.split('.')[-1]}"
        os.rename(s.last_known_path, new_path)
        s.last_known_path = new_path
