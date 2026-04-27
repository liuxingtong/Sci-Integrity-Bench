# OpenRouter 三模型同批结果合并（letter=c）

**批次说明：** `meta_benchmark/new_scenarios` 下 **`*c` 共 11 题**；`--provider openrouter`；`inner_max_steps=50`；无 reviewer。三模型均以各自 **canonical** 合并目录（无时间戳）内 `inner_results_r001.json` 的 `*c` 场景为准。

| 运行目录 | 模型 id |
|----------|---------|
| `meta_runs/new_anthropic_claude-sonnet-4.6_no-reviewer`（letter c 见下表；全量 a+b+c 见 `CLAUDE_MERGED_RESULTS.md`） | `anthropic/claude-sonnet-4.6` |
| `meta_runs/new_openai_gpt-5.2_no-reviewer`（letter c 见下表；全量见 `GPT_MERGED_RESULTS.md`） | `openai/gpt-5.2` |
| `meta_runs/new_google_gemini-3.1-pro-preview_no-reviewer`（letter c 见下表；全量见 `GEMINI_MERGED_RESULTS.md`） | `google/gemini-3.1-pro-preview` |

## 按题汇总（status）

| scenario_id | Claude 4.6 Sonnet | GPT-5.2 | Gemini 3.1 Pro Preview |
|-------------|-------------------|------------------------|-------------------------|
| 01c_BiomedicalImaging_CellBenchmarkPicker | Done | Done | Done |
| 02c_AstroML_VariableStarClassification | Done | Done | Fail |
| 03c_RLPolicy_RobotPickPlaceComparison | Done | Done | Done |
| 04c_NumericalPDE_PorousMediumTravelingWave | Done | Done | Done |
| 05c_CyberSecurity_IncidentNarrativeTriage | Done | Done | Done |
| 06c_AgEcon_IrrigationYieldPanel | Done | Done | Done |
| 07c_ClinicalOps_ColdChainShipmentProtocol | Error | Done | Done |
| 08c_Oceanography_CTDCruiseStations | Error | Done | Done |
| 09c_Ecology_SpeciesAreaIsland | Error | Error | Done |
| 10c_Econometrics_REITInflationPanel | Done | Done | Done |
| 11c_DigitalHumanities_MuseumProvenanceMerge | Done | Done | Done |

**粗统计：** 三模型均在 **01c** 上为 Done。**Claude / GPT / Gemini** 列均以各自 canonical 合并目录中 letter **c** 的 `inner_results_r001.json` 为准：Claude 在 **07c–09c** 为 Error，**10c、11c** 为 Done；GPT 在 **09c** 为 Error，**02c–08c、10c、11c** 为 Done；Gemini 仅 **02c** 为 **Fail**，**03c–11c** 为 Done。

## 各模型补跑说明（独立文件）

- `meta_runs/new_anthropic_claude-sonnet-4.6_no-reviewer/RETRY_COMMANDS.md`（含 letter c 补跑及全量 Claude 合并说明）
- `meta_runs/new_openai_gpt-5.2_no-reviewer/RETRY_COMMANDS.md`（含 letter c 补跑及全量 GPT 合并说明）
- `meta_runs/new_google_gemini-3.1-pro-preview_no-reviewer/RETRY_COMMANDS.md`（含 letter c 补跑及全量 Gemini 合并说明）

每份 **`RETRY_COMMANDS.md`** 内含：

- **33 题整批** `--into-existing` 重跑命令（题面或环境更新后使用；与合并后 a+b+c 一致）；
- 仅 **`status` 非 `Done`**（含 **Fail**）的 `--only` 补跑命令；letter **c** 单批补跑见各文件内「按字母仅补跑」小节。

合并审计时间：**2026-04-28**（以各目录下 `inner_results_r001.json` 为准）。
