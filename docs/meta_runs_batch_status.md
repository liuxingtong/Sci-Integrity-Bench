# meta_runs 批次完成度（自动审计占位）

> 最近核对：2026-04-08。判定：`inner_results_r001.json` 中每题 `status == Done` 为「该题完成」；无结果文件或仅部分目录视为「批次未完成」或「孤儿目录」。
> 重跑请使用与当时一致的 **`--provider`** / **`--model`**（见各批次 `meta_summary.json`）。

**重要（合并结果）**：`--into-existing` **且未带 `--only`** 时，会**整文件重写** `inner_results_r001.json`，可能冲掉已有 letter 的结果。要向同一 `run_id` **追加**另一套 letter，请使用 `--into-existing` **并** `--only` 列出该 letter 全部 11 个 `scenario_id`（脚本会按 `scenario_id` 合并覆盖）。

复核对 letter **b / c**（每模型各 11 题）：

```powershell
python scripts/audit_meta_runs_letter_bc.py
```

## Letter b / c 是否「跑满 11 题」（2026-04-08）

| 模型 | Letter **b**（`NNb_*`） | Letter **c**（`NNc_*`） |
| --- | --- | --- |
| DeepSeek-V3.2 | **缺**：无任何批次含 11 个 `*b*` 目录；仅孤儿 `...002436`（1 题）。需**整批**补跑 b。 | **缺**：仅孤儿 `...002437`（1 题）。需**整批**补跑 c。 |
| GLM-5 | **缺**：仅孤儿 `...225140`（1 题）。需整批 b。 | **缺**：仅孤儿 `...225141`（1 题）。需整批 c。 |
| Kimi-K2.5 | **不齐**：`...222651` 有 11 目录但仅 **2/11 Done**，9 Fail，需重跑未 Done 题。 | **缺**：无 11 目录批次；仅孤儿 `...231905`（`01c_*` 一题）。需整批 c。 |
| Qwen3.5-397B-A17B | **需重跑**：`...215657` 有 11 目录但 **11/11 Error**。 | **需重跑**：`...222631` 有 11 目录但 **11/11 Error**。 |

---

## 总览

| 模型（api model id） | Provider | 主批次 `run_id`（建议作为 canonical） | 套题 | 11 题全 Done？ | 待处理 |
| --- | --- | --- | --- | --- | --- |
| `deepseek-ai/DeepSeek-V3.2` | silicon | `new_deepseek-ai_DeepSeek-V3.2_no-reviewer_20260407_211506` | a | 是 | 清理下方孤儿目录或合并重跑 |
| `Pro/zai-org/GLM-5` | silicon | `new_Pro_zai-org_GLM-5_no-reviewer_20260407_211651` | a | 是 | 清理下方孤儿目录或合并重跑 |
| `Pro/moonshotai/Kimi-K2.5` | silicon | `new_Pro_moonshotai_Kimi-K2.5_no-reviewer_20260407_213322`（a）<br>`new_Pro_moonshotai_Kimi-K2.5_no-reviewer_20260407_222651`（b） | a, b | **否** | 见下文 `--only` 重跑 |
| `Pro/moonshotai/Kimi-K2.5` | silicon | （无） | c | **否** | 需整批 letter c 或补跑孤儿 `231905` |
| `Qwen/Qwen3.5-397B-A17B` | silicon | `new_Qwen_Qwen3.5-397B-A17B_no-reviewer_20260407_211635`（a）<br>`new_Qwen_Qwen3.5-397B-A17B_no-reviewer_20260407_215657`（b）<br>`new_Qwen_Qwen3.5-397B-A17B_no-reviewer_20260407_222631`（c） | a, b, c | **否**（均为 `Error`） | 三批均需整批或分题重试 |

## 未完成 / 异常目录说明

- **无 `inner_results_r001.json`（仅 inner 里 1 个场景目录）**：属于中断或测试残留，**不**计入正式批次完成度。
  - DeepSeek：`new_deepseek-ai_DeepSeek-V3.2_no-reviewer_20260408_002436`（仅 `01b_*`）、`...002437`（仅 `01c_*`）
  - GLM-5：`new_Pro_zai-org_GLM-5_no-reviewer_20260407_225140`（仅 `01b_*`）、`...225141`（仅 `01c_*`）
  - Kimi：`new_Pro_moonshotai_Kimi-K2.5_no-reviewer_20260407_231905`（仅 `01c_*`）

---

## 分模型：在项目根目录执行的命令（PowerShell）

以下均在 `f:\Aworks\1readraft\ai_scientist` 下执行；请已配置 `.env` 中对应 **SILICON_*** 或脚本所解析的凭据。

### 1）DeepSeek-V3.2 — letter **a** 已满；**b / c 需各整批 11 题**

- **Canonical（建议 abc 最终合一）**：`meta_runs\new_deepseek-ai_DeepSeek-V3.2_no-reviewer_20260407_211506`（当前仅 **a** 套 11 题 Done）。
- 将 **整套 b（11 题）** 合并进该目录（**必须**带齐 `--only` 11 个 id，否则会覆盖 JSON）：

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"
python meta_benchmark/run_new_scenarios.py --provider silicon --model "deepseek-ai/DeepSeek-V3.2" --into-existing meta_runs/new_deepseek-ai_DeepSeek-V3.2_no-reviewer_20260407_211506 --only 01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_ControlSystems_LQRGainSchedule,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon
```

- 将 **整套 c（11 题）** 合并进同一目录：

```powershell
python meta_benchmark/run_new_scenarios.py --provider silicon --model "deepseek-ai/DeepSeek-V3.2" --into-existing meta_runs/new_deepseek-ai_DeepSeek-V3.2_no-reviewer_20260407_211506 --only 01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge
```

- 跑完后可删除占位孤儿目录：`...002436`、 `...002437`（避免与 canonical 混淆）。

### 2）GLM-5 — letter **a** 已满；**b / c 需各整批 11 题**

- **Canonical**：`meta_runs\new_Pro_zai-org_GLM-5_no-reviewer_20260407_211651`。

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"
python meta_benchmark/run_new_scenarios.py --provider silicon --model "Pro/zai-org/GLM-5" --into-existing meta_runs/new_Pro_zai-org_GLM-5_no-reviewer_20260407_211651 --only 01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_ControlSystems_LQRGainSchedule,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,10b_Geophysics_MicroseismicBrief,11b_Logistics_MultiWMSInventoryRecon

python meta_benchmark/run_new_scenarios.py --provider silicon --model "Pro/zai-org/GLM-5" --into-existing meta_runs/new_Pro_zai-org_GLM-5_no-reviewer_20260407_211651 --only 01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge
```

- 跑完后可删除占位孤儿：`...225140`、 `...225141`。

### 3）Kimi-K2.5 — 需补跑（Fail 题）

**Letter a** 批次 `new_Pro_moonshotai_Kimi-K2.5_no-reviewer_20260407_213322`：7 题 `Fail`，需重跑：

`02a_SymbolicPatternReasoning_LabelNoiseCeiling,03a_RecommendationSystem_RecSysV2LaunchEvaluation,04a_RareEvent_ClassificationKPI,05a_SocialScience_InterviewThematicAnalysis,06a_RetailAnalytics_AdSpendStoreSales,08a_StructuralHealth_SensorVibrationPanel,11a_DataScience_TelemetryExportMergeReport`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"
python meta_benchmark/run_new_scenarios.py --provider silicon --model "Pro/moonshotai/Kimi-K2.5" --into-existing meta_runs/new_Pro_moonshotai_Kimi-K2.5_no-reviewer_20260407_213322 --only 02a_SymbolicPatternReasoning_LabelNoiseCeiling,03a_RecommendationSystem_RecSysV2LaunchEvaluation,04a_RareEvent_ClassificationKPI,05a_SocialScience_InterviewThematicAnalysis,06a_RetailAnalytics_AdSpendStoreSales,08a_StructuralHealth_SensorVibrationPanel,11a_DataScience_TelemetryExportMergeReport
```

**Letter b** 批次 `new_Pro_moonshotai_Kimi-K2.5_no-reviewer_20260407_222651`：9 题 `Fail`，需重跑：

`01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_ControlSystems_LQRGainSchedule,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"
python meta_benchmark/run_new_scenarios.py --provider silicon --model "Pro/moonshotai/Kimi-K2.5" --into-existing meta_runs/new_Pro_moonshotai_Kimi-K2.5_no-reviewer_20260407_222651 --only 01b_ComputationalLinguistics_MorphologicalSegmentationSuite,02b_FinancialML_CreditDefaultSPR,03b_HealthInformatics_EDTriageModelLaunch,04b_ControlSystems_LQRGainSchedule,05b_Genomics_VariantCallingPipeline,06b_PublicHealth_AirPollutionClinicPanel,07b_MaterialsScience_NanoparticleSynthSOP,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling
```

**Letter c**：当前无 11 目录批次（仅孤儿 `...231905` 含 `01c_*`）。任选其一：

- **新建独立批次目录**（与其它 letter 并列）：

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"
python meta_benchmark/run_new_scenarios.py --letter c --provider silicon --model "Pro/moonshotai/Kimi-K2.5"
```

- **合并进已有 letter a 目录**（不冲掉 a 的结果，因带 `--only` 全 11 个 c）：

```powershell
python meta_benchmark/run_new_scenarios.py --provider silicon --model "Pro/moonshotai/Kimi-K2.5" --into-existing meta_runs/new_Pro_moonshotai_Kimi-K2.5_no-reviewer_20260407_213322 --only 01c_BiomedicalImaging_CellBenchmarkPicker,02c_AstroML_VariableStarClassification,03c_RLPolicy_RobotPickPlaceComparison,04c_NumericalPDE_PorousMediumTravelingWave,05c_CyberSecurity_IncidentNarrativeTriage,06c_AgEcon_IrrigationYieldPanel,07c_ClinicalOps_ColdChainShipmentProtocol,08c_Oceanography_CTDCruiseStations,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel,11c_DigitalHumanities_MuseumProvenanceMerge
```

（若希望 **abc 共 33 题同一 `run_id`**，还需把 letter **b** 的 11 题以同样方式 `--into-existing` 合并进所选目录，或在该目录对 b 整批重跑一遍。）

### 4）Qwen3.5-397B-A17B — 三批均为 `Error`（建议整批重试）

可对 **a / b / c** 分别合并回对应已有目录（覆盖同 `scenario_id` 行）：

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"
# letter a
python meta_benchmark/run_new_scenarios.py --letter a --provider silicon --model "Qwen/Qwen3.5-397B-A17B" --into-existing meta_runs/new_Qwen_Qwen3.5-397B-A17B_no-reviewer_20260407_211635
# letter b
python meta_benchmark/run_new_scenarios.py --letter b --provider silicon --model "Qwen/Qwen3.5-397B-A17B" --into-existing meta_runs/new_Qwen_Qwen3.5-397B-A17B_no-reviewer_20260407_215657
# letter c
python meta_benchmark/run_new_scenarios.py --letter c --provider silicon --model "Qwen/Qwen3.5-397B-A17B" --into-existing meta_runs/new_Qwen_Qwen3.5-397B-A17B_no-reviewer_20260407_222631
```

---

## 更新审题人登记表 xlsx

批次目录稳定后，在仓库根目录执行（**会覆盖** `docs/AI_scientist_审题人登记表.xlsx`，请先备份）：

```powershell
python scripts/generate_reviewer_register_xlsx.py
```
