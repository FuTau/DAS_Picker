# -*- coding: utf-8 -*-
from DASpick_UI_reformat_addtab import DASPickerApp
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import psutil
from pandas import read_csv
import os
import sys
import warnings
from glob import glob
import matplotlib
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt, QThread, QDateTime, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QWidget, QLabel, QPushButton,
                             QFileDialog, QLineEdit, QVBoxLayout, QComboBox, QTextEdit, QListWidget, QListView,
                             QTableWidget, QSizePolicy, QHeaderView, QTableWidgetItem, QDesktopWidget, QDockWidget,
                             QTabWidget, QCheckBox, QMessageBox, QInputDialog)
from PyQt5.QtWidgets import QDoubleSpinBox
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas)
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from scipy.interpolate import interpolate
from scipy.signal import spectrogram
from workerthread import FilterWorker, FKFilterWorker, CoincidenceStaltaWorker, RecStaLtaWorker, \
    TemplatesMatchingWorker, PreprocessWorker
from subwindow import SubWindow
from DASpick_UI_reformat_addtab import DASPickerApp
from PyQt5.QtCore import Qt, QThread, QDateTime, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QWidget, QLabel, QPushButton,
                             QFileDialog, QLineEdit, QVBoxLayout, QComboBox, QTextEdit, QListWidget, QListView,
                             QTableWidget, QSizePolicy, QHeaderView, QTableWidgetItem, QDesktopWidget, QDockWidget,
                             QTabWidget, QCheckBox, QMessageBox, QInputDialog, QDoubleSpinBox)
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas,
                                                NavigationToolbar2QT as NavigationToolbar)
from scipy.interpolate import interpolate, interp1d
from scipy.signal import spectrogram, detrend, find_peaks
from scipy.ndimage import median_filter
from scipy.signal.windows import tukey
from workerthread import FilterWorker, FKFilterWorker, CoincidenceStaltaWorker, RecStaLtaWorker, \
    TemplatesMatchingWorker, PreprocessWorker
from subwindow import SubWindow
from utils import *
import cmath
import os
import sys
import warnings
from glob import glob
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.basemap import Basemap
from geopy.distance import geodesic
import numpy as np
from scipy import signal
from scipy.fft import fft2, ifft2, fftshift, ifftshift, rfft, rfft2, irfft2, fftfreq, rfftfreq
from obspy.core import Trace
import pandas as pd
from PyQt5.QtGui import QFont
from obspy.signal.array_analysis import array_processing
from copy import deepcopy
import h5py
from obspy import UTCDateTime
from concurrent.futures import ThreadPoolExecutor
import subprocess
import platform

warnings.filterwarnings('ignore', category=DeprecationWarning)
# warnings.filterwarnings('ignore', category = UserWarning)
matplotlib.use("Qt5Agg")

if __name__ == "__main__":
    from PyQt5.QtGui import QFont

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily("Times New Roman")
    font.setPointSize(11)
    app.setFont(font)

    main_window = DASPickerApp()
    main_window.show()
    sys.exit(app.exec_())
    gc.collect()
