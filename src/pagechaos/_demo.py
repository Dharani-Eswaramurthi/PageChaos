# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Two small consumers for the offline demo and validation suite."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from ._models import Record
from ._scenario import CursorScenario

if TYPE_CHECKING:
    import httpx


def demo_scenario() -> CursorScenario:
    return CursorScenario(
        [{"id": number, "name": f"item-{number}"} for number in range(1, 31)],
        page_sizes=[10, 3, 10, 7],
        name="short-page-with-continuation",
    )


def collect_correct(client: httpx.Client) -> Iterator[Record]:
    cursor: str | None = None
    while True:
        response = client.get("/items", params={"cursor": cursor} if cursor else {})
        response.raise_for_status()
        data = response.json()
        yield from data["items"]
        cursor = data.get("next_cursor")
        if not cursor:
            return


def collect_short_page(client: httpx.Client) -> Iterator[Record]:
    cursor: str | None = None
    while True:
        response = client.get("/items", params={"cursor": cursor} if cursor else {})
        response.raise_for_status()
        data = response.json()
        yield from data["items"]
        if len(data["items"]) < 10:
            return
        cursor = data.get("next_cursor")
        if not cursor:
            return
