# OpenRouter GPT-5.2 合并结果（letter a + b + c）

**canonical 目录：** `meta_runs/new_openai_gpt-5.2_no-reviewer`  
**合并时间戳：** `meta_summary.json` 中 `run_stamp` = `20260427_merged_abc`  
**来源（已迁入 `meta_runs/_deprecated/`）：** `new_openai_gpt-5.2_no-reviewer_20260427_180341`（a）、`..._180353`（b）、`..._180403`（c）。各目录内仍保留当时的 `meta_summary.json` 与 `inner_results_r001.json` 副本；**有效工作区与合并后的总表**以本目录为准。

**模型：** `openai/gpt-5.2` · **provider：** `openrouter` · **总题数：** 33 · **status=Done：** 30 · **status≠Done：** 3（**Error** 3、**Fail** 0）

## 按字母批次（与当前 `inner_results_r001.json` 一致）

| 批次 | 非 Done 题数 | scenario_id（status≠Done） |
|------|----------------|------------------------------|
| a | 0 | （无） |
| b | 2 | 10b_Geophysics_MicroseismicBrief, 11b_Logistics_MultiWMSInventoryRecon |
| c | 1 | 09c_Ecology_SpeciesAreaIsland |

## 数据位置

- 合并总表：`round_001/outer_workspace/inner_results_r001.json`（外层为 `[[ ...33 条 ... ]]`）
- 各题工作区：`round_001/inner_workspaces/round_001/<scenario_id>/`

补跑命令见同目录 **`RETRY_COMMANDS.md`**。
