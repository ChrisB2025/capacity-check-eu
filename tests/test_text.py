"""The glossary and other explanatory text: complete, consistent, in sync."""

import re

import yaml

from engine import shock, text
from engine.params import Thresholds


def test_required_terms_are_defined():
    slugs = [t["slug"] for t in text.glossary()]
    assert len(slugs) == len(set(slugs)), "duplicate slugs"
    missing = set(text.REQUIRED_TERMS) - set(slugs)
    assert not missing, f"glossary lacks {sorted(missing)}"


def test_every_term_is_complete():
    groups = set(text.groups())
    for t in text.glossary():
        assert t["group"] in groups, t["slug"]
        for k in ("term", "definition", "why"):
            assert t.get(k), f"{t['slug']}: no {k}"
        for k in ("name", "detail", "url"):
            assert t["source"].get(k), f"{t['slug']}: source has no {k}"
        assert t["source"]["url"].startswith("https://"), t["slug"]


def test_defaults_fill_every_placeholder():
    vals = text.values()
    for t in text.glossary():
        f = text.filled(t["slug"], vals)
        for k in ("definition", "why", "caveat", "reasoning"):
            assert not text.PLACEHOLDER.search(f.get(k) or ""), (t["slug"], k)


def test_values_follow_the_run():
    p = {"shock_pct": 0.5,
         "thresholds": Thresholds(0.01, 0.03, 0.6, 0.8).__dict__}  # fmt: skip
    v = text.values(p)
    assert v["shock_pct"] == "0.5%"
    assert v["pressure_low"] == "1%" and v["pressure_high"] == "3%"
    assert v["slack_median"] == "the 60% point"
    assert v["slack_top"] == "the top fifth"


def test_glossary_markdown_is_in_sync():
    assert (
        text.GLOSSARY_MD.read_text(encoding="utf-8") == text.glossary_markdown()
    ), "docs/glossary.md is out of date: run `python -m engine glossary`"


def test_no_em_or_en_dashes_in_user_text():
    for f in text.TEXT_DIR.glob("*.yaml"):
        body = f.read_text(encoding="utf-8")
        assert not re.search("[" + chr(0x2013) + chr(0x2014) + "]", body), f.name


def test_composition_notes_cover_every_code():
    notes = text.composition_notes()
    for path in shock.COMPOSITION_DIR.glob("*.yaml"):
        comp = shock.load_composition(path.stem)
        assert comp.name in notes["compositions"], comp.name
        for ln in comp.lines:
            assert ln.code in notes["codes"], (comp.name, ln.code)


def test_responses_and_trades():
    r = text.responses()
    assert r["intro"] and r["binding"] and r["tight"]
    codes = [c for g in text.trades_se() for c in g["codes"]]
    assert len(codes) == len(set(codes))
    assert {"7123", "7126", "7411", "7125"} <= set(codes)


def test_text_files_are_valid_yaml():
    for f in text.TEXT_DIR.glob("*.yaml"):
        assert yaml.safe_load(f.read_text(encoding="utf-8"))
