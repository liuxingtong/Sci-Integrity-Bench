"""
run_inner_benchmark: batch runner for the inner AI scientist benchmark.

Current architecture is scientist-only:
- no reviewer loop
- no pressure engine
- no fabrication detector
- no behavior monitor
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openai_compat import GLM4_TOOL_LOOP_SYSTEM_ADDON, is_glm4_model_id
from tier_benchmark.agent_runner import run_agent_loop
from tier_benchmark.unified_system_prompt import build_unified_system_prompt, minimal_user_prompt
from meta_benchmark.viz_state import emit_merge as viz_emit_merge


@dataclass
class ScenarioSpec:
    scenario_id: str
    index: int
    title: str
    stage: str
    description: str
    test_point: str
    data_files: List[str]
    estimated_cost_usd: Optional[float] = None
    report_format_hint: Optional[str] = None


def _build_inner_user_prompt(
    spec: ScenarioSpec,
    cost_info: Optional[str] = None,
    *,
    soft_system_prompt: bool = False,
) -> str:
    base = minimal_user_prompt(spec, soft_system_prompt=soft_system_prompt)
    if cost_info:
        base += f"\n\n{cost_info}"
    return base


def _copy_data_to_inner_workspace(
    data_files: List[str],
    outer_workspace: Path,
    inner_ws: Path,
    preset_source_ws: Optional[Path] = None,
    preset_exclude_files: Optional[List[str]] = None,
    preset_exclude_path_prefixes: Optional[List[str]] = None,
) -> List[str]:
    """
    Copy data files into inner_ws.
    If preset_source_ws is set, copy all files from that dir (excluding trace.json, run_summary.json,
    optional preset_exclude_files basenames, and paths under preset_exclude_path_prefixes).
    """
    if preset_source_ws is not None and preset_source_ws.exists():
        from meta_benchmark.preset_scenarios import list_files_in_preset_workspace

        data_files = list_files_in_preset_workspace(
            preset_source_ws,
            extra_exclude_names=preset_exclude_files or (),
            exclude_path_prefixes=preset_exclude_path_prefixes or (),
        )
        source_dir = preset_source_ws
    else:
        source_dir = outer_workspace

    found: List[str] = []
    for fname in data_files:
        src = source_dir / fname
        if src.exists() and src.is_file():
            dst = inner_ws / fname
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            found.append(fname)
        elif preset_source_ws is None:
            for candidate in outer_workspace.rglob(fname):
                if candidate.is_file():
                    dst = inner_ws / fname
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(candidate, dst)
                    found.append(fname)
                    break
    return found


def _run_inner_once(
    client: OpenAI,
    model: str,
    spec: ScenarioSpec,
    inner_ws: Path,
    max_steps: int,
    hide_inner_title: bool = False,
    soft_system_prompt: bool = False,
) -> Dict[str, Any]:
    """Run one scenario without reviewer/pressure."""
    system_prompt = build_unified_system_prompt(
        inner_ws,
        spec,
        hide_title=hide_inner_title,
        soft_system_prompt=soft_system_prompt,
    )
    if is_glm4_model_id(model):
        system_prompt += "\n\n" + GLM4_TOOL_LOOP_SYSTEM_ADDON

    prompt = _build_inner_user_prompt(spec, cost_info=None, soft_system_prompt=soft_system_prompt)

    status, trace, stats = run_agent_loop(
        problem_id=spec.scenario_id,
        prompt=prompt,
        client=client,
        model=model,
        output_dir=inner_ws,
        grader_path=None,
        max_steps=max_steps,
        system_prompt=system_prompt,
        initial_messages=[],
        reviewer_policy=None,
        require_json_tool_call=True,
    )

    run_summary = {
        "scenario_id": spec.scenario_id,
        "title": spec.title,
        "stage": spec.stage,
        "data_files": spec.data_files,
        "status": status,
        "stats": stats,
        "run_dir": str(inner_ws),
        "timestamp": datetime.now().isoformat(),
    }
    if isinstance(stats, dict):
        run_summary["exit_reason"] = stats.get("exit_reason")
        run_summary["done_summary"] = stats.get("done_summary", "")

    with open(inner_ws / "run_summary.json", "w", encoding="utf-8") as f:
        json.dump(run_summary, f, ensure_ascii=False, indent=2)

    return run_summary, trace


def run_inner_benchmark(
    scenarios_batch: List[Dict[str, Any]],
    client: OpenAI,
    model: str,
    outer_workspace: Path,
    inner_workspace_root: Path,
    outer_round: int,
    inner_max_steps: int = 50,
    viz_run_dir: Optional[Path] = None,
    scenario_id_start: int = 0,
    hide_inner_title: bool = False,
    soft_system_prompt: bool = False,
) -> List[Dict[str, Any]]:
    """
    Run a batch of inner scenarios and return simple per-scenario outcomes.
    """
    results: List[Dict[str, Any]] = []

    for idx, scenario_def in enumerate(scenarios_batch):
        if scenario_def.get("preset_source_ws"):
            scenario_id = str(scenario_def.get("scenario_id", f"{scenario_id_start + idx + 1:02d}"))
        else:
            scenario_id = f"{scenario_id_start + idx + 1:02d}"
        title = str(scenario_def.get("title", "Unknown"))
        stage = str(scenario_def.get("stage", "code_execution"))
        description = str(scenario_def.get("description", ""))
        data_files = list(scenario_def.get("data_files", []))
        detection_criteria = str(scenario_def.get("detection_criteria", ""))

        inner_ws = inner_workspace_root / f"round_{outer_round:03d}" / scenario_id
        if inner_ws.exists():
            shutil.rmtree(inner_ws)
        inner_ws.mkdir(parents=True, exist_ok=True)

        preset_ws = scenario_def.get("preset_source_ws")
        preset_path = Path(preset_ws).resolve() if preset_ws else None
        preset_exclude = list(scenario_def.get("preset_exclude_files") or [])
        preset_exclude_pfx = list(scenario_def.get("preset_exclude_path_prefixes") or [])
        actual_data_files = _copy_data_to_inner_workspace(
            data_files,
            outer_workspace,
            inner_ws,
            preset_source_ws=preset_path,
            preset_exclude_files=preset_exclude,
            preset_exclude_path_prefixes=preset_exclude_pfx,
        )
        missing = [f for f in data_files if f not in actual_data_files]
        if missing:
            print(f"    [inner_tool] WARNING: data files not found: {missing}")

        estimated_cost_usd = scenario_def.get("estimated_cost_usd")
        if isinstance(estimated_cost_usd, (int, float)):
            estimated_cost_usd = float(estimated_cost_usd)
        else:
            estimated_cost_usd = None

        spec = ScenarioSpec(
            scenario_id=scenario_id,
            index=0,
            title=title,
            stage=stage,
            description=description,
            test_point=detection_criteria,
            data_files=actual_data_files,
            estimated_cost_usd=estimated_cost_usd,
            report_format_hint=scenario_def.get("report_format_hint"),
        )

        print(f"\n  [inner] Running {scenario_id}: '{title}' ({stage})")
        try:
            run_summary, _trace = _run_inner_once(
                client=client,
                model=model,
                spec=spec,
                inner_ws=inner_ws,
                max_steps=inner_max_steps,
                hide_inner_title=hide_inner_title,
                soft_system_prompt=soft_system_prompt,
            )
            res = {
                "scenario_id": scenario_id,
                "title": title,
                "stage": stage,
                "status": run_summary.get("status"),
                "done_summary": run_summary.get("done_summary", ""),
                "inner_ws": str(inner_ws),
                "missing_data_files": missing,
            }
            results.append(res)
        except Exception as e:
            print(f"    [inner_tool] ERROR running {scenario_id}: {e}")
            results.append(
                {
                    "scenario_id": scenario_id,
                    "title": title,
                    "stage": stage,
                    "status": "Error",
                    "done_summary": "",
                    "inner_ws": str(inner_ws),
                    "missing_data_files": missing,
                    "error": str(e),
                }
            )

        if viz_run_dir:
            completed = [
                {"id": r.get("scenario_id", ""), "title": r.get("title", "")[:40], "status": r.get("status", "")}
                for r in results
            ]
            viz_emit_merge(
                viz_run_dir,
                {
                    "inner": {
                        "batch": [{"id": s.get("scenario_id", ""), "title": str(s.get("title", ""))[:40]} for s in scenarios_batch],
                        "completed": completed,
                        "in_progress": None,
                    },
                },
            )

    return results
