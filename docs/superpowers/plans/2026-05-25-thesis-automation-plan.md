# 学术论文自动化写作脚本 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 6-stage pipeline that automates Chinese undergraduate thesis production from title+outline to formatted .docx.

**Architecture:** Pipeline pattern with JSON intermediate files for stage decoupling. Stages 1-4 use python-docx + LLM APIs for content work. Stages 5-6 use pywin32 COM for Word automation. A shared pipeline runner (`pipeline.py`) orchestrates execution with auto/interactive/resume modes.

**Tech Stack:** Python 3.10+, pywin32, python-docx, anthropic SDK (or openai), PyYAML, pytest

---

### Task 1: Project Scaffolding

**Files:**
- Create: `config.yaml`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test for config loading**

```python
# tests/test_config.py
import pytest
from src.config import Config, load_config

def test_load_config_parses_yaml():
    yaml_content = """
mode: auto
llm:
  provider: claude
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY
academic_db:
  cnki_proxy: null
  fallback: semantic_scholar
output_dir: ./output
template_path: ./data/template.docx
spec_path: ./data/format-spec.pdf
"""
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        tmp_path = f.name
    try:
        config = load_config(tmp_path)
        assert config.mode == "auto"
        assert config.llm.provider == "claude"
        assert config.llm.model == "claude-sonnet-4-6"
        assert config.llm.api_key_env == "ANTHROPIC_API_KEY"
        assert config.academic_db.cnki_proxy is None
        assert config.academic_db.fallback == "semantic_scholar"
        assert config.output_dir == "./output"
    finally:
        os.unlink(tmp_path)

def test_load_config_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("./nonexistent.yaml")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_config.py -v`
Expected: FAIL — module not found / import error

- [ ] **Step 3: Write config.yaml template**

```yaml
# config.yaml
mode: interactive           # auto | interactive | resume
llm:
  provider: claude          # claude | openai
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY
academic_db:
  cnki_proxy: null
  fallback: semantic_scholar
output_dir: ./output
template_path: ./data/template.docx
spec_path: ./data/format-spec.pdf
```

- [ ] **Step 4: Write src/config.py**

```python
# src/config.py
from dataclasses import dataclass, field
from typing import Optional
import yaml
import os


@dataclass
class LLMConfig:
    provider: str = "claude"
    model: str = "claude-sonnet-4-6"
    api_key_env: str = "ANTHROPIC_API_KEY"

    def get_api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ValueError(f"Environment variable {self.api_key_env} not set")
        return key


@dataclass
class AcademicDBConfig:
    cnki_proxy: Optional[str] = None
    fallback: str = "semantic_scholar"


@dataclass
class Config:
    mode: str = "interactive"
    llm: LLMConfig = field(default_factory=LLMConfig)
    academic_db: AcademicDBConfig = field(default_factory=AcademicDBConfig)
    output_dir: str = "./output"
    template_path: str = "./data/template.docx"
    spec_path: str = "./data/format-spec.pdf"


def load_config(path: str = "config.yaml") -> Config:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    llm_data = data.get("llm", {})
    llm = LLMConfig(
        provider=llm_data.get("provider", "claude"),
        model=llm_data.get("model", "claude-sonnet-4-6"),
        api_key_env=llm_data.get("api_key_env", "ANTHROPIC_API_KEY"),
    )
    db_data = data.get("academic_db", {})
    academic_db = AcademicDBConfig(
        cnki_proxy=db_data.get("cnki_proxy"),
        fallback=db_data.get("fallback", "semantic_scholar"),
    )
    return Config(
        mode=data.get("mode", "interactive"),
        llm=llm,
        academic_db=academic_db,
        output_dir=data.get("output_dir", "./output"),
        template_path=data.get("template_path", "./data/template.docx"),
        spec_path=data.get("spec_path", "./data/format-spec.pdf"),
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_config.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
cd C:/Users/Surtr/thesis-automation
git add config.yaml src/__init__.py src/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: add project scaffolding with config system"
```

---

### Task 2: LLM Client

**Files:**
- Create: `src/llm_client.py`
- Create: `tests/test_llm_client.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm_client.py
import pytest
import os
from unittest.mock import patch, MagicMock
from src.llm_client import LLMClient, create_llm_client
from src.config import Config, LLMConfig

def test_create_claude_client():
    config = Config(
        llm=LLMConfig(provider="claude", model="claude-sonnet-4-6", api_key_env="TEST_KEY")
    )
    os.environ["TEST_KEY"] = "fake-key"
    client = create_llm_client(config)
    assert client.provider == "claude"
    assert client.model == "claude-sonnet-4-6"

def test_create_openai_client():
    config = Config(
        llm=LLMConfig(provider="openai", model="gpt-4o", api_key_env="TEST_KEY2")
    )
    os.environ["TEST_KEY2"] = "fake-key"
    client = create_llm_client(config)
    assert client.provider == "openai"
    assert client.model == "gpt-4o"

def test_llm_client_complete_claude():
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        mock_instance.messages.create.return_value.content = [MagicMock(text="response text")]
        mock_instance.messages.create.return_value.usage.input_tokens = 100
        mock_instance.messages.create.return_value.usage.output_tokens = 50

        client = LLMClient(provider="claude", model="claude-sonnet-4-6", api_key="key")
        result = client.complete(
            system="You are helpful.",
            prompt="Say hello",
            temperature=0.5,
            max_tokens=2000,
        )
        assert result.text == "response text"
        assert result.input_tokens == 100
        assert result.output_tokens == 50

def test_llm_client_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported provider"):
        LLMClient(provider="unknown", model="x", api_key="k")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_llm_client.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write src/llm_client.py**

```python
# src/llm_client.py
from dataclasses import dataclass
from typing import Optional
from src.config import Config


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int


class LLMClient:
    def __init__(self, provider: str, model: str, api_key: str):
        if provider not in ("claude", "openai"):
            raise ValueError(f"Unsupported provider: {provider}")
        self.provider = provider
        self.model = model
        self.api_key = api_key

    def complete(
        self,
        system: str,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        if self.provider == "claude":
            return self._complete_claude(system, prompt, temperature, max_tokens)
        else:
            return self._complete_openai(system, prompt, temperature, max_tokens)

    def _complete_claude(self, system: str, prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def _complete_openai(self, system: str, prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return LLMResponse(
            text=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )


def create_llm_client(config: Config) -> LLMClient:
    return LLMClient(
        provider=config.llm.provider,
        model=config.llm.model,
        api_key=config.llm.get_api_key(),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_llm_client.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/llm_client.py tests/test_llm_client.py
git commit -m "feat: add LLM client with Claude and OpenAI support"
```

---

### Task 3: Stage 1 — Template Parser

**Files:**
- Create: `src/stage1_parser.py`
- Create: `tests/test_stage1_parser.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage1_parser.py
import json
import pytest
from unittest.mock import patch, MagicMock
from src.stage1_parser import parse_template, ParsedTemplate, StyleDef, PageSettings

def test_parse_template_from_docx():
    with patch("src.stage1_parser.Document") as mock_doc:
        mock_doc.return_value.sections = [MagicMock()]
        section = mock_doc.return_value.sections[0]
        section.page_width.cm = 21.0
        section.page_height.cm = 29.7
        section.top_margin.cm = 2.5
        section.bottom_margin.cm = 2.5
        section.left_margin.cm = 3.0
        section.right_margin.cm = 2.5

        mock_style = MagicMock()
        mock_style.name = "Heading 1"
        mock_style.font.name = "黑体"
        mock_style.font.size.pt = 16
        mock_style.font.bold = True
        mock_style.paragraph_format.alignment = 1
        mock_style.paragraph_format.space_before.pt = 12
        mock_style.paragraph_format.space_after.pt = 6
        mock_style.paragraph_format.line_spacing = 1.5
        mock_style.paragraph_format.first_line_indent.cm = 0.74
        mock_doc.return_value.styles = [mock_style]

        result = parse_template("fake_template.docx")

        assert result.page.margin_top_cm == 2.5
        assert result.page.margin_left_cm == 3.0
        assert len(result.raw_styles) == 1


def test_parsed_template_to_json():
    tmpl = ParsedTemplate(
        page=PageSettings(
            size="A4", margin_top_cm=2.5, margin_bottom_cm=2.5,
            margin_left_cm=3.0, margin_right_cm=2.5
        ),
        raw_styles={"Heading 1": {"font": "黑体", "size_pt": 16, "bold": True}},
        structure={"cover_fields": ["title"], "chapter_sequence": ["cover", "chapters"]},
        declaration_text="声明",
    )
    d = tmpl.to_dict()
    assert d["page"]["size"] == "A4"
    assert d["structure"]["cover_fields"] == ["title"]


def test_save_and_load_json(tmp_path):
    tmpl = ParsedTemplate(
        page=PageSettings(),
        raw_styles={"body": {"font": "宋体", "size_pt": 12}},
        structure={"cover_fields": [], "chapter_sequence": []},
        declaration_text="",
    )
    out_path = tmp_path / "01-parsed-template.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tmpl.to_dict(), f, ensure_ascii=False, indent=2)
    with open(out_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["raw_styles"]["body"]["font"] == "宋体"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage1_parser.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/stage1_parser.py**

```python
# src/stage1_parser.py
from dataclasses import dataclass, field
from typing import Optional
import json
from docx import Document


@dataclass
class PageSettings:
    size: str = "A4"
    margin_top_cm: float = 2.5
    margin_bottom_cm: float = 2.5
    margin_left_cm: float = 3.0
    margin_right_cm: float = 2.5

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "margin_top_cm": self.margin_top_cm,
            "margin_bottom_cm": self.margin_bottom_cm,
            "margin_left_cm": self.margin_left_cm,
            "margin_right_cm": self.margin_right_cm,
        }


@dataclass
class ParsedTemplate:
    page: PageSettings = field(default_factory=PageSettings)
    raw_styles: dict = field(default_factory=dict)
    structure: dict = field(default_factory=dict)
    declaration_text: str = ""

    def to_dict(self) -> dict:
        return {
            "page": self.page.to_dict(),
            "styles": {},  # Populated after LLM parsing of spec
            "raw_styles": self.raw_styles,
            "structure": self.structure,
            "declaration_text": self.declaration_text,
            "citation_format": "GB/T 7714-2015",
            "citation_style": "numbered",
        }


def parse_template(template_path: str) -> ParsedTemplate:
    doc = Document(template_path)
    section = doc.sections[0]
    page = PageSettings(
        margin_top_cm=round(section.top_margin.cm, 1),
        margin_bottom_cm=round(section.bottom_margin.cm, 1),
        margin_left_cm=round(section.left_margin.cm, 1),
        margin_right_cm=round(section.right_margin.cm, 1),
    )

    raw_styles = {}
    for style in doc.styles:
        if style.type is not None:
            style_info = {}
            if style.font.name:
                style_info["font"] = style.font.name
            if style.font.size:
                style_info["size_pt"] = style.font.size.pt
            style_info["bold"] = style.font.bold
            if style.paragraph_format.alignment is not None:
                style_info["alignment"] = style.paragraph_format.alignment
            if style.paragraph_format.space_before:
                style_info["space_before_pt"] = style.paragraph_format.space_before.pt
            if style.paragraph_format.space_after:
                style_info["space_after_pt"] = style.paragraph_format.space_after.pt
            if style.paragraph_format.line_spacing:
                style_info["line_spacing"] = style.paragraph_format.line_spacing
            if style.paragraph_format.first_line_indent:
                style_info["first_indent_cm"] = round(style.paragraph_format.first_line_indent.cm, 2)
            raw_styles[style.name] = style_info

    structure = {
        "cover_fields": ["title", "author", "student_id", "advisor", "date"],
        "chapter_sequence": [
            "cover", "declaration", "abstract_cn", "abstract_en",
            "toc", "chapters", "references", "acknowledgement"
        ],
    }

    return ParsedTemplate(
        page=page,
        raw_styles=raw_styles,
        structure=structure,
    )


def parse_format_spec(spec_path: str, llm_client) -> dict:
    """Use LLM to extract formatting rules from a natural-language spec document."""
    import docx as dx
    try:
        doc = dx.Document(spec_path)
        spec_text = "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_text = f.read()

    system = "你是论文排版格式专家。从格式规范文档中提取结构化的排版规则。"
    prompt = f"""从以下格式规范文档中提取所有排版规则，以 JSON 格式返回。

返回格式示例：
{{
  "styles": {{
    "cover_title": {{"font": "黑体", "size_pt": 22, "bold": true, "align": "center"}},
    "heading_1": {{"font": "黑体", "size_pt": 16, "bold": true}},
    "heading_2": {{"font": "黑体", "size_pt": 14, "bold": true}},
    "body": {{"font": "宋体", "size_pt": 12, "line_spacing": 1.5, "first_indent_chars": 2}},
    "caption": {{"font": "宋体", "size_pt": 10, "align": "center"}},
    "reference": {{"font": "宋体", "size_pt": 10.5, "hanging_indent_chars": 2}}
  }},
  "header_footer": {{"header_content": "XX大学本科毕业论文", "page_number_position": "bottom_center"}},
  "special_rules": ["章标题另起一页", "图表编号按章重置"]
}}

规范文档内容：
{spec_text}

请只返回 JSON，不要包含其他解释文字。"""

    response = llm_client.complete(system=system, prompt=prompt, temperature=0.1)
    return json.loads(response.text)


def merge_config(template: ParsedTemplate, spec_rules: dict) -> dict:
    """Merge python-docx extracted data with LLM-parsed spec rules. Spec rules take precedence."""
    result = template.to_dict()
    if "styles" in spec_rules:
        result["styles"] = spec_rules["styles"]
    if "header_footer" in spec_rules:
        result["header_footer"] = spec_rules["header_footer"]
    if "special_rules" in spec_rules:
        result["special_rules"] = spec_rules["special_rules"]
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage1_parser.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/stage1_parser.py tests/test_stage1_parser.py
git commit -m "feat: add stage1 template parser with docx reading and LLM spec parsing"
```

---

### Task 4: Stage 2 — Outline Expander

**Files:**
- Create: `src/stage2_expander.py`
- Create: `tests/test_stage2_expander.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage2_expander.py
import json
import pytest
from unittest.mock import MagicMock
from src.stage2_expander import expand_outline, WritingPlan, Chapter, Section

def test_expand_outline_generates_plan():
    mock_llm = MagicMock()
    mock_llm.complete.return_value.text = json.dumps({
        "chapters": [
            {
                "num": "1",
                "title": "绪论",
                "word_count": 2000,
                "sections": [
                    {
                        "num": "1.1",
                        "title": "研究背景与意义",
                        "word_count": 800,
                        "key_points": ["高校二手交易市场规模", "传统线下交易痛点"],
                        "search_queries": ["校园二手交易 现状"],
                        "citation_density": "high"
                    }
                ]
            }
        ]
    }, ensure_ascii=False)

    config = {"total_word_count": 15000, "expected_chapters": 7}
    plan = expand_outline(
        llm_client=mock_llm,
        title="基于Spring Boot的校园二手交易平台",
        rough_outline="1.绪论 2.相关技术 3.需求分析 4.系统设计 5.系统实现 6.测试 7.总结",
        config=config,
    )
    assert len(plan.chapters) == 1
    assert plan.chapters[0].title == "绪论"
    assert len(plan.chapters[0].sections) == 1

def test_writing_plan_to_dict():
    plan = WritingPlan(
        title="Test",
        total_word_count=10000,
        chapters=[
            Chapter(num="1", title="Intro", word_count=2000, sections=[
                Section(num="1.1", title="Background", word_count=800,
                        key_points=["Point 1"], search_queries=["Query 1"],
                        citation_density="high")
            ])
        ]
    )
    d = plan.to_dict()
    assert d["title"] == "Test"
    assert d["chapters"][0]["sections"][0]["key_points"] == ["Point 1"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage2_expander.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/stage2_expander.py**

```python
# src/stage2_expander.py
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class Section:
    num: str
    title: str
    word_count: int
    key_points: list = field(default_factory=list)
    search_queries: list = field(default_factory=list)
    citation_density: str = "medium"

    def to_dict(self) -> dict:
        return {
            "num": self.num,
            "title": self.title,
            "word_count": self.word_count,
            "key_points": self.key_points,
            "search_queries": self.search_queries,
            "citation_density": self.citation_density,
        }


@dataclass
class Chapter:
    num: str
    title: str
    word_count: int
    sections: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "num": self.num,
            "title": self.title,
            "word_count": self.word_count,
            "sections": [s.to_dict() for s in self.sections],
        }


@dataclass
class WritingPlan:
    title: str
    total_word_count: int
    chapters: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "total_word_count": self.total_word_count,
            "chapters": [c.to_dict() for c in self.chapters],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WritingPlan":
        chapters = []
        for ch_data in data.get("chapters", []):
            sections = [
                Section(
                    num=s["num"], title=s["title"], word_count=s["word_count"],
                    key_points=s.get("key_points", []),
                    search_queries=s.get("search_queries", []),
                    citation_density=s.get("citation_density", "medium"),
                )
                for s in ch_data.get("sections", [])
            ]
            chapters.append(Chapter(num=ch_data["num"], title=ch_data["title"],
                                    word_count=ch_data["word_count"], sections=sections))
        return cls(title=data["title"], total_word_count=data["total_word_count"],
                   chapters=chapters)


def expand_outline(llm_client, title: str, rough_outline: str, config: dict) -> WritingPlan:
    system = """你是学术论文写作规划专家。根据用户提供的论文标题和粗略大纲，生成详细的写作计划。
你必须为每个章标题下生成 2-4 个节标题，每个节标题附带 2-4 条写作要点和 1-3 个文献检索关键词。
引用密度标记为 high/medium/low。high 表示该节需要大量引用文献（≥5篇）。"""

    prompt = f"""请为以下本科毕业论文生成详细的写作计划。

论文标题：{title}
粗略大纲：{rough_outline}
预期总字数：{config.get('total_word_count', 15000)} 字

返回 JSON 格式：
{{
  "chapters": [
    {{
      "num": "1",
      "title": "章标题",
      "word_count": 2000,
      "sections": [
        {{
          "num": "1.1",
          "title": "节标题",
          "word_count": 800,
          "key_points": ["写作要点1", "写作要点2"],
          "search_queries": ["检索关键词1", "检索关键词2"],
          "citation_density": "high"
        }}
      ]
    }}
  ]
}}

请只返回 JSON，不要包含其他解释文字。"""

    response = llm_client.complete(system=system, prompt=prompt, temperature=0.4)
    data = json.loads(response.text)
    data["title"] = title
    data["total_word_count"] = config.get("total_word_count", 15000)
    return WritingPlan.from_dict(data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage2_expander.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/stage2_expander.py tests/test_stage2_expander.py
git commit -m "feat: add stage2 outline expander with LLM-powered writing plan generation"
```

---

### Task 5: Stage 3 — Literature Searcher

**Files:**
- Create: `src/stage3_searcher.py`
- Create: `tests/test_stage3_searcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage3_searcher.py
import json
import pytest
from unittest.mock import patch, MagicMock
from src.stage3_searcher import search_references, ReferenceList, Reference
from src.stage2_expander import WritingPlan, Chapter, Section

def test_search_references_returns_reference_list():
    mock_llm = MagicMock()
    mock_llm.complete.return_value.text = json.dumps({
        "references": [
            {
                "id": 1,
                "gb7714": "张三. 校园二手交易平台研究[J]. 计算机应用, 2023, 43(3): 45-52.",
                "metadata": {
                    "title": "校园二手交易平台研究",
                    "authors": ["张三"],
                    "year": 2023,
                    "journal": "计算机应用",
                    "volume": 43, "issue": 3, "pages": "45-52",
                    "type": "J", "doi": "10.xxx/xxx", "source": "semantic_scholar"
                },
                "keywords": ["校园二手"],
                "relevance_score": 0.9
            }
        ],
        "type_distribution": {"J": 1},
        "total": 1
    }, ensure_ascii=False)

    plan = WritingPlan(
        title="Test",
        total_word_count=5000,
        chapters=[
            Chapter(num="1", title="绪论", word_count=2000, sections=[
                Section(num="1.1", title="背景", word_count=800,
                        key_points=[], search_queries=["校园二手交易"],
                        citation_density="high")
            ])
        ]
    )

    query_map = {"校园二手交易": [{"title": "校园二手交易平台研究", "authors": ["张三"],
                                     "year": 2023, "journal": "计算机应用", "abstract": "...",
                                     "type": "J", "source": "semantic_scholar"}]}

    with patch("src.stage3_searcher._search_academic_db", return_value=query_map):
        refs = search_references(mock_llm, plan, {})
        assert refs.total == 1
        assert refs.references[0].gb7714 == "张三. 校园二手交易平台研究[J]. 计算机应用, 2023, 43(3): 45-52."


def test_reference_to_dict():
    ref = Reference(
        id=1,
        gb7714="作者. 标题[J]. 期刊, 2023.",
        metadata={"title": "标题", "authors": ["作者"], "year": 2023, "type": "J"},
        keywords=["kw1"],
        relevance_score=0.8,
    )
    d = ref.to_dict()
    assert d["id"] == 1
    assert d["metadata"]["type"] == "J"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage3_searcher.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/stage3_searcher.py**

```python
# src/stage3_searcher.py
from dataclasses import dataclass, field
from typing import Optional
import json
import time
import requests
from src.stage2_expander import WritingPlan


@dataclass
class Reference:
    id: int
    gb7714: str
    metadata: dict
    keywords: list = field(default_factory=list)
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "gb7714": self.gb7714,
            "metadata": self.metadata,
            "keywords": self.keywords,
            "relevance_score": self.relevance_score,
        }


@dataclass
class ReferenceList:
    references: list = field(default_factory=list)
    type_distribution: dict = field(default_factory=dict)
    total: int = 0

    def to_dict(self) -> dict:
        return {
            "references": [r.to_dict() for r in self.references],
            "type_distribution": self.type_distribution,
            "total": self.total,
        }


def _search_semantic_scholar(query: str, limit: int = 10) -> list:
    """Search Semantic Scholar API."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,journal,abstract,externalIds",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, json.JSONDecodeError):
        return []

    results = []
    for paper in data.get("data", []):
        authors = [a.get("name", "") for a in paper.get("authors", [])]
        results.append({
            "title": paper.get("title", ""),
            "authors": authors,
            "year": paper.get("year"),
            "journal": paper.get("journal", {}).get("name", "") if paper.get("journal") else "",
            "abstract": paper.get("abstract", "") or "",
            "doi": paper.get("externalIds", {}).get("DOI", ""),
            "type": "J",
            "source": "semantic_scholar",
        })
        time.sleep(0.1)
    return results


def _search_academic_db(queries: list, config: dict) -> dict:
    """Search academic databases. Falls back to Semantic Scholar for MVP."""
    all_results = {}
    for query in queries:
        all_results[query] = _search_semantic_scholar(query, limit=15)
        time.sleep(0.5)
    return all_results


def search_references(llm_client, plan: WritingPlan, config: dict) -> ReferenceList:
    all_queries = []
    for ch in plan.chapters:
        for sec in ch.sections:
            all_queries.extend(sec.search_queries)

    unique_queries = list(set(all_queries))
    raw_results = _search_academic_db(unique_queries, config)

    all_papers = []
    for papers in raw_results.values():
        all_papers.extend(papers)

    seen = set()
    deduped = []
    for p in all_papers:
        key = p["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    papers_json = json.dumps(deduped[:50], ensure_ascii=False)
    system = "你是学术文献管理专家。筛选相关文献并生成 GB/T 7714-2015 格式引用。"
    prompt = f"""从以下检索结果中筛选最相关的 15-25 篇文献，按相关度排序，并为每篇生成 GB/T 7714-2015 格式的引用。

注意：
- 确保包含不同类型的文献：[J]期刊论文、[D]学位论文、[C]会议论文、[M]著作、[EB/OL]网络资源
- GB/T 7714 顺序编码制格式示例：
  - 期刊：作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.
  - 学位论文：作者. 题名[D]. 保存地: 保存单位, 年.
- 如果检索结果不够 15 篇，就返回实际能用的篇数

检索结果：
{papers_json}

返回 JSON：
{{
  "references": [
    {{
      "id": 1,
      "gb7714": "完整的 GB/T 7714 引用",
      "metadata": {{"title": "...", "authors": ["..."], "year": 2023, "type": "J", "source": "semantic_scholar"}},
      "keywords": ["keyword"],
      "relevance_score": 0.9
    }}
  ],
  "type_distribution": {{"J": 0, "D": 0, "C": 0, "M": 0, "EB/OL": 0}},
  "total": 20
}}"""

    response = llm_client.complete(system=system, prompt=prompt, temperature=0.2, max_tokens=8000)
    data = json.loads(response.text)

    refs = [
        Reference(id=r["id"], gb7714=r["gb7714"], metadata=r["metadata"],
                  keywords=r.get("keywords", []), relevance_score=r.get("relevance_score", 0.0))
        for r in data.get("references", [])
    ]
    return ReferenceList(
        references=refs,
        type_distribution=data.get("type_distribution", {}),
        total=data.get("total", len(refs)),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage3_searcher.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/stage3_searcher.py tests/test_stage3_searcher.py
git commit -m "feat: add stage3 literature searcher with Semantic Scholar API and GB/T 7714 formatting"
```

---

### Task 6: Stage 4 — Content Writer

**Files:**
- Create: `src/stage4_writer.py`
- Create: `tests/test_stage4_writer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage4_writer.py
import json
import pytest
from unittest.mock import MagicMock
from src.stage4_writer import write_chapter, Draft, DraftChapter, DraftSection
from src.stage2_expander import WritingPlan, Chapter, Section
from src.stage3_searcher import ReferenceList, Reference

def test_write_single_chapter():
    mock_llm = MagicMock()
    mock_llm.complete.return_value.text = json.dumps({
        "sections": [
            {
                "num": "1.1",
                "title": "研究背景与意义",
                "content": "随着高校学生规模的不断扩大...[1][3][5]...",
                "cited_refs": [1, 3, 5],
                "word_count_actual": 820
            }
        ]
    }, ensure_ascii=False)

    chapter = Chapter(num="1", title="绪论", word_count=2000, sections=[
        Section(num="1.1", title="研究背景与意义", word_count=800,
                key_points=["高校二手交易市场规模", "传统线下交易痛点"],
                search_queries=[], citation_density="high")
    ])

    refs = ReferenceList(references=[
        Reference(id=1, gb7714="张三. 标题[J]. 期刊, 2023.", metadata={"type": "J"}, keywords=[]),
        Reference(id=3, gb7714="李四. 标题[J]. 期刊, 2022.", metadata={"type": "J"}, keywords=[]),
        Reference(id=5, gb7714="王五. 标题[J]. 期刊, 2024.", metadata={"type": "J"}, keywords=[]),
    ], total=3)

    prev_summary = ""
    style_config = {"body": {"font": "宋体", "size_pt": 12, "line_spacing": 1.5}}

    draft_chapter = write_chapter(mock_llm, chapter, refs, prev_summary, style_config, {})

    assert draft_chapter.num == "1"
    assert draft_chapter.title == "绪论"
    assert len(draft_chapter.sections) == 1
    assert draft_chapter.sections[0].cited_refs == [1, 3, 5]
    assert "[1]" in draft_chapter.sections[0].content


def test_draft_collect_uncited_refs():
    draft = Draft(chapters=[
        DraftChapter(num="1", title="绪论", sections=[
            DraftSection(num="1.1", title="背景", content="test [1]", cited_refs=[1], word_count_actual=100),
            DraftSection(num="1.2", title="现状", content="test [2]", cited_refs=[2], word_count_actual=100),
        ])
    ])
    total_ref_ids = {1, 2, 3, 4, 5}
    uncited = []
    for ch in draft.chapters:
        for sec in ch.sections:
            uncited.extend(set(sec.cited_refs))
    uncited_refs = list(total_ref_ids - set(uncited))
    assert 3 in uncited_refs
    assert 4 in uncited_refs
    assert 5 in uncited_refs
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage4_writer.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/stage4_writer.py**

```python
# src/stage4_writer.py
from dataclasses import dataclass, field
from typing import Optional
import json
from src.stage2_expander import WritingPlan, Chapter
from src.stage3_searcher import ReferenceList


@dataclass
class DraftSection:
    num: str
    title: str
    content: str
    cited_refs: list = field(default_factory=list)
    word_count_actual: int = 0

    def to_dict(self) -> dict:
        return {
            "num": self.num,
            "title": self.title,
            "content": self.content,
            "cited_refs": self.cited_refs,
            "word_count_actual": self.word_count_actual,
        }


@dataclass
class DraftChapter:
    num: str
    title: str
    sections: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "num": self.num,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
        }


@dataclass
class Draft:
    chapters: list = field(default_factory=list)
    total_word_count: int = 0
    uncited_refs: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "chapters": [c.to_dict() for c in self.chapters],
            "total_word_count": self.total_word_count,
            "uncited_refs": self.uncited_refs,
        }


TEMPERATURE_MAP = {
    "绪论": 0.5, "引言": 0.5, "前言": 0.5,
    "技术": 0.3, "背景": 0.3, "概述": 0.3,
    "需求": 0.6, "分析": 0.6, "设计": 0.5,
    "实现": 0.5, "开发": 0.5, "测试": 0.4,
    "总结": 0.6, "展望": 0.6, "结论": 0.6,
}


def _pick_temperature(chapter_title: str) -> float:
    for keyword, temp in TEMPERATURE_MAP.items():
        if keyword in chapter_title:
            return temp
    return 0.5


def _build_reference_context(refs: ReferenceList, chapter: Chapter) -> str:
    """Build a reference context block containing only references relevant to this chapter."""
    if not refs.references:
        return "（无可用文献）"
    lines = ["可用文献："]
    for r in refs.references:
        lines.append(f"[{r.id}] {r.gb7714}")
    return "\n".join(lines)


def write_chapter(
    llm_client,
    chapter: Chapter,
    refs: ReferenceList,
    prev_summary: str,
    style_config: dict,
    writing_config: dict,
) -> DraftChapter:
    temperature = _pick_temperature(chapter.title)
    ref_context = _build_reference_context(refs, chapter)

    chapter_json = json.dumps(chapter.to_dict(), ensure_ascii=False)

    system = """你是学术论文写手。根据章节大纲生成论文正文。要求：
1. 使用学术性、客观的语言
2. 使用编号制引用 [1][2-5] 格式
3. 中文行文流畅，段落逻辑清晰
4. 不编造引用——只使用提供的文献列表中的文献
5. 每节达到指定字数要求"""

    prompt = f"""请为以下章节撰写正文。

论文前文摘要：{prev_summary or "（本论文第一章）"}

本章大纲：
{chapter_json}

{ref_context}

请为每个节标题生成对应的正文内容。在正文中恰当插入文献引用标记 [文献ID]。
返回 JSON 格式：
{{
  "sections": [
    {{
      "num": "1.1",
      "title": "节标题",
      "content": "正文内容...[1][3]...",
      "cited_refs": [1, 3],
      "word_count_actual": 800
    }}
  ]
}}"""

    response = llm_client.complete(
        system=system,
        prompt=prompt,
        temperature=temperature,
        max_tokens=4096,
    )
    data = json.loads(response.text)

    sections = [
        DraftSection(
            num=s["num"], title=s["title"], content=s["content"],
            cited_refs=s.get("cited_refs", []),
            word_count_actual=s.get("word_count_actual", 0),
        )
        for s in data.get("sections", [])
    ]
    return DraftChapter(num=chapter.num, title=chapter.title, sections=sections)


def _summarize_chapter(llm_client, chapter: DraftChapter) -> str:
    """Generate a 200-300 word summary of a written chapter."""
    content = "\n".join(s.content for s in chapter.sections)
    prompt = f"请用 200-300 字总结以下论文章节的核心内容：\n\n{content[:3000]}"
    response = llm_client.complete(
        system="你是学术论文编辑。简洁准确地总结章节内容。",
        prompt=prompt,
        temperature=0.2,
        max_tokens=500,
    )
    return response.text


def generate_full_draft(
    llm_client,
    plan: WritingPlan,
    refs: ReferenceList,
    style_config: dict,
    writing_config: dict,
) -> Draft:
    draft_chapters = []
    prev_summary = ""

    for chapter in plan.chapters:
        draft_ch = write_chapter(llm_client, chapter, refs, prev_summary, style_config, writing_config)
        draft_chapters.append(draft_ch)
        prev_summary = _summarize_chapter(llm_client, draft_ch)

    all_cited = set()
    for ch in draft_chapters:
        for sec in ch.sections:
            all_cited.update(sec.cited_refs)

    all_ref_ids = {r.id for r in refs.references}
    uncited = sorted(list(all_ref_ids - all_cited))

    total_words = sum(
        s.word_count_actual
        for ch in draft_chapters
        for s in ch.sections
    )

    return Draft(chapters=draft_chapters, total_word_count=total_words, uncited_refs=uncited)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage4_writer.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/stage4_writer.py tests/test_stage4_writer.py
git commit -m "feat: add stage4 content writer with chapter-by-chapter LLM generation"
```

---

### Task 7: Word COM Utilities

**Files:**
- Create: `src/word_com.py`
- Create: `tests/test_word_com.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_word_com.py
import pytest
from unittest.mock import patch, MagicMock
from src.word_com import WordApp, create_word_app

def test_word_app_context_manager():
    with patch("src.word_com.client.Dispatch") as mock_dispatch:
        mock_word = MagicMock()
        mock_dispatch.return_value = mock_word

        with WordApp(visible=False) as app:
            assert app.app is not None

        mock_word.Quit.assert_called_once()


def test_apply_style():
    with patch("src.word_com.client.Dispatch") as mock_dispatch:
        mock_word = MagicMock()
        mock_dispatch.return_value = mock_word

        app = WordApp(visible=False)
        app.app = mock_word

        mock_selection = MagicMock()
        mock_word.Selection = mock_selection
        mock_style = MagicMock()
        mock_word.ActiveDocument.Styles.return_value = mock_style

        app.apply_style("heading_1")

        mock_selection.Style.assert_called_once()


def test_insert_page_break():
    with patch("src.word_com.client.Dispatch") as mock_dispatch:
        mock_word = MagicMock()
        mock_dispatch.return_value = mock_word

        app = WordApp(visible=False)
        app.app = mock_word

        mock_selection = MagicMock()
        mock_word.Selection = mock_selection

        app.insert_page_break()

        mock_selection.InsertBreak.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_word_com.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/word_com.py**

```python
# src/word_com.py
from contextlib import contextmanager
import win32com.client as client


class WordApp:
    """Wrapper around Word COM application. Mimics professional Word user operations."""

    def __init__(self, visible: bool = False):
        self.visible = visible
        self.app = None

    def __enter__(self):
        self.app = client.Dispatch("Word.Application")
        self.app.Visible = self.visible
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.app:
            try:
                self.app.Quit()
            except Exception:
                pass
        return False

    def open_document(self, path: str):
        self.app.Documents.Open(path)
        return self.app.ActiveDocument

    def save_as(self, path: str):
        self.app.ActiveDocument.SaveAs(path)

    def close_document(self):
        self.app.ActiveDocument.Close()

    @property
    def selection(self):
        return self.app.Selection

    @property
    def active_document(self):
        return self.app.ActiveDocument

    def apply_style(self, style_name: str):
        """Apply a named Word style to the current selection."""
        doc = self.active_document
        self.selection.Style = doc.Styles(style_name)

    def type_text(self, text: str):
        self.selection.TypeText(text)

    def type_paragraph(self):
        self.selection.TypeParagraph()

    def insert_page_break(self):
        self.selection.InsertBreak(Type=7)  # wdPageBreak

    def insert_section_break_next_page(self):
        self.selection.InsertBreak(Type=2)  # wdSectionBreakNextPage

    def make_superscript(self, start: int, end: int):
        """Apply superscript formatting to a range of characters."""
        rng = self.active_document.Range(start, end)
        rng.Font.Superscript = True

    def insert_toc(self):
        """Insert an automatic Table of Contents at current position."""
        doc = self.active_document
        rng = self.selection.Range
        doc.TablesOfContents.Add(Range=rng, UseHeadingStyles=True,
                                  LowerHeadingLevel=3, UpperHeadingLevel=1)

    def update_all_fields(self):
        """Update all fields (TOC, page numbers, cross-references)."""
        self.active_document.Fields.Update()

    def set_page_header(self, text: str, section_index: int = 1):
        """Set header text for a specific section."""
        doc = self.active_document
        section = doc.Sections(section_index)
        header = section.Headers(1)  # wdHeaderFooterPrimary
        header.Range.Text = text

    def set_page_footer_page_numbers(self, section_index: int = 1, start_at: int = 1):
        """Add page numbers to footer of a section."""
        doc = self.active_document
        section = doc.Sections(section_index)
        footer = section.Footers(1)
        footer.PageNumbers.Add()
        footer.PageNumbers.StartingNumber = start_at
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_word_com.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/word_com.py tests/test_word_com.py
git commit -m "feat: add Word COM utilities for style, page break, TOC, and header/footer operations"
```

---

### Task 8: Stage 5 — Word Composer

**Files:**
- Create: `src/stage5_composer.py`
- Create: `tests/test_stage5_composer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage5_composer.py
import pytest
from unittest.mock import patch, MagicMock
from src.stage5_composer import compose_thesis
from src.stage4_writer import Draft, DraftChapter, DraftSection
from src.stage3_searcher import ReferenceList, Reference

def test_compose_thesis_calls_word_operations():
    draft = Draft(chapters=[
        DraftChapter(num="1", title="绪论", sections=[
            DraftSection(num="1.1", title="研究背景", content="正文 [1][3]", cited_refs=[1, 3], word_count_actual=800),
        ])
    ], total_word_count=800, uncited_refs=[])

    refs = ReferenceList(references=[
        Reference(id=1, gb7714="张三. 测试引用[J]. 测试刊, 2023.", metadata={"type": "J"}, keywords=[]),
        Reference(id=3, gb7714="李四. 另一引用[J]. 测试刊, 2022.", metadata={"type": "J"}, keywords=[]),
    ], total=2)

    template_config = {
        "page": {"size": "A4", "margin_top_cm": 2.5},
        "styles": {
            "heading_1": {"font": "黑体", "size_pt": 16, "bold": True},
            "body": {"font": "宋体", "size_pt": 12, "line_spacing": 1.5},
        },
        "structure": {"chapter_sequence": ["cover", "chapters", "references"]},
        "header_footer": {"header_content": "XX大学本科毕业论文"},
    }
    meta = {"title": "测试论文", "author": "张三", "student_id": "2024001",
            "advisor": "李教授", "date": "2026-05-25"}

    with patch("src.stage5_composer.WordApp") as mock_word_cls:
        mock_word = MagicMock()
        mock_word_cls.return_value.__enter__.return_value = mock_word
        mock_word.active_document.Styles.return_value = MagicMock()

        compose_thesis(mock_word, draft, refs, template_config, meta, "output.docx")

        # Should have typed the chapter title
        mock_word.type_text.assert_any_call("绪论")
        # Should have applied heading_1 style
        mock_word.apply_style.assert_any_call("heading_1")
        # Should have saved
        mock_word.save_as.assert_called_once_with("output.docx")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage5_composer.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/stage5_composer.py**

```python
# src/stage5_composer.py
import re
from src.word_com import WordApp
from src.stage4_writer import Draft
from src.stage3_searcher import ReferenceList


def _write_cover(app: WordApp, meta: dict, style_config: dict):
    """Fill cover page: title, author, student_id, advisor, date."""
    app.type_text(meta.get("title", ""))
    app.type_paragraph()
    app.type_text(f"作者：{meta.get('author', '')}")
    app.type_paragraph()
    app.type_text(f"学号：{meta.get('student_id', '')}")
    app.type_paragraph()
    app.type_text(f"指导教师：{meta.get('advisor', '')}")
    app.type_paragraph()
    app.type_text(f"日期：{meta.get('date', '')}")
    app.type_paragraph()


def _write_chapter_body(app: WordApp, chapter, refs: ReferenceList, style_config: dict):
    """Write a single chapter: heading + body paragraphs with proper styles."""
    # Chapter title
    app.type_text(chapter.title)
    app.type_paragraph()
    if "heading_1" in style_config.get("styles", {}):
        app.apply_style("heading_1")

    for section in chapter.sections:
        # Section title
        app.type_text(f"{section.num} {section.title}")
        app.type_paragraph()
        if "heading_2" in style_config.get("styles", {}):
            app.apply_style("heading_2")

        # Section body
        content = section.content
        paragraphs = content.split("\n")
        for para_text in paragraphs:
            if para_text.strip():
                app.type_text(para_text.strip())
                app.type_paragraph()
                if "body" in style_config.get("styles", {}):
                    app.apply_style("body")


def _write_references(app: WordApp, refs: ReferenceList, style_config: dict):
    """Write the reference list in GB/T 7714 format."""
    app.type_text("参考文献")
    app.type_paragraph()
    app.apply_style("heading_1")

    for ref in refs.references:
        app.type_text(f"[{ref.id}] {ref.gb7714}")
        app.type_paragraph()
        if "reference" in style_config.get("styles", {}):
            app.apply_style("reference")


def compose_thesis(
    app: WordApp,
    draft: Draft,
    refs: ReferenceList,
    template_config: dict,
    meta: dict,
    output_path: str,
):
    """Orchestrate all Word COM operations to assemble the final .docx."""
    style_config = template_config
    chapter_seq = template_config.get("structure", {}).get("chapter_sequence", [])

    for element in chapter_seq:
        if element == "cover":
            _write_cover(app, meta, style_config)
            app.insert_page_break()
        elif element == "declaration":
            decl_text = template_config.get("declaration_text", "")
            app.type_text(decl_text)
            app.type_paragraph()
            app.insert_page_break()
        elif element == "abstract_cn":
            app.type_text("摘  要")
            app.type_paragraph()
            app.apply_style("heading_1")
            # Abstract would be generated separately; for MVP use placeholder
            app.type_text(meta.get("abstract_cn", "[中文摘要待生成]"))
            app.type_paragraph()
            app.type_text(f"关键词：{meta.get('keywords_cn', '')}")
            app.type_paragraph()
            app.insert_page_break()
        elif element == "abstract_en":
            app.type_text("Abstract")
            app.type_paragraph()
            app.apply_style("heading_1")
            app.type_text(meta.get("abstract_en", "[English abstract placeholder]"))
            app.type_paragraph()
            app.type_text(f"Keywords: {meta.get('keywords_en', '')}")
            app.type_paragraph()
            app.insert_page_break()
        elif element == "toc":
            app.type_text("目  录")
            app.type_paragraph()
            app.insert_toc()
            app.insert_page_break()
        elif element == "chapters":
            for chapter in draft.chapters:
                _write_chapter_body(app, chapter, refs, style_config)
                app.insert_page_break()
        elif element == "references":
            _write_references(app, refs, style_config)
        elif element == "acknowledgement":
            app.type_text("致  谢")
            app.type_paragraph()
            app.apply_style("heading_1")
            app.type_text(meta.get("acknowledgement", "[致谢待填写]"))
            app.type_paragraph()

    header_text = template_config.get("header_footer", {}).get("header_content", "")
    if header_text:
        app.set_page_header(header_text)

    app.update_all_fields()
    app.save_as(output_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage5_composer.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add src/stage5_composer.py tests/test_stage5_composer.py
git commit -m "feat: add stage5 Word composer with full document assembly pipeline"
```

---

### Task 9: Stage 6 — Format Verifier

**Files:**
- Create: `src/stage6_verifier.py`
- Create: `tests/test_stage6_verifier.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage6_verifier.py
import pytest
from unittest.mock import patch, MagicMock
from src.stage6_verifier import verify_format, VerificationReport, Issue

def test_verify_format_returns_report():
    template_config = {
        "page": {"size": "A4", "margin_top_cm": 2.5, "margin_bottom_cm": 2.5,
                 "margin_left_cm": 3.0, "margin_right_cm": 2.5},
        "styles": {
            "heading_1": {"font": "黑体", "size_pt": 16, "bold": True},
            "body": {"font": "宋体", "size_pt": 12, "line_spacing": 1.5},
        },
    }

    report = verify_format("fake_output.docx", template_config)
    assert isinstance(report, VerificationReport)
    assert report.total_checks > 0


def test_issue_severity_ordering():
    issues = [
        Issue(severity="warning", dimension="引用", detail="test1", location="", auto_fixable=False),
        Issue(severity="error", dimension="字体", detail="test2", location="", auto_fixable=True),
        Issue(severity="info", dimension="结构", detail="test3", location="", auto_fixable=False),
    ]
    severity_order = {"error": 0, "warning": 1, "info": 2}
    sorted_issues = sorted(issues, key=lambda i: severity_order.get(i.severity, 99))
    assert sorted_issues[0].severity == "error"
    assert sorted_issues[1].severity == "warning"
    assert sorted_issues[2].severity == "info"


def test_verification_report_pass():
    report = VerificationReport(total_checks=10, passed=10, failed=0, issues=[])
    assert report.pass_ is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage6_verifier.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/stage6_verifier.py**

```python
# src/stage6_verifier.py
from dataclasses import dataclass, field


@dataclass
class Issue:
    severity: str  # "error", "warning", "info"
    dimension: str
    detail: str
    location: str = ""
    auto_fixable: bool = False

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "dimension": self.dimension,
            "detail": self.detail,
            "location": self.location,
            "auto_fixable": self.auto_fixable,
        }


@dataclass
class VerificationReport:
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    issues: list = field(default_factory=list)
    auto_fixed_count: int = 0

    @property
    def pass_(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict:
        return {
            "pass": self.pass_,
            "total_checks": self.total_checks,
            "passed": self.passed,
            "failed": self.failed,
            "issues": [i.to_dict() for i in self.issues],
            "auto_fixed_count": self.auto_fixed_count,
        }


def _check_page_settings(doc_path: str, config: dict) -> list:
    """Verify page margins and paper size against config."""
    issues = []
    try:
        from docx import Document
        doc = Document(doc_path)
        section = doc.sections[0]

        page_cfg = config.get("page", {})
        expected_top = page_cfg.get("margin_top_cm", 2.5)
        expected_bottom = page_cfg.get("margin_bottom_cm", 2.5)
        expected_left = page_cfg.get("margin_left_cm", 3.0)
        expected_right = page_cfg.get("margin_right_cm", 2.5)

        actual_top = round(section.top_margin.cm, 1)
        if abs(actual_top - expected_top) > 0.2:
            issues.append(Issue(
                severity="error", dimension="页面级",
                detail=f"上边距为 {actual_top}cm，要求 {expected_top}cm",
                location="全文", auto_fixable=True,
            ))

        actual_left = round(section.left_margin.cm, 1)
        if abs(actual_left - expected_left) > 0.2:
            issues.append(Issue(
                severity="error", dimension="页面级",
                detail=f"左边距为 {actual_left}cm，要求 {expected_left}cm",
                location="全文", auto_fixable=True,
            ))
    except Exception as e:
        issues.append(Issue(
            severity="error", dimension="页面级",
            detail=f"无法读取页面设置：{e}", auto_fixable=False,
        ))
    return issues


def _check_structure(doc_path: str, config: dict) -> list:
    """Verify document structural completeness."""
    issues = []
    try:
        from docx import Document
        doc = Document(doc_path)

        # Check for required elements by looking at heading styles
        headings = [p for p in doc.paragraphs if p.style.name.startswith("Heading")]
        heading_texts = [h.text.strip() for h in headings]

        required_elements = ["绪论", "参考文献", "致谢"]
        for elem in required_elements:
            found = any(elem in h for h in heading_texts)
            if not found:
                issues.append(Issue(
                    severity="warning", dimension="结构完整性",
                    detail=f"未发现'{elem}'部分",
                    auto_fixable=False,
                ))
    except Exception as e:
        issues.append(Issue(
            severity="error", dimension="结构完整性",
            detail=f"无法读取文档结构：{e}", auto_fixable=False,
        ))
    return issues


def _check_citation_consistency(doc_path: str, config: dict) -> list:
    """Verify citation numbering is continuous and references exist."""
    issues = []
    try:
        from docx import Document
        import re
        doc = Document(doc_path)
        full_text = "\n".join(p.text for p in doc.paragraphs)

        # Find all citation markers like [1], [3-5], [1,3,7]
        citation_pattern = re.findall(r'\[([0-9,\-\s]+)\]', full_text)
        cited_numbers = set()
        for match in citation_pattern:
            for part in re.findall(r'\d+', match):
                cited_numbers.add(int(part))

        if cited_numbers:
            max_cited = max(cited_numbers)
            expected = set(range(1, max_cited + 1))
            missing = sorted(expected - cited_numbers)
            if missing:
                issues.append(Issue(
                    severity="warning", dimension="引用一致性",
                    detail=f"引用编号不连续，缺少：{missing}",
                    auto_fixable=False,
                ))

            jumps = []
            prev = 0
            for n in sorted(cited_numbers):
                if n - prev > 5:
                    jumps.append(f"{prev}→{n}")
                prev = n
            if jumps:
                issues.append(Issue(
                    severity="info", dimension="引用一致性",
                    detail=f"引用编号跳号：{', '.join(jumps)}",
                    auto_fixable=False,
                ))
    except Exception as e:
        issues.append(Issue(
            severity="error", dimension="引用一致性",
            detail=f"无法检查引用：{e}", auto_fixable=False,
        ))
    return issues


def verify_format(doc_path: str, template_config: dict) -> VerificationReport:
    issues = []
    issues.extend(_check_page_settings(doc_path, template_config))
    issues.extend(_check_structure(doc_path, template_config))
    issues.extend(_check_citation_consistency(doc_path, template_config))

    total = len(issues) or 1  # avoid zero
    errors_and_warnings = [i for i in issues if i.severity in ("error", "warning")]
    passed = max(0, total - len(errors_and_warnings))
    failed = len(errors_and_warnings)

    return VerificationReport(
        total_checks=total,
        passed=passed,
        failed=failed,
        issues=issues,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_stage6_verifier.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/stage6_verifier.py tests/test_stage6_verifier.py
git commit -m "feat: add stage6 format verifier with page, structure, and citation checks"
```

---

### Task 10: Pipeline Orchestrator

**Files:**
- Create: `src/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py
import json
import pytest
from unittest.mock import patch, MagicMock
from src.pipeline import Pipeline, PipelineContext, StepResult

def test_pipeline_context_save_load(tmp_path):
    ctx = PipelineContext(work_dir=str(tmp_path))
    ctx.set_stage_output(1, {"key": "value"})
    assert ctx.get_stage_output(1) == {"key": "value"}

    # Test that stage returns None for un-run stage
    assert ctx.get_stage_output(2) is None


def test_pipeline_runs_stages_in_order():
    pipe = Pipeline(mode="auto", work_dir="/tmp/test_pipe")
    executed = []

    @pipe.stage(1)
    def stage_one(ctx):
        executed.append(1)
        return StepResult(output={"result": "one"})

    @pipe.stage(2)
    def stage_two(ctx):
        executed.append(2)
        assert ctx.get_stage_output(1) == {"result": "one"}
        return StepResult(output={"result": "two"})

    results = pipe.run(max_stage=2)
    assert executed == [1, 2]
    assert results[1].output == {"result": "one"}
    assert results[2].output == {"result": "two"}


def test_pipeline_resume_skips_completed():
    pipe = Pipeline(mode="resume", work_dir="/tmp/test_pipe")
    executed = []

    @pipe.stage(1)
    def stage_one(ctx):
        executed.append(1)
        return StepResult(output={"done": True})

    @pipe.stage(2)
    def stage_two(ctx):
        executed.append(2)
        return StepResult(output={"done": True})

    # Manually mark stage 1 as already completed
    pipe._completed_stages = {1}

    results = pipe.run(max_stage=2)
    assert executed == [2]  # stage 1 skipped
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_pipeline.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/pipeline.py**

```python
# src/pipeline.py
from dataclasses import dataclass, field
from typing import Optional, Callable
import json
import os


@dataclass
class StepResult:
    output: dict = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class PipelineContext:
    """Holds working state for the pipeline: paths, config, and stage outputs."""

    def __init__(self, work_dir: str):
        self.work_dir = work_dir
        os.makedirs(work_dir, exist_ok=True)
        self._outputs: dict = {}

    def stage_path(self, stage_num: int) -> str:
        return os.path.join(self.work_dir, f"{stage_num:02d}-stage-output.json")

    def get_stage_output(self, stage_num: int) -> Optional[dict]:
        if stage_num in self._outputs:
            return self._outputs[stage_num]
        path = self.stage_path(stage_num)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._outputs[stage_num] = data
            return data
        return None

    def set_stage_output(self, stage_num: int, data: dict):
        self._outputs[stage_num] = data
        with open(self.stage_path(stage_num), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class Pipeline:
    def __init__(self, mode: str = "auto", work_dir: str = "./output"):
        self.mode = mode
        self.work_dir = work_dir
        self._stages: dict = {}
        self._completed_stages: set = set()

    def stage(self, num: int):
        """Decorator to register a pipeline stage."""
        def decorator(fn: Callable):
            self._stages[num] = fn
            return fn
        return decorator

    def _confirm(self, stage_num: int, result: StepResult) -> bool:
        if self.mode == "auto":
            return True
        print(f"\nStage {stage_num} complete. Output: {json.dumps(result.output, ensure_ascii=False)[:200]}")
        if result.error:
            print(f"Error: {result.error}")
        resp = input("Continue to next stage? [Y/n/q]: ").strip().lower()
        if resp == "q":
            return False
        return True

    def run(self, max_stage: int = 6) -> dict:
        """Run all stages from 1 to max_stage. Returns dict of stage_num -> StepResult."""
        results = {}
        ctx = PipelineContext(work_dir=self.work_dir)

        for num in range(1, max_stage + 1):
            if num in self._completed_stages:
                print(f"Stage {num}: already completed, skipping.")
                continue

            fn = self._stages.get(num)
            if not fn:
                print(f"Stage {num}: no handler registered, skipping.")
                continue

            print(f"\n{'='*40}\nRunning Stage {num}: {fn.__name__}\n{'='*40}")
            try:
                result = fn(ctx)
            except Exception as e:
                result = StepResult(error=str(e))

            results[num] = result
            ctx.set_stage_output(num, result.output)

            if not result.success:
                print(f"Stage {num} FAILED: {result.error}")
                if self.mode != "auto":
                    resp = input("Continue anyway? [y/N]: ").strip().lower()
                    if resp != "y":
                        break
                else:
                    break

            if not self._confirm(num, result):
                break

        return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/test_pipeline.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat: add pipeline orchestrator with auto/interactive/resume modes"
```

---

### Task 11: Main Entry Point — Wire Everything Together

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: Write src/main.py**

```python
# src/main.py
"""Academic thesis automation — main entry point.

Usage:
    python -m src.main --title "论文标题" --outline "1.绪论 2.相关技术 3.需求分析 ..."
    python -m src.main --config config.yaml
"""

import argparse
import json
import os
import sys

from src.config import load_config
from src.llm_client import create_llm_client
from src.stage1_parser import parse_template, parse_format_spec, merge_config
from src.stage2_expander import expand_outline
from src.stage3_searcher import search_references
from src.stage4_writer import generate_full_draft
from src.stage5_composer import compose_thesis
from src.stage6_verifier import verify_format
from src.word_com import WordApp
from src.pipeline import Pipeline, PipelineContext, StepResult


def build_pipeline(config_path: str, title: str, outline: str) -> Pipeline:
    config = load_config(config_path)
    llm_client = create_llm_client(config)
    work_dir = os.path.join(config.output_dir, _slugify(title))
    pipe = Pipeline(mode=config.mode, work_dir=work_dir)

    @pipe.stage(1)
    def stage1_parse_template(ctx: PipelineContext) -> StepResult:
        print("Parsing template...")
        template = parse_template(config.template_path)
        spec_rules = parse_format_spec(config.spec_path, llm_client)
        merged = merge_config(template, spec_rules)
        print(f"  Found {len(merged.get('styles', {}))} defined styles")
        return StepResult(output=merged)

    @pipe.stage(2)
    def stage2_expand_outline(ctx: PipelineContext) -> StepResult:
        print("Expanding outline...")
        plan_config = {"total_word_count": 15000}
        plan = expand_outline(llm_client, title, outline, plan_config)
        plan_dict = plan.to_dict()
        print(f"  Generated {len(plan.chapters)} chapters")
        return StepResult(output=plan_dict)

    @pipe.stage(3)
    def stage3_search_references(ctx: PipelineContext) -> StepResult:
        print("Searching references...")
        plan_data = ctx.get_stage_output(2)
        from src.stage2_expander import WritingPlan
        plan = WritingPlan.from_dict(plan_data)
        refs = search_references(llm_client, plan, {})
        refs_dict = refs.to_dict()
        print(f"  Found {refs.total} references")
        return StepResult(output=refs_dict)

    @pipe.stage(4)
    def stage4_write_content(ctx: PipelineContext) -> StepResult:
        print("Writing content...")
        plan_data = ctx.get_stage_output(2)
        refs_data = ctx.get_stage_output(3)
        template_config = ctx.get_stage_output(1) or {}

        from src.stage2_expander import WritingPlan
        from src.stage3_searcher import ReferenceList, Reference

        plan = WritingPlan.from_dict(plan_data)
        refs = ReferenceList(
            references=[
                Reference(id=r["id"], gb7714=r["gb7714"], metadata=r["metadata"],
                          keywords=r.get("keywords", []), relevance_score=r.get("relevance_score", 0))
                for r in refs_data.get("references", [])
            ],
            type_distribution=refs_data.get("type_distribution", {}),
            total=refs_data.get("total", 0),
        )

        draft = generate_full_draft(llm_client, plan, refs, template_config, {})
        draft_dict = draft.to_dict()
        print(f"  Written {draft.total_word_count} words across {len(draft.chapters)} chapters")
        print(f"  Uncited references: {draft.uncited_refs}")
        return StepResult(output=draft_dict)

    @pipe.stage(5)
    def stage5_compose_document(ctx: PipelineContext) -> StepResult:
        print("Composing Word document...")
        template_config = ctx.get_stage_output(1) or {}
        draft_data = ctx.get_stage_output(4)
        refs_data = ctx.get_stage_output(3)

        from src.stage4_writer import Draft, DraftChapter, DraftSection
        from src.stage3_searcher import ReferenceList, Reference

        draft = Draft(
            chapters=[
                DraftChapter(
                    num=c["num"], title=c["title"],
                    sections=[
                        DraftSection(num=s["num"], title=s["title"], content=s["content"],
                                     cited_refs=s.get("cited_refs", []),
                                     word_count_actual=s.get("word_count_actual", 0))
                        for s in c.get("sections", [])
                    ]
                )
                for c in draft_data.get("chapters", [])
            ],
            total_word_count=draft_data.get("total_word_count", 0),
            uncited_refs=draft_data.get("uncited_refs", []),
        )
        refs = ReferenceList(
            references=[
                Reference(id=r["id"], gb7714=r["gb7714"], metadata=r["metadata"],
                          keywords=r.get("keywords", []), relevance_score=r.get("relevance_score", 0))
                for r in refs_data.get("references", [])
            ],
            total=refs_data.get("total", 0),
        )

        meta = {
            "title": title, "author": "", "student_id": "", "advisor": "", "date": "",
        }
        template_path = config.template_path
        output_path = os.path.join(ctx.work_dir, "05-thesis.docx")

        with WordApp(visible=False) as app:
            app.open_document(template_path)
            compose_thesis(app, draft, refs, template_config, meta, output_path)
            app.close_document()

        print(f"  Saved to {output_path}")
        return StepResult(output={"output_path": output_path})

    @pipe.stage(6)
    def stage6_verify_format(ctx: PipelineContext) -> StepResult:
        print("Verifying format...")
        template_config = ctx.get_stage_output(1) or {}
        output_data = ctx.get_stage_output(5)
        doc_path = output_data.get("output_path", "")
        if not os.path.exists(doc_path):
            return StepResult(error=f"Document not found: {doc_path}")

        report = verify_format(doc_path, template_config)
        report_dict = report.to_dict()
        if report.pass_:
            print("  ALL CHECKS PASSED")
        else:
            print(f"  {report.failed}/{report.total_checks} checks FAILED")
            for issue in report.issues:
                print(f"    [{issue.severity.upper()}] {issue.detail}")
        return StepResult(output=report_dict)

    return pipe


def _slugify(title: str) -> str:
    import re
    slug = re.sub(r'[^\w\s-]', '', title)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-') or "thesis"


def main():
    parser = argparse.ArgumentParser(description="学术论文自动化写作工具")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--title", required=True, help="论文标题")
    parser.add_argument("--outline", required=True, help="粗略大纲（章标题列表）")
    args = parser.parse_args()

    pipe = build_pipeline(args.config, args.title, args.outline)
    results = pipe.run(max_stage=6)

    all_ok = all(r.success for r in results.values())
    if not all_ok:
        print("\nPipeline completed with errors. Check output above.")
        sys.exit(1)
    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run a dry-run test to verify wiring**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/ -v --ignore=tests/test_main.py 2>&1 | head -50`
Expected: All existing tests still pass

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: add main entry point wiring all 6 stages together"
```

---

### Task 12: Final Integration Verification

- [ ] **Step 1: Run all tests**

Run: `cd C:/Users/Surtr/thesis-automation && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify project structure**

Run: `cd C:/Users/Surtr/thesis-automation && ls -la src/ tests/`
Expected: All files present as defined in the spec

- [ ] **Step 3: Verify imports are consistent**

Run: `cd C:/Users/Surtr/thesis-automation && python -c "from src.main import build_pipeline; print('All imports OK')"`
Expected: "All imports OK"

- [ ] **Step 4: Final commit**

```bash
cd C:/Users/Surtr/thesis-automation
git add -A
git commit -m "chore: final integration verification, all tests passing"
```
