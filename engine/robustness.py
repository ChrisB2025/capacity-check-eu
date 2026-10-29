"""Step 9. How many ratings change between two runs.

Used for every robustness test: another FIGARO edition, another composition,
other thresholds, the vacancy-based slack indicator. A line counts as
changed when its rating differs. Lines unrated in either run are reported
separately and excluded from the share, so a test cannot pass by producing
more "no rating" lines.

The second stopping-rule test fires when more than a quarter of ratings
change between two FIGARO editions.
"""

from __future__ import annotations

import pandas as pd

from engine.rating import NO_RATING

STOPPING_RULE_SHARE = 0.25


def compare_ratings(base: pd.DataFrame, alt: pd.DataFrame) -> dict:
    keys = ["economy", "industry"]
    m = base[[*keys, "rating"]].merge(
        alt[[*keys, "rating"]], on=keys, suffixes=("_base", "_alt")
    )
    rated = m[(m["rating_base"] != NO_RATING) & (m["rating_alt"] != NO_RATING)]
    changed = rated[rated["rating_base"] != rated["rating_alt"]]
    transitions = (
        changed.groupby(["rating_base", "rating_alt"])
        .size()
        .rename("lines")
        .reset_index()
        .to_dict(orient="records")
    )
    return {
        "lines_compared": len(m),
        "lines_rated_in_both": len(rated),
        "lines_unrated_in_either": len(m) - len(rated),
        "ratings_changed": len(changed),
        "share_changed": len(changed) / len(rated) if len(rated) else float("nan"),
        "transitions": transitions,
    }


def edition_test(base: pd.DataFrame, alt: pd.DataFrame) -> dict:
    out = compare_ratings(base, alt)
    out["stopping_rule_threshold"] = STOPPING_RULE_SHARE
    out["stopping_rule_fires"] = bool(out["share_changed"] > STOPPING_RULE_SHARE)
    return out
