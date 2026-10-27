# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Offline example: install the dev extra, including notion-client==3.1.0."""

from notion_client import Client
from notion_client.helpers import iterate_paginated_api

from pagechaos import CursorProtocol, CursorScenario, audit

BLOCK_ID = "00000000-0000-0000-0000-000000000001"


def collect(http):
    sdk = Client(client=http, auth="synthetic-test-token", base_url="https://pagechaos.test")
    yield from iterate_paginated_api(sdk.blocks.children.list, block_id=BLOCK_ID)


def main():
    scenario = CursorScenario(
        [{"id": str(i), "object": "block"} for i in range(30)],
        page_sizes=[10, 0, 3, 17],
        path=f"/v1/blocks/{BLOCK_ID}/children",
        protocol=CursorProtocol("results", "next_cursor", "start_cursor", "has_more"),
        name="notion-sdk-synthetic-block-list",
    )
    report = audit(collect, scenario=scenario)
    report.assert_complete()
    print(report.explain())


if __name__ == "__main__":
    main()
