# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import socket
from collections.abc import Iterator

import httpx
import pytest

from pagechaos import CursorProtocol, CursorScenario, Fault, PaginationAssertionError, audit
from pagechaos._demo import collect_correct, collect_short_page, demo_scenario


def codes(report):
    return {finding.code for finding in report.findings}


def test_correct_consumer_keeps_short_page_continuation():
    report = audit(collect_correct, scenario=demo_scenario())
    report.assert_complete()
    assert report.observed_count == 30
    assert report.request_count == 4


def test_short_page_mutant_loses_seventeen_records():
    report = audit(collect_short_page, scenario=demo_scenario())
    assert report.observed_count == 13
    assert report.missing_ids == tuple(range(14, 31))
    assert "CONTINUATION_REMAINING" in codes(report)
    with pytest.raises(PaginationAssertionError, match="17 snapshot"):
        report.assert_complete()


@pytest.mark.parametrize("terminal", ["null", "empty", "missing"])
def test_terminal_encodings(terminal):
    report = audit(
        collect_correct,
        scenario=CursorScenario([{"id": i} for i in range(20)], terminal=terminal),
    )
    report.assert_complete()
    assert report.request_count == 2


def test_empty_page_does_not_mean_complete():
    scenario = CursorScenario([{"id": i} for i in range(4)], page_sizes=[0, 2, 0, 2])
    report = audit(collect_correct, scenario=scenario)
    report.assert_complete()
    assert [event.record_count for event in report.trace] == [0, 2, 0, 2]


def test_empty_page_mutant_stops_with_no_records():
    def broken(client):
        response = client.get("/items").json()
        if not response["items"]:
            return []
        raise AssertionError("Fixture should have started with an empty page")

    report = audit(broken, scenario=CursorScenario([{"id": 1}], page_sizes=[0, 1]))
    assert report.missing_ids == (1,)
    assert not report.ok


def test_empty_dataset_still_requires_a_terminal_response():
    audit(collect_correct, scenario=CursorScenario([])).assert_complete()
    report = audit(lambda client: [], scenario=CursorScenario([]))
    assert "NO_REQUESTS" in codes(report)


def test_opaque_cursor_is_preserved_exactly():
    token = "1756123456789012345+%&=/漢字"
    scenario = CursorScenario([{"id": 1}, {"id": 2}], page_size=1, cursor_tokens=["initial", token])
    report = audit(collect_correct, scenario=scenario)
    report.assert_complete()
    assert report.trace[1].cursor == token


def test_float_cursor_mutant_is_rejected():
    def broken(client):
        first = client.get("/items").json()
        yield from first["items"]
        cursor = str(float(first["next_cursor"]))
        response = client.get("/items", params={"cursor": cursor})
        response.raise_for_status()
        yield from response.json()["items"]

    scenario = CursorScenario(
        [{"id": 1}, {"id": 2}], page_size=1, cursor_tokens=["initial", "1756123456789012345"]
    )
    report = audit(broken, scenario=scenario)
    assert report.missing_ids == (2,)
    assert "PROTOCOL_ERROR" in codes(report)


def test_repeated_page_reports_duplicates_even_if_later_requests_recover():
    scenario = CursorScenario(
        [{"id": i} for i in range(6)], page_size=2, faults=[Fault.repeat_cursor(2)]
    )
    report = audit(collect_correct, scenario=scenario)
    assert report.terminal_reached
    assert report.missing_ids == ()
    assert report.duplicate_ids == (2, 3)
    assert not report.ok


def test_request_budget_interrupts_broad_exception_retry_loops():
    def broken(client) -> Iterator[dict]:
        while True:
            try:
                yield from client.get("/items").json()["items"]
            except Exception:
                continue

    report = audit(
        broken, scenario=CursorScenario([{"id": 1}, {"id": 2}], page_size=1), max_requests=5
    )
    assert report.budget_exceeded
    assert report.request_count == 5
    assert report.missing_ids == (2,)


@pytest.mark.parametrize("fault", [Fault.http_error(2, 503), Fault.timeout(2)])
def test_late_failure_retains_already_yielded_records(fault):
    scenario = CursorScenario([{"id": i} for i in range(6)], page_size=2, faults=[fault])
    report = audit(collect_correct, scenario=scenario)
    assert report.observed_count == 2
    assert report.missing_ids == (2, 3, 4, 5)
    assert report.error is not None
    assert "CLIENT_ERROR" in codes(report)


def test_429_retry_keeps_cursor_and_exercises_header():
    delays = []

    def retrying(client):
        cursor = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            response = client.get("/items", params=params)
            if response.status_code == 429:
                delays.append(response.headers["Retry-After"])
                continue
            response.raise_for_status()
            payload = response.json()
            yield from payload["items"]
            cursor = payload.get("next_cursor")
            if not cursor:
                return

    scenario = CursorScenario(
        [{"id": i} for i in range(4)],
        page_size=2,
        faults=[Fault.http_error(2, 429, retry_after="2")],
    )
    report = audit(retrying, scenario=scenario)
    report.assert_complete()
    assert delays == ["2"]  # Header handling only; no claim about elapsed-time compliance.
    assert report.trace[1].cursor == report.trace[2].cursor
    assert [event.status_code for event in report.trace] == [200, 429, 200]


def test_scheduled_but_unreached_fault_cannot_silently_pass():
    report = audit(collect_correct, scenario=CursorScenario([{"id": 1}], faults=[Fault.timeout(3)]))
    assert "UNEXERCISED_FAULT" in codes(report)
    assert not report.ok


def test_runs_are_isolated():
    scenario = CursorScenario([{"id": 1}, {"id": 2}], page_size=1, faults=[Fault.http_error(2)])
    first = audit(collect_correct, scenario=scenario)
    second = audit(collect_correct, scenario=scenario)
    assert first.to_dict() == second.to_dict()
    assert first.trace[1].status_code == second.trace[1].status_code == 503


def test_records_are_detached_from_inputs_and_previous_responses():
    records = [{"id": 1, "tags": ["original"]}]
    scenario = CursorScenario(records)
    records[0]["tags"].append("caller-change")
    exposed = scenario.records
    exposed[0]["tags"].append("property-change")
    audit(collect_correct, scenario=scenario).assert_complete()
    assert scenario.records[0]["tags"] == ["original"]


def test_custom_endpoint_and_flat_protocol():
    scenario = CursorScenario(
        [{"key": "a"}, {"key": "b"}],
        page_size=1,
        path="/v2/data",
        protocol=CursorProtocol("data", "after", "page_token"),
    )

    def consume(client):
        cursor = None
        while True:
            response = client.get("/v2/data", params={"page_token": cursor} if cursor else {})
            response.raise_for_status()
            payload = response.json()
            yield from payload["data"]
            cursor = payload.get("after")
            if not cursor:
                return

    audit(consume, scenario=scenario, item_key="key").assert_complete()


@pytest.mark.parametrize("change", ["duplicate", "unexpected", "modified", "missing-key"])
def test_output_contract_mutants(change):
    def broken(client):
        rows = list(collect_correct(client))
        if change == "duplicate":
            rows.append(rows[0])
        elif change == "unexpected":
            rows.append({"id": 99})
        elif change == "modified":
            rows[0]["text"] = "changed"
        else:
            rows.append({"other": "value"})
        return rows

    report = audit(broken, scenario=CursorScenario([{"id": 1, "text": "original"}]))
    expected = {
        "duplicate": "DUPLICATE_RECORDS",
        "unexpected": "UNEXPECTED_RECORDS",
        "modified": "MODIFIED_RECORDS",
        "missing-key": "INVALID_RECORD_ID",
    }
    assert expected[change] in codes(report)


def test_callable_identity():
    scenario = CursorScenario([{"tenant": "a", "number": 1}, {"tenant": "b", "number": 1}])
    audit(
        collect_correct, scenario=scenario, item_key=lambda row: f"{row['tenant']}:{row['number']}"
    ).assert_complete()


def test_string_and_integer_ids_remain_distinct():
    report = audit(collect_correct, scenario=CursorScenario([{"id": 1}, {"id": "1"}]))
    report.assert_complete()
    assert report.unique_count == 2


@pytest.mark.parametrize("records", [[{"id": 1}, {"id": 1}], [{"other": 1}], [{"id": True}]])
def test_bad_snapshot_identity_is_configuration_error(records):
    with pytest.raises(ValueError):
        audit(collect_correct, scenario=CursorScenario(records))


@pytest.mark.parametrize("target", ["/wrong", "https://other.test/items"])
def test_unexpected_request_never_falls_back_to_network(target, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("A real network connection was attempted")

    monkeypatch.setattr(socket.socket, "connect", forbidden)

    def broken(client):
        response = client.get(target)
        response.raise_for_status()
        return response.json()["items"]

    report = audit(broken, scenario=CursorScenario([{"id": 1}]))
    assert "PROTOCOL_ERROR" in codes(report)
    assert isinstance(report.error, httpx.HTTPStatusError)


def test_correct_client_never_uses_real_sockets(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("A real network connection was attempted")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    audit(collect_correct, scenario=demo_scenario()).assert_complete()


def test_duplicate_cursor_parameters_are_rejected_even_if_one_is_valid():
    scenario = CursorScenario([{"id": 1}], cursor_tokens=["\x00ambiguous-cursor"])

    def broken(client):
        response = client.get(
            "/items", params=[("cursor", "one"), ("cursor", "\x00ambiguous-cursor")]
        )
        response.raise_for_status()
        return response.json()["items"]

    report = audit(broken, scenario=scenario)
    assert "PROTOCOL_ERROR" in codes(report)


def test_reports_do_not_serialize_headers_record_bodies_or_exception_text():
    secret = "sensitive-test-value"

    def broken(client):
        client.headers["Authorization"] = secret
        client.get("/items")
        raise RuntimeError(secret)

    report = audit(broken, scenario=CursorScenario([{"id": 1, "secret": secret}]))
    serialized = report.to_json()
    assert secret not in serialized
    assert "RuntimeError" in serialized
    assert json.loads(serialized)["schema_version"] == 1
    assert secret not in report.explain()


@pytest.mark.parametrize("result", [None, "text", {"id": 1}, [42]])
def test_invalid_consumer_results_become_findings(result):
    report = audit(lambda client: result, scenario=CursorScenario([{"id": 1}]))
    assert "CLIENT_ERROR" in codes(report)


def test_async_consumer_is_rejected_without_unawaited_coroutine_warning():
    async def wrong(client):
        return []

    report = audit(wrong, scenario=CursorScenario([]))
    assert isinstance(report.error, TypeError)
    assert "synchronous" in str(report.error)


@pytest.mark.parametrize("exception", [KeyboardInterrupt, SystemExit])
def test_process_control_exceptions_propagate(exception):
    def interrupted(client):
        raise exception()

    with pytest.raises(exception):
        audit(interrupted, scenario=CursorScenario([]))


@pytest.mark.parametrize(
    "url",
    [
        "ftp://host",
        "https://u:p@host",
        "https://host/path",
        "https://host/?token=secret",
        "https://host/#fragment",
    ],
)
def test_invalid_base_urls_are_configuration_errors(url):
    with pytest.raises(ValueError):
        audit(collect_correct, scenario=CursorScenario([]), base_url=url)


def test_iterator_cleanup_runs_before_client_is_closed():
    closed = []

    def broken(client):
        try:
            yield {"id": 1}
            yield 42
        finally:
            closed.append(client.is_closed)

    report = audit(broken, scenario=CursorScenario([{"id": 1}]))
    assert isinstance(report.error, TypeError)
    assert closed == [False]


def test_yielding_without_requests_is_bounded():
    closed = []

    def broken(client):
        try:
            while True:
                yield {"id": 1}
        finally:
            closed.append(True)

    report = audit(broken, scenario=CursorScenario([{"id": 1}]), max_records=7)
    assert report.observed_count == 7
    assert report.record_budget_exceeded
    assert "RECORD_BUDGET_EXCEEDED" in codes(report)
    assert closed == [True]


def test_exact_record_limit_can_complete_cleanly():
    report = audit(collect_correct, scenario=CursorScenario([{"id": 1}]), max_records=1)
    report.assert_complete()


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_record_budget(value):
    with pytest.raises(ValueError):
        audit(collect_correct, scenario=CursorScenario([]), max_records=value)


def test_nested_nonstring_keys_are_rejected_without_coercion():
    with pytest.raises(TypeError, match="nested"):
        CursorScenario([{"id": 1, "nested": {1: "value"}}])
