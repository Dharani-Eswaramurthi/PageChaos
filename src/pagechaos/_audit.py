# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Run a synchronous consumer and independently check its snapshot output."""

from __future__ import annotations

import inspect
import json
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import TYPE_CHECKING, Any

from ._models import AuditReport, Finding, Record, RecordKey, RequestBudgetExceeded
from ._scenario import CursorScenario, encode_record, positive_int

if TYPE_CHECKING:
    import httpx

ItemKey = str | Callable[[Mapping[str, Any]], RecordKey]
Consumer = Callable[["httpx.Client"], Iterable[Mapping[str, Any]]]


def _key(record: Mapping[str, Any], item_key: ItemKey) -> RecordKey:
    value = record[item_key] if isinstance(item_key, str) else item_key(record)
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("Record identities must be strings or integers (not booleans)")
    return value


def audit(
    consumer: Consumer,
    *,
    scenario: CursorScenario,
    item_key: ItemKey = "id",
    max_requests: int = 100,
    max_records: int | None = None,
    base_url: str = "https://pagechaos.test",
) -> AuditReport:
    """Exercise a consumer using a fresh, fully mocked HTTPX client.

    Return an iterator from the consumer to retain already-yielded items when a
    later page fails. Returning a buffered list is supported, but items lost
    inside that function cannot be recovered. Input/configuration errors raise;
    consumer exceptions become findings. Process-control exceptions propagate.
    """
    expected = scenario.records
    expected_by_key: dict[RecordKey, str] = {}
    for expected_record in expected:
        try:
            identity = _key(expected_record, item_key)
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("Every snapshot record needs a valid identity") from exc
        if identity in expected_by_key:
            raise ValueError("Snapshot identities must be unique; choose a different item_key")
        expected_by_key[identity] = encode_record(expected_record)
    record_limit = max_records if max_records is not None else max(100, 2 * len(expected))
    positive_int(record_limit, "max_records")
    session = scenario.session(max_requests=max_requests)
    # Lazy import keeps scenario/report primitives usable without optional packages.
    from ._transport import make_client

    records: list[Record] = []
    error: Exception | None = None
    budget_exceeded = False
    record_budget_exceeded = False
    iterator: Iterator[Mapping[str, Any]] | None = None
    findings: list[Finding] = []
    with make_client(session, base_url=base_url) as client:
        try:
            result = consumer(client)
            if inspect.isawaitable(result):
                if inspect.iscoroutine(result):
                    result.close()
                raise TypeError("audit supports synchronous consumers; async is not supported")
            if isinstance(result, (str, bytes, Mapping)):
                raise TypeError("The consumer must return an iterable of record objects")
            iterator = iter(result)
            for record in iterator:
                if len(records) >= record_limit:
                    record_budget_exceeded = True
                    break
                records.append(json.loads(encode_record(record)))
        except RequestBudgetExceeded:
            budget_exceeded = True
        except Exception as exc:
            error = exc
        finally:
            # Close suspended consumers while their injected HTTP client is still open.
            close = getattr(iterator, "close", None)
            if callable(close):
                try:
                    close()
                except Exception as exc:
                    if error is None:
                        error = exc
    actual_counts: Counter[RecordKey] = Counter()
    modified: list[RecordKey] = []
    invalid_count = 0
    for record in records:
        try:
            identity = _key(record, item_key)
        except (KeyError, ValueError, TypeError):
            invalid_count += 1
            continue
        actual_counts[identity] += 1
        if (
            identity in expected_by_key
            and encode_record(record) != expected_by_key[identity]
            and identity not in modified
        ):
            modified.append(identity)
    missing = tuple(identity for identity in expected_by_key if identity not in actual_counts)
    duplicates = tuple(identity for identity, count in actual_counts.items() if count > 1)
    unexpected = tuple(identity for identity in actual_counts if identity not in expected_by_key)
    if missing:
        findings.append(Finding("MISSING_RECORDS", f"{len(missing)} snapshot record(s) missing."))
    if duplicates:
        findings.append(
            Finding("DUPLICATE_RECORDS", f"{len(duplicates)} identity/identities repeated.")
        )
    if unexpected:
        findings.append(
            Finding("UNEXPECTED_RECORDS", f"{len(unexpected)} unknown identity/identities.")
        )
    if modified:
        findings.append(Finding("MODIFIED_RECORDS", f"{len(modified)} record body/bodies changed."))
    if invalid_count:
        findings.append(
            Finding("INVALID_RECORD_ID", f"{invalid_count} record(s) lack a valid identity.")
        )
    if not session.events:
        findings.append(Finding("NO_REQUESTS", "The consumer never called the simulated endpoint."))
    if session.last_next_cursor is not None:
        findings.append(
            Finding("CONTINUATION_REMAINING", "The last successful page had a continuation cursor.")
        )
    if not session.terminal_reached:
        findings.append(Finding("NO_TERMINAL_RESPONSE", "A terminal response was not reached."))
    if session.protocol_errors:
        findings.append(
            Finding(
                "PROTOCOL_ERROR", "An unknown cursor, endpoint, origin, or method was requested."
            )
        )
    unapplied = [
        fault.at_request
        for fault in scenario.faults
        if fault.at_request not in session.applied_faults
    ]
    if unapplied:
        findings.append(
            Finding("UNEXERCISED_FAULT", f"Scheduled faults not exercised: {unapplied}.")
        )
    if budget_exceeded:
        findings.append(
            Finding("REQUEST_BUDGET_EXCEEDED", f"Stopped after {max_requests} dispatched requests.")
        )
    if record_budget_exceeded:
        findings.append(
            Finding("RECORD_BUDGET_EXCEEDED", f"Stopped after {record_limit} yielded records.")
        )
    if error is not None:
        # Exception strings can include URLs, credentials, or private response data.
        findings.append(Finding("CLIENT_ERROR", f"The consumer raised {type(error).__name__}."))
    return AuditReport(
        scenario=scenario.name,
        expected_count=len(expected),
        observed_count=len(records),
        unique_count=len(actual_counts),
        missing_ids=missing,
        duplicate_ids=duplicates,
        unexpected_ids=unexpected,
        modified_ids=tuple(modified),
        findings=tuple(findings),
        trace=tuple(session.events),
        terminal_reached=session.terminal_reached,
        budget_exceeded=budget_exceeded,
        record_budget=record_limit,
        record_budget_exceeded=record_budget_exceeded,
        records=tuple(records),
        error=error,
    )
