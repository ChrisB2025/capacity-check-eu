# Gate 1 report: data acquisition

Date: 2026-10-29. Status: **two of the three checks pass; the second is waiting on a manual download.** The first stopping-rule test does not fire.

Every figure below comes from the tables in `docs/gate-1/`, produced by `python -m engine gate1`. `docs/gate-1/SOURCES.md` lists the raw files and checksums behind each table, and `docs/data-register.md` records every download.

## Summary

| Check | Answer |
| :--- | :--- |
| 1. Do the DG ECFIN sector files hold the labour constraint question for most member states? | **Yes.** All 27 have the construction series. Manufacturing and services coverage by division is good for most countries, with gaps listed below. |
| 2. Can an earlier FIGARO edition be obtained? | **Not yet confirmed.** The 2026 edition is held and validated for 2023 and 2024. The 2025 edition exists only on CIRCABC, which cannot be downloaded by script. You need to download it by hand (instructions below). |
| 3. Do the Swedish occupation tables load and join to the 64 industries? | **Yes, with limits.** Both tables load completely. The join to the 64 industries is at the level of 16 industry groups, so occupation mixes within manufacturing and within business services are shared across their industries. |
| Stopping rule, first test | **Does not fire.** No member state lacks the construction labour series. |

## Check 1: DG ECFIN labour constraint series

Release `nace2_ecfin_2610`, downloaded 29 October 2026, all 16 workbooks plus the country weights file. The labour answer was identified from each workbook's code book, not assumed:

| Survey | Question | Labour answer | Frequency |
| :--- | :--- | :--- | :--- |
| Construction | Q2 main factors currently limiting your building activity | F4 shortage of labour force | Monthly |
| Industry | Q8 factors limiting the production | F3 labour | Quarterly |
| Services | Q7 factors limiting the business | F3 labour | Quarterly |
| Retail trade | none | none | |

**Construction, the core of the shock.** All 27 member states have the series for construction as a whole (`ecfin_country_summary.csv`). The earliest start is January 1985 (Austria, Finland, Italy). The latest is May 2016 (Ireland). Germany has divisions 41 and 42 but not 43, which is specialised construction such as installation and finishing. Estonia and Malta stop in April 2026, because their surveys were suspended in May 2026.

**Coverage of the 64 industries.** Of the 64 FIGARO industries, 48 contain at least one division the surveys ask about (`engine/concordances/a64.csv`). The other 16 have no survey question at all. They are agriculture (A01 to A03), mining (B), energy (D35), water and waste (E36, E37-39), all three trade industries (G45 to G47), public administration (O84), education (P85), health and social care (Q86, Q87_88), households (T) and extraterritorial bodies (U). Across countries and the 48 surveyed industries, the status depends on how much history a series must have (`ecfin_a64_coverage_5y.csv`, `ecfin_a64_coverage_10y.csv`):

| History required | Full | Partial | Missing |
| :--- | ---: | ---: | ---: |
| At least 5 years | 1,089 | 43 | 164 |
| At least 10 years | 992 | 49 | 255 |

"Full" means every division of the industry has a series. "Partial" means some do. Each count is a country and industry pair, out of 1,296.

**Industries the shock buys from directly** are construction (F), wood (C16), plastics (C22), non-metallic minerals (C23), metal products (C25), electrical equipment (C27), machinery including heat pumps (C28), and architecture and engineering (M71).

- With five years of history required, 26 countries have all eight. Luxembourg lacks M71.
- With ten years required, Ireland has none of the eight, because its series start in 2016. Hungary and Luxembourg lack M71.

**Weak spots in services.** Luxembourg's services series has a single observation, 2026Q4. Spain's services series ends in 2024Q3. Finland and Estonia report few services divisions.

**Publisher caveats.** DG ECFIN states that the subsector series are back-cast by the partner institutes and "have not undergone a full validation process". The workbooks' INFO sheets record revisions, such as the French and Romanian services data in July 2026, and the Estonian and Maltese suspensions. The series are shares of firms, not quantities.

## Check 2: FIGARO editions

**Held now:** the 2026 edition for reference years 2023 and 2024 (`figaro_editions.csv`). It came from the Eurostat SDMX API, dataflows `naio_10_fcp_ii4` (2022 onward), one request per origin economy. Each year is one raw zip of the unedited API responses. Both years pass validation:

- 50 economies (49 plus rest of world) and 64 industries, 11,060,700 flows, no missing values, no negative intermediate flows, no flagged observations.
- For every economy and industry, total output by row equals total inputs plus value added by column. The largest relative gap is of the order of 10^-15, which is rounding.

**The 2025 edition** (reference years 2010 to 2023) is not on the API, which only serves the current edition. Eurostat's database page, as archived on 6 March 2026, linked the 2025 files to a CIRCABC folder (`0d8bab1e-d159-40b9-9aff-ef8e6d58e24e`). CIRCABC is a JavaScript application that rejects scripted requests, so I could not confirm the folder is still there. **What you need to do:**

1. Open the FIGARO library on CIRCABC in a browser: https://circabc.europa.eu/ui/group/cec66924-a924-4f91-a0ef-600a0531e3ba/library/460a20fc-5956-44f9-8633-2821eb48dd62
2. Look for the 2025 edition. Download the **industry-by-industry input-output table, CSV flat format**, for reference year **2023**. If 2024 sits next to it in the 2026 edition folder, download that file too.
3. Run, for each file:
   ```bash
   python -m engine import-figaro <downloaded file> --edition 2025 --year 2023
   python -m engine import-figaro <downloaded file> --edition 2026 --year 2024
   ```
   This copies the file unedited into `data/raw/`, checksums it and registers it. I then write the parser for the CSV layout and check it against the API copy of the 2026 edition, which must agree to rounding.

If the 2025 edition is no longer on CIRCABC, the fallback is to ask Eurostat user support for it. Without a previous edition the robustness test and the second stopping-rule test cannot run.

**A finding about recent years.** Eurostat's FIGARO information page says national supply and use tables generally arrive about 36 months after the reference year, so the most recent FIGARO years are projected by Eurostat. The metadata marks most non-EU economies' 2024 tables as estimated by Eurostat. It states accuracy as "not available", and says "there is no point at which data are final". This affects which reference year to use (decision 3 below).

## Check 3: Swedish occupation tables

Both tables load through the Statistics Sweden API with nothing suppressed (`data-register.md`):

- **YREG54BAS**: 430 occupation codes (SSYK 2012, four digits) by 16 industry groups, 2020 to 2024. In 2024, 0.4% of employees have an unknown occupation and 0.7% an unknown industry.
- **YREG52BAS**: the same occupations by field of education, 2020 to 2024. It has only **ten broad fields of education**, such as "engineering, manufacturing and construction" as one field.

**The 16-group to 64-industry concordance** is the `scb_group` column of `engine/concordances/a64.csv`, and the join test is `sweden_scb_group_join_2024.csv`. It compares Statistics Sweden employees in each group with national accounts employees for the industries mapped to it, in 2024:

| Group | Industries mapped | Register employees to national accounts employees |
| :--- | ---: | ---: |
| F construction | 1 | 0.985 |
| B+C mining and manufacturing | 20 | 1.021 |
| M+N business services | 9 | 1.329 |
| H transport | 5 | 1.539 |
| O public administration | 1 | 1.316 |
| All other groups | 1 to 7 each | between 0.86 and 0.99 |

**Limits.**

- **Construction is a group of its own,** so the occupational split for the industry the shock hits hardest needs no assumption.
- **Manufacturing is one group covering 20 industries.** The occupation mix of, say, machinery (including heat pumps) is assumed to be the average for all manufacturing. Business services similarly covers 9 industries, including M71 architecture and engineering.
- **The transport and business services ratios are high partly because national accounts lack 2024 values for Sweden** in 2 of the 5 transport industries and 2 of the 9 business services industries. Sweden has persons employed for 58 of the 64 industries. The public administration ratio has no explanation yet; it likely reflects how public units are classified in the register.
- **The register counts employees only.** Self-employed tradespeople, a large group in construction, are not in YREG54BAS.
- **YREG52BAS is too coarse** to show qualified people working outside their trade at any useful detail. See decision 6.

**Other Swedish sources.**
- *Arbetsförmedlingen*: the Yrkesbarometer round 2026-1 covers 219 occupations nationally, licensed CC0. Construction trades are covered, including carpenters, bricklayers, concrete workers, insulation fitters, plumbers, heat-pump technicians, sheet-metal workers, painters and electricians, plus civil engineers and building technicians.
- *Konjunkturinstitutet*: the quarterly table named in the specification (`Bartotq.px`) does not hold the limiting-factor question. The monthly construction table `Barboam.px` does (question 1084, labour), but only from January 2022. It is useful as a cross-check of recent DG ECFIN figures for Sweden, not as a history. Konjunkturinstitutet is DG ECFIN's Swedish partner institute.

## Other data

**Employment by industry, 2024** (`employment_coverage_2024.csv`, data updated 27 October 2026). Persons employed are available for nearly all 64 industries in most countries. The exceptions are Luxembourg (35), Malta (56) and Sweden (58). **Hours worked are available only at a coarser level in six countries**: Belgium (21 industries), Bulgaria (20), Germany (21), Estonia (7), France (22) and Lithuania (19). Construction has both persons and hours in all 27. The 2024 values are flagged provisional for Germany, Greece, Spain, France, Luxembourg and the Netherlands.

**GDP 2024** (data updated 22 October 2026): all 27 member states, 6 values flagged provisional.

**Job vacancy rates** (`vacancy_coverage.csv`, data updated 20 March 2026, to 2025Q4). These are at NACE section level only, so one rate covers several of the 64 industries. Construction (F) is available for all 27, from 2016 for Italy and from 2017 for Malta. Denmark covers business sectors only (B to N).

**ELA shortages report.** The PDF is saved and checked: 140 pages, published June 2026. Its annexes hold methodology and trend tables, **not the full list of 436 occupations by country**. That list will have to come from EURES's own data in Phase 5.

## Licences

| Source | Terms |
| :--- | :--- |
| Eurostat (FIGARO, national accounts, vacancies) | Reuse with acknowledgement of the source, Commission Decision 2011/833/EU |
| DG ECFIN business surveys | Commission reuse policy, CC BY 4.0; subsector series not fully validated |
| Statistics Sweden | CC0 1.0; citation requested |
| Arbetsförmedlingen Yrkesbarometer | CC0 1.0 |
| Konjunkturinstitutet | **No licence found.** See decision 4. |
| European Labour Authority report | Copyright ELA 2026; no reuse licence stated; cite as the report directs |

## Concordances

- **FIGARO and national accounts codes.** These map mechanically, for example `C10-12` to `C10-C12`. All 64 codes exist in the employment data.
- **DG ECFIN divisions and the 64 industries.** This is lossy in three ways:
  - Industries made of several divisions need a rule to combine them, for example food, beverages and tobacco (C10-12). That rule is for Phase 2.
  - Construction can use either the sector total or divisions 41 to 43.
  - Sixteen industries have no question, listed above.
- **Products and industries in FIGARO.** The tables are industry by industry, with final demand recorded against the supplying industry. A purchase of a product (CPA 2.1, two digits) is therefore assigned to the industry with the same code. For example, construction work (CPA F) is assigned to construction (F) and machinery (CPA 28) to C28. Eurostat's metadata refers to the FIGARO handbook for how the tables are derived, and I have not yet confirmed the assumption it uses. The practical effect is that goods made as secondary products of another industry are attributed to the main producer. This matters most for heating equipment, which is split between machinery (C28) and electrical equipment (C27). The composition table must state which code each purchase uses.
- **Statistics Sweden groups and the 64 industries.** See check 3.

## Departure from a decision already taken

On 29 October you chose our own parser for the CIRCABC CSV files, with the API as a cross-check. Now that the API proved complete and exactly balanced, and CIRCABC proved impossible to script, I propose to swap the roles:

- The API becomes the primary source for the 2026 edition, because it is fully reproducible from the command line.
- The CIRCABC CSV parser is used for the 2025 edition.
- That parser is proven on the 2026 CSV against the API copy, so both editions effectively pass through the same tested path.

This needs your approval (decision 1).

## Decisions for you

1. **Swap the FIGARO loader roles as described above.** Recommended.
2. **Download the FIGARO files from CIRCABC** (check 2). This blocks closing check 2.
3. **Which reference year the edition comparison uses.** Comparing 2023 in the 2025 and 2026 editions isolates Eurostat's revisions. Comparing each edition's latest year (2023 against 2024) mixes revision with a year of change. I recommend 2023 against 2023 for the stopping-rule test, with the latest-year comparison reported alongside. The same point raises whether the main run should use 2024, which is the shock year but mostly projected, or 2023. This is a method question for the reviewer; my recommendation is 2024, with 2023 as a sensitivity.
4. **Konjunkturinstitutet licence.** I recommend using it only as an internal cross-check and not republishing its values unless it confirms reuse terms. Alternatively, write to them.
5. **The 16 industries with no survey question.** I recommend "no rating" for them, as the method says when slack is missing, rather than borrowing another sector's series. Trade (G45 to G47) is the one most likely to matter for this shock, through distribution of materials.
6. **YREG52BAS.** It has only ten fields of education, so I recommend dropping the "qualified people working elsewhere" part of step 8, or presenting it at that broad level with the limit stated.
7. **Hours worked.** Six countries lack hours at industry detail. I recommend persons employed as the main jobs measure in every country, with hours shown where published.

Earlier open items still stand: the Railway region, the `railway.toml` retirement on 1 December, and reading the BMAS FB 683 report before any claim of novelty.
