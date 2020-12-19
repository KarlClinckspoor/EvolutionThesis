# Used to create stats of a specific commit, such as the number of pages of the
# pdf file, the number of words, number of sections, etc

from config import thesis_path, stats_basepath
import os
import glob
import re
from collections import Counter, namedtuple
import pathlib
import pdb


# TODO: is this a good way of implementing the class? I think I need some
# decorators, getters and setters
class Stats:
    debug = True

    def __init__(
        self,
        filename: str,
        output_path: str = ".",
        debug_output_path: str = ".",
    ):
        """Creates an instance of a Stats class. To calculate, need to run
        calculate_stats, to save as a text file, need to run save_as_text, to
        save as a table, need to run save_as_csv.

                Args:
                    filename (str): path to file
        """
        self.filename = filename
        self.basename = os.path.basename(filename)
        self.open_file(filename)
        self.original_text = self.text[:]
        self.output_path = output_path
        self.debug_output_path = debug_output_path

    def open_file(self, filepath: str) -> None:
        """Opens a file"""
        self.text = open(filepath, "r", encoding="utf8").read()

    def count_words(self):
        """Counts words in the text, not escaped by \ (i.e., no commands). Will
        count comments and single-letter words also."""
        # Regex Translation: Ignores everything preceded by \, like \chapter,
        # etc
        word_regex = re.compile(r"(?<!\\)\b\w+\b")
        self.word_count = len(word_regex.findall(self.text))

    def count_unique_words(self) -> None:
        """Removes word duplicates"""
        word_regex = re.compile(r"(?<!\\)\b\w+\b")
        self.unique_word_count = len(set(word_regex.findall(self.text)))

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

    def Counter_words(self) -> None:
        """Creates a dictionary (specifically a collections.Counter) that
        contains the most used words in the text, but all lowercase
        """
        # Regex translation: Find everything not escaped (preceded by \), not
        # preceded by "{", not followed by "}", that's made by word characters (\w)
        # between two word boundaries (\b).
        word_regex = re.compile(r"(?<!\\)(?<!{)\b\w+\b(?!})")
        words = word_regex.findall(self.text.lower())
        self.word_Counter = Counter(words)

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
        try:
            import nltk
        except ModuleNotFoundError:
            print("Please install nltk")
        try:
            nltk.data.find("corpora/stopwords")
        except LookupError:
            nltk.download("stopwords")

        stopwords = nltk.corpus.stopwords.words("portuguese")
        self.reduced_word_Counter = self.word_Counter.copy()
        for word in stopwords:
            del self.reduced_word_Counter[word]

    def remove_spurious_words(self) -> None:
        """Removes words that are just numbers or single letter words with no
        meaning (e.g. "c", "d", etc)"""
        # TODO: complete
        pass

    def calculate_stats(self) -> None:
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "original",
                self.original_text,
                restart=True,
            )

        # First step is to remove comments, since they don't count
        self.remove_comments()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
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
                self.debug_output_path + self.basename + "-test.txt",
                "wo includegraphics",
                self.text,
            )
        self.remove_label()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "wo label",
                self.text,
            )
        self.remove_index()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "wo index",
                self.text,
            )
        self.remove_citations()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "wo cite",
                self.text,
            )
        self.remove_references()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "wo refs",
                self.text,
            )
        self.remove_unnumbered_equations()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "wo unnum eq",
                self.text,
            )
        self.remove_equation_envs()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "wo eq envs",
                self.text,
            )
        self.remove_inputminted()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "wo inputminted",
                self.text,
            )
        self.remove_subfigure_envs()
        if self.debug:
            self._save_intermediary_text(
                self.debug_output_path + self.basename + "-test.txt",
                "wo subfigs",
                self.text,
            )

        # Count number of words
        self.count_words()
        # Of these, how many are unique?
        self.count_unique_words()
        # Rank the words by usage
        self.Counter_words()
        # Rank the interesting words (removes stopping words)
        self.remove_common_words()

    def save_as_text(self) -> None:
        self.stats_text = (
            f"word count: {self.word_count} \n"
            f"unique word count {self.unique_word_count}\n"
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
            f"latex commands: {self.command_Counter}\n"
            f"latex environments: {self.env_Counter}\n"
            f"--- Most common words --- \n"
            f"word_counter: \n {self.word_Counter.most_common(50)} \n"
            f"better word counter: \n {self.reduced_word_Counter.most_common(50)} \n"
        )
        with open(
            self.output_path + "Stats for " + self.basename + ".txt", "w"
        ) as fhand:
            fhand.write(self.stats_text)

    def _save_intermediary_text(
        self, filename, annotation: str, text: str, restart=False
    ) -> None:
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

    def save_as_csv(self) -> None:
        pass


def main():
    path = pathlib.Path(thesis_path)
    tex_files = glob.glob(str(path / "*.tex"))
    list_of_Stats = []
    for file in tex_files:
        st = Stats(file, stats_basepath, stats_basepath)
        st.calculate_stats()
        st.save_as_text()
        list_of_Stats.append(st)


if __name__ == "__main__":
    main()
