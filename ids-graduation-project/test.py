from model import *

import numpy as np
np.random.seed(1337)  # for reproducibility

import pandas as pd
import seaborn as sns
import torch
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix,roc_curve
import matplotlib.pyplot as plt




if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data_test_set = pd.read_csv('data/cicddos2017/MachineLearningCSV/MachineLearningCVE/test_final.csv', sep=',')
    # data_test_set = pd.read_csv('data/test.csv', sep=',')
    data_test = data_test_set.iloc[:, 0:(data_test_set.shape[1] - 1)]
    # 获取最后一个维度标签
    label_test = data_test_set.iloc[:, -1]
    from sklearn.preprocessing import LabelEncoder, MinMaxScaler
    data_test = MinMaxScaler().fit_transform(data_test)
    print("测试集过采样前的类别分布：")
    print(label_test.value_counts())
    # 将标签转换为NumPy数组，再转换为PyTorch Tensor

    label_test = torch.tensor(label_test.values, dtype=torch.long)

    #输入数据维度为数据总维度减1
    input_size = (data_test.shape[1], 1)[0]
    print(input_size)
    #模型构建




    # ========== 选择模型 ==========
    print("\n请选择要测试的模型：")
    print("1 - CNN")
    print("2 - CNN-LSTM")  
    print("3 - CNN-BiLSTM")
    choice = input("输入数字 (1/2/3): ").strip()
    
    if choice == '1':
        print("正在加载 CNN 模型...")
        model = CNNModel().to(device)
        model.load_state_dict(torch.load('save_weights/cnn_best_model.pth', map_location='cpu'))
    elif choice == '2':
        print("正在加载 CNN-LSTM 模型...")
        model = CNNLSTMModel().to(device)
        model.load_state_dict(torch.load('save_weights/cnn_lstm_best_model.pth', map_location='cpu'))
    else:
        print("正在加载 CNN-BiLSTM 模型...")
        model = CNNBILSTMModel().to(device)
        model.load_state_dict(torch.load('save_weights/cnn_bilstm_best_model.pth', map_location='cpu'))
    # =============================
    
    # 【3】测试 CNN-BiLSTM：取消下面两行的注释
    model = CNNBILSTMModel().to(device)
    model.load_state_dict(torch.load('save_weights/cnn_bilstm_best_model.pth', map_location='cpu'))

    # Assuming 'data_test' is your numpy array
    data_test_tensor = torch.tensor(data_test, dtype=torch.float32)
    # 设置批处理大小
    batch_size = 128

    # 创建测试集 DataLoader
    test_dataset = TensorDataset(torch.tensor(data_test, dtype=torch.float32), label_test)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)
    # 初始化列表以存储预测和标签
    all_y_pred_classes = []
    all_label_test = []

    # 初始化正确预测数量和总样本数
    correct_test = 0
    total_test = 0
    model.eval()

    # 关闭梯度计算
    with torch.no_grad():
        # 以批处理的形式遍历测试集
        for i, (inputs, labels) in enumerate(test_loader):
            # 将数据移至 GPU 或 CPU
            inputs, labels = inputs.to(device), labels.to(device)

            # 进行模型预测
            y_pred = model(inputs.unsqueeze(1))
            _, y_pred_classes = torch.max(y_pred, 1)

            # 将预测结果和标签添加到列表中
            all_y_pred_classes.extend(y_pred_classes.cpu().numpy())
            all_label_test.extend(labels.cpu().numpy())
            correct_test += (y_pred_classes == labels).sum().item()
            total_test += labels.size(0)
        val_accuracy = correct_test / total_test

    print(val_accuracy)

    # print(all_y_pred_classes)
    y_pred_classes = torch.argmax(y_pred, dim=1).cpu().numpy()

    # Calculate evaluation metrics
    acc = accuracy_score(all_label_test, all_y_pred_classes)
    precision = precision_score(all_label_test, all_y_pred_classes, average='weighted')
    recall = recall_score(all_label_test, all_y_pred_classes, average='weighted')
    f1 = f1_score(all_label_test, all_y_pred_classes, average='weighted')

    confusion_mat = confusion_matrix(all_label_test, all_y_pred_classes)

    # Print evaluation results
    print("Accuracy:", acc)
    print("Precision:", precision)
    print("Recall:", recall)
    print("F1-score:", f1)


    # 定义标签
    labels = ["BENIGN", "DoS Hulk","PortScan","DDoS","DoS GoldenEye","FTP-Patator"
        ,"SSH-Patator","DoS slowloris","DoS Slowhttptest","Bot","Web Attack"
              ]


    # 绘制混淆矩阵
    plt.figure(figsize=(8, 6))
    sns.heatmap(confusion_mat, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
    plt.xlabel('Predicted Labels')
    plt.ylabel('True Labels')
    plt.title('Confusion Matrix')
    plt.show()
    