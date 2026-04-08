# 待补跑说明（合并后审计）

审计时间：**2026-04-08**，以 `round_001/outer_workspace/inner_results_r001.json` 为准。

## 摘要

| 类型 | 数量 |
| --- | --- |
| `Done` | **32** |
| `Error` | **1** |
| `Fail` | 0 |
| 缺失 | 0 |

按 letter：**a** 11 Done；**b** 11 Done；**c** 10 Done，**1 Error**（`02c_*`）。

整批 a/b/c 已跑满 33 条记录；**仅剩 1 题需补跑**。

## 待重跑场景（Error，共 1）

`02c_AstroML_VariableStarClassification`

## 重跑指令（一条 `--only`）

可选加大步数：`--inner-max-steps 80`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

python meta_benchmark/run_new_scenarios.py --provider silicon --model "Pro/moonshotai/Kimi-K2.5" --inner-max-steps 80 --into-existing meta_runs/new_Pro_moonshotai_Kimi-K2.5_no-reviewer --only 02c_AstroML_VariableStarClassification
```
