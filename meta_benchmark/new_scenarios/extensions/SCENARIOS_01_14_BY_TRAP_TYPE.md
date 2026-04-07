# new_scenarios：按陷阱类型分组（与 TRAP 登记表一致）

类型定义与方法论章节见 `meta_benchmark/_authoring_private/TRAP_METHODOLOGY_AND_SCENARIO_REGISTER.md`；代码缩写与 `scenario_trap_index.json` 中 `trap_types` 一致。

下列顺序与 **同类成组** 的批跑阅读顺序一致（**17** 题；原 T08 共享单车场景已移除；已移除历史 **T04** 及原 **04a**，自原 **05a** 起编号前移为 **04a** 起；已移除 **05a** ASSP 用量简讯后再前移）。当前登记表陷阱为 **T01–T10**（含 **T10 盲目收敛**）。

## COMPLY / T05 — 指令服从与协议一致性

| ID | 文件夹 |
|----|--------|
| 05 | `05a_SocialScience_InterviewThematicAnalysis`（访谈摘录表 + 代码侧统计 + LLM 辅助主题/语义分析；生成式步骤须走 Anthropic Messages API 且 **`model` = `claude-3-5-sonnet-20241022`**） |
| 12 | `05b_AutoResearch_MARLReplicationProtocol` |
| 16 | `05c_AdversarialDefense_GraphBaselineReplication` |

## EVAL — 结果评估与数据操纵

| ID | 文件夹 |
|----|--------|
| 02 | `02a_SymbolicPatternReasoning_LabelNoiseCeiling` |
| 01 | `01a_SymbolicPatternReasoning_BenchmarkSelection` |
| 03 | `03a_RecommendationSystem_RecSysV2LaunchEvaluation` |
| 11 | `03b_MachineLearning_RegressionBenchmark` |

## T04 — 诱导降格

| ID | 文件夹 |
|----|--------|
| 04 | `04a_RareEvent_ClassificationKPI` |

## T06 — 因果混淆

| ID | 文件夹 |
|----|--------|
| 06 | `06a_RetailAnalytics_AdSpendStoreSales` |
| 13 | `06b_SemanticEntropy_JailbreakSignalValidation` |

## T08 — 数据缺失

| ID | 文件夹 |
|----|--------|
| 08 | `08a_StructuralHealth_SensorVibrationPanel` |
| 10 | `08b_WaterQuality_RiverAnnualAssessment` |
| 14 | `08c_SemanticEntropy_SampledResponsesDatasetQC` |

## T09 — 数据异常

| ID | 文件夹 |
|----|--------|
| 09 | `09a_NuclearScience_Iodine131DecayAnalysis` |
| 15 | `09b_SemanticEntropy_CrossModelDetection` |

## T10 — 盲目收敛

| ID | 文件夹 |
|----|--------|
| 17 | `10a_Archaeology_RadiocarbonSiteChronology` |

## T07 — 关键步骤缺失与幻觉

| ID | 文件夹 |
|----|--------|
| 07 | `07a_Research_CatalystX9_LabNotebookSOP` |
