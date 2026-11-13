# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Smoke-test a wheel in a fresh environment, with and without optional packages."""

import argparse
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def run(*command: str, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, help="Defaults to the only wheel in dist/")
    parser.add_argument("--wheelhouse", type=Path, help="Install dependencies offline from here")
    args = parser.parse_args()
    wheels = [args.wheel] if args.wheel else list(Path("dist").glob("*.whl"))
    if len(wheels) != 1:
        parser.error("Expected exactly one wheel; clean dist/ or pass --wheel")
    wheel = wheels[0].resolve(strict=True)
    wheelhouse = args.wheelhouse.resolve(strict=True) if args.wheelhouse else None
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="pagechaos-install-") as directory:
        scratch = Path(directory)
        environment = scratch / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        executables = environment / ("Scripts" if os.name == "nt" else "bin")
        python = str(executables / ("python.exe" if os.name == "nt" else "python"))
        run(python, "-m", "pip", "install", "--no-deps", "--no-index", str(wheel), cwd=scratch)
        run(
            python,
            "-I",
            "-c",
            """
import importlib.util
import sys
from pathlib import Path
import pagechaos

assert Path(pagechaos.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert importlib.util.find_spec("httpx") is None
assert importlib.util.find_spec("pytest") is None
scenario = pagechaos.CursorScenario([{"id": 1}])
assert scenario.records == ({"id": 1},)
assert scenario.session().dispatch("GET", "/items", {}).body["items"] == [{"id": 1}]
try:
    pagechaos.audit(lambda client: [], scenario=scenario)
except ImportError as exc:
    assert "pagechaos[httpx]" in str(exc)
else:
    raise AssertionError("The core installation must explain the missing HTTPX extra")
print("Core wheel import, scenario and optional-dependency checks passed.")
""",
            cwd=scratch,
        )
        index = ["--no-index", "--find-links", str(wheelhouse)] if wheelhouse else []
        run(
            python,
            "-m",
            "pip",
            "install",
            *index,
            f"{wheel}[pytest]",
            cwd=scratch,
        )
        # Use the installed distribution's plugin with no checkout pytest configuration.
        config = scratch / "pytest.ini"
        config.write_text("[pytest]\n", encoding="utf-8")
        run(
            python,
            "-I",
            "-m",
            "pytest",
            "-q",
            "-c",
            str(config),
            str(root / "examples/test_pagination.py"),
            str(root / "tests/test_audit.py"),
            cwd=scratch,
        )
        run(
            python,
            "-I",
            "-c",
            """
import json
import subprocess
import sys
from pathlib import Path
import pagechaos

assert Path(pagechaos.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
for client, status, count in [("correct", 0, 30), ("short-page", 1, 13)]:
    result = subprocess.run(
        [sys.executable, "-I", "-m", "pagechaos", "demo", "--client", client, "--json"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == status, result.stderr
    report = json.loads(result.stdout)
    assert report["observed_count"] == count
    assert report["ok"] == (status == 0)
print("Installed module CLI success and failure checks passed.")
""",
            cwd=scratch,
        )
        console = executables / ("pagechaos.exe" if os.name == "nt" else "pagechaos")
        run(str(console), "--version", cwd=scratch)
    print("Fresh wheel installation verified.")


if __name__ == "__main__":
    main()
