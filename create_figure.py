# import pandas as pd
import datetime
import glob
import pickle
from collections import Counter
from pathlib import Path
from typing import List

# To stop a PIL warning that the image is too large
import PIL
import imageio
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud

from config import *
from text_stats import (
    Stats,
    open_file,
    fix_specific_things,
)

PIL.Image.MAX_IMAGE_PIXELS = 933120000

debug = False

plt.rcParams.update(
    {
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": ["Latin Modern Roman"],
    }
)


# Messages to put on specific commit statuses.
commit_status_messages = {
    "5ed030fd8df9a137338766ca9cdb01d4c3c6a950": "Started writing",
    "e328113ec7c6706601ef9da0297d7a82f7c97b5f": "Defining overall format",
    "395d313b066f7534e0e06c6f30ef4f98c324b14f": "Started writing one appendix",
    "cd4dbc7d9e89ab182c2fb82792f77e03094685b2": "Started writing the results and discussions (Urea)",
    "860d47b05b81675bedf326f47d2ddda15ac9cd4a": "Decided on another table format",
    "af6cfc5d7130763f0fd1638dd78ab3942c50f31d": "Started to add figures as pdfs, not pngs",
    "248b5a49e1ca6c1776c3d49fe6b4d427614fb33f": "Continued battling Urea in the discussion (SAXS, DLS, DSC)",
    "86e48e9b0b09ff4103af5345caae4cb66cbd7f7c": "Finished Urea",
    "f98a90abac29c0623674a31148f923399ccbb2ab": "Tidying up some code to add as listings",
    "d925eb70b4e6d9bf690affe321b30b2c47a9d306": "Started Materials and Methods",
    "c6c41bac1cf01bb4b767efd0736bedc8ae8c6b04": "Finished Materials and Methods",
    "15ba65d44811d9f6ff5915567f0e615e7c750e03": "Started writing introduction",
    "74d7c44f8f8bfcfa3f2623305735ac1339e498af": "Finished introduction draft",
    "995209f2a17ee61f94763b4f8d50c445a84f7c00": "Started writing Background Theory (Rheology)",
    "a852e2a71c727b3fac129c5ac9f7cc1cba9ac2f4": "Background Theory (ITC)",
    "f3a2274f4fc9f877252df0b86fceee27c67961cc": "Background Theory (SAXS)",
    "ce9eb41680b28bdc3fce4ad39f4e087df016fbfa": "Background Theory (SAXS) rewritten from scratch",
    "ad5f0740bd6a1e278cb14761f2d95dd722ba2513": "Added several illustrative plots",
    "59f4f3ca60cb8a25185b4e690ec11460b2e04424": "Continued discussion (Rheology, ITC)",
    "a5f886f9a60a6857e6cb85dbfc3c5bb2680a0e48": "Multivariate analysis added",
    "299d6e4565deaf05f4288461e332390c9669b8c4": "Noticed more information had to be added to Background Theory",
    "a5b3b317b90da1d873e4382f5ba47b202277d2a9": "Continued the Results and Discussion",
    "0e5ba506bcd8951cd0a8358597b4abe049e40a6d": "Finished first part of Results and Discussion draft",
    "5507ff4b3a29392d3e9a8ce78d11b2b58274ee64": "Started writing about the Results and Discussion of the nonfortuitous kinetics work",
    "774b8636eb248628730ba78dfaf33ad487e21c67": "Finished the nonfortuitous kinetics work",
    "da0fefa6be3c859b0feb334823e77ba25b05d918": "Added an appendix citing my contributions to other works",
    "c050c53d94caa6fa219c68bbe20f7d5fbe04ef4e": "Hopefully finished writing the Background Theory.",
    "1fc1c8266b5d3fb15f6893dd12a536558fde3277": "Started wrapping up cross-references, citations, small corrections, etc.",
    "b9acc0d0da67c99ccf4b73fe10662bbefc655378": "Finished revising cross-references",
    "35254976ab9a9d54ab5a47d7e269fb101837d39a": "Sent for correction and review to friends, family and supervisor",
    "a70bc21ea0d32d0b8b573b98644d5f6b5333a6ea": "Went through the review by my mother",
    "77344f08c27585281a923f804d0860bd77e420b7": "Went through the review by a close friend",
    "7984ed8d3a5ef67a8366aae94b26f351b0bf1403": "Started working on the review by my supervisor",
    "c12761b75589a493430b713f07cd3b0e37dbbcc6": "Sent to committee (12th Feb. 2019)",  # Sent on the 12th of February.
    "d0ad630be3604b73cf82e07a6d63f2863e8045b2": "Approved (19th March 2019)! Revising committee suggestions",
    "38f3c13c31bdf71d43f4878b6c614af52d34f2e9": "Finished revising suggestions by Member 1 (Be)",
    "8896a7f5108ff4d700cbc6ded1f72c5272140c01": "Finished revising suggestions by Member 2 (Bo)",
    "b34ac69f9a65ac4a2b8a311fe21dc6bcf2e3f392": "Finished revising suggestions by Member 3 (PM)",
    "7d425169c76aefe5b439c0337f8c4df4fb593b1f": "Finished revising suggestions by Member 4 (WL)",
    "65f4681432a262a1f550b336f88c300e5d6eb164": "Minor corrections and bureaucratic changes",
    "47c4a42c8c1ee33aa003a48ea91e734175a5ecfa": "Added library catalog info",
    "e6bf1efcfffb6301457da6d66bc7a29d6a99e29c": "Started back and forth to fit institutional formatting requirements",
    "30937f61271564f7d5b3fd59a852ee590e101115": "Final approval - Diploma incoming!",
}

# Define the colors of each type of stat used
color_code_stats = dict(
    wc="C0",
    uwc="C1",
    fig="C2",
    tab="C3",
    eq="C4",
    list="C5",
)


def create_wordcloud(
    word_Counter: Counter,
    width: int = 1920,
    height: int = 1080,
    background_color: str = "white",
    **kwargs,
) -> WordCloud:
    """Creates a wordcloud element based on the Stats of a

    Args:
        word_Counter (Counter): [description]
        width (int, optional): [description]. Defaults to 1920.
        height (int, optional): [description]. Defaults to 1080.
        background_color (str, optional): [description]. Defaults to "white".

    Returns:
        WordCloud: [description]
    """

    cloud = WordCloud(
        stopwords={""},
        width=width,
        height=height,
        background_color=background_color,
        **kwargs,
    ).generate_from_frequencies(word_Counter)
    return cloud


def transfer_stats_between_wc(
    reference_cloud: WordCloud,
    target_cloud: WordCloud,
    transfer_fontsize: bool = False,
    transfer_pos: bool = False,
    transfer_orientation: bool = False,
    transfer_color: bool = False,
    transfer_unk: bool = False,
) -> WordCloud:
    """Transfer the stats between two wordclouds, for example, the text positions. If a word is not
    present in the reference cloud, then its corresponding value in the target cloud is zero.

        Args:
            reference_cloud (WordCloud): The wordcloud that will supply the
              properties
            target_cloud (WordCloud): The wordcloud that will be changed
            transfer_fontsize (bool): Choose to transfer the font size. Defaults to False.
            transfer_pos (bool): Choose to transfer the position. Defaults to False.
            transfer_orientation (bool): Choose to transfer the orientation. Defaults to False.
            transfer_color (bool): Choose to transfer the color. Defaults to False.
            transfer_unk (bool): Choose to transfer the unknown property. Defaults to False.

        Returns:
            WordCloud: The modified wordcloud
    """
    # layout_: list of (string, font size, position, orientation, color)
    ref_cloud_fs = {i[0][0]: i[1] for i in reference_cloud.layout_}
    ref_cloud_unknown = {i[0][0]: i[0][1] for i in reference_cloud.layout_}
    ref_cloud_pos = {i[0][0]: i[2] for i in reference_cloud.layout_}
    ref_cloud_or = {i[0][0]: i[3] for i in reference_cloud.layout_}
    ref_cloud_col = {i[0][0]: i[4] for i in reference_cloud.layout_}
    # layout_: list of (string, font size, position, orientation, color)
    for i, item in enumerate(target_cloud.layout_):
        word = item[0][0]
        fs = ref_cloud_fs.get(word, 0) if transfer_fontsize else item[1]
        unk = ref_cloud_unknown.get(word, 0) if transfer_unk else item[0][1]
        pos = ref_cloud_pos.get(word, (0, 0)) if transfer_pos else item[2]
        or_ = ref_cloud_or.get(word, 0) if transfer_orientation else item[3]
        col = ref_cloud_col.get(word, 0) if transfer_color else item[4]
        newitem = ((word, unk), fs, pos, or_, col)
        target_cloud.layout_[i] = newitem
    return target_cloud


def scale_wordcloud(
    target_cloud: WordCloud,
    reference_cloud: WordCloud,
    target_wordcount: int,
    reference_wordcount: int,
    scale_type: str = "log",
) -> WordCloud:
    """The word size of each word in a wordcloud can be adjusted manually.
    Unfortunately, since the words are located by a corner (upper left?), they won't
    be centered as you adjust the sizes. This can be used to evaluate the evolution
    of the word sizes as the document grows.

        Args:
            target_cloud (WordCloud): The wordcloud that will be changed
            reference_cloud (WordCloud): The wordcloud that will be taken as the 100% size reference.
            target_wordcount (int): The sum of all word counts used to create the wordcloud that will be changed (<100%)
            reference_wordcount (int): The sum of all word counts used to create the reference (100%)
            scale_type (str, optional): The type of scaling. It can be `linear`, where the percentage change of the word
             size is the ratio between the reference and target wordclouds. It can be `log`, where the ratio is the
             ratio of the log10 of each wordcount. Defaults to "log".


        Returns:
            WordCloud: The size adjusted wordcloud
    """
    # Transfer other properties, then scale the font size
    target_cloud = transfer_stats_between_wc(
        reference_cloud,
        target_cloud,
        transfer_pos=True,
        transfer_orientation=True,
        transfer_unk=True,
        transfer_color=True,
    )
    ref_cloud_fs = {i[0][0]: i[1] for i in reference_cloud.layout_}
    for i, item in enumerate(target_cloud.layout_):
        word = item[0][0]
        if scale_type == "linear":
            scaled_fs = (
                ref_cloud_fs.get(word, 1) * target_wordcount / reference_wordcount
            )
        else:
            scaled_fs = (
                ref_cloud_fs.get(word, 1)
                * np.log10(target_wordcount)
                / np.log10(reference_wordcount)
            )
        # elif scale_type == "logistic":
        #     assert False  # Not implemented
        # f(x) = L / (1 + e^(-k(x-x0)))
        # https://en.wikipedia.org/wiki/Logistic_function
        # def logistic(x, L, k, x0):
        #     return L / (1 + 2.71 ** (-k * (x - x0)))
        # Maximum value will be reference_wordcount * reference_fontsize
        # Current value will be target_wordcount * word_fontsize
        # L will be maximum value
        # k will be found empirically
        # x0 will be the mean of the values found?
        # max_val = reference_wordcount * max(ref_cloud_fs.values())
        # curr_val = target_wordcount * item[1]
        # min_val = min(i[1] for i in target_cloud.layout_) * target_wordcount
        # k = 10
        # # x0 = (max_val + min_val) / (target_wordcount + reference_wordcount)
        # x0 = (
        #     max(ref_cloud_fs.values())
        #     + min(i[1] for i in target_cloud.layout_)
        # ) / (2)
        # scaled_fs = logistic(item[1], max_val, k, x0)

        newitem = list(item)
        newitem[1] = scaled_fs
        # newitem = tuple(newitem)
        target_cloud.layout_[i] = newitem
    return target_cloud


def load_joined_pdf_image(sha: str, extension: str = ".jpeg") -> np.ndarray:
    """Opens the image using the provided commit sha hash and the extension. Returns a numpy array

    Args:
        sha (str): The commit sha hash
        extension (str, optional): The extension. If ".jpeg", it's the
        compressed version. If '.png', it's the uncompressed version. Defaults
        to ".jpeg".

    Returns:
        np.ndarray: The image itself as a numpy array
    """
    fig_text = imageio.imread(Path(collated_pdfs_path) / (sha + ".jpeg"))
    return fig_text


def create_frame_() -> matplotlib.figure.Figure:
    """An unsuccessful attempt to use gridspec to create the axes.

    Returns:
        matplotlib.figure.Figure: Figure object
        matplotlib.axes: Several axes
    """
    fig_width_height_ratio = 1920 / 1080
    fig_base_width_inch = 12
    # a4_width_mm = 210
    # a4_height_mm = 297

    fig = plt.figure(
        figsize=(
            fig_base_width_inch,
            fig_base_width_inch / fig_width_height_ratio,
        ),
        constrained_layout=True,
    )

    gs = fig.add_gridspec(10, 10)
    ax_text = fig.add_subplot(gs[0:, :7])
    ax_header = fig.add_subplot(gs[0:2, 7:])
    ax_stats = fig.add_subplot(gs[3:7, 7:])
    ax_wc = fig.add_subplot(gs[7:, 7:])

    ax_text.set_xticklabels([])
    ax_text.set_xticks([])
    ax_text.set_yticklabels([])
    ax_text.set_yticks([])

    ax_header.set_xticklabels([])
    ax_header.set_xticks([])
    ax_header.set_yticklabels([])
    ax_header.set_yticks([])

    # ax_stats.set_xticklabels([])
    # ax_stats.set_xticks([])
    # ax_stats.set_yticklabels([])
    # ax_stats.set_yticks([])

    ax_wc.set_xticklabels([])
    ax_wc.set_xticks([])
    ax_wc.set_yticklabels([])
    ax_wc.set_yticks([])
    return fig, ax_text, ax_header, ax_stats, ax_wc


def create_frame() -> matplotlib.figure.Figure:
    """Creates a figure object and several axes at the specific regions.

    Returns:
        matplotlib.figure.Figure: Figure object
        matplotlib.axes: Axis where the collated text will appear
        matplotlib.axes: Axis where the header will appear
        matplotlib.axes: Axis where the stats graph will appear
        matplotlib.axes: Axis where the wordcloud will appear
    """
    fig_width_height_ratio = 1920 / 1080
    fig_base_width_inch = 12
    # a4_width_mm = 210
    # a4_height_mm = 297

    fig = plt.figure(
        figsize=(
            fig_base_width_inch,
            fig_base_width_inch / fig_width_height_ratio,
        )
    )

    # Axis design
    # Left side: mostly occupied by the axis containing the pdf
    # Right side: contains the statistics
    # Right side header: date, time delta, commit hash (added as ax_header)
    # Some base stats (word count, etc) (added as ax_header)
    # Figure containing the evolution of several stats (word counts, unique word
    # counts, etc) (ax_stats)
    # Figure containing the wordcloud of nonstopping words (ax_wc)

    margin = 0.01
    # Define positions
    ax_text_left = margin
    ax_text_bottom = margin
    ax_text_width = 0.65
    ax_text_height = 1 - margin
    ax_text_rect = [ax_text_left, ax_text_bottom, ax_text_width, ax_text_height]

    hor_dividing_buffer = 0.01
    ver_dividing_buffer = 0.01
    subfig_height = 0.3

    ax_header_extra_height = -0.1

    ax_header_left = ax_text_left + ax_text_width + ver_dividing_buffer
    ax_header_bottom = 1 - margin - subfig_height - ax_header_extra_height + 0.005
    ax_header_width = 1 - ax_text_width - 3 * margin
    ax_header_height = subfig_height + ax_header_extra_height
    ax_header_rect = [
        ax_header_left,
        ax_header_bottom,
        ax_header_width,
        ax_header_height,
    ]

    ax_stats_extra_height = 0.1
    ax_stats_buffer_labels = 0.05
    ax_stats_left = ax_header_left + ax_stats_buffer_labels
    ax_stats_bottom = (
        ax_header_bottom
        - subfig_height
        - hor_dividing_buffer
        + ax_stats_buffer_labels
        - ax_stats_extra_height
    )
    ax_stats_width = ax_header_width - ax_stats_buffer_labels
    ax_stats_height = subfig_height - ax_stats_buffer_labels + ax_stats_extra_height
    ax_stats_rect = [
        ax_stats_left,
        ax_stats_bottom,
        ax_stats_width,
        ax_stats_height,
    ]

    ax_wc_extra_bottom = 0.058
    ax_wc_left = ax_header_left
    ax_wc_bottom = (
        ax_stats_bottom
        - subfig_height
        - hor_dividing_buffer
        - ax_stats_buffer_labels
        - ax_wc_extra_bottom
    )
    ax_wc_width = ax_header_width
    ax_wc_height = subfig_height + ax_wc_extra_bottom
    ax_wc_rect = [ax_wc_left, ax_wc_bottom, ax_wc_width, ax_wc_height]

    # [left, bottom, width, height]
    ax_text = fig.add_axes(ax_text_rect)
    ax_header = fig.add_axes(ax_header_rect)
    ax_stats = fig.add_axes(ax_stats_rect)
    ax_wc = fig.add_axes(ax_wc_rect)
    if debug:
        ax_text.text(0.5, 0.5, "text")
        ax_header.text(0.5, 0.5, "header")
        ax_stats.text(0.5, 0.5, "stats")
        ax_wc.text(0.5, 0.5, "wc")

    ax_text.set_xticklabels([])
    ax_text.set_xticks([])
    ax_text.set_yticklabels([])
    ax_text.set_yticks([])

    ax_header.set_xticklabels([])
    ax_header.set_xticks([])
    ax_header.set_yticklabels([])
    ax_header.set_yticks([])

    # ax_stats.set_xticklabels([])
    # ax_stats.set_xticks([])
    # ax_stats.set_yticklabels([])
    # ax_stats.set_yticks([])

    ax_wc.set_xticklabels([])
    ax_wc.set_xticks([])
    ax_wc.set_yticklabels([])
    ax_wc.set_yticks([])

    # if debug:
    #     plt.savefig("teste.png")
    #     plt.show()
    return fig, ax_text, ax_header, ax_stats, ax_wc


def add_wordcloud(ax_wc, cloud: WordCloud):
    """Adds a wordcloud to a matplotlib axis

    Args:
        ax_wc (matplotlib axis): The axis where the wordcloud will be drawn
        cloud (WordCloud): The wordcloud image to be drawn

    Returns:
        Image: The image resulting from calling imshow.
    """
    im = ax_wc.imshow(cloud, interpolation="bilinear")
    return im


def add_stats_graph(
    ax_stats,
    list_of_Stats: List[Stats],
    start_timestamp: int = 1531090905,
) -> None:
    """Creates a graph using the attributes specified, using the list_of_Stats,
    which can be a subset of the total stats you want to consider.

        Args:
            ax_stats (matplotlib axis): axis where the graph will be plotted
            list_of_Stats (List[Stats]): the ordered collection of stats to be added, from oldest to newest.
            start_timestamp (int, optional): The timestamp of the first commit to be considered. Defaults to 1531090905,
             which is the first commit I have.
    """
    start_date = datetime.datetime.fromtimestamp(start_timestamp)
    # Y-Axis: Declaring the containers
    list_word_counts: List[int] = []
    list_unique_word_counts: List[int] = []
    list_fig_count: List[int] = []
    list_tab_count: List[int] = []
    list_eq_count: List[int] = []
    # list_list_count: List[int] = []
    # list_latex_comm_count: List[int] = []
    # list_latex_env_count: List[int] = []

    # X-axis: Declaring the containers
    list_dates: List[datetime.datetime] = []
    list_delta: List[datetime.timedelta] = []
    list_deltas_days: List[float] = []

    # Populating the containers
    for stat in list_of_Stats:
        # X-axis
        date = datetime.datetime.fromtimestamp(int(stat.date))
        delta = date - start_date
        delta_days = delta.days + delta.seconds / 60 / 60 / 24
        list_dates.append(date)
        list_delta.append(delta)
        list_deltas_days.append(delta_days)

        # Y-axis
        list_word_counts.append(stat.word_count)
        list_unique_word_counts.append(stat.unique_word_count)
        list_fig_count.append(stat.figure_count)
        list_eq_count.append(stat.equation_counts)
        # list_list_count.append(stat.listing_count)
        list_tab_count.append(stat.table_count)
        # list_latex_comm_count.append(sum(stat.command_Counter.values()))
        # list_latex_env_count.append(sum(stat.env_Counter.values()))

    ms = 4  # Defining markersize
    # Plotting everything. Labels and legend are unused at the moment.
    ax_stats.plot(
        list_deltas_days,
        list_word_counts,
        marker="o",
        label="Words",
        ms=ms,
        c=color_code_stats["wc"],
    )
    ax_stats.plot(
        list_deltas_days,
        list_unique_word_counts,
        marker="o",
        label="UWords",
        ms=ms,
        c=color_code_stats["uwc"],
    )
    ax_stats.plot(
        list_deltas_days,
        list_fig_count,
        marker="o",
        label="Figs",
        ms=ms,
        c=color_code_stats["fig"],
    )
    ax_stats.plot(
        list_deltas_days,
        list_eq_count,
        marker="o",
        label="Eqs",
        ms=ms,
        c=color_code_stats["eq"],
    )
    ax_stats.plot(
        list_deltas_days,
        list_tab_count,
        marker="o",
        label="Table",
        ms=ms,
        c=color_code_stats["tab"],
    )
    ax_stats.set(xlabel="Days elapsed", ylabel="Count")
    ax_stats.grid(which="major", ls="-", color="gray", alpha=0.9)
    ax_stats.grid(which="minor", ls=":", color="gray", alpha=0.5)


def add_header(
    ax_header, reference_Stat: Stats, current_Stat: Stats, message: str
) -> None:
    """Takes an axis instance and fills it with text related to a reference
    Stat, such as time elapsed, and also information about the current stat.

    Args:
        ax_header (matplotlib axis): The axis where text will be drawn
        reference_Stat (Stats): The reference (last) Stat object
        current_Stat (Stats): The current Stat object
        message (str): The message that needs to be placed
    """

    # Calculate stuff
    timedelta = datetime.datetime.fromtimestamp(
        int(current_Stat.date)
    ) - datetime.datetime.fromtimestamp(int(reference_Stat.date))
    date = str(datetime.datetime.fromtimestamp(int(current_Stat.date)))
    sha = current_Stat.commit_hash
    pagenum = len(list((Path(pdf_pages_path) / current_Stat.commit_hash).glob("*png")))

    # Text settings
    text_options = dict(fontsize=12, usetex=True)
    # Text positions in data coordinates (!) I thought it was axis coordinates,
    # but it's working now.
    line1_height = 0.88
    line2_height = 0.76
    line3_height = 0.68
    line4_height = 0.60
    line5_height = 0.28
    line6_height = 0.12

    # All text in the leftmost column is left-aligned. Text in the center column
    # is center-aligned and in the right column, it's right-aligned.
    col1_left = 0.05
    col2_center = 0.5
    col3_right = 0.95

    # Configuring the positions of the text entries
    # Line 1
    sha_pos = (col2_center, line1_height)
    # Line 2
    date_pos = (col1_left, line2_height)
    delta_pos = (col3_right, line2_height)
    # Stats Line 1
    wordcount_pos = (col1_left, line5_height)
    unique_wordcount_pos = (col2_center, line5_height)
    pagenum_pos = (col3_right, line5_height)
    # Stats Line 2
    numfigs_pos = (col1_left, line6_height)
    numeqs_pos = (col2_center, line6_height)
    numtabs_pos = (col3_right, line6_height)

    # Placing the text
    # Line 1
    ax_header.text(*sha_pos, sha, ha="center", **text_options)
    # Line 2
    ax_header.text(*date_pos, date, ha="left", **text_options)
    ax_header.text(*delta_pos, str(timedelta), ha="right", **text_options)
    # Stats line 1
    ax_header.text(
        *wordcount_pos,
        f"Words: {current_Stat.word_count}",
        ha="left",
        color=color_code_stats["wc"],
        **text_options,
    )
    ax_header.text(
        *unique_wordcount_pos,
        f"Unique words: {current_Stat.unique_word_count}",
        ha="center",
        color=color_code_stats["uwc"],
        **text_options,
    )
    ax_header.text(
        *pagenum_pos, f"Pages: {pagenum}", ha="right", color="k", **text_options
    )
    # Stats line 2
    ax_header.text(
        *numfigs_pos,
        f"Figures: {current_Stat.figure_count}",
        ha="left",
        color=color_code_stats["fig"],
        **text_options,
    )
    ax_header.text(
        *numeqs_pos,
        f"Equations: {current_Stat.equation_counts}",
        ha="center",
        color=color_code_stats["eq"],
        **text_options,
    )
    ax_header.text(
        *numtabs_pos,
        f"Tables: {current_Stat.table_count}",
        ha="right",
        color=color_code_stats["tab"],
        **text_options,
    )

    # Message line. This ensures the text will fit in the provided area
    import textwrap

    # Message line
    message_pos = (col2_center, line4_height)

    maximum_width = 50  # Hardcoded to the dimensions of this figure.
    message = textwrap.fill(message, width=maximum_width)
    # If there's two lines, move text up a bit to fit better
    numlines = len(message.split("\n"))
    if numlines == 2:
        message_pos = (message_pos[0], message_pos[1] + 0.07)
    ax_header.text(
        *message_pos,
        message,
        ha="center",
        color="k",
        va="top",
        **text_options,
    )


def create_all_graphs() -> None:
    """Creates a figure containing all the graphs and saves it to frames_path."""
    # Loads all the pickled Stats files
    files = Path(stats_basepath).glob("*.pkl")
    list_of_Stats = []
    for file in files:
        with open(file, "rb") as fhand:
            st = pickle.load(fhand)
            list_of_Stats.append(st)
    list_of_Stats.sort(key=lambda x: x.date)

    # Creates a standard for the wordclouds that will be created
    wc_kws = dict(
        width=450,
        height=300,
        random_state=9,
        colormap="brg",
        background_color="white",
        relative_scaling=1,
        min_font_size=8,
    )
    # This is the last wordcloud, which dictates the positioning of the words in
    # the previous wordclouds.
    reference_cloud = create_wordcloud(
        list_of_Stats[-1].reduced_word_Counter,
        **wc_kws,
    )
    # Hardcoded to -2 because my last commit is unrelated to the writing process
    reference_wc = sum(list_of_Stats[-2].reduced_word_Counter.values())

    starting_stat = fix_specific_things(list_of_Stats[0])
    previous_message = ""

    # Start of figure creation
    for i, stat in enumerate(list_of_Stats):
        sha = stat.commit_hash
        # sha '714fad5902cfb17cf54633e4dba4314a74675047' is almost a repeat, but removing it is not necessary
        stat = fix_specific_things(stat)
        fig, ax_text, ax_header, ax_stats, ax_wc = create_frame()

        # First, fill in the Text axis
        # Loads the compressed images, although I don't think that improved
        # performance much.
        fig_text = load_joined_pdf_image(sha, ".jpeg")
        ax_text.imshow(fig_text)

        # Next, fill in the header.
        message = commit_status_messages.get(stat.commit_hash, None)
        if not message:
            message = previous_message
        else:
            previous_message = message

        add_header(
            ax_header,
            starting_stat,
            stat,
            message=message,
        )
        # Then create the Stats graph
        # Creates and plots the stats graph using every stat up to the current one
        add_stats_graph(ax_stats, list_of_Stats[: i + 1])
        ax_stats.set_yscale("log")  # I think I prefer this way

        # Lastly create the wordcloud
        cloud = create_wordcloud(stat.reduced_word_Counter, **wc_kws)
        target_wc = sum(stat.reduced_word_Counter.values())
        scaled_cl = transfer_stats_between_wc(
            reference_cloud,
            cloud,
            transfer_pos=True,
            transfer_fontsize=True,
            transfer_color=True,
            transfer_orientation=True,
            transfer_unk=True,
        )
        _ = add_wordcloud(ax_wc, scaled_cl)

        fig.savefig(Path(frames_path) / f"{i:03d}.png", dpi=300)
        plt.close(fig)
        print(f"Processed {i:03d}", flush=True)


# Functions to test stuff


def create_test_Stat(output_filename: str = "test_stats.pkl") -> None:
    """Used to create a Stats object to test the wordcloud generation

    Args:
        output_filename (str, optional): Path to the pickled file to be created. Defaults to "test_stats.pkl".
    """
    path = Path(thesis_path)
    tex_files = glob.glob(str(path / "*.tex"))
    full_text = []
    for file in tex_files:
        text = open_file(file)
        full_text.append(text)
    full_text = "\n".join(full_text)
    st = Stats(
        "all",
        full_text,
        commit_hash="test",
        description="all",
        date="1605480687",
        output_path=stats_basepath,
        debug_output_path=stats_basepath,
        number_most_common=100,
    )
    st.debug = False
    st.calculate_stats()
    st = fix_specific_things(st)
    with open(output_filename, "wb") as fhand:
        pickle.dump(st, fhand)


def test_wordcloud(pickle_path: str = "test_stats.pkl") -> None:
    """Uses a Stats pickled object to generate a wordcloud. Can be created with
    the create_test_Stat function.

    Args:
        pickle_path (str, optional): The path to the Stat object. Defaults to "test_stats.pkl".
    """
    with open(pickle_path, "rb") as fhand:
        st = pickle.load(fhand)
    cloud = create_wordcloud(st.reduced_word_Counter, width=580, height=300)
    # fig, ax_text, ax_header, ax_stats, ax_wc, ax_wc_cb = create_frame_with_cb()
    fig, ax_text, ax_header, ax_stats, ax_wc = create_frame()
    _ = add_wordcloud(ax_wc, cloud)
    # add_colorbar(wc_im, ax_wc_cb)
    plt.show()


def test_stats_graph():
    files = list(Path(stats_basepath).glob("*.pkl"))
    list_of_Stats = []
    for file in files:
        with open(file, "rb") as fhand:
            st = pickle.load(fhand)
            list_of_Stats.append(st)
    list_of_Stats.sort(key=lambda x: x.date, reverse=True)
    fig, ax_text, ax_header, ax_stats, ax_wc = create_frame()
    add_stats_graph(ax_stats, list_of_Stats[2:])
    ax_stats.set_yscale("log")
    plt.show()


def test_header():
    files = glob.glob("./stats/*.pkl")
    list_of_Stats = []
    for file in files:
        with open(file, "rb") as fhand:
            st = pickle.load(fhand)
            list_of_Stats.append(st)
    list_of_Stats.sort(key=lambda x: x.date)

    reference_Stat = list_of_Stats[0]  # First one

    for i, stat in enumerate(list_of_Stats):

        print(f"Testing header {i}", flush=True)
        fig, ax_text, ax_header, ax_stats, ax_wc = create_frame()
        message = commit_status_messages.get(stat.commit_hash, None)
        if not message:
            message = previous_message
        else:
            previous_message = message

        add_header(
            ax_header,
            reference_Stat,
            stat,
            message=message,
        )
        if not Path("./test_headers").is_dir():
            Path("./test_headers").mkdir()

        plt.savefig(f"./test_headers/{i:03d}")
        plt.close(fig)


def test_layout():
    create_frame()
    plt.show()
