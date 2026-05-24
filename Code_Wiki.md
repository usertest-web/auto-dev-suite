# Code Wiki - 基于深度学习的CIC-DDoS2017流量检测系统

## 目录
1. [项目概述](#项目概述)
2. [项目架构](#项目架构)
3. [主要模块职责](#主要模块职责)
4. [关键类与函数说明](#关键类与函数说明)
5. [依赖关系](#依赖关系)
6. [项目运行方式](#项目运行方式)
7. [数据流分析](#数据流分析)
8. [扩展指南](#扩展指南)

---

## 项目概述

### 项目简介
本项目是一个完整的网络流量恶意行为检测系统，基于CIC-DDoS2017数据集，使用CNN、CNN-LSTM、CNN-BiLSTM三种深度学习模型，实现11类网络流量的精准分类。

### 核心功能
- ✅ 多模型支持（CNN / CNN-LSTM / CNN-BiLSTM）
- ✅ 完整的11分类检测（正常流量 + 10种攻击类型）
- ✅ PyQt5桌面应用（支持用户登录、可视化分析）
- ✅ Flask网页应用（支持文件上传、批量检测）
- ✅ 分批推理解决显存不足问题
- ✅ 训练过程可视化（损失/准确率曲线）

### 数据集类别
| 编号 | 类别 | 说明 |
|------|------|------|
| 0 | BENIGN | 正常流量 |
| 1 | DoS Hulk | Hulk拒绝服务攻击 |
| 2 | PortScan | 端口扫描 |
| 3 | DDoS | 分布式拒绝服务 |
| 4 | DoS GoldenEye | GoldenEye拒绝服务 |
| 5 | FTP-Patator | FTP暴力破解 |
| 6 | SSH-Patator | SSH暴力破解 |
| 7 | DoS slowloris | Slowloris攻击 |
| 8 | DoS Slowhttptest | Slowhttptest攻击 |
| 9 | Bot | 僵尸网络 |
| 10 | Web Attack | Web攻击 |

---

## 项目架构

### 目录结构
```
cicddos流量分类带界面/
├── data/                          # 数据集目录
│   ├── cicddos2017/
│   │   └── MachineLearningCSV/
│   │       └── MachineLearningCVE/
│   │           ├── train_final.csv     # 训练集（预处理完成）
│   │           └── test_final.csv      # 测试集（预处理完成）
│   └── test.csv                       # 临时测试文件
├── save_weights/                  # 模型权重目录
│   ├── cnn_best_model.pth
│   ├── cnn_lstm_best_model.pth
│   └── cnn_bilstm_best_model.pth
├── pic/                           # 训练曲线与图片资源
│   ├── cnn_accuracy_curve.png
│   ├── cnn_loss_curve.png
│   └── ...
├── templates/                     # Web前端模板
│   └── index.html
├── ui/                            # PyQt5界面文件
│   ├── login_ts.py
│   ├── login_ts.ui
│   ├── register.py
│   └── register.ui
├── model.py                       # 模型定义文件
├── train.py                       # 模型训练脚本
├── web_app.py                     # Flask Web应用
├── window.py                      # PyQt5桌面应用主程序
├── main.py                        # PyQt5界面定义
├── userinfo.csv                   # 用户账号信息
└── style.qss                      # PyQt5样式表
```

### 架构图
```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                               │
├───────────────────────────────┬─────────────────────────────────┤
│   桌面端 (PyQt5)              │   Web端 (Flask + HTML)         │
│   - window.py                 │   - web_app.py                  │
│   - main.py                   │   - templates/index.html        │
│   - ui/                       │                                 │
└───────────────────────────────┴─────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         业务逻辑层                               │
├───────────────────────────────┬─────────────────────────────────┤
│   训练模块                    │   推理模块                       │
│   - train.py                  │   - window.py (桌面推理)         │
│                               │   - web_app.py (Web推理)         │
└───────────────────────────────┴─────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         模型层                                   │
├─────────────────────────────────────────────────────────────────┤
│   CNNModel / CNNLSTMModel / CNNBILSTMModel (model.py)           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         数据层                                   │
├─────────────────────────────────────────────────────────────────┤
│   data/cicddos2017/MachineLearningCSV/...                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 主要模块职责

### 1. 模型模块 - [model.py](file:///d:/cicddos流量分类带界面/model.py)
**职责**：定义三种深度学习模型的网络结构
- CNNModel：纯卷积神经网络
- CNNLSTMModel：CNN特征提取 + LSTM时序建模
- CNNBILSTMModel：CNN + 双向LSTM

### 2. 训练模块 - [train.py](file:///d:/cicddos流量分类带界面/train.py)
**职责**：模型训练与评估
- 加载训练集和测试集
- 数据归一化处理
- 模型训练与验证
- 保存最佳模型权重
- 绘制训练/验证损失曲线和准确率曲线

### 3. 桌面应用模块 - [window.py](file:///d:/cicddos流量分类带界面/window.py)
**职责**：提供图形化用户界面
- 用户登录/注册功能
- 数据加载与表格展示
- 模型推理与结果展示
- 可视化分析（柱状图、饼图）
- 图像识别功能

### 4. Web应用模块 - [web_app.py](file:///d:/cicddos流量分类带界面/web_app.py)
**职责**：提供Web服务接口
- Flask服务启动
- 文件上传处理
- 模型推理（分批推理）
- 数据集统计信息API
- 训练曲线API
- 模型信息API

### 5. 界面定义模块 - [main.py](file:///d:/cicddos流量分类带界面/main.py)
**职责**：PyQt5主界面UI定义
- 流量提取标签页
- 流量鉴别标签页
- 可视化标签页

---

## 关键类与函数说明

### 模型模块 ([model.py](file:///d:/cicddos流量分类带界面/model.py))

#### CNNModel 类
```python
class CNNModel(nn.Module):
    """纯卷积神经网络模型"""
    # 输入维度: (batch_size, 1, 78)
    # 输出维度: (batch_size, 11)
    def __init__(self):
        # Conv1d(1, 32, 3) -> Conv1d(32, 64, 3) -> Flatten -> Linear(4736, 128) -> Linear(128, 11)
```

#### CNNLSTMModel 类
```python
class CNNLSTMModel(nn.Module):
    """CNN + LSTM模型"""
    # CNN提取特征后，送入LSTM进行时序建模
    def __init__(self):
        # CNN层 -> LSTM(4736, 256) -> Linear(256, 128) -> Linear(128, 11)
```

#### CNNBILSTMModel 类
```python
class CNNBILSTMModel(nn.Module):
    """CNN + 双向LSTM模型"""
    # 使用双向LSTM捕获前后文依赖
    def __init__(self):
        # CNN层 -> BiLSTM(4736, 256) -> Linear(512, 128) -> Linear(128, 11)
```

---

### 训练模块 ([train.py](file:///d:/cicddos流量分类带界面/train.py))

#### save_best_model 函数
```python
def save_best_model(model, best_val_accuracy, current_val_accuracy, save_path):
    """
    保存验证集准确率最高的模型
    参数:
        model: 当前模型
        best_val_accuracy: 历史最佳验证准确率
        current_val_accuracy: 当前验证准确率
        save_path: 保存路径
    返回:
        更新后的最佳验证准确率
    """
```

#### 主训练流程
```python
if __name__ == '__main__':
    # 1. 加载数据
    # 2. 归一化处理 (MinMaxScaler)
    # 3. 构建模型并移动到GPU/CPU
    # 4. 定义损失函数 (CrossEntropyLoss) 和优化器 (Adam)
    # 5. 训练循环 (epochs=20)
    # 6. 保存最佳模型和训练曲线
```

---

### 桌面应用模块 ([window.py](file:///d:/cicddos流量分类带界面/window.py))

#### Login_class 类
```python
class Login_class(QMainWindow, Ui_Login_MainWindow):
    """登录界面类"""
    # 功能:
    #   - 用户账号密码验证
    #   - 跳转到主界面
    #   - 跳转到注册界面
```

#### Regist_class 类
```python
class Regist_class(QMainWindow, Ui_Register_MainWindow):
    """注册界面类"""
    # 功能:
    #   - 新用户注册
    #   - 检查用户名是否已存在
    #   - 保存用户信息到userinfo.csv
```

#### Main_class 类
```python
class Main_class(QMainWindow, Ui_MainWindow):
    """主界面类"""
    
    def loadcsv(self):
        """加载CSV数据"""
        # 从test_final.csv中按指定数量随机采样
        # 保存到data/test.csv
        # 在表格中展示
    
    def detect(self):
        """流量检测"""
        # 加载模型权重
        # 分批推理
        # 展示检测结果
        # 生成可视化图表
    
    def view(self):
        """查看可视化"""
        # 切换到可视化标签页
        # 刷新图表展示
    
    def upload_and_recognize_image(self):
        """上传并识别图像"""
        # 选择图像文件
        # 显示图像
        # 模型推理
        # 显示识别结果和置信度
    
    def _setup_embedded_charts(self):
        """设置嵌入式图表"""
        # 使用matplotlib嵌入PyQt5界面
        # 替换静态标签为交互式图表
    
    def _setup_image_recognition_tab(self):
        """设置图像识别标签页"""
        # 动态添加图像识别标签页
```

#### feature_row_to_image 函数
```python
def feature_row_to_image(feature_row, save_path="flow_sample.png", img_size=32):
    """
    将一条流量特征向量转换为灰度图
    参数:
        feature_row: 特征向量
        save_path: 保存路径
        img_size: 图像尺寸
    返回:
        保存的图像路径
    """
```

---

### Web应用模块 ([web_app.py](file:///d:/cicddos流量分类带界面/web_app.py))

#### load_models 函数
```python
def load_models():
    """
    加载三个预训练模型到内存
    模型: CNN, CNN-LSTM, CNN-BiLSTM
    """
```

#### preprocess_data 函数
```python
def preprocess_data(df):
    """
    数据预处理（与训练时一致）
    参数:
        df: 包含标签的DataFrame
    返回:
        tensor_data: 归一化后的特征张量
        labels: 标签数组
    """
```

#### /predict 路由
```python
@app.route('/predict', methods=['POST'])
def predict():
    """
    预测接口
    请求:
        file: CSV/TXT文件
        model: 模型名称 (cnn/cnn_lstm/cnn_bilstm)
    返回:
        JSON格式的预测结果
    """
    # 1. 接收并解析文件
    # 2. 数据预处理
    # 3. 分批推理 (batch_size=256)
    # 4. 返回结果
```

#### /api/stats 路由
```python
@app.route('/api/stats', methods=['GET'])
def stats():
    """返回数据集统计信息"""
```

#### /api/model_info 路由
```python
@app.route('/api/model_info', methods=['GET'])
def model_info():
    """返回三个模型的结构信息"""
```

---

## 依赖关系

### 主要依赖库
| 库名 | 版本要求 | 用途 |
|------|----------|------|
| Python | 3.7+ | 编程语言基础 |
| PyTorch | 1.7+ | 深度学习框架 |
| PyQt5 | 5.15+ | 桌面GUI框架 |
| Flask | 2.0+ | Web框架 |
| pandas | 1.0+ | 数据处理与CSV读写 |
| NumPy | 1.19+ | 数值计算 |
| scikit-learn | 0.24+ | 数据预处理与评估 |
| matplotlib | 3.3+ | 可视化绘图 |
| seaborn | 0.11+ | 高级可视化 |
| flask-cors | 3.0+ | 跨域资源共享 |

### 安装依赖
```bash
# PyTorch (GPU版本)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 其他依赖
pip install flask flask-cors pandas numpy scikit-learn matplotlib seaborn pyqt5
```

---

## 项目运行方式

### 桌面端运行
```bash
# 在项目根目录下执行
python window.py
```

#### 桌面端操作流程
1. 用户登录/注册
2. 流量提取 - 从测试集截取数据
3. 流量鉴别 - 使用CNN模型检测
4. 可视化分析 - 查看柱状图和饼图
5. 图像识别 - 上传特征图像进行识别

### Web端运行
```bash
# 在项目根目录下执行
python web_app.py
```

服务启动后访问：`http://localhost:5000`

#### Web端操作流程
1. 访问系统首页
2. 上传CSV/TXT格式的流量数据文件
3. 选择模型 (CNN/CNN-LSTM/CNN-BiLSTM)
4. 点击开始检测
5. 查看检测结果
6. 可导出CSV结果文件

### 模型训练
```bash
# 在train.py中选择要训练的模型
# 取消对应的注释:
# model = CNNModel().to(device)
# model = CNNLSTMModel().to(device)
model = CNNBILSTMModel().to(device)

# 运行训练脚本
python train.py
```

---

## 数据流分析

### 训练数据流
```
原始CSV数据集
    ↓
pandas读取
    ↓
特征/标签分离
    ↓
MinMaxScaler归一化
    ↓
TensorDataset封装
    ↓
DataLoader分批
    ↓
模型训练 (前向传播 + 反向传播)
    ↓
验证集评估
    ↓
保存最佳模型权重 (.pth)
    ↓
绘制训练曲线 (Loss/Accuracy)
```

### 推理数据流
```
用户输入数据 (CSV/采样)
    ↓
pandas读取
    ↓
MinMaxScaler归一化
    ↓
转换为PyTorch Tensor
    ↓
添加通道维度 (unsqueeze)
    ↓
分批推理 (batch_size=256)
    ↓
softmax获取概率
    ↓
argmax获取预测类别
    ↓
展示结果 (表格/图表)
```

---

## 扩展指南

### 添加新模型
1. 在 [model.py](file:///d:/cicddos流量分类带界面/model.py) 中定义新模型类
2. 在 [train.py](file:///d:/cicddos流量分类带界面/train.py) 中添加训练代码
3. 在 [window.py](file:///d:/cicddos流量分类带界面/window.py) 和 [web_app.py](file:///d:/cicddos流量分类带界面/web_app.py) 中添加推理支持
4. 训练并保存模型权重

### 新增数据集类别
1. 更新标签映射 `LABEL_LIST`
2. 重新训练模型
3. 更新界面中的类别展示

### 优化性能
- 调整 `batch_size` 以平衡速度和显存
- 使用混合精度训练 (`torch.cuda.amp`)
- 实现数据缓存机制
- 使用更快的推理引擎 (如TensorRT)

### 界面自定义
- 桌面端: 修改 [style.qss](file:///d:/cicddos流量分类带界面/style.qss) 样式表
- Web端: 修改 [templates/index.html](file:///d:/cicddos流量分类带界面/templates/index.html)

---

## 常见问题

### 显存不足
**解决方案**: 使用分批推理，代码中已实现 `batch_size=256`，可进一步减小该值。

### 找不到数据集文件
**解决方案**: 确保数据集位于 `data/cicddos2017/MachineLearningCSV/MachineLearningCVE/` 目录下。

### PyQt5中文乱码
**解决方案**: 确保 `.py` 文件使用UTF-8编码保存，并在文件头部添加 `# -*- coding: utf-8 -*-`。

### 模型预测准确率低
**解决方案**: 
1. 检查数据预处理是否与训练时一致
2. 确保使用了正确的模型权重文件
3. 检查特征维度是否为78

---

*Code Wiki v1.0*
