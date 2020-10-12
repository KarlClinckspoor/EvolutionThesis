import matplotlib.pyplot as plt
import glob
import numpy as np
import os
import shutil
import math
import imageio
import gc

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

hor_resolution = 1920
ver_resolution = 1080
dpi = 100
figwidth = hor_resolution / dpi
figheight = ver_resolution / dpi

for i, folder in enumerate(folders):
    if not os.path.isdir(folder):
        continue
    if os.path.isfile(os.path.join('./images', os.path.basename(folder)+'.png')):
        print('File already exists', folder+'.png', 'skipping')
        continue
    print(f'Processing folder {i+1}/{len(folders)}, {folder}')
    images = glob.glob(os.path.join(folder, "*png"))

    fig, axs = plt.subplots(
        nrows=ideal_height, ncols=ideal_width, figsize=(figwidth, figheight)
    )
    axs = axs.flatten()

    #images = glob.glob('./images/0e5ba506bcd8951cd0a8358597b4abe049e40a6d/*png')

    for ax, image in zip(axs, images):
        #print(f'Processing image {image}')
        data = imageio.imread(image)
        ax.imshow(data)

    for ax in axs:
        ax.set_frame_on(False)
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)

    plt.subplots_adjust(left=1E-3, right=0.99999, bottom=1E-3, top=0.9999, wspace=0, hspace=0)
    plt.axis('off')
    fig.savefig(f'{folder}.png')

    del axs
    fig.clear()
    del fig
    gc.collect()

# print(size, number_cols * maximum_width - (maximum_width - remainder))
