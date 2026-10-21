# Final Replay Report

## Execution Summary
- Triggers processed: 2,679
- Decisions recorded: 2,679
- Published actions: 1,060
- Holdout actions: 0
- Users receiving actions: 699
- Persisted viewer states: 1,746
- Simulator outcome events: 31,469
- Replay processing time: 1971.023 ms total.
- Average decision latency: 0.7357 ms (replay-reported average).

## Goal-Specific Outcome Attribution
- Goal assignments evaluated: 1,504
- Succeeded: 677
- Failed: 827
- Agent assignments: 748
- Agent successes: 365
- Agent success rate: 48.80%
- Holdout assignments: 756
- Holdout successes: 312
- Holdout success rate: 41.27%
- Descriptive difference: +7.53 percentage points in favor of the agent arm.
- G10 excluded because the assignment defines no measurable success event.
- G03 uses the corrected rule: `play_started` on a later IST calendar day.

These results are descriptive goal attribution and do not establish that the agent caused the observed difference.

## Preliminary Event-Level Impact
| Metric | Agent | Holdout | Difference (agent - holdout) | 95% confidence interval for difference |
|---|---:|---:|---:|---:|
| Users with play started | 74.86% | 75.76% | -0.90 percentage points | [-4.96, +3.14] percentage points |
| Users with purchase completed | 4.17% | 4.08% | +0.09 percentage points | [-1.80, +2.00] percentage points |

Both confidence intervals include zero. This event-level comparison does not show a clear difference between the rates. These simulated outcomes depend on the simulator seed and do not establish causal uplift.

## Reliability and Verification
- Submission test suite: 54 tests passed in the latest run.
- Independent verifier is applied before replay actions are accepted.
- Duplicate-trigger handling and stale-trigger abstention are implemented.
- Actions are not generated for holdout users.
- Title selection is filtered by dialect and current availability.
- Missing or unsupported dialects result in abstention rather than an unsupported dialect guess.

## Limitations
- Results are simulated and descriptive, not proof of causal impact.
- Confidence intervals quantify sampling uncertainty under the binary-outcome model; they do not correct data-quality issues, bias, or faulty randomization.
- Viewer state is replay-derived file-backed persistence, not a transactional production database.
- The baseline generates home-page actions only; push and WhatsApp delivery are not enabled.
- Some reliability scenarios need deeper integration testing, including real dependency failures, source-conflict resolution, and end-to-end goal eligibility.
- The goal-specific and event-level reports use different outcome definitions and should not be interpreted as interchangeable metrics.

## Reproducibility
Run commands from the project root using the active virtual environment. See `submission/README.md` for replay, simulation, evaluation, impact-report, and test commands.

## Replay latency

Measured 2,679 individual replay decisions.

- Average: 0.6918 ms
- p95: 2.2979 ms
- p99: 4.6912 ms
- Minimum: 0.0074 ms
- Maximum: 9.6747 ms

These figures measure local per-decision replay processing time only. They are **not end-to-end production latency** and do not include external-service response times. The replay-summary average may differ slightly from the mean of individually recorded decision timings.

See `latency_report.json` for the machine-readable report.
