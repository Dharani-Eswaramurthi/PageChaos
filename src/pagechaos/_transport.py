# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Optional HTTPX adapter; no real-network fallback is configured."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._scenario import ScenarioSession

if TYPE_CHECKING:
    import httpx


def make_client(session: ScenarioSession, *, base_url: str) -> httpx.Client:
    try:
        import httpx
    except ImportError as exc:
        raise ImportError('HTTPX support requires: pip install "pagechaos[httpx]"') from exc
    origin = httpx.URL(base_url)
    if origin.scheme not in {"http", "https"} or not origin.host:
        raise ValueError("base_url must be an absolute HTTP(S) URL")
    if origin.username or origin.password or origin.query or origin.fragment:
        raise ValueError("base_url cannot contain credentials, a query, or a fragment")
    if origin.path not in {"", "/"}:
        raise ValueError("Use an origin-only base_url and set the endpoint in scenario.path")

    def handle(request: httpx.Request) -> httpx.Response:
        cursor_values = request.url.params.get_list(session.scenario.protocol.cursor_param)
        query = dict(request.url.params)
        same_origin = (request.url.scheme, request.url.host, request.url.port) == (
            origin.scheme,
            origin.host,
            origin.port,
        )
        response = session.dispatch(
            request.method,
            request.url.path,
            query,
            origin_matches=same_origin,
            ambiguous_cursor=len(cursor_values) > 1,
        )
        if response.status_code is None:
            raise httpx.ReadTimeout("PageChaos injected a read timeout", request=request)
        return httpx.Response(
            response.status_code, json=response.body, headers=response.headers, request=request
        )

    return httpx.Client(
        transport=httpx.MockTransport(handle),
        base_url=base_url,
        trust_env=False,
        follow_redirects=False,
    )
