# download, sort and do managing stuff with music files

import os

import opts
from newpipe_db_handler import NewpipeDBHandler
from song import Song, SongInfo
from tracker import Tracker
from artist import Artist

class Manager:
    def __init__(self):
        self.musi_path = opts.musi_path
        self.np_playlists = opts.newpipe_playlists
        self.musisorter_path = opts.musisorter_path
        self.musicache_path = opts.musicache_path

        self.tracker = Tracker()

    def new(self):
        self.tracker.new()

    def load(self):
        self.tracker.load()
    
    def save(self):
        self.tracker.save()

    def download_new_from_newpipe_db(self):
        # self.tracker.gen_extra_data() # to make sure data is updated

        np_db = NewpipeDBHandler()
        playlists = np_db.extract_from_zip()
        for songs_data in playlists.values():
            for song_data in songs_data:
                song = Song(song_data[0], song_data[2], song_data[1])
                if song.key in self.tracker.all_song_keys: continue
                song.download()
                song.sort_using_tracker(self.tracker) # sets the correct artist name and adds self to tracker
                print("")

    # check if any song removed and notify user + handle that in tracker +
    # check if sorted correctly(eg if i change some stuff in artist keywords and stuff)
    def check_songs(self): 
        musidata = {}
        for directory, _, files in os.walk(opts.musi_path):
            if files == []: continue
            artist_name = os.path.basename(directory)
            songs = [Song(None, file[0:-len(".m4a")], artist_name) for file in files]
            musidata[artist_name] = songs
        
        artists_copy = self.tracker.artists.copy()
        for artist in artists_copy:
            # yeet empty artists
            if not artist.songs and not artist.ignore_no_songs:
                self.tracker.artists.remove(artist)
                continue
            
            songs_copy = artist.songs.copy()
            for song in songs_copy:
                found = False
                for _, songs_t in musidata.items():
                    songs_t_copy = songs_t.copy()
                    for song_t in songs_t_copy:
                        if song.key != song_t.key: continue
                        found = True
                        song_t.title = song.title # new songs wont have a title
                        
                        # more suitable artist stuff
                        besto_artisto = song.get_suitable_artist_using_tracker(self.tracker)
                        # if not besto_artisto: print(f"NO ARTIST FOUND -- {song}, {song_t}")
                        
                        # either the actual song isnt in the best directory, or this is a new best artist
                        if song.artist_name != besto_artisto.name:
                            print(f"AAAAAAAAAAAA {song} ----- {besto_artisto}")##########
                            artist.remove_song(song)
                            song.artist_name = besto_artisto.name
                            song.tag()
                            song.sort()
                            besto_artisto.add_song(song)
                        elif song_t.artist_name != besto_artisto.name:
                            song.tag()
                            song.sort()
                        
                        # next song in tracker
                        break
                    if found: break
                if found: continue
                # song removed from directory but in tracker
                print(f"song not found in directory - {song}")
                print("removing the song from db")
                artist.remove_song(song)
                
        # only newly added songs left without a title
        for name, songs in musidata.items():
            for song in songs:
                if song.title: continue
                found = False
                song.get_info()
                song.tag()
                song.title = song.info.titles[0]
                for artist in self.tracker.artists:
                    if song.artist_name == artist.name:
                        artist.add_song(song)
                        found = True
                if found: continue

                # artist not found
                artist = Artist(song.artist_name, song.info.channel_id)
                artist.name_confirmation_status = True
                artist.add_song(song)
                self.tracker.add_artist(artist)
            
        # removing empty directories in the main dir
        for directory, subdirs, files in os.walk(opts.musi_path):
            if files == [] and subdirs == []:
                print(f"removing empty directory {directory}")
                if not opts.debug_no_edits_to_stored:
                    os.rmdir(directory)


        """
        # check if all songs are sorted properly - ie if i change something in sorter
        for songs in musidata.values():
            for song in songs:
                found = False
                for artist in self.tracker.artists:
                    for song_t in artist.songs:
                        if song.key == song_t.key:
                            found = True
                            song.title = song_t.title # notice that newly added songs (not in tracker) will not have a title
                            suitable_artist = song_t.get_suitable_artist_using_tracker(self.tracker)
                            if song.artist_name != suitable_artist.name:
                                song_t.sort(current_path=song.path())
                            break
                    if found: break

        # check if a new songs in dir
        for songs in musidata.values(): #### nect time this func runs, how do i gurantee it wont try to sort it properly ??
            for song in songs:
                if song.title: continue
                current_path = song.path(after=True)
                found = False
                for artist in self.tracker.artists: # if its one of the newly created artist from a few lines below
                    if song.artist_name == artist.name:
                        found = True
                        # song.tag()
                        try: song.tag()
                        except Exception as e:
                            print(e, "  ", song)
                            song.get_info_from_tags()
                            artist.songs.add(song)
                            break
                        artist.songs.add(song)
                        artist.add_key(song.info.channel_id, song.info.artist_names)
                        break
                if found: continue
                print(f"found new song, so assuming that the artist name is currect and stuff {song}")
                # song.tag()
                try: song.tag()
                except Exception as e:
                    print(e, "   ", song)
                    song.get_info_from_tags()
                    continue
                artist = Artist(song.artist_name, song.info.channel_id)
                artist.add_key(song.info.channel_id, song.info.artist_names) # just to print it out
                artist.name_confirmation_status = True
                artist.songs.add(song)
                self.tracker.artists.add(artist)

        # check if all items in tracker are in the dir
        for artist in self.tracker.artists:
            songs = artist.songs.copy()
            for song in songs:
                if not os.path.exists(song.path(after=True)):
                    print(f"song not found in directory - {song}")
                    print("removing the song from db")
                    artist.songs.remove(song)
                    if artist.ignore_no_songs: continue
                    if not artist.songs:
                        print(f"no songs found in artist, so removing {artist}")
                        self.tracker.remove(artist)
        """




