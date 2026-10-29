"""Phase 0 smoke tests: the package imports and the CLI parses."""

import engine
from engine.cli import EXIT_BAD_ARGS, EXIT_NOT_IMPLEMENTED, build_parser, main
from engine.sources.catalogue import PLANNED_SOURCES


def test_package_imports():
    assert engine.__version__


def test_cli_parses_run_arguments():
    args = build_parser().parse_args(["run", "--shock", "1.0", "--edition", "2026"])
    assert args.command == "run"
    assert args.shock == 1.0
    assert args.edition == 2026


def test_fetch_dry_run_lists_every_source(capsys):
    assert main(["fetch", "--dry-run"]) == 0
    out = capsys.readouterr().out
    for src in PLANNED_SOURCES:
        assert src.key in out


def test_run_is_not_implemented_yet():
    assert main(["run", "--shock", "1.0"]) == EXIT_NOT_IMPLEMENTED


def test_run_rejects_out_of_range_shock():
    assert main(["run", "--shock", "3.0"]) == EXIT_BAD_ARGS


def test_catalogue_keys_are_unique():
    keys = [s.key for s in PLANNED_SOURCES]
    assert len(keys) == len(set(keys))
