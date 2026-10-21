# Final Replay and Validation Report

## Execution summary

- Dataset pack: `one_user_one_agent_pack`
- Triggers processed: 2,679
- Decisions recorded: 2,679
- Actions created: 1,060
- Abstentions: 521
- Holdout decisions: 1,098
- Holdout actions: 0
- Profiles loaded: 4,858
- Experiment arms loaded: 5,000
- Catalogue titles loaded: 2,014
- Goal rules loaded: 12
- Missing profiles: 192
- Unknown experiment arms: 0
- Withdrawn titles encountered: 1
- Goal-rule corrections encountered: 1
- Replay processing time: 3,034.788 ms
- Average decision time in replay summary: 1.1328 ms

## Decision latency

Measured from the generated decision records:

| Metric | Latency |
|---|---:|
| Minimum | 0.0074 ms |
| Average | 0.6918 ms |
| p95 (nearest-rank) | 2.2979 ms |
| p99 (nearest-rank) | 4.6912 ms |
| Maximum | 9.6747 ms |

The replay summary and latency report use different timing measurements. The latency figures are local per-decision processing measurements, not end-to-end production latency.

## Goal-specific outcome attribution

- Assignments evaluated: 1,504
- Overall successes: 677
- Overall failures: 827
- Agent assignments: 748; successes: 365; success rate: 48.80%
- Holdout assignments: 756; successes: 312; success rate: 41.27%
- Goal rule G10 excluded because it has no measurable success event.
- Goal rule G03 uses the corrected `play_started` event on a later IST calendar day.

These results are descriptive. They do not establish that the agent caused the difference in goal-success rates.

## Agent-versus-holdout event comparison

- Play-started user rate: agent 74.86%; holdout 75.76%; difference -0.90 percentage points; 95% CI [-4.96, +3.14].
- Purchase-completed user rate: agent 4.17%; holdout 4.08%; difference +0.09 percentage points; 95% CI [-1.80, +2.00].

Both confidence intervals include zero. Do not claim causal uplift.

## Safety and reliability observations

The replay report states that generated home-page actions pass the independent verifier, holdout actions are not created, and stale triggers older than the configured 86,400-second limit are abstained. The test suite covers duplicate events and triggers, dialect conflicts, consent, verifier rules, prompt injection, goal deadlines, corrected goal rules, dependency-failure reporting, timestamp handling, and persisted viewer state.

## Limitations

- Replay and outcome results are simulated/local, not production evidence.
- Average decision latency and replay wall time are different measurements.
- Event-level comparisons and goal-success rates are descriptive, not causal estimates.
- The baseline does not generate push or WhatsApp messages.
- Missing profiles and unresolved evidence require conservative handling.
- Production-scale throughput, end-to-end latency, and recovery behavior require deployment-level validation.

See `ARCHITECTURE.md`, `AI_COLLABORATION.md`, and `KNOWN_LIMITATIONS.md` for design and implementation context.
