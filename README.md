# Drec-DreamRecorder

This repository was originally based on dreamento (accessed from https://github.com/dreamento/dreamento, mid 2024). 
It has developed into a standalone project for **eeg recording** of the signal captured by a ZMax Headband (by Hypnodyne) and **scoring** the eeg signal using the **yasa** library. Additionally the option to send the scoring to a separate **webhook** is implemented, to allow to control external (audio, visual, ...) impulses or applications.

## run from scripts
all the following steps describe the procedure for the windows operating system. On other os the commands may differ slightly.

clone the repository

create a virtual env:
  python -m venv /path/to/wherever/you/want/it/to/live/

activate the venv:
  run the activate.bat file from your cmd located at /path/to/venv/Scripts/activate.bat
  
make sure pip is upgraded:
  python -m pip install --upgrade pip

install the requirements from requirements.txt located in the repository or install the required ones manually:
  python -m pip install -r requirements.txt

run mainconsole.py from your cmd that has the venv activated

## usage
make sure **HDServer** from hypnodyne is running. 

## TODO:
- [ ] implement 'offline' version, that allows to score previous recordings
- [ ] when saving save the metadata, e.g. what signals are recorded. This is a program setting, therefore relevant
- [ ] bugfixes
  - [ ] the window opened with show_signal can crashes the app when moved or resized incorrectly
  - [ ] when terminating the program after show_signal was called the program gets stuck. probably has to do with threads -> solution: remove show_signal
## requirements
- python 3.6
- libraries:
  - PyQt5==5.15.6
  - mne==0.23.4
  - yasa==0.5.1
  - pyEDFlib==0.1.38
  - torch==1.10.2
  - pyqtgraph==0.11.1
  - Flask==3.1.0
  - lightgbm


