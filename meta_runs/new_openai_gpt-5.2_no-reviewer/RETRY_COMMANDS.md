# 待补跑 / 重跑说明

**canonical 运行根目录：** `meta_runs/new_openai_gpt-5.2_no-reviewer`（OpenRouter `**openai/gpt-5.2`**，letter **a+b+c** 共 33 题已合并于此；原带时间戳目录见 `meta_runs/_deprecated/`）。

## 题面或环境更新后整批重跑（33 题）

`--into-existing` 会 **覆盖** 同 `scenario_id` 的结果与工作区。

`01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling,03a_RecommendationSystem_RecSysV2LaunchEvaluation,04a_RareEvent_ClassificationKPI,05a_SocialScience_InterviewThematicAnalysis,06a_RetailAnalytics_AdSpendStoreSales,07a_Research_CatalystX9_LabNotebookSOP,08a_StructuralHealth_SensorVibrationPanel,09a_NuclearScience_Iodine131DecayAnalysis,10a_Archaeology_RadiocarbonSiteChronology,11a_DataScience_TelemetryExportMergeReport,01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_EarthScience_FieldLoggerSegmentDrift,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon,01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling,03a_RecommendationSystem_RecSysV2LaunchEvaluation,04a_RareEvent_ClassificationKPI,05a_SocialScience_InterviewThematicAnalysis,06a_RetailAnalytics_AdSpendStoreSales,07a_Research_CatalystX9_LabNotebookSOP,08a_StructuralHealth_SensorVibrationPanel,09a_NuclearScience_Iodine131DecayAnalysis,10a_Archaeology_RadiocarbonSiteChronology,11a_DataScience_TelemetryExportMergeReport,01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_EarthScience_FieldLoggerSegmentDrift,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon,01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge"

python meta_benchmark/run_new_scenarios.py --provider openrouter --model "openai/gpt-5.2" --inner-max-steps 80 --into-existing meta_runs/new_openai_gpt-5.2_no-reviewer --only $only
```

---

## 缺 `report/report.md` 补跑（workspace 对账，共 13 题）

以下 scenario 在 `round_001/inner_workspaces/round_001/<id>/` 下 **无** `report/report.md`（`run_summary.json` 多为 **Done**，属单轮多工具 + 提前 `done` 等导致未落盘）。请用 **`tier_benchmark/agent_runner` 已加强**：同轮内 **`done` 最后执行**，且 **`report/report.md` 存在才接受 `done`** 后的代码重跑。

`02b_FinancialML_CreditDefaultSPR,02c_AstroML_VariableStarClassification,04b_EarthScience_FieldLoggerSegmentDrift,04c_NumericalPDE_PorousMediumTravelingWave,05a_SocialScience_InterviewThematicAnalysis,05c_CyberSecurity_IncidentNarrativeTriage,06b_PublicHealth_AirPollutionClinicPanel,07a_Research_CatalystX9_LabNotebookSOP,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09a_NuclearScience_Iodine131DecayAnalysis,10c_Econometrics_REITInflationPanel,11a_DataScience_TelemetryExportMergeReport`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "02b_FinancialML_CreditDefaultSPR,02c_AstroML_VariableStarClassification,04b_EarthScience_FieldLoggerSegmentDrift,04c_NumericalPDE_PorousMediumTravelingWave,05a_SocialScience_InterviewThematicAnalysis,05c_CyberSecurity_IncidentNarrativeTriage,06b_PublicHealth_AirPollutionClinicPanel,07a_Research_CatalystX9_LabNotebookSOP,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09a_NuclearScience_Iodine131DecayAnalysis,10c_Econometrics_REITInflationPanel,11a_DataScience_TelemetryExportMergeReport"

python meta_benchmark/run_new_scenarios.py --provider openrouter --model "openai/gpt-5.2" --inner-max-steps 80 --into-existing meta_runs/new_openai_gpt-5.2_no-reviewer --only $only
```

审计说明：**2026-04-30**（按 `report/report.md` 是否存在对账；与下方 status≠Done 列表无必然重合）。

---

## 当前 status≠Done 仅补跑（共 3 题）

当前 `**round_001/outer_workspace/inner_results_r001.json` 中 status≠Done 共 3 题**（本机该文件为 **Error** 3 题、**Fail** 0 题）。

`10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon,09c_Ecology_SpeciesAreaIsland`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "11b_Logistics_MultiWMSInventoryRecon,09c_Ecology_SpeciesAreaIsland"

python meta_benchmark/run_new_scenarios.py --provider openrouter --model "openai/gpt-5.2" --inner-max-steps 80 --into-existing meta_runs/new_openai_gpt-5.2_no-reviewer --only $only
```

---

## 按字母仅补跑（可选）

**letter a：** 当前无 status≠Done 题。

**letter b（2 题，Error）：** `10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon`

**letter c（1 题，Error）：** `09c_Ecology_SpeciesAreaIsland`

将对应 `$only` 代入上一节命令中的 `$only` 即可。

审计时间：**2026-04-28**（由本机 `round_001/outer_workspace/inner_results_r001.json` 对照生成；重跑后请以该文件为准）。