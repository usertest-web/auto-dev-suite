# AI Dev Workbench

Claude Code + DeepSeek 驱动的自动化开发工作台，涵盖从机器学习到学术写作的 AI 辅助工具集。

---

## 项目一：学术论文自动化写作脚本

> 6 阶段 Pipeline，输入标题和大纲，自动生成格式完整的本科毕业论文 `.docx`

用户只需提供论文标题和粗略大纲，脚本自动完成：模板解析 → 大纲细化 → 文献检索 → 逐章撰写 → Word 排版 → 格式校验。

**技术栈：** pywin32 COM / python-docx / LLM API (Claude/OpenAI) / Semantic Scholar / GB/T 7714-2015

**快速使用：**
```bash
cd thesis-automation
pip install pywin32 python-docx pyyaml anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
python -m src.main --title "论文标题" --outline "1.绪论 2.相关技术 ..."
```

**测试：** `python -m pytest tests/ -v` — 28 tests, all passing

详见：[README_THESIS.md](README_THESIS.md) | [开发日志](docs/DEVELOPMENT_LOG.md)

---

## 项目二：基于机器学习的网络入侵检测系统

基于 CNN-LSTM 混合网络的入侵检测系统（NSL-KDD 数据集），毕业设计实践项目。

**核心功能：**
- Flask + Vue 前后端分离架构
- CNN-LSTM 混合模型训练与评估
- 可视化检测结果界面
- 模型测试集准确率：92%+

**快速使用：**
```bash
cd ids-graduation-project
pip install -r requirements.txt
python app.py          # 后端
cd frontend && npm install && npm run serve   # 前端
```

---

## 仓库信息

- 所有代码均由 Claude Code AI 辅助生成
- 开发方法论：Superpowers 插件体系（头脑风暴 → 设计文档 → 实现计划 → 子代理驱动开发）
- Token 消耗：日均 150-250 万（开发高峰期）

## 后续计划

毕业后持续迭代，目标打磨为可开源通用模板，帮助零基础开发者快速上手 AI 辅助全栈开发与学术写作。
