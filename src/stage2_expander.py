from dataclasses import dataclass, field
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
            chapters.append(
                Chapter(
                    num=ch_data["num"], title=ch_data["title"],
                    word_count=ch_data["word_count"], sections=sections,
                )
            )
        return cls(
            title=data["title"],
            total_word_count=data["total_word_count"],
            chapters=chapters,
        )


def expand_outline(
    llm_client, title: str, rough_outline: str, config: dict
) -> WritingPlan:
    """Expand a rough outline into a detailed writing plan using an LLM.

    Args:
        llm_client: Client with a ``complete(system, prompt, temperature)`` method.
        title: Thesis title.
        rough_outline: Space-separated chapter headings (e.g. "1.绪论 2.相关技术").
        config: Dict containing ``total_word_count`` and optionally ``expected_chapters``.

    Returns:
        A fully populated WritingPlan with chapters and sections.
    """
    system = (
        "你是学术论文写作规划专家。根据用户提供的论文标题和粗略大纲，生成详细的写作计划。"
        "你必须为每个章标题下生成 2-4 个节标题，每个节标题附带 2-4 条写作要点和 1-3 个文献检索关键词。"
        "引用密度标记为 high/medium/low。high 表示该节需要大量引用文献（≥5篇）。"
    )

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
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM response: {e}\n"
            f"Response text: {response.text[:500]}"
        )
    data["title"] = title
    data["total_word_count"] = config.get("total_word_count", 15000)
    return WritingPlan.from_dict(data)
