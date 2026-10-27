# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""pytest example: python -m pytest examples/test_pagination.py"""

from pagechaos import CursorScenario
from pagechaos._demo import collect_correct


def test_snapshot_export(pagechaos_audit):
    scenario = CursorScenario([{"id": i} for i in range(12)], page_sizes=[3, 0, 9])
    pagechaos_audit(collect_correct, scenario=scenario).assert_complete()
