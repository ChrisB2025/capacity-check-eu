# Decisions

A dated log of judgement calls. Newest entries at the bottom. Each entry says what was decided, who decided it, and why.

## 2026-10-29: Phase 0 opening decisions

**Inputs read.** `docs/spec-v1.md` (specification, 9 October 2026), `docs/cdm-v1.6.2-baseline.md` (Real Capital CDM frozen baseline, 27 October 2026) and `docs/ciaran-briefing.md` (Ciaran McKenna's note on merging the two proposals). No `spec-v2.md` exists, so spec-v1 and the build brief govern. Where they differ on dates, the build brief wins: the data check targets 3 November, not 30 October.

**Name.** Undecided; Chris decides. Working options are "Capacity Check Europe" and "Real Resource Check". The slug `capacity-check-eu` is used for the repository and Railway project until then.

**Licence.** Decided by Chris. Code under MIT; documents, results tables, method note and report under CC BY 4.0. CC BY matches Eurostat's attribution condition and lets reviewers and the CDM project reuse tables. The copyright line reads "the Capacity Check Europe contributors" until Chris names a holder.

**Development database.** Decided by Chris. Local PostgreSQL 17 for development from Phase 4. The Railway database is used only by the deployed service. The engine needs no database.

**FIGARO parser.** Decided by Chris, on this evidence. This departs from spec-v1, which named pymrio or MARIO.

- pymrio 0.7.0 (released 19 October 2026) has no FIGARO parser. Its changelog and API reference do not mention FIGARO.
- MARIO (`mariopy`) has `parse_figaro`, but it reads only from the Eurostat SDMX API. The API holds only the current edition, so it cannot load the previous edition the robustness test needs. It also defaults to product-by-product tables.
- Decision: a pandas parser of our own for the FIGARO CSV flat files from CIRCABC, one code path for both editions. The SDMX dataflows `naio_10_fcp_ii1` to `naio_10_fcp_ii4` are loaded separately for the 2026 edition to cross-check the CSV parse. The Leontief inverse is computed with numpy or scipy and cached per edition.

### Source verification before Phase 1

Checked against each publisher's own metadata or API on 2026-10-29. Downloads into the repository start in Phase 1; nothing below is a model input yet.

**FIGARO.**
- Current edition: 2026, covering 2010 to 2024, 64 industries, 49 economies plus rest of world. Industry-by-industry dataflows `naio_10_fcp_ii1` (2010 to 2013), `ii2` (2014 to 2017), `ii3` (2018 to 2021), `ii4` (2022 onward), updated 18 to 20 July 2026.
- Flat files sit in the CIRCABC FIGARO space, library `460a20fc-5956-44f9-8633-2821eb48dd62`. CIRCABC cannot be listed from a script, so Phase 1 downloads may need a browser step.
- Previous edition: the Eurostat database page archived on 6 March 2026 described the 2025 edition (2010 to 2023) and linked CIRCABC folder `0d8bab1e-d159-40b9-9aff-ef8e6d58e24e`. Whether it is still live is a Gate 1 check. Fallback: Eurostat user support.

**Employment and GDP.** `nama_10_a64_e` (data updated 27 October 2026) and `nama_10_gdp` (updated 22 October 2026) both exist on the Eurostat SDMX API.

**DG ECFIN labour series.** Verified by downloading release `nace2_ecfin_2610`. The answer codes differ by survey, and the obvious guess is wrong for construction:

| Survey | Question | Labour answer | Frequency | Detail |
| :--- | :--- | :--- | :--- | :--- |
| Construction | Q2 main factors limiting building activity | F4 shortage of labour force (F3 is weather) | Monthly | Total, NACE 41, 42, 43 |
| Industry | Q8 factors limiting production | F3 labour | Quarterly | Total, NACE 10 to 33 |
| Services | Q7 factors limiting the business | F3 labour | Quarterly | Total, NACE 49 to 96 |

Coverage in that release: the construction and industry labour series exist for all 27 member states, so the first stopping-rule test does not fire on present evidence. Known gaps: Estonia and Malta surveys suspended from May 2026; Germany lacks NACE 43; Luxembourg services and Spanish services after 2024Q3 are thin or missing. Gate 1 repeats this on the registered download. Files checked (sha256):

```
8926fa1625aa88b15063a66fa5d0d76fc63bab9c3f54cc4b09bb1c7a7299fa87  building_subsectors_nsa_nace2.zip
504388f0ed6b14d4cb798fa73558f12e6134ac43af1a17afce4ece14b8ab9940  building_total_nsa_nace2.zip
f8e3a7e51fa0a6328501ca41f618efa5fb1a2497506db403c4372651fbcd9697  industry_subsectors_nsa_nace2.zip
762825027c6b7f9772c6037c5a954d8b2cc4010beda8c0578cb3dc2fc613bf91  industry_total_nsa_nace2.zip
a98f31d46f5d050b0c395f115ef3f5fabc06802f898ac1f3f06bfd640a27e361  services_subsectors_nsa_nace2.zip
7be85462afe9ebcdfca74611844f892563fb7047c39a412d48dd92c136986eee  services_total_nsa_nace2.zip
```

**Job vacancies.** `jvs_q_nace2` covers 2001Q1 to 2025Q4 at NACE section level only, so its mapping to A64 is many-to-one. France and Italy omit some public units; Denmark covers NACE B to N only.

**ELA report.** The briefed PDF URL resolves. The publication landing page returns 404; the news release is at `ela.europa.eu/en/news/ela-launches-2025-eures-report-highlighting-structural-labour-shortages-across-europe`.

**Sweden.**
- SCB tables YREG54BAS and YREG52BAS load through the PxWeb API at `api.scb.se/OV0104/v1/doris/sv/ssd/START/AM/AM0208/AM0208E/`. YREG54BAS has 16 industry groups and an "unknown" group, so the join to A64 is at section level.
- The `jobtechdev.se` site does not resolve from this machine. The data host `data.jobtechdev.se/prognoser/` serves `yrkesbarometer.json` under CC0 1.0.
- Konjunkturinstitutet: the quarterly table named in the spec (`Bartotq.px`) does not hold the limiting-factor question. The monthly construction table `KonjBar/ftgmanad/Barboam.px` does: question 1084, labour, by SNI 41, 42 and 43, from 1996M02.

**Plausibility references.** The Irish Fiscal Council PDF refuses scripted downloads (HTTP 403) and must be saved by hand. The XPair and BMAS FB 683 pages resolve.

### CDM baseline gaps found on first reading

These become Baseline Change Requests in `docs/cdm-mapping.md` in Phase 2, alongside the three named in the brief (`required_quantity`, `assessment_category`, `availability_basis`).

1. `Region.region_type` has no NUTS0 value, but the mapping needs one row per member state at NUTS0.
2. Section 1.2 of the baseline requires a `linked_performance_record_id` whenever `LifecycleActivity.target_entity_type` is Performance. This project produces no `AssetPerformanceRecord`.
3. `UnitOfMeasure` has PERSONS but no unit for hours worked.

Also noted: the baseline field is `activity_description`, not `description`.

**Not committed.** `docs/ciaran-briefing.md` is kept out of the public repository until Chris says otherwise. It is an internal note with links to private documents and is not part of the layout in the brief.

## 2026-10-29: Phase 1 data acquisition

**Go for Phase 1.** Chris said go after the Gate 0 report. Layout and licence stand as proposed.

**FIGARO loader roles, proposed swap, awaiting Chris.** The Eurostat API serves the whole 2026 edition and the downloaded tables balance exactly, while CIRCABC cannot be scripted. Proposal: the API is the primary loader for the current edition; the CIRCABC CSV parser handles earlier editions and is proven on the 2026 CSV against the API copy. See `docs/gate-1-report.md`, decision 1.

**Labour answer codes come from the code book.** The construction survey's labour answer is F4 (F3 there is weather), while industry and services use F3. `engine/sources/ecfin.py` finds the code by its label in each workbook's Index sheet and fails if it cannot, so a renumbering by DG ECFIN cannot silently swap the series.

**Raw data are whole releases.** Eurostat datasets are saved whole (or, for GDP, the one series used) as compressed SDMX-CSV, and FIGARO as one zip of unedited API responses per reference year. Processed parquet files record their raw files and checksums in their own metadata.

**Konjunkturinstitutet table.** The table named in spec-v1 (`Bartotq.px`) lacks the limiting-factor question; the monthly construction table `Barboam.px` is used instead. Its labour question starts in January 2022.

**One concordance file.** `engine/concordances/a64.csv` links each FIGARO industry to its national accounts code, NACE divisions, DG ECFIN survey and Statistics Sweden group. It is generated by `python -m engine concordance` from rules in `engine/concordance.py` and committed so changes show in review.

**New dependencies.** `python-calamine` reads the DG ECFIN Excel workbooks quickly; `pypdf` checks the ELA report.

## 2026-10-29: FIGARO 2025 edition not available

Chris checked the CIRCABC FIGARO library in a browser: it holds only the 2026 edition. He downloaded the 2026 industry-by-industry flat file for 2024 and the description workbook, both imported and registered. The CIRCABC parser reproduces the API copy exactly (11,060,700 flows, largest difference zero). The 2025 edition is not on the API, CIRCABC, DBnomics or any public deposit found; it has to be requested from Eurostat (ESTAT-IGA@ec.europa.eu). Every edition is now saved with a checksum on download, so this does not recur.

## 2026-10-29: Phase 2 engine, judgement calls

Chris said go for Phase 2 while the Eurostat request is outstanding. The edition comparison is built and waits for the 2025 file. No results are run until the composition table has been to the reviewer and Chris has confirmed it; the engine enforces this, refusing any composition whose status is not "confirmed".

Choices made in the engine, each a parameter in `engine/params.py` and listed in `docs/method-note.md` for the reviewer:

- **Application: simultaneous by default.** The scenario is every member state applying the shock, so cross-border demand adds up. "own" is a variant.
- **Origin split from gross fixed capital formation.** Public renovation is investment; the member state's existing investment purchases of each product decide home, rest-of-EU and non-EU shares, with stated fallbacks.
- **Multi-division industries take the simple mean of their survey divisions.** DG ECFIN's weights file weights countries, not divisions; employment weights would need another dataset.
- **Current slack is the latest four-quarter mean, placed in the history of the same rolling mean.** Monthly series use complete quarters only.
- **Missing industry employment uses the NACE section ratio, flagged.**
- **Provisional, pending Chris (gate 1 decisions 5 to 7):** industries with no survey question get no rating; persons employed is the jobs measure with hours shown; minimum slack history is five years.

Additions to the brief's layout: `engine/params.py` (run parameters), `engine/pipeline.py` (runs the steps in order and saves a run), `engine/compositions/` (composition files with a status). The Leontief inverse is cached as a NumPy file with a JSON record of its source checksum, rather than as parquet, because it is a dense matrix.

The baseline mapping found six gaps beyond the three in the brief; all nine are change requests in `docs/cdm-mapping.md`.

## 2026-10-29: Composition table proposed

Four compositions drafted from sources opened and checked on 29 October 2026, all with status "proposed": `standard` (KfW fee share plus Quirion's input-output allocation of deep renovation), `alt_contractor` (KfW as it stands), `alt_materials` (GEM-E3 split used for DG ENER) and `alt_heating` (Danish Energy Agency heat pump split). The guiding principle, to be challenged by the reviewer: list a product separately only when it is bought separately from the installer, or when construction's average supply chain lacks it, so that materials are not counted twice. Chris decides the final values after review (`docs/composition-table.md`).

## 2026-10-29: Provisional Gate 2 results published

Chris decided to publish the provisional Gate 2 report, its tables in `docs/gate-2/` and the fixed test set's fixtures, although the composition is not yet confirmed. The report is marked provisional and unreviewed, and `summary.json` and each fixture manifest record the composition's status. All three are regenerated once a composition is confirmed.
