# File containing functions to create, modify, compile PDFs

import os
import shutil
import subprocess
import git
from pathlib import Path
from config import compiled_pdfs_path, thesis_path
from repo_info import load_commit_list


def compile_pdf_from_sha(
    sha: str,
    repo: git.Repo,
    output_path: str = compiled_pdfs_path,
    texfile_location: str = thesis_path,
    mainfile_name: str = "main.tex",
    fix_includeonly: bool = True,
    verbose: bool = False,
    overwrite_pdf: bool = False,
) -> None:
    r"""Compiles the pdf using xelatex, targetting the file in `mainfile_name`,
    then copies the pdf to the path specified in `output_path`. Requires a
    git.Repo instance pointing to the repository. Can remove lines that contain
    "includeonly", so it compiles the full text. Verbose can be used to show, or
    not, the compilation output.

        Args:
            sha (str): the sha hash that git can use to checkout
            output_path (str): where the compiled pdf will be stored
            repo (git.Repo): the git repo instance
            texfile_location (str): the location of the .tex files
            mainfile_name (str): the name of the main file, typically main.tex
            fix_includeonly (bool, optional): Removes any lines that contain
                "\includeonly". Defaults to True.
            verbose (bool, optional): If set to true, shows all the output of
                the programs used. Defaults to False.
            overwrite_pdf (bool): Overwrites any already compiled pdf
    """
    repo.git.checkout(sha, force=True)
    xelatex_command = (
        "xelatex",
        "-shell-escape",
        "-interaction=nonstopmode",
        mainfile_name,
    )
    makeindex_command = ("makeindex", mainfile_name)
    bibtex_command = ("bibtex", mainfile_name[:-4])

    # Create folder if not exists
    os.makedirs(output_path, exist_ok=True)
    # Check if there's already a pdf file there
    if (not overwrite_pdf) and os.path.isfile(Path(output_path) / (sha + ".pdf")):
        print(f"Already compiled {sha}, skipping")
        return

    # It's easier to change dirs because of the latex commands, copy the pdf,
    # then change back
    original_dir = os.getcwd()
    os.chdir(texfile_location)

    if fix_includeonly:
        maintex = open(mainfile_name, "r").readlines()
        # Very crude
        for i, line in enumerate(maintex):
            if "includeonly" in line:
                # maintex.replace("includeonly", "")
                maintex[i] = ""
        with open(mainfile_name, "w") as fhand:
            fhand.write(
                "".join(maintex)
            )  # not "\n".join... Because written in Windows?

    # One specific commit had a problem, where there was a table in the file
    # "aditivos.tex" where the first cell title was [NaSal], and the previous
    # command was \toprule. Even with the newline between them, xelatex was
    # considering it to be \toprule[NaSal], and accusing NaSal of not being a
    # number, freezing compilation.
    if sha.startswith("df17dbd"):
        problematic_text = open("aditivos.tex", "r").read()
        import re

        problematic_text = re.sub(
            r"\\toprule([\s%]+?)\[NaSal\]",
            r"\\toprule\1NaSal",
            problematic_text,
        )
        with open("aditivos.tex", "w") as fhand:
            fhand.write(problematic_text)

    print("\tCompilation 1", flush=True)
    _ = subprocess.run(xelatex_command, capture_output=not verbose)
    print("\tIndex", flush=True)
    _ = subprocess.run(makeindex_command, capture_output=not verbose)
    print("\tReferences", flush=True)
    _ = subprocess.run(bibtex_command, capture_output=not verbose)
    print("\tCompilation 2", flush=True)
    _ = subprocess.run(xelatex_command, capture_output=not verbose)
    print("\tCompilation 3", flush=True)
    _ = subprocess.run(xelatex_command, capture_output=not verbose)
    print("\tCompilation 4", flush=True)
    _ = subprocess.run(xelatex_command, capture_output=not verbose)
    print(flush=True)
    print("\tCompilation done", flush=True)

    shutil.copy(
        mainfile_name[:-4] + ".pdf",
        Path(original_dir) / Path(output_path) / f"{sha}.pdf",
    )

    os.chdir(original_dir)


def compile_all_pdfs() -> None:
    """Compiles all pdfs possible."""

    commits = load_commit_list()
    repo = git.Repo(thesis_path)
    for i, commit in enumerate(commits):
        print(
            f'Compilation {i+1} of {len(commits)}: {commit["message"]}',
            flush=True,
        )
        compile_pdf_from_sha(commit["sha"], repo, verbose=False)
