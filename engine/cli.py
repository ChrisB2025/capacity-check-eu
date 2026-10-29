"""Command line entry point: ``python -m engine <command>``.

``fetch``          download, parse and validate every registered source
``import-figaro``  register a FIGARO file downloaded by hand from CIRCABC
``concordance``    regenerate engine/concordances/a64.csv
``gate1``          write the gate 1 coverage tables to docs/gate-1/
``run``            run the model; refuses compositions not yet confirmed
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable

from engine.sources.catalogue import PLANNED_SOURCES

EXIT_BAD_ARGS = 2
EXIT_NOT_IMPLEMENTED = 3
EXIT_SOURCE_FAILED = 4
EXIT_NOT_CONFIRMED = 5


def _loaders(force: bool) -> dict[str, Callable[[], object]]:
    from engine.sources import (
        arbetsformedlingen,
        ecfin,
        ela,
        eurostat,
        figaro,
        konj,
        scb,
    )

    return {
        "nama_10_gdp": lambda: eurostat.gdp(force),
        "nama_10_a64_e": lambda: eurostat.employment(force),
        "jvs_q_nace2": lambda: eurostat.vacancies(force),
        "figaro_2026_y2024": lambda: figaro.load_sdmx(2024, "2026", force),
        "figaro_2026_y2023": lambda: figaro.load_sdmx(2023, "2026", force),
        "ecfin": lambda: ecfin.load(force),
        "scb_yreg54bas": lambda: scb.load("scb_yreg54bas", force),
        "scb_yreg52bas": lambda: scb.load("scb_yreg52bas", force),
        "af_yrkesbarometer": lambda: arbetsformedlingen.load(force),
        "konj_construction": lambda: konj.load(force),
        "ela_shortages_2025": lambda: ela.load(force),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m engine",
        description="Capacity Check Europe model engine.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Download, parse and validate sources.")
    fetch.add_argument(
        "--dry-run",
        action="store_true",
        help="List the planned sources without downloading anything.",
    )
    fetch.add_argument("--only", nargs="+", help="Only these loader keys.")
    fetch.add_argument(
        "--force", action="store_true", help="Download again even if held."
    )

    imp = sub.add_parser(
        "import-figaro", help="Register a FIGARO file downloaded from CIRCABC."
    )
    imp.add_argument("path", help="The downloaded file, unedited.")
    imp.add_argument("--edition", required=True, help="Edition year, e.g. 2025.")
    imp.add_argument("--year", type=int, required=True, help="Reference year.")

    sub.add_parser("concordance", help="Regenerate the A64 concordance.")
    sub.add_parser("gate1", help="Write the gate 1 coverage tables.")
    ts = sub.add_parser("testset", help="Regenerate the fixed test set fixtures.")
    ts.add_argument(
        "--provisional",
        action="store_true",
        help="Allow a composition not yet confirmed.",
    )
    g2 = sub.add_parser("gate2", help="Run the gate 2 checks and write tables.")
    g2.add_argument(
        "--provisional",
        action="store_true",
        help="Allow a composition not yet confirmed.",
    )

    run = sub.add_parser("run", help="Run the model for one shock.")
    run.add_argument(
        "--shock",
        type=float,
        default=1.0,
        help="Shock size as a percentage of 2024 GDP, from 0.5 to 2.",
    )
    run.add_argument("--edition", default="2026", help="FIGARO edition year.")
    run.add_argument("--year", type=int, default=2024, help="FIGARO reference year.")
    run.add_argument("--composition", default="standard")
    run.add_argument(
        "--application", choices=["simultaneous", "own"], default="simultaneous"
    )
    run.add_argument("--slack", choices=["ecfin", "vacancy"], default="ecfin")
    run.add_argument("--pressure-low", type=float, default=0.02)
    run.add_argument("--pressure-high", type=float, default=0.05)
    run.add_argument(
        "--provisional",
        action="store_true",
        help="Allow a composition not yet confirmed; the run is marked provisional.",
    )
    return parser


def cmd_fetch(args: argparse.Namespace) -> int:
    if args.dry_run:
        for src in PLANNED_SOURCES:
            print(f"{src.key:20s} [{src.layer}] {src.publisher}: {src.dataset}")
            print(f"{'':20s} {src.location}")
        return 0
    loaders = _loaders(args.force)
    keys = args.only or list(loaders)
    unknown = set(keys) - set(loaders)
    if unknown:
        print(f"Unknown loader keys: {sorted(unknown)}", file=sys.stderr)
        return EXIT_BAD_ARGS
    failed = []
    for key in keys:
        print(f"{key} ...", flush=True)
        try:
            loaders[key]()
        except Exception as exc:  # report every failure, then carry on
            failed.append(key)
            print(f"  FAILED: {exc}", file=sys.stderr)
        else:
            print("  ok")
    print(
        "FIGARO 2025 edition is not fetched automatically: download it from "
        "CIRCABC and run `python -m engine import-figaro`.",
        file=sys.stderr,
    )
    return EXIT_SOURCE_FAILED if failed else 0


def cmd_import_figaro(args: argparse.Namespace) -> int:
    from engine.sources import figaro

    raw = figaro.import_circabc(args.path, args.edition, args.year)
    print(f"{raw.path.name}  {raw.sha256}")
    _, out, checks = figaro.load_circabc(args.edition, args.year)
    print(out)
    print(json.dumps(checks, indent=1))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not 0.5 <= args.shock <= 2.0:
        print("--shock must be between 0.5 and 2.", file=sys.stderr)
        return EXIT_BAD_ARGS
    from engine import cdm, pipeline
    from engine.params import RunParams, Thresholds
    from engine.shock import CompositionNotConfirmed

    params = RunParams(
        shock_pct=args.shock,
        edition=str(args.edition),
        ref_year=args.year,
        composition=args.composition,
        application=args.application,
        slack_indicator=args.slack,
        thresholds=Thresholds(
            pressure_low=args.pressure_low, pressure_high=args.pressure_high
        ),
    )
    try:
        result = pipeline.run(params, allow_unconfirmed=args.provisional)
    except CompositionNotConfirmed as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_NOT_CONFIRMED
    except FileNotFoundError as exc:
        print(f"Missing input: {exc.filename or exc}", file=sys.stderr)
        return EXIT_BAD_ARGS
    out = pipeline.save(result)
    cdm_dir = out / "cdm"
    cdm_dir.mkdir(exist_ok=True)
    for name, df in cdm.write(result).items():
        df.to_csv(cdm_dir / f"{name}.csv", index=False, lineterminator=chr(10))
    print(out)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "fetch":
        return cmd_fetch(args)
    if args.command == "import-figaro":
        return cmd_import_figaro(args)
    if args.command == "concordance":
        from engine import concordance

        print(concordance.write())
        return 0
    if args.command == "testset":
        from engine import testset

        print(testset.generate(allow_unconfirmed=args.provisional))
        return 0
    if args.command == "gate2":
        from engine import gate2
        from engine.shock import CompositionNotConfirmed

        try:
            summary = gate2.run(allow_unconfirmed=args.provisional)
        except CompositionNotConfirmed as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_NOT_CONFIRMED
        brief = {k: v for k, v in summary.items() if k != "runs"}
        print(json.dumps(brief, indent=1))
        return 0
    if args.command == "gate1":
        from engine import gate1

        print(json.dumps(gate1.run(), indent=1))
        return 0
    return cmd_run(args)
