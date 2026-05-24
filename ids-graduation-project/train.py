from model import *


import numpy as np
np.random.seed(1337)  # for reproducibility

import pandas as pd

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import numpy as np



def save_model(model, filepath):
    torch.save(model.state_dict(), filepath)

# Function to save the best model state dictionary
def save_best_model(model, best_val_accuracy, current_val_accuracy, save_path):
    if current_val_accuracy > best_val_accuracy:
        torch.save(model.state_dict(), save_path)
        print("Best model saved.")
        return current_val_accuracy
    else:
        return best_val_accuracy



if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 读取训练数据
    data_train_set = pd.read_csv(r'data/cicddos2017/MachineLearningCSV/MachineLearningCVE/train_final.csv', sep=',')
    data_test_set = pd.read_csv(r'data/cicddos2017/MachineLearningCSV/MachineLearningCVE/test_final.csv', sep=',')
    data_train = data_train_set.iloc[:, 0:(data_train_set.shape[1] - 1)]
    # 获取最后一个维度标签
    label_train = data_train_set.iloc[:, -1]
    data_test = data_test_set.iloc[:, 0:(data_test_set.shape[1] - 1)]
    # 获取最后一个维度标签
    label_test = data_test_set.iloc[:, -1]

    from sklearn.preprocessing import LabelEncoder, MinMaxScaler

    data_train = MinMaxScaler().fit_transform(data_train)
    data_test = MinMaxScaler().fit_transform(data_test)




    # # 打印过采样前后的类别分布
    print("训练集的类别分布：")
    print(label_train.value_counts())
    print("测试集的类别分布：")
    print(label_test.value_counts())
    # 将标签转换为NumPy数组，再转换为PyTorch Tensor
    label_train = torch.tensor(label_train.values, dtype=torch.long )
    label_test = torch.tensor(label_test.values, dtype=torch.long)





    #输入数据维度为数据总维度减1
    input_size = (data_train.shape[1], 1)[0]
    print(input_size)
    #模型构建

    # model = CNNModel().to(device)
    # model = CNNLSTMModel().to(device)
    model = CNNBILSTMModel().to(device)




    # 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0002, betas=(0.9, 0.995), eps=1e-6)

    # 将数据和标签转换为DataLoader以进行批处理
    batch_size = 256  # 可根据内存大小调整


    # Now, create the train_dataset
    train_dataset = TensorDataset(torch.tensor(data_train, dtype=torch.float32), label_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_dataset = TensorDataset(torch.tensor(data_test, dtype=torch.float32), label_test)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)
    # 训练循环
    epochs = 20
    train_losses = []
    val_losses = []
    train_accuracies = []  # 用于存储训练集准确率
    val_accuracies = []  # 用于存储验证集准确率
    best_val_accuracy = 0.0
    for epoch in range(epochs):
        model.train()
        train_running_loss = 0.0
        correct_train = 0  # 用于计算训练集正确预测的数量
        total_train = 0  # 用于计算训练集总样本数
        test_running_loss = 0
        correct_test = 0
        total_test = 0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            # print(inputs.size())
            # print(inputs.unsqueeze(1).size())
            outputs = model(inputs.unsqueeze(1))
            loss = criterion(outputs.squeeze(), labels)
            loss.backward()
            optimizer.step()
            train_running_loss += loss.item() * inputs.size(0)
            _, predicted_labels = torch.max(outputs, 1)

            # 计算训练集准确率
            correct_train += (predicted_labels == labels).sum().item()

            total_train += labels.size(0)

        train_accuracy = correct_train / total_train
        train_loss = train_running_loss / len(data_train)
        train_losses.append(train_loss)
        train_accuracies.append(train_accuracy)

        # 在验证集上进行评估
        model.eval()
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs.unsqueeze(1))
                loss = criterion(outputs.squeeze(), labels)

                test_running_loss += loss.item() * inputs.size(0)

                # 计算训练集准确率
                _, predicted_labels = torch.max(outputs, 1)
                correct_test += (predicted_labels == labels).sum().item()
                total_test += labels.size(0)
            val_accuracy = correct_test / total_test
            val_loss = test_running_loss / len(data_test)

            val_losses.append(val_loss)

            # 计算验证集准确率

            val_accuracies.append(val_accuracy)
            best_val_accuracy = save_best_model(model, best_val_accuracy, val_accuracy, 'save_weights/cnn_bilstm_best_model.pth')
            # # 保存当前模型
            # save_model(model, f'save_weights/cnn_bigru_model_epoch_{epoch + 1}.pth')

        print(
            f"Epoch {epoch + 1}/{epochs}, Train Loss: {train_loss:.4f}, Train Accuracy: {train_accuracy:.4f}, Val Loss: {val_loss:.4f}, Val Accuracy: {val_accuracy:.4f}")



    # 绘制训练和验证损失曲线
    plt.figure(figsize=(8, 6))
    epochs = range(1, len(train_losses) + 1)
    plt.plot(epochs, train_losses, 'b', label='Train Loss')
    plt.plot(epochs, val_losses, 'r', label='Validation Loss')
    plt.title('Training and Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.savefig('pic/cnn_bilstm_loss_curve.png')
    plt.close()


    plt.figure(figsize=(8, 6))
    epochs = range(1, len(train_accuracies) + 1)
    plt.plot(epochs, train_accuracies, 'b', label='Train Accuracy')
    plt.plot(epochs, val_accuracies, 'r', label='Validation Accuracy')
    plt.title('Training and Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.savefig('pic/cnn_bilstm_accuracy_curve.png')
    plt.close()





