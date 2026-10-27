# Validation record

Date: 27 October 2026. Status: local alpha, 0.1.0a1.

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

The local check results and build verification are recorded below. The prepared
GitHub Actions matrix has not run here.

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

The build artifacts are local alpha outputs. The prepared GitHub Actions matrix
has not run, so Python versions other than 3.12 and operating systems other than
Windows have not yet been verified. Track public CI and release status at https://github.com/Dharani-Eswaramurthi/PageChaos/actions.


## Public-release preparation

The Apache 2.0 release preparation preserves the original snapshot contract.
The 102 tests, Ruff checks, strict mypy, version/attribution checks, source build,
wheel build, and Twine strict checks passed again locally on 27 October 2026.
The rebuilt wheel declares Apache-2.0, includes LICENSE and NOTICE, contains the
full-name author credit without an author email, and supplies project URLs.
Public CI results should be read from the workflow runs rather than inferred
from this local record.
