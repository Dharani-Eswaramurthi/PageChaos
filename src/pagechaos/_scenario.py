# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""A cursor-page script independent of HTTPX and pytest."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from ._models import Record, RequestBudgetExceeded, RequestEvent


def positive_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def encode_record(record: Mapping[str, Any]) -> str:
    if not isinstance(record, Mapping) or not all(isinstance(key, str) for key in record):
        raise TypeError("Records must be JSON objects with string keys")
    pending: list[Any] = [record]
    visited: set[int] = set()
    while pending:
        value = pending.pop()
        if isinstance(value, (Mapping, list, tuple)):
            if id(value) in visited:
                continue
            visited.add(id(value))
            if isinstance(value, Mapping):
                if not all(isinstance(key, str) for key in value):
                    raise TypeError("JSON object keys must be strings, including nested objects")
                pending.extend(value.values())
            else:
                pending.extend(value)
    return json.dumps(dict(record), ensure_ascii=False, allow_nan=False, sort_keys=True)


@dataclass(frozen=True)
class CursorProtocol:
    """Flat JSON response fields and the request cursor parameter."""

    items_field: str = "items"
    next_cursor_field: str = "next_cursor"
    cursor_param: str = "cursor"
    has_more_field: str | None = None

    def __post_init__(self) -> None:
        for value in (self.items_field, self.next_cursor_field, self.cursor_param):
            if not isinstance(value, str) or not value:
                raise ValueError("Protocol field names must be nonempty strings")
        response_fields = [self.items_field, self.next_cursor_field]
        if self.has_more_field is not None:
            if not isinstance(self.has_more_field, str) or not self.has_more_field:
                raise ValueError("has_more_field must be a nonempty string or None")
            response_fields.append(self.has_more_field)
        if len(set(response_fields)) != len(response_fields):
            raise ValueError("Response field names must be distinct")


@dataclass(frozen=True)
class Fault:
    """One fault at an absolute request number; fresh sessions replay independently."""

    at_request: int
    kind: Literal["http_error", "timeout", "repeat_cursor"]
    status_code: int | None = None
    retry_after: str | None = None

    def __post_init__(self) -> None:
        positive_int(self.at_request, "at_request")
        if self.kind not in {"http_error", "timeout", "repeat_cursor"}:
            raise ValueError("Unknown fault kind")
        if self.kind == "http_error":
            if (
                isinstance(self.status_code, bool)
                or not isinstance(self.status_code, int)
                or not 400 <= self.status_code <= 599
            ):
                raise ValueError("HTTP faults require a status code from 400 through 599")
            if self.retry_after is not None and (
                not isinstance(self.retry_after, str)
                or "\r" in self.retry_after
                or "\n" in self.retry_after
            ):
                raise ValueError("retry_after must be a single-line string")
        elif self.status_code is not None or self.retry_after is not None:
            raise ValueError("Only HTTP faults accept status_code or retry_after")

    @classmethod
    def http_error(
        cls, at_request: int, status_code: int = 503, *, retry_after: str | None = None
    ) -> Fault:
        return cls(at_request, "http_error", status_code, retry_after)

    @classmethod
    def timeout(cls, at_request: int) -> Fault:
        return cls(at_request, "timeout")

    @classmethod
    def repeat_cursor(cls, at_request: int) -> Fault:
        return cls(at_request, "repeat_cursor")


class CursorScenario:
    """Fixed snapshot and a scripted sequence of page sizes.

    Explicit sizes are a prefix; remaining records use page_size. Zero makes an
    empty page that may still have continuation. Request limit parameters do not
    change the script. Records are detached from callers through JSON encoding.
    """

    def __init__(
        self,
        records: Sequence[Mapping[str, Any]],
        *,
        page_size: int = 10,
        page_sizes: Sequence[int] | None = None,
        cursor_tokens: Sequence[str] | None = None,
        protocol: CursorProtocol | None = None,
        faults: Sequence[Fault] = (),
        path: str = "/items",
        terminal: Literal["null", "empty", "missing"] = "null",
        name: str = "cursor-snapshot",
    ) -> None:
        positive_int(page_size, "page_size")
        if isinstance(records, (str, bytes)):
            raise TypeError("records must be a sequence of JSON objects")
        if not isinstance(path, str) or not path.startswith("/") or "?" in path or "#" in path:
            raise ValueError("path must be an absolute URL path without query or fragment")
        if terminal not in {"null", "empty", "missing"}:
            raise ValueError("terminal must be null, empty, or missing")
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a nonempty string")
        self._encoded = tuple(encode_record(record) for record in records)
        sizes = tuple(page_sizes) if page_sizes is not None else ()
        if any(isinstance(size, bool) or not isinstance(size, int) or size < 0 for size in sizes):
            raise ValueError("page_sizes must contain nonnegative integers")
        if sum(sizes) > len(self._encoded):
            raise ValueError("Explicit page sizes cannot consume more than the snapshot")
        remaining = len(self._encoded) - sum(sizes)
        extra = (page_size,) * (remaining // page_size)
        if remaining % page_size:
            extra += (remaining % page_size,)
        self.page_sizes = sizes + extra or (0,)
        pages: list[tuple[str, ...]] = []
        offset = 0
        for size in self.page_sizes:
            pages.append(self._encoded[offset : offset + size])
            offset += size
        self._pages = tuple(pages)
        if isinstance(cursor_tokens, (str, bytes)):
            raise TypeError("cursor_tokens must be a sequence of strings")
        tokens = (
            tuple(cursor_tokens)
            if cursor_tokens is not None
            else tuple(f"pc_{index:04d}" for index in range(len(pages)))
        )
        if (
            len(tokens) != len(pages)
            or any(not isinstance(token, str) or not token for token in tokens)
            or len(set(tokens)) != len(tokens)
        ):
            raise ValueError("cursor_tokens must supply one unique nonempty string per page")
        fault_map: dict[int, Fault] = {}
        for fault in faults:
            if not isinstance(fault, Fault):
                raise TypeError("faults must contain Fault objects")
            if fault.at_request in fault_map:
                raise ValueError("Only one fault may be scheduled per request")
            fault_map[fault.at_request] = fault
        self.cursor_tokens = tokens
        if protocol is not None and not isinstance(protocol, CursorProtocol):
            raise TypeError("protocol must be a CursorProtocol")
        self.protocol = protocol or CursorProtocol()
        self.faults = tuple(fault_map.values())
        self.path = path
        self.terminal = terminal
        self.name = name

    @property
    def records(self) -> tuple[Record, ...]:
        return tuple(json.loads(record) for record in self._encoded)

    def session(self, *, max_requests: int = 100) -> ScenarioSession:
        return ScenarioSession(self, max_requests=max_requests)


@dataclass(frozen=True)
class ResponseSpec:
    status_code: int | None
    body: dict[str, Any]
    headers: dict[str, str]


class ScenarioSession:
    """Mutable state owned by one audit. No state is reused between audit runs."""

    def __init__(self, scenario: CursorScenario, *, max_requests: int) -> None:
        positive_int(max_requests, "max_requests")
        self.scenario = scenario
        self.max_requests = max_requests
        self.events: list[RequestEvent] = []
        self.applied_faults: set[int] = set()
        self.protocol_errors: list[str] = []
        self.last_next_cursor: str | None = None
        self.terminal_reached = False
        self._cursor_indices = {token: index for index, token in enumerate(scenario.cursor_tokens)}
        self._faults = {fault.at_request: fault for fault in scenario.faults}

    def dispatch(
        self,
        method: str,
        path: str,
        query: Mapping[str, str],
        *,
        origin_matches: bool = True,
        ambiguous_cursor: bool = False,
    ) -> ResponseSpec:
        if len(self.events) >= self.max_requests:
            raise RequestBudgetExceeded(f"Request budget of {self.max_requests} exhausted")
        number = len(self.events) + 1
        cursor = query.get(self.scenario.protocol.cursor_param) or None
        if ambiguous_cursor:
            return self._invalid(number, method, path, cursor, "ambiguous_cursor", 400)
        page_index = 0 if cursor is None else self._cursor_indices.get(cursor)
        if method != "GET" or path != self.scenario.path or not origin_matches:
            return self._invalid(number, method, path, cursor, "unexpected_endpoint", 404)
        if page_index is None:
            return self._invalid(number, method, path, cursor, "unknown_cursor", 400)
        fault = self._faults.get(number)
        if fault is not None and fault.kind in {"http_error", "timeout"}:
            self.applied_faults.add(number)
            status = fault.status_code if fault.kind == "http_error" else None
            self.events.append(
                RequestEvent(number, method, path, cursor, status, page_index, fault=fault.kind)
            )
            headers = {"Retry-After": fault.retry_after} if fault.retry_after is not None else {}
            return ResponseSpec(status, {"error": fault.kind}, headers)
        records = [json.loads(record) for record in self.scenario._pages[page_index]]
        next_index = page_index + 1
        next_cursor = (
            self.scenario.cursor_tokens[next_index]
            if next_index < len(self.scenario._pages)
            else None
        )
        if fault is not None and fault.kind == "repeat_cursor":
            self.applied_faults.add(number)
            next_cursor = self.scenario.cursor_tokens[page_index]
        self.last_next_cursor = next_cursor
        self.terminal_reached = next_cursor is None
        body: dict[str, Any] = {self.scenario.protocol.items_field: records}
        if self.scenario.protocol.has_more_field is not None:
            body[self.scenario.protocol.has_more_field] = next_cursor is not None
        if next_cursor is not None or self.scenario.terminal != "missing":
            body[self.scenario.protocol.next_cursor_field] = (
                next_cursor
                if next_cursor is not None
                else ""
                if self.scenario.terminal == "empty"
                else None
            )
        self.events.append(
            RequestEvent(
                number,
                method,
                path,
                cursor,
                200,
                page_index,
                len(records),
                next_cursor,
                fault.kind if fault is not None else None,
            )
        )
        return ResponseSpec(200, body, {})

    def _invalid(
        self, number: int, method: str, path: str, cursor: str | None, code: str, status: int
    ) -> ResponseSpec:
        self.protocol_errors.append(code)
        self.events.append(RequestEvent(number, method, path, cursor, status, fault=code))
        return ResponseSpec(status, {"error": code}, {})
