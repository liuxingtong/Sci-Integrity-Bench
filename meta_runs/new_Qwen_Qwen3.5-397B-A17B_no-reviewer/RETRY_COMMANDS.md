# 待补跑说明（合并后审计）

审计时间：**2026-04-08**，以 `round_001/outer_workspace/inner_results_r001.json` 为准。

## 摘要

| 类型 | 数量 |
| --- | --- |
| `Error` | **28** |
| `Done` | 5 |
| `Fail` | 0 |
| 缺失 | 0 |

按 letter：**a** 9 Error / 2 Done；**b** 9 Error / 2 Done；**c** 10 Error / 1 Done。

## 待重跑场景（Error，共 28）

`01a_SymbolicPatternReasoning_BenchmarkSelection`, `01c_BiomedicalImaging_CellBenchmarkPicker`, `02a_SymbolicPatternReasoning_LabelNoiseCeiling`, `02b_FinancialML_CreditDefaultSPR`, `02c_AstroML_VariableStarClassification`, `03a_RecommendationSystem_RecSysV2LaunchEvaluation`, `03b_HealthInformatics_EDTriageModelLaunch`, `03c_RLPolicy_RobotPickPlaceComparison`, `04a_RareEvent_ClassificationKPI`, `04b_ControlSystems_LQRGainSchedule`, `04c_NumericalPDE_PorousMediumTravelingWave`, `05a_SocialScience_InterviewThematicAnalysis`, `05b_Genomics_VariantCallingPipeline`, `05c_CyberSecurity_IncidentNarrativeTriage`, `06a_RetailAnalytics_AdSpendStoreSales`, `06b_PublicHealth_AirPollutionClinicPanel`, `06c_AgEcon_IrrigationYieldPanel`, `07b_MaterialsScience_NanoparticleSynthSOP`, `08a_StructuralHealth_SensorVibrationPanel`, `08b_EnergySystems_LoadForecastCSV`, `08c_Oceanography_CTDCruiseStations`, `09c_Ecology_SpeciesAreaIsland`, `10a_Archaeology_RadiocarbonSiteChronology`, `10b_Geophysics_MicroseismicBrief`, `10c_Econometrics_REITInflationPanel`, `11a_DataScience_TelemetryExportMergeReport`, `11b_Logistics_MultiWMSInventoryRecon`, `11c_DigitalHumanities_MuseumProvenanceMerge`

## 重跑指令（一条 `--only`）

当前代码已包含路径校验与 5xx 重试；若仍大量 Error，可错峰分半批跑两次 `--only`。

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

python meta_benchmark/run_new_scenarios.py --provider silicon --model "Qwen/Qwen3.5-397B-A17B" --into-existing meta_runs/new_Qwen_Qwen3.5-397B-A17B_no-reviewer --only 01a_SymbolicPatternReasoning_BenchmarkSelection,01c_BiomedicalImaging_CellBenchmarkPicker,02a_SymbolicPatternReasoning_LabelNoiseCeiling,02b_FinancialML_CreditDefaultSPR,02c_AstroML_VariableStarClassification,03a_RecommendationSystem_RecSysV2LaunchEvaluation,03b_HealthInformatics_EDTriageModelLaunch,03c_RLPolicy_RobotPickPlaceComparison,04a_RareEvent_ClassificationKPI,04b_ControlSystems_LQRGainSchedule,04c_NumericalPDE_PorousMediumTravelingWave,05a_SocialScience_InterviewThematicAnalysis,05b_Genomics_VariantCallingPipeline,05c_CyberSecurity_IncidentNarrativeTriage,06a_RetailAnalytics_AdSpendStoreSales,06b_PublicHealth_AirPollutionClinicPanel,06c_AgEcon_IrrigationYieldPanel,07b_MaterialsScience_NanoparticleSynthSOP,08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10a_Archaeology_RadiocarbonSiteChronology,10b_Geophysics_MicroseismicBrief,10c_Econometrics_REITInflationPanel,11a_DataScience_TelemetryExportMergeReport,11b_Logistics_MultiWMSInventoryRecon,11c_DigitalHumanities_MuseumProvenanceMerge
```
