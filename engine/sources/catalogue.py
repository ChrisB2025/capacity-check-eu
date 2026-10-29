"""Catalogue of the datasets the engine will fetch, as verified on 2026-10-29.

This is metadata only: identifiers, URLs and the reason each source is used.
No figures live here. Download, parse and validate functions per source are
added in Phase 1, and each actual download is recorded in
``docs/data-register.md`` and ``data/checksums.txt``.
"""

from __future__ import annotations

from dataclasses import dataclass

EUROSTAT_SDMX = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1"
ECFIN_SERIES = (
    "https://ec.europa.eu/economy_finance/db_indicators/surveys/documents/series"
)
SCB_PXWEB = "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/AM/AM0208/AM0208E"
KONJ_PXWEB = "https://statistik.konj.se/PxWeb/api/v1/sv/KonjBar"
CIRCABC_FIGARO = (
    "https://circabc.europa.eu/ui/group/cec66924-a924-4f91-a0ef-600a0531e3ba/library"
)


@dataclass(frozen=True)
class PlannedSource:
    key: str
    publisher: str
    dataset: str
    location: str
    used_for: str
    layer: str = "EU"


PLANNED_SOURCES: tuple[PlannedSource, ...] = (
    PlannedSource(
        "figaro_2026",
        "Eurostat",
        "FIGARO inter-country IO, industry by industry, 2026 edition (2010-2024)",
        f"{CIRCABC_FIGARO}/460a20fc-5956-44f9-8633-2821eb48dd62 (CSV flat, manual)",
        "Cross-check of the API copy",
    ),
    PlannedSource(
        "figaro_2026_sdmx",
        "Eurostat",
        "naio_10_fcp_ii1 to naio_10_fcp_ii4, API (current edition only)",
        f"{EUROSTAT_SDMX}/data/naio_10_fcp_ii4",
        "Step 2 supply chains, current edition (primary loader)",
    ),
    PlannedSource(
        "figaro_2025",
        "Eurostat",
        "FIGARO inter-country IO, industry by industry, 2025 edition (2010-2023)",
        f"{CIRCABC_FIGARO}/0d8bab1e-d159-40b9-9aff-ef8e6d58e24e (to confirm live)",
        "Step 9 robustness across editions",
    ),
    PlannedSource(
        "nama_10_a64_e",
        "Eurostat",
        "nama_10_a64_e, EMP_DC, THS_PER and THS_HW",
        f"{EUROSTAT_SDMX}/data/nama_10_a64_e",
        "Step 3 jobs and step 4 pressure",
    ),
    PlannedSource(
        "nama_10_gdp",
        "Eurostat",
        "nama_10_gdp, B1GQ, CP_MEUR",
        f"{EUROSTAT_SDMX}/data/nama_10_gdp",
        "Step 1 shock size",
    ),
    PlannedSource(
        "ecfin_building",
        "European Commission, DG ECFIN",
        "Construction survey, Q2 answer F4 shortage of labour force",
        f"{ECFIN_SERIES}/<release>/building_subsectors_nsa_nace2.zip",
        "Step 5 slack, NACE 41 to 43",
    ),
    PlannedSource(
        "ecfin_industry",
        "European Commission, DG ECFIN",
        "Industry survey, Q8 answer F3 labour",
        f"{ECFIN_SERIES}/<release>/industry_subsectors_nsa_nace2.zip",
        "Step 5 slack, NACE 10 to 33",
    ),
    PlannedSource(
        "ecfin_services",
        "European Commission, DG ECFIN",
        "Services survey, Q7 answer F3 labour",
        f"{ECFIN_SERIES}/<release>/services_subsectors_nsa_nace2.zip",
        "Step 5 slack, NACE 49 to 96",
    ),
    PlannedSource(
        "jvs_q_nace2",
        "Eurostat",
        "jvs_q_nace2, job vacancy rate by NACE section",
        f"{EUROSTAT_SDMX}/data/jvs_q_nace2",
        "Step 9 alternative slack indicator",
    ),
    PlannedSource(
        "ela_shortages_2025",
        "European Labour Authority",
        "EURES report on labour shortages and surpluses 2025",
        "https://www.ela.europa.eu/sites/default/files/2026-06/"
        "labour-shortages-report-ela-2025.pdf",
        "Step 8 comparison",
    ),
    PlannedSource(
        "scb_yreg54bas",
        "Statistics Sweden",
        "YREG54BAS, employees by SSYK 2012 occupation and 16 industry groups",
        f"{SCB_PXWEB}/YREG54BAS",
        "Step 8 occupational split",
        "Sweden",
    ),
    PlannedSource(
        "scb_yreg52bas",
        "Statistics Sweden",
        "YREG52BAS, employees by SSYK 2012 occupation and field of education",
        f"{SCB_PXWEB}/YREG52BAS",
        "Step 8 qualified people outside the occupation",
        "Sweden",
    ),
    PlannedSource(
        "af_yrkesbarometer",
        "Arbetsformedlingen",
        "Yrkesbarometer occupational outlook (CC0 1.0)",
        "https://data.jobtechdev.se/prognoser/yrkesbarometer.json",
        "Step 8 comparison",
        "Sweden",
    ),
    PlannedSource(
        "konj_construction",
        "Konjunkturinstitutet",
        "Barboam.px, question 1084 limiting factor labour, SNI 41 to 43, monthly",
        f"{KONJ_PXWEB}/ftgmanad/Barboam.px",
        "Cross-check of the ECFIN construction series for Sweden",
        "Sweden",
    ),
)
