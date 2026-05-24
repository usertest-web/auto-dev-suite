from dataclasses import dataclass, field
from typing import Optional, Callable
import json
import os


@dataclass
class StepResult:
    output: dict = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class PipelineContext:
    """Holds working state for the pipeline: paths, config, and stage outputs."""

    def __init__(self, work_dir: str):
        self.work_dir = work_dir
        os.makedirs(work_dir, exist_ok=True)
        self._outputs: dict = {}

    def stage_path(self, stage_num: int) -> str:
        return os.path.join(self.work_dir, f"{stage_num:02d}-stage-output.json")

    def get_stage_output(self, stage_num: int) -> Optional[dict]:
        if stage_num in self._outputs:
            return self._outputs[stage_num]
        path = self.stage_path(stage_num)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._outputs[stage_num] = data
            return data
        return None

    def set_stage_output(self, stage_num: int, data: dict):
        self._outputs[stage_num] = data
        with open(self.stage_path(stage_num), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class Pipeline:
    def __init__(self, mode: str = "auto", work_dir: str = "./output"):
        self.mode = mode
        self.work_dir = work_dir
        self._stages: dict = {}
        self._completed_stages: set = set()

    def stage(self, num: int):
        """Decorator to register a pipeline stage."""
        def decorator(fn: Callable):
            self._stages[num] = fn
            return fn
        return decorator

    def _confirm(self, stage_num: int, result: StepResult) -> bool:
        if self.mode in ("auto", "resume"):
            return True
        print(f"\nStage {stage_num} complete. Output: {json.dumps(result.output, ensure_ascii=False)[:200]}")
        if result.error:
            print(f"Error: {result.error}")
        resp = input("Continue to next stage? [Y/n/q]: ").strip().lower()
        if resp == "q":
            return False
        return True

    def run(self, max_stage: int = 6) -> dict:
        """Run all stages from 1 to max_stage."""
        results = {}
        ctx = PipelineContext(work_dir=self.work_dir)

        for num in range(1, max_stage + 1):
            if num in self._completed_stages:
                print(f"Stage {num}: already completed, skipping.")
                continue

            fn = self._stages.get(num)
            if not fn:
                print(f"Stage {num}: no handler registered, skipping.")
                continue

            print(f"\n{'='*40}\nRunning Stage {num}\n{'='*40}")
            try:
                result = fn(ctx)
            except Exception as e:
                result = StepResult(error=str(e))

            results[num] = result
            ctx.set_stage_output(num, result.output)

            if not result.success:
                print(f"Stage {num} FAILED: {result.error}")
                if self.mode not in ("auto", "resume"):
                    resp = input("Continue anyway? [y/N]: ").strip().lower()
                    if resp != "y":
                        break
                else:
                    break

            if not self._confirm(num, result):
                break

        return results
