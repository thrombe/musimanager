

class Artist:
    def __init__(self, name, key):
        self.name = name
        if type(key) == type(["key"]): self.keys = set(key)
        elif type(key) == type("string"): self.keys = set([key])
        else: self.keys = None
        self.check_stat = True
        self.ignore_no_songs = False # wont be removed from db even if no songs in it (only tracking for new albums)
        self.name_confirmation_status = False
        
        self.known_albums = set()
        self.songs = set() # downloaded songs
        self.keywords = set() # keywords for sort
    