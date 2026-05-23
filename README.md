# AI Dev Workbench

基于 Claude Code + DeepSeek 驱动的个人全栈自动化工作台。本项目从零开始，完全由 AI 辅助编程完成，作为毕业设计《基于机器学习的网络入侵检测系统》的实践延伸。

## 核心功能

- **智能代码脚手架**：一键生成 Flask + Vue 项目结构
- **模型训练辅助**：自动调参、日志记录、性能评估
- **文档与图表生成**：AI 辅助撰写技术文档、绘制架构图
- **自动化测试**：批量生成单元测试用例

## 技术栈

- 后端：Python / Flask / PyTorch
- 前端：Vue.js
- 模型：CNN-LSTM 混合网络（NSL-KDD 数据集）
- AI 工具：Claude Code（长链推理，单次任务 40-60 轮迭代）

## 项目成果

- 模型测试集准确率：92%+
- 完成前后端联调与可视化检测界面
- 日均 AI Token 消耗：150-250 万（开发高峰期）

## 使用说明

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
python app.py

# 启动前端（需进入 frontend 目录）
npm install
npm run serve
#后续计划
毕业后持续迭代，目标打磨为可开源的通用模板，帮助零基础开发者快速上手 AI 辅助全栈开发。
#致谢
本项目开发过程中大量使用 Claude Code 进行代码生成、Bug 修复与架构优化。
