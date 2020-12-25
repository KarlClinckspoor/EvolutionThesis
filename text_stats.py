# Used to create stats of a specific commit, such as the number of pages of the
# pdf file, the number of words, number of sections, etc

from config import thesis_path, stats_basepath
import os
import glob
import re
from collections import Counter, namedtuple
import pathlib
import pdb
from typing import Union
import pandas as pd
import pickle

try:
    import nltk
except ModuleNotFoundError:
    print("Please install nltk")
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")
try:
    from nltk.stem import rslp
except LookupError:
    nltk.download("rslp")
try:
    from nltk.stem.snowball import SnowballStemmer
except LookupError:
    nltk.download("snowball_data")


def open_file(filepath: Union[str, pathlib.Path]) -> str:
    """Opens a file"""
    text = open(str(filepath), "r", encoding="utf8").read()
    return text


# TODO: is this a good way of implementing the class? I think I need some
# decorators, getters and setters
class Stats:
    debug = False

    def __init__(
        self,
        name: str,
        text: str,
        date: str = "00000000",
        description: str = "nothing",
        commit_hash: str = "nothing",
        output_path: str = ".",
        debug_output_path: str = ".",
        number_most_common: int = 50,
    ):
        """Creates an instance of a Stats class. To calculate, need to run
        calculate_stats, to save as a text file, need to run save_as_text, to
        save as a table, need to run save_as_csv.

                Args:
                    filename (str): File name
                    text (str): contents of the file
                    date (str): date in a parseable format by datetime
                    description (str): brief description (like commit info)
                    commit_hash (str): sha1 hash of the commit
                    output_path (str): folder where the files will be stored
                    debug_output_path (str): folder where the debug documents will be stored.
                    number_most_common (int): number of most common items to be included in the Counters
        """
        self.name = name
        self.text = text
        self.original_text = self.text[:]
        self.output_path = pathlib.Path(output_path)
        self.debug_output_path = pathlib.Path(debug_output_path)
        self.description = description
        self.commit_hash = commit_hash
        self.number_most_common = number_most_common
        self.date = date

    def tokenize_text(self) -> None:
        """Creates a long list of all the words in the text, excluding any latex
        commands, and not cleaned"""
        word_regex = re.compile(r"(?<!\\)(?<!{)\b\w+\b(?!})")
        self.tokens = word_regex.findall(self.text.lower())

    def create_unique_tokens(self) -> None:
        """Uses the tokens available to create a set of unique tokens"""
        self.unique_tokens = list(set(self.tokens))

    def count_words(self):
        """Counts words in the text, not escaped by \ (i.e., no commands). Will
        count comments and single-letter words also, so be careful"""
        # Regex Translation: Ignores everything preceded by \, like \chapter,
        # etc
        self.word_count = len(self.tokens)

    def count_unique_words(self) -> None:
        """Don't consider repeated words"""
        self.unique_word_count = len(self.unique_tokens)

    def Counter_words(self) -> None:
        """Creates a dictionary (specifically a collections.Counter) that
        contains the most used words in the text, but all lowercase
        """
        self.word_Counter = Counter(self.tokens)

    def stemmatize_words(self) -> None:
        """Get the stems of words using RSLP Stemmer"""
        stemmer = rslp.RSLPStemmer()
        self.stems = [stemmer.stem(word) for word in self.tokens]
        self.unique_stems = list(
            set([stemmer.stem(word) for word in self.unique_tokens])
        )

    def stemmatize_nonstopping_words(self) -> None:
        """Get the stems of nonstopping words using RSLP"""
        stemmer = rslp.RSLPStemmer()
        self.nonstopping_stems = [
            stemmer.stem(word) for word in self.reduced_tokens
        ]
        self.unique_nonstopping_stems = list(set(self.nonstopping_stems))

    def stemmatize_words_(self) -> None:
        """Get the stems of words using SnowballStemmer"""

        stemmer = SnowballStemmer("portuguese")
        self.stems = [stemmer.stem(word) for word in self.tokens]
        self.unique_stems = list(
            set([stemmer.stem(word) for word in self.unique_tokens])
        )

    def stemmatize_nonstopping_words_(self) -> None:
        """Get the stems of nonstopping words using SnowballStemmer"""
        stemmer = SnowballStemmer("portuguese")
        self.nonstopping_stems = [
            stemmer.stem(word) for word in self.reduced_tokens
        ]
        self.unique_nonstopping_stems = list(set(self.nonstopping_stems))

    def Counter_stems(self) -> None:
        self.stem_Counter = Counter(self.stems)

    def Counter_nonstopping_stems(self) -> None:
        """Creates Counter object of the nonstopping stems"""
        self.nonstopping_stem_Counter = Counter(self.nonstopping_stems)

    def count_equations(self) -> None:
        """Counts separately equations in the form of $ ... $ and $$ ... $$, \( ...
        \), \[ ... \], \begin{equation} ... \end{equation}"""
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
        old_eq_regex = re.compile(r"\$?\$(?:.+?)\$\$?", flags=re.DOTALL)

        # Regex translation: anything surrounded by "\(...\)", that's at least 1
        # character, and doesn't isn't "$$", which is the line equation
        new_inline_eq_regex = re.compile(r"\\\(.+?\\\)")

        ## Regex translation: anything surrounded by "\[ ... \]" that's at least 1 character.
        new_display_eq_regex = re.compile(r"\\\[.*?\\\]", flags=re.DOTALL)

        # Regex translation: any start of equation environment
        equation_env_regex = re.compile(r"\\begin{equation\*?}")

        # Regex translation: any start of subequation environment
        subequation_env_regex = re.compile(r"\\begin{subequation\*?}")

        self.old_eq_count = len(old_eq_regex.findall(self.text))
        self._old_eq_count_DEBUG = [
            match
            for match in old_eq_regex.finditer(self.text)
            if len(match.group()) > 250
        ]
        if self._old_eq_count_DEBUG:
            print("CHECK old eq counter!")
        self.display_eq_count = len(new_display_eq_regex.findall(self.text))
        self.inline_eq_count = len(new_inline_eq_regex.findall(self.text))
        self.eq_env_count = len(equation_env_regex.findall(self.text))
        self.subeq_env_count = len(subequation_env_regex.findall(self.text))

    def Counter_latex_commands(self) -> None:
        """Counts the number of \begin \label \index, etc. """
        # Regex translation: Anything that starts with "\"
        latex_command_regex = re.compile(r"\\\w+")
        commands = latex_command_regex.findall(self.text)
        self.command_Counter = Counter(commands)

    def Counter_latex_environments(self) -> None:
        """Counts the number of environments such as \begin{figure}, etc """
        # Regex translation: match everything that starts with \begin, then has an
        # optional, noncapturing group composed of anything between [],
        # lazily matched, and then get the environment name proper between {}.
        latex_env_regex = re.compile(r"\\begin(?:\[.*?\])?{(\w+)}")
        envs = latex_env_regex.findall(self.text)
        self.env_Counter = Counter(envs)

    def Counter_number_subfigs_figures(self) -> None:
        """Adds a collections.Counter object that states how many figures with n
        subfigures there are. For example, if all n figures have no subfigures,
        then it's Counter({0: n})
        """
        figure_env_regex = re.compile(
            r"\\begin{figure\*?}.*?\\end{figure\*?}",
            flags=re.MULTILINE | re.DOTALL,
        )
        subfigure_env_regex = re.compile(
            r"\\begin{subfigure\*?}.*?\\end{subfigure\*?}",
            flags=re.MULTILINE | re.DOTALL,
        )
        count_subfigures = []
        for match in figure_env_regex.finditer(self.text):
            figure_text = match.group()
            num_subfigures = len(subfigure_env_regex.findall(figure_text))
            count_subfigures.append(num_subfigures)
        self.subfigures_in_figures_Counter = Counter(count_subfigures)

    def Counter_references(self) -> None:
        """Creates a Counter object of all the references used in \cite and \citeauthor"""
        cite_regex = re.compile(r"\\cite(?:author)?({.*?})?")
        self.references_Counter = cite_regex.findall(self.text)

    def remove_comments(self) -> None:
        """Removes comments from the text using a simple regex """
        # From start of the line, group everything until the first % (lazily), if
        # it is not preceded by \ (i.e. escaped). Then match everything from % to
        # the end of the line.
        comment_regex = re.compile(r"(^.*?)((?<!\\)%.*$)", flags=re.MULTILINE)
        splitted_text = self.text.split("\n")
        for i, line in enumerate(splitted_text):
            # Not a list comprehension to make debugging easier
            cleaned_line = comment_regex.sub(r"\1", line)
            splitted_text[i] = cleaned_line
        self.text = "\n".join(splitted_text)

    def remove_includegraphics(self) -> None:
        """Removes a includegraphics command"""
        # Regex translation: Everything starting with \includegraphics, perhaps
        # having [...], and certainly having {...}. Inside, matches are lazy so it
        # matches something as small as possible.
        includegraphics_regex = re.compile(
            r"\\includegraphics(\[.*?\])?({.*?})"
        )
        self.text = includegraphics_regex.sub("", self.text)

    def remove_label(self) -> None:
        """Removes \label{...} from the text """
        # Regex translation: Everything that starts with \label and then has
        # {...}, with lazy matching.
        label_regex = re.compile(r"\\label({.*?})")
        self.text = label_regex.sub("", self.text)

    def remove_index(self) -> None:
        """Removes \index{...} from the text """
        # Everything that has \index and then {...}
        index_regex = re.compile(r"\\index({.*?})")
        self.text = index_regex.sub("", self.text)

    def remove_citations(self) -> None:
        """Removes \cite{...} and \citeauthor{...} from the text"""
        cite_regex = re.compile(r"\\cite(author)?({.*?})?")
        self.text = cite_regex.sub("", self.text)

    def remove_inputminted(self, language: str = "python") -> None:
        """Removes inputminted{language}{path}, default language is python """
        cite_regex = re.compile(r"\\inputminted{" + language + r"}{.*?}")
        self.text = cite_regex.sub("", self.text)

    def remove_equation_envs(self) -> None:
        """Removes everything inside an equation environment """
        equation_env_regex = re.compile(
            r"\\begin{equation\*?}.*?\\end{equation\*?}",
            flags=re.MULTILINE | re.DOTALL,
        )
        self.text = equation_env_regex.sub("", self.text)

    def remove_listing_envs(self) -> None:
        """Removes everything inside listing environments"""
        listing_env_regex = re.compile(
            r"\\begin{listing\*?}.*?\\end{listing\*?}",
            flags=re.MULTILINE | re.DOTALL,
        )
        self.text = listing_env_regex.sub("", self.text)

    def remove_subfigure_envs(self) -> None:
        """Removes everything inside subfigures"""
        subfigure_env_regex = re.compile(
            r"\\begin{subfigure\*?}.*?\\end{subfigure\*?}",
            flags=re.MULTILINE | re.DOTALL,
        )
        self.text = subfigure_env_regex.sub("", self.text)

    def remove_itemize_envs(self) -> None:
        """Removes everything inside itemize environments """
        itemize_env_regex = re.compile(
            r"\\begin{itemize\*?}.*?\\end{itemize\*?}",
            flags=re.MULTILINE | re.DOTALL,
        )
        self.text = itemize_env_regex.sub("", self.text)

    def remove_references(self) -> None:
        """Removes autoref and ref from the text """
        ref_regex = re.compile(r"\\(auto)?ref(\[.*\])?({.*?})?")
        self.text = ref_regex.sub("", self.text)

    def remove_unnumbered_equations(self) -> None:
        """Removes $ ... $, $$ ... $$ \( ... \), \[ ... \] from the text """
        # Regex translation: anything surrounded by "$ ... $" or "$$ ... $$"
        # that's at least 1 character. Will store the middle part for testing
        # (stray $ in the text for example)
        old_eq_regex = re.compile(r"\$?\$(.+?)\$\$?", flags=re.DOTALL)

        # Regex translation: anything surrounded by "\(...\)", that's at least 1
        # character, and doesn't isn't "$$", which is the line equation
        new_inline_eq_regex = re.compile(r"\\\(.+?\\\)")

        # Regex translation: anything surrounded by "\[ ... \]" that's at least
        # 1 character.
        new_line_eq_regex = re.compile(r"\\\[.*?\\\]", flags=re.DOTALL)

        # Removing regexes
        first_pass = old_eq_regex.sub("", self.text)
        second_pass = new_inline_eq_regex.sub("", first_pass)
        third_pass = new_line_eq_regex.sub("", second_pass)
        self.text = third_pass

    def remove_enumerate_envs(self) -> None:
        """Removes everything inside an enumerate environment"""
        enumerate_env_regex = re.compile(
            r"\\begin{enumerate\*?}.*?\\end{enumerate\*?}",
            flags=re.MULTILINE | re.DOTALL,
        )
        self.text = enumerate_env_regex.sub("", self.text)

    def remove_common_words(self) -> None:
        """Removes common words (stopwords) from the word Counter object. """

        stopwords = nltk.corpus.stopwords.words("portuguese")
        self.reduced_tokens = [
            word for word in self.tokens if word not in stopwords
        ]
        self.reduced_word_Counter = Counter(self.reduced_tokens)

    def remove_words_with_numerals(self) -> None:
        """Removes words that contain numerals"""
        self.tokens = [word for word in self.tokens if word.isalpha()]
        # for i, word in enumerate(self.tokens):
        #     if not word.isalpha():
        #         self.tokens.remove(word)

    def remove_single_letter_words(self) -> None:
        """Removes words with length 1, but which aren't articles (a, e, o)"""
        acceptable_1_letter_words = ["a", "e", "o", "é", "á", "à", "ó"]
        self.tokens = [
            word
            for word in self.tokens
            if (
                (
                    (len(word) == 1)
                    and (word in acceptable_1_letter_words)
                    or len(word) > 1
                )
            )
        ]

    def calculate_stats(self) -> None:
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "original",
                self.original_text,
                restart=True,
            )

        # First step is to remove comments, since they don't count
        self.remove_comments()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo comments",
                self.text,
            )

        # For preservation
        self.text_wo_comments = self.text[:]

        # Calculate stats based on latex commands, so things like equations,
        # cross references, etc.
        self.Counter_latex_commands()
        self.Counter_latex_environments()
        self.Counter_number_subfigs_figures()
        self.Counter_references()
        self.count_equations()
        self.part_count = self.command_Counter[r"\part"]
        self.chapter_count = self.command_Counter[r"\chapter"]
        self.section_count = self.command_Counter[r"\section"]
        self.subsection_count = self.command_Counter[r"\subsection"]
        self.subsubsection_count = self.command_Counter[r"\subsubsection"]
        self.page_crossref = self.command_Counter[r"\pageref"]
        self.other_crossref = (
            self.command_Counter[r"\autoref"] + self.command_Counter[r"\ref"]
        )
        self.figure_count = self.env_Counter["figure"]
        self.subfigure_count = self.env_Counter["subfigure"]
        self.equation_counts = self.eq_env_count + self.display_eq_count
        self.listing_count = self.env_Counter["listing"]
        self.table_count = self.env_Counter["table"]
        self.includegraphics_count = self.command_Counter[r"\includegraphics"]
        self.inputminted = self.command_Counter[r"\inputminted"]
        self.citation_counts = (
            self.command_Counter[r"\citeauthor"]
            + self.command_Counter[r"\cite"]
        )
        self.index_count = self.command_Counter[r"\index"]
        self.footnote_count = self.command_Counter[r"\footnote"]

        # Counting words
        # Text needs to be cleaned
        self.remove_includegraphics()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo includegraphics",
                self.text,
            )
        self.remove_label()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo label",
                self.text,
            )
        self.remove_index()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo index",
                self.text,
            )
        self.remove_citations()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo cite",
                self.text,
            )
        self.remove_references()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo refs",
                self.text,
            )
        self.remove_unnumbered_equations()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo unnum eq",
                self.text,
            )
        self.remove_equation_envs()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo eq envs",
                self.text,
            )
        self.remove_inputminted()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo inputminted",
                self.text,
            )
        self.remove_subfigure_envs()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path / (self.name + "-test.txt"),
                "wo subfigs",
                self.text,
            )

        # Tokenize text (split into words)
        self.tokenize_text()
        # Remove words with numbers
        self.remove_words_with_numerals()
        # Remove single letter words that are not articles (like "c" in tabular
        # envs)
        self.remove_single_letter_words()
        # Create a unique set of words
        self.create_unique_tokens()
        # Count number of words
        self.count_words()
        # Of these, how many are unique?
        self.count_unique_words()
        # Rank the words by usage
        self.Counter_words()
        # Remove stopping words
        self.remove_common_words()
        # Stemmatize words
        self.stemmatize_words_()
        # Stemmatize nonstopping words
        self.stemmatize_nonstopping_words_()
        # Count stems
        self.Counter_stems()
        # Count nonstopping stems
        self.Counter_nonstopping_stems()

    def __str__(self) -> str:
        self.stats_text = (
            f"Stats for {self.name} - commit {self.commit_hash} - description - {self.description} - date {self.date}\n"
            f"word count: {self.word_count} \n"
            f"unique word count {self.unique_word_count}\n"
            f"stem count {len(self.stems)}\n"
            f"unique stem count {len(self.unique_stems)}\n"
            f"--- Sectioning of the text --- \n"
            f"parts: {self.part_count} \n"
            f"chapters: {self.chapter_count} \n"
            f"sections: {self.section_count} \n"
            f"subsections: {self.subsection_count} \n"
            f"subsubsections: {self.subsubsection_count} \n"
            f"--- Referencing --- \n"
            f"page cross references: {self.page_crossref} \n"
            f"figure/table/listing cross references: {self.other_crossref} \n"
            f"--- Floats --- \n"
            f"figures: {self.figure_count}\n"
            f"subfigures: {self.subfigure_count}\n"
            f"subfigures in figures: {self.subfigures_in_figures_Counter}\n"
            f"includegraphics: {self.includegraphics_count}\n"
            f"equations: {self.equation_counts}\n"
            f"listings: {self.listing_count}\n"
            f"intputminted: {self.inputminted}\n"
            f"tables: {self.table_count}\n"
            f"--- Bibliographic stuff ---\n"
            f"citations: {self.citation_counts} \n"
            f"index entries: {self.index_count} \n"
            f"footnotes: {self.footnote_count} \n"
            f"Usage of references: \n {self.references_Counter} \n"
            f"--- LaTeX stuff --- \n"
            f"count of latex commands: {sum(self.command_Counter.values())}\n"
            f"latex commands: {self.command_Counter}\n"
            f"count of latex environments: {sum(self.env_Counter.values())}\n"
            f"latex environments: {self.env_Counter}\n"
            f"--- Most common words --- \n"
            f"most common words: \n {self.word_Counter.most_common(self.number_most_common)} \n"
            f"most common interesting words: \n {self.reduced_word_Counter.most_common(self.number_most_common)} \n"
            f"most common stems: \n {self.stem_Counter.most_common(self.number_most_common)} \n"
            f"most common nonstopping stems: \n {self.nonstopping_stem_Counter.most_common(self.number_most_common)} \n"
        )
        return self.stats_text

    def save_as_text(self) -> None:
        with open(
            self.output_path
            / ("Stats for " + self.name + self.commit_hash + ".txt"),
            "w",
        ) as fhand:
            fhand.write(self.__str__())

    def pickle(self) -> None:
        with open(
            self.output_path / (self.name + "-" + self.commit_hash + ".pkl"),
            "wb",
        ) as fhand:
            pickle.dump(self, fhand)

    def _save_intermediary_text(
        self, filename, annotation: str, text: str, restart=False
    ) -> None:
        if not os.path.isfile(filename):
            mode = "w"
        else:
            mode = "a"
        if restart:
            mode = "w"
        with open(str(filename), mode) as fhand:
            fhand.write("-" * 80 + "\n")
            fhand.write(annotation.center(80) + "\n")
            fhand.write("-" * 80 + "\n")
            fhand.write(text)

    def save_as_csv(self) -> None:
        """Converts object into a series then saves it as a csv file. Note: If
        you want to recover the Counter objects, an eval might work!
        """
        self.to_Series()
        self.series.to_csv(self.output_path / (self.name + ".csv"))

    def to_Series(self) -> pd.Series:
        """Converts the class into a pandas Series object.

        Returns:
            pd.Series: Class converted into a Series object
        """
        data_dict = dict(
            filename=self.name,
            commit_hash=self.commit_hash,
            description=self.description,
            date=self.date,
            word_count=self.word_count,
            unique_word_count=self.unique_word_count,
            stem_count=len(self.stems),
            unique_stem_count=len(self.unique_stems),
            #       --- Sectioning of the text --- ,
            parts=self.part_count,
            chapters=self.chapter_count,
            sections=self.section_count,
            subsections=self.subsection_count,
            subsubsections=self.subsubsection_count,
            #            --- Referencing --- ,
            page_cross_references=self.page_crossref,
            figure_table_listing_cross_references=self.other_crossref,
            #            --- Floats --- ,
            figures=self.figure_count,
            subfigures=self.subfigure_count,
            subfigures_in_figures=self.subfigures_in_figures_Counter,
            includegraphics=self.includegraphics_count,
            equations=self.equation_counts,
            listings=self.listing_count,
            intputminted=self.inputminted,
            tables=self.table_count,
            #            --- Bibliographic stuff ---,
            citations=self.citation_counts,
            index_entries=self.index_count,
            footnotes=self.footnote_count,
            # --- LaTeX stuff --- ,
            latex_command_count=sum(self.command_Counter.values()),
            latex_commands=self.command_Counter,
            latex_env_count=sum(self.env_Counter.values()),
            latex_environments=self.env_Counter,
            # --- Most common words --- ,
            most_common_words=self.word_Counter.most_common(
                self.number_most_common
            ),
            most_common_nonstopping_words=self.reduced_word_Counter.most_common(
                self.number_most_common
            ),
            most_common_stems=self.stem_Counter.most_common(
                self.number_most_common
            ),
            most_common_nonstopping_stems=self.nonstopping_stem_Counter.most_common(
                self.number_most_common
            ),
        )
        self.series: pd.Series = pd.Series(data_dict, name="Stats")
        return self.series


def fix_specific_things(stats: Stats) -> Stats:
    # Replace nasal with NaSal
    stats.word_Counter["NaSal"] = stats.word_Counter["nasal"]
    stats.word_Counter["nasal"] = 0
    stats.reduced_word_Counter["NaSal"] = stats.reduced_word_Counter["nasal"]
    stats.reduced_word_Counter["nasal"] = 0
    occurrence_micelas_gigantes = re.findall(r"micelas gigantes", stats.text)
    occurrence_micelas_only = re.findall(r"micelas ?(?!gigantes)", stats.text)
    stats.word_Counter["micelas"] = len(occurrence_micelas_only)
    stats.word_Counter["micelas gigantes"] = len(occurrence_micelas_gigantes)
    stats.reduced_word_Counter["micelas"] = len(occurrence_micelas_only)
    stats.reduced_word_Counter["micelas gigantes"] = len(
        occurrence_micelas_gigantes
    )

    return stats


def usage_example():
    path = pathlib.Path(thesis_path)
    tex_files = glob.glob(str(path / "*.tex"))
    list_of_Stats = []
    full_text = []
    for file in tex_files:
        text = open_file(file)
        st = Stats(
            file,
            text=text,
            commit_hash="test",
            description="test",
            output_path=stats_basepath,
            debug_output_path=stats_basepath,
        )
        st.calculate_stats()
        st.save_as_text()
        st.pickle()
        list_of_Stats.append(st)
        full_text.append(text)
    full_text = "\n".join(full_text)
    st = Stats(
        "all",
        full_text,
        commit_hash="hash",
        description="all",
        output_path=stats_basepath,
        debug_output_path=stats_basepath,
        number_most_common=100,
    )
    st.debug = False
    st.calculate_stats()
    st.save_as_text()
    list_of_Stats.append(st)
    st.save_as_csv()
    st.pickle()
    return list_of_Stats


def create_stats_all_tex_files(
    filename: str, commit_hash: str, description: str
) -> Stats:
    path = pathlib.Path(thesis_path)
    tex_files = glob.glob(str(path / "*.tex"))
    full_text = []
    for file in tex_files:
        text = open_file(file)
        full_text.append(text)
    full_text_str = "\n".join(full_text)
    st = Stats(
        "all",
        full_text_str,
        commit_hash=commit_hash,
        description=description,
        output_path=stats_basepath,
        debug_output_path=stats_basepath,
        number_most_common=100,
    )
    st.calculate_stats()
    st = fix_specific_things(st)
    return st
