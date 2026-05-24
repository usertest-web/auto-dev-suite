# src/main.py
"""Academic thesis automation -- main entry point.

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
