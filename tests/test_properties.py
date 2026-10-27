# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

from hypothesis import given, settings
from hypothesis import strategies as st

from pagechaos import CursorScenario, audit
from pagechaos._demo import collect_correct


@settings(max_examples=150, deadline=None, derandomize=True)
@given(
    sizes=st.lists(st.integers(min_value=0, max_value=8), max_size=12),
    tail=st.integers(min_value=0, max_value=16),
    default_size=st.integers(min_value=1, max_value=9),
)
def test_correct_client_is_complete_across_empty_and_uneven_pages(sizes, tail, default_size):
    count = sum(sizes) + tail
    expected = [{"id": i, "payload": {"value": i * 7}} for i in range(count)]
    scenario = CursorScenario(expected, page_sizes=sizes, page_size=default_size)
    report = audit(collect_correct, scenario=scenario, max_requests=50)
    report.assert_complete()
    assert list(report.records) == expected
    assert report.request_count == len(scenario.page_sizes)


@settings(max_examples=75, deadline=None, derandomize=True)
@given(
    token=st.text(
        alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1, max_size=40
    ).filter(lambda value: value != "initial"),
)
def test_arbitrary_opaque_tokens_round_trip(token):
    scenario = CursorScenario(
        [{"id": "one"}, {"id": "two"}], page_size=1, cursor_tokens=["initial", token]
    )
    report = audit(collect_correct, scenario=scenario)
    report.assert_complete()
    assert report.trace[1].cursor == token
