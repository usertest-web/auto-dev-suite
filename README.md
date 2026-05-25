# auto-dev-suite

全栈自动化开发套件 —— 支持脚手架生成、CI/CD 配置、多环境部署。

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Vue 3 + Vite | IDS 入侵检测可视化面板 |
| 后端 | Flask (Python) | REST API 服务 |
| 机器学习 | PyTorch / CNN-LSTM | 网络入侵检测模型（NSL-KDD 数据集） |
| 文档自动化 | python-docx / pywin32 COM | 学术论文自动排版输出 .docx |
| LLM 编排 | Anthropic SDK / Claude API | 6 阶段 Pipeline 长链推理写作 |

## 项目结构

```
auto-dev-suite/
├── ids-graduation-project/   # Flask + Vue + PyTorch 入侵检测系统
│   ├── model.py              # CNN-LSTM 混合网络模型
│   ├── train.py              # 模型训练脚本
│   ├── web_app.py            # Flask 后端
│   ├── window.py             # PyQt 桌面界面
│   └── main.py               # 入口
├── src/                      # 学术论文自动化写作 Pipeline
│   ├── stage1_parser.py      # 阶段1：模板解析
│   ├── stage2_expander.py    # 阶段2：大纲细化
│   ├── stage3_searcher.py    # 阶段3：文献检索
│   ├── stage4_writer.py      # 阶段4：逐章撰写
│   ├── stage5_composer.py    # 阶段5：Word 排版
│   ├── stage6_verifier.py    # 阶段6：格式校验
│   └── llm_client.py         # LLM API 客户端
├── tests/                    # 单元测试（28 tests）
├── docs/                     # 开发文档与设计规范
└── config.yaml               # 全局配置
```

## Agent 使用说明

本项目的代码均由 **Claude Code Agent** 辅助生成，采用 **40-60 轮长链推理** 的深度协作模式：

| 阶段 | 轮次 | 产出 |
|------|------|------|
| 头脑风暴 | 5-8 轮 | 技术方案设计文档 |
| 实现计划 | 8-12 轮 | 分步实施计划与文件清单 |
| 子代理并行开发 | 15-25 轮 | 各模块独立实现 |
| 调试与修复 | 8-12 轮 | Bug 修复与边界处理 |
| 代码审查 | 4-6 轮 | 安全性与代码质量审查 |

**方法论**：Superpowers 插件体系 → 结构化设计文档 → 子代理驱动开发 → 验证闭环

## 日均 Token 消耗

| 场景 | 输入 Token | 输出 Token | 合计 |
|------|-----------|-----------|------|
| 常规开发日 | 50-80 万 | 100-170 万 | **150-250 万** |
| 高峰开发日（新模块） | 120-180 万 | 250-400 万 | **370-580 万** |
| Code Review 日 | 200-300 万 | 100-150 万 | **300-450 万** |

> 数据基于 Claude Code + DeepSeek-v4-pro[1M] 组合使用场景，1M 上下文窗口支持单轮加载全量代码库。

## 快速开始

```bash
# 学术论文自动写作
cd auto-dev-suite
pip install pywin32 python-docx pyyaml anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
python -m src.main --title "论文标题" --outline "1.绪论 2.相关技术 ..."

# 入侵检测系统
cd ids-graduation-project
pip install -r requirements.txt
python web_app.py
```

## 许可证

MIT License
