# Copyright 2026 Dharani Eswaramurthi
# SPDX-License-Identifier: Apache-2.0

"""CLI demonstrations; this command never targets a live API."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__, audit
from ._demo import collect_correct, collect_short_page, demo_scenario


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pagechaos")
    parser.add_argument("--version", action="version", version=__version__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    demo = subcommands.add_parser("demo", help="Test a bundled consumer against synthetic pages")
    demo.add_argument("--client", choices=["correct", "short-page"], default="correct")
    demo.add_argument("--json", action="store_true", help="Print a structured report")
    args = parser.parse_args(argv)
    consumer = collect_correct if args.client == "correct" else collect_short_page
    report = audit(consumer, scenario=demo_scenario())
    print(report.to_json() if args.json else report.explain())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
