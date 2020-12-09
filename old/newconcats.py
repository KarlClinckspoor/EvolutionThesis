# coding: utf-8
import numpy as np
import imageio
import glob


def add_border(image, width=1):
    newimage = np.zeros(
        (image.shape[0] + width * 2, image.shape[1] + width * 2, image.shape[2])
    )
    newimage[width:-width, width:-width, :] = image
    return newimage


# todo: assure all images have the same size


def concat_pages(pages, width, height, background_color=255):
    readpages = [imageio.imread(page) for page in pages]
    borderpages = [add_border(page, width=2) for page in readpages]
    stackh = np.hstack(borderpages[0:width])
    stackv = stackh.copy()
    for i in range(1, height):
        prev_stackh_shape = stackh.shape
        try:
            stackh = np.hstack(borderpages[i * width : (i + 1) * width])
        except ValueError:
            stackh = np.full(prev_stackh_shape, background_color)
        if stackh.shape != prev_stackh_shape:
            # No more images. Fill with white
            new_stackh = np.full(
                prev_stackh_shape, background_color, dtype="uint8"
            )
            new_stackh[:, : stackh.shape[1], :] = stackh
            stackh = new_stackh
        stackv = np.vstack([stackv, stackh])
    # imageio.imsave('../../teste.png', stackv)
    return stackv


if __name__ == "__main__":
    folders = glob.glob(".")
    pages = glob.glob("./*png")
    pages.sort(key=lambda x: int(x.split("-")[1][:-4]))
