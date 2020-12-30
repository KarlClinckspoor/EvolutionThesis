import glob
import numpy as np
import imageio
import math


def add_border(image, width=1):
    newimage = np.zeros(
        (image.shape[0] + width * 2, image.shape[1] + width * 2, image.shape[2])
    )
    newimage[width:-width, width:-width, :] = image
    return newimage


def concat_pages2(pages, num_rows, num_cols, background_color=255):
    # Load one page to get the dimensions
    test_page = imageio.imread(pages[0])
    # page_size = test_page.shape
    t_bpage = add_border(test_page)
    t_bpage_w, t_bpage_h, _ = t_bpage.shape

    # Create the empty array
    # canvas = np.zeros(
    #     (num_rows * t_bpage_h, num_cols * t_bpage_w, 3), dtype="uint8"
    # )
    canvas = np.zeros(
        (num_cols * t_bpage_w, num_rows * t_bpage_h, 3), dtype="uint8"
    )
    # extra_pages = [None] * (len(pages) - num_rows * num_cols)
    ideal_num_pages = num_rows * num_cols
    extra_required_pages = ideal_num_pages - len(pages)
    pages = pages + [None] * extra_required_pages
    # arr_pages = np.array(pages + extra_pages).reshape((num_rows, num_cols))
    arr_pages = np.array(pages).reshape((num_rows, num_cols))

    for i in range(0, num_rows):
        for j in range(0, num_cols):
            # Try to open. If not in range (no more pages left), add blank page
            page = arr_pages[i, j]
            if page:
                bpage = add_border(imageio.imread(page))
            else:  # Extra page
                bpage = np.full((t_bpage_w, t_bpage_h, 3), background_color)
            canvas[
                j * t_bpage_w : (j + 1) * t_bpage_w,
                i * t_bpage_h : (i + 1) * t_bpage_h,
                :,
            ] = bpage

    return canvas


def test_concat():
    images = glob.glob("./imgs/e7f3e0e57a750ca29a4e2857850587a2f07260aa/*png")
    images.sort(key=lambda x: int(x.split("-")[1][:-4]))

    # 792 - 12 = 780
    # 668

    size = len(images)
    A4_page_size = (210, 297)  # width, height in mm
    available_size_image = (780, 668)  # width, height in px
    width_magnitude = 16
    height_magnitude = 9

    number_cols = math.floor(
        (size * width_magnitude / height_magnitude) ** (1 / 2)
    )
    number_rows = math.floor(
        (size * height_magnitude / width_magnitude) ** (1 / 2)
    )

    # Adds another row if there's too little space (from floor)
    if number_rows * number_cols < size:
        number_rows += 1
    # If the ratios are inverted, needs to add a new column
    # if number_rows * number_cols < size:
    #     number_cols += 1

    concat = concat_pages2(images, number_cols, number_rows)
    imageio.imsave("test.png", concat)


test_concat()