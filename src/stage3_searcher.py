# src/stage3_searcher.py
from dataclasses import dataclass, field
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
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM response as JSON: {e}\n"
            f"Response text: {response.text[:500]}"
        )

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
