from enum import Enum

"""ann2label = {
    "Sleep stage W": 0,
    "Sleep stage 1": 1,
    "Sleep stage 2": 2,
    "Sleep stage 3": 3, "Sleep stage 4": 3, # Follow AASM Manual
    "Sleep stage R": 4,
    "Sleep stage ?": 6,
    "Movement time": 5
}
"""


class ESleepState(Enum):
    WAKE = 0
    ONE = 1
    TWO = 2
    THREE = 3
    REM = 4
    MOVEMENT = 5
    UNKNOWN = 6

