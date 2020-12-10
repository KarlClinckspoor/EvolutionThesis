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


def remove_comments(text: str) -> str:
    """Removes comments from the text using a simple regex

    Args:
        text (str): The whole text string

    Returns:
        str: Text string removing everything after a %
    """
    # From start of the line, select everything until the first % (lazily), if
    # it is not preceded by \ (i.e. escaped). Then group everything from % to
    # the end of the line.
    comment_regex = re.compile(r"(^.*?)((?<!\\)%.*$)")
    splitted_text = text.split("\n")
    for i, line in enumerate(splitted_text):
        # Not a list comprehension to make debugging easier
        cleaned_line = comment_regex.sub("\1", line)
        splitted_text[i] = cleaned_line
    return "\n".join(splitted_text)


def remove_includegraphics(text: str) -> str:
    # TODO
    pass


def remove_labels(text: str) -> str:
    # TODO
    pass


def remove_index(text: str) -> str:
    # TODO
    pass


def remove_equation_envs(text: str) -> str:
    # TODO
    equation_env_regex = re.compile(r"\\begin{equation}.*\\end{equation}")
    equation_env_regex2 = re.compile(r"\\begin{equation*}.*\\end{equation*}")


def remove_citations(text: str) -> str:
    # TODO
    pass


def remove_unnumbered_equations(text: str) -> str:
    # TODO
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


test2()