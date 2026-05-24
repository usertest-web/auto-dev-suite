import torch.nn as nn
import torch.nn.functional as F
class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(4736, 128)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, 11)


    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.flatten(x)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)

        return x



class CNNLSTMModel(nn.Module):
    def __init__(self):
        super(CNNLSTMModel, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3)
        self.flatten = nn.Flatten()
        self.dropout = nn.Dropout(0.5)

        self.lstm = nn.LSTM(input_size=4736, hidden_size=256, num_layers=1, batch_first=True)

        self.fc1 = nn.Linear(256, 128)

        self.fc2 = nn.Linear(128, 11)

    def forward(self, x):

        x = self.conv1(x)
        x = F.relu(x)
        x = self.dropout(x)

        x = self.conv2(x)
        x = F.relu(x)
        x = self.dropout(x)

        x = x.view(x.size(0), 1, -1)
        x, _ = self.lstm(x)
        x = self.dropout(x)
        x = self.flatten(x[:, -1, :])
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)

        return x

class CNNBILSTMModel(nn.Module):
    def __init__(self):
        super(CNNBILSTMModel, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3)
        self.flatten = nn.Flatten()
        self.dropout = nn.Dropout(0.5)

        self.bilstm = nn.LSTM(input_size=4736, hidden_size=256, num_layers=1, batch_first=True, bidirectional=True)

        self.fc1 = nn.Linear(512, 128)

        self.fc2 = nn.Linear(128, 11)

    def forward(self, x):

        x = self.conv1(x)
        x = F.relu(x)
        x = self.dropout(x)

        x = self.conv2(x)
        x = F.relu(x)
        x = self.dropout(x)

        x = x.view(x.size(0), 1, -1)
        x, _ = self.bilstm(x)
        x = self.dropout(x)
        x = self.flatten(x[:, -1, :])
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)

        return x


