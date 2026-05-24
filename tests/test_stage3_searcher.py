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
