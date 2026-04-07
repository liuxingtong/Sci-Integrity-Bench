"""Regenerate meta_benchmark/_authoring_private/scenario_trap_index.json (18 scenarios).

Replaces `scenarios`, `recommended_run_order`, and `a_series_benchmark_map`.
Preserves `trap_types`, `appendix`, and `a_series_subunits` (including `related_scenarios`).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "_authoring_private"
p = ROOT / "scenario_trap_index.json"
d = json.loads(p.read_text(encoding="utf-8"))

scenarios = [
    {"id": "01", "folder": "01a_SymbolicPatternReasoning_BenchmarkSelection", "trap": "T01"},
    {"id": "02", "folder": "02a_SymbolicPatternReasoning_LabelNoiseCeiling", "trap": "T02"},
    {"id": "03", "folder": "03a_RecommendationSystem_RecSysV2LaunchEvaluation", "trap": "T03"},
    {"id": "04", "folder": "04a_RareEvent_ClassificationKPI", "trap": "T05"},
    {"id": "05", "folder": "05a_SocialScience_InterviewThematicAnalysis", "trap": "T05"},
    {"id": "06", "folder": "06a_RetailAnalytics_AdSpendStoreSales", "trap": "T06"},
    {"id": "07", "folder": "07a_Research_CatalystX9_LabNotebookSOP", "trap": "T07"},
    {"id": "08", "folder": "08a_StructuralHealth_SensorVibrationPanel", "trap": "T08"},
    {"id": "09", "folder": "09a_NuclearScience_Iodine131DecayAnalysis", "trap": "T09"},
    {"id": "10", "folder": "08b_WaterQuality_RiverAnnualAssessment", "trap": "T08"},
    {"id": "11", "folder": "03b_MachineLearning_RegressionBenchmark", "trap": "T03"},
    {"id": "12", "folder": "05b_AutoResearch_MARLReplicationProtocol", "trap": "T07", "literature": "A.1 MARL-1"},
    {"id": "13", "folder": "06b_SemanticEntropy_JailbreakSignalValidation", "trap": "T06", "literature": "A.2 SE-1"},
    {"id": "14", "folder": "08c_SemanticEntropy_SampledResponsesDatasetQC", "trap": "T08", "literature": "A.3 SE-2"},
    {"id": "15", "folder": "09b_SemanticEntropy_CrossModelDetection", "trap": "T09", "literature": "A.4 SE-3"},
    {"id": "16", "folder": "05c_AdversarialDefense_GraphBaselineReplication", "trap": "T07"},
    {"id": "17", "folder": "10a_Archaeology_RadiocarbonSiteChronology", "trap": "T10"},
    {"id": "18", "folder": "11a_DataScience_TelemetryExportMergeReport", "trap": "T11"},
]

d["scenarios"] = scenarios

d["recommended_run_order"] = [
    "05",
    "12",
    "16",
    "01",
    "11",
    "02",
    "03",
    "04",
    "15",
    "06",
    "13",
    "14",
    "07",
    "08",
    "10",
    "09",
    "17",
    "18",
]
d["a_series_benchmark_map"] = {
    "A.1_MARL-1": "12",
    "A.2_SE-1": "13",
    "A.3_SE-2": "14",
    "A.4_SE-3": "15",
}

p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("OK", len(d["scenarios"]), "scenarios")
