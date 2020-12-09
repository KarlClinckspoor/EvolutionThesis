import subprocess
import os
import shutil
import glob

movie_folder = './movie'
os.makedirs(movie_folder, exist_ok=True)

reference = open('ids_dates.txt', 'r').read().split('\n')
hash_equivalence = {}
hash_equivalence_inv = {}
hash_order = []

for i, line in enumerate(reference):
    hash_ = line.split(' ')[0]
    hash_equivalence[hash_] = 94 - i
    hash_equivalence_inv[i] = hash_
    hash_order.append(hash_)

# Copy files with names to correct folder

for file in glob.glob('./images/*png'):
    try:
        shutil.copy(file, os.path.join(movie_folder, f'{hash_equivalence[os.path.basename(file)[:-4]]:04d}.png'))
    except shutil.SameFileError:
        pass

proc = subprocess.run(['ffmpeg.exe', '-i', './movie/%04d.png', '-framerate', '4', '-s', '1920x1690', 'tese.mp4'])
