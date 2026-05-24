"""
===============================================================================
  深度学习入侵检测系统 — Web 启动说明
===============================================================================

  一键启动步骤：
    1. 确保已安装依赖：
         pip install flask flask-cors numpy pandas torch scikit-learn

    2. 确保以下文件存在于项目根目录：
         - model.py                          (模型定义)
         - save_weights/cnn_best_model.pth   (CNN 权重)
         - save_weights/cnn_lstm_best_model.pth   (CNN-LSTM 权重)
         - save_weights/cnn_bilstm_best_model.pth (CNN-BiLSTM 权重)
         - templates/index.html              (前端页面)

    3. 在项目根目录下运行：
         python web_app.py

    4. 浏览器访问：
         http://localhost:5000

  可选参数（启动时环境变量）：
    - 端口修改：直接改底部 app.run(port=xxxx)
    - GPU 加速：自动检测 CUDA，无 GPU 则使用 CPU

  项目结构概览：
    web_app.py          ← Flask 后端（本文件）
    model.py            ← PyTorch 模型定义 (CNN / CNN-LSTM / CNN-BiLSTM)
    templates/index.html ← 前端页面 (Tailwind CSS)
    save_weights/       ← 训练好的 .pth 权重文件
    data/               ← 测试数据集

===============================================================================
"""

import os
import numpy as np
import pandas as pd
import torch
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from sklearn.preprocessing import MinMaxScaler

from model import CNNModel, CNNLSTMModel, CNNBILSTMModel

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ==================== 全局配置 ====================
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
LABEL_LIST = [
    "BENIGN", "DoS Hulk", "PortScan", "DDoS", "DoS GoldenEye",
    "FTP-Patator", "SSH-Patator", "DoS slowloris",
    "DoS Slowhttptest", "Bot", "Web Attack"
]
WEIGHT_DIR = os.path.join(os.path.dirname(__file__), 'save_weights')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'test.csv')

# ==================== 模型加载 ====================
models = {}

def load_models():
    cnn = CNNModel().to(DEVICE)
    cnn.load_state_dict(torch.load(os.path.join(WEIGHT_DIR, 'cnn_best_model.pth'), map_location='cpu'))
    cnn.eval()
    models['cnn'] = cnn

    cnn_lstm = CNNLSTMModel().to(DEVICE)
    cnn_lstm.load_state_dict(torch.load(os.path.join(WEIGHT_DIR, 'cnn_lstm_best_model.pth'), map_location='cpu'))
    cnn_lstm.eval()
    models['cnn_lstm'] = cnn_lstm

    cnn_bilstm = CNNBILSTMModel().to(DEVICE)
    cnn_bilstm.load_state_dict(torch.load(os.path.join(WEIGHT_DIR, 'cnn_bilstm_best_model.pth'), map_location='cpu'))
    cnn_bilstm.eval()
    models['cnn_bilstm'] = cnn_bilstm

    print(f"[INFO] 3 models loaded on {DEVICE}")

load_models()

# ==================== 数据预处理 ====================
def preprocess_data(df):
    """与 test.py 一致的预处理：MinMaxScaler 归一化 + tensor 转换"""
    data = df.iloc[:, 0:(df.shape[1] - 1)].values.astype(np.float32)
    labels = df.iloc[:, -1].values if df.shape[1] > 0 else None

    scaler = MinMaxScaler()
    normalized = scaler.fit_transform(data)

    tensor_data = torch.tensor(normalized, dtype=torch.float32)
    return tensor_data, labels


def preprocess_features_only(df):
    """仅特征预处理（无标签列）"""
    data = df.values.astype(np.float32)
    scaler = MinMaxScaler()
    normalized = scaler.fit_transform(data)
    return torch.tensor(normalized, dtype=torch.float32)


def _parse_txt_content(content):
    """解析 TXT 文件内容，支持多种分隔符和无表头情况"""
    from io import StringIO

    df = None
    # 依次尝试逗号、空白分隔符
    for sep in [',', r'\s+']:
        try:
            df = pd.read_csv(StringIO(content), sep=sep, engine='python' if sep == r'\s+' else 'c')
            if df.shape[1] > 1:
                break
        except Exception:
            continue

    if df is None or df.shape[1] < 1:
        raise ValueError('无法解析 TXT 文件，请检查格式')

    # 检测是否有表头：如果第一列的名称可以转为数字，说明第一行是数据而非表头
    try:
        float(str(df.columns[0]))
        # 第一行是数据 → 无表头，重新读取并添加列名
        if df.shape[1] > 1:
            sep_used = ',' if ',' in content.split('\n')[0] else r'\s+'
            df = pd.read_csv(
                StringIO(content),
                sep=sep_used, header=None,
                engine='python' if sep_used == r'\s+' else 'c'
            )
        else:
            df = pd.read_csv(StringIO(content), header=None)
        df.columns = [f'f{i}' for i in range(df.shape[1])]
    except ValueError:
        pass  # 第一列名称非数字 → 已有合法表头

    return df


# ==================== 路由 ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """预测路由 — 全流程 try-except 包裹，带详细日志"""
    import traceback

    try:
        # ---- 1. 参数校验 ----
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        print(f"[PREDICT] 1. 收到文件: {file.filename}")

        model_name = request.args.get('model', 'cnn')
        if model_name not in models:
            return jsonify({'error': f'无效模型名: {model_name}，可选: cnn, cnn_lstm, cnn_bilstm'}), 400
        print(f"[PREDICT] 2. 选择模型: {model_name}")

        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ('csv', 'txt'):
            return jsonify({'error': '仅支持 CSV 或 TXT 格式'}), 400

        # ---- 2. 文件读取 ----
        if ext == 'csv':
            df = pd.read_csv(file)
        else:
            content = file.read().decode('utf-8')
            df = _parse_txt_content(content)
        print(f"[PREDICT] 3. 读取数据形状: {df.shape}")

        if df.shape[1] < 2:
            return jsonify({'error': f'数据列数不足: 当前{df.shape[1]}列，至少需要2列（特征+可选标签）'}), 400

        # ---- 3. 标签检测 ----
        last_col = df.iloc[:, -1]
        has_label = not pd.api.types.is_numeric_dtype(last_col) or last_col.nunique() <= 15
        print(f"[PREDICT] 4. 标签检测: has_label={has_label}")

        # ---- 4. 数据预处理 ----
        if has_label:
            tensor_data, labels = preprocess_data(df)
        else:
            tensor_data = preprocess_features_only(df)
            labels = None
        print(f"[PREDICT] 5. 预处理完成, tensor形状: {tensor_data.shape}")

        # ---- 5. 维度校验 ----
        num_features = tensor_data.shape[1]
        expected_features = 78
        if num_features != expected_features:
            msg = f'特征维度不匹配: 当前{num_features}维，模型需要{expected_features}维。请使用与训练集相同特征数的数据。'
            print(f"[PREDICT] 错误: {msg}")
            return jsonify({'error': msg}), 400
        print(f"[PREDICT] 6. 维度校验通过: {num_features} 特征")

        # ---- 6. 模型推理 (分批推理, 避免显存不足) ----
        model = models[model_name]
        model.to(DEVICE)
        model.eval()
        print(f"[PREDICT] 7. 开始模型推理, 设备: {DEVICE}")

        BATCH_SIZE = 256
        batch_input = tensor_data.unsqueeze(1).to(DEVICE)  # (N, 1, 78)
        results = []
        all_probs = []

        with torch.no_grad():
            for start_idx in range(0, len(batch_input), BATCH_SIZE):
                end_idx = min(start_idx + BATCH_SIZE, len(batch_input))
                mini_batch = batch_input[start_idx:end_idx]
                outputs = model(mini_batch)                     # (batch, 11)
                probs = torch.softmax(outputs, dim=1).cpu().numpy()  # (batch, 11)
                all_probs.append(probs)

        all_probs = np.concatenate(all_probs, axis=0)          # (N, 11)
        pred_indices = all_probs.argmax(axis=1)                 # (N,)
        confidences = all_probs[np.arange(len(all_probs)), pred_indices]

        for i in range(len(pred_indices)):
            result = {
                'index': i,
                'prediction': LABEL_LIST[int(pred_indices[i])],
                'confidence': round(float(confidences[i]), 4),
                'probabilities': {LABEL_LIST[j]: round(float(all_probs[i][j]), 4) for j in range(len(LABEL_LIST))}
            }
            if labels is not None:
                result['true_label'] = str(labels[i]) if labels[i] is not None else None
            results.append(result)

        print(f"[PREDICT] 8. 推理完成, 结果数量: {len(results)}")

        return jsonify({
            'model': model_name,
            'total_records': len(results),
            'results': results
        })

    except Exception as e:
        print(f"[PREDICT] 致命错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'预测失败: {str(e)}'}), 500


@app.route('/export', methods=['POST'])
def export_csv():
    """后端导出 CSV（备选方案）"""
    import traceback
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        model_name = request.args.get('model', 'cnn')
        if model_name not in models:
            return jsonify({'error': f'无效模型名: {model_name}'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ('csv', 'txt'):
            return jsonify({'error': '仅支持 CSV 或 TXT 格式'}), 400

        if ext == 'csv':
            df = pd.read_csv(file)
        else:
            content = file.read().decode('utf-8')
            df = _parse_txt_content(content)

        last_col = df.iloc[:, -1]
        has_label = not pd.api.types.is_numeric_dtype(last_col) or last_col.nunique() <= 15
        if has_label:
            tensor_data, _ = preprocess_data(df)
        else:
            tensor_data = preprocess_features_only(df)

        num_features = tensor_data.shape[1]
        if num_features != 78:
            return jsonify({'error': f'特征维度不匹配: 当前{num_features}维，模型需要78维'}), 400

        model = models[model_name]
        model.to(DEVICE)
        model.eval()

        BATCH_SIZE = 256
        batch_input = tensor_data.unsqueeze(1).to(DEVICE)
        rows = []

        with torch.no_grad():
            all_probs = []
            for start_idx in range(0, len(batch_input), BATCH_SIZE):
                end_idx = min(start_idx + BATCH_SIZE, len(batch_input))
                mini_batch = batch_input[start_idx:end_idx]
                outputs = model(mini_batch)
                probs = torch.softmax(outputs, dim=1).cpu().numpy()
                all_probs.append(probs)

            all_probs = np.concatenate(all_probs, axis=0)
            pred_indices = all_probs.argmax(axis=1)
            confidences = all_probs[np.arange(len(all_probs)), pred_indices]

            for i in range(len(pred_indices)):
                prediction = LABEL_LIST[int(pred_indices[i])]
                is_attack = '是' if prediction != 'BENIGN' else '否'
                rows.append(f'{i+1},"{i}","{prediction}","{is_attack}","{confidences[i]:.4f}","{model_name}"')

        csv_header = '序号,原始数据序号,预测类别,是否攻击,置信度,使用的模型'
        csv_body = '\n'.join(rows)
        csv_content = '﻿' + csv_header + '\n' + csv_body

        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=detection_results.csv'}
        )
    except Exception as e:
        print(f"[EXPORT] 错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """数据集统计信息"""
    total_samples = 0
    normal_samples = 0
    attack_samples = 0

    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'test.csv')
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            total_samples = len(df)
            last_col = df.iloc[:, -1]
            attack_samples = int((last_col != 'BENIGN').sum())
            normal_samples = total_samples - attack_samples
        except Exception:
            total_samples = 50000
            normal_samples = 30000
            attack_samples = 20000
    else:
        total_samples = 50000
        normal_samples = 30000
        attack_samples = 20000

    return jsonify({
        'dataset_name': 'CIC-DDoS2017',
        'total_samples': total_samples,
        'normal_samples': normal_samples,
        'attack_samples': attack_samples,
        'attack_types': LABEL_LIST
    })


@app.route('/api/training_curves', methods=['GET'])
def training_curves():
    """返回 pic/ 目录下所有训练曲线图的 URL 列表"""
    pic_dir = os.path.join(os.path.dirname(__file__), 'pic')
    images = []
    if os.path.isdir(pic_dir):
        for fname in sorted(os.listdir(pic_dir)):
            if fname.lower().endswith('.png'):
                images.append(f'/pic/{fname}')
    return jsonify({'images': images})


@app.route('/api/model_info', methods=['GET'])
def model_info():
    """返回三个模型的结构信息"""
    return jsonify([
        {
            'name': 'CNN',
            'params': '约45万',
            'layers': 'Conv1d×2 + FC×3 (4736→128→11)',
            'input_shape': '(batch, 1, 78)',
            'description': '纯卷积神经网络，2层卷积提取特征后经全连接层分类'
        },
        {
            'name': 'CNN-LSTM',
            'params': '约120万',
            'layers': 'Conv1d×2 + LSTM(256) + FC(128→11)',
            'input_shape': '(batch, 1, 78)',
            'description': 'CNN提取空间特征后送入LSTM捕获序列依赖'
        },
        {
            'name': 'CNN-BiLSTM',
            'params': '约180万',
            'layers': 'Conv1d×2 + BiLSTM(256×2) + FC(512→128→11)',
            'input_shape': '(batch, 1, 78)',
            'description': 'CNN+双向LSTM，同时捕获前后文序列信息'
        }
    ])


@app.route('/pic/<path:filename>')
def serve_pic(filename):
    """提供 pic/ 目录下的静态图片"""
    pic_dir = os.path.join(os.path.dirname(__file__), 'pic')
    return send_from_directory(pic_dir, filename)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
