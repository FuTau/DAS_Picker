# DAS_Picker

<img src="https://github.com/FuTau/DAS_Picker/blob/main/icon/icon.png" width="100" height="100" alt="描述文本">

---

## 简介
&emps;&emps;分布式光纤声波传感技术（DAS）在近年来飞速发展，其利用瑞利背向散射以测量振动带来的相位变化来得到沿轴向的应变，而它能将光纤变为一系列振动传感器的特点也为我们带来了海量的数据，这为我们对于一些地震信号或者其他信号的筛选带来了挑战，DAS_Picker 的设计目标是一款 **功能强大且易于使用的DAS数据到时拾取软件**，旨在为用户提供 简便易行、用户友好的方式来进行信号的识别和提取，分别包括了指定文件夹h5文件自动检索、异常信息抛出、数据关键属性呈现、DAS数据可视化、数据预处理、频域滤波、FK滤波、单道频谱分析、FK谱分析、长短窗识别、Phasenet-DAS集成、手动拾取调整与模板匹配矫正等功能。

&emps;&emps;将 DAS 应用于地震或者主动源观测已经相对成熟，然而利用传统的地震或者主动源到时拾取工具来进行 DAS 数据处理是相对较为耗时的，该软件旨在通过结合传统的长短窗（STA/LTA）、模板匹配和先进的机器学习技术，并辅以手动到时修正来进行快捷、方便和准确的信号拾取。不仅如此，DAS Picker 还提供了一系列小工具，如 h5 文件拼接、坏道去除、内存建议、波形聚束分析、加速度转换等来进行辅助操作和分析，以便用户能够更好地了解自己的数据。

## 特性
- **主要功能**：支持 指定文件夹h5文件自动检索、异常信息抛出、数据关键属性呈现、DAS数据可视化、数据预处理、频域滤波、FK滤波、单道频谱分析、FK谱分析、长短窗识别、Phasenet-DAS集成、手动拾取调整与模板匹配矫正
- **易于使用**：简洁的用户界面，快速上手。
- **跨平台支持**：Windows、macOS、Linux

## 使用示例
### 文件读取
&emps;&emps;主界面包括三部分，从左到右分别为文件夹管理、主界面画布以及操作面板。当我们点击左侧文件夹管理面板中的第一个 Browse 按钮，点击到存有 h5 文件的文件夹，DAS Picker 会自动检测该文件夹内所有的h5 文件，然后在 Filenames 下方的空白框中会出现所有的 h5 文件名，点击任意一个 h5 文件即可读取数据。

&emps;&emps;在读取文件之后最右侧面板中的 Properties 中会出现一些重要字段，包括"Starttime"、"Trace Num"、"Time Length(s)" 、"Sample Frequency(Hz)" 、 "Spatial Sampling Interval(m)"、"Gauge Length(m)"、"Pulse width(nm)"，读取结果如图。而在操纵面板中的“Show Setting”中可以选择显示的归一化方式，如“Max”，“Z-Score”，“One-bit”或不进行归一化“None”，而在标签页“Preprocess”中提供勾选框（包括去趋势 Detrend，去均值 Demean，尖灭 Taper[默认 5%]，中值滤波 Median，去尖峰噪声 Spike，是否使用归一化数据进行后续处理 Use Norm Data）来供用户进行预处理，这些都需要在载入数据前进行选择。而左侧面板最下方是一个消息盒，用于为用户进行处理提醒和错误提示，用户如需保存日志，可将其复制粘贴到一个 txt 文件中。

&emps;&emps;中间面板是一个画布，底部的工具箱从左到右依次的作用为 1、返回最初视图，2、返回上一步视图，3、到达当前视图的下一步视图，4、移动视图，5、放大所框选的范围，6、配置子图，7、各个轴的控制面板，8、保存当前视图

<img src="https://github.com/FuTau/DAS_Picker/blob/main/gif/文件读取.gif" width="700" height="400" alt="描述文本">

### 频率域滤波-FK滤波以及单道查看
&emps;&emps;而操纵面板中包含除上述提到的功能外，主要功能包括频率滤波Freq Filter、FK 滤波 FK Filter，单道频谱分析，一致性长短窗Coincidence STA/LTA，每道递归长短窗 Recursive STA/LTA，机器学习到时拾取 Phasenet-DAS（From Weiqiang Zhu），手动拾取和修改 Mannual Pick，模板匹配 Templates Matching。而在 FK Filter 面板中可以选择绘制原始数据的 FK 谱和处理过后的数据 FK 谱，同样在单道频谱分析中也可以在输入道号后选择查看原始信号的时频谱还是处理过后数据的时频谱，而底部工具箱也和中间画布面板作用相同。

<img src="https://github.com/FuTau/DAS_Picker/blob/main/gif/频域滤波-FK滤波以及单道查看.gif" width="700" height="400" alt="描述文本">

### 长短窗拾取示例

<img src="https://github.com/FuTau/DAS_Picker/blob/main/gif/长短窗.gif" width="700" height="400" alt="描述文本">
