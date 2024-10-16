import json

import os

import numpy as np
import scipy.signal
import matplotlib.pyplot as plt

from source_code.dreamento.scripts.SleepScoring.SleePyCoInference import SleePyCoInference
import torch

from models.main_model import MainModel

# chosen signal type:
# [0, 1, 2, 3, 4, 5, 7, 8]
# [
#   0=eegr, 1=eegl, 2=dx, 3=dy, 4=dz, 5=bodytemp,
#   6=bat, 7=noise, 8=light, 9=nasal_l, 10=nasal_r,
#   11=oxy_ir_ac, 12=oxy_r_ac, 13=oxy_dark_ac,
#   14=oxy_ir_dc, 15=oxy_r_dc, 16=oxy_dark_dc
# ]
from source_code.dreamento.scripts.Utils.ESleepStages import ESleepState


def read_recording(path: str):
    samples_db = np.load(path + 'samples_db.npy')
    eegr = []
    eegl = []
    with open(path + 'complete.txt', 'r') as f:
        i = 0
        for line in f.readlines():
            elems = line.split(',')
            elems = [float(e.replace('\n', '')) for e in elems]
            eegr.append(elems[0])
            eegl.append(elems[1])
            i += 1

    return eegr, eegl, samples_db

def get_time_from_seconds(seconds):
    s = int((seconds % (60*60))) % 60
    m = int((seconds - s) / 60) % 60
    h = int((seconds - s - 60*m) / 3600)

    return (f'{h}:{m}:{s}')



if __name__ == '__main__':
    # model
    config_path = 'scripts/SleepScoring/SleePyCo/SleePyCo/configs/SleePyCo-Transformer_SL-10_numScales-3_Sleep-EDF-2018_freezefinetune.json'
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    config['name'] = os.path.basename(config_path).replace('.json', '')

    model = SleePyCoInference(1, config)

    # recording
    eegr, eegl, samples_db = read_recording('recordings/recording-date-2024-10-09-time-01-36-28/')

    epoch_length_in_samples = 30 * 256# time_in_seconds * sample_rate * number of epochs

    start_idx = 0
    end_idx = epoch_length_in_samples
    predictions = []
    predictions_resampled = []

    while end_idx < len(eegr):
        eeg_30_sec = eegr[start_idx:end_idx]
        signal_resampled = scipy.signal.resample(eeg_30_sec, int(100 / 256 * len(eeg_30_sec)))

        input = np.array(eeg_30_sec).reshape(((1,1,len(eeg_30_sec))))
        input_resampled = np.array(signal_resampled).reshape((1, 1, len(signal_resampled)))

        pred = int(model.infere(input)[0])
        pred_resampled = int(model.infere(input_resampled)[0])

        predictions.append((get_time_from_seconds(start_idx/256), ESleepState(int(pred))))
        predictions_resampled.append((get_time_from_seconds(start_idx / 256), ESleepState(int(pred_resampled))))

        start_idx += int(epoch_length_in_samples/2)
        end_idx += int(epoch_length_in_samples/2)

    print(predictions)
    print(predictions_resampled)

