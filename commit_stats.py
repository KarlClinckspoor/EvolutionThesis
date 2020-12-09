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


def counter_words(text: str) -> Counter:
    """Creates a dictionary (specifically a collections.Counter) that contains
    the most used words in a string.

        Args:
            text (str): text to count words

        Returns:
            Counter: Counter object with the counts of the words. All lowercase.
    """
    # TODO: add restrictions to regex to remove {figure} and similar things.
    word_regex = re.compile(r"(?<!\\)\b\w+\b")
    words = word_regex.findall(text.lower())
    word_counter = Counter(words)
    return word_counter


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
        counter_words(text).most_common(5),
        remove_common_words(counter_words(text)).most_common(20),
        sep="\n",
    )


def test2():
    path = pathlib.Path(thesis_path)
    files = glob.glob(str(path / "*.tex"))
    for file in files:
        text = open_file(file)
        print("-" * 20)
        print(f"{file}".center(20))
        print("-" * 20)
        print(
            f"Número de palavras {count_words(text)}",
            f"Número de palavras únicas {count_unique_words(text)}",
            # counter_words(text).most_common(5),
            f"Palavras mais comuns {remove_common_words(counter_words(text)).most_common(20)}",
            sep="\n",
        )


test2()