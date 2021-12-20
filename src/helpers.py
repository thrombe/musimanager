from difflib import SequenceMatcher
from wcwidth import wcwidth, wcswidth
from PIL import Image
import io
import py_cui

# 2 width chars are counted as 1 width by len(), so causes probs
# https://github.com/jupiterbjy/CUIAudioPlayer/
def pad_zwsp(string):
    zwsp = "\u200b" # zero width space character or something
    pads = 0
    for char in string:
        p = wcwidth(char)-len(char)
        pads += p
    return zwsp*pads + string

def kinda_similar(str1, str2, threshold=0.4):
    # this func is terrible, use a different one
    perc = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    if perc >= threshold: return True
    else: return False

def chop_image_into_square(imag):
    if type(imag) == type(bytes()): img = Image.open(io.BytesIO(imag))
    elif type(imag) == type(""): img = Image.open(imag)
    
    x, y = img.size
    imag = io.BytesIO()
    if abs(x - y) < 2:
        img.save(imag, "jpeg")
        return imag.getvalue()
    
    a = (x-y)/2
    if a > 0: box = (a, 0, x - a, y)
    else: box = (0, -a, x, y+a)
    img = img.crop(box)
    img.save(imag, "jpeg")
    return imag.getvalue()

def text_on_both_sides(x, y, width):
    if len(x)+len(y) > width-2:
        ex = len(x) > width/2
        yae = len(y) > width/2
        if ex and not yae:
            x = py_cui.fit_text(width-2-len(y), x)
        elif not ex and yae:
            y = py_cui.fit_text(width-2-len(x), y)
        elif ex and yae:
            widthe = int((width-2)/2)
            x, y = py_cui.fit_text(widthe + 1, x), py_cui.fit_text(widthe, y)
    return x + (width - len(x) - len(y))*" " + y