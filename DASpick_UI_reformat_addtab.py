import psutil
from pandas import read_csv
import os
import sys
import warnings
from glob import glob
import matplotlib
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt, QThread, QDateTime
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
from utils import *
from H5_Concate_window import H5Concate
from Beamforming_window import Beamforming
warnings.filterwarnings('ignore', category=DeprecationWarning)
# warnings.filterwarnings('ignore', category = UserWarning)
matplotlib.use("Qt5Agg")

# import os
# import obspy
#
# dirname = os.path.dirname(os.path.dirname(obspy.__file__))
# data_list = [(dirname + '\\' + x, x) for x in os.listdir(dirname) if '-info' in x] + [(dirname + '\\' + x, x) for x in
#                                                                                       os.listdir(dirname) if
#                                                                                       'obspy' in x]
# spec文件加入上面几行，datalist为datas
# print(data_list)
class DASPickerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAS Seismic Wave Picker Author@FuTao")
        # self.resize(1600, 900)
        # self.setStyleSheet("QMainWindow { background-color: #F0FFF0; }")
        self.expiry_date = QDateTime.fromString('2025-06-01', 'yyyy-MM-dd')

        # 检查系统日期是否超过到期日期
        if QDateTime.currentDateTime() > self.expiry_date:
            QMessageBox.warning(None, 'Out of date', 'Your software\'s license has expired. Please contact the sales department to obtain authorization.')
            sys.exit(0)  # 退出程序
        self.data = None
        self.filtered_data = None
        self.file_path = None
        self.threadmark = 0
        self.sub_window = SubWindow()
        self.templates = []
        # 临时存储列表
        self.picks = []  # 存储轨迹点的列表
        self.event_connections = []
        self.meta = {}
        # 最终结果字典
        self.ct = {}
        self.result = {}
        self.templates_cc = {}
        self.templates_raw = {}
        self.templates_ch = {}
        self.templates_time = {}
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # 获取屏幕分辨率
        screen = QDesktopWidget().screenGeometry()
        # 设置窗口的宽度为屏幕的80%，高度为屏幕的85%
        window_width = int(screen.width() * 0.8)
        window_height = int(screen.height() * 0.8)
        # 设置窗口的尺寸
        self.setGeometry(100, 100, window_width, window_height)
        # 设置窗口的最小尺寸
        self.setMinimumSize(window_width, window_height)
        self.center()
        self.create_menu()
        # Layouts
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Left panel: File input
        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignTop)
        main_layout.addLayout(left_panel, 1)

        self.file_label = QLabel("Select Input Folder")
        left_panel.addWidget(self.file_label)

        self.file_entry = QLineEdit()
        left_panel.addWidget(self.file_entry)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)
        left_panel.addWidget(self.browse_button)
        ####################################
        self.output_label = QLabel("Select Output Folder")
        left_panel.addWidget(self.output_label)

        self.output_entry = QLineEdit()
        left_panel.addWidget(self.output_entry)

        self.output_browse_button = QPushButton("Browse Folder")
        self.output_browse_button.clicked.connect(self.browse_folder)
        left_panel.addWidget(self.output_browse_button)
        ######################################
        self.filelist_label = QLabel("Filenames")
        left_panel.addWidget(self.filelist_label)

        self.fileList = QListWidget()
        self.fileList.setStyleSheet("""
            QListView::item {
                border: 0.5px solid #ccc;  /* 网格线颜色 */
                padding: 0.5px;           /* 内边距 */
            }
            QListView::item:hover {
                background-color: #8EE5EE;  /* 鼠标悬停高亮 */
            }
            QListView::item:selected {
                background-color: #8EE5EE;  /* 选中项背景颜色 */
                color: #000000;            /* 选中项文字颜色 */
            }
        """)
        # self.fileList.setFlow(QListView.TopToBottom)
        # self.fileList.setViewMode(QListView.IconMode)
        # self.fileList.setResizeMode(QListView.Adjust)  # 自动调整项大小
        # self.fileList.setSpacing(1)
        # self.fileList.setWrapping(True)  # 启用换行
        left_panel.addWidget(self.fileList)
        self.fileList.itemClicked.connect(self.load_data)
        ########################
        self.message_box_label = QLabel("Message")
        left_panel.addWidget(self.message_box_label)

        self.message_box = QTextEdit()
        self.message_box.setReadOnly(True)  # 设置为只读
        self.message_box.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 设置不自动换行
        left_panel.addWidget(self.message_box)
        # Middle panel: DAS image

        middle_panel = QVBoxLayout()
        middle_panel.setAlignment(Qt.AlignBottom)
        main_layout.addLayout(middle_panel, 4)
        self.figure, self.ax = plt.subplots(figsize=(14,6))
        self.figure.subplots_adjust(top=0.9, bottom=0.15, left=0.08, right=0.95, hspace=0.2, wspace=0.2)
        self.canvas = FigureCanvas(self.figure)
        #####
        # screen_type = [(1280,720),(1366,768),(1360,768),(1600,900),(1920,1080),(1280,800),(1440,900),(1680,1050),(1920,1200),(1280,1024),(800,600),(1024,768),(1280,960),(1400,1050),(1600,1200),(1920,1400),(2048,1536),(3840,2160)]
        # if (window_width,window_height) in screen_type:
        global font_properties
        if screen.width()<=1920:
            font_properties = {"family": "Times New Roman", 'size': 12, 'weight': 'normal'}
        else:
            font_properties = {"family": "Times New Roman", 'size': round(8/1920*(screen.width()-1920))+12, 'weight': 'normal'}
        self.scatters = self.ax.scatter([], [], c="orange", s=5)
        middle_panel.addWidget(self.canvas, 4)
        self.mpl_ntb = NavigationToolbar(self.canvas, self)  # 添加完整的 toolbar,增加图片放大、移动的按钮
        middle_panel.addWidget(self.mpl_ntb)
        middle_panel.setStretch(1,1)

        # Right panel: Control panel
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignTop)

        self.create_preprocess_tabs()
        right_panel.addWidget(self.tab_widget_preprocess)

        self.create_filter_tabs()
        right_panel.addWidget(self.tab_widget_filter)

        self.create_single_trace_analysis()
        right_panel.addWidget(self.tab_widget_single)

        self.create_first_pick()
        right_panel.addWidget(self.tab_widget_first_pick)

        self.create_pick_correction()
        right_panel.addWidget(self.tab_widget_pick_correction)

        self.save_manual_pick_button = QPushButton("Save")
        self.save_manual_pick_button.clicked.connect(self.save_result)
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("Choose save or not:"))
        save_layout.addWidget(self.save_manual_pick_button)
        save_layout.setSpacing(30)
        right_panel.addLayout(save_layout)
        ###################################
        spacer = QWidget()
        spacer.setMinimumHeight(5)
        right_panel.addWidget(spacer)
        self.table_label = QLabel("Properties")
        right_panel.addWidget(self.table_label)
        # layout_table = QVBoxLayout()
        self.property_table = QTableWidget()
        self.property_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.property_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.property_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.property_table.setRowCount(6)
        self.property_table.setColumnCount(2)
        self.property_table.setHorizontalHeaderLabels(["Property", "Value"])

        # layout_table.addWidget(self.property_table)
        # right_panel.addLayout(layout_table)

        right_panel.addWidget(self.property_table)

        tab_style_sheet = generate_tab_style_sheet(min_width=100, max_width=400)
        # 更新所有QTabWidget的样式表
        self.update_all_tabs_style_sheet(tab_style_sheet)

        self.leftqw = QWidget()
        self.centerqw = QWidget()
        self.rightqw = QWidget()
        self.leftqw.setLayout(left_panel)
        self.centerqw.setLayout(middle_panel)
        self.rightqw.setLayout(right_panel)
        main_layout.addWidget(self.rightqw, 1)
        # self.setCentralWidget(self.centerqw)

        right_dock = QDockWidget("Options Panel", self)

        right_dock.setWidget(self.rightqw)# 必须如此才能建立docker窗口
        self.addDockWidget(Qt.RightDockWidgetArea, right_dock)
        right_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

    def create_preprocess_tabs(self):
        self.tab_widget_preprocess = QTabWidget()
        tab_show = QWidget()
        tab_pre = QWidget()

        show_layout = QVBoxLayout()
        show_row1_layout = QHBoxLayout()
        self.norm_combo = QComboBox()
        self.norm_combo.addItems(["Max", "Z-score", "One-bit", 'None'])
        show_row1_layout.addWidget(QLabel("Norm:"))
        show_row1_layout.addWidget(self.norm_combo)
        show_layout.addLayout(show_row1_layout)
        tab_show.setLayout(show_layout)
        self.tab_widget_preprocess.addTab(tab_show,'Show Setting')

        pre_layout = QVBoxLayout()
        pre_row1_layout = QHBoxLayout()
        pre_row2_layout = QHBoxLayout()
        self.detrend_checkbox = QCheckBox('Detrend', self)
        self.demean_checkbox = QCheckBox('Demean', self)
        self.taper_checkbox = QCheckBox('Taper', self)
        self.median_checkbox = QCheckBox('Median', self)

        pre_row1_layout.addWidget(self.detrend_checkbox)
        pre_row1_layout.addWidget(self.demean_checkbox)
        pre_row1_layout.addWidget(self.taper_checkbox)
        pre_row1_layout.addWidget(self.median_checkbox)


        self.spike_removal_checkbox = QCheckBox('Spike', self)
        self.usenormdata_checkbox = QCheckBox('Use Norm Data', self)
        pre_row2_layout.addWidget(self.spike_removal_checkbox)
        pre_row2_layout.addWidget(self.usenormdata_checkbox)

        pre_layout.addLayout(pre_row1_layout)
        pre_layout.addLayout(pre_row2_layout)

        tab_pre.setLayout(pre_layout)
        self.tab_widget_preprocess.addTab(tab_pre, 'Preprocess')
    def create_filter_tabs(self):
        self.tab_widget_filter = QTabWidget()
        tab_freq_filter = QWidget()
        tab_fk_filter = QWidget()

        freq_layout = QHBoxLayout()
        self.low_freq_entry = QDoubleSpinBox()
        self.low_freq_entry.setRange(0, 100)
        self.low_freq_entry.setValue(1)
        self.low_freq_entry.setSuffix(" Hz")
        self.high_freq_entry = QDoubleSpinBox()
        self.high_freq_entry.setRange(0, 2000)
        self.high_freq_entry.setValue(10)
        self.high_freq_entry.setSuffix(" Hz")
        freq_layout.addWidget(QLabel("Low Freq:"))
        freq_layout.addWidget(self.low_freq_entry)
        freq_layout.addWidget(QLabel("High Freq:"))
        freq_layout.addWidget(self.high_freq_entry)
        self.apply_filter_button = QPushButton("Filter")
        self.apply_filter_button.clicked.connect(self.apply_filter)
        freq_layout.addWidget(self.apply_filter_button)
        # freq_layout.setSpacing(30)
        tab_freq_filter.setLayout(freq_layout)
        self.tab_widget_filter.addTab(tab_freq_filter, 'Freq Filter')

        fk_layout = QVBoxLayout()
        fk_apply_layout = QHBoxLayout()
        # 设置低速和高速的 SpinBox
        self.low_vel = QDoubleSpinBox()
        self.low_vel.setRange(0, 5)
        self.low_vel.setValue(1)
        self.low_vel.setSuffix(" km/s")
        self.high_vel = QDoubleSpinBox()
        self.high_vel.setRange(0, 200)
        self.high_vel.setValue(8)
        self.high_vel.setSuffix(" km/s")

        # 添加标签和SpinBox
        fk_apply_layout.addWidget(QLabel("Low vel:"))
        fk_apply_layout.addWidget(self.low_vel)
        fk_apply_layout.addWidget(QLabel("High vel:"))
        fk_apply_layout.addWidget(self.high_vel)

        # 创建并添加Direction下拉菜单
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["left", "right", "both"])
        fk_apply_layout.addWidget(QLabel("Direction:"))
        fk_apply_layout.addWidget(self.direction_combo)

        # 创建并连接"Apply FK Filter"按钮
        self.fk_filter_button = QPushButton("Apply")
        self.fk_filter_button.clicked.connect(self.apply_fk_filter)
        fk_apply_layout.addWidget(self.fk_filter_button)
        fk_layout.addLayout(fk_apply_layout)

        # 添加展示fk域图像的按钮
        fk_show_layout = QHBoxLayout()
        self.fk_show_button = QPushButton("Raw F-K Image")
        self.fk_show_button.clicked.connect(self.plot_fk_raw)
        fk_show_layout.addWidget(self.fk_show_button)
        self.fk_show_pro_button = QPushButton("Processed F-K Image")
        self.fk_show_pro_button.clicked.connect(self.plot_fk)
        fk_show_layout.addWidget(self.fk_show_pro_button)
        fk_layout.addLayout(fk_show_layout)

        tab_fk_filter.setLayout(fk_layout)
        self.tab_widget_filter.addTab(tab_fk_filter, 'FK Filter')
    def create_single_trace_analysis(self):
        self.tab_widget_single = QTabWidget()
        tab_single = QWidget()

        single_layout = QHBoxLayout()
        # single_layout.setSpacing(30)
        self.trace_num = QLineEdit()
        # self.trace_num.setFixedWidth(100)
        single_layout.addWidget(QLabel("Channel:"))
        # single_layout.addSpacing(-80)
        single_layout.addWidget(self.trace_num)
        self.single_button = QPushButton("Original")
        self.single_button.clicked.connect(self.original_spectrogram)
        self.single_processed_button = QPushButton("Processed")
        self.single_processed_button.clicked.connect(self.spectrogram)
        single_layout.addWidget(self.single_button)
        single_layout.addWidget(self.single_processed_button)

        tab_single.setLayout(single_layout)
        self.tab_widget_single.addTab(tab_single, 'Single Trace Analysis')

    def create_first_pick(self):
        self.tab_widget_first_pick = QTabWidget()
        tab_pick = QWidget()
        tab_phasenet_das = QWidget()

        stalta_layout = QVBoxLayout()
        stalta_setting_layout = QHBoxLayout()
        self.sta = QDoubleSpinBox()
        self.sta.setSingleStep(0.1)
        self.sta.setValue(0.3)
        self.sta.setSuffix(" s")
        self.lta = QDoubleSpinBox()
        self.lta.setSingleStep(1)
        self.lta.setValue(3)
        self.lta.setSuffix(" s")

        self.trig_on = QDoubleSpinBox()
        self.trig_on.setValue(3.3)
        self.trig_off = QDoubleSpinBox()
        self.trig_off.setValue(1.3)

        stalta_setting_layout.addWidget(QLabel("STA:"))
        stalta_setting_layout.addWidget(self.sta)
        stalta_setting_layout.addWidget(QLabel("LTA:"))
        stalta_setting_layout.addWidget(self.lta)
        stalta_setting_layout.addWidget(QLabel("trig_on:"))
        stalta_setting_layout.addWidget(self.trig_on)
        stalta_setting_layout.addWidget(QLabel("trig_off:"))
        stalta_setting_layout.addWidget(self.trig_off)
        stalta_layout.addLayout(stalta_setting_layout)

        csl_button_layout = QHBoxLayout()
        # csl_button_layout.setContentsMargins(0, 0, 0, 0)  # 去除默认的边距
        # csl_button_container.setLayout(csl_button_layout)

        # 将按钮添加到水平布局中
        self.stalta_button = QPushButton("Coincidence")
        self.stalta_button.clicked.connect(self.coincidence_stalta)
        csl_button_layout.addWidget(self.stalta_button)

        self.show_sub_window_button = QPushButton("Show Images")
        self.show_sub_window_button.clicked.connect(self.plot_data_in_sub_window)
        csl_button_layout.addWidget(self.show_sub_window_button)

        self.rec_stalta_button = QPushButton("Recursive")
        self.rec_stalta_button.clicked.connect(self.rec_sta_lta)
        csl_button_layout.addWidget(self.rec_stalta_button)

        stalta_layout.addLayout(csl_button_layout)
        # 将水平布局容器添加到右侧面板
        tab_pick.setLayout(stalta_layout)
        self.tab_widget_first_pick.addTab(tab_pick, 'STA/LTA')

        # Phasenet_das
        phasenet_layout = QVBoxLayout()
        env_input_layout = QHBoxLayout()
        phasenet_button_layout = QHBoxLayout()
        self.conda_env_name = QLineEdit()
        # self.trace_num.setFixedWidth(100)
        env_input_layout.addWidget(QLabel("Conda Environment Name:"))
        # single_layout.addSpacing(-80)
        env_input_layout.addWidget(self.conda_env_name)
        # Add the Phasenet_das run button
        self.run_phasenet_button = QPushButton("Run Phasenet_das")
        self.run_phasenet_button.clicked.connect(self.run_phasenet_das)
        phasenet_button_layout.addWidget(self.run_phasenet_button)

        self.run_phasenet_post_button = QPushButton("Run Phasenet_das with STA/LTA")
        self.run_phasenet_post_button.clicked.connect(self.run_phasenet_das_V2)
        phasenet_button_layout.addWidget(self.run_phasenet_post_button)

        phasenet_layout.addLayout(env_input_layout)
        phasenet_layout.addLayout(phasenet_button_layout)
        tab_phasenet_das.setLayout(phasenet_layout)
        self.tab_widget_first_pick.addTab(tab_phasenet_das, 'Phasenet DAS')

    def create_pick_correction(self):
        self.tab_widget_pick_correction = QTabWidget()
        tab_mannul_pick = QWidget()
        tab_templates_matching = QWidget()

        manual_pick_layout = QHBoxLayout()

        # manual_pick_layout.setSpacing(30)
        self.group = QLineEdit()
        # self.group.setFixedWidth(100)
        manual_pick_layout.addWidget(QLabel("Group:"))
        # manual_pick_layout.addSpacing(-80)
        manual_pick_layout.addWidget(self.group)
        # Add the munual pick button
        self.manual_pick_button = QPushButton("Manual Pick")
        self.manual_pick_button.clicked.connect(self.manual_pick)
        manual_pick_layout.addWidget(self.manual_pick_button)

        self.stop_manual_pick_button = QPushButton("Stop")
        self.stop_manual_pick_button.clicked.connect(self.stop_manual_pick)
        manual_pick_layout.addWidget(self.stop_manual_pick_button)
        tab_mannul_pick.setLayout(manual_pick_layout)
        self.tab_widget_pick_correction.addTab(tab_mannul_pick, 'Manual Pick')

        # Template Matching
        TM_layout = QVBoxLayout()
        Template_Matching_control_layout = QHBoxLayout()
        self.cc_min = QDoubleSpinBox()
        # self.cc_min.setFixedWidth(80)
        self.cc_min.setSingleStep(0.1)
        self.cc_min.setValue(0.3)

        self.templates_size = QDoubleSpinBox()
        # self.templates_size.setFixedWidth(80)
        self.templates_size.setSingleStep(0.1)
        self.templates_size.setValue(0.5)
        self.templates_size.setSuffix(" s")

        Template_Matching_control_layout.addWidget(QLabel("CC:"))
        # Template_Matching_control_layout.addSpacing(-90)
        Template_Matching_control_layout.addWidget(self.cc_min)
        # Template_Matching_control_layout.addSpacing(20)
        Template_Matching_control_layout.addWidget(QLabel("Window Size:"))
        # Template_Matching_control_layout.addSpacing(-40)
        Template_Matching_control_layout.addWidget(self.templates_size)
        # Template_Matching_control_layout.addSpacing(20)

        self.Templates_Matching_button = QPushButton("Apply")
        self.Templates_Matching_button.clicked.connect(self.Templates_Matching4result)
        Template_Matching_control_layout.addWidget(self.Templates_Matching_button)

        TM_layout.addLayout(Template_Matching_control_layout)

        Template_Matching_meta_layout = QHBoxLayout()

        self.Templates_meta_button = QPushButton("Template Matching Meta")
        self.Templates_meta_button.clicked.connect(self.plot_Templates_Meta)
        Template_Matching_meta_layout.addWidget(self.Templates_meta_button)

        TM_layout.addLayout(Template_Matching_meta_layout)
        tab_templates_matching.setLayout(TM_layout)
        self.tab_widget_pick_correction.addTab(tab_templates_matching, 'Templates Matching')
    def property_write(self):
        try:
            start_time = self.meta['starttime']
            trace_num = self.meta['nch']
            sample_time = self.meta['time_length']
            sample_frequency = self.meta['fs']
            dx = self.meta['dx']
            gl = self.meta['GaugeLength']
            lamb = self.meta['lamb']
            item_xs = []
            item_xs.append(QTableWidgetItem(f"Starttime"))
            item_xs.append(QTableWidgetItem(f"Trace Num"))
            item_xs.append(QTableWidgetItem(f"Time Length(s)"))
            item_xs.append(QTableWidgetItem(f"Sample Frequency(Hz)"))
            item_xs.append(QTableWidgetItem(f"Spatial Sampling Interval(m)"))
            item_xs.append(QTableWidgetItem(f"Gauge Length(m)"))
            item_xs.append(QTableWidgetItem(f"Pulse width(nm)"))
            for i in range(len(item_xs)):
                item_xs[i].setFlags(item_xs[i].flags() & ~Qt.ItemIsEditable)
                self.property_table.setItem(i, 0, item_xs[i])
            item_ys = []
            item_ys.append(QTableWidgetItem(f"{start_time}"))
            item_ys.append(QTableWidgetItem(f"{trace_num}"))
            item_ys.append(QTableWidgetItem(f"{sample_time}"))
            item_ys.append(QTableWidgetItem(f"{sample_frequency}"))
            item_ys.append(QTableWidgetItem(f"{dx}"))
            item_ys.append(QTableWidgetItem(f"{gl}"))
            item_ys.append(QTableWidgetItem(f"{lamb}"))
            for i in range(len(item_xs)):
                item_ys[i].setFlags(item_ys[i].flags() & ~Qt.ItemIsEditable)
                self.property_table.setItem(i, 1, item_ys[i])
        except Exception as e:
            exception_message = f"Properties Error: {str(e)}"
            self.display_message(exception_message)
    #########Menu Part#########
    def create_menu(self):
        # 创建菜单栏和菜单项
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        tools_menu = menubar.addMenu('Tools')
        license_menu = menubar.addMenu('license')
        about_menu = menubar.addMenu('About')

        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.closeEvent)
        save_action = file_menu.addAction('Save h5')
        save_action.triggered.connect(self.save_h5)

        about_action = about_menu.addAction('Info')
        about_action.triggered.connect(self.author_info)
        # 创建 'Open License' 操作并将其添加到 'License' 菜单
        # license_action =license_menu.addAction('open')
        # license_action.triggered.connect(self.license_open)
        tools_action_1 = tools_menu.addAction('H5 Files Concatenation')
        tools_action_1.triggered.connect(self.h5_concate)
        tools_action_2 = tools_menu.addAction('Delete Bad Traces')
        tools_action_2.triggered.connect(self.Delete_Bad_Traces)

        tools_action_3 = tools_menu.addAction('Convert to Acc')
        tools_action_3.triggered.connect(self.Convert_to_Acc)
        # tools_action_2.triggered.connect(self.tools_1)
        tools_action_4 = tools_menu.addAction('Beamforming')
        tools_action_4.triggered.connect(self.beamforming_win)
        tools_action_5 = tools_menu.addAction('Memory Suggestion')
        tools_action_5.triggered.connect(self.Memory_suggest)

    def h5_concate(self):
        self.h5_concate_window = H5Concate() # 必须加上self
        self.h5_concate_window.show()
    def Memory_suggest(self):
        mem = psutil.virtual_memory()
        self.msg_box = QMessageBox()
        self.msg_box.setWindowTitle("Notice")
        self.msg_box.setText(f"Memory in total: {mem.total / (1024 * 1024):.2f} MB\n"
                             f"Memory available: {mem.available / (1024 * 1024):.2f} MB\n"
                             f"Suggest file size <={mem.available / (1024 * 1024 * 5):.2f} MB")
        self.msg_box.setStyleSheet("QLabel { text-align: left; }")
        self.msg_box.exec_()

    def Delete_Bad_Traces(self):
        if self.data is None:
            self.display_message("No data loaded")
            return
        try:
            good_chn, bad_chn = channel_checking(self.data)
            self.data = np.delete(self.data,bad_chn,axis=0)
            self.x = np.delete(self.x, bad_chn, axis=0)
            self.display_message(f'{bad_chn} are removed...')
            self.plot_data(self.data, self.x, self.t, self.starttime)
        except Exception as e:
            self.display_message(f'Error:{e}')

    def Convert_to_Acc(self):
        if self.data is None:
            self.display_message("No data loaded")
            return
        fmax,iftape = QInputDialog.getText(None, "Input Dialog", "Enter fmax:")
        try:
            fmax = (int(fmax.split(',')[0]),int(fmax.split(',')[1]))
            dx = self.x[1]-self.x[0]
            fs = 1/(self.t[1]-self.t[0])
            # new_data = fk_rescaling(self.data, dx, fs, fmax=fmax)
            new_data = fk_rescaling(self.data, dx, fs)
            self.plot_data(new_data, self.x, self.t, self.starttime)
        except Exception as e:
            self.display_message(f'Error:{e}')


    def save_h5(self):
        if self.data is None:
            self.display_message("No data to be saved")
            return
        if self.filtered_data is None:
            data = self.data
        else:
            data = self.filtered_data.astype(np.float32)
        try:
            new_name = self.FullFilename.split('.h5')[0]+'new.h5'
            with h5py.File(self.FullFilename, "r") as old_fp:
                with h5py.File(new_name, "w") as new_fp:
                    old_fp.copy("Acquisition", new_fp)
                    del new_fp["Acquisition/Raw[0]/RawData"]
                    # 创建新的 "Acquisition/Raw[0]/RawData" 数据集并写入 concated_data
                    new_fp.create_dataset("Acquisition/Raw[0]/RawData", data=data.T)
            del data
        except Exception as e:
            self.display_message(e)

    def beamforming_win(self):
        self.beamforming_window = Beamforming() # 必须加上self
        self.beamforming_window.show()

    def author_info(self):
        self.info_box = QMessageBox()
        self.info_box.setWindowTitle("Author infomation")
        self.info_box.setText(f"This software is designed by Fu Tao,\n"
                             f"If you have any questions, please contact the author's email\n"
                              f"ood@mail.ustc.edu.cn")
        self.info_box.setStyleSheet("QLabel { text-align: left; }")

        self.info_box.exec_()
########################################################
    def center(self):
        # 窗口居中
        screen = QDesktopWidget().availableGeometry()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen.center())
        self.move(frame_geometry.topLeft())

    def resizeEvent(self, event):
        # 动态调整右侧部件宽度为主窗口宽度的四分之一
        main_window_width = self.width()
        new_width = max(300, int(main_window_width // 3.5))  # 保证最小宽度为 200
        self.rightqw.setFixedWidth(new_width)
        super().resizeEvent(event)  # 保持父类的行为

    def update_all_tabs_style_sheet(self, style_sheet):
        # 更新所有QTabWidget的样式表
        # 假设你有一个QTabWidget的列表
        tabs = [self.tab_widget_single,self.tab_widget_filter,self.tab_widget_first_pick,self.tab_widget_pick_correction]  # 这里添加你所有的QTabWidget实例
        for tab in tabs:
            tab.setStyleSheet(style_sheet)

    def closeEvent(self, event):
        print("Closing main application...")
        plt.close('all')  # 关闭所有 Matplotlib 图形窗口
        event.accept()

    def browse_file(self):
        self.file_path = QFileDialog.getExistingDirectory(self, "Load Input Folder")
        if self.file_path:
            self.file_entry.setText(self.file_path)
            self.fileList.clear()
            files = glob(os.path.join(self.file_path, '*.h5'))
            files.sort()
            for f in files:
                self.fileList.addItem(os.path.basename(f))
            # print(files)
            # self.load_data(self.file_path)
            # self.load_data(files[0])

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            self.output_entry.setText(folder_path)

    def display_message(self, message):
        self.message_box.append(message)

    def Changeh5Format(self):
        with h5py.File(self.file_path.split('.h5')[0] + 'phasenet_das.h5', "w") as f:
            ds = f.create_dataset('data', data=self.filtered_data)
            ds.attrs['dt_s'] = self.t[1] - self.t[0]
            ds.attrs['dx_m'] = self.x[1] - self.x[0]
            ds.attrs['begin_time'] = self.starttime.isoformat()

    def load_data(self, file_path):
        self.picks = []  # 存储轨迹点的列表
        self.x_all = []
        self.y_all = []
        self.result = {}
        self.templates_cc = {}
        self.templates_raw = {}
        self.templates_ch = {}
        self.templates_time = {}
        self.FullFilename = os.path.join(self.file_path,file_path.text())
        try:
            # Placeholder for loading DAS data, replace with actual implementation
            self.data, self.x, self.t, self.starttime, self.meta= read_zdh5(self.FullFilename)
            self.preprocess_used()
            self.plot_data(self.data, self.x, self.t, self.starttime)
            self.property_write()
        except Exception as e:
            self.display_message(f"Failed to load data: {e}")

    def preprocess_used(self):
        # 收集选项
        options = {
            "detrend": self.detrend_checkbox.isChecked(),
            "demean": self.demean_checkbox.isChecked(),
            "median": self.median_checkbox.isChecked(),
            "taper": self.taper_checkbox.isChecked(),
            "spike": self.spike_removal_checkbox.isChecked(),
            "usenormdata": self.usenormdata_checkbox.isChecked(),
        }
        all_false = all(not value for value in options.values())
        if all_false:
            pass
        else:
        # 创建线程任务
            options["norm_method"] = self.norm_combo.currentText()
            self.thread = QThread()
            self.worker = PreprocessWorker(self.data, options)
            self.worker.moveToThread(self.thread)
            # 连接信号和槽
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.message.connect(self.display_message)
            self.worker.error.connect(self.display_message)
            self.worker.data_ready.connect(self.update_process_data)

            # 启动线程
            self.thread.started.connect(self.worker.run)
            self.thread.start()

            self.display_message("Preprocess process started...")




    def plot_data(self, data, x, t, starttime):
        self.ax.clear()
        if self.norm_combo.currentText()=='Max':
            normalize = lambda x: (x) / np.max(np.abs(x), axis=-1, keepdims=True)
        elif self.norm_combo.currentText()=='Z-score':
            normalize = lambda x: (x-np.mean(x,axis=-1, keepdims=True)) / np.std(x, axis=-1, keepdims=True)
        elif self.norm_combo.currentText()=='One-bit':
            normalize = lambda x: np.where(x > 0, 1, np.where(x < 0, -1, 0))
        elif self.norm_combo.currentText()=="None":
            normalize = lambda x: x/1
        Qvmin = np.nanpercentile(np.reshape(normalize(data), np.size(data)), 0.005)
        Qvmax = np.nanpercentile(np.reshape(normalize(data), np.size(data)), 99.995)
        self.im = self.ax.imshow(normalize(data).T, cmap="seismic", aspect="auto",vmax=Qvmax,vmin=Qvmin,
                                 extent=[x[0], x[-1], t[-1], t[0]], interpolation="none")
        self.ax.invert_yaxis()
        self.ax.set_title(starttime, **font_properties)
        self.ax.set_xlabel("Distance (m)", **font_properties)
        self.ax.set_ylabel("Time (s)", **font_properties)
        self.ax.tick_params(labelsize=font_properties['size']-1)
        self.canvas.draw()

    def plot_data_in_sub_window(self):
        if not hasattr(self, 'all_cft') or self.all_cft is None:
            self.display_message("Coincedence STA/LTA is needed before display!")
            return
        # 在附属窗口中绘图
        self.sub_window = SubWindow()
        # self.sub_window = SubWindow()
        self.sub_window.show()
        self.sub_window.plot_stalta_data(all_cft=self.all_cft, x=self.x, t=self.t, starttime=self.starttime)
        # self.sub_window.plot_sin()

    def original_spectrogram(self):
        if self.filtered_data is None:
            self.display_message("No data to process")
            return
        try:
            trace_num = int(self.trace_num.text())
        except:
            self.display_message(f'Channel input is needed!')
            return
        self.sub_window = SubWindow()
        if trace_num > self.data.shape[0] or trace_num < 0:
            self.display_message(f'Channel out of range!')
            return
        dt = self.t[1] - self.t[0]
        signal = self.st_unfiltered[trace_num].data
        signal_t = self.st_unfiltered[trace_num].times()
        f, t_spec, Sxx = spectrogram(signal, fs=1 / dt)
        self.sub_window.show()
        self.sub_window.plot_single_data(signal, signal_t, Sxx, t_spec, f)

    def spectrogram(self):
        if self.filtered_data is None:
            self.display_message("No filtered data to process")
            return
        trace_num = int(self.trace_num.text())

        self.sub_window = SubWindow()
        if trace_num is None:
            self.display_message(f'Channel input is needed!')
            return
        if trace_num > self.data.shape[0] or trace_num < 0:
            self.display_message(f'Channel out of range!')
            return
        dt = self.t[1] - self.t[0]
        signal = self.st[trace_num].data
        signal_t = self.st[trace_num].times()
        f, t_spec, Sxx = spectrogram(signal, fs=1 / dt)
        self.sub_window.show()
        self.sub_window.plot_single_data(signal, signal_t, Sxx, t_spec, f)

    def apply_filter(self):
        if self.data is None:
            self.display_message("No data loaded")
            return
        self.threadmark = 1
        # 清空缓存
        self.picks = []  # 存储轨迹点的列表
        self.x_all = []
        self.y_all = []
        self.result = {}
        self.templates_cc = {}
        self.templates_raw = {}
        self.templates_ch = {}
        self.templates_time = {}
        # 获取频率值
        low_freq = self.low_freq_entry.value()
        high_freq = self.high_freq_entry.value()

        # 创建线程和工作类
        self.thread = QThread()
        self.worker = FilterWorker(self.data, self.x, self.t, self.starttime, low_freq, high_freq)
        self.worker.moveToThread(self.thread)

        # 连接信号和槽
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.message.connect(self.display_message)
        self.worker.error.connect(self.display_message)
        self.worker.data_ready.connect(self.update_filtered_data)

        # 启动线程
        self.thread.started.connect(self.worker.run)
        self.thread.start()

        self.display_message("Filter process started...")




    def apply_fk_filter(self):
        if self.filtered_data is None:
            self.display_message("No filtered data to process")
            return
        self.threadmark = 1
        low_vel = self.low_vel.value()  # 低速
        high_vel = self.high_vel.value()  # 高速
        direction_combo = self.direction_combo.currentText()  # 获取方向选择

        self.thread = QThread()
        self.worker = FKFilterWorker(self.filtered_data, self.x, self.t, low_vel, high_vel, direction_combo)
        self.worker.moveToThread(self.thread)

        # 连接信号到不同的槽函数
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.log_message.connect(self.display_message)
        self.worker.error.connect(self.display_message)
        self.worker.data_ready.connect(self.update_fkfiltered_data)

        # 启动线程
        self.thread.started.connect(self.worker.run)
        self.thread.start()


    def plot_fk_raw(self):
        if self.data is None:
            self.display_message("No data loaded")
            return

        self.sub_window = SubWindow()
        dx = self.x[1] - self.x[0]
        dt = self.t[1] - self.t[0]

        self.sub_window.show()
        self.sub_window.plot_fk(self.data, dx, dt, type=None)

    def plot_fk(self):
        if self.filtered_data is None:
            self.display_message("No filtered data to process")
            return

        self.sub_window = SubWindow()
        dx = self.x[1] - self.x[0]
        dt = self.t[1] - self.t[0]

        self.sub_window.show()
        self.sub_window.plot_fk(self.filtered_data, dx, dt, type=None)

    def plot_Templates_Meta(self):
        try:
            group = int(self.group.text())
        except:
            self.display_message(f'Group input is needed!')
            return
        if len(self.templates_cc) == 0 or group not in self.templates_cc.keys():
            self.display_message("Do the Template Matching first!")
            return

        self.sub_window = SubWindow()
        self.sub_window.show()
        self.sub_window.plot_templates_meta(self.templates_raw[group], self.templates_ch[group],
                                            self.templates_time[group], self.templates_cc[group], self.ct[group],
                                            cc_min=self.cc_min.value())

    def coincidence_stalta(self):
        if self.data is None:
            self.display_message("No data loaded")
            return
        if hasattr(self, 'all_cft'):
            del self.all_cft
        if self.filtered_data is None:
            self.display_message("Filtering data is needed")
            return

        # 创建线程和工作对象
        self.thread = QThread()
        self.worker = CoincidenceStaltaWorker(
            self.filtered_data, self.st, self.t, self.starttime,
            self.trig_on.value(), self.trig_off.value(),
            self.sta.value(), self.lta.value()
        )
        self.worker.moveToThread(self.thread)

        # 连接信号和槽
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.log_message.connect(self.display_message)
        self.worker.data_ready.connect(self.update_coin_stalta_results)

        # 启动线程
        self.thread.started.connect(self.worker.run)
        self.thread.start()

        self.display_message("STA/LTA coincidence trigger process started...")

    def rec_sta_lta(self):
        if self.data is None:
            self.display_message("No data loaded")
            return
        if not hasattr(self, 'first_ATestimates') or len(self.first_ATestimates)==0 or len(self.first_ATestimates) is None:
            self.display_message("No Coincidence result is available...")
            return
        # 创建线程和工作对象
        self.thread = QThread()
        self.worker = RecStaLtaWorker(
            self.filtered_data, self.st, self.t, self.x, self.starttime,
            self.trig_on.value(), self.trig_off.value(),
            self.sta.value(), self.lta.value(), self.first_ATestimates
        )
        self.worker.moveToThread(self.thread)

        # 连接信号和槽
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.log_message.connect(self.display_message)
        self.worker.data_ready.connect(self.update_rec_sta_lta_results)

        # 启动线程
        self.thread.started.connect(self.worker.run)
        self.thread.start()

        self.display_message("REC STA/LTA processing started...")

    def run_phasenet_das(self):
        self.display_message("Notice: This button is aimed to view the raw result of Phasenet-DAS!")
        if self.filtered_data is None:
            self.display_message("No data loaded")
            return
        try:
            resultpath = self.output_entry.text()
        except Exception as e:
            self.display_message(e)
        # This function is mainly designed to pick only one earthquake
        self.Changeh5Format()
        ngpu = device_count()
        datapath = os.path.dirname(self.file_path)
        base_cmd = f"EQNet/predict.py --model phasenet_das --data_list=files.txt  --data_path {datapath} --result_path {resultpath} --format=h5  --batch_size 1 --workers 0 --resample_time"
        with open("files.txt", "w") as f:
            f.write(f"{self.file_path.split('.h5')[0]}phasenet_das.h5")
        if ngpu == 0:
            cmd = f"python {base_cmd} --device cpu"
        elif ngpu == 1:
            cmd = f"python {base_cmd}"
        else:
            cmd = f"torchrun --nproc_per_node {ngpu} {base_cmd}"

        self.display_message(cmd)
        # Detect env is exist
        try:
            process = os.popen('conda info -e')
            output = process.read()
            if 'conda environments' and self.conda_env_name.text() in output:
                self.display_message(f"Conda environment {self.conda_env_name.text()} is detected...")
            else:
                self.display_message(f"Conda environment {self.conda_env_name.text()} is NOT detected...")
                return
            process.close()
            process = os.popen(f'conda activate {self.conda_env_name.text()} & {cmd}')
            output = process.read()
            self.display_message(output)
        except Exception as e:
            self.display_message(e)

        picks = read_csv(
            f"{resultpath}/picks_phasenet_das/{os.path.basename(self.file_path).split('.h5')[0]}phasenet_das.csv")
        self.plot_data(self.filtered_data, self.x, self.t, self.starttime)
        color = picks["phase_type"].map({"P": "C0", "S": "C1"})
        dx = self.x[1] - self.x[0]
        dt = self.t[1] - self.t[0]
        self.ax.scatter(picks["channel_index"].values * dx, picks["phase_index"].values * 0.01, c=color, s=5)
        self.ax.scatter([], [], c="C0", label="P")
        self.ax.scatter([], [], c="C1", label="S")
        self.ax.legend()
        self.canvas.draw()

    def run_phasenet_das_V2(self):
        # This function is mainly designed to pick only one earthquake
        if not hasattr(self, 'first_ATestimates') or len(self.first_ATestimates) == 0 or self.first_ATestimates is None:
            self.display_message("Appropriate parameters for Coincidence STA/LTA is needed!")
            return
        if self.filtered_data is None:
            self.display_message("No data loaded")
            return
        try:
            resultpath = self.output_entry.text()
        except Exception as e:
            self.display_message(e)
        self.Changeh5Format()
        ngpu = device_count()
        datapath = os.path.dirname(self.file_path)
        base_cmd = f"EQNet/predict.py --model phasenet_das --data_list=files.txt  --data_path {datapath} --result_path {resultpath} --format=h5  --batch_size 1 --workers 0 --resample_time"
        with open("files.txt", "w") as f:
            f.write(f"{self.file_path.split('.h5')[0]}phasenet_das.h5")
        if ngpu == 0:
            cmd = f"python {base_cmd} --device cpu"
        elif ngpu == 1:
            cmd = f"python {base_cmd}"
        else:
            cmd = f"torchrun --nproc_per_node {ngpu} {base_cmd}"

        self.display_message(cmd)
        # Detect env is exist
        try:
            process = os.popen('conda info -e')
            output = process.read()
            if 'conda environments' and self.conda_env_name.text() in output:
                self.display_message(f"Conda environment {self.conda_env_name.text()} is detected...")
            else:
                self.display_message(f"Conda environment {self.conda_env_name.text()} is NOT detected...")
                return
            process.close()
            process = os.popen(f'conda activate {self.conda_env_name.text()} & {cmd}')
            output = process.read()
            self.display_message(output)
        except Exception as e:
            self.display_message(e)
        Qlta = self.lta.value()
        picks = read_csv(
            f"{resultpath}/picks_phasenet_das/{os.path.basename(self.file_path).split('.h5')[0]}phasenet_das.csv")
        dx = self.x[1] - self.x[0]
        dt = self.t[1] - self.t[0]
        pick_dists = []
        pick_time = []
        for i, first_ATestimate in enumerate(self.first_ATestimates):
            ref = first_ATestimate - self.starttime
            chs = []
            time = []
            phases = []
            for ch in range(self.filtered_data.shape[0]):
                if len(picks[picks['channel_index'] == ch]) == 0:
                    continue
                tmp = picks[picks['channel_index'] == ch]['phase_index'].values * 0.01 - ref
                min_value = min(abs(tmp))
                if min_value > Qlta:  # 这个值应该由用户自己决定
                    continue
                abs_tmp = np.array(abs(tmp))
                time_tmp = tmp[np.argmin(abs_tmp)] + ref
                chs.append(ch)
                time.append(time_tmp)
                df = picks[picks['channel_index'] == ch]

                df = df[df['phase_index'] == round(time_tmp * 100)]
                phase = df['phase_type'].values
                phases.append(phase[0])
            phasenet_dists = np.array(chs) * dx
            phasenet_relative = np.array(time)

            f_relative = interpolate.interp1d(phasenet_dists, phasenet_relative, kind='linear',
                                              bounds_error=False, fill_value="extrapolate")
            pick_dists.append(self.x)
            pick_time.append([element for element in f_relative(self.x)])
            self.result[i] = list(zip(self.x, f_relative(self.x)))

        self.plot_data(self.filtered_data, self.x, self.t, self.starttime)
        for i in range(len(pick_time)):
            # self.ax.scatter(self.x,pick_time[i],color="orange")
            self.scatters = self.ax.scatter(pick_dists[i], pick_time[i], color="orange", s=5)
        self.canvas.draw()

    def on_press(self, event):
        # 获取鼠标的坐标
        if event.xdata is None or event.ydata is None:
            return
        if event.button == 1:
            self.update_coordinates(event.xdata, event.ydata)
        if event.button == 3:  # 右键处理
            self.handle_right_click(event.xdata, event.ydata)

    def on_MouseMove(self, event):
        # 获取鼠标的坐标
        if event.xdata is None or event.ydata is None:
            return
        if event.button == 1:
            self.update_coordinates(event.xdata, event.ydata)
        if event.button == 3:  # 右键处理
            self.handle_right_click(event.xdata, event.ydata)

    def update_coordinates(self, x, y):
        self.picks.append((x, y))
        self.update_scatter()

    def handle_right_click(self, x, y):
        # 右键点击处理
        """删除距离指定坐标较近的点并更新 scatter 绘图"""
        self.picks = [
            (px, py) for px, py in self.picks if abs(px - x) >= self.data.shape[0]/100 or abs(py - y) >= self.data.shape[1]/100
        ]
        self.update_scatter()

    def update_scatter(self):
        self.scatters.set_offsets(self.picks)
        self.canvas.draw()

    def manual_pick(self):
        if self.data is None:
            self.display_message("No data to pick")
            return
        try:
            group = int(self.group.text())
        except:
            self.display_message(f'Group input is needed!')
            return
        self.display_message(f'Manual pick mode...')

        if group not in self.result:
            self.picks = []  # 重置轨迹点列表
            if self.scatters:
                self.scatters.remove()
            # self.plot_data(self.filtered_data, self.x, self.t, self.starttime)
            # self.canvas.draw()
            self.scatters = self.ax.scatter([], [], c="orange", s=5)
            self.canvas.draw()
        else:
            self.picks = self.result[group]  # 重置轨迹点列表
            self.scatters.remove()  # 这一步非常重要
            self.scatters = self.ax.scatter([], [], c="orange", s=5)
            self.update_scatter()

        self.event_connections.append(self.canvas.mpl_connect('motion_notify_event', self.on_MouseMove))
        self.event_connections.append(self.canvas.mpl_connect('button_press_event', self.on_press))

    def stop_manual_pick(self):
        try:
            group = int(self.group.text())
        except ValueError:
            self.display_message('Group input is needed!')
            return
        if len(self.picks) == 0:
            self.display_message("Please Do Manual Pick First!")
            return
        x, y = list(zip(*self.picks))
        func = interpolate.interp1d(x, y, kind='linear',
                                    bounds_error=False, fill_value="extrapolate")
        y_new = func(self.x)
        self.picks = list(zip(self.x, y_new))
        self.result[group] = self.picks
        self.update_scatter()

        # 断开事件连接
        for connection in self.event_connections:
            self.canvas.mpl_disconnect(connection)
        self.event_connections.clear()  # 清空连接列表
        self.display_message("Manual pick stopped")

    # def save_result(self):
    #     output_folder = self.output_entry.text()
    #     if not self.result:
    #         self.display_message("No Pick result!")
    #         return
    #     dx = self.x[1] - self.x[0]
    #     for key, pick_list in self.result.items():
    #         # 为每个键创建一个文件名 (例如 'key1.csv', 'key2.csv' 等)
    #         filename = f"{output_folder}/{key}.csv"
    #
    #         # 打开文件进行写入
    #         with open(filename, mode='w', newline='') as file:
    #             writer = csv.writer(file)
    #
    #             # 写入列头
    #             writer.writerow(['Channel', 'Times'])
    #
    #             # 写入每个元组
    #             for value_tuple in pick_list:
    #                 value_tuple = list(value_tuple)
    #                 value_tuple[0] = str(round(value_tuple[0]/dx))
    #                 value_tuple[1] = str(value_tuple[1])
    #                 writer.writerow(value_tuple)
    def Templates_Matching4result(self):
        if not self.result:
            self.display_message('The result of the previous step is empty')
            return
        self.threadmark = 1
        # 创建线程和工作对象
        self.thread = QThread()
        self.worker = TemplatesMatchingWorker(
            self.result, self.x, self.t, self.starttime, self.st,
            self.filtered_data, self.templates_size.value(), self.cc_min.value()
        )
        self.worker.moveToThread(self.thread)

        # 连接信号和槽
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.log_message.connect(self.display_message)
        self.worker.data_ready.connect(self.update_templates_matching_results)

        # 启动线程
        self.thread.started.connect(self.worker.run)
        self.thread.start()

        self.display_message("Template matching processing started...")

    def save_result(self):
        output_folder = self.output_entry.text()
        if not self.result:
            self.display_message("No Pick result!")
            return
        dx = self.x[1] - self.x[0]

        for key, pick_list in self.result.items():
            # 为每个键创建一个文件名 (例如 'key1.txt', 'key2.txt' 等)
            filename = f"{output_folder}/{os.path.basename(self.FullFilename).split('.h5')[0]}_{key}.txt"

            # 打开文件进行写入
            with open(filename, mode='w', newline='') as file:
                # 你可以选择使用空格或制表符等分隔符
                for value_tuple in pick_list:
                    value_tuple = list(value_tuple)
                    value_tuple[0] = str(round(value_tuple[0] / dx))
                    value_tuple[1] = str(value_tuple[1])

                    # 将元组写入txt文件，使用空格作为分隔符
                    file.write(f"{value_tuple[0]} {value_tuple[1]}\n")

            self.display_message(f"Result saved as {filename}.")

    def update_filtered_data(self, filtered_data, st, st_unfiltered):
        # 更新主线程变量
        self.threadmark = 0
        self.filtered_data = filtered_data
        self.st = st
        self.st_unfiltered = st_unfiltered
        self.display_message("Filtered data updated successfully.")

        # 调用绘图函数
        self.plot_data(filtered_data, self.x, self.t, self.starttime)

    def update_process_data(self, processed_data):
        self.threadmark = 0
        self.data = processed_data
        self.plot_data(self.data, self.x, self.t, self.starttime)
        self.display_message("Processed data updated successfully.")
    def update_fkfiltered_data(self, filtered_data):
        # 更新主线程变量
        self.filtered_data = filtered_data
        self.threadmark = 0
        self.display_message("FK Filtered data updated successfully.")

        # 调用绘图函数
        self.plot_data(filtered_data, self.x, self.t, self.starttime)

    def update_coin_stalta_results(self, all_cft, trig_times):
        self.all_cft = all_cft
        if len(trig_times)!=0:
            self.first_ATestimates = [UTCDateTime(tt) for tt in trig_times]

            # 在图上绘制触发结果
            for first_ATestimate in self.first_ATestimates:
                self.ax.axhline(y=first_ATestimate - self.starttime, color='red', linestyle='--')
            self.canvas.draw()
            self.display_message("STA/LTA processing completed.")
        else:
            self.display_message("No Coincidence STA/LTA result available.")

    def update_rec_sta_lta_results(self, pick_dists, pick_time, result):
        self.result = result
        self.threadmark = 0
        # 绘制结果
        self.plot_data(self.filtered_data, self.x, self.t, self.starttime)
        self.scatters = self.ax.scatter(pick_dists, pick_time, color="orange", s=5)
        self.canvas.draw()

        self.display_message("REC STA/LTA processing completed.")

    def update_templates_matching_results(self, result, pick_dists, pick_time, templates_cc,templates_raw,template_ch,templates_time,ctss):
        self.result = result
        self.templates_cc = templates_cc
        self.templates_time = templates_time
        self.templates_raw = templates_raw
        self.templates_ch = template_ch
        self.threadmark = 0
        self.ct = ctss
        # 更新轨迹点和散点图
        for g in self.result.keys():
            self.picks = self.result[g]
            if hasattr(self, 'scatters') and self.scatters:
                self.scatters.remove()
            self.scatters = self.ax.scatter(pick_dists, pick_time, c="orange", s=5)
            self.update_scatter()

        self.display_message("Template matching completed.")


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
