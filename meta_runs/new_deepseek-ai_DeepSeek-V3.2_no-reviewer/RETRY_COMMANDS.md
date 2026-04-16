# 待补跑 / 重跑说明

## 题面更新后整批重跑（推荐）

以下 **8** 题已改过 `task_info.json`（中性题面、无额外 md 点名、04a 自建 TSI / 不复制 `utils/` 等）。用 `--into-existing` **覆盖**同目录下对应 `scenario_id` 的 `inner_results_r001.json` 行与工作区。

**场景列表（一条 `--only`，逗号分隔、无空格）：**

`04a_RareEvent_ClassificationKPI,04b_ControlSystems_LQRGainSchedule,04c_NumericalPDE_PorousMediumTravelingWave,08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "04a_RareEvent_ClassificationKPI,04b_ControlSystems_LQRGainSchedule,04c_NumericalPDE_PorousMediumTravelingWave,08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel"

python meta_benchmark/run_new_scenarios.py --provider silicon --model "deepseek-ai/DeepSeek-V3.2" --inner-max-steps 80 --into-existing meta_runs/new_deepseek-ai_DeepSeek-V3.2_no-reviewer --only $only
```

---

## 历史 Error 仅补跑（可选）

若只补之前失败、不跑整批 8 题，可用。当前 **`inner_results_r001.json` 中 status=Error 共 7 题**：

`04a_RareEvent_ClassificationKPI,04b_ControlSystems_LQRGainSchedule,04c_NumericalPDE_PorousMediumTravelingWave,08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,09c_Ecology_SpeciesAreaIsland`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "04a_RareEvent_ClassificationKPI,04b_ControlSystems_LQRGainSchedule,04c_NumericalPDE_PorousMediumTravelingWave,08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,09c_Ecology_SpeciesAreaIsland"

python meta_benchmark/run_new_scenarios.py --provider silicon --model "deepseek-ai/DeepSeek-V3.2" --inner-max-steps 80 --into-existing meta_runs/new_deepseek-ai_DeepSeek-V3.2_no-reviewer --only $only
```

审计时间：**2026-04-16（复查）**——仍为上述 **7** 题 `Error`，`$only` 与列表无需改动。（`round_001/outer_workspace/inner_results_r001.json` 以本机为准。）
