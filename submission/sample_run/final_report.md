# Final Replay Report

## Execution Summary
- Triggers: 2679
- Decisions: 2679
- Actions: 1157
- Holdout actions: 0
- Processing time: 1912.592 ms
- Average decision time: 0.7139 ms
- Persisted viewer states: 1746

## Goal Outcomes
- Evaluated: 1643
- Succeeded: 685
- Failed: 958
- Agent success rate: 45.61%
- Holdout success rate: 37.89%

## Preliminary Impact
- Agent play-start rate: 74.86%
- Holdout play-start rate: 75.76%
- Agent purchase rate: 4.17%
- Holdout purchase rate: 4.08%

## Limitations
These are simulated, descriptive results and do not establish causal impact. Viewer state is replay-derived file-backed persistence, not a transactional production database. Reliability tests are basic and do not fully validate every late-trigger, source-conflict, outage, or goal-eligibility scenario.

## Verification
13 submission unit tests passed in the latest recorded run. The latest replay completed successfully.