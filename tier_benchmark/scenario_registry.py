import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ScenarioSpec:
    scenario_id: str
    index: int
    title: str
    stage: str
    description: str
    test_point: str
    execution_mode: str  # "tool" | "text"
    data_files: List[str]
    estimated_cost_usd: Optional[float] = None  # from outer AI scenario design; shown to inner when scientist_config in (1,2,3)
    reviewer_criteria_extra: Optional[str] = None  # appended to reviewer criteria; e.g. "Reject (needs_revision) if report is not in Markdown format."

    def to_dict(self) -> Dict:
        return asdict(self)


STAGE_RULES = [
    (1, 2, "experimental_design"),
    (3, 4, "data_cleaning"),
    (5, 6, "stat_analysis"),
    (7, 10, "code_execution"),
    (11, 14, "result_interpretation"),
    (15, 18, "report_writing"),
]


TOOL_MODE_SCENARIOS = {3, 4, 5, 6, 9, 10}  # S07, S08 removed (domain-specific physics scenarios)


def _infer_stage(index: int) -> str:
    for start, end, stage in STAGE_RULES:
        if start <= index <= end:
            return stage
    return "unknown"


def _infer_execution_mode(index: int) -> str:
    return "tool" if index in TOOL_MODE_SCENARIOS else "text"


def _find_data_files(data_dir: Path, index: int) -> List[str]:
    pattern = f"scenario{index}_*"
    return sorted([p.name for p in data_dir.glob(pattern) if p.is_file()])


def _extract_test_point(block: str) -> str:
    m = re.search(r"\*\*测试点：\*\*(.+?)(?:\n### |\n## |\Z)", block, re.S)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""


def _extract_scenario_description(block: str) -> str:
    if "**测试点：**" in block:
        block = block.split("**测试点：**", 1)[0]
    return re.sub(r"\n\s*\n", "\n", block).strip()


def load_scenarios_from_markdown(benchmark_md_path: Path, data_dir: Path) -> Dict[str, ScenarioSpec]:
    text = benchmark_md_path.read_text(encoding="utf-8")

    # Split by scenario heading blocks:
    # ### 场景1 — xxx
    pattern = re.compile(r"#{3,4}\s*场景(\d+)\s*—\s*(.+?)\n(.*?)(?=\n#{3,4}\s*场景\d+\s*—|\Z)", re.S)
    matches = list(pattern.finditer(text))

    scenarios: Dict[str, ScenarioSpec] = {}
    for m in matches:
        idx = int(m.group(1))
        title = m.group(2).strip()
        body = m.group(3).strip()
        scenario_id = f"S{idx:02d}"
        stage = _infer_stage(idx)
        execution_mode = _infer_execution_mode(idx)
        test_point = _extract_test_point(body)
        data_files = _find_data_files(data_dir, idx)

        # Strip test-point content so agent only sees scenario description.
        desc = _extract_scenario_description(body)

        scenarios[scenario_id] = ScenarioSpec(
            scenario_id=scenario_id,
            index=idx,
            title=title,
            stage=stage,
            description=desc,
            test_point=test_point,
            execution_mode=execution_mode,
            data_files=data_files,
        )
    return scenarios


def select_scenarios(scenarios: Dict[str, ScenarioSpec], ids: Optional[List[str]] = None) -> List[ScenarioSpec]:
    if not ids:
        return [scenarios[k] for k in sorted(scenarios.keys())]
    chosen = []
    for sid in ids:
        if sid not in scenarios:
            raise ValueError(f"Unknown scenario id: {sid}")
        chosen.append(scenarios[sid])
    return chosen
