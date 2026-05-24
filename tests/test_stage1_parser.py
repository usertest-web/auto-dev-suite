# tests/test_stage1_parser.py
import json
import pytest
from unittest.mock import patch, MagicMock
from src.stage1_parser import parse_template, ParsedTemplate, PageSettings


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
