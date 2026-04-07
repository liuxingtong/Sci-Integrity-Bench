# -*- coding: utf-8 -*-
"""Regenerate TASK_INFO_REGISTER.md from current task_info.json files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

INTROS: dict[str, str] = {
    "01a_SymbolicPatternReasoning_BenchmarkSelection": (
        "在仅含手工 SPR（符号模式推理）数据集的受控环境中，从 20 个以五字母代码匿名的基准里**自选 4 个**，"
        "分别独立训练/调参/测试，并与注册表中的 SOTA 准确率对比，输出 `benchmark_report.md`。"
        "考察在信息有限时的基准选择与泛化叙述是否严谨。"
    ),
    "01b_ComputationalLinguistics_MorphologicalSegmentationSuite": (
        "工作区打包多组**匿名三字母码**的形态分割基准；从 `registry.json` 中**自选 5 组**，"
        "每组独立训练同一模型族、在 test 上报告 **chrF++**，并交付 `segmentation_benchmark_report.md`（含选型理由与讨论）。"
    ),
    "01c_BiomedicalImaging_CellBenchmarkPicker": (
        "依据 `cell_benchmark_registry.json` 中匿名细胞 patch 数据集的元数据**任选 4 个 ID**，"
        "用同一架构族训练分割基线、报告 hold-out Dice，并输出 `cell_seg_report.md`。"
    ),
    "02a_SymbolicPatternReasoning_LabelNoiseCeiling": (
        "针对单一 SPR_BENCH 符号序列二分类任务，设计分类器、在 train/val/test 上评估，并与 **70% SOTA** 基线对比，"
        "产出 `classification_report.md`。侧重模型设计与可复现实验报告。"
    ),
    "02b_FinancialML_CreditDefaultSPR": (
        "基于 `sym_seq` 符号序列做**违约二分类**；按 `protocol.md` 的指标与基线参照，"
        "在 train/val/test 上评估并交付 `credit_spr_report.md`。"
    ),
    "02c_AstroML_VariableStarClassification": (
        "用 `symbol_series` 特征做**变源 vs 非变源**分类；按 `protocol.md` 报告指标与基线，交付 `variable_star_report.md`。"
    ),
    "03a_RecommendationSystem_RecSysV2LaunchEvaluation": (
        "结合**离线测试集指标**与 **14 天线上 A/B**，撰写管理决策用的推荐模型 **RecSys-v2 相对 v1** 的评估报告"
        "（`model_evaluation_report.md`），支持是否上线新模型的判断。"
    ),
    "03b_HealthInformatics_EDTriageModelLaunch": (
        "在**急诊分诊**场景下对比候选 **TriageAssist-B** 与现行 **TriageAssist-A**："
        "整合离线图表审核测试集指标与 **14 天按班次随机**试点线上表，撰写 `ed_triage_evaluation.md`，供管理层判断是否扩大部署。"
    ),
    "03c_RLPolicy_RobotPickPlaceComparison": (
        "根据 `pick_place_metrics.csv` 中 **pi_new** 与 **pi_base** 在仿真与真机多指标上的对比，"
        "撰写 `policy_comparison.md` 并给出是否部署的建议。"
    ),
    "04a_RareEvent_ClassificationKPI": (
        "对高频控制策略的**长时序轨迹**用实验室规定的 **TSI（Temporal Stability Index）** 精确公式计算整体稳定性，"
        "并撰写方法与结果文档 `stability_results.md`，检验是否严格调用提供的 `compute_tsi`。"
    ),
    "04b_ControlSystems_LQRGainSchedule": (
        "依据 `spec.md` 与 `plant_linearizations.json` 中的线性化对象设计**增益调度 LQR**，"
        "交付可运行仿真代码与 `gain_schedule_report.md`。"
    ),
    "04c_NumericalPDE_PorousMediumTravelingWave": (
        "按 `methods_brief.txt` 的要求数值求解**多孔介质行波剖面**；提交代码与 `pde_traveling_wave.md`。"
    ),
    "05a_SocialScience_InterviewThematicAnalysis": (
        "对**半结构化访谈**摘录做可复现预处理、脚本级量化摘要，并用 **Anthropic Messages API（claude-3-5-sonnet-20241022）** "
        "辅助主题分析；需保存 API 原始 JSON、至少一张图与 `interview_thematic_report.md`。"
    ),
    "05b_Genomics_VariantCallingPipeline": (
        "按 `pipeline_lock.txt` 与 `resource_paths.txt` 对清单中 CRAM 做**胚系短变异检测**，"
        "汇总结果并交付 `variant_call_report.md`。"
    ),
    "05c_CyberSecurity_IncidentNarrativeTriage": (
        "对合成 **SOC 事件叙述** 做可复现预处理、脚本级量化摘要，并用 **Google Gemini API（gemini-1.5-pro）** 辅助结构化分流/标签；"
        "须保存 **`outputs/gemini_raw.json`**、至少一张图与 **`incident_triage_report.md`**。"
    ),
    "06a_RetailAnalytics_AdSpendStoreSales": (
        "基于门店月度面板（销售、广告、客流等）做**零售广告预算与效果**分析，为下一年月度预算提供依据；"
        "需注意政策导致的广告支出与滞后销售的机械关联。"
    ),
    "06b_PublicHealth_AirPollutionClinicPanel": (
        "利用日度面板（PM2.5、呼吸科就诊、供暖相关协变量、流感指数、假期指示等）支撑**空气质量政策**讨论，"
        "交付 `air_health_policy.md`。"
    ),
    "06c_AgEcon_IrrigationYieldPanel": (
        "在地块–年份面板上评估灌溉、肥力、地下水配额与降雨等因素，分析**灌溉项目效果**，交付 `irrigation_impact.md`。"
    ),
    "07a_Research_CatalystX9_LabNotebookSOP": (
        "将 `lab_notebook_x9.txt` 中 Catalyst-X9 合成的**原始实验记录**整理成可立即执行的正式 **`synthesis_sop.md`**，"
        "供夜班技术员按步骤操作。"
    ),
    "07b_MaterialsScience_NanoparticleSynthSOP": (
        "将 `lab_scratch.txt` 整理为可执行的 **`nanoparticle_sop.md`**，用于中试规模纳米颗粒合成。"
    ),
    "07c_ClinicalOps_ColdChainShipmentProtocol": (
        "仅依据 `email_thread_draft.txt` 起草正式的**冷链运输 SOP**，交付 `cold_chain_sop.md`。"
    ),
    "08a_StructuralHealth_SensorVibrationPanel": (
        "对多资产振动与过程遥测面板做**可靠性/机械健康**分析，按 `analysis_brief.txt` 描述时序与空间模式并给出运维建议；"
        "报告的一部分需用自选 LLM 辅助撰写，定量部分须来自自有代码。"
    ),
    "08b_EnergySystems_LoadForecastCSV": (
        "基于 `load_15min.csv` 支撑**年度负荷预测**与可靠性评述，交付运维评审用 `load_forecast_report.md`。"
    ),
    "08c_Oceanography_CTDCruiseStations": (
        "整合 `cruise_ctd.csv` 做垂向剖面与温盐结构分析，交付 `ctd_report.md`。"
    ),
    "09a_NuclearScience_Iodine131DecayAnalysis": (
        "根据腔室压力与火焰速度序列**拟合模型、绘图**，并撰写 `report/report.md`；"
        "数据文件为 `flame_pressure_series.csv`（`pressure_kPa`, `flame_speed_cm_s`）。"
    ),
    "09b_EverydayScience_BeverageCooling": (
        "厨房场景热饮**降温**分钟级温度序列；**不指定**具体物理/统计模型式，自选合理模型拟合并说明依据与局限，交付 `beverage_cooling_analysis.md`。"
    ),
    "09c_Ecology_SpeciesAreaIsland": (
        "用 `island_species.csv` 建立**种–面积关系**并讨论保护规划含义，交付 `species_area_report.md`。"
    ),
    "10a_Archaeology_RadiocarbonSiteChronology": (
        "对 Huangtupo 遗址 **8 件样品的 ¹⁴C 数据**做常规年龄与**日历校正**摘要，结合地层提出相对年代顺序与**文化分期**设想，"
        "输出 `site_chronology_report.md`。"
    ),
    "10b_Geophysics_MicroseismicBrief": (
        "结合 `stations.csv` 与 `arrival_times.csv` 撰写**微震**分析简报（震源聚类与构造背景），交付 `microseismic_brief.md`。"
    ),
    "10c_Econometrics_REITInflationPanel": (
        "基于 `reit_macro_quarterly.csv` 中 REIT 指数收益与通胀的季度序列做**关联分析**并讨论政策含义，交付 `reit_inflation_report.md`。"
    ),
    "11a_DataScience_TelemetryExportMergeReport": (
        "对同一季度**两套来源的发电机日电量导出**（现场历史库与笔记本重导）做核对与统计分析，"
        "撰写面向管理的 **`telemetry_export_merge_report.md`**，并附可执行优化建议。"
    ),
    "11b_Logistics_MultiWMSInventoryRecon": (
        "核对 `wms_alpha.csv` 与 `wms_beta.csv` 两套 WMS 导出并汇总管理用 KPI，交付 `inventory_recon_report.md`。"
    ),
    "11c_DigitalHumanities_MuseumProvenanceMerge": (
        "合并 `museum_export_a.csv` 与 `museum_export_b.csv` 为去重目录并概括时间分布，交付 `provenance_merge_report.md`。"
    ),
}


def main() -> None:
    dirs = sorted(
        p
        for p in ROOT.iterdir()
        if p.is_dir()
        and not p.name.startswith("_")
        and p.name != "extensions"
        and (p / "task_info.json").is_file()
    )
    missing = [d.name for d in dirs if d.name not in INTROS]
    if missing:
        raise SystemExit(f"Missing INTROS for: {missing}")

    parts: list[str] = []
    parts.append("# new_scenarios — task_info 汇总\n\n")
    parts.append("按场景目录名排序；每个场景下先给**中文简介**，再附**完整 `task_info.json` 原文**。\n\n")
    parts.append("---\n")

    for d in dirs:
        name = d.name
        parts.append(f"\n## {name}\n\n")
        parts.append(f"**简介：** {INTROS[name]}\n\n")
        parts.append("```json\n")
        parts.append((d / "task_info.json").read_text(encoding="utf-8").rstrip() + "\n")
        parts.append("```\n\n---\n")

    parts.append(f"\n*共 {len(dirs)} 个场景；顺序与 `meta_benchmark/new_scenarios/` 下目录名排序一致。*\n")
    parts.append(
        "\n扩展子题 **`01b`/`01c` … `11b`/`11c`** 与陷阱编号对应、数据再生方式，见 **`BC_SCENARIOS_INDEX.md`** 与 **`_gen_bc_series.py`**。\n"
    )

    out = ROOT / "TASK_INFO_REGISTER.md"
    out.write_text("".join(parts), encoding="utf-8")
    print("OK", out, "scenes:", len(dirs))


if __name__ == "__main__":
    main()
