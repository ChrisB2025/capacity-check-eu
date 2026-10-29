"""Steps 4, 6 and 7. Pressure, rating and headline; data quality flags.

Pressure is extra persons employed as a share of the industry's current
employment in that member state.

The rating combines pressure with the slack class from ``engine.slack``,
following the proposed rule in spec-v1 with thresholds as parameters:

* binding: pressure above ``pressure_high`` and slack in the top quartile
* tight: pressure at or above ``pressure_low``, or slack above the median
* clear: otherwise, that is pressure below ``pressure_low`` and slack at or
  below the median
* no rating: no slack class (series missing or too short), or no jobs
  estimate. A rating is never forced.

The headline for a member state's shock is the share of the jobs it creates
in the EU that fall on lines rated tight or binding.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.params import Thresholds
from engine.slack import ELEVATED, HIGH, LOW

CLEAR, TIGHT, BINDING, NO_RATING = "clear", "tight", "binding", "no rating"

# Data quality grade for a country row, from the share of that country's
# shock jobs that sit on lines with a given weakness.
GRADE_GOOD_MAX = 0.10
GRADE_LIMITED_MAX = 1 / 3


def rate(pressure: float, slack_class: str | None, t: Thresholds) -> str:
    if (
        slack_class not in (LOW, ELEVATED, HIGH)
        or pressure is None
        or np.isnan(pressure)
    ):
        return NO_RATING
    if pressure > t.pressure_high and slack_class == HIGH:
        return BINDING
    if pressure >= t.pressure_low or slack_class in (ELEVATED, HIGH):
        return TIGHT
    return CLEAR


def rate_lines(lines: pd.DataFrame, t: Thresholds) -> pd.Series:
    return pd.Series(
        [
            rate(p, s, t)
            for p, s in zip(lines["pressure"], lines["slack_class"], strict=True)
        ],
        index=lines.index,
    )


def quality(shares: dict[str, float], notes: list[str]) -> tuple[str, str]:
    """Grade from shares of the shock's jobs on weak lines, plus fixed notes."""
    worst = max(shares.values()) if shares else 0.0
    if worst <= GRADE_GOOD_MAX and not notes:
        grade = "good"
    elif worst <= GRADE_LIMITED_MAX:
        grade = "limited"
    else:
        grade = "poor"
    parts = [f"{k} {v:.0%}" for k, v in shares.items() if v > 0] + notes
    return grade, "; ".join(parts)
