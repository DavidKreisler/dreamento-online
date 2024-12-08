import mne
from datetime import datetime
import requests

from scripts.Connection.ZmaxHeadband import ZmaxHeadband
from scripts.Logic.RecorderThread import RecordThread
from scripts.Utils.yasa_functions import YasaClassifier


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
        self.recordingFinished = True

        self.scoring_predictions = []
        self.epochCounter = 0

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
        self.recorderThread.recordingFinishedSignal.connect(self.on_recording_finished_write_predictions)
        self.recorderThread.sendEEGdata2MainWindow.connect(self.getEEG_from_thread)
        self.recorderThread.sendEpochData2MainWindow.connect(self.get_epoch_for_scoring)

        self.recordingFinished = False

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

    def on_recording_finished_write_predictions(self, fileName):
        self.recordingFinished = True
        if self.scoring_predictions:
            with open(f"{fileName}-predictions.txt", "a") as outfile:
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
            if len(eegSigr) >= 90 * 60 * self.sample_rate:  # only when minimum of 90 mins of signal have been
                # sent, for performance.

                info = mne.create_info(ch_names=['eegr', 'eegl'], sfreq=256, ch_types='eeg')
                mne_array = mne.io.RawArray([eegSigr, eegSigl], info)

                sleep_stages = YasaClassifier.get_preds_per_epoch(mne_array, 'eegl')

                predictionToTransmit = sleep_stages[-1]
                self.scoring_predictions.append((datetime.now(),
                                                 epochCounter,
                                                 predictionToTransmit))

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

    def start_webhook(self):
        try:
            requests.post(self.webHookBaseAdress + 'hello', data={'hello': 'hello'})
            self.webhookActive = True
        except Exception as e:
            #print(e)
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
