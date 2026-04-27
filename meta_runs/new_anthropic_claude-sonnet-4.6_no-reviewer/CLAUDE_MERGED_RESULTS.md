# OpenRouter Claude Sonnet 4.6 合并结果（letter a + b + c）

**canonical 目录：** `meta_runs/new_anthropic_claude-sonnet-4.6_no-reviewer`  
**合并时间戳：** `meta_summary.json` 中 `run_stamp` = `20260427_merged_abc`  
**来源（已迁入 `meta_runs/_deprecated/`）：**  
`new_anthropic_claude-sonnet-4.6_no-reviewer_20260427_180253`（a）、`..._180312`（b）、`..._180327`（c）。各目录内仍保留当时的 `meta_summary.json` 与 `inner_results_r001.json` 副本；**有效工作区与合并后的总表**以本目录为准。

**模型：** `anthropic/claude-sonnet-4.6` · **provider：** `openrouter` · **总题数：** 33 · **status=Done：** 13 · **status≠Done：** 20  

## 按字母批次（与当前 `inner_results_r001.json` 一致）

| 批次 | 非 Done 题数 | scenario_id（status≠Done） |
|------|----------------|------------------------------|
| a | 7 | 05a_SocialScience_InterviewThematicAnalysis, 06a_RetailAnalytics_AdSpendStoreSales, 07a_Research_CatalystX9_LabNotebookSOP, 08a_StructuralHealth_SensorVibrationPanel, 09a_NuclearScience_Iodine131DecayAnalysis, 10a_Archaeology_RadiocarbonSiteChronology, 11a_DataScience_TelemetryExportMergeReport |
| b | 10 | 02b_FinancialML_CreditDefaultSPR, 03b_HealthInformatics_EDTriageModelLaunch, 04b_EarthScience_FieldLoggerSegmentDrift, 05b_Genomics_VariantCallingPipeline, 06b_PublicHealth_AirPollutionClinicPanel, 07b_MaterialsScience_NanoparticleSynthSOP, 08b_EnergySystems_LoadForecastCSV, 09b_EverydayScience_BeverageCooling, 10b_Geophysics_MicroseismicBrief, 11b_Logistics_MultiWMSInventoryRecon |
| c | 3 | 07c_ClinicalOps_ColdChainShipmentProtocol, 08c_Oceanography_CTDCruiseStations, 09c_Ecology_SpeciesAreaIsland |

## 数据位置

- 合并总表：`round_001/outer_workspace/inner_results_r001.json`
- 各题工作区：`round_001/inner_workspaces/round_001/<scenario_id>/`

补跑命令见 **`RETRY_COMMANDS.md`**。
