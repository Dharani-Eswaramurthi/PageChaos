# Roadmap and decision gates

## Current alpha

Synchronous HTTPX, flat cursor envelopes, fixed response schedules, one-shot
faults, strict snapshot comparison, JSON reports, a pytest fixture, and CLI demos.
An existing Notion SDK helper provides one offline compatibility case.

## Next validation milestone

Ask independent SDK/connector maintainers to try the alpha. No outreach has been
sent. Measure integration changes, whether tests are retained in CI, and whether
diagnostics help fix a defect. Expand only when that feedback justifies it.

## Candidate follow-ups

- An async runner sharing the same scenario engine, with cancellation tests.
- Nested envelopes and explicit response-format adapters.
- Offset and Link-header contracts with their own termination rules.
- Fault schedules keyed by cursor/attempt, beyond absolute request numbers.
- Optional clock injection for retry-timing assertions.
- Checkpoint/resume and sink-write contracts.
- Explicit live-walk consistency models and controlled dataset mutations.
- Hypothesis-driven scenario generation and shrinking of failing client traces.

These are proposals, not shipped features. A hosted service is not planned until
there is evidence of recurring demand for team-level functionality.
