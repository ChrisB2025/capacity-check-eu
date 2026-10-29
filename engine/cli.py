"""Command line entry point: ``python -m engine <command>``.

Phase 0 provides argument parsing only. ``fetch`` lists the planned sources;
``run`` stops with a message until the model is built in Phase 2.
"""

from __future__ import annotations

import argparse
import sys

from engine.sources.catalogue import PLANNED_SOURCES

EXIT_BAD_ARGS = 2
EXIT_NOT_IMPLEMENTED = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m engine",
        description="Capacity Check Europe model engine.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Download every registered source.")
    fetch.add_argument(
        "--dry-run",
        action="store_true",
        help="List the planned sources without downloading anything.",
    )

    run = sub.add_parser("run", help="Run the model for one shock.")
    run.add_argument(
        "--shock",
        type=float,
        default=1.0,
        help="Shock size as a percentage of 2024 GDP, from 0.5 to 2.",
    )
    run.add_argument("--edition", type=int, default=2026, help="FIGARO edition year.")
    return parser


def cmd_fetch(args: argparse.Namespace) -> int:
    for src in PLANNED_SOURCES:
        print(f"{src.key:20s} [{src.layer}] {src.publisher}: {src.dataset}")
        print(f"{'':20s} {src.location}")
    if not args.dry_run:
        print("\nDownloads arrive in Phase 1. Nothing was fetched.", file=sys.stderr)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not 0.5 <= args.shock <= 2.0:
        print("--shock must be between 0.5 and 2.", file=sys.stderr)
        return EXIT_BAD_ARGS
    print("The model arrives in Phase 2. No run was performed.", file=sys.stderr)
    return EXIT_NOT_IMPLEMENTED


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "fetch":
        return cmd_fetch(args)
    return cmd_run(args)
