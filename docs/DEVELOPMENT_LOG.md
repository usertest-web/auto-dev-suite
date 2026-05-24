# 学术论文自动化写作脚本 — 开发日志

## 项目概述

自动化生成符合中文本科毕业论文规范的 `.docx` 文件。用户提供论文标题和粗略大纲，系统通过 6 阶段 Pipeline 输出格式完整、引用规范的 Word 论文。

- **仓库：** https://github.com/usertest-web/ai-dev-workbench
- **开发日期：** 2026-05-25
- **开发方式：** Superpowers 方法论 — 头脑风暴 → 设计文档 → 实现计划 → 子代理驱动开发

## 开发流程（Superpowers 方法论）

本次开发完整使用了 Superpowers 插件体系，流程如下：

### 1. 头脑风暴 (brainstorming)

通过渐进式提问明确需求，输出了完整的设计规格。

**关键决策：**
- 技术方案：pywin32 COM 自动化（而非 python-docx 或混合方案）
- 架构模式：6 阶段 Pipeline（而非 Agent 循环或模板填充）
- 学术领域：中文本科毕业论文，GB/T 7714-2015 引用格式
- 内容生成：LLM API（Claude/OpenAI）
- 文献检索：多层降级（知网 → 万方 → Semantic Scholar → Google Scholar）
- 运行模式：可配置（全自动 / 交互式 / 断点续跑）

**产出：** `docs/superpowers/specs/2026-05-25-thesis-automation-design.md`

### 2. 实现计划 (writing-plans)

将设计规格分解为 12 个 bite-sized 任务，每个任务含精确的代码、测试和提交命令，遵循 TDD 原则。

**产出：** `docs/superpowers/plans/2026-05-25-thesis-automation-plan.md`

### 3. 子代理驱动开发 (subagent-driven-development)

每个任务派发独立子代理实现，通过两阶段审查（Spec 合规 → 代码质量）保证质量。

**审查流程：**
- Spec 合规审查：验证实现是否完全匹配计划要求
- 代码质量审查：检查架构、错误处理、测试覆盖率、生产就绪度

**发现并修复的关键问题：**
- Task 1：空 YAML 文件导致 AttributeError 崩溃（添加 None 守卫）
- Task 1：`get_api_key()` 缺少测试覆盖（补充 2 个测试）
- Task 2：环境变量泄漏（改用 monkeypatch）
- Task 3：`json.loads` 无错误处理（添加 JSONDecodeError 保护）
- Task 3：样式字段假值检查问题（改用 `is not None`）
- Task 4：LLM 响应 JSON 解析无保护（与 Task 3 统一处理模式）

## 架构总览

```
用户输入（标题 + 大纲）
       │
       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  阶段 1      │    │  阶段 2      │    │  阶段 3      │    │  阶段 4      │    │  阶段 5      │    │  阶段 6      │
│  模板解析器   │───→│  大纲细化器   │───→│  文献检索器   │───→│  逐章撰写器   │───→│  Word排版器   │───→│  格式校验器   │
│              │    │              │    │              │    │              │    │              │    │              │
│ python-docx  │    │  LLM API     │    │ Semantic     │    │  LLM API     │    │  pywin32     │    │  python-docx │
│ + LLM        │    │              │    │ Scholar API  │    │  (逐章生成)   │    │  COM         │    │  + 自动修复   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼                   ▼                   ▼
  格式配置JSON         写作计划JSON         参考文献JSON         完整草稿JSON          .docx文件          校验报告
```

### 数据流

所有阶段通过 JSON 中间文件传递数据，支持断点续跑：

```
output/<thesis-slug>/
├── 01-parsed-template.json      # 阶段 1 输出 — 模板格式配置
├── 02-writing-plan.json         # 阶段 2 输出 — 详细写作计划
├── 03-references.json           # 阶段 3 输出 — GB/T 7714 参考文献
├── 04-draft.json                # 阶段 4 输出 — 完整正文草稿
├── 05-thesis.docx               # 阶段 5 输出 — 格式化 Word 论文
└── 06-verification-report.json  # 阶段 6 输出 — 格式校验报告
```

## 项目结构

```
thesis-automation/
├── config.yaml                       # 运行配置（LLM提供者/模式/路径）
├── data/
│   ├── template.docx                 # 学校模板（待放入）
│   └── format-spec.pdf               # 格式规范文档（待放入）
├── src/
│   ├── main.py                       # CLI 入口
│   ├── config.py                     # 配置系统（YAML → 数据类）
│   ├── llm_client.py                 # LLM 客户端（Claude/OpenAI 双后端）
│   ├── word_com.py                   # Word COM 自动化工具
│   ├── pipeline.py                   # Pipeline 编排器（auto/interactive/resume）
│   ├── stage1_parser.py              # 阶段 1：模板解析
│   ├── stage2_expander.py            # 阶段 2：大纲细化
│   ├── stage3_searcher.py            # 阶段 3：文献检索
│   ├── stage4_writer.py              # 阶段 4：逐章撰写
│   ├── stage5_composer.py            # 阶段 5：Word 排版
│   └── stage6_verifier.py            # 阶段 6：格式校验
├── tests/
│   ├── test_config.py                # 5 tests
│   ├── test_llm_client.py            # 4 tests
│   ├── test_stage1_parser.py         # 3 tests
│   ├── test_stage2_expander.py       # 2 tests
│   ├── test_stage3_searcher.py       # 2 tests
│   ├── test_stage4_writer.py         # 2 tests
│   ├── test_stage5_composer.py       # 1 test
│   ├── test_stage6_verifier.py       # 3 tests
│   ├── test_word_com.py              # 3 tests
│   └── test_pipeline.py              # 3 tests
├── docs/
│   ├── DEVELOPMENT_LOG.md            # 本文件 — 开发日志
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-05-25-thesis-automation-design.md   # 设计文档
│       └── plans/
│           └── 2026-05-25-thesis-automation-plan.md     # 实现计划
└── output/                           # 生成输出目录
```

## 测试结果

**28 tests, all passing** (10 test files, 0 failures)

| 模块 | 测试数 | 覆盖内容 |
|------|--------|---------|
| config | 5 | YAML 解析、缺失文件、环境变量、默认值 |
| llm_client | 4 | Claude/OpenAI 创建、API 调用、不支持提供者 |
| stage1_parser | 3 | Mock docx 解析、序列化、JSON 往返 |
| stage2_expander | 2 | LLM 大纲扩展、WritingPlan 序列化 |
| stage3_searcher | 2 | 文献检索流程、Reference 序列化 |
| stage4_writer | 2 | 章节生成、未引用文献检测 |
| stage5_composer | 1 | Word COM 操作序列验证 |
| stage6_verifier | 3 | 格式报告、严重性排序、pass 判定 |
| word_com | 3 | 上下文管理器、样式应用、分页符 |
| pipeline | 3 | 上下文存储、阶段顺序、断点续跑 |

## 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Word 操控 | pywin32 COM | 完整的 Word 自动化（样式、目录、页眉页脚、域） |
| 模板解析 | python-docx | 读取模板页面设置和样式 |
| 格式规范解析 | LLM API | 从自然语言规范中提取结构化规则 |
| 内容生成 | LLM API (Claude/OpenAI) | 大纲细化、逐章撰写、文献筛选格式化 |
| 文献检索 | Semantic Scholar API | 实时学术文献检索 |
| 引用格式 | GB/T 7714-2015 | 顺序编码制引用 |
| 运行配置 | YAML | 模式/LLM/路径配置 |
| 测试 | pytest + unittest.mock | 28 个单元测试，mock 外部依赖 |

## 使用方法

### 前置准备

1. 安装依赖：
   ```bash
   pip install pywin32 python-docx pyyaml anthropic openai pytest
   ```

2. 放入学校模板文件：
   - `data/template.docx` — Word 模板
   - `data/format-spec.pdf` — 格式规范文档

3. 配置 LLM API key：
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."    # 如用 Claude
   export OPENAI_API_KEY="sk-..."           # 如用 OpenAI
   ```

### 运行

```bash
# 交互模式（每阶段完成后确认）
python -m src.main \
  --title "基于Spring Boot的校园二手交易平台设计与实现" \
  --outline "1.绪论 2.相关技术 3.需求分析 4.系统设计 5.系统实现 6.测试 7.总结"

# 全自动模式
# 编辑 config.yaml，将 mode 改为 auto

# 断点续跑
# 编辑 config.yaml，将 mode 改为 resume
```

### 运行测试

```bash
python -m pytest tests/ -v
```

## 风险与限制

| 风险 | 缓解措施 |
|------|---------|
| 知网需要校园网/VPN | Semantic Scholar 保底 |
| LLM 生成内容可能包含事实错误 | 人工审核，阶段 6 不检查内容正确性 |
| 长篇论文超出上下文窗 | 滑动窗口 + 摘要压缩策略 |
| GB/T 7714 格式可能出错 | 阶段 6 校验引用格式一致性 |
| COM 操作需 Word 运行环境 | 仅阶段 5/6 需要 |

## 后续改进方向

- [ ] 支持知网/万方 API 直接检索
- [ ] 添加图表自动生成（Mermaid → Word 图片）
- [ ] 多模板支持（不同学校模板切换）
- [ ] Web UI 界面
- [ ] 批量论文生成
- [ ] 查重预检集成

## 相关文档

- [设计规格文档](superpowers/specs/2026-05-25-thesis-automation-design.md)
- [实现计划](superpowers/plans/2026-05-25-thesis-automation-plan.md)
- [Superpowers 插件](https://github.com/obra/superpowers)
