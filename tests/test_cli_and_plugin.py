# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys
from pathlib import Path

from pagechaos._demo import collect_correct, demo_scenario


def test_installed_pytest_fixture(pagechaos_audit):
    pagechaos_audit(collect_correct, scenario=demo_scenario()).assert_complete()


def test_cli_correct():
    result = subprocess.run(
        [sys.executable, "-m", "pagechaos", "demo", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["observed_count"] == 30


def test_cli_broken_has_failure_exit_and_json():
    result = subprocess.run(
        [sys.executable, "-m", "pagechaos", "demo", "--client", "short-page", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing_ids"] == list(range(14, 31))


def test_core_import_and_scenario_work_without_site_packages():
    source = str(Path(__file__).resolve().parents[1] / "src")
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "import pagechaos; "
        "s = pagechaos.CursorScenario([{'id': 1}]); "
        "assert s.session().dispatch('GET', '/items', {}).body['items'] == [{'id': 1}]; "
        "assert 'httpx' not in sys.modules"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", code, source],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
