# Known Limitations

- Per-viewer snapshots are replay-derived file-backed state. They are not a transactional production state store and do not demonstrate crash-safe recovery.
- Evidence references identify recorded decision and trigger IDs plus evidence descriptions; they do not guarantee immutable source-event storage.
- Unit tests cover selected cases, including conflicting dialect evidence, corrected goal rules, dependency-failure reporting, trigger-age rejection, duplicate-trigger rejection, verifier constraints, and persistence. They do not cover every required scenario end to end.
- Trigger-age validation fails closed when the trigger age cannot be verified and rejects triggers older than the configured maximum. The default maximum age is 86,400 seconds.
- The current baseline generates home-page actions only. It does not send real push notifications or WhatsApp messages.
- Goal attribution and event-level comparisons are descriptive. They do not establish causal impact; the event-level confidence intervals include zero for both play and purchase differences.
- Simulated outcomes depend on the simulator and its seed. They do not establish real delivery, engagement, or business impact.
- Aggregate local replay speed does not establish production p95/p99 latency or guarantee a production latency target.
- Further end-to-end testing is needed for offline stale bursts, purchase events arriving after a decision, three-way dialect conflicts, unsupported model eligibility claims, catalogue prompt injection across the full pipeline, model/store outages, and traffic spikes.
