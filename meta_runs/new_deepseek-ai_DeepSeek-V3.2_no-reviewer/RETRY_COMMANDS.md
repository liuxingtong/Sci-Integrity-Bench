# 待补跑说明（合并后审计）

审计时间：**2026-04-08**，以 `round_001/outer_workspace/inner_results_r001.json` 为准。

## 摘要

| 类型 | 数量 | 说明 |
| --- | --- | --- |
| letter **a** / **b** | 各 11 | 全为 `Done` |
| letter **c** | 10 `Done` + **1 `Error`** | 仅 **`01c_*`** 需重跑 |

## 待重跑场景

| scenario_id | 当前 status |
| --- | --- |
| `01c_BiomedicalImaging_CellBenchmarkPicker` | Error |

## 重跑指令

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

python meta_benchmark/run_new_scenarios.py --provider silicon --model "deepseek-ai/DeepSeek-V3.2" --into-existing meta_runs/new_deepseek-ai_DeepSeek-V3.2_no-reviewer --only 01c_BiomedicalImaging_CellBenchmarkPicker
```

跑完后可删除本文件或更新为「已无待补跑」。
