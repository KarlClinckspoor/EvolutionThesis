# Used to create stats of a specific commit, such as the number of pages of the
# pdf file, the number of words, number of sections, etc

from config import thesis_path
import glob
import re
from collections import Counter
import pathlib


def count_words(text):
    # TODO: process user macros before counting words
    # Ignores everything preceded by \, like \chapter, etc
    word_regex = re.compile(r"(?<!\\)\b\w+\b")
    number_words = len(word_regex.findall(text))
    return number_words


def count_unique_words(text):
    word_regex = re.compile(r"(?<!\\)\b\w+\b")
    unique_words = len(set(word_regex.findall(text)))
    return unique_words


def create_Counter_obj(text: str) -> Counter:
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
        "old Eq": old_eq_counter,
        "New LEq": line_eq_counter,
        "New ILEq": inline_eq_counter,
        "Eq Env": eq_env_counter,
        "SubEq Env": subeq_env_counter,
    }


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
        cleaned_line = comment_regex.sub("\1", line)
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


def remove_cite(text: str) -> str:
    """Removes \cite{...} and \citeauthor{...} from the text

    Args:
        text (str): Full text

    Returns:
        str: Text without \cite{...} and \citeauthor{...}
    """
    cite_regex = re.compile(r"\\cite(author)?({.*?})?")
    cleaned_text = cite_regex.sub("", text)
    return cleaned_text


def remove_equation_envs(text: str) -> str:
    equation_env_regex = re.compile(
        r"\\begin{equation\*?}.*?\\end{equation\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = equation_env_regex.sub("", text)
    return cleaned_text


def remove_subfigures(text: str) -> str:
    subfigure_env_regex = re.compile(
        r"\\begin{subfigure\*?}.*?\\end{subfigure\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = subfigure_env_regex.sub("", text)
    return cleaned_text


def remove_itemize(text: str) -> str:
    itemize_env_regex = re.compile(
        r"\\begin{itemize\*?}.*?\\end{itemize\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = itemize_env_regex.sub("", text)
    return cleaned_text


def remove_enumerate(text: str) -> str:
    enumerate_env_regex = re.compile(
        r"\\begin{enumerate\*?}.*?\\end{enumerate\*?}",
        flags=re.MULTILINE | re.DOTALL,
    )
    cleaned_text = enumerate_env_regex.sub("", text)
    return cleaned_text


def remove_references(text: str) -> str:
    ref_regex = re.compile(r"\\(auto)?ref(\[.*\])?({.*})?")
    citeauthor_regex = re.compile(r"\\citeauthor(\[.*\])?({.*})?")
    temp_text = cite_regex.sub("", text)
    cleaned_text = citeauthor_regex.sub("", temp_text)
    return cleaned_text


def remove_unnumbered_equations(text: str) -> str:
    # Regex translation: anything surrounded by "$ ... $", that's at least 1
    # character, and doesn't isn't "$$", which is the line equation
    old_inline_eq_regex = re.compile(r"\$(?<!\$).+?(?!\$)\$")
    # Regex translation: anything surrounded by "\(...\)", that's at least 1
    # character, and doesn't isn't "$$", which is the line equation
    new_inline_eq_regex = re.compile(r"\\\(.+?\\\)")
    # Regex translation: anything surrounded by "$$ ... $$" that's at least 1
    # character.
    old_line_eq_regex = re.compile(r"\$\$.+?\$\$")
    ## Regex translation: anything surrounded by "\[ ... \]" that's at least 1 character.
    new_line_eq_regex = re.compile(r"\\\[.*?\\\]")


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


def test():
    path = pathlib.Path(thesis_path)
    concl = path / "conclusoes_finais.tex"
    # concl = "/home/kjc/Repos/Tese/conclusoes_finais.tex"
    text = open_file(concl)
    # print(text)
    print(
        count_words(text),
        count_unique_words(text),
        create_Counter_obj(text).most_common(5),
        remove_common_words(create_Counter_obj(text)).most_common(20),
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
            f"Palavras mais comuns {remove_common_words(create_Counter_obj(text)).most_common(20)}",
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


# test2()
test3()