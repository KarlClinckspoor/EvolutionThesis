#!python
# encoding=utf8
# This file contains a sequence that should be followed in order to compile all the frames of the video
# To join the frames into a movie and add some music, one must use a video editor, like DaVinci Resolve
from collate_pages import dismember_all_pdfs, collate_all, compress_all_images
from create_figure import create_all_graphs
from repo_info import create_commit_list
from text_stats import create_all_stats
from latex_manip import compile_all_pdfs
import config
from pathlib import Path

debug = True

def main():
    options = """
    Choose an option
    
    1. Create commit stats
    2. Calculate statistics for all files
    3. Compile all PDFs
    4. Split PDFs into images
    5. Collate PDF images into a figure
    6. Compress all collated images
    7. Create all video frames
    8. Do all
    """
    print("Checking folders")
    create_directories()
    while True:
        if debug:
            create_commit_list()
            create_all_stats()
            compile_all_pdfs()
            dismember_all_pdfs()
            collate_all()
            compress_all_images()
            create_all_graphs()
            print('Done')
            break
        print(options)
        choice = input("What is your choice?")
        if choice not in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            print("Invalid choice, exiting")
            break
        else:
            if (choice == "1") or (choice == "8"):
                create_commit_list()
            elif (choice == "2") or (choice == "8"):
                create_all_stats()
            elif (choice == "3") or (choice == "8"):
                compile_all_pdfs()
            elif (choice == "4") or (choice == "8"):
                dismember_all_pdfs()
            elif (choice == "5") or (choice == "8"):
                collate_all()
            elif (choice == "6") or (choice == "8"):
                compress_all_images()
            elif (choice == "7") or (choice == "8"):
                create_all_graphs()


def create_directories() -> None:
    for key, val in config.__dict__.items():
        if key.startswith("__"):
            continue
        folder = Path(val)
        print("Checking", folder)
        if not folder.is_dir():
            if input("Create directory:" + str(folder) + "? (Y/n)").lower() == "n":
                pass
            else:
                print("Creating", folder)
                folder.mkdir()


if __name__ == "__main__":
    main()
