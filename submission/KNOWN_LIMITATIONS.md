# Known Limitations

- Per-viewer snapshots are derived after replay. They are not a transactional production state store and do not demonstrate crash-safe recovery.
- Evidence references currently identify recorded decision and trigger IDs plus evidence descriptions; they do not guarantee immutable source-event storage.
- Dedicated tests are still needed for late triggers, conflicting sources, dependency failures, and corrected goal rules.
- Goal eligibility and outcome attribution require further validation against the assignment rules.
- Reported group differences are descriptive and do not establish causal impact.
- Aggregate replay latency does not establish p95/p99 latency or guarantee a production latency target.
- Local simulation does not prove real delivery, user engagement, or business impact.
- The current 22-test suite covers selected event-loader, planner, verifier, reliability, persistence, impact-reporting, deep-link parsing, and prompt-injection cases. It does not cover every required scenario or replace full end-to-end integration testing.
