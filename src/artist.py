
import serde
import os

import song
import album
import cui_content_providers
import opts

class Artist(serde.Model):
    name: serde.fields.Str()
    keys: serde.fields.List(serde.fields.Str())
    check_stat: serde.fields.Bool()
    ignore_no_songs: serde.fields.Bool() # wont be removed from db even if no songs in it (only tracking for new albums)
    name_confirmation_status: serde.fields.Bool()
    songs: serde.fields.List(serde.fields.Nested(song.Song))
    known_albums: serde.fields.List(serde.fields.Nested(album.Album)) # to track what albums the user has listened to
    keywords: serde.fields.List(serde.fields.Str()) # keywords for sort
    non_keywords: serde.fields.List(serde.fields.Str()) # keywords/keys to specifically ignore

    def new(name, keys):
        if type(keys) == type(["key"]): keys = keys
        elif type(keys) == type("string"): keys = [keys]
        return Artist(
            name=name,
            keys=keys,
            check_stat=True,
            ignore_no_songs=False,
            name_confirmation_status=False,
            songs=[],
            known_albums=[],
            keywords=[],
            non_keywords=[],
        )
    
    def add_song(self, s):
        self.songs.append(s)
        if s.artist_name not in self.non_keywords:
            if s.artist_name not in self.keywords:
                self.keywords.append(s.artist_name)
        if s.info.channel_id not in self.non_keywords:
            if s.info.channel_id not in self.keys:
                self.keys.append(s.info.channel_id)
        if s.info.uploader_id not in self.non_keywords:
            if s.info.uploader_id not in self.keys:
                self.keys.append(s.info.uploader_id)
        s.artist_name = self.name
    
    def remove_song(self, s):
        return cui_content_providers.SongProvider(self.songs, self.name).remove_song(s)

    def contains_song(self, s):
        return cui_content_providers.SongProvider(self.songs, self.name).contains_song(s)
    
    def change_name(self, name):
        self.name_confirmation_status = True
        if name == self.name: return
        old_name = self.name
        self.name = name
        if name not in self.keywords:
            self.keywords.append(name)
        for s in self.songs:
            s.artist_name = self.name
            s.move_to_artist_folder()
        old_folder_path = f"{opts.musi_path}{old_name}"
        if os.path.isdir(old_folder_path):
            if not os.listdir(old_folder_path): # is empty
                os.rmdir(old_folder_path)
    
    def check_songs(self):
        # path = f"{opts.musi_path}{self.name}"
        # if not os.path.exists(path):
        #     os.mkdir(path)
        for s in self.songs:
            if s.last_known_path is None or not os.path.exists(s.last_known_path):
                s.download()
                s.tag(img_bytes=s.download_cover_image())
                s.move_to_artist_folder()
                continue
            if s.last_known_path.split(os.path.sep)[-2] != self.name:
                s.tag()
                s.move_to_artist_folder()
