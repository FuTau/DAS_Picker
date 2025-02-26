# -*- coding: utf-8 -*-
import matplotlib
from DASpick_UI_reformat_addtab import DASPickerApp
from PyQt5.QtCore import Qt, QThread, QDateTime, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QWidget, QLabel, QPushButton,
                             QFileDialog, QLineEdit, QVBoxLayout, QComboBox, QTextEdit, QListWidget, QListView,
                             QTableWidget, QSizePolicy, QHeaderView, QTableWidgetItem, QDesktopWidget, QDockWidget,
                             QTabWidget, QCheckBox, QMessageBox, QInputDialog, QDoubleSpinBox)
import sys
import warnings

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
