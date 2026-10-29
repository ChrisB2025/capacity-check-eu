"""Run parameters. Every judgement call that affects a number is a parameter here,
with its default, so that a run is fully described by its parameters plus the
checksums of the data it read.

Defaults marked PROVISIONAL follow recommendations in the gate 1 report that
Chris has not yet confirmed; see docs/decisions.md.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

from engine.sources._common import EU27


@dataclass(frozen=True)
class Thresholds:
    """The proposed rating rule (spec-v1). Parameters, not constants."""

    pressure_low: float = 0.02  # extra jobs as a share of employment: tight from here
    pressure_high: float = 0.05  # binding above this, if slack is also high
    slack_median_quantile: float = 0.5  # above this: elevated
    slack_top_quantile: float = 0.75  # at or above this: high


@dataclass(frozen=True)
class RunParams:
    shock_pct: float = 1.0  # additional spending, % of GDP
    gdp_year: int = 2024
    edition: str = "2026"  # FIGARO edition
    ref_year: int = 2024  # FIGARO reference year and employment year
    composition: str = "standard"
    # "simultaneous": every member state applies the shock at once, so pressure
    # on an industry adds up demand from all 27 programmes. "own": each
    # country's industries see only spillovers from its own programme.
    application: str = "simultaneous"
    # Final demand category whose origin pattern splits each product between
    # home, rest of EU and outside EU. Public renovation is investment.
    import_basis: str = "P51G"
    slack_indicator: str = "ecfin"  # or "vacancy"
    slack_seasonally_adjusted: bool = False
    slack_window_quarters: int = 4  # current slack: mean of the latest year
    slack_min_years: float = 5.0  # PROVISIONAL: less history gives no rating
    jobs_measure: str = "persons"  # PROVISIONAL: hours shown where published
    thresholds: Thresholds = field(default_factory=Thresholds)
    countries: tuple[str, ...] = EU27

    def __post_init__(self):
        if not 0.5 <= self.shock_pct <= 2.0:
            raise ValueError("shock_pct must be between 0.5 and 2")
        if self.application not in ("simultaneous", "own"):
            raise ValueError("application must be 'simultaneous' or 'own'")
        if self.slack_indicator not in ("ecfin", "vacancy"):
            raise ValueError("slack_indicator must be 'ecfin' or 'vacancy'")
        if self.jobs_measure not in ("persons", "hours"):
            raise ValueError("jobs_measure must be 'persons' or 'hours'")

    def as_dict(self) -> dict:
        d = asdict(self)
        d["countries"] = list(self.countries)
        return d

    def digest(self) -> str:
        blob = json.dumps(self.as_dict(), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()
