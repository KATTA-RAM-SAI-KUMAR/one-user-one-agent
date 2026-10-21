# Architecture

## Current implementation
The project uses Python modules for data auditing, event loading, goal planning, verification, replay, outcome evaluation, and impact reporting.

## Replay workflow
1. Audit the input data.
2. Load and normalize events.
3. Evaluate available evidence and decide whether to act or abstain.
4. Verify proposed actions.
5. Record decisions and actions.
6. Simulate outcomes and generate reports.

## Safety and reliability
The implementation must be evaluated against the assignment requirements. See KNOWN_LIMITATIONS.md for gaps that still require verification.
