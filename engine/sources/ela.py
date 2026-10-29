"""European Labour Authority, EURES report on labour shortages and surpluses 2025.

Phase 1 saves and checks the PDF. The report's annexes carry methodology and
trend tables, not the full occupation-by-country shortage list, so the
occupation list for step 8 is sourced in Phase 5 (see the gate-1 report).
"""

from __future__ import annotations

from pypdf import PdfReader

from engine.sources._common import SourceError, download, record

URL = (
    "https://www.ela.europa.eu/sites/default/files/2026-06/"
    "labour-shortages-report-ela-2025.pdf"
)
PUBLISHER = "European Labour Authority"
LICENCE = (
    "(c) European Labour Authority 2026; no reuse licence stated in the report; "
    "cite as the report directs"
)
EXPECTED_TITLE = "EURES-Report on labour shortages and surpluses 2025"


def load(force: bool = False):
    raw = download(
        "ela_shortages_2025",
        URL,
        "ela-eures-shortages",
        "2025-report",
        "pdf",
        force=force,
    )
    reader = PdfReader(raw.path)
    title = (reader.metadata or {}).get("/Title", "")
    if title != EXPECTED_TITLE:
        raise SourceError(f"ELA report: unexpected title {title!r}")
    checks = {"pages": len(reader.pages), "title": title}
    record(raw, PUBLISHER, LICENCE, "PDF only; occupation list not machine-readable")
    return raw, None, checks
