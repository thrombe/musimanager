from pydub import AudioSegment
song = AudioSegment.from_mp3("/sdcard/Documents/SEG2Fd6YwNY-320.mp3")
img = '/storage/emulated/0/Pictures/Screenshots/periodic-table-of-distro_compress82.jpg'
song.export("/sdcard/Documents/out.m4a", format="ipod", bitrate="160k", tags={'artist': 'Various artists', 'album': 'Best of 2011', 'comments': 'This album is awesome!'})#, cover = img)
# only mp3 covers are supported as of 12/4/21