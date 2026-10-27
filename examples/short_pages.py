# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Run after installing this checkout with the httpx extra."""

from collections.abc import Iterator

import httpx

from pagechaos import CursorScenario, PaginationAssertionError, Record, audit


def fetch_all_items(http: httpx.Client) -> Iterator[Record]:
    cursor = None
    while True:
        response = http.get("/items", params={"cursor": cursor} if cursor else {})
        response.raise_for_status()
        payload = response.json()
        yield from payload["items"]
        cursor = payload.get("next_cursor")
        if not cursor:
            return


def stop_on_short_page(http: httpx.Client) -> Iterator[Record]:
    cursor = None
    while True:
        response = http.get("/items", params={"cursor": cursor} if cursor else {})
        response.raise_for_status()
        payload = response.json()
        yield from payload["items"]
        if len(payload["items"]) < 10:
            return
        cursor = payload.get("next_cursor")
        if not cursor:
            return


def main() -> None:
    scenario = CursorScenario(
        [{"id": i} for i in range(1, 31)],
        page_sizes=[10, 3, 10, 7],
        name="short-page-with-continuation",
    )
    correct = audit(fetch_all_items, scenario=scenario)
    correct.assert_complete()
    print(correct.explain())

    broken = audit(stop_on_short_page, scenario=scenario)
    try:
        broken.assert_complete()
    except PaginationAssertionError:
        print("\nDeliberate defect detected:")
        print(broken.explain())
    else:
        raise AssertionError("The deliberately broken consumer unexpectedly passed")


if __name__ == "__main__":
    main()
