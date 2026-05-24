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

        mock_word.type_text.assert_any_call("绪论")
        mock_word.apply_style.assert_any_call("heading_1")
        mock_word.save_as.assert_called_once_with("output.docx")
