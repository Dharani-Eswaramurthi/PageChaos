# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Public report types, requiring only the standard library."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

Record = dict[str, Any]
RecordKey = str | int


class PaginationAssertionError(AssertionError):
    """A consumer violated the snapshot-completeness contract."""


class RequestBudgetExceeded(BaseException):
    """Audit stop signal, bypassing ordinary application except Exception blocks.

    The runner catches this signal. It never catches KeyboardInterrupt or SystemExit.
    """


@dataclass(frozen=True)
class Finding:
    code: str
    message: str


@dataclass(frozen=True)
class RequestEvent:
    number: int
    method: str
    path: str
    cursor: str | None
    status_code: int | None
    page_index: int | None = None
    record_count: int = 0
    next_cursor: str | None = None
    fault: str | None = None


@dataclass(frozen=True)
class AuditReport:
    scenario: str
    expected_count: int
    observed_count: int
    unique_count: int
    missing_ids: tuple[RecordKey, ...]
    duplicate_ids: tuple[RecordKey, ...]
    unexpected_ids: tuple[RecordKey, ...]
    modified_ids: tuple[RecordKey, ...]
    findings: tuple[Finding, ...]
    trace: tuple[RequestEvent, ...]
    terminal_reached: bool
    budget_exceeded: bool
    record_budget: int
    record_budget_exceeded: bool
    records: tuple[Record, ...] = field(repr=False)
    error: Exception | None = field(default=None, repr=False, compare=False)

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def request_count(self) -> int:
        """Dispatched requests; the blocked budget attempt is excluded."""
        return len(self.trace)

    def explain(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        lines = [
            f"{status}: {self.scenario}",
            f"Expected records: {self.expected_count}",
            f"Observed records: {self.observed_count} ({self.unique_count} unique)",
            f"Requests: {self.request_count}; terminal reached: {self.terminal_reached}",
        ]
        lines.extend(f"[{finding.code}] {finding.message}" for finding in self.findings)
        return "\n".join(lines)

    def assert_complete(self) -> None:
        """Require all snapshot records exactly once, unchanged, and clean termination."""
        if not self.ok:
            raise PaginationAssertionError(self.explain())

    def to_dict(self) -> dict[str, Any]:
        """Omit record bodies, headers and raw exception messages from JSON reports.

        IDs and cursors remain visible. Use synthetic fixtures, never credentials.
        """
        return {
            "schema_version": 1,
            "scenario": self.scenario,
            "ok": self.ok,
            "expected_count": self.expected_count,
            "observed_count": self.observed_count,
            "unique_count": self.unique_count,
            "request_count": self.request_count,
            "terminal_reached": self.terminal_reached,
            "budget_exceeded": self.budget_exceeded,
            "record_budget": self.record_budget,
            "record_budget_exceeded": self.record_budget_exceeded,
            "missing_ids": list(self.missing_ids),
            "duplicate_ids": list(self.duplicate_ids),
            "unexpected_ids": list(self.unexpected_ids),
            "modified_ids": list(self.modified_ids),
            "error_type": type(self.error).__name__ if self.error is not None else None,
            "findings": [asdict(finding) for finding in self.findings],
            "trace": [asdict(event) for event in self.trace],
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, allow_nan=False, indent=indent)
