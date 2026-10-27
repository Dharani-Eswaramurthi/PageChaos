# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

import pytest

from pagechaos import CursorProtocol, CursorScenario, Fault, RequestBudgetExceeded


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_default_page_size(value):
    with pytest.raises(ValueError):
        CursorScenario([], page_size=value)


@pytest.mark.parametrize("sizes", [[-1], [True], [1.5], [2]])
def test_invalid_explicit_page_sizes(sizes):
    with pytest.raises(ValueError):
        CursorScenario([{"id": 1}], page_sizes=sizes)


@pytest.mark.parametrize("tokens", [[], [""], ["a", "a"], ["a", 2], "ab"])
def test_invalid_cursor_tokens(tokens):
    with pytest.raises((ValueError, TypeError)):
        CursorScenario([{"id": 1}, {"id": 2}], page_size=1, cursor_tokens=tokens)


@pytest.mark.parametrize(
    "kwargs",
    [{"items_field": ""}, {"cursor_param": ""}, {"items_field": "x", "next_cursor_field": "x"}],
)
def test_protocol_field_validation(kwargs):
    with pytest.raises(ValueError):
        CursorProtocol(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"at_request": 0, "kind": "timeout"},
        {"at_request": True, "kind": "timeout"},
        {"at_request": 1, "kind": "unknown"},
        {"at_request": 1, "kind": "http_error", "status_code": 200},
        {"at_request": 1, "kind": "http_error", "status_code": True},
        {"at_request": 1, "kind": "timeout", "retry_after": "2"},
        {"at_request": 1, "kind": "http_error", "status_code": 429, "retry_after": "1\r\nx: y"},
    ],
)
def test_fault_validation(kwargs):
    with pytest.raises(ValueError):
        Fault(**kwargs)


def test_one_fault_per_request():
    with pytest.raises(ValueError):
        CursorScenario([], faults=[Fault.timeout(1), Fault.http_error(1)])


@pytest.mark.parametrize("max_requests", [0, -1, True, 1.2])
def test_invalid_budget(max_requests):
    with pytest.raises(ValueError):
        CursorScenario([]).session(max_requests=max_requests)


def test_session_budget_does_not_dispatch_one_extra_response():
    session = CursorScenario([]).session(max_requests=1)
    assert session.dispatch("GET", "/items", {}).status_code == 200
    with pytest.raises(RequestBudgetExceeded):
        session.dispatch("GET", "/items", {})
    assert len(session.events) == 1


def test_explicit_sizes_are_prefix_and_remainder_is_partitioned():
    scenario = CursorScenario([{"id": i} for i in range(17)], page_size=5, page_sizes=[0, 2])
    assert scenario.page_sizes == (0, 2, 5, 5, 5)


def test_non_finite_numbers_are_rejected():
    with pytest.raises(ValueError):
        CursorScenario([{"id": 1, "value": float("nan")}])


@pytest.mark.parametrize("path", ["items", "/items?key=value", "/items#fragment", None])
def test_invalid_path(path):
    with pytest.raises(ValueError):
        CursorScenario([], path=path)


def test_invalid_protocol_object():
    with pytest.raises(TypeError):
        CursorScenario([], protocol="wrong")


@pytest.mark.parametrize("field", ["", 1, "items", "next_cursor"])
def test_has_more_field_validation(field):
    with pytest.raises(ValueError):
        CursorProtocol(has_more_field=field)
