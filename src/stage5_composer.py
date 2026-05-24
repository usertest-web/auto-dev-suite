import re
from src.word_com import WordApp
from src.stage4_writer import Draft
from src.stage3_searcher import ReferenceList


def _write_cover(app: WordApp, meta: dict, style_config: dict):
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
    app.type_text(chapter.title)
    app.type_paragraph()
    if "heading_1" in style_config.get("styles", {}):
        app.apply_style("heading_1")

    for section in chapter.sections:
        app.type_text(f"{section.num} {section.title}")
        app.type_paragraph()
        if "heading_2" in style_config.get("styles", {}):
            app.apply_style("heading_2")

        content = section.content
        paragraphs = content.split("\n")
        for para_text in paragraphs:
            if para_text.strip():
                app.type_text(para_text.strip())
                app.type_paragraph()
                if "body" in style_config.get("styles", {}):
                    app.apply_style("body")


def _write_references(app: WordApp, refs: ReferenceList, style_config: dict):
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
