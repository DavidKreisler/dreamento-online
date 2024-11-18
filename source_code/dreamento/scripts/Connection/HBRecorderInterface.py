import mne
import scipy.signal
import yasa
from datetime import datetime, timedelta
import os
import time
import json
import numpy as np
import requests

from scripts.Connection.ZmaxHeadband import ZmaxHeadband
from scripts.Utils.RecorderThread import RecordThread
from scripts.Utils.ESleepStages import ESleepState
from scripts.SleepScoring.SleePyCoInference import SleePyCoInference
from scripts.UI.EEGPlotWindow import EEGVisThread


class HBRecorderInterface:
    def __init__(self):
        self.sample_rate = 256
        self.scoring_sample_rate = 100
        self.signalType = [0, 1, 2, 3, 4, 5, 7, 8]
        # [
        #   0=eegr, 1=eegl, 2=dx, 3=dy, 4=dz, 5=bodytemp,
        #   6=bat, 7=noise, 8=light, 9=nasal_l, 10=nasal_r,
        #   11=oxy_ir_ac, 12=oxy_r_ac, 13=oxy_dark_ac,
        #   14=oxy_ir_dc, 15=oxy_r_dc, 16=oxy_dark_dc
        # ]

        self.hb = None
        self.recorderThread = None
        self.isConnected = False

        self.isRecording = False
        self.firstRecording = True

        # stimulations
        self.stimulationDataBase = {}  # have info of all triggered stimulations

        # scoring
        self.sleepScoringConfigPath = 'scripts/SleepScoring/SleePyCo/SleePyCo/configs/SleePyCo-Transformer_SL-10_numScales-3_Sleep-EDF-2018_freezefinetune.json'
        with open(self.sleepScoringConfigPath, 'r') as config_file:
            config = json.load(config_file)
        config['name'] = os.path.basename(self.sleepScoringConfigPath).replace('.json', '')
        self.sleepScoringConfig = config

        #self.inferenceModel = None
        self.scoring_predictions = []
        self.epochCounter = 0

        # visualization
        self.eegThread = None

        # program parameters
        self.scoreSleep = False

        # webhook
        self.webHookBaseAdress = "http://127.0.0.1:5000/webhookcallback/"
        self.webhookActive = False

    def connect_to_software(self):
        self.hb = ZmaxHeadband()
        if self.hb.readSocket is None or self.hb.writeSocket is None:  # HDServer is not running
            print('Sockets can not be initialized.')
        else:
            self.isConnected = True
            print('Connected')

    def start_recording(self):
        if self.isRecording:
            return

        self.recorderThread = RecordThread(signalType=self.signalType)

        if self.firstRecording:
            self.firstRecording = False

        self.isRecording = True

        self.recorderThread.start()

        self.recorderThread.finished.connect(self.on_recording_finished)
        self.recorderThread.recordingFinishedSignal.connect(self.on_recording_finished_write_stimulation_db)
        self.recorderThread.sendEEGdata2MainWindow.connect(self.getEEG_from_thread)
        self.recorderThread.sendEpochData2MainWindow.connect(self.get_epoch_for_scoring)

        print('recording started')

    def stop_recording(self):
        if not self.isRecording:
            return

        self.recorderThread.stop()
        self.recorderThread.quit()
        self.isRecording = False
        print('recording stopped')

    def on_recording_finished(self):
        # when the recording is finished, this function is called
        self.isRecording = False

        # send signal to webhook if it is running
        if self.webhookActive:
            requests.post(self.webHookBaseAdress + 'finished')
        print('recording finished')

    def on_recording_finished_write_stimulation_db(self, fileName):
        print('on_recording_finished called')
        # save triggered stimulation information on disk:
        with open(f'{fileName}-markers.json', 'w') as fp:
            json.dump(self.stimulationDataBase, fp, indent=4, separators=(',', ': '))

        with open(f"{fileName}-predictions.txt", "a") as outfile:
            if self.scoring_predictions:
                # stagesList = ['W', 'N1', 'N2', 'N3', 'REM', 'MOVE', 'UNK']
                self.scoring_predictions.insert(0, (
                datetime.now(), -1))  # first epoch is not predicted, therefore put -1 instead
                outfile.write("\n".join(str(time) + ': ' + str(item) for time, item in self.scoring_predictions))

    def start_scoring(self):
        self.scoreSleep = True
        print('scoring started')

    def stop_scoring(self):
        self.scoreSleep = False
        print('scoring stopped')

    def get_epoch_for_scoring(self, eegSigr=None, eegSigl=None, epochCounter=0):
        if self.scoreSleep:
            # inference
            if len(eegSigr) >= 5 * 60 * self.sample_rate:  # only when minimum of 5 mins of signal have been sent.
                # to perform sleep scoring of a 5 min single channel signal
                info = mne.create_info(ch_names=['AF8-AFZ'], sfreq=256, ch_types='eeg')
                mne_array = mne.io.RawArray([eegSigr], info)

                y_pred = yasa.SleepStaging(mne_array, eeg_name="AF8-AFZ").predict()

                # since this happens every 15 seconds we are only interested in the period from 2:30 to 3:00 in the signal
                # the rest of the interval is needed by the yasa module as context
                predictionToTransmit = y_pred[5]
                self.scoring_predictions.append((datetime.now() - timedelta(minutes=2), predictionToTransmit))

                if self.webhookActive:
                    data = {'state': predictionToTransmit,
                            'epoch': self.epochCounter}
                    try:
                        requests.post(self.webHookBaseAdress + 'sleepstate', data=data)
                    except Exception as e:
                        print(e)
                        print('webhook is probably not available')

    def getEEG_from_thread(self, eegSignal_r, eegSignal_l, epoch_counter=0):
        self.epochCounter = epoch_counter

        if self.eegThread and self.eegThread.is_alive():
            sigR = eegSignal_r
            sigL = eegSignal_l
            t = [number / self.sample_rate for number in range(len(eegSignal_r))]
            self.eegThread.update_plot(t, sigR, sigL)

    def show_eeg_signal(self):
        if not self.eegThread:
            self.eegThread = EEGVisThread()

        if self.eegThread.is_alive():
            self.eegThread.stop()
        else:
            self.eegThread.start()

    def start_webhook(self):
        try:
            requests.post(self.webHookBaseAdress + 'hello', data={'hello': 'hello'})
            self.webhookActive = True
        except Exception as e:
            print(e)
            print('webhook seems to be offline. not activating')
            return
        print('webhook started')

    def stop_webhook(self):
        self.webhookActive = False
        print('webhook stopped')

    def set_signaltype(self, types: list = []):
        self.signalType = types

    def quit(self):
        if self.recorderThread:
            self.stop_recording()

        if self.eegThread and self.eegThread.isRunning():
            self.eegThread.stop()
            self.eegThread.quit()
