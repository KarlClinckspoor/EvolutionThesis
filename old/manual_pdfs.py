# coding: utf-8

# !/usr/bin/python3
# encoding='utf8'
# todo: remove \includeonly from text
# todo: remove \today from text

import subprocess
import os
import shutil
import time
import sys
import glob
import re

# number of compiles to skip
try:
    number_skips = int(sys.argv[1])
except IndexError:
    number_skips = 0
except ValueError:
    number_skips = 0

base_dir = os.getcwd()
pdf_dir = os.path.join(base_dir, "pdfs")
os.makedirs(pdf_dir, exist_ok=True)
os.chdir("./Tese")


def set_repo_master():
    proc = subprocess.run(["git", "checkout", "master", "--force"], capture_output=False)
    return proc


def get_all_commit_ids() -> list:
    set_repo_master()
    gitlog = subprocess.run(["git", "log", "--oneline"], capture_output=True)
    log = gitlog.stdout.decode("utf8").split("\n")
    ids = [line.split(" ")[0] for line in log][:-1]
    ids = ids[::-1]  # starts with the earliest
    return ids


def parse_commit_dates(string: str) -> tuple:
    parser = re.compile(
        r"(\w{3})\s+(\w{3})\s+(\d{1,2})\s+(\d\d:\d\d:\d\d)\s+(201\d)\s+"
    )
    match = parser.search(string)
    day_week, month, day_month, time, year = match.groups()
    return day_week, month, day_month, time, year


def get_commit_hashes_full() -> list:
    # Guarantees the repo is at master
    set_repo_master()
    log = subprocess.run(["git", "log"], capture_output=True)
    return log.stdout.decode("utf8").split("\n")


def get_all_commit_ids_dates() -> dict:
    log = get_commit_hashes_full()
    commits = [i.strip().split(" ")[1] for i in log if i.startswith("commit")]
    dates = [parse_commit_dates(i) for i in log if i.startswith("Date:")]
    return dict(zip(commits, dates))


def reset_commit(id_=None):
    if id_:
        proc = subprocess.run(["git", "reset", id_, "--hard"], capture_output=False)
    else:
        proc = subprocess.run(["git", "reset", "HEAD", "--hard"], capture_output=False)
    return proc


def set_commit(id_):
    proc = subprocess.run(["git", "checkout", id_, "--force"], capture_output=True)
    return proc


def create_logfiles() -> tuple:
    log = open(os.path.join(base_dir, "log.txt"), "w", encoding="utf8")
    err = open(os.path.join(base_dir, "err.txt"), "w", encoding="utf8")
    return log, err


def close_logfiles(log, err) -> None:
    log.close()
    err.close()


def initiate_logfiles(log, err, idd):
    lf_fillwidth = 40
    log.write("\n" + "*" * lf_fillwidth + "\n")
    log.write(f"{idd}".center(lf_fillwidth, "*"))
    log.write("\n" + "*" * lf_fillwidth + "\n")

    err.write("\n" + "*" * lf_fillwidth + "\n")
    err.write(f"{idd}".center(lf_fillwidth, "*"))
    err.write("\n" + "*" * lf_fillwidth + "\n")


def write_logfiles(proc, log, err):
    log.write(proc.stdout.decode("utf8"))
    err.write(proc.stderr.decode("utf8"))


def compilation_sequence(log, err):
    xelatex_command = [
        "xelatex",
        "main.tex",
        "-shell-escape",
        "-interaction=nonstopmode",
    ]
    makeindex_command = ["makeindex", "main.tex"]
    bibtex_command = ["bibtex", "main"]
    print("\tCompilation 1", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tIndex", flush=True)
    proc = subprocess.run(makeindex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tReferences", flush=True)
    proc = subprocess.run(bibtex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tCompilation 2", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tCompilation 3", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tCompilation 4", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print(flush=True)
    print("\tCompilation done", flush=True)


def copy_compiled_file(log, err, idx: int, idd: str) -> None:
    try:
        print("\tTrying to copy main.pdf", flush=True)
        shutil.copy("main.pdf", os.path.join(base_dir, pdf_dir, f"{idx:04d}-{idd}.pdf"))
        print("\tDone", flush=True)
        log.write("\n\nCopying done")
    except FileNotFoundError:
        print(f"Failed to copy {idd}")
        err.write("\n\nFailed to copy")


def replace_text_file(filename: str, text: str, replacement: str) -> None:
    file = open(filename, "r", encoding="utf8").read()
    file.replace(text, replacement)
    with open(filename, "w", encoding="utf8") as f:
        f.write(file)


def remove_includeonly():
    replace_text_file("main.tex", r"\includeonly", r"%\includeonly")


def alter_date(date):
    pattern = re.compile(r'(\\dat[ae]){.*?}')
    file = open('main.tex', "r", encoding="utf8").read()
    replacement = pattern.sub(r'\1{' + date + '}', file)
    with open('main.tex', "w", encoding="utf8") as f:
        f.write(replacement)


def clear_pdf_aux() -> None:
    files = (
        glob.glob("*pdf")
        + glob.glob("*aux")
        + glob.glob("*.l??")
        + glob.glob("*.idx")
        + glob.glob("*synctex*")
    )
    for file in files:
        os.remove(file)


def batch_compilation(alter_tex=True):
    """Compiles the latex files into pdfs. Does not perform any changes at all"""
    #ids = get_all_commit_ids()
    date_dict = get_all_commit_ids_dates()
    ids = list(date_dict.keys())
    log, err = create_logfiles()
    for idx, idd in enumerate(date_dict.keys()):
        # Jump ahead if necessary
        if idx < number_skips:
            continue

        initiate_logfiles(log, err, idd)
        sequence(idd, idx, log, err, date_dict, alter_tex=alter_tex)


    print("Resetting repository to master", flush=True)
    # proc = subprocess.run(["git", "reset", "HEAD"], capture_output=True)
    proc = set_repo_master()
    write_logfiles(proc, log, err)
    close_logfiles(log, err)


def sequence(idd, idx, log, err, date_dict, alter_tex=True):
    proc = subprocess.run(["git", "checkout", idd, "--force"], capture_output=True)
    write_logfiles(proc, log, err)
    print("Removing pdf files and aux files")
    clear_pdf_aux()
    if alter_tex:
        alter_date(" ".join(date_dict[idd][:3]))
        remove_includeonly()

    print(f"Starting compilation {idx + 1}/{len(ids[::-1])}: {idd}", flush=True)
    compilation_sequence(log, err)
    copy_compiled_file(log, err, idx, idd)
    print("Resetting the commit")
    reset_commit(idd)
    write_logfiles(proc, log, err)


def adjusted_compilation():
    """Compiles the pdf files, and changes the dates to the ones given in the commits, and
removes the \includeonly tags"""

    ids_dates = get_commit_hashes_full()
    ids = [i[0] for i in ids_dates]
    dates = [i[2] + " " + i[1] + " " + i[4] for i in ids_dates]

    log, err = create_logfiles()
    for idx, idd in enumerate(ids[:]):
        # Jump ahead if necessary
        if idx < number_skips:
            continue

        date = dates[idx]

        initiate_logfiles(log, err, idd)

        proc = subprocess.run(["git", "checkout", idd, "--force"], capture_output=True)

        write_logfiles(proc, log, err)

        print("Cleaning filesystem")
        clear_pdf_aux()

        remove_includeonly()
        alter_date(date)

        print(f"Starting compilation {idx + 1}/{len(ids[::-1])}: {idd}", flush=True)
        compilation_sequence(log, err)
        copy_compiled_file(log, err, idx, idd)

        print("Resetting the commit")
        proc = subprocess.run(["git", "reset", "HEAD", "--hard"], capture_output=True)

        write_logfiles(proc, log, err)

    print("Resetting repository to master", flush=True)
    proc = subprocess.run(["git", "reset", "HEAD"], capture_output=True)
    write_logfiles(proc, log, err)

    proc = subprocess.run(["git", "checkout", "master", "--force"], capture_output=True)
    write_logfiles(proc, log, err)
    close_logfiles(log, err)
get_ipython().run_line_magic('pwd', '')
# !/usr/bin/python3
# encoding='utf8'
# todo: remove \includeonly from text
# todo: remove \today from text

import subprocess
import os
import shutil
import time
import sys
import glob
import re

# number of compiles to skip
try:
    number_skips = int(sys.argv[1])
except IndexError:
    number_skips = 0
except ValueError:
    number_skips = 0

base_dir = os.getcwd()
pdf_dir = os.path.join(base_dir, "pdfs")
os.makedirs(pdf_dir, exist_ok=True)
#os.chdir("./Tese")


def set_repo_master():
    proc = subprocess.run(["git", "checkout", "master", "--force"], capture_output=False)
    return proc


def get_all_commit_ids() -> list:
    set_repo_master()
    gitlog = subprocess.run(["git", "log", "--oneline"], capture_output=True)
    log = gitlog.stdout.decode("utf8").split("\n")
    ids = [line.split(" ")[0] for line in log][:-1]
    ids = ids[::-1]  # starts with the earliest
    return ids


def parse_commit_dates(string: str) -> tuple:
    parser = re.compile(
        r"(\w{3})\s+(\w{3})\s+(\d{1,2})\s+(\d\d:\d\d:\d\d)\s+(201\d)\s+"
    )
    match = parser.search(string)
    day_week, month, day_month, time, year = match.groups()
    return day_week, month, day_month, time, year


def get_commit_hashes_full() -> list:
    # Guarantees the repo is at master
    set_repo_master()
    log = subprocess.run(["git", "log"], capture_output=True)
    return log.stdout.decode("utf8").split("\n")


def get_all_commit_ids_dates() -> dict:
    log = get_commit_hashes_full()
    commits = [i.strip().split(" ")[1] for i in log if i.startswith("commit")]
    dates = [parse_commit_dates(i) for i in log if i.startswith("Date:")]
    return dict(zip(commits, dates))


def reset_commit(id_=None):
    if id_:
        proc = subprocess.run(["git", "reset", id_, "--hard"], capture_output=False)
    else:
        proc = subprocess.run(["git", "reset", "HEAD", "--hard"], capture_output=False)
    return proc


def set_commit(id_):
    proc = subprocess.run(["git", "checkout", id_, "--force"], capture_output=True)
    return proc


def create_logfiles() -> tuple:
    log = open(os.path.join(base_dir, "log.txt"), "w", encoding="utf8")
    err = open(os.path.join(base_dir, "err.txt"), "w", encoding="utf8")
    return log, err


def close_logfiles(log, err) -> None:
    log.close()
    err.close()


def initiate_logfiles(log, err, idd):
    lf_fillwidth = 40
    log.write("\n" + "*" * lf_fillwidth + "\n")
    log.write(f"{idd}".center(lf_fillwidth, "*"))
    log.write("\n" + "*" * lf_fillwidth + "\n")

    err.write("\n" + "*" * lf_fillwidth + "\n")
    err.write(f"{idd}".center(lf_fillwidth, "*"))
    err.write("\n" + "*" * lf_fillwidth + "\n")


def write_logfiles(proc, log, err):
    log.write(proc.stdout.decode("utf8"))
    err.write(proc.stderr.decode("utf8"))


def compilation_sequence(log, err):
    xelatex_command = [
        "xelatex",
        "main.tex",
        "-shell-escape",
        "-interaction=nonstopmode",
    ]
    makeindex_command = ["makeindex", "main.tex"]
    bibtex_command = ["bibtex", "main"]
    print("\tCompilation 1", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tIndex", flush=True)
    proc = subprocess.run(makeindex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tReferences", flush=True)
    proc = subprocess.run(bibtex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tCompilation 2", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tCompilation 3", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print("\tCompilation 4", flush=True)
    proc = subprocess.run(xelatex_command, capture_output=True)
    write_logfiles(proc, log, err)

    print(flush=True)
    print("\tCompilation done", flush=True)


def copy_compiled_file(log, err, idx: int, idd: str) -> None:
    try:
        print("\tTrying to copy main.pdf", flush=True)
        shutil.copy("main.pdf", os.path.join(base_dir, pdf_dir, f"{idx:04d}-{idd}.pdf"))
        print("\tDone", flush=True)
        log.write("\n\nCopying done")
    except FileNotFoundError:
        print(f"Failed to copy {idd}")
        err.write("\n\nFailed to copy")


def replace_text_file(filename: str, text: str, replacement: str) -> None:
    file = open(filename, "r", encoding="utf8").read()
    file.replace(text, replacement)
    with open(filename, "w", encoding="utf8") as f:
        f.write(file)


def remove_includeonly():
    replace_text_file("main.tex", r"\includeonly", r"%\includeonly")


def alter_date(date):
    pattern = re.compile(r'(\\dat[ae]){.*?}')
    file = open('main.tex', "r", encoding="utf8").read()
    replacement = pattern.sub(r'\1{' + date + '}', file)
    with open('main.tex', "w", encoding="utf8") as f:
        f.write(replacement)


def clear_pdf_aux() -> None:
    files = (
        glob.glob("*pdf")
        + glob.glob("*aux")
        + glob.glob("*.l??")
        + glob.glob("*.idx")
        + glob.glob("*synctex*")
    )
    for file in files:
        os.remove(file)


def batch_compilation(alter_tex=True):
    """Compiles the latex files into pdfs. Does not perform any changes at all"""
    #ids = get_all_commit_ids()
    date_dict = get_all_commit_ids_dates()
    ids = list(date_dict.keys())
    log, err = create_logfiles()
    for idx, idd in enumerate(date_dict.keys()):
        # Jump ahead if necessary
        if idx < number_skips:
            continue

        initiate_logfiles(log, err, idd)
        sequence(idd, idx, log, err, date_dict, alter_tex=alter_tex)


    print("Resetting repository to master", flush=True)
    # proc = subprocess.run(["git", "reset", "HEAD"], capture_output=True)
    proc = set_repo_master()
    write_logfiles(proc, log, err)
    close_logfiles(log, err)


def sequence(idd, idx, log, err, date_dict, alter_tex=True):
    proc = subprocess.run(["git", "checkout", idd, "--force"], capture_output=True)
    write_logfiles(proc, log, err)
    print("Removing pdf files and aux files")
    clear_pdf_aux()
    if alter_tex:
        alter_date(" ".join(date_dict[idd][:3]))
        remove_includeonly()

    print(f"Starting compilation {idx + 1}/{len(ids[::-1])}: {idd}", flush=True)
    compilation_sequence(log, err)
    copy_compiled_file(log, err, idx, idd)
    print("Resetting the commit")
    reset_commit(idd)
    write_logfiles(proc, log, err)


def adjusted_compilation():
    """Compiles the pdf files, and changes the dates to the ones given in the commits, and
removes the \includeonly tags"""

    ids_dates = get_commit_hashes_full()
    ids = [i[0] for i in ids_dates]
    dates = [i[2] + " " + i[1] + " " + i[4] for i in ids_dates]

    log, err = create_logfiles()
    for idx, idd in enumerate(ids[:]):
        # Jump ahead if necessary
        if idx < number_skips:
            continue

        date = dates[idx]

        initiate_logfiles(log, err, idd)

        proc = subprocess.run(["git", "checkout", idd, "--force"], capture_output=True)

        write_logfiles(proc, log, err)

        print("Cleaning filesystem")
        clear_pdf_aux()

        remove_includeonly()
        alter_date(date)

        print(f"Starting compilation {idx + 1}/{len(ids[::-1])}: {idd}", flush=True)
        compilation_sequence(log, err)
        copy_compiled_file(log, err, idx, idd)

        print("Resetting the commit")
        proc = subprocess.run(["git", "reset", "HEAD", "--hard"], capture_output=True)

        write_logfiles(proc, log, err)

    print("Resetting repository to master", flush=True)
    proc = subprocess.run(["git", "reset", "HEAD"], capture_output=True)
    write_logfiles(proc, log, err)

    proc = subprocess.run(["git", "checkout", "master", "--force"], capture_output=True)
    write_logfiles(proc, log, err)
    close_logfiles(log, err)
idx = 1
dict_ = get_all_commit_ids_dates()
lst = [(key, val) for (key, val) in dict_.items()]
lst
idx = 1
set_commit(lst[idx][0])
remove_includeonly()
compilation_sequence(log, err)
log, err = create_logfiles()
set_commit(lst[idx][0])
remove_includeonly()
compilation_sequence(log, err)
copy_compiled_file(log, err)
copy_compiled_file(log, err, idx, lst[idx][0])
print(lst[idx][0])
idx=2
set_commit(lst[idx][0])
remove_includeonly()
compilation_sequence(log, err)
copy_compiled_file(log, err, idx, lst[idx][0])
idx
copy_compiled_file(log, err, idx, lst[idx][0])
shutil.copy("main.pdf", os.path.join(base_dir, pdf_dir, f"{idx:04d}-{lst[idx][0]}.pdf"))
base_dir
base_dir = r'D:\filme'
pdf_dir
pdf_dir = r'D:\filme\pdfs'
copy_compiled_file(log, err, idx, lst[idx][0])
idx
idx=3
set_commit(lst[idx][0])
remove_includeonly()
compilation_sequence(log, err)
copy_compiled_file(log, err, idx, lst[idx][0])
def step1():
    set_commit(lst[idx][0])
    compilation_sequence(log, err)
    
def step2():
    copy_compiled_file(log, err, idx, lst[idx][0])
    
def step3():
    global idx
    idx += 1
    
idx
step3()
idx
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step1()
step2()
step3()
step1()
step2()
step3()
step1()
def step1():
    set_commit(lst[idx][0])
    print(lst([idx][1]))
    compilation_sequence(log, err)
    
   
step1()
def step1():
    set_commit(lst[idx][0])
    print(lst[idx][1])
    compilation_sequence(log, err)
    
   
step1()
step2()
step3()
idx
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step2()
step3()
step1()
step2()
step3()
idx
step1()
step2()
step3()
for i in range(100):
    step1()
    step2()
    step3()
    
idx
for i in range(100):
    step1()
    step2()
    step3()
    print(idx)
    
step2()
step2()
step3()
for i in range(100):
    step1()
    step2()
    step3()
    print(idx)
    
def step1test():
    set_commit(lst[idx][0])
    print(lst[idx][1])
    content = open('main.tex', 'r').read()
    if '\n\\includeonly' in content:
        print(idx, lst[idx][1])
        

   
idx = 66
for i in range(50):
    step1test()
    step3()
    
def step1test():
    set_commit(lst[idx][0])
    print(lst[idx][1])
    content = open('main.tex', 'r', encoding='utf8').read()
    if '\n\\includeonly' in content:
        print(idx, lst[idx][1])
for i in range(50):
    step1test()
    step3()
    
def step1test():
    set_commit(lst[idx][0])
#    print(lst[idx][1])
    content = open('main.tex', 'r', encoding='utf8').read()
    pattern = re.compile(r'^(\\includeonly.*)$')
    subst = pattern.sub(r'', content)
    if subst != content:
        print(idx)
    with open('main.tex', 'w', encoding='utf8') as fhand:
        fhand.write(subst)
        
idx = 66
for i in range(50):
    step1test()
    step3()
    
get_ipython().run_line_magic('pinfo', 're.sub')
def step1test():
    set_commit(lst[idx][0])
#    print(lst[idx][1])
    content = open('main.tex', 'r', encoding='utf8').read()
    pattern = re.compile(r'\n(\\includeonly.*)\n')
    subst = pattern.sub(r'', content)
    if subst != content:
        print(idx)
    with open('main.tex', 'w', encoding='utf8') as fhand:
        fhand.write(subst)
        
idx = 66
for i in range(50):
    step1test()
    step3()
    
def step1test():
    set_commit(lst[idx][0])
#    print(lst[idx][1])
    content = open('main.tex', 'r', encoding='utf8').read()
    pattern = re.compile(r'\n(\\includeonly.*)\n')
    subst = pattern.sub(r'', content)
    if subst != content:
        print(idx)
    with open('main.tex', 'w', encoding='utf8') as fhand:
        fhand.write(subst)
    compilation_sequence(log, err)
            
idx = 66
idx = 60
for i in range(100):
    step1test()
    step2()
    step3()
    
get_ipython().run_line_magic('pinfo', '%save')
