# src/stage4_writer.py
from dataclasses import dataclass, field
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
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM response for chapter '{chapter.title}': {e}\n"
            f"Response text: {response.text[:500]}"
        )

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
