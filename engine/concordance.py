"""Concordance for the 64 FIGARO industries (NACE Rev. 2, A64 level).

One row per FIGARO industry code, linking it to:

* the code used in Eurostat national accounts employment (``nama_10_a64_e``),
* the NACE sections and 2-digit divisions it contains,
* the DG ECFIN survey that asks about factors limiting activity for those
  divisions (if any), and
* the Statistics Sweden industry group used in table YREG54BAS.

The links follow mechanically from the NACE code structure; the rules are
in this module, and the generated table is committed as
``engine/concordances/a64.csv`` so that a change is visible in review.
Labels are Eurostat's own, from the IND_AVA code list.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from engine.sources._common import http_session

CODELIST_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/codelist/ESTAT/IND_AVA"
)
CSV_PATH = Path(__file__).resolve().parent / "concordances" / "a64.csv"

FIGARO_A64 = (
    "A01 A02 A03 B C10-12 C13-15 C16 C17 C18 C19 C20 C21 C22 C23 C24 C25 C26 C27 "
    "C28 C29 C30 C31_32 C33 D35 E36 E37-39 F G45 G46 G47 H49 H50 H51 H52 H53 I J58 "
    "J59_60 J61 J62_63 K64 K65 K66 L M69_70 M71 M72 M73 M74_75 N77 N78 N79 N80-82 "
    "O84 P85 Q86 Q87_88 R90-92 R93 S94 S95 S96 T U"
).split()

# Sections that are a single A64 industry, and the divisions they contain.
SECTION_DIVISIONS = {
    "B": range(5, 10),
    "F": range(41, 44),
    "I": range(55, 57),
    "L": [68],
    "T": range(97, 99),
    "U": [99],
}

# Divisions with a DG ECFIN "factors limiting activity" question. Industry
# covers manufacturing (10 to 33), construction covers 41 to 43, services the
# divisions listed. The retail survey (47) has no limiting-factor question.
ECFIN_INDUSTRY = set(range(10, 34))
ECFIN_BUILDING = {41, 42, 43}
ECFIN_SERVICES = {
    49,
    50,
    51,
    52,
    53,
    55,
    56,
    58,
    59,
    60,
    61,
    62,
    63,
    64,
    65,
    66,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    77,
    78,
    79,
    80,
    81,
    82,
    90,
    91,
    92,
    93,
    94,
    95,
    96,
}

# Statistics Sweden YREG54BAS groups, keyed by NACE section.
SCB_GROUP = {
    "A": "A",
    "B": "B+C",
    "C": "B+C",
    "D": "D+E",
    "E": "D+E",
    "F": "F",
    "G": "G",
    "H": "H",
    "I": "I",
    "J": "J",
    "K": "K",
    "L": "L",
    "M": "M+N",
    "N": "M+N",
    "O": "O",
    "P": "P",
    "Q": "Q",
    "R": "R+S+T+U",
    "S": "R+S+T+U",
    "T": "R+S+T+U",
    "U": "R+S+T+U",
}


def divisions(code: str) -> list[int]:
    """NACE 2-digit divisions contained in a FIGARO industry code."""
    section, rest = code[0], code[1:]
    if not rest:
        return list(SECTION_DIVISIONS[section])
    m = re.fullmatch(r"(\d{2})(?:([-_])(\d{2}))?", rest)
    if not m:
        raise ValueError(f"unrecognised industry code {code}")
    first = int(m.group(1))
    if not m.group(2):
        return [first]
    last = int(m.group(3))
    return list(range(first, last + 1)) if m.group(2) == "-" else [first, last]


def nama_code(code: str) -> str:
    """The same industry as coded in nama_10_a64_e, e.g. C10-12 to C10-C12."""
    return re.sub(r"^([A-Z])(\d{2})([-_])(\d{2})$", r"\1\2\3\1\4", code)


def ecfin_survey(divs: list[int]) -> tuple[str, list[int]]:
    for name, covered in (
        ("industry", ECFIN_INDUSTRY),
        ("building", ECFIN_BUILDING),
        ("services", ECFIN_SERVICES),
    ):
        hit = [d for d in divs if d in covered]
        if hit:
            return name, hit
    return "", []


def eurostat_labels() -> dict[str, str]:
    resp = http_session().get(CODELIST_URL, timeout=120)
    resp.raise_for_status()
    labels = {}
    pattern = re.compile(
        r'<s:Code id="([^"]+)"[^>]*>.*?<c:Name xml:lang="en">([^<]+)</c:Name>', re.S
    )
    for code, name in pattern.findall(resp.text):
        labels[code] = name.strip()
    return labels


def build() -> pd.DataFrame:
    labels = eurostat_labels()
    rows = []
    for code in FIGARO_A64:
        divs = divisions(code)
        survey, covered = ecfin_survey(divs)
        rows.append(
            {
                "figaro_code": code,
                "label": labels.get(code, ""),
                "nace_section": code[0],
                "section_label": labels.get(code[0], ""),
                "nace_divisions": " ".join(f"{d:02d}" for d in divs),
                "nama_code": nama_code(code),
                "ecfin_survey": survey,
                "ecfin_divisions": " ".join(f"{d:02d}" for d in covered),
                "scb_group": SCB_GROUP[code[0]],
            }
        )
    df = pd.DataFrame(rows)
    missing = df.loc[
        (df["label"] == "") | (df["section_label"] == ""), "figaro_code"
    ].tolist()
    if missing:
        raise ValueError(f"no Eurostat label for {missing}")
    return df


def write() -> Path:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    build().to_csv(CSV_PATH, index=False, lineterminator="\n")
    return CSV_PATH


def load() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
