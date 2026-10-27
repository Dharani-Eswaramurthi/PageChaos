# PageChaos

**Python pagination testing, created and maintained by
[Dharani Eswaramurthi](https://github.com/Dharani-Eswaramurthi).**

[![Validate](https://github.com/Dharani-Eswaramurthi/PageChaos/actions/workflows/ci.yml/badge.svg)](https://github.com/Dharani-Eswaramurthi/PageChaos/actions/workflows/ci.yml)


Test whether your Python API client silently loses records, returns duplicates, or
stops before a cursor-paginated export is complete.

**Alpha: 0.1.0a1.** Synchronous HTTPX, flat JSON cursor responses, fixed snapshots.
Python 3.11+. CI exercises Linux on Python 3.11–3.15, plus Windows and macOS on Python 3.12.

PageChaos runs your existing consumer against an in-process mock transport. It
compares collected records with a known snapshot and explains pagination failures.
It does not replace your paginator or retry policy.

## Install the alpha

    python -m pip install "pagechaos[httpx]==0.1.0a1"

For the optional pytest fixture:

    python -m pip install "pagechaos[pytest]==0.1.0a1"

For development, clone this repository and install the local checkout:

    git clone https://github.com/Dharani-Eswaramurthi/PageChaos.git
    cd PageChaos
    python -m pip install -e ".[httpx]"

## See the defect

    python -m pagechaos demo --client correct
    python -m pagechaos demo --client short-page

The correct client collects 30 records in four requests. The broken client stops
on the second, short page and returns only 13. Its command exits 1, intentionally:

    FAIL: short-page-with-continuation
    Expected records: 30
    Observed records: 13 (13 unique)
    Requests: 2; terminal reached: False
    [MISSING_RECORDS] 17 snapshot record(s) missing.
    [CONTINUATION_REMAINING] The last successful page had a continuation cursor.
    [NO_TERMINAL_RESPONSE] A terminal response was not reached.

## A runnable test

Copy this into a Python file after installing the HTTPX extra:

```python
from pagechaos import CursorScenario, audit


def fetch_all_items(http):
    cursor = None
    while True:
        response = http.get("/items", params={"cursor": cursor} if cursor else {})
        response.raise_for_status()
        page = response.json()
        yield from page["items"]
        cursor = page.get("next_cursor")
        if not cursor:
            return


scenario = CursorScenario(
    records=[{"id": i} for i in range(1, 31)],
    page_sizes=[10, 3, 10, 7],
)
report = audit(fetch_all_items, scenario=scenario, item_key="id", max_requests=12)
report.assert_complete()
print(report.explain())
```

Replace fetch_all_items with your consumer, using the supplied HTTPX client.
Change the consumer to stop when a page contains fewer than 10 items and the
audit fails with 17 missing records. A short page can still have continuation.

The default endpoint is GET /items, with flat JSON fields items and next_cursor.
The injected client's base URL is https://pagechaos.test; requests through this
client use the mock transport, including absolute URLs. Unexpected endpoints and
origins receive errors, with no real-network fallback.

Return an iterator to preserve records yielded before a later-page exception.
If your function buffers a list and raises before returning it, those internal
records are unavailable to PageChaos.

See [a complete runnable example](https://github.com/Dharani-Eswaramurthi/PageChaos/blob/main/examples/short_pages.py).

## Scenarios and faults

- Short and empty pages with valid continuation.
- Full final pages and null, empty, or absent terminal cursors.
- Custom opaque cursors, including large numeric-looking strings and Unicode.
- Repeated-cursor responses.
- One-shot HTTP errors and simulated read timeouts.
- Configurable flat field names and an optional has_more field.
- Fresh state for every audit.

```python
from pagechaos import CursorScenario, Fault

scenario = CursorScenario(
    [{"id": i} for i in range(12)],
    page_size=4,
    faults=[Fault.http_error(2, 429, retry_after="2")],
)
```

Faults target absolute request numbers, counting retries. PageChaos sends the
header; the consumer owns retrying and waiting. An unexercised scheduled fault is
a failed audit, so a test cannot claim coverage of a failure it never reached.

## Assertions and reports

assert_complete() requires each snapshot record exactly once and unchanged, a
terminal response, no consumer error, no protocol error, all scheduled faults
exercised, and no budget exhaustion. Record ordering is not asserted.

Use report.explain(), report.to_dict(), or report.to_json(). JSON reports omit
record bodies, request headers, and raw exception messages. IDs and cursors remain
visible: use synthetic fixtures. The in-memory report.records and report.error
remain available for local investigation.

A separate record limit stops endlessly yielding consumers:
max_records defaults to max(100, 2 * snapshot size). max_requests defaults to 100.
These limits do not interrupt blocking I/O, CPU loops without yields, or consumer
code that catches BaseException. Use a process timeout for untrusted/hanging code.

## pytest

```python
def test_export(pagechaos_audit):
    report = pagechaos_audit(fetch_all_items, scenario=scenario)
    report.assert_complete()
```

The fixture performs no automatic auditing and does not patch unrelated clients.

## Compatibility evidence

The suite exercises the existing notion-client 3.1.0 pagination helper against
synthetic block-list responses, including short and empty pages. It uses a dummy
token and forbids socket connections. This establishes offline compatibility for
that helper, not live Notion API behavior or production adoption.

See [the integration example](https://github.com/Dharani-Eswaramurthi/PageChaos/blob/main/examples/notion_sdk.py).

## Boundaries

- Fixed response schedules: client limit parameters do not change page sizes.
- Flat JSON cursor APIs only; no nested envelopes, Link headers, offsets, or POST.
- No live dataset mutations or snapshot guarantees for a real upstream.
- Duplicate-delivery allowance, checkpointing, and sink writes need other contracts.
- Simulated timeouts exercise exception handling, not TCP timeout enforcement.
- Requests made through another client, subprocess, or library are outside interception.
- No elapsed-time verification, async runner, hosted service, or remote collection.

Read [the API contract](https://github.com/Dharani-Eswaramurthi/PageChaos/blob/main/docs/api.md),
[validation evidence](https://github.com/Dharani-Eswaramurthi/PageChaos/blob/main/docs/validation.md),
and [roadmap](https://github.com/Dharani-Eswaramurthi/PageChaos/blob/main/docs/roadmap.md).

## Feedback and support

[Report a bug or suggest a scenario](https://github.com/Dharani-Eswaramurthi/PageChaos/issues).
Use synthetic fixtures and describe the API contract you need to test.
[Report security issues privately](https://github.com/Dharani-Eswaramurthi/PageChaos/security/advisories/new).

The library is freely usable under Apache 2.0. For a scoped integration or support
inquiry, open an issue describing the technical need without confidential data.
Community maintenance has no guaranteed response time.

## Development

    python -m venv .venv
    python -m pip install -r requirements-dev.lock
    python -m pip install --no-deps --no-build-isolation -e .
    python -m pytest
    python -m ruff check .
    python -m ruff format --check .
    python -m mypy
    python -m build

Activate the virtual environment or use its Python executable for these commands.
[Contributing](https://github.com/Dharani-Eswaramurthi/PageChaos/blob/main/CONTRIBUTING.md).
[Apache 2.0 license](https://github.com/Dharani-Eswaramurthi/PageChaos/blob/main/LICENSE).
