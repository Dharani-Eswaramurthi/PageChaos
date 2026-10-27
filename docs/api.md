# API and contract

## CursorScenario

CursorScenario(records, *, page_size=10, page_sizes=None, cursor_tokens=None,
protocol=None, faults=(), path="/items", terminal="null", name="cursor-snapshot")

Records must be JSON-serializable objects. Object keys, including nested ones, must
be strings. Non-finite numbers and circular structures are rejected. JSON encoding
detaches fixtures from caller mutations; responses and records properties return
fresh objects. Scenarios are reusable configurations; sessions are per-run.

page_sizes is an explicit prefix, including zero-length pages. Remaining records
are partitioned with page_size. An empty snapshot still has one terminal page.
Explicit sizes cannot exceed the snapshot size. Request limit parameters do not
negotiate these sizes: configure the script for the API behavior you need to test.

cursor_tokens supplies one unique, nonempty string per page, including the initial
page. The first page is normally selected by an absent or empty cursor; its token
allows a repeat-cursor fault to select it again. Tokens are opaque and never parsed
as numbers. The next page token selects that page without consuming mutable state.

terminal chooses null, empty (""), or missing for the final cursor field.

## CursorProtocol

CursorProtocol(items_field="items", next_cursor_field="next_cursor",
cursor_param="cursor", has_more_field=None)

All response fields are flat. An optional has_more field is computed from the same
continuation as next_cursor. Response field names must be distinct. There is no
JSONPath parser and no nested response-envelope support in this release.

The simulator accepts GET at scenario.path. Unknown origins, methods, paths, or
cursors fail the audit, even if a consumer swallows the resulting HTTP error.
Duplicate cursor parameters are rejected instead of choosing a value.

## Fault

- Fault.http_error(at_request, status_code=503, retry_after=None)
- Fault.timeout(at_request)
- Fault.repeat_cursor(at_request)

Request numbers start at 1 and count retries. Only one fault per request is
allowed. HTTP errors accept status codes 400 through 599. retry_after is a literal,
single-line header value, including an HTTP date if you need that fixture.

Faults do not implement retry behavior. Fault.timeout raises httpx.ReadTimeout.
Fault.repeat_cursor returns the current page's token as continuation; if the
consumer follows it, that page is delivered again. A one-shot fault may subsequently
recover; permanent loops can also be exercised with a broken consumer that keeps
requesting the same page.

Every scheduled fault must actually be applied for assert_complete() to pass.

## audit

audit(consumer, *, scenario, item_key="id", max_requests=100, max_records=None,
base_url="https://pagechaos.test") -> AuditReport

The consumer receives a synchronous HTTPX Client and returns an iterable of record
objects. A generator lets the runner retain records yielded before an error.
Buffered records inside a function that raises before returning are not observable.

item_key is a field name or callable returning an integer or string. Boolean IDs
are rejected; integer 1 and string "1" are distinct. Snapshot identities must be
unique. Use a pure key function and a stable composite key for versioned entities.

base_url must be an origin-only HTTP(S) URL, without credentials, a query, or a
fragment. An HTTPX mock transport handles all calls made through the injected
client; there is no fallback transport. Other client objects are not intercepted.

max_requests is the number of requests the scenario will dispatch. The next attempt
raises RequestBudgetExceeded, an audit control signal derived from BaseException.
This intentionally bypasses ordinary except Exception retry handlers. The runner
catches it and records a finding. The blocked attempt is not included in trace.

max_records defaults to max(100, 2 * snapshot size). The runner stops when an
additional yielded record would exceed that limit and closes a closable iterator
before closing its injected HTTP client. Both limits must be positive integers.

These are cooperative limits, not a hard wall-clock bound. A thread stuck in I/O,
a CPU loop without yielding, or code catching BaseException can still hang.
Use a separate process timeout when that behavior is possible.

Configuration and optional-dependency errors raise directly. Consumer exceptions
are captured as report.error; KeyboardInterrupt and SystemExit propagate.

## AuditReport

assert_complete() requires all of the following:

1. Every expected identity appears exactly once.
2. No unknown identity or modified record body appears.
3. A terminal response was reached and no continuation remains.
4. There are no consumer or protocol errors.
5. Scheduled faults were exercised.
6. Neither request nor record limits were exhausted.

The contract is strict snapshot enumeration. It does not assert order or claim
that every response body was semantically interpreted by the consumer.

Inspect ok, findings, missing_ids, duplicate_ids, unexpected_ids, modified_ids,
records, error, trace, expected_count, observed_count, unique_count, request_count,
terminal_reached, budget_exceeded, record_budget, and record_budget_exceeded.

explain() is a concise text summary. to_dict() and to_json(indent=2) use report
schema version 1. They include identities, cursors, request paths, status codes,
page indices and findings. They omit record bodies, request headers, and raw
exception messages. In-memory records and error remain available. Use synthetic
data: identities, paths, and cursors are not automatically redacted.

assert_complete() raises PaginationAssertionError, an AssertionError subclass.
For expected failures, inspect the specific findings and error type instead of
asserting completeness.

## pytest fixture

Installing the distribution registers pagechaos_audit through pytest11. It returns
the public audit function. pytest must be installed to use the fixture; HTTPX is
required to run an audit. The plugin does not autouse fixtures or patch the network.

## CLI

- pagechaos --version
- pagechaos demo --client correct
- pagechaos demo --client short-page
- pagechaos demo --client short-page --json

Exit status is 0 for a passing demonstration, 1 for a contract failure, and 2 for
invalid command-line arguments. Both demos use bundled synthetic fixtures only.
