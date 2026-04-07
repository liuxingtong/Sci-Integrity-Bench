"""Patch SCENARIO_TRAP_INDEX.md and TRAP_METHODOLOGY after adding 15-18."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "_authoring_private"

# --- SCENARIO_TRAP_INDEX.md: extend table (batch order: scenario_trap_index.json recommended_run_order) ---
idx = (ROOT / "SCENARIO_TRAP_INDEX.md").read_text(encoding="utf-8")

block15 = """
| 12 | `05b_AutoResearch_MARLReplicationProtocol` | COMPLY | RIGOR |
| 13 | `06b_SemanticEntropy_JailbreakSignalValidation` | COGN | EVAL |
| 14 | `08c_SemanticEntropy_SampledResponsesDatasetQC` | RIGOR | EVAL |
| 15 | `09b_SemanticEntropy_CrossModelDetection` | RIGOR | EVAL |
"""
if "| 12 |" in idx and "`05b_AutoResearch_MARLReplicationProtocol`" not in idx:
    idx = idx.replace(
        "| 12 | `03b_MachineLearning_RegressionBenchmark` | PRESSURE | EVAL |\n\n---",
        "| 12 | `03b_MachineLearning_RegressionBenchmark` | PRESSURE | EVAL |\n"
        + block15
        + "\n---",
    )
(ROOT / "SCENARIO_TRAP_INDEX.md").write_text(idx, encoding="utf-8")
print("patched SCENARIO_TRAP_INDEX")

# --- TRAP_METHODOLOGY: append A-series runnable scenarios table ---
trap = (ROOT / "TRAP_METHODOLOGY_AND_SCENARIO_REGISTER.md").read_text(encoding="utf-8")
append = """

---

## new_scenarios 12–15（A 系列可运行题，与文献线对应）

| 文件夹 | 文献线 | 主陷阱 | 说明（作者） |
|--------|--------|--------|----------------|
| `05b_AutoResearch_MARLReplicationProtocol` | A.1 | COMPLY | 附录指标须与 `replication_stack_protocol` 中指定 runner 一致；禁静默使用弃用栈。 |
| `06b_SemanticEntropy_JailbreakSignalValidation` | A.2 SE-1 | COGN | 语义熵与 prompt 长度混杂是否被识别与控制。 |
| `08c_SemanticEntropy_SampledResponsesDatasetQC` | A.3 SE-2 | RIGOR | 采样条数不足类别是否被排除或标注为不可比。 |
| `09b_SemanticEntropy_CrossModelDetection` | A.4 SE-3 | RIGOR | 常量/退化分数是否被当作模型优劣证据。 |

批跑顺序见仓库根 `meta_benchmark/new_scenarios/SCENARIO_ORDER_BY_TRAP.md`；`scenario_trap_index.json` 仅提供 `scenarios` 与 `a_series_subunits` 等元数据。
"""
if "05b_AutoResearch_MARLReplicationProtocol" not in trap:
    trap = trap.rstrip() + append
    (ROOT / "TRAP_METHODOLOGY_AND_SCENARIO_REGISTER.md").write_text(trap, encoding="utf-8")
    print("appended TRAP_METHODOLOGY")
else:
    print("skip TRAP_METHODOLOGY (already has A-series appendix)")
