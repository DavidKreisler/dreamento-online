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
- [X] implement always responsive console
- [X] implement recorder
  - [X] connect to software 
  - [X] receive data from socket
  - [X] Pack the data received from the socket into 256 chunks, since the sample frequency is 256 and we want to structure it by seconds -> not necessary, since the server sends it in this manner.
  - [ ] when saving save the metadate, e.g. what signals are recorded. This is a program setting, therefore relevant
- [X] implement visualization
  - [X] for eeg singal
  - [X] for automatic scoring prediction  
- [ ] implement automatic scoring
  - [X] yasa
  - [ ] test model
- [X] implement webhook
  - [X] for sleep scoring prediction
  - [X] for epoch
- [ ] bugfixes
  - [ ] the window opened with show_signal can crashes the app when moved or resized incorrectly
  - [ ] when terminating the program after show_signal was called the program gets stuck. probably has to do with threads -> solution: remove show_signal
- [ ] record test night and validate scoring
- [ ] remove warning message at startup
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


