# Changelog

## 0.1.0 - stable

- Stabilize the documented synchronous HTTPX, flat JSON cursor, fixed-snapshot
  API and report schema version 1, with patch compatibility described in docs/api.md.
- Fix request-budget exhaustion during iterator cleanup so audit returns a report
  and preserves the original consumer error or record-limit finding.
- Add regression coverage for both cleanup failure paths and for process-control
  exceptions, which continue to propagate.
- Verify fresh wheel installations, optional dependencies, installed pytest
  discovery, audit regressions, module CLI behavior, and the console entry point
  in validation and release workflows before publication.
- Update package metadata, installation examples, citation, security policy, and
  release guidance for stable releases.

Publication date and artifact provenance are recorded on GitHub and PyPI.

## 0.1.0a1 — alpha, 27 October 2026

- Add fixed-snapshot cursor scenarios with uneven and empty pages.
- Add custom flat response fields and optional has_more.
- Add one-shot HTTP errors, read timeouts, and repeated cursors.
- Add an offline HTTPX audit runner with request and output limits.
- Report missing, duplicate, unknown, and changed records and incomplete traversal.
- Include structured reports, CLI demos, typed exports, and a pytest fixture.
- Validate an existing Notion Python SDK pagination helper entirely offline.

- Prepare Apache 2.0 licensing, public maintainer attribution, package links,
  issue forms, and a Trusted Publishing release workflow.

Publication status is recorded in the GitHub release and package-index pages.
See docs/validation.md for verification and remaining limitations.
