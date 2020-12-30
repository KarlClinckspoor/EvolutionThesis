import numpy as np
import imageio
import math
from config import pdf_pages_path, collated_pdfs_path
from pathlib import Path
from typing import Tuple


def add_border(image: np.ndarray, width: int = 1) -> np.ndarray:
    """Adds a black border with width `border_width`, in pixels,
    around an image.

        Args:
            image (np.ndarray): Original image
            border_width (int, optional): Border width in pixels. Defaults to 1.

        Returns:
            np.ndarray: Image with border
    """
    newimage = np.zeros(
        (image.shape[0] + width * 2, image.shape[1] + width * 2, image.shape[2])
    )
    newimage[width:-width, width:-width, :] = image
    return newimage


def add_border_c(
    image: np.ndarray, border_width: int = 1, color=(0, 0, 0)
) -> np.ndarray:
    """Adds a border of color `color` and width `border_width`, in pixels,
    around an image.

        Args:
            image (np.ndarray): Original image
            border_width (int, optional): Border width in pixels. Defaults to 1.
            color (tuple, optional): The color of the border. Defaults to (0, 0, 0)
            , black.

        Returns:
            np.ndarray: Image with border
    """
    rows, cols, depth = image.shape
    # Create new slightly bigger array (border above and below, so 2x)
    newimage = np.full(
        (rows + border_width * 2, cols + border_width * 2, depth), color
    )
    # Places original image in the center
    newimage[border_width:-border_width, border_width:-border_width, :] = image
    return newimage


def collate_pdf_by_sha(sha: str, rows: int, cols: int) -> None:
    """Generates a png image containing all the images generated, side by side,
    with the specific number of rows and columns. Saves it as `{sha}.png` file
    in its appropriate folder

        Args:
            sha (str): SHA hash of commit
            rows (int): number of rows
            cols (int): number of columns
    """
    list_of_images = list((Path(pdf_pages_path) / sha).glob("*png"))
    list_of_images.sort(key=lambda x: x.stem)
    assert rows * cols >= len(list_of_images)  # Can't have missing pages
    canvas = arrange_pages_horizontal(
        list_of_images, rows, cols, background_color=(200, 200, 200)
    )
    output_path = Path(collated_pdfs_path) / (sha + ".png")
    imageio.imsave(output_path, canvas)


def __arrange_pages_vertical(
    pages, num_rows, num_cols, background_color=(255, 255, 255)
) -> np.ndarray:
    """Concatenates the pages vertically into a grid of num_rows x num_cols,
    and fills in any remaining space with "blank pages" of the selected
    background color, default white. WARNING: There's a logic error here, use at
    own risk.

        Args:
            pages (list): A list containing the paths to the png pages
            num_rows (int): The number of rows desired
            num_cols (int): the number of columns desired
            background_color (tuple of int, optional): Color to fill in the
            extra pages. Defaults to (255, 255, 255), white.

        Returns:
            numpy array: Contains a numpy array of shape
            (num_rows * page height (px), num_cols * page width (px), 3).
    """
    # Load one page to get the dimensions
    test_page = imageio.imread(pages[0])
    # page_size = test_page.shape
    t_bpage = add_border(test_page)
    t_bpage_w, t_bpage_h, _ = t_bpage.shape

    # Create the empty array
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


def arrange_pages_horizontal(
    pages, num_rows, num_cols, background_color=(255, 255, 255)
) -> np.ndarray:
    """Concatenates the pages horizontally into a grid of num_rows x num_cols,
    and fills in any remaining space with "blank pages" of the selected
    background color, default white.

        Args:
            pages (list): A list containing the paths to the png pages
            num_rows (int): The number of rows desired
            num_cols (int): the number of columns desired
            background_color (tuple of int, optional): Color to fill in the
            extra pages. Defaults to (255, 255, 255), white.

        Returns:
            numpy array: Contains a numpy array of shape
            (num_rows * page height (px), num_cols * page width (px), 3).
    """
    # Load one page to get the dimensions
    test_page = imageio.imread(pages[0])
    # page_size = test_page.shape
    t_bpage = add_border(test_page)
    t_bpage_h, t_bpage_w, _ = t_bpage.shape

    # Create the empty array
    canvas = np.zeros(
        ((num_rows) * t_bpage_h, num_cols * t_bpage_w, 3), dtype="uint8"
    )
    # extra_pages = [None] * (len(pages) - num_rows * num_cols)
    ideal_num_pages = num_rows * num_cols
    extra_required_pages = ideal_num_pages - len(pages)
    pages = pages + [None] * extra_required_pages
    arr_pages = np.array(pages).reshape((num_rows, num_cols))

    for i in range(0, num_rows):
        for j in range(0, num_cols):
            # Try to open. If not in range (no more pages left), add blank page
            page = arr_pages[i, j]
            if page:
                bpage = add_border_c(imageio.imread(page), color=(0, 0, 0))
            else:  # Extra page
                bpage = np.full((t_bpage_h, t_bpage_w, 3), background_color)
            canvas[
                i * t_bpage_h : (i + 1) * t_bpage_h,
                j * t_bpage_w : (j + 1) * t_bpage_w,
                :,
            ] = bpage

    return canvas


def determine_ideal_shape(sha: str) -> Tuple[int, int]:
    """Returns a tuple containing the number of rows and columns to better fit a
    specific sha. Work in progress

        Args:
            sha (str): Identification

        Returns:
            Tuple[int, int]: number_rows, number_cols
    """
    list_of_images = list((Path(pdf_pages_path) / sha).glob("*png"))
    # list_of_images.sort(key=lambda x: x.stem)
    # 792 - 12 = 780
    # 668
    A4_page_size = (210, 297)  # width, height in mm
    available_size_image = (780, 668)  # width, height in px
    num_a4_on_rows = math.floor(available_size_image[0] / A4_page_size[0])
    num_a4_on_cols = math.floor(available_size_image[1] / A4_page_size[1])
    # Still thinking if there's a way of determining the best size
    # algorithmically
    size = len(list_of_images)

    # Starts with the number of pages that can be fit given the A4 page size,
    # then keeps adding a row and a column, until the canvas could fit more or
    # exactly the number of pages required
    adder_r = 0
    adder_c = 0

    for i in range(100):
        if i % 2 == 0:
            adder_r += 1
        else:
            adder_c += 1
        if (num_a4_on_rows + adder_r) * (num_a4_on_cols + adder_c) >= size:
            break

    number_cols = num_a4_on_cols + adder_c
    number_rows = num_a4_on_rows + adder_r

    return number_rows, number_cols


def find_maximum_number_pages(save: bool = True) -> int:
    folders = [i for i in Path(pdf_pages_path).glob("*") if i.is_dir()]
    number_of_images = {
        folder.stem: len(list(folder.glob("*png"))) for folder in folders
    }
    if save:
        with open("number_of_pages.txt", "w") as fhand:
            fhand.write("sha;pages\n")
            for sha, number in number_of_images.items():
                fhand.write(f"{sha};{number}\n")
    return max(number_of_images.values())


# collate_pdf_by_sha("e7f3e0e57a750ca29a4e2857850587a2f07260aa", 15, 25)
# print(determine_ideal_shape("e7f3e0e57a750ca29a4e2857850587a2f07260aa"))
print(find_maximum_number_pages(save=True))