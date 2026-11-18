"""Explanatory text shared by the web app and the documents.

The files in ``engine/text/`` hold every definition, reason and caveat the
web app shows, so that tooltips, the glossary page and ``docs/glossary.md``
cannot drift apart. ``python -m engine glossary`` writes the reference table
for the pressure thresholds and then ``docs/glossary.md``.
"""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path

import yaml

from engine.params import RunParams
from engine.sources._common import REPO_ROOT

TEXT_DIR = Path(__file__).resolve().parent / "text"
GLOSSARY_MD = REPO_ROOT / "docs" / "glossary.md"

# Terms the review of 18 November 2026 asked to be defined, at least.
REQUIRED_TERMS = (
    "input-output-table", "figaro", "nace-a64", "shock", "composition",
    "jobs-conversion", "employment-multiplier", "labour-shortage-indicator",
    "pressure", "slack-current", "slack-percentile", "headline",
    "unrated-share", "origin", "occupation-share", "clear", "tight",
    "binding", "no-rating", "estimated-risk-category", "thresholds",
    "risk-indicator",
)  # fmt: skip

RISK_LABEL = (
    "Ratings are estimated risk categories: risk indicators, not factual "
    "judgements about whether a programme can be delivered."
)

PLACEHOLDER = re.compile(r"\{(\w+)\}")


@cache
def _load(name: str) -> dict:
    with open(TEXT_DIR / f"{name}.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def glossary() -> list[dict]:
    return _load("glossary")["terms"]


def groups() -> list[str]:
    return _load("glossary")["groups"]


def term(slug: str) -> dict:
    for t in glossary():
        if t["slug"] == slug:
            return t
    raise KeyError(f"no glossary term '{slug}'")


def responses() -> dict:
    return _load("responses")


def composition_notes() -> dict:
    return _load("composition_notes")


def trades_se() -> list[dict]:
    return _load("trades_se")["groups"]


def quantile_phrase(q: float, upper: bool) -> str:
    """0.5 as "the median", 0.75 as "the top quarter", and so on."""
    named = {0.5: "the median", 0.75: "the top quarter", 0.8: "the top fifth",
             0.67: "the top third", 0.9: "the top tenth"}  # fmt: skip
    q = round(float(q), 2)
    if q in named and (upper or q == 0.5):
        return named[q]
    return f"the top {1 - q:.0%}" if upper else f"the {q:.0%} point"


def _pct(v: float, digits: int = 0) -> str:
    return f"{v * 100:.{digits}f}%".replace(".0%", "%")


def _reference_values() -> dict:
    from engine import sensitivity

    ref = sensitivity.load_reference()
    if ref is None:
        return {}
    out = {}
    for scope, key in (("all industries", "all"), ("construction (F)", "f")):
        for cut, name in ((0.02, "low"), (0.05, "high")):
            row = ref[(ref["scope"] == scope) & (ref["cutoff"].round(4) == cut)]
            if not row.empty:
                out[f"ref_{key}_{name}"] = _pct(row["share_weighted"].iloc[0])
    out["ref_years"] = f"{ref['first_year'].min()} to {ref['last_year'].max()}"
    return out


def values(params: dict | RunParams | None = None) -> dict:
    """Placeholder values from a run's parameters, or the defaults."""
    if params is None:
        params = RunParams()
    p = params.as_dict() if isinstance(params, RunParams) else params
    t = p["thresholds"]
    return {
        "shock_pct": f"{p['shock_pct']:g}%",
        "pressure_low": _pct(t["pressure_low"], 1),
        "pressure_high": _pct(t["pressure_high"], 1),
        "slack_median": quantile_phrase(t["slack_median_quantile"], upper=False),
        "slack_top": quantile_phrase(t["slack_top_quantile"], upper=True),
        **_reference_values(),
    }


def fill(s: str | None, vals: dict) -> str:
    """Replace known placeholders; leave unknown ones visible, never fail."""
    if not s:
        return ""
    return PLACEHOLDER.sub(lambda m: str(vals.get(m.group(1), m.group(0))), s)


def filled(slug: str, vals: dict) -> dict:
    t = dict(term(slug))
    for k in ("definition", "why", "caveat", "reasoning"):
        t[k] = fill(t.get(k), vals)
    return t


def glossary_markdown() -> str:
    vals = values()
    out = [
        "# Glossary",
        "",
        "Generated from `engine/text/glossary.yaml` by `python -m engine glossary`; "
        "edit that file, not this one. The same text drives the tooltips and the "
        "glossary page in the web app. Values shown are the defaults; in the web "
        "app they follow the run being viewed.",
        "",
        f"**{RISK_LABEL}**",
        "",
    ]
    for g in groups():
        out += [f"## {g}", ""]
        for t in glossary():
            if t["group"] != g:
                continue
            t = filled(t["slug"], vals)
            out.append(f"### {t['term']}")
            out.append("")
            out.append(t["definition"])
            out.append("")
            out.append(f"*Why it matters.* {t['why']}")
            if t.get("caveat"):
                out += ["", f"*Limit.* {t['caveat']}"]
            if t.get("reasoning"):
                out += ["", f"*Reasoning.* {t['reasoning']}"]
            src = t["source"]
            out += ["", f"*Source.* [{src['name']}]({src['url']}): {src['detail']}."]
            if t.get("also_used_by"):
                refs = "; ".join(
                    f"[{a['name']}]({a['url']})" if a.get("url") else a["name"]
                    for a in t["also_used_by"]
                )
                out += ["", f"*Also used by.* {refs}."]
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def write_glossary() -> str:
    GLOSSARY_MD.write_text(glossary_markdown(), encoding="utf-8", newline="\n")
    return str(GLOSSARY_MD)
