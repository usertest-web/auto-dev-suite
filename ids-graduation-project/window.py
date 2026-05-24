# -*- coding: utf-8 -*-
# @Author : Code_ts
# @Time : 2023/5/4 下午4:29
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMainWindow, QWidget, QPushButton,
                              QLabel, QLineEdit, QGridLayout, QMessageBox, QVBoxLayout,
                              QHBoxLayout, QProgressBar, QSizePolicy, QFrame)
from PyQt5 import QtWidgets
from main import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
import pandas as pd
import csv
from datetime import datetime
from PyQt5 import QtGui
from model import *
import sys
import torch
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from ui.register import Ui_Register_MainWindow
from ui.login_ts import Ui_Login_MainWindow
from torch.utils.data import DataLoader, TensorDataset

# ==================== 特征转图像函数 ====================
def feature_row_to_image(feature_row, save_path="flow_sample.png", img_size=32):
    """
    将一条流量特征向量转换为灰度图并保存。
    feature_row: 一维特征向量（numpy 数组或可转为数组）
    """
    vec = np.array(feature_row, dtype=np.float32)

    # 归一化到 [0, 1]
    v_min, v_max = float(vec.min()), float(vec.max())
    if v_max > v_min:
        vec = (vec - v_min) / (v_max - v_min)
    else:
        vec = np.zeros_like(vec)

    # 补齐/截断到 img_size * img_size
    need_len = img_size * img_size
    if vec.shape[0] < need_len:
        pad = need_len - vec.shape[0]
        vec = np.pad(vec, (0, pad), mode="constant")
    else:
        vec = vec[:need_len]

    img = vec.reshape(img_size, img_size)
    plt.imsave(save_path, img, cmap="gray")
    return save_path

# ==================== 登录界面类（原始版，已修正跳转逻辑） ====================
class Login_class(QMainWindow, Ui_Login_MainWindow):
    def __init__(self, parent=None):
        super(Login_class, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('恶流量分析系统')
        # 登录按钮与用户名密码固定的验证函数相绑定
        self.pushButton.clicked.connect(self.on_pushButton_enter_clicked)
        self.pushButton_2.clicked.connect(self.exit)
        self.pushButton_3.clicked.connect(self.zhuce)

    def exit(self):
        QtWidgets.qApp.quit()

    def zhuce(self):
        # 注意：这里需要实例化注册窗口，但注册窗口类 Regist_class 在下面有定义
        # 为了防止循环导入，我们在函数内部临时导入
        self.regist_window = Regist_class()
        self.regist_window.show()
        self.close()

    def on_pushButton_enter_clicked(self, text):
        # 读取输入
        input_username = self.lineEdit.text()
        input_password = self.lineEdit_2.text()

        # 读取 userinfo.csv 验证
        with open('userinfo.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                username, password = row[:2]  # 前两列是用户名和密码
                if input_username == username:
                    if input_password == password:
                        # 登录成功
                        msg = QMessageBox()
                        msg.setText('输入正确,跳转至主界面')
                        msg.exec_()
                        print("密码正确")
                        print("输入正确,跳转至主界面")

                        # === ✅ 修正后的跳转逻辑 ===
                        self.main_window = Main_class()  # 创建主窗口
                        self.main_window.show()          # 显示主窗口
                        self.close()                     # 关闭当前登录窗口
                        return
                    else:
                        msg = QMessageBox()
                        msg.setText('密码不正确')
                        msg.exec_()
                        print("密码不正确")
                        return
        # 用户名未找到
        msg = QMessageBox()
        msg.setText('用户名不正确')
        msg.exec_()
        print("用户名不正确")

# ==================== 注册界面类 ====================
class Regist_class(QMainWindow, Ui_Register_MainWindow):
    def __init__(self, parent=None):
        super(Regist_class, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('流量分析系统')
        self.pushButton_3.clicked.connect(self.zhucehanshu)
        self.pushButton_2.clicked.connect(self.exit)

    def zhucehanshu(self):
        global user_page
        global user_yema
        global user_dangqianye

        username = self.lineEdit.text()
        password0 = self.lineEdit_2.text()
        password1 = self.lineEdit_3.text()

        if len(username) == 0 or len(password0) == 0 or len(password1) == 0:
            QMessageBox.information(self, '提示', '账号、用户与密码不得为空')
        elif password0 != password1:
            QMessageBox.information(self, '提示', '两次密码不一样')
        elif len(password0) < 3:
            QMessageBox.information(self, '提示', '密码必须大于3位')
        else:
            # 检查用户名是否已存在
            with open('userinfo.csv', 'r') as file:
                reader = csv.reader(file)
                data_list = [row[0] for row in reader]
                if username in data_list:
                    QMessageBox.information(self, '提示', '用户名已存在')
                    return

            # 写入新用户
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('userinfo.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([username, password0, current_time])
                QMessageBox.information(self, "消息", "注册成功！")

        # 清空输入框
        self.lineEdit.clear()
        self.lineEdit_2.clear()
        self.lineEdit_3.clear()

    def exit(self):
        self.close()
        # 重新显示登录窗口（需要全局变量，这里简单处理：创建新的登录窗口）
        # 更好的做法是用信号，但为了简化，直接创建新实例
        self.login_window = Login_class()
        self.login_window.show()

# ==================== 主界面类 ====================
class Main_class(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(Main_class, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("流量检测系统")
        # 窗口尺寸优化
        self.resize(1200, 800)
        self.setMinimumSize(1100, 700)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - 1200) // 2, (screen.height() - 800) // 2)

        # ========== 表格配置 ==========
        for tw in [self.tableWidget, self.tableWidget_2]:
            tw.setAlternatingRowColors(True)
            tw.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            tw.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            tw.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tw.horizontalHeader().setStretchLastSection(True)
            tw.setSortingEnabled(True)
            tw.verticalHeader().setDefaultSectionSize(30)

        # ========== 状态栏 ==========
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("就绪")

        # 信号连接
        self.read_button.clicked.connect(self.loadcsv)
        self.upload_pic_5.clicked.connect(self.detect)
        self.upload_pic_6.clicked.connect(self.view)

        # ========== 可视化页面 — 嵌入交互式图表 ==========
        self._setup_embedded_charts()

        # ========== 图像识别标签页 ==========
        self._setup_image_recognition_tab()

    def _setup_embedded_charts(self):
        """将可视化 Tab 中的静态 QLabel 替换为交互式 matplotlib 画布"""
        # --- 柱状图区域 ---
        self.bar_figure = Figure(figsize=(6, 4), dpi=100)
        self.bar_canvas = FigureCanvas(self.bar_figure)
        self.bar_toolbar = NavigationToolbar(self.bar_canvas, self.text_widget_2)

        # 替换 label_2 的父布局,用 canvas 替代
        bar_layout = self.text_widget_2.layout()
        # 找到 label_2 的索引并移除
        for i in range(bar_layout.count()):
            if bar_layout.itemAt(i).widget() == self.label_2:
                old_label = bar_layout.takeAt(i)
                old_label.widget().deleteLater()
                break
        bar_layout.insertWidget(1, self.bar_canvas)
        bar_layout.addWidget(self.bar_toolbar)

        # --- 饼图区域 ---
        self.pie_figure = Figure(figsize=(5, 4), dpi=100)
        self.pie_canvas = FigureCanvas(self.pie_figure)
        self.pie_toolbar = NavigationToolbar(self.pie_canvas, self.text_widget_3)

        pie_layout = self.text_widget_3.layout()
        for i in range(pie_layout.count()):
            if pie_layout.itemAt(i).widget() == self.label_11:
                old_label = pie_layout.takeAt(i)
                old_label.widget().deleteLater()
                break
        pie_layout.insertWidget(1, self.pie_canvas)
        pie_layout.addWidget(self.pie_toolbar)

    def _setup_image_recognition_tab(self):
        """创建美化后的图像识别标签页"""
        self.image_tab = QWidget()
        self.image_tab.setStyleSheet("background-color: #f8f9fb;")
        layout = QVBoxLayout(self.image_tab)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ---- 标题 ----
        title = QLabel("图像流量识别")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50; background: transparent;")
        layout.addWidget(title)

        # ---- 图片卡片 ----
        card = QFrame()
        card.setObjectName("image_card")
        card.setStyleSheet("QFrame#image_card { background-color: #ffffff; border: 1px solid #e0e4e8; border-radius: 10px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)

        self.flow_image_label = QLabel()
        self.flow_image_label.setAlignment(Qt.AlignCenter)
        self.flow_image_label.setMinimumHeight(320)
        self.flow_image_label.setStyleSheet(
            "background-color: #f5f6f8; border: 2px dashed #d0d5dd; border-radius: 8px; color: #999; font-size: 14px;"
        )
        self.flow_image_label.setText("请上传流量图像\n（支持 PNG / JPG / JPEG / BMP）")
        card_layout.addWidget(self.flow_image_label)
        layout.addWidget(card)

        # ---- 结果区域 ----
        result_frame = QFrame()
        result_frame.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #e0e4e8; border-radius: 10px; }")
        result_layout = QHBoxLayout(result_frame)
        result_layout.setContentsMargins(20, 12, 20, 12)
        result_layout.setSpacing(24)

        self.result_text_label = QLabel("流量类别：未识别")
        self.result_text_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #666; background: transparent;")
        result_layout.addWidget(self.result_text_label)

        # 置信度进度条
        conf_container = QWidget()
        conf_container.setStyleSheet("background: transparent;")
        conf_layout = QHBoxLayout(conf_container)
        conf_layout.setContentsMargins(0, 0, 0, 0)
        conf_label = QLabel("置信度：")
        conf_label.setStyleSheet("font-size: 13px; color: #888; background: transparent;")
        conf_layout.addWidget(conf_label)
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setMinimum(0)
        self.confidence_bar.setMaximum(100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setFixedWidth(200)
        self.confidence_bar.setFixedHeight(22)
        self.confidence_bar.setFormat("%.1f%%" % 0.0)
        conf_layout.addWidget(self.confidence_bar)
        result_layout.addWidget(conf_container)
        result_layout.addStretch()

        layout.addWidget(result_frame)

        # ---- 按钮 ----
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.upload_image_button = QPushButton("上传图像并识别")
        self.upload_image_button.setMinimumSize(200, 44)
        self.upload_image_button.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.upload_image_button.setStyleSheet("""
            QPushButton {
                background-color: #1890ff; border: none; border-radius: 8px;
                color: #fff; font-size: 15px; font-weight: bold; padding: 10px 32px;
            }
            QPushButton:hover { background-color: #40a9ff; }
            QPushButton:pressed { background-color: #096dd9; }
        """)
        self.upload_image_button.clicked.connect(self.upload_and_recognize_image)
        btn_row.addWidget(self.upload_image_button)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()
        self.tabWidget.addTab(self.image_tab, "图像识别")

    def loadcsv(self):
        self.statusbar.showMessage("正在加载数据...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.sums = self.lineEdit_2.text()
            self.load_csv("data/cicddos2017/MachineLearningCSV/MachineLearningCVE/test_final.csv", int(self.sums))
            self.label_6.setText("数据加载完成")
            self.label_6.setStyleSheet("color: #52c41a; font: 8pt '微软雅黑';")
            self.statusbar.showMessage(f"已加载 {self.sums} 条数据")
        finally:
            QApplication.restoreOverrideCursor()

    def load_csv(self, file_path, num_rows):
        # 使用 pandas 读取 CSV 文件的前 num_rows 行
        df1 = pd.read_csv(file_path)
        # 获取文件总行数
        total_rows = len(df1)

        # 计算采样比例
        frac = num_rows / total_rows
        sampled_df = df1.sample(frac=frac, random_state=42)

        # 保存采样后的数据
        sampled_df.to_csv('data/test.csv', index=False)

        # 读取采样后的数据用于表格显示
        df = pd.read_csv("data/test.csv", nrows=num_rows)

        # 设置 QTableWidget
        self.tableWidget.setRowCount(df.shape[0])
        self.tableWidget.setColumnCount(df.shape[1] - 1)  # 不显示最后一列

        headers = list(df.columns[:-1])
        self.tableWidget.setHorizontalHeaderLabels(headers)

        for i in range(df.shape[0]):
            for j in range(df.shape[1] - 1):
                cell_data = str(df.iloc[i, j])
                item = QTableWidgetItem(cell_data)
                self.tableWidget.setItem(i, j, item)

    def upload_and_recognize_image(self):
        self.statusbar.showMessage("正在识别图像...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not file_path:
            QApplication.restoreOverrideCursor()
            self.statusbar.showMessage("就绪")
            return

        # 显示原始图像
        pixmap = QtGui.QPixmap(file_path).scaled(
            self.flow_image_label.width(), self.flow_image_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.flow_image_label.setPixmap(pixmap)

        try:
            tmp_df = pd.read_csv("data/cicddos2017/MachineLearningCSV/MachineLearningCVE/test_final.csv", nrows=1)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.information(self, "错误", f"无法读取特征维度：{e}")
            self.statusbar.showMessage("就绪")
            return

        input_size = tmp_df.shape[1] - 1

        img = plt.imread(file_path)
        if img.ndim == 3:
            img = img[..., :3].mean(axis=2)
        img = img.astype(np.float32)
        if img.max() > 1.0:
            img = img / 255.0

        vec = img.flatten()
        if vec.shape[0] < input_size:
            pad = input_size - vec.shape[0]
            vec = np.pad(vec, (0, pad), mode="constant")
        else:
            vec = vec[:input_size]

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = CNNModel().to(device)
        try:
            model.load_state_dict(torch.load('save_weights/cnn_best_model.pth', map_location='cpu'))
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.information(self, "错误", f"无法加载模型权重：{e}")
            self.statusbar.showMessage("就绪")
            return

        model.eval()
        with torch.no_grad():
            single_input = torch.tensor(vec, dtype=torch.float32).unsqueeze(0).to(device)
            single_output = model(single_input.unsqueeze(1))
            single_prob = torch.softmax(single_output, dim=1)[0].cpu().numpy()
            single_idx = int(single_prob.argmax())
            single_conf = float(single_prob[single_idx])

        label_list = ["BENIGN", "DoS Hulk","PortScan","DDoS","DoS GoldenEye","FTP-Patator",
                      "SSH-Patator","DoS slowloris","DoS Slowhttptest","Bot","Web Attack"]

        if single_idx < 0 or single_idx >= len(label_list):
            QApplication.restoreOverrideCursor()
            QMessageBox.information(self, "错误", "模型输出类别索引超出范围")
            self.statusbar.showMessage("就绪")
            return

        pred_label = label_list[single_idx]
        is_benign = (pred_label == "BENIGN")

        # 更新结果
        self.result_text_label.setText(f"流量类别：{'良性流量' if is_benign else '恶意流量'}（{pred_label}）")
        self.result_text_label.setStyleSheet(
            f"font-size: 16pt; font-weight: bold; color: {'#52c41a' if is_benign else '#ff4d4f'}; background: transparent;"
        )

        conf_pct = single_conf * 100
        self.confidence_bar.setValue(int(conf_pct))
        self.confidence_bar.setFormat("%.1f%%" % conf_pct)
        self.confidence_bar.setStyleSheet(
            "QProgressBar { border: none; border-radius: 6px; background-color: #f0f0f0; text-align: center; "
            "color: #333; font-size: 12px; height: 18px; }" +
            ("QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #52c41a,stop:1 #73d13d); border-radius: 6px; }"
             if is_benign else
             "QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff4d4f,stop:1 #ff7875); border-radius: 6px; }")
        )

        QApplication.restoreOverrideCursor()
        self.statusbar.showMessage(f"识别完成 — {pred_label}（置信度 {conf_pct:.1f}%）")

    def detect(self):
        self.statusbar.showMessage("正在进行流量检测...")
        self.label_6.setText("程序运行中")
        self.label_6.setStyleSheet("color: #ff4d4f; font: 8pt '微软雅黑';")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

        try:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            tests = pd.read_csv('data/test.csv', sep=',')
            data_test = tests.iloc[:, 0:(tests.shape[1] - 1)]
            label_test = tests.iloc[:, -1]
            from sklearn.preprocessing import LabelEncoder, MinMaxScaler

            data_test = MinMaxScaler().fit_transform(data_test)
            normalized_data = data_test.copy()

            label_test = torch.tensor(label_test.values, dtype=torch.long)
            batch_size = 256

            test_dataset = TensorDataset(torch.tensor(data_test, dtype=torch.float32), label_test)
            test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

            model = CNNModel().to(device)
            model.load_state_dict(torch.load('save_weights/cnn_best_model.pth', map_location='cpu'))
            all_y_pred_classes = []
            all_label_test = []
            model.eval()
            with torch.no_grad():
                for i, (inputs, labels) in enumerate(test_loader):
                    inputs, labels = inputs.to(device), labels.to(device)
                    y_pred = model(inputs.unsqueeze(1))
                    _, y_pred_classes = torch.max(y_pred, 1)
                    all_y_pred_classes.extend(y_pred_classes.cpu().numpy())
                    all_label_test.extend(labels.cpu().numpy())

            # 填充识别结果表格
            arr_df = pd.DataFrame(all_y_pred_classes, columns=['label'])
            df = pd.read_csv("data/test.csv")
            headers = list(df.columns[:-1])
            data_test = pd.DataFrame(data_test, columns=headers)
            result = pd.concat([data_test, arr_df], axis=1)

            self.tableWidget_2.setRowCount(result.shape[0])
            self.tableWidget_2.setColumnCount(result.shape[1])
            self.tableWidget_2.setHorizontalHeaderLabels(list(result.columns))

            for i in range(result.shape[0]):
                for j in range(result.shape[1]):
                    self.tableWidget_2.setItem(i, j, QTableWidgetItem(str(result.iloc[i, j])))

            # 统计各类别数量
            label_list = ["BENIGN", "DoS Hulk","PortScan","DDoS","DoS GoldenEye","FTP-Patator",
                          "SSH-Patator","DoS slowloris","DoS Slowhttptest","Bot","Web Attack"]
            value_list = [all_y_pred_classes.count(float(i)) for i in range(len(label_list))]

            # 更新图像识别页面
            if normalized_data.shape[0] > 0:
                first_feature_row = normalized_data[0]
                img_path = feature_row_to_image(first_feature_row, save_path="flow_sample.png", img_size=32)

                pixmap = QtGui.QPixmap(img_path).scaled(
                    self.flow_image_label.width(), self.flow_image_label.height(),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.flow_image_label.setPixmap(pixmap)

                with torch.no_grad():
                    single_input = torch.tensor(first_feature_row, dtype=torch.float32).unsqueeze(0).to(device)
                    single_output = model(single_input.unsqueeze(1))
                    single_prob = torch.softmax(single_output, dim=1)[0].cpu().numpy()
                    single_idx = int(single_prob.argmax())
                    single_conf = float(single_prob[single_idx])

                pred_label = label_list[single_idx]
                is_benign = (pred_label == "BENIGN")
                self.result_text_label.setText(f"流量类别：{'良性流量' if is_benign else '恶意流量'}（{pred_label}）")
                self.result_text_label.setStyleSheet(
                    f"font-size: 16pt; font-weight: bold; color: {'#52c41a' if is_benign else '#ff4d4f'}; background: transparent;"
                )
                conf_pct = single_conf * 100
                self.confidence_bar.setValue(int(conf_pct))
                self.confidence_bar.setFormat("%.1f%%" % conf_pct)
                self.confidence_bar.setStyleSheet(
                    "QProgressBar { border: none; border-radius: 6px; background-color: #f0f0f0; "
                    "text-align: center; color: #333; font-size: 12px; height: 18px; }" +
                    ("QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #52c41a,stop:1 #73d13d); border-radius: 6px; }"
                     if is_benign else
                     "QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff4d4f,stop:1 #ff7875); border-radius: 6px; }")
                )

            # 绘制到嵌入式画布
            value_sum = np.sum(value_list)
            value_prop = [v / value_sum for v in value_list] if value_sum > 0 else value_list
            value_count = len(value_list)

            # 柱状图
            self.bar_figure.clear()
            ax1 = self.bar_figure.add_subplot(111)
            bars = ax1.bar(range(value_count), value_list, color='#1890ff', edgecolor='white')
            ax1.set_xticks(range(value_count))
            ax1.set_xticklabels(label_list, rotation=45, ha='right', fontsize=9)
            ax1.set_ylabel('数量', fontsize=11)
            ax1.set_title('流量类别分布', fontsize=13, fontweight='bold')
            for i, v in enumerate(value_list):
                ax1.text(i, v + max(value_list) * 0.02, str(v), ha='center', fontsize=9, fontweight='bold')
            self.bar_figure.tight_layout()
            self.bar_canvas.draw()

            # 饼图
            self.pie_figure.clear()
            ax2 = self.pie_figure.add_subplot(111)
            colors = plt.cm.Set3(np.linspace(0, 1, value_count))
            wedges, texts, autotexts = ax2.pie(value_prop, labels=label_list, autopct='%1.1f%%',
                                                startangle=90, colors=colors)
            for t in autotexts:
                t.set_fontsize(7)
            for t in texts:
                t.set_fontsize(8)
            ax2.set_title('流量类别占比', fontsize=13, fontweight='bold')
            self.pie_figure.tight_layout()
            self.pie_canvas.draw()

            self.label_6.setText("识别完成")
            self.label_6.setStyleSheet("color: #52c41a; font: 8pt '微软雅黑';")
            self.statusbar.showMessage(f"检测完成 — 共 {len(all_y_pred_classes)} 条记录")
        finally:
            QApplication.restoreOverrideCursor()

    def view(self):
        self.tabWidget.setCurrentWidget(self.tab_3)
        # 如果已有图表数据则刷新画布
        if hasattr(self, 'bar_canvas'):
            self.bar_canvas.draw()
        if hasattr(self, 'pie_canvas'):
            self.pie_canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    try:
        with open('style.qss', 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except:
        pass

    login_window = Login_class()
    login_window.show()

    sys.exit(app.exec_())