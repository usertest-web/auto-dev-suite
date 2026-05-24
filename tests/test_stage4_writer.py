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
    cited = set()
    for ch in draft.chapters:
        for sec in ch.sections:
            cited.update(sec.cited_refs)
    uncited = total_ref_ids - cited
    assert 3 in uncited
    assert 4 in uncited
    assert 5 in uncited
