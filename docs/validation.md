# Validation record

## Stable 0.1.0 release preparation - 13 November 2026

The stable candidate preserves the documented synchronous HTTPX, flat JSON
cursor, fixed-snapshot contract and report schema version 1.

- 106 tests pass locally on Windows, Python 3.12.14, including the runnable pytest
  example and the two property tests with 150 and 75 examples.
- Four new regression cases cover request-budget exhaustion during iterator
  cleanup after either the record limit or invalid output, and propagation of
  KeyboardInterrupt and SystemExit from cleanup. Both budget failures return
  reports with the earlier failure retained.
- scripts/check_install.py checks an isolated core wheel installation, the missing
  optional-dependency message, the pytest extra and fixture, the audit suite,
  module CLI success/failure behavior, and the console entry point. Both CI and
  the release build require this check before publishing.
- The local fresh-wheel check passed all 58 installed audit/example cases,
  core-only import and scenario checks, both module CLI outcomes, and the console
  entry point. Ruff lint/format, strict mypy, dependency consistency, release
  identity, and source/wheel builds also pass locally.

The new candidate must pass its own full CI matrix, strict Twine checks, and the
TestPyPI artifact verification before production publication. Local results alone
do not establish that the stable version has been published. Publication status
and provenance are recorded on GitHub and PyPI.

## Published alpha evidence

The published v0.1.0a1 tag, commit 3f60e4c, completed all seven validation jobs:
Linux on Python 3.11-3.15, Windows on Python 3.12, and macOS on Python 3.12.
The release workflow also completed TestPyPI publication, artifact verification,
and the reviewed PyPI upload on 27 October 2026.

- [Alpha validation run](https://github.com/Dharani-Eswaramurthi/PageChaos/actions/runs/40473699136)
- [Alpha release run](https://github.com/Dharani-Eswaramurthi/PageChaos/actions/runs/40473908678)
- [PyPI release history](https://pypi.org/project/pagechaos/#history)

## Original alpha validation - 27 October 2026

The following sections retain the original local 0.1.0a1 validation record.

## What has been validated

- A cursor-following reference consumer retrieves all 30 records from pages of
  sizes 10, 3, 10, and 7.
- A consumer that stops on a short page returns 13, and the audit identifies the
  17 missing records and remaining continuation.
- Deliberately broken consumers exercise early empty-page termination, lossy
  numeric cursor conversion, repeated output, changed bodies, unknown output
  identities, ignored continuation, and unbounded request/output loops.
- Generated tests vary page schedules and opaque Unicode cursors. Two property
  tests are configured for 150 and 75 examples.
- Session replay, fixture detachment, iterator cleanup, terminal conventions,
  configuration validation, request/record budgets, CLI status, JSON reports, and
  the installed pytest fixture are covered.
- Socket connection attempts are forbidden in dedicated offline transport tests.
- The existing notion-client 3.1.0 iterate_paginated_api helper is exercised with
  synthetic block-list responses, short and empty pages, and a dummy token.
  This is an offline compatibility test, not live service verification.

The original local check results and build verification are recorded below.
Subsequent public alpha CI evidence is linked above.

## Evidence behind the test cases

These sources motivate scenarios; upstream bug reports were not reproduced in
their original deployments, and PageChaos does not claim to fix their projects.

1. [Slack pagination contract](https://docs.slack.dev/apis/web-api/pagination/):
   short pages can still have continuation. Termination should follow the cursor.
2. [Honua Python SDK issue 236](https://github.com/honua-io/honua-sdk-python/issues/236):
   a September 2026 report describes stopping on short pages while more rows exist.
3. [Twenty issue 20044](https://github.com/twentyhq/twenty/issues/20044):
   a historical repeated-cursor/duplicate-record report, subsequently closed.
4. [HTTPX transports](https://www.python-httpx.org/advanced/transports/):
   the documented mock transport is the implementation foundation.
5. [Notion SDK helper source](https://github.com/ramnes/notion-sdk-py/blob/main/notion_client/helpers.py):
   the external helper used by the pinned offline compatibility test.

The short-page reproduction in this repository is a deliberately authored
consumer with that failure pattern, not a reproduced Honua SDK execution.
The large numeric cursor test is a synthetic precision-loss trap.

## Competitive scope

HTTPX, RESPX, pytest-httpx and general stateful mock servers already provide the
primitives needed to write these tests. PageChaos packages a small fixed-snapshot
scenario model, independent record comparison, budgets, and diagnostics.

Technical feasibility is demonstrated locally. Independent adoption, demand,
production reliability, and willingness to pay remain unvalidated. The package
name was absent from PyPI when checked on this date; that does not reserve it.

## Limits of the evidence

No real API, real credentials, customer data, or external account was used by the
test suite. Network access was used to retrieve dependencies and public source
documentation. The initial validation preceded public publication; current release status is shown on GitHub and PyPI.

Fixed-snapshot checks do not establish live-dataset consistency, sink idempotency,
exactly-once writes, checkpoint safety, hard timeout enforcement, retry timing,
async behavior, or compatibility with every SDK. Read the explicit API contract.

## Local release checks

The following checks passed locally on Windows, Python 3.12.14:

- 102 tests, including the runnable pytest example. Two property tests within
  that count are configured for 150 page-schedule and 75 opaque-cursor examples.
- Ruff lint and formatting checks across source, tests, and examples.
- Strict mypy checks across all 8 source modules.
- Dependency consistency check.
- Core-only wheel installation in a fresh virtual environment, importing without
  HTTPX and reporting the missing optional dependency when audit is called.
- 4 additional clean-wheel smoke tests: installed import location, registered
  pytest fixture, module CLI, and installed console entry point.
- Build of both the source distribution and the pure-Python wheel.

These build artifacts were local alpha outputs. Cross-platform alpha validation
subsequently passed as recorded above. Each new release must pass its own CI run.


## Public-release preparation

The Apache 2.0 release preparation preserves the original snapshot contract.
The 102 tests, Ruff checks, strict mypy, version/attribution checks, source build,
wheel build, and Twine strict checks passed again locally on 27 October 2026.
The rebuilt wheel declares Apache-2.0, includes LICENSE and NOTICE, contains the
full-name author credit without an author email, and supplies project URLs.
Public CI results should be read from the workflow runs rather than inferred
from this local record.
