# Impact Report

## Scope
Preliminary event-level comparison; not goal success attribution

This report summarizes the existing simulated results. Differences are descriptive and do not establish causal impact.

## Event-level comparison

| Metric | Agent | Holdout | Difference (agent - holdout) |
|---|---:|---:|---:|
| Triggered users | 863 | 883 | ? |
| Users with play started | 646 | 669 | ? |
| Play user rate | 0.7486 | 0.7576 | -0.0090 |
| Users with purchase completed | 36 | 36 | ? |
| Purchase user rate | 0.0417 | 0.0408 | +0.0009 |

## Goal-specific attribution

| Metric | Agent | Holdout |
|---|---:|---:|
| Assigned goals | 809 | 834 |
| Succeeded | 369 | 316 |
| Failed | 440 | 518 |
| Success rate among assignments | 0.4561 | 0.3789 |

The observed goal-success rate difference is descriptive only. Eligibility and goal attribution still require validation.

## Replay summary

- Triggers: 2679
- Decisions: 2679
- Actions created: 1157
- Holdout decisions: 1234
- Abstentions: 288
- Holdout actions created: 0

## Limitations

- Outcomes are simulated and depend on the simulator seed.
- The event-level report does not establish goal-specific success or causal uplift.
- Validate holdout isolation and goal attribution before making impact claims.
- Percentile latency measurements were not available in the recorded replay report.
