# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Verify that TestPyPI serves this run's exact wheel, then install and smoke it."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--version", required=True)
args = parser.parse_args()
expected = list(Path("dist").glob("*.whl"))
assert len(expected) == 1
destination = Path("work/testpypi-download")
destination.mkdir(parents=True, exist_ok=True)
download = [
    sys.executable,
    "-m",
    "pip",
    "download",
    "--no-deps",
    "--only-binary=:all:",
    "--no-cache-dir",
    "--index-url",
    "https://test.pypi.org/simple/",
    "--dest",
    str(destination),
    f"pagechaos=={args.version}",
]
for attempt in range(6):
    result = subprocess.run(download, check=False)
    if result.returncode == 0:
        break
    if attempt == 5:
        raise SystemExit(result.returncode)
    time.sleep(10)
with urlopen(f"https://test.pypi.org/pypi/pagechaos/{args.version}/json", timeout=30) as reply:
    published = json.load(reply)
digests = {item["filename"]: item["digests"]["sha256"] for item in published["urls"]}
for artifact in Path("dist").iterdir():
    assert digests.get(artifact.name) == hashlib.sha256(artifact.read_bytes()).hexdigest(), (
        f"TestPyPI artifact differs from this run: {artifact.name}"
    )
wheels = list(destination.glob("*.whl"))
assert len(wheels) == 1
assert (
    hashlib.sha256(wheels[0].read_bytes()).digest()
    == hashlib.sha256(expected[0].read_bytes()).digest()
), "TestPyPI wheel differs from the reviewed artifact"
subprocess.run(
    [sys.executable, "-m", "pip", "install", "--no-deps", "--force-reinstall", str(wheels[0])],
    check=True,
)
for client, code in [("correct", 0), ("short-page", 1)]:
    result = subprocess.run(
        [sys.executable, "-I", "-m", "pagechaos", "demo", "--client", client],
        check=False,
    )
    assert result.returncode == code, (client, result.returncode)
print("TestPyPI wheel hash and installed demonstrations verified.")
