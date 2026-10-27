# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Offline pagination scenarios and snapshot-completeness checks."""

from ._audit import Consumer, ItemKey, audit
from ._models import (
    AuditReport,
    Finding,
    PaginationAssertionError,
    Record,
    RecordKey,
    RequestBudgetExceeded,
    RequestEvent,
)
from ._scenario import CursorProtocol, CursorScenario, Fault

__version__ = "0.1.0a1"
__all__ = [
    "AuditReport",
    "Consumer",
    "CursorProtocol",
    "CursorScenario",
    "Fault",
    "Finding",
    "ItemKey",
    "PaginationAssertionError",
    "Record",
    "RecordKey",
    "RequestBudgetExceeded",
    "RequestEvent",
    "audit",
]
