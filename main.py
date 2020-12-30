#!python3
# author: Karl Jan Clinckspoor
# start date: 2020-12-08
# last update: 2020-12-08

from config import (
    thesis_path,
    stats_basepath,
    compiled_pdfs_path,
    pdf_pages_path,
    collated_pdfs_path,
)
from repo_info import create_commit_list
from text_stats import Stats
import pathlib
import git
import glob
import os
import shutil
from typing import List, Tuple
import subprocess


def main():  # TODO
    # Step 1: Extract information from the directory
    print(thesis_path)
    print("Creating commit list", end="")
    create_commit_list()
    print(" - Done")


def create_stats_from_sha(
    sha: str,
    repo: git.Repo,
    filename_pattern: str = "*.tex",
    merge: bool = True,
) -> List[Stats]:
    """Creates a stats object and computes its values starting from a commit
    hash and a git.Repo object pointing to the repo.

        Args:
            sha (str): The commit sha hash
            repo (git.Repo): The target repo
            filename_pattern (str, optional): The pattern used to get the
            appropriate files. Defaults to "*.tex".
            merge (bool, optional): Whether or not to compute the stats for all
            the files as one, or to compute them individually. Defaults to True.

        Returns:
            List[Stats]: A list containing the invididual Stats for each file considered. If `merge==True`, then its a single item list.
    """
    from text_stats import open_file

    starting_sha = repo.commit().hexsha
    repo.git.checkout(sha)
    date = repo.commit().committed_date

    path = pathlib.Path(thesis_path)
    tex_files = glob.glob(str(path / filename_pattern))
    assert len(tex_files) >= 1

    if merge:
        list_text: List[str] = []
        for file in tex_files:
            text = open_file(file)
            list_text.append(text)
        full_text = "\n".join(list_text)
        st = Stats(
            f"all",
            text=full_text,
            commit_hash=sha,
            description="",
            date=date,
            output_path=stats_basepath,
        )
        st.calculate_stats()
        return [st]
    else:
        list_stats: List[Stats] = []
        for file in tex_files:
            text = open_file(file)
            st = Stats(
                file,
                text=full_text,
                commit_hash=sha,
                description=filename_pattern,
                output_path=str(pathlib.Path(stats_basepath) / sha),
                debug_output_path=str(pathlib.Path(stats_basepath) / sha),
            )
            list_stats.append(st)
        return list_stats

    repo.git.checkout(starting_sha)


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
    """Compiles the pdf using xelatex, targetting the file in `mainfile_name`,
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
    starting_sha = repo.commit().hexsha
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
    if (not overwrite_pdf) and os.path.isfile(
        pathlib.Path(output_path) / (sha + ".pdf")
    ):
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
            )  # TODO: not "\n".join... Because written in Windows?

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
    proc = subprocess.run(xelatex_command, capture_output=not verbose)
    print("\tIndex", flush=True)
    proc = subprocess.run(makeindex_command, capture_output=not verbose)
    print("\tReferences", flush=True)
    proc = subprocess.run(bibtex_command, capture_output=not verbose)
    print("\tCompilation 2", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=not verbose)
    print("\tCompilation 3", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=not verbose)
    print("\tCompilation 4", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=not verbose)
    print(flush=True)
    print("\tCompilation done", flush=True)

    shutil.copy(
        mainfile_name[:-4] + ".pdf",
        pathlib.Path(original_dir) / pathlib.Path(output_path) / f"{sha}.pdf",
    )

    os.chdir(original_dir)


def test_create_all_stats():  # Tests creating all stats for all commits
    from repo_info import load_commit_list

    commits = load_commit_list()
    starting_commit = commits[0]["sha"]
    repo = git.Repo(thesis_path)
    repo.git.checkout(starting_commit, force=True)

    for commit in commits:
        st = create_stats_from_sha(
            commit["sha"],
            repo,
        )[0]
        st.pickle()
        st.save_as_text()


def compile_all_pdfs() -> None:
    """Compiles all pdfs possible."""
    from repo_info import load_commit_list

    commits = load_commit_list()
    starting_commit = commits[0]
    repo = git.Repo(thesis_path)
    for i, commit in enumerate(commits):
        print(
            f'Compilation {i+1} of {len(commits)}: {commit["message"]}',
            flush=True,
        )
        compile_pdf_from_sha(commit["sha"], repo, verbose=True)


# TODO: consider moving this and other image-related functions to another file
def dismember_pdf_images_from_sha(sha: str, dpi: int = 50) -> None:
    """Creates images for each page of a compiled pdf, starting from its sha.

    Args:
        sha (str): SHA hash of the commit
        dpi (int, optional): the default dpi used for the images. Defaults to
        50. It's not necessary to be very large.
    """
    starting_dir = pathlib.Path(os.getcwd()).absolute()
    pdf_path = (pathlib.Path(compiled_pdfs_path) / (sha + ".pdf")).absolute()
    output_dir = (pathlib.Path(pdf_pages_path) / sha).absolute()

    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)
    subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r",
            str(dpi),
            "-hide-annotations",
            pdf_path.absolute(),
            "pdf",
        ],
        capture_output=False,
    )
    os.chdir(starting_dir)


def test_all_includeonlys() -> None:
    """Tests commit by commit if there's a line containing \\includeonly. This
    needs to be removed to better represent the evolution of the pages
    """
    from repo_info import load_commit_list

    commits = load_commit_list()
    repo = git.Repo(thesis_path)
    for i, commit in enumerate(commits):
        repo.git.checkout(commit["sha"], force=True)
        maintex = open(
            pathlib.Path(thesis_path) / pathlib.Path("main.tex"), "r"
        ).readlines()
        for j, line in enumerate(maintex):
            if "includeonly" in line:
                print(f'{commit["sha"]}, line {j}: {line.strip()}')
                break
        else:
            print(
                fr'{commit["sha"]}: Commit does not have an \includeonly statement'
            )


def test_all_img_from_path() -> None:
    """Tests creating images for all pdfs"""
    # TODO: change this to pathlib.Path.glob
    pdf_files = glob.glob(compiled_pdfs_path + "/*pdf")
    for i, file in enumerate(pdf_files):
        print(f"({i+1}:{len(pdf_files)}) Dismembering", file)
        pdf_path = pathlib.Path(file)
        dismember_pdf_images_from_sha(pdf_path.stem, dpi=50)


def test_collate_all() -> None:
    from repo_info import load_commit_list
    from collate_pages import collate_pdf_by_sha

    commits = load_commit_list()
    for i, commit in enumerate(commits):
        print(
            f"({i+1}/{len(commits)}): Merging {commit['sha']}...",
            end="",
            flush=True,
        )
        if (
            pathlib.Path(collated_pdfs_path) / (commit["sha"] + ".png")
        ).is_file():
            print(" Already processed, skipping.", flush=True)
            continue
        # Hard coded because these seem to be the better size for my case
        collate_pdf_by_sha(commit["sha"], rows=15, cols=25)
        print(" Done.", flush=True)


# def delete_problematic_pdfs() -> None:
#     with open("problem_includeonlys", "r") as fhand:
#         problem_pdfs = [
#             "./pdfs/" + line.split(" ")[2][:-1] + ".pdf" for line in fhand
#         ]
#         print(*problem_pdfs, sep="\n")
#         for pdf in problem_pdfs:
#             shutil.move(pdf, "./pdfs/bad")


# test_create_all_stats()
# compile_all_pdfs()
# test_all_includeonlys()
# test_all_img_from_path()
test_collate_all()


# if __name__ == "__main__":
#     main()
