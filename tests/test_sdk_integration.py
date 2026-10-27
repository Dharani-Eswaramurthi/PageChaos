# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Offline compatibility checks against notion-client 3.1.0, not live Notion."""

import socket

import pytest
from notion_client import Client
from notion_client.helpers import iterate_paginated_api

from pagechaos import CursorProtocol, CursorScenario, audit


@pytest.mark.parametrize("sizes", [[10, 3, 10, 7], [0, 10, 0, 20]])
def test_existing_notion_sdk_helper_handles_uneven_and_empty_pages(sizes, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("The SDK attempted a real network connection")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    block_id = "00000000-0000-0000-0000-000000000001"
    scenario = CursorScenario(
        [{"id": str(i), "object": "block"} for i in range(30)],
        page_sizes=sizes,
        path=f"/v1/blocks/{block_id}/children",
        protocol=CursorProtocol(
            items_field="results",
            next_cursor_field="next_cursor",
            cursor_param="start_cursor",
            has_more_field="has_more",
        ),
        name="notion-sdk-offline-pagination",
    )

    def consume(http):
        notion = Client(client=http, auth="synthetic-test-token", base_url="https://pagechaos.test")
        yield from iterate_paginated_api(notion.blocks.children.list, block_id=block_id)

    report = audit(consume, scenario=scenario)
    report.assert_complete()
    assert report.request_count == 4
    assert report.observed_count == 30
