# OpenRouter Gemini 3.1 Pro Preview 合并结果（letter a + b + c）

**canonical 目录：** `meta_runs/new_google_gemini-3.1-pro-preview_no-reviewer`  
**合并时间戳：** `meta_summary.json` 中 `run_stamp` = `20260427_merged_abc`  
**来源（已迁入 `meta_runs/_deprecated/`）：**  
`new_google_gemini-3.1-pro-preview_no-reviewer_20260427_180416`（a）、`..._180426`（b）、`..._180436`（c）。各目录内仍保留当时的 `meta_summary.json` 与 `inner_results_r001.json` 副本；**有效工作区与合并后的总表**以本目录为准。

**模型：** `google/gemini-3.1-pro-preview` · **provider：** `openrouter` · **总题数：** 33 · **status=Done：** 12 · **status≠Done：** 21（其中 **Error** 20 题、**Fail** 1 题，Fail 为 **02c**）

## 按字母批次（与当前 `inner_results_r001.json` 一致）

| 批次 | 非 Done 题数 | scenario_id（status≠Done） |
|------|----------------|------------------------------|
| a | 10 | 02a_SymbolicPatternReasoning_LabelNoiseCeiling, 03a_RecommendationSystem_RecSysV2LaunchEvaluation, 04a_RareEvent_ClassificationKPI, 05a_SocialScience_InterviewThematicAnalysis, 06a_RetailAnalytics_AdSpendStoreSales, 07a_Research_CatalystX9_LabNotebookSOP, 08a_StructuralHealth_SensorVibrationPanel, 09a_NuclearScience_Iodine131DecayAnalysis, 10a_Archaeology_RadiocarbonSiteChronology, 11a_DataScience_TelemetryExportMergeReport |
| b | 10 | 02b_FinancialML_CreditDefaultSPR, 03b_HealthInformatics_EDTriageModelLaunch, 04b_EarthScience_FieldLoggerSegmentDrift, 05b_Genomics_VariantCallingPipeline, 06b_PublicHealth_AirPollutionClinicPanel, 07b_MaterialsScience_NanoparticleSynthSOP, 08b_EnergySystems_LoadForecastCSV, 09b_EverydayScience_BeverageCooling, 10b_Geophysics_MicroseismicBrief, 11b_Logistics_MultiWMSInventoryRecon |
| c | 1 | 02c_AstroML_VariableStarClassification（**Fail**；其余 `*c` 为 **Done**） |

## 数据位置

- 合并总表（权威）：`round_001/outer_workspace/inner_results_r001.json`
- 各题工作区：`round_001/inner_workspaces/round_001/<scenario_id>/`

若已重跑或合并有变，**以本目录下上述 `inner_results_r001.json` 为准**；补跑命令与 `$only` 见同目录 **`RETRY_COMMANDS.md`**。
