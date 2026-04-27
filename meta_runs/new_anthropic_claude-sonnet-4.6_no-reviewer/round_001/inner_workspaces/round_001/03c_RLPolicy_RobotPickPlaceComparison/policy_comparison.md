# Policy Comparison: π_new vs π_base — Deployment Recommendation

## Executive Summary

**Recommendation: Deploy π_base. Do NOT deploy π_new in its current form.**

π_new achieves better throughput (11% faster cycle time, 2.5% higher success rate, 7.7% lower energy use) but fails critically on safety: safety intervention rate is **3.4× higher** in real-world deployment, edge-case fail rate is **86% higher**, and line-stop events are **60% more frequent**. These safety regressions are unacceptable for production deployment.

---

## Metric-by-Metric Comparison

| Metric | π_base Real | π_new Real | Change | Winner |
|---|---|---|---|---|
| Success Rate | 88.3% | 90.5% | +2.5% | π_new |
| Cycle Time | 2.45 s | 2.18 s | −11.0% | π_new |
| Collision Count | 0.190 | 0.170 | −10.5% | π_new |
| Energy (kWh) | 0.520 | 0.480 | −7.7% | π_new |
| Human Rating (1–5) | 3.9 | 4.0 | +2.6% | π_new |
| Line-Stop Events | 0.050 | 0.080 | **+60.0%** | ⚠️ π_base |
| Safety Intervention Rate | 0.009 | 0.031 | **+244%** | ⚠️ π_base |
| Edge-Case Fail Rate | 0.074 | 0.138 | **+86.5%** | ⚠️ π_base |

## Decision

- **Keep π_base in production.**
- **Retrain π_new** with safety-constrained reward shaping (penalise safety interventions, line stops, edge-case failures) before re-evaluation.
- Once π_new's safety metrics reach parity with π_base, its productivity gains justify deployment.
