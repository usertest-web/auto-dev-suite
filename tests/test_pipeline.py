import json
import pytest
import os
from unittest.mock import patch, MagicMock
from src.pipeline import Pipeline, PipelineContext, StepResult


def test_pipeline_context_save_load(tmp_path):
    ctx = PipelineContext(work_dir=str(tmp_path))
    ctx.set_stage_output(1, {"key": "value"})
    assert ctx.get_stage_output(1) == {"key": "value"}
    assert ctx.get_stage_output(2) is None


def test_pipeline_runs_stages_in_order():
    pipe = Pipeline(mode="auto", work_dir="/tmp/test_pipe")
    executed = []

    @pipe.stage(1)
    def stage_one(ctx):
        executed.append(1)
        return StepResult(output={"result": "one"})

    @pipe.stage(2)
    def stage_two(ctx):
        executed.append(2)
        assert ctx.get_stage_output(1) == {"result": "one"}
        return StepResult(output={"result": "two"})

    results = pipe.run(max_stage=2)
    assert executed == [1, 2]
    assert results[1].output == {"result": "one"}
    assert results[2].output == {"result": "two"}


def test_pipeline_resume_skips_completed():
    pipe = Pipeline(mode="resume", work_dir="/tmp/test_pipe")
    executed = []

    @pipe.stage(1)
    def stage_one(ctx):
        executed.append(1)
        return StepResult(output={"done": True})

    @pipe.stage(2)
    def stage_two(ctx):
        executed.append(2)
        return StepResult(output={"done": True})

    pipe._completed_stages = {1}
    results = pipe.run(max_stage=2)
    assert executed == [2]
