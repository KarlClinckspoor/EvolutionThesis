#!python3
# author: Karl Jan Clinckspoor
# start date: 2020-12-08
# last update: 2020-12-08

from config import thesis_path
from repo_info import create_commit_list


def main():
    # Step 1: Extract information from the directory
    print(thesis_path)
    print("Creating commit list", end="")
    create_commit_list()
    print(" - Done")


if __name__ == "__main__":
    main()