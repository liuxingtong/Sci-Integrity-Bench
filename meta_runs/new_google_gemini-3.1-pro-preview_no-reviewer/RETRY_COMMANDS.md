# 待补跑 / 重跑说明

**canonical 运行根目录：** `meta_runs/new_google_gemini-3.1-pro-preview_no-reviewer`（OpenRouter **`google/gemini-3.1-pro-preview`**，letter **a+b+c** 共 33 题已合并于此；原带时间戳目录见 `meta_runs/_deprecated/`）。

## 题面或环境更新后整批重跑（33 题）

`--into-existing` 会 **覆盖** 同 `scenario_id` 的结果与工作区。

`01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling,03a_RecommendationSystem_RecSysV2LaunchEvaluation,04a_RareEvent_ClassificationKPI,05a_SocialScience_InterviewThematicAnalysis,06a_RetailAnalytics_AdSpendStoreSales,07a_Research_CatalystX9_LabNotebookSOP,08a_StructuralHealth_SensorVibrationPanel,09a_NuclearScience_Iodine131DecayAnalysis,10a_Archaeology_RadiocarbonSiteChronology,11a_DataScience_TelemetryExportMergeReport,01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_EarthScience_FieldLoggerSegmentDrift,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon,01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling,03a_RecommendationSystem_RecSysV2LaunchEvaluation,04a_RareEvent_ClassificationKPI,05a_SocialScience_InterviewThematicAnalysis,06a_RetailAnalytics_AdSpendStoreSales,07a_Research_CatalystX9_LabNotebookSOP,08a_StructuralHealth_SensorVibrationPanel,09a_NuclearScience_Iodine131DecayAnalysis,10a_Archaeology_RadiocarbonSiteChronology,11a_DataScience_TelemetryExportMergeReport,01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_EarthScience_FieldLoggerSegmentDrift,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon,01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge"

python meta_benchmark/run_new_scenarios.py --provider openrouter --model "google/gemini-3.1-pro-preview" --inner-max-steps 80 --into-existing meta_runs/new_google_gemini-3.1-pro-preview_no-reviewer --only $only
```

---

## 缺 `report/report.md` 补跑（workspace 对账，共 2 题）

与下方 **status≠Done** 为同一批：`02b_FinancialML_CreditDefaultSPR`、`02c_AstroML_VariableStarClassification` 在 `inner_workspaces` 下 **`report/report.md` 缺失**（当时多为 **Fail / max_steps** 或未写完报告）。请在更新后的 `tier_benchmark/agent_runner`（**`done` 同轮最后执行** + **存在 `report/report.md` 才接受 `done`**）后补跑（可与下一节命令二选一或合并 `$only`）：

`02b_FinancialML_CreditDefaultSPR,02c_AstroML_VariableStarClassification`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "02b_FinancialML_CreditDefaultSPR,02c_AstroML_VariableStarClassification"

python meta_benchmark/run_new_scenarios.py --provider openrouter --model "google/gemini-3.1-pro-preview" --inner-max-steps 80 --into-existing meta_runs/new_google_gemini-3.1-pro-preview_no-reviewer --only $only
```

审计说明：**2026-04-30**。

---

## 当前 status≠Done 仅补跑（共 2 题）

当前 **`round_001/outer_workspace/inner_results_r001.json` 中 status≠Done 共 2 题**（**Error** 2、**Fail** 0）。

`02b_FinancialML_CreditDefaultSPR,02c_AstroML_VariableStarClassification`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "02b_FinancialML_CreditDefaultSPR,02c_AstroML_VariableStarClassification"

python meta_benchmark/run_new_scenarios.py --provider openrouter --model "google/gemini-3.1-pro-preview" --inner-max-steps 80 --into-existing meta_runs/new_google_gemini-3.1-pro-preview_no-reviewer --only $only
```

---

## 按字母仅补跑（可选）

**letter a：** 当前无 status≠Done 题。

**letter b（1 题，Error）：** `02b_FinancialML_CreditDefaultSPR`

**letter c（1 题，Error）：** `02c_AstroML_VariableStarClassification`

审计时间：**2026-04-30**（与当前 `round_001/outer_workspace/inner_results_r001.json` 再次核对一致；重跑后请以该文件为准）。
