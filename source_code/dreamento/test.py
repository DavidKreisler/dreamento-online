import json

import os

import numpy as np
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



def read_recording():
    recording_base_path = 'recordings/recording-date-2024-08-05-time-20-18-55/'
    samples_db = np.load(recording_base_path + 'samples_db.npy')
    eegr = []
    eegl = []
    with open(recording_base_path + 'complete.txt', 'r') as f:
        i = 0
        for line in f.readlines():
            elems = line.split(',')
            elems = [float(e.replace('\n', '')) for e in elems]
            eegr.append(elems[0])
            eegl.append(elems[1])
            i += 1

    return eegr, eegl, samples_db

if __name__ == '__main__':
    eegr, eegl, samples_db = read_recording()
    epoch_length_in_samples = 30 * 256 # time_in_seconds * sample_rate

    eegr_30_sec = eegr[:epoch_length_in_samples]
    eegl_30_sec = eegl[:epoch_length_in_samples]

    config_path = 'scripts/SleepScoring/SleePyCo/SleePyCo/configs/SleePyCo-Transformer_SL-10_numScales-3_Sleep-EDF-2018_freezefinetune.json'
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    config['name'] = os.path.basename(config_path).replace('.json', '')

    inf = SleePyCoInference(1, config)
    input = np.array(eegr_30_sec).reshape((1,1,len(eegr_30_sec)))
    pred = inf.infere(input)

    print(pred)

    # len(samples_db) is total length of signal in seconds
    # samples_db tells what line belongs to what second
    # this may be off due to the socket and not taking into account the sampling rate there
