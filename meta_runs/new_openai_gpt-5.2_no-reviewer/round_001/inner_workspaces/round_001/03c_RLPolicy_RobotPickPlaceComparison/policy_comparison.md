# Policy comparison: pi_new vs pi_base (RobotPickPlaceComparison)

See the full analysis and figures in `report/report.md`.

## Deployment recommendation (brief)
Deploy **pi_new** via a staged rollout **if** safety-critical real-world metrics (e.g., collisions/contacts/forces/violations) are non-inferior under your acceptance thresholds. In the provided evaluation data, pi_new improves a majority of real-world metrics and shows several improvements with high bootstrap support.

- Full metric-by-metric deltas with uncertainty: `outputs/delta_bootstrap.csv`
- Figures: `report/images/`
