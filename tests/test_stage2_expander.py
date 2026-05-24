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
