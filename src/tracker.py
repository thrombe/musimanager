import os
import serde
import json

import opts
import song
import artist
import album

def to_json(obj):
    if type(obj) == type(set()): return list(obj)
    return obj.__dict__

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
    """        
    def load(self):
        if not os.path.exists(opts.musitracker_path + ".lol"):
            if opts.debug_no_edits_to_db: return
            with open(opts.musitracker_path + ".lol", "w") as f:
                json.dump(self.to_dict(), f, indent=4)
            return
            
        with open(opts.musitracker_path, "r") as f:
            celf = json.load(f)
        self.artists = []
        for json_artist in celf["artists"]:
            artst = artist.Artist.new(json_artist["name"], json_artist["keys"])
            artst.check_stat = json_artist["check_stat"]
            artst.ignore_no_songs = json_artist["ignore_no_songs"]
            artst.name_confirmation_status = json_artist["name_confirmation_status"]

            # for json_album in json_artist["known_albums"]:
            #     albm = album.Album("", "", "", "")
            #     albm.__dict__ = json_album
            #     artst.known_albums.add(albm)

            for song_data in json_artist["songs"]:
                sng = song.Song.new(song_data["title"], song_data["key"], song_data["artist_name"])
                sng.info = song.SongInfo.empty()
                if song_data["info"]["titles"] is not None:
                    sng.info.titles = song_data["info"]["titles"]
                # else:
                #     sng.info.titles = None

                if song_data["info"]["video_id"] is not None:
                    sng.info.video_id = song_data["info"]["video_id"]
                # else:
                #     sng.info.video_id = None

                if song_data["info"]["tags"] is not None:
                    sng.info.tags = song_data["info"]["tags"]
                # else:
                #     sng.info.tags = None

                if song_data["info"]["thumbnail_url"] is not None:
                    sng.info.thumbnail_url = song_data["info"]["thumbnail_url"]
                # else:
                #     sng.info.thumbnail_url = None

                if song_data["info"]["album"] is not None:
                    sng.info.album = song_data["info"]["album"]
                # else:
                #     sng.info.album = None

                if song_data["info"]["artist_names"] is not None:
                    sng.info.artist_names = song_data["info"]["artist_names"]
                # else:
                #     sng.info.artist_names = None

                if song_data["info"]["channel_id"] is not None:
                    sng.info.channel_id = song_data["info"]["channel_id"]
                # else:
                #     sng.info.channel_id = None

                if song_data["info"]["uploader_id"] is not None:
                    sng.info.uploader_id = song_data["info"]["uploader_id"]
                # else:
                #     sng.info.uploader_id = None

                artst.songs.append(sng)
            artst.keywords = json_artist["keywords"]
            self.artists.append(artst)

        # self.load_sorter()
    
    # def load_sorter(self):
    #     with open(opts.musisorter_path, "r") as f:
    #         dikt = json.load(f)
    #     # dont change all 3 in one go
    #     for artst in self.artists:
    #         data = dikt.get(artst.name, None)
    #         if not data:
    #             for key, val in dikt.items():
    #                 if any([
    #                     list(artst.keys).sort() == val["keys"].sort(),
    #                     list(artst.keywords).sort() == val["keywords"].sort(),
    #                 ]):
    #                     data = val
    #                     artst.set_new_name(key)
    #                     break
    #         artst.keys = set(data["keys"])
    #         artst.keywords = set(data["keywords"])
    #         artst.check_stat = data["check_stat"]
    """
    def get_song_paths(dir: str, ext: list=opts.search_exts):
        song_paths = []
        for basepath, _, files in os.walk(dir):
            for f in files:
                if f.split(".")[-1] in ext:
                    song_paths.append(os.path.join(basepath, f))
        return song_paths
