# 学术论文自动化写作脚本

> 6 阶段 Pipeline 自动生成符合中文本科毕业论文规范的 `.docx` 文件

## 它能做什么

你只需要提供**论文标题**和**粗略大纲**（章标题列表），脚本自动完成：

1. **解析模板** — 读取学校 `.docx` 模板 + 格式规范文档，提取排版规则
2. **细化大纲** — 将粗略大纲扩展为带字数分配和写作要点的详细计划
3. **检索文献** — 从学术数据库检索真实文献，生成 GB/T 7714-2015 格式引用
4. **逐章撰写** — 调用 LLM 按章生成正文，自动插入文献引用标记
5. **Word 排版** — 通过 pywin32 COM 组装为格式完美的 `.docx` 文件
6. **格式校验** — 检查页面/字体/引用/结构合规性，可选自动修复

## 快速开始

```bash
# 1. 安装依赖
pip install pywin32 python-docx pyyaml anthropic pytest requests

# 2. 放入学校文件
cp 你的模板.docx data/template.docx
cp 格式规范.pdf data/format-spec.pdf

# 3. 配置 API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 4. 运行
python -m src.main \
  --title "基于Spring Boot的校园二手交易平台设计与实现" \
  --outline "1.绪论 2.相关技术 3.需求分析 4.系统设计 5.系统实现 6.测试 7.总结"
```

## 架构

```
模板解析 → 大纲细化 → 文献检索 → 逐章撰写 → Word排版 → 格式校验
(Parser)  (Expander) (Searcher)  (Writer)   (Composer)  (Verifier)
```

每个阶段通过 JSON 中间文件传递数据，支持断点续跑。

## 运行模式

编辑 `config.yaml`：

```yaml
mode: interactive   # auto（全自动）| interactive（每阶段确认）| resume（断点续跑）
```

## 测试

```bash
python -m pytest tests/ -v    # 28 tests, all passing
```

## 项目结构

```
thesis-automation/
├── src/                   # 11 个模块
│   ├── main.py            # CLI 入口
│   ├── config.py          # 配置系统
│   ├── llm_client.py      # LLM 客户端 (Claude/OpenAI)
│   ├── word_com.py        # Word COM 自动化
│   ├── pipeline.py        # Pipeline 编排器
│   ├── stage1_parser.py   # 阶段 1：模板解析
│   ├── stage2_expander.py # 阶段 2：大纲细化
│   ├── stage3_searcher.py # 阶段 3：文献检索
│   ├── stage4_writer.py   # 阶段 4：逐章撰写
│   ├── stage5_composer.py # 阶段 5：Word 排版
│   └── stage6_verifier.py # 阶段 6：格式校验
├── tests/                 # 10 个测试文件
├── docs/                  # 开发文档
├── config.yaml            # 运行配置
└── output/                # 生成输出
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Word 操控 | pywin32 COM（样式/目录/页眉页脚/域） |
| 内容生成 | LLM API（Claude / OpenAI） |
| 文献检索 | Semantic Scholar API |
| 模板解析 | python-docx + LLM |
| 引用格式 | GB/T 7714-2015 顺序编码制 |

## 文档

- [设计规格文档](docs/superpowers/specs/2026-05-25-thesis-automation-design.md)
- [实现计划](docs/superpowers/plans/2026-05-25-thesis-automation-plan.md)
- [开发日志](docs/DEVELOPMENT_LOG.md)

## 限制

- 需要本机安装 Microsoft Word（阶段 5/6 的 COM 依赖）
- LLM 生成内容需人工审核事实准确性
- 知网检索需要校园网/VPN（Semantic Scholar 保底）
