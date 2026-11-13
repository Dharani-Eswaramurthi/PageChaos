# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""Validate release identity and optionally require the selected version tag."""

import argparse
import os
import tomllib
from pathlib import Path

from packaging.version import Version

import pagechaos

parser = argparse.ArgumentParser()
parser.add_argument("--require-tag", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
version = metadata["version"]
assert version == pagechaos.__version__, "Package and metadata versions differ"
assert metadata["name"] == "pagechaos"
assert metadata["license"] == "Apache-2.0"
assert metadata["authors"] == [{"name": "Dharani Eswaramurthi"}]
assert len(metadata["urls"]) >= 4
parsed_version = Version(version)
stable = not (parsed_version.is_prerelease or parsed_version.is_devrelease)
assert ("Development Status :: 5 - Production/Stable" in metadata["classifiers"]) == stable, (
    "Development status must match the release version"
)
assert f"version: {version}" in (root / "CITATION.cff").read_text(encoding="utf-8").splitlines(), (
    "Citation and package versions differ"
)
assert f"## {version} " in (root / "CHANGELOG.md").read_text(encoding="utf-8"), (
    "Changelog is missing this release"
)
readme = (root / "README.md").read_text(encoding="utf-8")
for extra in ("httpx", "pytest"):
    assert f"pagechaos[{extra}]=={version}" in readme, "README installation version differs"
if args.require_tag:
    assert os.environ.get("GITHUB_REF_TYPE") == "tag", "Select a version tag"
    assert os.environ.get("GITHUB_REF_NAME") == f"v{version}", "Tag and version differ"
if output := os.environ.get("GITHUB_OUTPUT"):
    with Path(output).open("a", encoding="utf-8") as stream:
        stream.write(f"version={version}\n")
print(f"Release identity verified: pagechaos {version}")
