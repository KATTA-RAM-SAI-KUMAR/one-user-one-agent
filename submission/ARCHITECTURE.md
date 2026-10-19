# Architecture

## Components
- `src/data_audit.py`: structural data checks.
- `src/event_loader.py`: event loading, normalization, and deduplication.
- `src/goal_planner.py`: evidence-based goal planning.
- `src/verifier.py`: action verification and safety checks.
- `src/replay_engine.py`: deterministic replay and decision/action recording.
- `src/goal_outcome_evaluator.py`: goal outcome attribution.
- `src/impact_report.py`: preliminary impact summaries.

## Replay workflow
1. Audit the supplied data pack.
2. Load and normalize events and resolve profile snapshots.
3. Evaluate evidence and decide to act or abstain.
4. Verify actions, including holdout isolation.
5. Write decisions, actions, and replay metrics.
6. Simulate outcomes and produce descriptive reports.
7. Derive per-viewer snapshots from the recorded decisions and actions.

## Per-viewer snapshots
`sample_run/viewer_state/` contains one JSON snapshot per viewer and an index. Each snapshot links to decision IDs, trigger event IDs, evidence descriptions, and action IDs. These are derived from the completed replay, not a transactional state store used during decision processing.
