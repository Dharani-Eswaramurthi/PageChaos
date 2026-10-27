# Contributing

PageChaos is an early alpha. Small, reproducible failures and scenario corrections
are especially useful.

## Setup

Create and activate a Python 3.11+ virtual environment, then run:

    python -m pip install -r requirements-dev.lock
    python -m pip install --no-deps --no-build-isolation -e .

The lock records the dependency versions used for local validation. Core runtime
code uses only the standard library; the HTTPX adapter and pytest fixture are
optional integrations.

## Checks

    python -m pytest
    python -m ruff check .
    python -m ruff format --check .
    python -m mypy
    python -m build

Also run examples/short_pages.py and examples/notion_sdk.py with Python. The latter
uses synthetic responses through the real SDK and does not call Notion.

## Tests that matter

For a new scenario, include a correct consumer that passes and an appropriate
broken consumer that fails. Establish expected records independently from the
paginator's cursor calculations. Test false positives as well as detections.

Keep ordinary CI offline. Do not use real tokens or recorded personal data.
State whether a fixture is synthetic or reproduces an external defect, with a
source link when appropriate. Never describe an authored test as a measured
production incident.

Changes to report fields require review of the documented schema_version and
serialization contract. Do not add retry timing or network guarantees without
tests that actually observe those properties.

## Release

Build a source archive and wheel, then install the wheel into a fresh environment.
Verify core imports with no optional packages, the demo with HTTPX, and pytest
plugin discovery. Publication to GitHub or PyPI is a separate explicit action.

## Contributions and license

By submitting a contribution for inclusion, you agree to offer it under the
project's Apache 2.0 license. Only submit material you have the right to contribute.
Keep existing attribution notices. Reusable fixes and well-explained tests are
welcome; paid support does not bypass normal technical review.

See docs/releasing.md for the release process.
