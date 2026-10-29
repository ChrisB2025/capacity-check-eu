"""Step 10. Plausibility checks for France and Ireland.

The model is linear, so a run's jobs per million euros of programme scale to
any programme size. For each country this gives the model's jobs for the
official programme size and compares them with the official job estimate.

Three model measures are shown, because the official estimates count
different things: construction jobs in the country itself, all jobs in the
country, and all jobs in the EU. ``compare_with`` in the reference file says
which one is compared.

The stopping rule's third test fires when the model and the official estimate
differ by more than a factor of two. It is applied only to references marked
verified in ``plausibility_refs.yaml``.
"""

from __future__ import annotations

from pathlib import Path

import yaml

FACTOR = 2.0
REFS = Path(__file__).with_name("plausibility_refs.yaml")


def references() -> dict:
    return yaml.safe_load(REFS.read_text(encoding="utf-8"))


def rates(res, country: str) -> dict:
    """Persons per million euros of the country's own programme."""
    lines = res.tables["lines"]
    c = res.tables["countries"].set_index("country").loc[country]
    own = lines[lines["economy"] == country]
    shock = c["shock_meur"]
    return {
        "home_construction": own.loc[own["industry"] == "F", "extra_persons_own"].sum()
        / shock,
        "home_all": own["extra_persons_own"].sum() / shock,
        "eu_all": c["extra_persons_eu"] / shock,
    }


def check(res, country: str, ref: dict) -> dict:
    r = rates(res, country)
    basis = ref["compare_with"]
    out = {
        "country": country,
        "run_id": res.run_id,
        "measure": ref["measure"],
        "official_low": ref["estimate_low"],
        "official_high": ref["estimate_high"],
        "programme_meur_low": ref["programme_meur_low"],
        "programme_meur_high": ref["programme_meur_high"],
        "compare_with": basis,
        **{f"persons_per_meur_{k}": v for k, v in r.items()},
        "verified": bool(ref["verified"]),
        "source": " ".join(ref["source"].split()),
    }
    lo, hi = ref["programme_meur_low"], ref["programme_meur_high"]
    if lo is not None and hi is not None:
        # Every measure is shown; only ``compare_with`` decides the check.
        for k, v in r.items():
            out[f"model_low_{k}"] = v * lo
            out[f"model_high_{k}"] = v * hi
        out["model_low"] = r[basis] * lo
        out["model_high"] = r[basis] * hi
        # Ratio of model to official at the matching ends of both ranges.
        ratios = [out["model_low"] / ref["estimate_low"],
                  out["model_high"] / ref["estimate_high"]]  # fmt: skip
        out["ratio_low"], out["ratio_high"] = ratios
        within = all(1 / FACTOR <= x <= FACTOR for x in ratios)
        out["within_factor_two"] = within
        out["status"] = (
            ("passes" if within else "fires") if ref["verified"] else "unverified"
        )
    else:
        out["implied_programme_meur"] = ref["estimate_low"] / r[basis]
        out["status"] = "not applied: official programme size not held"
    return out


def run(res) -> list[dict]:
    return [check(res, code, ref) for code, ref in _keyed().items()]


def _keyed() -> dict:
    names = {"france": "FR", "ireland": "IE"}
    return {names[k]: v for k, v in references().items()}
