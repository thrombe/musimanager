from difflib import SequenceMatcher
from wcwidth import wcwidth, wcswidth

# 2 width chars are counted as 1 width by len(), so causes probs
# https://github.com/jupiterbjy/CUIAudioPlayer/
def pad_zwsp(string):
    zwsp = "\u200b" # zero width space character or something
    pads = 0
    for char in string:
        p = wcwidth(char)-len(char)
        pads += p
    return string + zwsp*pads

def kinda_similar(str1, str2, threshold=0.4):
    # this func is terrible, use a different one
    perc = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    if perc >= threshold: return True
    else: return False
