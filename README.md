# The making of a thesis

This project goes through my thesis repository, extracts some data
from the .tex files (word count, character count, number of sections, etc),
compiles the pdfs, converts each pdf page into an image, then combines
everything into a frame. The frames themselves have to be joined together 
later with another tool. I used DaVinci Resolve.

I did this because it seemed fun. I wrote a bit more about what went on my 
mind [here](https://karlclinckspoor.github.io/evol_thesis.html)

I created two movies, one fast and one slow. They can be found on YouTube.

* https://youtu.be/jKUw8FVsJxE (fast)
* https://youtu.be/o8FFMAszz5s (slow)

## Running the script

First, you must clone this repository with `git clone https://github.
com/KarlClinckspoor/EvolutionThesis.git`, or click on the green `Code` button, 
then `Download ZIP`, then extract the ZIP file.

Then, you need a repository with a thesis, like mine. Once again, run `git clone https://github.
com/KarlClinckspoor/Tese.git`, or download the ZIP. It is recommended to 
place this at the same parent folder as the other repository. 

Edit the file `config.py` to point to the absolute/relative path of the 
thesis repository. Here you can also change the names of the directories the 
temporary output files will be placed. My names are horribly nondescriptive.

The file `main.py` contains the main entry point to this script. It is very 
simple, and just points to other functions that do the brunt of the work. 

If the script hangs up when compiling the .tex files, go to `latex_manip.py` 
and change the line `compile_pdf_from_sha(commit["sha"], repo, verbose=False)` 
to `compile_pdf_from_sha(commit["sha"], repo, verbose=True)`. This will show 
the LaTeX compilation output and let you recognize some possible problems.

This works fine in (Manjaro) Linux. I had some problems running this in Windows,
because of complicated dependency installs and some issues with
`pathlib`, `PosixPath` I'm not going to fix, so I recommend using a Linux VM
(or perhaps WSL). I don't know how compatible this is with MacOS, haven't
tested.

## Requirements:

### LaTeX

This requirement is for my thesis itself. I compiled it with XeLaTeX
(TeXLive 2020, Version 3.14159265-2.6-0.999992). pdfLaTeX won't work because my
thesis uses fontspec. It also requires the
[Latin Modern Fonts](www.fontsquirrel.com/fonts/Latin-Modern-Roman). Download
them (Roman, Sans and Mono) and check the method appropriate to your OS to 
install them.

### pdftoppm

This script uses the tool pdftoppm. It is part of
the [poppler project](https://github.com/freedesktop/poppler). On Windows, it
comes with [MikTeX](https://miktex.org/), or you can install with
[Chocolatey](https://chocolatey.org/packages/poppler) or
using `conda install -c conda-forge poppler`. On Linux, you can get it by
installing `poppler-utils` (Ubuntu) or `poppler` (Manjaro). On Mac, you can 
install it with Homebrew (`brew install poppler`) or `conda`.

### Python

The entire script is written in Python. I used the Anaconda 2020.11 that I 
installed using [`pyenv`](https://github.com/pyenv/pyenv) on my Manjaro 
Linux system. The packages I used are in the `requirements.txt` file.

I had some problems trying to reproduce my python install. Anaconda environments
worked fine, but "pure" python installs with `pip install -r requirements.txt`
did not. I tried creating a virtual environment of "pure" Python 3.9.0 and
3.8.4, `pip` installed the requirements. There would be problems when creating the
wordcloud, with varying messages, such as `segmentation faults` and 
`corrupted size vs prev_size`, `munmap_chunk(): invalid pointer`. Using 
`conda` solved the problem, though.

The following process worked for me. I recommend using venv, pipenv, 
virtualenvwrapper, pyenv or stuff like that, because it makes 
resetting and testing other stuff much easier.

1. Install miniconda or anaconda (e.g. `pyenv install anaconda3-2020.11`)
2. (Optional) Create a virtual environment of this install (e.g. `pyenv 
   virtualenv evolutionthesis anaconda3-2020.11`)
3. (Possibly optional) Activate the environment (e.g. `pyenv local 
   anaconda3-2020.11` or `pyenv local evolutionthesis`)
4. Check the python version (`python --version`). If it's 3.9+, downgrade it to
   3.8.0 or 3.8.5 with `conda install python=3.8.5`. If you're not using a
   virtual environment or pyenv, then I recommend creating a conda
   env, `conda create --name condaenv python=3.8.5 pip`.
5. Install the requirements
   with `conda install -c conda-forge --file requirements.txt`. It might 
   take a while. It only complained about incompatibilities if my python 
   version was 3.9+.
   
Then run `main.py`. If there's something wrong with your install, it will 
probably hang up when creating to frames of the movie (specifically when calling
`wordcloud`).

# Licensing

You can use and modify the code here to your heart's content. I would appreciate
being thanked or contacted, if someone decides to use this. Don't try to sell
anything you create with this. I don't think anyone would buy, and it also
wouldn't be very cool (unless you asked for permission beforehand). 