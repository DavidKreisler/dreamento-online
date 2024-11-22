import sys
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg
import numpy as np


class EEGWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.sample_rate = 256
        self.desiredXrange = 60

        # Set up the main window
        self.setWindowTitle('EEX Plot')
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget and set the layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create a PlotWidget and add it to the layout
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setYRange(-500, 500)
        self.layout.addWidget(self.plot_widget)

        # orig
        self.EEGLinePen1 = pg.mkPen(color=(100, 90, 150), width=1.5)
        self.EEGLinePen2 = pg.mkPen(color=(90, 170, 160), width=1.5)

        t = [number / self.sample_rate for number in range(self.sample_rate * 30)]  # sample_rate * 30 seconds

        self.eegLine1 = self.plot_widget.plot(t, np.random.randn(30 * self.sample_rate), self.EEGLinePen1)
        self.eegLine2 = self.plot_widget.plot(t, np.random.randn(30 * self.sample_rate), self.EEGLinePen2)

    def update_plot(self, t, sigR, sigL):
        """Update the plot with new data."""
        self.eegLine1.setData(t, sigR, pen=self.EEGLinePen1)
        self.eegLine2.setData(t, sigL, pen=self.EEGLinePen2)

        displayedXrangeCounter = len(sigL)  # for plotting Xrange — number of displayed samples on screen

        sec = int(np.floor(displayedXrangeCounter / self.sample_rate))
        if sec % self.desiredXrange == 0:
            random_reset_timer_variable = 30
            k = int(np.floor(sec / self.desiredXrange))
            if self.desiredXrange * k < random_reset_timer_variable:
                xMin = self.desiredXrange * k
                xMax = self.desiredXrange * (k + 1)
            else:
                xMin = 0
                xMax = self.desiredXrange
            a_X = self.plotWidget.getAxis('bottom')
            ticks = range(xMin, xMax, 1)
            a_X.setTicks([[(v, str(v)) for v in ticks]])
            self.plotWidget.setXRange(xMin, xMax, padding=0)


class EEGWorker(QObject):
    data_ready = pyqtSignal(list, list, list)  # Signals will carry t, sigR, sigL

    def __init__(self):
        super().__init__()

    def update_plot(self, t, sigR, sigL):
        # Emit the signal to send data to the GUI thread
        self.data_ready.emit(t, sigR, sigL)


class EEGVisThread(QThread):
    def __init__(self):
        super().__init__()
        self.window = None
        self.worker = None
        self.running = False

    def run(self):
        self.app = QApplication(sys.argv)

        self.window = EEGWindow()
        self.worker = EEGWorker()

        self.worker.data_ready.connect(self.window.update_plot)
        self.window.show()

        self.app.exec_()

    def update_plot(self, t, sigR, sigL):
        if self.worker:
            self.worker.update_plot(t, sigR, sigL)

    def is_alive(self):
        return self.isRunning()

    def stop(self):
        self.app.quit()
        self.app.exit()
