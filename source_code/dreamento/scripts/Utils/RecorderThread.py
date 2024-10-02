import os
from datetime import datetime
import time
from PyQt5.QtCore import QThread, pyqtSignal
from pathlib import Path
import numpy as np
from pyedflib import highlevel

from scripts.Connection.ZmaxHeadband import ZmaxDataID, ZmaxHeadband


class RecordThread(QThread):
    recordingProgessSignal = pyqtSignal(int)  # a sending signal to mainWindow - sends time info of ongoing recording to mainWindow
    recordingFinishedSignal = pyqtSignal(str)  # a sending signal to mainWindow - sends name of stored file to mainWindow
    sendEEGdata2MainWindow = pyqtSignal(object, object, int)
    sendEpochData2MainWindow = pyqtSignal(object, object, int)

    def __init__(self, parent=None, signalType=None):
        super(RecordThread, self).__init__(parent)
        if signalType is None:
            signalType = [0, 1, 5, 2, 3, 4]
        self.model_CNNLSTM = None
        self.threadactive = True
        self.signalType = signalType  # "EEGR, EEGL, TEMP, DX, DY, DZ"
        self.stimulationType = ""
        self.secondCounter = 0
        self.dataSampleCounter = 0
        self.totalDataSampleCounter = 0
        self.epochCounter = 0
        self.samples_db = []
        self.sample_rate = 256

    def sendData2main(self, data=None, columns=None):
        self.sendData2MainWindow.emit(data, columns)

    def sendEEGdata2main(self, eegSigR=None, eegSigL=None):
        self.sendEEGdata2MainWindow.emit(eegSigR, eegSigL, self.epochCounter)

    def sendEpochForScoring2main(self, eegSigR=None, eegSigL=None, epochCounter=0):
        self.sendEpochData2MainWindow.emit(eegSigR, eegSigL, epochCounter)

    def run(self):
        # This part of the cord RECORDS signal.
        # In each second, also calculates the sampling rate (# of samples received by program over stream)
        recording = []
        cols = self.signalType
        cols.extend([998, 999])  # add two columns for sample number, sample time
        # cols = [ZmaxDataID.eegr.value, ZmaxDataID.eegl.value, ZmaxDataID.bodytemp.value, 999, 999]  # eegr, eegl, temp, sample number, sample time
        recording.append(cols)  # first row of received data is the col_id. eg: 0 => eegr
        hb = ZmaxHeadband()  # create a new client on the server, therefore we use it only for reading the stream

        now = datetime.now()  # for file name
        dt_string = now.strftime("recording-date-%Y-%m-%d-time-%H-%M-%S")
        file_path = f".\\recordings\\{dt_string}"
        file_name = f"{file_path}\\complete.txt"
        Path(f"{file_path}").mkdir(parents=True, exist_ok=True)  # ensures directory exists

        actual_start_time = time.time()
        print(f'actual start time {actual_start_time}')

        buffer2analyzeIsReady = False
        sendEpochForScoring = False
        dataSamplesToAnalyzeCounter = 0  # count samples, when reach 30*256, feed all to deep learning model
        dataSamplesToAnalyzeBeginIndex = 0
        self.secondCounter = 0
        self.epochCounter = 0  # each epoch is 30 seconds

        sigR_accumulative = []  # accumulate 256*30 data samples and empty it afterward
        sigL_accumulative = []

        while True:
            if self.epochCounter % 60 == 0 and dataSamplesToAnalyzeCounter == 0:
                del hb
                hb = ZmaxHeadband()

            self.dataSampleCounter = 0  # count samples in each second
            self.secondCounter += 1
            self.recordingProgessSignal.emit(
                self.secondCounter)  # send second counter to the mainWindow (then show on button)

            t_end = time.time() + 1

            while time.time() < t_end:
                x = hb.read(cols[:-2])
                if x:
                    for line in x:
                        dataEntry = line
                        dataEntry.extend([self.dataSampleCounter, self.secondCounter])
                        self.dataSampleCounter += 1
                        self.totalDataSampleCounter += 1
                        recording.append(dataEntry)
                        if not buffer2analyzeIsReady:
                            if self.secondCounter >= 2:  # ignore 1st second for analysis, because it is unstable
                                dataSamplesToAnalyzeCounter += 1
                                if dataSamplesToAnalyzeCounter == 1:  # x[dataSamplesToAnalyzeIDXbegin:dataSamplesToAnalyzeIDXbegin+30*256]
                                    sigR_accumulative = []
                                    sigL_accumulative = []

                                if dataSamplesToAnalyzeCounter <= 30 * self.sample_rate:
                                    sigR_accumulative.append(line[ZmaxDataID.eegr.value])
                                    sigL_accumulative.append(line[ZmaxDataID.eegl.value])

                                    if dataSamplesToAnalyzeCounter % self.sample_rate/2 == 0:  # send EEG data for plotting to mainWindow
                                        self.sendEEGdata2main(eegSigR=sigR_accumulative, eegSigL=sigL_accumulative)

                                else:
                                    buffer2analyzeIsReady = True
                                    sendEpochForScoring = True
                                    self.epochCounter += 1

                else:
                    #print("[] data")
                    continue

            self.samples_db.append(self.dataSampleCounter)
            #print(f'{self.dataSampleCounter} samples')
            if buffer2analyzeIsReady:
                # send eeg data of last 30 seconds (30*256 samples) to mainWindow for plotting (spectrogram and periodogram) and sleep scoring
                self.sendEEGdata2main(eegSigR=sigR_accumulative, eegSigL=sigL_accumulative)
                dataSamplesToAnalyzeCounter = 0
                buffer2analyzeIsReady = False

            if sendEpochForScoring:
                if self.secondCounter % 15 == 0:
                    print(f'should send now. epoch {self.secondCounter}')
                    sendEEGr = [sample[0] for sample in recording[-(30*256):]]
                    sendEEGl = [sample[1] for sample in recording[-(30*256):]]
                    self.sendEpochForScoring2main(sendEEGr, sendEEGl, self.epochCounter)

            if self.threadactive is False:
                break  # break the loop if record button is pressed again, recording stops

        actual_end_time = time.time()
        print(f'actual end time {actual_end_time}')
        time_diff = actual_end_time - actual_start_time
        minute = time_diff / 60
        seconds = time_diff % 60
        print(f"actual {minute} minute, {seconds} seconds")

        self.save_edf(recording, cols, file_path)
        np.savetxt(file_name, recording, delimiter=',')  # save recording as txt
        print(f"Recording saved to {file_name}")
        np.save(os.path.join(file_path, 'samples_db.npy'), self.samples_db)

        self.recordingFinishedSignal.emit(f"{file_path}\\{dt_string}")  # send path of recorded file to mainWindow

    def stop(self):
        self.threadactive = False

    def save_edf(self, signals: list, channels: list, path: str):
        # write an edf file
        signals_reformatted = []
        for idx, ch in enumerate(channels):
            signals_reformatted.append([])
            for s in signals:
                signals_reformatted[idx].append(s[idx])

        channel_names = [str(ZmaxDataID(channel)) for channel in channels]
        signal_headers = highlevel.make_signal_headers(channel_names, sample_frequency=256, physical_min=-10000, physical_max=10000)
        header = highlevel.make_header(patientname='patient')
        highlevel.write_edf(os.path.join(path, 'complete_recording.edf'), np.array(signals_reformatted), signal_headers, header)
