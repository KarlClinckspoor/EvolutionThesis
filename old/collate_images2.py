import glob
import numpy as np
import os
import shutil
import math
import imageio
from newconcats import concat_pages

folders = glob.glob("./images/*")
folders = [i for i in folders if os.path.isdir(i)]
max_size = 0

for folder in folders:
    images = glob.glob(os.path.join(folder, "*png"))
    if len(images) > max_size:
        max_size = len(images)

# images = glob.glob('./images/0e5ba506bcd8951cd0a8358597b4abe049e40a6d/*png')

size = max_size
width_ratio = 16
height_ratio = 9

ideal_width = math.floor((size * width_ratio / height_ratio) ** (1 / 2))
ideal_height = math.floor((size * height_ratio / width_ratio) ** (1 / 2))

if ideal_height * ideal_width < size:
    ideal_height += 1

# print(ideal_width, ideal_height, ideal_width * ideal_height, size)

for i, folder in enumerate(folders):
    if not os.path.isdir(folder):
        continue
    if os.path.isfile(os.path.join('./images', os.path.basename(folder)+'.png')):
        print('File already exists', folder+'.png', 'skipping')
        continue
    print(f'Processing folder {i+1}/{len(folders)}, {folder}')
    images = glob.glob(os.path.join(folder, "*png"))
    images.sort(key=lambda x: int(x.split('-')[1][:-4]))
    concat = concat_pages(images, ideal_width, ideal_height).astype('uint8')
    imageio.imsave(f'./{folder}.png', concat)

