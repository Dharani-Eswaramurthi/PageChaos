# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Optional explicit pytest fixture; no automatic auditing or network patching."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from ._audit import audit
from ._models import AuditReport


@pytest.fixture
def pagechaos_audit() -> Callable[..., AuditReport]:
    """Return the public audit function with a fresh session for every call."""
    return audit
