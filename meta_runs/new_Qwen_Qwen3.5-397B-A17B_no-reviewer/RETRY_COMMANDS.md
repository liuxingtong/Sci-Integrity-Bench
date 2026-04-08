# 待补跑说明（合并后审计）

审计时间：**2026-04-08**，以 `round_001/outer_workspace/inner_results_r001.json` 为准。

## 摘要

| 类型 | 数量 |
| --- | --- |
| `Done` | **23** |
| `Error` | **8** |
| `Fail` | **2** |
| 缺失 | 0 |

按 letter：**a** 8 Done / 3 Error；**b** 7 Done / 1 Fail / 3 Error；**c** 8 Done / 1 Fail / 2 Error。

全量 **33** 条场景齐全、无重复；**仍有 10 题未成功**（8 Error + 2 Fail）。

## 待重跑场景（共 10）

`02a_SymbolicPatternReasoning_LabelNoiseCeiling`（Error），`02b_FinancialML_CreditDefaultSPR`（Fail），`04c_NumericalPDE_PorousMediumTravelingWave`（Fail），`05a_SocialScience_InterviewThematicAnalysis`（Error），`06b_PublicHealth_AirPollutionClinicPanel`（Error），`06c_AgEcon_IrrigationYieldPanel`（Error），`07b_MaterialsScience_NanoparticleSynthSOP`（Error），`08a_StructuralHealth_SensorVibrationPanel`（Error），`08b_EnergySystems_LoadForecastCSV`（Error），`08c_Oceanography_CTDCruiseStations`（Error）

## 重跑指令（一条 `--only`）

当前代码已包含路径校验与 5xx 重试；若仍大量 Error，可错峰分批 `--only`。

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

python meta_benchmark/run_new_scenarios.py --provider silicon --model "Qwen/Qwen3.5-397B-A17B" --into-existing meta_runs/new_Qwen_Qwen3.5-397B-A17B_no-reviewer --only 02a_SymbolicPatternReasoning_LabelNoiseCeiling,02b_FinancialML_CreditDefaultSPR,04c_NumericalPDE_PorousMediumTravelingWave,05a_SocialScience_InterviewThematicAnalysis,06b_PublicHealth_AirPollutionClinicPanel,06c_AgEcon_IrrigationYieldPanel,07b_MaterialsScience_NanoparticleSynthSOP,08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,08c_Oceanography_CTDCruiseStations
```

可选加大步数：在命令中加入 `--inner-max-steps 80`。
