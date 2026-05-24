# 学术论文自动化写作脚本 — 设计文档

## 概述

自动化生成符合中文本科毕业论文规范的 `.docx` 文件。用户提供论文标题和粗略大纲，系统输出格式完整、引用规范的 Word 论文。

## 技术选型

| 组件 | 技术 | 理由 |
|------|------|------|
| Word 操控 | pywin32 COM 自动化 | 完整访问 Word 全部功能（样式、域、分节符、题注） |
| 模板解析 | python-docx + LLM | python-docx 提取数值，LLM 解析自然语言规范 |
| 内容生成 | LLM API（Claude/OpenAI） | 分章节生成，控制温度和引用密度 |
| 文献检索 | CNKI/万方/Google Scholar/Semantic Scholar | 多层降级，优先中文数据库 |
| 数据传递 | JSON 中间文件 | 阶段间解耦，支持断点续跑 |

## 架构：6 阶段 Pipeline

```
模板解析 → 大纲细化 → 文献检索 → 逐章撰写 → Word排版 → 格式校验
(Parser)  (Expander) (Searcher)  (Writer)   (Composer)  (Verifier)
```

每个阶段读取前一阶段的输出 JSON，处理后写入新的 JSON，最终输出 `.docx` 文件。

运行模式通过 `config.yaml` 控制：
- `auto` — 全自动跑完
- `interactive` — 每阶段完成暂停等用户确认
- `resume` — 从断点续跑

## 阶段 1：模板解析器 (Template Parser)

**职责：** 解析 `.docx` 模板和格式规范文档，生成结构化格式配置。

**输入：**
- 学校下发的 `.docx` 模板文件
- 格式规范文档（PDF 或 `.docx`，自然语言描述排版规则）

**处理逻辑：**
1. `python-docx` 读取模板：页面设置（纸张大小、页边距）、样式定义（字体/字号/间距）、占位符位置（封面字段、声明页、目录位置）、章节结构标记
2. LLM 解析规范文档：提取自然语言描述的格式规则（如"正文宋体小四号 1.5 倍行距"）
3. 合并：python-docx 结果为基础，LLM 结果补充和校验，不一致时以规范文档为准并警告

**输出：** `01-parsed-template.json`
```json
{
  "page": { "size": "A4", "margin_top_cm": 2.5, "margin_bottom_cm": 2.5,
            "margin_left_cm": 3.0, "margin_right_cm": 2.5 },
  "styles": {
    "cover_title": { "font": "黑体", "size_pt": 22, "bold": true, "align": "center" },
    "heading_1":   { "font": "黑体", "size_pt": 16, "bold": true },
    "heading_2":   { "font": "黑体", "size_pt": 14, "bold": true },
    "body":        { "font": "宋体", "size_pt": 12, "line_spacing": 1.5, "first_indent_chars": 2 },
    "caption":     { "font": "宋体", "size_pt": 10, "align": "center" },
    "reference":   { "font": "宋体", "size_pt": 10.5, "hanging_indent_chars": 2 }
  },
  "structure": {
    "cover_fields": ["title", "author", "student_id", "advisor", "date"],
    "chapter_sequence": ["cover", "declaration", "abstract_cn", "abstract_en", "toc", "chapters", "references", "acknowledgement"]
  },
  "citation_format": "GB/T 7714-2015",
  "citation_style": "numbered"
}
```

## 阶段 2：大纲细化器 (Outline Expander)

**职责：** 将用户粗略大纲扩展为详细的写作计划。

**输入：**
- 论文标题
- 用户提供的粗略大纲（章标题列表）
- 阶段 1 的格式配置（用于估算字数）

**处理逻辑：**
1. LLM 标准化大纲为章节树（章 → 节 → 小节，最多三级）
2. 为每个末级标题生成 3-5 条具体写作要点
3. 按预期总字数反推每节字数分配
4. 为每章生成文献检索关键词和引用密度标记
5. 并发处理独立的节标题扩展

**输出：** `02-writing-plan.json`
```json
{
  "title": "...",
  "total_word_count": 15000,
  "chapters": [
    {
      "num": "1", "title": "绪论", "word_count": 2000,
      "sections": [
        {
          "num": "1.1", "title": "研究背景与意义",
          "word_count": 800,
          "key_points": ["要点1", "要点2", "要点3"],
          "search_queries": ["关键词1", "关键词2"],
          "citation_density": "high"
        }
      ]
    }
  ]
}
```

## 阶段 3：文献检索器 (Literature Searcher)

**职责：** 从学术数据库检索真实文献，生成格式化的参考文献列表。

**输入：** 阶段 2 中的 search_queries

**数据源（按优先级降级）：**

| 优先级 | 来源 | 覆盖范围 | 接口 |
|--------|------|---------|------|
| 1 | 知网 (CNKI) | 中文论文/期刊 | 网页爬取/API |
| 2 | 万方 (Wanfang) | 中文期刊 | 网页爬取 |
| 3 | Semantic Scholar | 计算机/工程英文 | 免费 API |
| 4 | Google Scholar | 全覆盖 | 爬取（备选） |

**处理逻辑：**
1. 每个 search_query 检索前 10-20 条
2. 合并去重后 LLM 按相关度排序
3. 选出 top 15-25 篇，确保文献类型覆盖 [J][D][C][M][EB/OL]
4. LLM 为每篇生成 GB/T 7714-2015 格式引用
5. 检索失败时自动降级到下一数据源

**输出：** `03-references.json`
```json
{
  "references": [
    {
      "id": 1,
      "gb7714": "张三, 李四. 校园二手交易平台的设计与实现[J]. 计算机应用, 2023, 43(3): 45-52.",
      "metadata": {
        "title": "...", "authors": ["张三", "李四"], "year": 2023,
        "journal": "计算机应用", "type": "J", "doi": "...", "source": "cnki"
      },
      "keywords": ["校园二手交易"],
      "relevance_score": 0.92
    }
  ],
  "type_distribution": { "J": 12, "D": 3, "C": 4, "M": 1 },
  "total": 20
}
```

**风险：** 知网需要校园网/VPN。缓解：支持配置代理，Semantic Scholar + Google Scholar 保底。

## 阶段 4：逐章撰写器 (Content Writer)

**职责：** 调用 LLM 逐章生成论文正文，管理上下文窗口和引用插入。

**输入：** 写作计划 + 参考文献列表 + 格式配置

**处理逻辑：**
1. 按章顺序逐章生成，每章是一次 LLM 调用
2. Prompt 包含：系统指令（引用规范）+ 格式规则 + 前一章摘要 + 本章大纲 + 本章可用文献
3. 上下文管理：用前一章 200-300 字摘要代替完整前文，保证不超 token 限制
4. LLM 在正文中用 `[1]`、`[3-5]` 标记引用位置
5. 不同类型章节用不同 temperature（绪论 0.5 / 技术介绍 0.3 / 实现 0.5 / 总结 0.6）

**输出：** `04-draft.json`
```json
{
  "chapters": [
    {
      "num": "1", "title": "绪论",
      "sections": [
        {
          "num": "1.1", "title": "研究背景与意义",
          "content": "正文内容... [1][3][5] ...",
          "cited_refs": [1, 3, 5],
          "word_count_actual": 820
        }
      ]
    }
  ],
  "uncited_refs": [19, 20]
}
```

## 阶段 5：Word 排版器 (Word Composer)

**职责：** 通过 pywin32 COM 将草稿组装为格式完美的 .docx 文件。模拟真实 Word 用户操作行为。

**输入：** 草稿 JSON + 参考文献列表 + 模板配置

**COM 操作序列：**
1. 打开模板 .docx
2. 封面页：定位占位符，替换为论文元数据，应用样式
3. 声明页：填充声明文本
4. 中文摘要 + 关键词：写入正文，应用 body 样式
5. 英文摘要 + Keywords：同上，英文用 Times New Roman
6. 目录页：调用 `TablesOfContents.Add()` 插入 Word 自动目录域
7. 逐章写入：每章标题 → heading_1，节标题 → heading_2，正文 → body，章间插入分页符
8. 引用处理：将 `[1]` 标记渲染为上标格式
9. 图表题注：用 `InsertCaption` 实现自动编号
10. 参考文献：写入 GB/T 7714 条目，应用 reference 样式
11. 致谢：写入标题和正文
12. 全局设置：分节符控制页眉页脚/页码，更新所有域（目录、交叉引用）
13. 另存为最终文件

**关键设计决策：**
- 样式来源为模板定义的命名样式，不硬编码字体
- 目录使用 Word TOC 域自动生成，不手写
- 图表编号用 Word Caption 功能，支持自动更新
- 分节符实现封面无页眉/正文有页眉/不同页码格式

**输出：** `05-thesis.docx`

## 阶段 6：格式校验器 (Format Verifier)

**职责：** 检查最终 .docx 的格式合规性，生成报告，可选自动修复。

**输入：** 最终 .docx + 格式配置

**检查维度（约 30+ 检查项）：**

| 维度 | 检查项示例 |
|------|-----------|
| 页面级 | 纸张大小、页边距、页眉页脚距离 |
| 字体段落 | 每级样式字体/字号/加粗/行距/缩进 |
| 结构完整性 | 封面字段、声明页、摘要、目录、章节、参考文献、致谢 |
| 引用一致性 | 正文引用编号连续、无死条目、格式一致 |
| 编号 | 图表编号按章重置、页码连续 |

**自动修复能力：** 字体/字号/行距/缩进/页边距/页眉页脚/页码可自动通过 COM 修复。缺失内容、引用逻辑错误需人工处理。

**输出：** `06-verification-report.json`
```json
{
  "pass": false,
  "total_checks": 32, "passed": 28, "failed": 4,
  "issues": [
    { "severity": "error", "dimension": "字体段落", "detail": "...",
      "location": "第12页第3段", "auto_fixable": true }
  ],
  "auto_fixed_count": 2
}
```

## 运行配置

`config.yaml`:
```yaml
mode: interactive           # auto | interactive | resume
llm:
  provider: claude          # claude | openai
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY
academic_db:
  cnki_proxy: null          # 校园网代理，如 http://proxy.university.edu:8080
  fallback: semantic_scholar
output_dir: ./output
template_path: ./data/template.docx
spec_path: ./data/format-spec.pdf
```

## 项目结构

```
thesis-automation/
├── config.yaml
├── data/
│   ├── template.docx                # 学校模板
│   └── format-spec.pdf              # 格式规范文档
├── src/
│   ├── main.py                      # 入口，串联 pipeline
│   ├── config.py                    # 配置读取
│   ├── stage1_parser.py             # 模板解析
│   ├── stage2_expander.py           # 大纲细化
│   ├── stage3_searcher.py           # 文献检索
│   ├── stage4_writer.py             # 逐章撰写
│   ├── stage5_composer.py           # Word 排版
│   ├── stage6_verifier.py           # 格式校验
│   ├── llm_client.py                # LLM API 封装
│   ├── word_com.py                  # pywin32 COM 工具函数
│   └── pipeline.py                  # Pipeline 运行控制
├── output/
│   └── <thesis-slug>/
│       ├── 01-parsed-template.json
│       ├── 02-writing-plan.json
│       ├── 03-references.json
│       ├── 04-draft.json
│       ├── 05-thesis.docx
│       └── 06-verification-report.json
├── tests/
└── docs/superpowers/specs/
    └── 2026-05-25-thesis-automation-design.md
```

## 风险与限制

| 风险 | 缓解措施 |
|------|---------|
| 知网访问不稳定 | 多层数据源降级（Semantic Scholar / Google Scholar 保底） |
| LLM 生成内容可能包含事实错误 | 阶段 6 不检查内容正确性，用户需自行审核 |
| 长篇论文超出 LLM 上下文窗 | 滑动窗口 + 摘要压缩策略 |
| GB/T 7714 格式由 LLM 生成可能出错 | 阶段 6 校验引用格式一致性 |
| COM 操作慢且需要 Word 运行环境 | 仅阶段 5/6 需要，其余阶段在后台独立运行 |
