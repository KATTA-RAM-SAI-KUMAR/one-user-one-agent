# Final Replay Report

Generated from the existing local sample reports.

## Execution summary

- Pack: one_user_one_agent_pack
- Trigger count: 2679
- Decisions recorded: 2679
- Actions created: 1157
- Abstentions: 288
- Holdout decisions: 1234
- Holdout actions created: 0
- Processing elapsed: 1897.378 ms
- Average decision time: 0.7082 ms

## Outcome summary

- Goal assignments evaluated: 1643
- Goal successes: 685
- Goal failures: 958
- Agent goal success rate: 0.4561
- Holdout goal success rate: 0.3789

## Interpretation

These are local replay and simulation results, not production results. The goal-success rates and event-level differences are descriptive and do not demonstrate causal uplift.

## Outstanding validation

1. Add dedicated tests for late triggers, conflicting sources, tool/dependency failures, and corrected goal rules.
2. Validate goal eligibility and attribution against every applicable assignment rule.
3. Verify state persistence, recovery, and required safety controls.
4. Capture latency percentiles if required.
5. Rerun tests and replay after any implementation changes.

See `ARCHITECTURE.md` and `KNOWN_LIMITATIONS.md` for additional context.
