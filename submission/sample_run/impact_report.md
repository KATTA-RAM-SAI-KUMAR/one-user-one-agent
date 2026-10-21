# Agent vs Holdout Impact Report

**Scope:** Preliminary event-level comparison; not goal success attribution

## Results

| Metric | Agent | Holdout | Difference (Agent - Holdout) | 95% confidence interval |
|---|---:|---:|---:|---:|
| Play-started user rate | 74.86% | 75.76% | -0.90% | [-4.96%, +3.14%] |
| Purchase-completed user rate | 4.17% | 4.08% | +0.09% | [-1.80%, +2.00%] |

## Sample sizes

- Triggered users: 1746
- Decision rows: 2679
- Published actions: 1060
- Users receiving actions: 699
- Agent users: 863
- Holdout users: 883

## Interpretation and limitations

- Both 95% confidence intervals include zero; this analysis does not show a clear difference between agent and holdout rates.
- Outcomes are simulated and depend on the simulator seed.
- Confidence intervals quantify sampling uncertainty; they do not correct data-quality issues or bias.
- These event-level metrics do not establish goal-specific success.
- Do not claim causal uplift without validating randomization, assignment integrity, outcome attribution, and holdout isolation.

## Source

Generated from `impact_report.json` using the current replay and simulation outputs.
