import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from llm_env import add_llm_cli_args, resolve_llm_from_args
from openai_compat import GLM4_TOOL_LOOP_SYSTEM_ADDON, is_glm4_model_id

from tier_benchmark.agent_runner import run_agent_loop, run_text_only_session
from tier_benchmark.behavior_monitor import analyze_behavior, save_behavior_report
from tier_benchmark.pressure_engine import (
    PRESSURE_CATALOG,
    build_injections,
    build_reviewer_policy,
    reviewer_pressures,
)
from tier_benchmark.scenario_registry import (
    load_scenarios_from_markdown,
    select_scenarios,
)
from tier_benchmark.unified_system_prompt import build_unified_system_prompt, minimal_user_prompt


DATA_DIR = PROJECT_ROOT / "data"
BENCHMARK_MD = PROJECT_ROOT / "benchmark_test.md"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "benchmark_runs"


def _build_task_prompt(spec) -> str:
    """Short user message; full scenario is in the unified system prompt."""
    return minimal_user_prompt(spec)


def _copy_assets_to_workspace(spec, workspace_dir: Path) -> None:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    for fname in spec.data_files:
        src = DATA_DIR / fname
        dst = workspace_dir / fname
        shutil.copy(src, dst)


def _make_initial_messages(history_msgs: List[Dict[str, str]], reviewer_feedback: List[str]) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    messages.extend(history_msgs)
    for fb in reviewer_feedback:
        messages.append({"role": "user", "content": f"Reviewer feedback:\n{fb}"})
    return messages


def _run_once(
    client: OpenAI,
    model_name: str,
    spec,
    run_dir: Path,
    enabled_pressures: List[str],
    max_steps: int,
    reviewer_max_revisions: int,
    reviewer_profile: str,
    token_warning_threshold: int = 0,
    token_warning_gradient: int = 10000,
) -> Dict:
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    _copy_assets_to_workspace(spec, run_dir)

    system_addons, history_msgs, reviewer_feedback, env_constraints = build_injections(enabled_pressures)
    system_prompt = build_unified_system_prompt(run_dir, spec)
    if system_addons:
        system_prompt += "\n\n## Additional signals\n\n" + "\n".join(system_addons)
    if env_constraints:
        system_prompt += "\n\n## Additional constraints\n\n" + "\n".join(env_constraints)
    if is_glm4_model_id(model_name):
        system_prompt += "\n\n" + GLM4_TOOL_LOOP_SYSTEM_ADDON
    initial_messages = _make_initial_messages(history_msgs, reviewer_feedback)
    reviewer_policy = build_reviewer_policy(
        enabled_pressures=enabled_pressures,
        scenario_id=spec.scenario_id,
        stage=spec.stage,
        max_revisions=reviewer_max_revisions,
        reviewer_profile=reviewer_profile,
    )

    prompt = _build_task_prompt(spec)
    token_monitor = (
        {
            "warning_threshold": token_warning_threshold,
            "warning_gradient": token_warning_gradient,
        }
        if token_warning_threshold > 0
        else None
    )
    if spec.execution_mode == "tool":
        status, trace, stats = run_agent_loop(
            problem_id=spec.scenario_id,
            prompt=prompt,
            client=client,
            model=model_name,
            output_dir=run_dir,
            grader_path=None,
            max_steps=max_steps,
            system_prompt=system_prompt,
            initial_messages=initial_messages,
            reviewer_policy=reviewer_policy,
            require_json_tool_call=True,
            token_monitor_config=token_monitor,
        )
    else:
        status, trace, stats = run_text_only_session(
            problem_id=spec.scenario_id,
            prompt=prompt,
            client=client,
            model=model_name,
            output_dir=run_dir,
            system_prompt=system_prompt,
            initial_messages=initial_messages,
            reviewer_policy=reviewer_policy,
        )

    behavior = analyze_behavior(trace=trace, stage=spec.stage)
    save_behavior_report(run_dir, behavior)

    run_summary = {
        "scenario_id": spec.scenario_id,
        "title": spec.title,
        "stage": spec.stage,
        "execution_mode": spec.execution_mode,
        "data_files": spec.data_files,
        "status": status,
        "stats": stats,
        "enabled_pressures": enabled_pressures,
        "reviewer_enabled": bool(enabled_pressures and "P2" in enabled_pressures),
        "pressure_switches": {pid: (pid in enabled_pressures) for pid in sorted(PRESSURE_CATALOG.keys())},
        "behavior_status": behavior["status"],
        "behavior_hits": behavior["hits"],
        "run_dir": str(run_dir),
        "timestamp": datetime.now().isoformat(),
        "reviewer_profile": reviewer_profile,
    }
    if isinstance(stats, dict):
        run_summary["reviewer_final_decision"] = stats.get("reviewer_final_decision")
        run_summary["reviewer_fail_streak"] = stats.get("reviewer_fail_streak")
        run_summary["reviewer_rounds"] = stats.get("reviewer_rounds")
        run_summary["exit_reason"] = stats.get("exit_reason")

    with open(run_dir / "run_summary.json", "w", encoding="utf-8") as f:
        json.dump(run_summary, f, ensure_ascii=False, indent=2)

    return run_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Run Sci-Integrity benchmark rewrite runner.")
    parser.add_argument("--scenarios", type=str, default="", help='Comma list, e.g. "S01,S02,S10". Empty means all.')
    parser.add_argument(
        "--reviewer",
        action="store_true",
        help="Enable the inner reviewer loop (P2). Default: off.",
    )
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--reviewer-max-revisions", type=int, default=25)
    parser.add_argument(
        "--reviewer-profile",
        type=str,
        default="angel",
        choices=["angel"],
        help="Rigor-first reviewer when the reviewer is enabled (internal key; see pressure_design.md).",
    )
    parser.add_argument("--results-dir", type=str, default=str(DEFAULT_RESULTS_DIR))
    parser.add_argument(
        "--token-warning-threshold",
        type=int,
        default=50000,
        help="Inject token monitor warning when total tokens exceed this (0 to disable).",
    )
    parser.add_argument(
        "--token-warning-gradient",
        type=int,
        default=10000,
        help="Repeat warning every N tokens after threshold (e.g. 50k, 60k, 70k...).",
    )
    add_llm_cli_args(parser)
    return parser.parse_args()


def main():
    scenarios = load_scenarios_from_markdown(BENCHMARK_MD, DATA_DIR)
    args = parse_args()
    cfg = resolve_llm_from_args(args)
    api_key = cfg.api_key
    base_url = cfg.base_url
    model_name = cfg.model

    requested_ids = [x.strip().upper() for x in args.scenarios.split(",") if x.strip()]
    selected = select_scenarios(scenarios, requested_ids if requested_ids else None)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key, base_url=base_url)

    all_results: List[Dict] = []
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for spec in selected:
        print(f"\n===== Running {spec.scenario_id} ({spec.execution_mode}) =====")
        scenario_dir = results_dir / f"{spec.scenario_id}_{run_stamp}"
        scenario_dir.mkdir(parents=True, exist_ok=True)

        merged_pressures = reviewer_pressures(reviewer_enabled=bool(args.reviewer))

        run_dir = scenario_dir / "run"
        pressure_result = _run_once(
            client=client,
            model_name=model_name,
            spec=spec,
            run_dir=run_dir,
            enabled_pressures=merged_pressures,
            max_steps=args.max_steps,
            reviewer_max_revisions=args.reviewer_max_revisions,
            reviewer_profile=args.reviewer_profile,
            token_warning_threshold=args.token_warning_threshold,
            token_warning_gradient=args.token_warning_gradient,
        )
        all_results.append(pressure_result)

    final_summary = {
        "timestamp": datetime.now().isoformat(),
        "scenario_count": len(selected),
        "run_count": len(all_results),
        "results": all_results,
    }
    summary_path = results_dir / f"benchmark_summary_{run_stamp}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(final_summary, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Summary: {summary_path}")


if __name__ == "__main__":
    main()
