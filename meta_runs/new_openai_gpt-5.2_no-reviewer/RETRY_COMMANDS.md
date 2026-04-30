# 待补跑 / 重跑说明

**canonical 运行根目录：** `meta_runs/new_openai_gpt-5.2_no-reviewer`（OpenRouter `**openai/gpt-5.2`**，letter **a+b+c** 共 33 题已合并于此；原带时间戳目录见 `meta_runs/_deprecated/`）。

## Inner agent runner 行为（`tier_benchmark/agent_runner.py`）

以下策略作用于 **`meta_benchmark/run_new_scenarios.py` 等使用的 inner tool 循环**，用于避免「假 done、报告没落盘」：

1. **同一 assistant 一轮内的多个 JSON tool**  
   解析后 **在本 step 内按顺序全部执行**；若同一条消息里既有普通 tool 又有 `done(summary)`，会将 **`done` 放到该批次的最后执行**（先跑完写文件/执行命令，再验收 `done`）。

2. **`done(summary)` 交付物校验**  
   仅在同时满足时接受 `done`：
   - 工作区内存在 **`report/report.md`**；
   - 读取该文件后，其中 **Markdown 图片 `![](…)` / `![…](…)` 以及 `<img src="…">` 引用的本地路径**（非 `http(s)`）解析后必须落在 workspace 内且 **文件真实存在**（路径相对于 `report/report.md` 所在目录解析，通常即 `report/images/…`）。

若校验失败，trace 里 `done` 的 `status` 为 `rejected_deliverable`，模型需修补后再调用 `done`。

**防止「丢掉 report」主要靠第 2 条**：没有合格的 `report/report.md`（及链接到的本地图）就无法结束任务；这与「一轮执行几个 tool」无关。

## 重跑前清理半成品（可选）

重跑单题时建议删掉可再生成目录，保留 `data/`、`related_work/`：

- `code/`、`outputs/`、`report/`（含 `report/images/`）

路径：`meta_runs/new_openai_gpt-5.2_no-reviewer/round_001/inner_workspaces/round_001/<scenario_id>/`。

若题目复杂或模型习惯一轮塞很多 tool，可适当提高 **`--inner-max-steps`**（例如 80→100）。

### 仅重跑曾缺 `report/report.md` 的 5 题（示例）

`04b_EarthScience_FieldLoggerSegmentDrift`，`04c_NumericalPDE_PorousMediumTravelingWave`，`09a_NuclearScience_Iodine131DecayAnalysis`，`11a_DataScience_TelemetryExportMergeReport`，`07a_Research_CatalystX9_LabNotebookSOP`（前四题无或空报告；07a 仅有 `report/synthesis_sop.md` 时亦需标准 `report/report.md` 才能 `done`）。

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "04b_EarthScience_FieldLoggerSegmentDrift,04c_NumericalPDE_PorousMediumTravelingWave,07a_Research_CatalystX9_LabNotebookSOP,09a_NuclearScience_Iodine131DecayAnalysis,11a_DataScience_TelemetryExportMergeReport"

python meta_benchmark/run_new_scenarios.py --provider openrouter --model "openai/gpt-5.2" --inner-max-steps 100 --into-existing meta_runs/new_openai_gpt-5.2_no-reviewer --only $only
```

## 题面或环境更新后整批重跑（33 题）

`--into-existing` 会 **覆盖** 同 `scenario_id` 的结果与工作区。

`01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling,03a_RecommendationSystem_RecSysV2LaunchEvaluation,04a_RareEvent_ClassificationKPI,05a_SocialScience_InterviewThematicAnalysis,06a_RetailAnalytics_AdSpendStoreSales,07a_Research_CatalystX9_LabNotebookSOP,08a_StructuralHealth_SensorVibrationPanel,09a_NuclearScience_Iodine131DecayAnalysis,10a_Archaeology_RadiocarbonSiteChronology,11a_DataScience_TelemetryExportMergeReport,01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_EarthScience_FieldLoggerSegmentDrift,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon,01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling,03a_RecommendationSystem_RecSysV2LaunchEvaluation,04a_RareEvent_ClassificationKPI,05a_SocialScience_InterviewThematicAnalysis,06a_RetailAnalytics_AdSpendStoreSales,07a_Research_CatalystX9_LabNotebookSOP,08a_StructuralHealth_SensorVibrationPanel,09a_NuclearScience_Iodine131DecayAnalysis,10a_Archaeology_RadiocarbonSiteChronology,11a_DataScience_TelemetryExportMergeReport,01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_EarthScience_FieldLoggerSegmentDrift,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon,01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge"

python meta_benchmark/run_new_scenarios.py --provider openrouter --model "openai/gpt-5.2" --inner-max-steps 80 --into-existing meta_runs/new_openai_gpt-5.2_no-reviewer --only $only
```

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