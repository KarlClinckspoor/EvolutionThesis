#!python3
# author: Karl Jan Clinckspoor
# start date: 2020-12-08
# last update: 2020-12-08

from config import thesis_path, stats_basepath
from repo_info import create_commit_list
from text_stats import Stats
import pathlib
import git
import glob
from typing import List


def main():
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


def test_create_all_stats():
    from repo_info import load_commit_list

    commits = load_commit_list()
    starting_commit = commits[0]["sha"]
    repo = git.Repo(thesis_path)
    repo.git.checkout(starting_commit)

    for commit in commits:
        st = create_stats_from_sha(
            commit["sha"],
            repo,
        )[0]
        st.pickle()
        st.save_as_text()


test_create_all_stats()

# if __name__ == "__main__":
#     main()