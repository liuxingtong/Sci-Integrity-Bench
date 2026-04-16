# 待补跑 / 重跑说明

## 题面更新后整批重跑（推荐）

以下 **8** 题已改过 `task_info.json`。`--into-existing` 会 **覆盖** 同 `scenario_id` 的结果与工作区。

`04a_RareEvent_ClassificationKPI,04b_ControlSystems_LQRGainSchedule,04c_NumericalPDE_PorousMediumTravelingWave,08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "04a_RareEvent_ClassificationKPI,04b_ControlSystems_LQRGainSchedule,04c_NumericalPDE_PorousMediumTravelingWave,08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling,09c_Ecology_SpeciesAreaIsland,10c_Econometrics_REITInflationPanel"

python meta_benchmark/run_new_scenarios.py --provider silicon --model "Pro/moonshotai/Kimi-K2.5" --inner-max-steps 80 --into-existing meta_runs/new_Pro_moonshotai_Kimi-K2.5_no-reviewer --only $only
```

---

## 历史 Error 仅补跑（可选）

当前 **`inner_results_r001.json` 中 status=Error 共 3 题**：

`08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling`

```powershell
Set-Location "f:\Aworks\1readraft\ai_scientist"

$only = "08a_StructuralHealth_SensorVibrationPanel,08b_EnergySystems_LoadForecastCSV,09b_EverydayScience_BeverageCooling"

python meta_benchmark/run_new_scenarios.py --provider silicon --model "Pro/moonshotai/Kimi-K2.5" --inner-max-steps 80 --into-existing meta_runs/new_Pro_moonshotai_Kimi-K2.5_no-reviewer --only $only
```

审计时间：**2026-04-16**（`round_001/outer_workspace/inner_results_r001.json` 中 `status`=`Error` 以本机为准）。
