import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from config import *
from collections import Counter
from text_stats import (
    Stats,
    open_file,
    create_stats_all_tex_files,
    fix_specific_things,
)
import pathlib
import glob
import pickle
import pandas as pd
import datetime
from typing import Union, List

debug = False
matplotlib.rcParams["text.usetex"] = True


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
        stopwords=[""],
        width=width,
        height=height,
        background_color=background_color,
        colormap="gnuplot",
        max_words=30,
        **kwargs,
    ).generate_from_frequencies(word_Counter)
    return cloud


def load_joined_pdf_image(imagepath: pathlib.Path):
    pass


def create_frame() -> matplotlib.figure.Figure:
    """Creates a figure object and several axes at the specific regions.

    Returns:
        matplotlib.figure.Figure: Figure object
        matplotlib.axes: Several axes
    """
    fig_width_height_ratio = 1920 / 1080
    fig_base_width_inch = 12
    a4_width_mm = 210
    a4_height_mm = 297

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
    ax_header_bottom = 1 - margin - subfig_height - ax_header_extra_height
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
    ax_stats_height = (
        subfig_height - ax_stats_buffer_labels + ax_stats_extra_height
    )
    ax_stats_rect = [
        ax_stats_left,
        ax_stats_bottom,
        ax_stats_width,
        ax_stats_height,
    ]

    ax_wc_left = ax_header_left
    ax_wc_bottom = (
        ax_stats_bottom
        - subfig_height
        - hor_dividing_buffer
        - ax_stats_buffer_labels
    )
    ax_wc_width = ax_header_width
    ax_wc_height = subfig_height
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


def create_frame_with_cb() -> matplotlib.figure.Figure:
    fig_width_height_ratio = 1920 / 1080
    fig_base_width_inch = 12
    a4_width_mm = 210
    a4_height_mm = 297

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

    ax_header_extra_height = 0.05

    ax_header_left = ax_text_left + ax_text_width + ver_dividing_buffer
    ax_header_bottom = 1 - margin - subfig_height - ax_header_extra_height
    ax_header_width = 1 - ax_text_width - 3 * margin
    ax_header_height = subfig_height + ax_header_extra_height
    ax_header_rect = [
        ax_header_left,
        ax_header_bottom,
        ax_header_width,
        ax_header_height,
    ]

    ax_stats_buffer_labels = 0.01
    ax_stats_left = ax_header_left + ax_stats_buffer_labels
    ax_stats_bottom = (
        ax_header_bottom
        - subfig_height
        - hor_dividing_buffer
        + ax_stats_buffer_labels
    )
    ax_stats_width = ax_header_width - ax_stats_buffer_labels
    ax_stats_height = subfig_height - ax_stats_buffer_labels
    ax_stats_rect = [
        ax_stats_left,
        ax_stats_bottom,
        ax_stats_width,
        ax_stats_height,
    ]

    ax_wc_cb_width = 0.02
    ax_wc_cb_buffer = 0.01
    ax_wc_left = ax_header_left
    ax_wc_bottom = ax_stats_bottom - subfig_height - hor_dividing_buffer
    ax_wc_width = ax_stats_width - ax_wc_cb_width
    ax_wc_height = subfig_height
    ax_wc_rect = [ax_wc_left, ax_wc_bottom, ax_wc_width, ax_wc_height]

    ax_wc_cb_left = ax_wc_left + ax_wc_width + ax_wc_cb_buffer
    ax_wc_cb_bottom = ax_wc_bottom
    ax_wc_cb_height = ax_wc_height
    ax_wc_cb_rect = [
        ax_wc_cb_left,
        ax_wc_cb_bottom,
        ax_wc_cb_width,
        ax_wc_cb_height,
    ]

    # [left, bottom, width, height]
    ax_text = fig.add_axes(ax_text_rect)
    ax_header = fig.add_axes(ax_header_rect)
    ax_stats = fig.add_axes(ax_stats_rect)
    ax_wc = fig.add_axes(ax_wc_rect)
    ax_wc_cb = fig.add_axes(ax_wc_cb_rect)
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
    return fig, ax_text, ax_header, ax_stats, ax_wc, ax_wc_cb


def add_wordcloud(
    ax_wc: matplotlib.axes._axes.Axes, cloud: WordCloud
) -> matplotlib.axes._axes.Axes:
    im = ax_wc.imshow(cloud, interpolation="bilinear")
    return im


def add_colorbar(image, cax):
    plt.colorbar(image, cax=cax)


def add_stats_graph(
    ax_stats,
    list_of_Stats: List[Stats],
    start_timestamp: int = 1531090905,
    attributes: List[str] = ["word_count", "unique_word_count"],
) -> None:
    """Creates a graph using the attributes specified, using the list_of_Stats,
    which can be a subset of the total stats you want to consider.

        Args:
            ax_stats (matplotlib axis): axis where the graph will be plotted
            list_of_Stats (List[Stats]): the ordered collection of stats to be added, from oldest to newest.
            start_timestamp (int, optional): The timestamp of the first commit to be considered. Defaults to 1531090905, which is the first commit I have.
            attributes (List[str], optional): The attributes of the Stats class that will be plotted
    """
    start_date = datetime.datetime.fromtimestamp(start_timestamp)
    # Y-Axis
    list_word_counts: List[int] = []
    list_unique_word_counts: List[int] = []
    list_fig_count: List[int] = []
    list_tab_count: List[int] = []
    list_eq_count: List[int] = []
    list_list_count: List[int] = []
    list_latex_comm_count: List[int] = []
    list_latex_env_count: List[int] = []

    # X-axis
    list_dates: List[datetime.datetime] = []
    list_delta: List[datetime.timedelta] = []
    list_deltas_days: List[float] = []

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
        list_list_count.append(stat.listing_count)
        list_latex_comm_count.append(sum(stat.command_Counter.values()))
        list_latex_env_count.append(sum(stat.env_Counter.values()))

    ax_stats.plot(list_deltas_days, list_word_counts, marker="o", label="Words")
    ax_stats.plot(
        list_deltas_days,
        list_unique_word_counts,
        marker="o",
        label="UWords",
    )
    ax_stats.plot(list_deltas_days, list_fig_count, marker="o", label="Figs")
    ax_stats.plot(list_deltas_days, list_eq_count, marker="o", label="Eqs")
    ax_stats.plot(list_deltas_days, list_list_count, marker="o", label="List")
    ax_stats.plot(
        list_deltas_days,
        list_latex_comm_count,
        marker="o",
        label="LComm",
    )
    ax_stats.plot(
        list_deltas_days,
        list_latex_env_count,
        marker="o",
        label="LEnv",
    )
    ax_stats.legend(fontsize=6)
    ax_stats.set(xlabel="Days", ylabel="count")


def test_stats():
    path = pathlib.Path(thesis_path)
    tex_files = glob.glob(str(path / "*.tex"))
    list_of_Stats = []
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
    # st.reduced_word_Counter["NaSal"] = st.reduced_word_Counter["nasal"]
    # st.reduced_word_Counter["nasal"] = 0

    with open("temp_stats.pkl", "wb") as fhand:
        pickle.dump(st, fhand)


def test_wordcloud():
    with open("temp_stats.pkl", "rb") as fhand:
        st = pickle.load(fhand)
    cloud = create_wordcloud(st.reduced_word_Counter, width=580, height=300)
    # fig, ax_text, ax_header, ax_stats, ax_wc, ax_wc_cb = create_frame_with_cb()
    fig, ax_text, ax_header, ax_stats, ax_wc = create_frame()
    wc_im = add_wordcloud(ax_wc, cloud)
    # add_colorbar(wc_im, ax_wc_cb)
    plt.show()


def test_stats_graph():
    files = glob.glob("./stats/*.pkl")
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


def test_stats_graph2():
    files = glob.glob("./stats/*.pkl")
    list_of_Stats = []
    for file in files:
        with open(file, "rb") as fhand:
            st = pickle.load(fhand)
            list_of_Stats.append(st)
    list_of_Stats.sort(key=lambda x: x.date)
    for i, stat in enumerate(list_of_Stats):
        if i + 1 > len(list_of_Stats) - 3:
            continue
        fig, ax_text, ax_header, ax_stats, ax_wc = create_frame()
        add_stats_graph(ax_stats, list_of_Stats[: i + 1])
        ax_stats.set_yscale("log")
        fig.savefig(f"./figs/{i}.jpg", dpi=100)
        plt.close(fig)


def test_header():
    with open("temp_stats.pkl", "rb") as fhand:
        st = pickle.load(fhand)


# test_stats()
# test_wordcloud()
test_stats_graph2()