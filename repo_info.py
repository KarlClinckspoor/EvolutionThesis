# This file contains functions to extract information about the repository, such
# as number of commits, their ids, the date they were created, and so on
# Uses gitpython to make the process easier

import git
from config import thesis_path
import pandas as pd
from text_stats import Stats, open_file
import glob
import pathlib


def create_commit_list(repo: git.Repo, out_filename: str = 'git_commits_info.txt') -> list:
    """Goes through the commits and generates an external text file that has the
    sha, the commit message and the unix date.

        Returns:
        List of dicts containing the same elements that were written to the file
    """
    commits = []
    with open(out_filename, "w", encoding="utf8") as fhand:
        # Write header to file
        fhand.write("sha;message;timestamp\n")
        for commit in repo.iter_commits():
            sha = commit.hexsha
            message = commit.message.rstrip()
            # Needs to be converted afterwards to a datetime object. To store,
            # will use the "pure" number.
            date = commit.committed_date
            fhand.write(f"{sha};{message};{date}\n")
            commits.append({"sha": sha, "message": message, "date": date})
    return commits


def load_commit_list(filename: str = "git_commits_info.txt") -> list:
    """Goes through the file created in create_commit_list and generates a list
    of dicts containing information about the commits

        Args:
            filename (str): path to file
        Returns:
            List of dicts containing "sha", "message", "time" as keys.
    """
    lines = open(filename, "r", encoding="utf8").read()
    commits = []
    for i, line in enumerate(lines.split("\n")):
        if i == 0:  # Skip the header
            continue
        if len(line) == 0:
            continue
        sha, message, time = line.split(";")
        commits.append({"sha": sha, "message": message, "time": time})
    return commits


def test_repo_info():
    repo = git.Repo(thesis_path)
    create_commit_list(repo)
    print(load_commit_list("git_commits_info.txt"))
