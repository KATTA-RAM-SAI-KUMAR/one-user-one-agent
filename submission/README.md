# STAGE — One User, One Agent

## Overview

A deterministic, replay-based agent prototype that evaluates viewer triggers, selects measurable goals from available evidence, filters content by dialect and availability, and validates proposed actions through an independent verifier.

The implementation uses mock/replay data. It does not send real push notifications or WhatsApp messages.

## Requirements

- Python 3.11 or compatible version
- Project dependencies installed in the active virtual environment
- The `one_user_one_agent_pack` data pack available at the project root

## Run from the project root

### 1. Replay triggers

```powershell
python -m submission.src.replay_engine --pack one_user_one_agent_pack --out submission\sample_run
```

### 2. Simulate outcomes

```powershell
python one_user_one_agent_pack\simulator\simulate_outcomes.py --pack one_user_one_agent_pack --actions submission\sample_run\actions.jsonl --out submission\sample_run\sim
```

### 3. Evaluate goal outcomes

```powershell
python -m submission.src.goal_outcome_evaluator --pack one_user_one_agent_pack --run submission\sample_run
```

### 4. Generate the impact report

```powershell
python -m submission.src.impact_report --pack one_user_one_agent_pack --run submission\sample_run
```

### 5. Run submission tests

```powershell
python -m unittest discover -s submission\tests -v
```

## Key outputs

- `sample_run/decisions.jsonl` — per-trigger decisions
- `sample_run/actions.jsonl` — accepted actions
- `sample_run/viewer_state/` — replay-derived viewer state
- `sample_run/sim/` — simulated outcome events
- `sample_run/goal_outcome_report.json` — goal-specific attribution
- `sample_run/impact_report.json` — event-level comparison and confidence intervals
- `sample_run/final_report.md` — consolidated results and limitations

## Latest recorded results

- Triggers processed: 2,679
- Decisions recorded: 2,679
- Published actions: 1,060
- Users receiving actions: 699
- Simulated outcome events: 31,469
- Submission tests: 22 passed

See `sample_run/final_report.md` for goal-attribution results, confidence intervals, and interpretation.

## Limitations

- Results are simulated and descriptive; they do not prove causal impact.
- The event-level confidence intervals include zero for both play and purchase differences.
- Viewer state is replay-derived file-backed persistence, not a transactional production database.
- The current baseline generates home-page actions only; push and WhatsApp delivery are not enabled.
- Source-conflict resolution, real dependency failures, and some goal-eligibility cases need deeper integration testing.
- Run the commands from the project root. The documented Python modules use the submission.src implementation.
