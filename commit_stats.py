# Used to create stats of a specific commit, such as the number of pages of the
# pdf file, the number of words, number of sections, etc

from config import thesis_path
import os
import glob
import re
from collections import Counter
import pathlib
import pdb


def count_words(text: str) -> int:
    """Counts words in the text, not escaped by \ (i.e., no commands). Will
    count comments and single-letter words also.

        Args:
            text (str): full text

        Returns:
            int: Number of words
    """
    # TODO: process user macros before counting words
    # Ignores everything preceded by \, like \chapter, etc
    word_regex = re.compile(r"(?<!\\)\b\w+\b")
    number_words = len(word_regex.findall(text))
    return number_words


def count_unique_words(text: str) -> int:
    """Removes word duplicates

    Args:
        text (str): Full text

    Returns:
        int: Number of unique words
    """
    word_regex = re.compile(r"(?<!\\)\b\w+\b")
    unique_words = len(set(word_regex.findall(text)))
    return unique_words


def Counter_words(text: str) -> Counter:
    """Creates a dictionary (specifically a collections.Counter) that contains
    the most used words in a string.

        Args:
            text (str): text to count words

        Returns:
            Counter: Counter object with the counts of the words. All lowercase.
    """
    # Regex translation: Find everything not escaped (preceded by \), not
    # preceded by "{", not followed by "}", that's made by word characters (\w)
    # between two word boundaries (\b).
    word_regex = re.compile(r"(?<!\\)(?<!{)\b\w+\b(?!})")
    words = word_regex.findall(text.lower())
    word_counter = Counter(words)
    return word_counter


def count_latex_commands(text: str) -> Counter:
    """Counts the number of \begin \label \index, etc.

    Args:
        text (str): Full text

    Returns:
        Counter: Counter object with the commands
    """
    # Regex translation: Anything that starts with "\"
    latex_command_regex = re.compile(r"\\\w+")
    commands = latex_command_regex.findall(text)
    command_counter = Counter(commands)
    return command_counter


def count_latex_environments(text: str) -> Counter:
    """Counts the number of environments such as \begin{figure}, etc

    Args:
        text (str): Full text

    Returns:
        Counter: Counter object with the environment instances
    """
    # Regex translation: match everything that starts with \begin, then has an
    # optional, noncapturing group composed of anything between [],
    # lazily matched, and then get the environment name proper between {}.
    latex_env_regex = re.compile(r"\\begin(?:\[.*?\])?{(\w+)}")
    envs = latex_env_regex.findall(text)
    env_counter = Counter(envs)
    return env_counter


def count_equations(text: str) -> dict:
    """Counts separately equations in the form of $ ... $ and $$ ... $$, \( ...
    \), \[ ... \], \begin{equation} ... \end{equation}

    Args: text (str): Full text

    Returns: dict: Dict with keys relevant to each type of equation
    """
    # Disabled: Merged two regexes into the one below
    # Regex translation: anything surrounded by "$ ... $", that's at least 1
    # character, and doesn't isn't "$$", which is the line equation
    # old_inline_eq_regex = re.compile(r"\$(?<!\$).+?(?!\$)\$")

    # Disabled: Merged two regexes into the one below
    # Regex translation: anything surrounded by "$$ ... $$" that's at least 1
    # character.
    # old_line_eq_regex = re.compile(r"\$\$.+?\$\$", flags=re.MULTILINE)

    # Regex translation: anything surrounded by "$ ... $" or "$$ ... $$" that's
    # at least 1 character. Will store the middle part for testing (stray $ in
    # the text for example)
    old_eq_regex = re.compile(r"\$?\$(.+?)\$\$?", flags=re.DOTALL)

    # Regex translation: anything surrounded by "\(...\)", that's at least 1
    # character, and doesn't isn't "$$", which is the line equation
    new_inline_eq_regex = re.compile(r"\\\(.+?\\\)")

    ## Regex translation: anything surrounded by "\[ ... \]" that's at least 1 character.
    new_line_eq_regex = re.compile(r"\\\[.*?\\\]", flags=re.DOTALL)

    # Regex translation: any start of equation environment
    equation_env_regex = re.compile(r"\\begin{equation\*?}")

    # Regex translation: any start of subequation environment
    subequation_env_regex = re.compile(r"\\begin{subequation\*?}")

    old_eq_counter = [
        1
        for match in old_eq_regex.finditer(text)  # if len(match.group()) < 500
    ]
    monitor_old_eq_counter = [
        match
        for match in old_eq_regex.finditer(text)
        if len(match.group()) > 250
    ]
    line_eq_counter = [
        1
        for match in new_line_eq_regex.finditer(
            text
        )  # if len(match.group()) < 500
    ]
    inline_eq_counter = [
        1
        for match in new_inline_eq_regex.finditer(
            text
        )  # if len(match.group()) < 500
    ]
    eq_env_counter = [
        1
        for match in equation_env_regex.finditer(
            text
        )  # if len(match.group()) < 500
    ]
    subeq_env_counter = [
        1
        for match in subequation_env_regex.finditer(
            text
        )  # if len(match.group()) < 500
    ]
    return {
        "old Eq": sum(old_eq_counter),
        "New LEq": sum(line_eq_counter),
        "New ILEq": sum(inline_eq_counter),
        "Eq Env": sum(eq_env_counter),
        "SubEq Env": sum(subeq_env_counter),
    }


def count_number_subfigs_figures(text: str) -> Counter:
    figure_env_regex = re.compile(
        r"\\begin{figure\*?}.*?\\end{figure\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    subfigure_env_regex = re.compile(
        r"\\begin{subfigure\*?}.*?\\end{subfigure\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    count_subfigures = []
    # pdb.set_trace()
    for match in figure_env_regex.finditer(text):
        figure_text = match.group()
        num_subfigures = len(subfigure_env_regex.findall(figure_text))
        count_subfigures.append(num_subfigures)
    Count_subfigures = Counter(count_subfigures)
    return Count_subfigures


def remove_comments(text: str) -> str:
    """Removes comments from the text using a simple regex

    Args:
        text (str): The whole text string

    Returns:
        str: Text string removing everything after a %
    """
    # From start of the line, group everything until the first % (lazily), if
    # it is not preceded by \ (i.e. escaped). Then match everything from % to
    # the end of the line.
    comment_regex = re.compile(r"(^.*?)((?<!\\)%.*$)", flags=re.MULTILINE)
    splitted_text = text.split("\n")
    for i, line in enumerate(splitted_text):
        # Not a list comprehension to make debugging easier
        cleaned_line = comment_regex.sub(r"\1", line)
        splitted_text[i] = cleaned_line
    return "\n".join(splitted_text)


def remove_includegraphics(text: str) -> str:
    """Removes a includegraphics command

    Args:
        text (str): Full text

    Returns:
        str: Text without \includegraphics[...]{...}
    """
    # Regex translation: Everything starting with \includegraphics, perhaps
    # having [...], and certainly having {...}. Inside, matches are lazy so it
    # matches something as small as possible.
    includegraphics_regex = re.compile(r"\\includegraphics(\[.*?\])?({.*?})")
    cleaned_text = includegraphics_regex.sub("", text)
    return cleaned_text


def remove_label(text: str) -> str:
    """Removes \label{...} from the text

    Args:
        text (str): Full text

    Returns:
        str: Text without \label{...}
    """
    # Regex translation: Everything that starts with \label and then has {...},
    # with lazy matching.
    label_regex = re.compile(r"\\label({.*?})")
    cleaned_text = label_regex.sub("", text)
    return cleaned_text


def remove_index(text: str) -> str:
    """Removes \index{...} from the text

    Args:
        text (str): Full text

    Returns:
        str: Text without \index{...}
    """
    # Everything that has \index and then {...}
    index_regex = re.compile(r"\\index({.*?})")
    cleaned_text = index_regex.sub("", text)
    return cleaned_text


def remove_citations(text: str) -> str:
    """Removes \cite{...} and \citeauthor{...} from the text

    Args:
        text (str): Full text

    Returns:
        str: Text without \cite{...} and \citeauthor{...}
    """
    cite_regex = re.compile(r"\\cite(author)?({.*?})?")
    cleaned_text = cite_regex.sub("", text)
    return cleaned_text


def remove_inputminted(text: str, language: str = "python") -> str:
    """Removes inputminted{language}{path}, default language is python

    Args:
        text (str): Full text

    Returns:
        str: Text without \inputminted
    """
    cite_regex = re.compile(r"\\inputminted{" + language + r"}{.*?}")
    cleaned_text = cite_regex.sub("", text)
    return cleaned_text


def remove_equation_envs(text: str) -> str:
    """Removes everything inside an equation environment

    Args:
        text (str): Full text

    Returns:
        str: Full text without equation envs
    """
    equation_env_regex = re.compile(
        r"\\begin{equation\*?}.*?\\end{equation\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = equation_env_regex.sub("", text)
    return cleaned_text


def remove_listing_envs(text: str) -> str:
    """Removes everything inside listing environments

    Args:
        text (str): Full text

    Returns:
        str: Full text without listings
    """
    listing_env_regex = re.compile(
        r"\\begin{listing\*?}.*?\\end{listing\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = listing_env_regex.sub("", text)
    return cleaned_text


def remove_subfigure_envs(text: str) -> str:
    """Removes everything inside subfigures

    Args:
        text (str): Full text

    Returns:
        str: Full text without subfigures
    """
    subfigure_env_regex = re.compile(
        r"\\begin{subfigure\*?}.*?\\end{subfigure\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = subfigure_env_regex.sub("", text)
    return cleaned_text


def remove_itemize_envs(text: str) -> str:
    """Removes everything inside itemize environments

    Args:
        text (str): Full text

    Returns:
        str: Full text without itemize
    """
    itemize_env_regex = re.compile(
        r"\\begin{itemize\*?}.*?\\end{itemize\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = itemize_env_regex.sub("", text)
    return cleaned_text


def remove_references(text: str) -> str:
    """Removes autoref and ref from the text

    Args:
        text (str): full text

    Returns:
        str: text without references
    """
    ref_regex = re.compile(r"\\(auto)?ref(\[.*\])?({.*?})?")
    return ref_regex.sub("", text)


def remove_unnumbered_equations(text: str) -> str:
    """Removes $ ... $, $$ ... $$ \( ... \), \[ ... \] from the text

    Args:
        text (str): Full text

    Returns:
        str: Text without the equations
    """
    # Regex translation: anything surrounded by "$ ... $" or "$$ ... $$" that's
    # at least 1 character. Will store the middle part for testing (stray $ in
    # the text for example)
    old_eq_regex = re.compile(r"\$?\$(.+?)\$\$?", flags=re.DOTALL)

    # Regex translation: anything surrounded by "\(...\)", that's at least 1
    # character, and doesn't isn't "$$", which is the line equation
    new_inline_eq_regex = re.compile(r"\\\(.+?\\\)")

    ## Regex translation: anything surrounded by "\[ ... \]" that's at least 1 character.
    new_line_eq_regex = re.compile(r"\\\[.*?\\\]", flags=re.DOTALL)

    # Removing regexes
    first_pass = old_eq_regex.sub("", text)
    second_pass = new_inline_eq_regex.sub("", first_pass)
    third_pass = new_line_eq_regex.sub("", second_pass)
    return third_pass


def remove_enumerate_envs(text: str) -> str:
    """Removes everything inside an enumerate environment

    Args:
        text (str): Full text

    Returns:
        str: Text without enumerates
    """
    enumerate_env_regex = re.compile(
        r"\\begin{enumerate\*?}.*?\\end{enumerate\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = enumerate_env_regex.sub("", text)
    return cleaned_text


def open_file(filepath: str) -> str:
    """Opens a file and returns the text inside

    Args:
        filepath (pathlib path or str): Path to file

    Returns:
        str: contents
    """
    text = open(filepath, "r", encoding="utf8").read()
    return text


def remove_common_words(counter: Counter) -> Counter:
    """Removes common words (stopwords) from the word Counter object.

    Args:
        counter (Counter): collections.Counter object

    Returns:
        Counter: A copy of the provided counter without the stopwords.
    """
    try:
        import nltk
    except ModuleNotFoundError:
        print("Please install nltk")
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords")

    stopwords = nltk.corpus.stopwords.words("portuguese")
    counter = counter.copy()
    for word in stopwords:
        del counter[word]
    return counter


def save_text(filename: str, annotation: str, text: str, restart=False) -> None:
    if not os.path.isfile(filename):
        mode = "w"
    else:
        mode = "a"
    if restart:
        mode = "w"
    with open(filename, mode) as fhand:
        fhand.write("-" * 80 + "\n")
        fhand.write(annotation.center(80) + "\n")
        fhand.write("-" * 80 + "\n")
        fhand.write(text)


def calculate_stats(file):
    original_text = open_file(file)
    basename = os.path.basename(file)
    debug = True

    if debug:
        save_text(
            basename + "-test.txt", "original", original_text, restart=True
        )
    text_wo_comm = remove_comments(original_text)
    if debug:
        save_text(basename + "-test.txt", "wo comments", text_wo_comm)

    # Calculate the stats related to Latex commands
    latex_comm_count = count_latex_commands(text_wo_comm)
    latex_env_count = count_latex_environments(text_wo_comm)
    eq_count = count_equations(text_wo_comm)
    subfigure_counts = count_number_subfigs_figures(text_wo_comm)
    part_count = latex_comm_count[r"\part"]
    chapter_count = latex_comm_count[r"\chapter"]
    section_count = latex_comm_count[r"\section"]
    subsection_count = latex_comm_count[r"\subsection"]
    subsubsection_count = latex_comm_count[r"\subsubsection"]
    page_cross_references = latex_comm_count[r"\pageref"]
    fig_tab_list_cross_references = (
        latex_comm_count[r"\autoref"] + latex_comm_count[r"\ref"]
    )
    includegraphic_count = latex_comm_count[r"\includegraphics"]
    intputminted_count = latex_comm_count[r"\inputminted"]
    citation_counts = (
        latex_comm_count[r"\citeauthor"] + latex_comm_count[r"\cite"]
    )
    index_count = latex_comm_count[r"\index"]
    footnote_count = latex_comm_count[r"\footnote"]

    # Cleaning the text to count words better
    # Saving the intermediate steps is to work out any inadequate regex
    # substitutions.
    cleaned_text = remove_includegraphics(text_wo_comm)
    if debug:
        save_text(basename + "-test.txt", "wo includegraphics", cleaned_text)
    cleaned_text = remove_label(cleaned_text)
    if debug:
        save_text(basename + "-test.txt", "wo label", cleaned_text)
    cleaned_text = remove_index(cleaned_text)
    if debug:
        save_text(basename + "-test.txt", "wo index", cleaned_text)
    cleaned_text = remove_citations(cleaned_text)
    if debug:
        save_text(basename + "-test.txt", "wo cite", cleaned_text)
    cleaned_text = remove_references(cleaned_text)
    if debug:
        save_text(basename + "-test.txt", "wo refs", cleaned_text)
    cleaned_text = remove_unnumbered_equations(cleaned_text)
    if debug:
        save_text(basename + "-test.txt", "wo unnum eq", cleaned_text)
    cleaned_text = remove_equation_envs(cleaned_text)
    if debug:
        save_text(basename + "-test.txt", "wo eq envs", cleaned_text)
    cleaned_text = remove_inputminted(cleaned_text)
    if debug:
        save_text(basename + "-test.txt", "wo inputminted", cleaned_text)
    cleaned_text = remove_subfigure_envs(cleaned_text)
    if debug:
        save_text(basename + "-test.txt", "wo subfigs", cleaned_text)
    # cleaned_text = remove_itemize(cleaned_text)
    # cleaned_text = remove_enumerate(cleaned_text)

    # Start to create word counters
    # Basic word count
    word_count = count_words(cleaned_text)
    # Removes duplicated words
    unique_word_count = count_unique_words(cleaned_text)
    # Creates a Counter object of words, naively
    word_Counter = Counter_words(cleaned_text)
    # Removes the stopping words/common words, with only "interesting" words
    # remaining
    int_word_Counter = remove_common_words(word_Counter)
    # Create stats text
    chapter_count = latex_comm_count[r"\chapter"]
    part_count = latex_comm_count[r"\part"]
    section_count = latex_comm_count[r"\section"]
    subsection_count = latex_comm_count[r"\subsection"]
    subsubsection_count = latex_comm_count[r"\subsubsection"]
    stats = (
        f"word count: {word_count} \n"
        f"unique word count {unique_word_count}\n"
        f"parts: {part_count} \n"
        f"chapters: {chapter_count} \n"
        f"sections: {section_count} \n"
        f"subsections: {subsection_count} \n"
        f"subsubsections: {subsubsection_count} \n"
        f"page cross references: {page_cross_references} \n"
        f"figure/table/listing cross references: {fig_tab_list_cross_references} \n"
        f"figures: {latex_env_count['figure']}\n"
        f"subfigures: {latex_env_count['subfigure']}\n"
        f"subfigures in figures: {subfigure_counts}\n"
        f"includegraphics: {includegraphic_count}\n"
        f"equations: {eq_count['New LEq'] + eq_count['Eq Env']}\n"
        f"listings: {latex_env_count['listing']}\n"
        f"intputminteds: {intputminted_count}\n"
        f"tables: {latex_env_count['IBGEtab']}\n"
        f"citations: {citation_counts} \n"
        f"index entries: {index_count} \n"
        f"footnotes: {footnote_count} \n"
        f"latex commands: {latex_comm_count}\n"
        f"latex environments: {latex_env_count}\n"
        f"word_counter: \n {word_Counter.most_common(50)} \n"
        f"better word counter: \n {int_word_Counter.most_common(50)} \n"
    )
    save_text(
        f"Stats for {basename}.txt",
        f"Stats for {basename}",
        stats,
        restart=True,
    )


def main():
    path = pathlib.Path(thesis_path)
    tex_files = glob.glob(str(path / "*.tex"))
    for file in tex_files:
        calculate_stats(file)


if __name__ == "__main__":
    main()


def test():
    path = pathlib.Path(thesis_path)
    concl = path / "conclusoes_finais.tex"
    # concl = "/home/kjc/Repos/Tese/conclusoes_finais.tex"
    text = open_file(concl)
    # print(text)
    print(
        count_words(text),
        count_unique_words(text),
        Counter_words(text).most_common(5),
        remove_common_words(Counter_words(text)).most_common(20),
        sep="\n",
    )


def test2():
    path = pathlib.Path(thesis_path)
    files = glob.glob(str(path / "*.tex"))
    for file in files:
        text = open_file(file)
        text = remove_comments(text)
        print("-" * 20)
        print(f"{file}".center(20))
        print("-" * 20)
        print(
            f"Número de palavras {count_words(text)}",
            f"Número de palavras únicas {count_unique_words(text)}",
            # create_Counter_obj(text).most_common(5),
            f"Palavras mais comuns {remove_common_words(Counter_words(text)).most_common(20)}",
            sep="\n",
        )


def test3():
    path = pathlib.Path(thesis_path)
    files = glob.glob(str(path / "*.tex"))
    fulltext = ""
    for file in files:
        text = open_file(file)
        text = remove_comments(text)
        fulltext += text
    latex_commands = count_latex_commands(fulltext)
    latex_envs = count_latex_environments(fulltext)
    print(latex_commands)
    print(latex_envs)
    with open("latex_commands.txt", "w") as fhand:
        for key, value in sorted(
            latex_commands.items(), key=lambda x: x[1], reverse=True
        ):
            fhand.write(key + ";" + str(value) + "\n")
    with open("latex_envs.txt", "w") as fhand:
        for key, value in sorted(
            latex_envs.items(), key=lambda x: x[1], reverse=True
        ):
            fhand.write(key + ";" + str(value) + "\n")
    return latex_commands, latex_envs


def test4():
    path = pathlib.Path(thesis_path)
    files = glob.glob(str(path / "*.tex"))
    for file in files:
        text = open_file(file)
        text = remove_comments(text)
        eqs = count_equations(text)
        print("-" * 20)
        print(f"{file}".center(20))
        print("-" * 20)
        print(eqs)


# test2()
# test3()
# test4()