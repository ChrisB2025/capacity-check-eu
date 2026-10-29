# Gate 3 report: EU-wide results

Date: 30 October 2026.

> **Provisional and unreviewed.** Every result here uses compositions with status "proposed": the reviewer has not yet commented and Chris has not confirmed one. Chris authorised Phases 3, 4 and 5 to proceed overnight on 29 October, ahead of the Gate 2 go, with results marked provisional. Every figure is regenerated once a composition is confirmed.

All figures come from `docs/results/`, written by `python -m engine results --provisional`. `docs/results/summary.json` lists the base run's parameters and the checksum of every data file read; every run in the matrix is saved with its manifest in `data/processed/runs/<run_id>/`. The base run is `dbe55db9208e`, the same as Gate 2.

## Summary

| Phase 3 item | Status |
| :--- | :--- |
| Full run matrix | **72 runs**: shocks of 0.5%, 1% and 2%; four compositions; three threshold sets; two slack indicators; FIGARO 2026 edition. The 72 runs on the 2025 edition are skipped: it is still awaited from Eurostat. |
| Results tables as CSV | `countries.csv`, `lines.csv` (with home, rest-of-EU and non-EU split and the six-group column), `dependencies.csv`, `robustness.csv`, `matrix.csv`, `plausibility.csv`, `sweden_*.csv` |
| Six-group aggregation | Added as a column, with a **proposed** mapping (below). |
| Plausibility, France and Ireland | Computed. **The third stopping-rule test is not applied**: neither official source could be read and checked (below). |
| Stopping rule, second test (editions) | Still cannot be applied. |
| Reviewer package | `docs/review/review-package-provisional.zip` |

## The run matrix

The design is full factorial: every combination of shock size (0.5, 1, 2% of GDP), composition (standard, contractor-led, materials bought directly, heating replacement), thresholds and slack indicator. The thresholds are the defaults (2% and 5%), a lower set (1% and 3%) and a higher set (3% and 8%); the brief asks for "default and alternative thresholds" and does not name the alternatives, so these two are my choice, logged in `docs/decisions.md`.

A check on the engine falls out of the matrix: the 2% shock and the lower thresholds (half the defaults) give identical headlines for every member state, as they must in a linear model.

## Robustness: ratings changed against the base run

`robustness.csv`. Of 1,728 member state and industry lines, 1,132 are rated in the base run. Lines unrated in either run are counted separately.

| Test | Variant | Ratings changed | Share |
| :--- | :--- | ---: | ---: |
| Shock size | 0.5% | 32 | 2.8% |
| Shock size | 2% | 51 | 4.5% |
| Thresholds | lower (1%, 3%) | 40 | 3.5% |
| Thresholds | higher (3%, 8%) | 25 | 2.2% |
| Composition | contractor-led | 10 | 0.9% |
| Composition | materials bought directly | 50 | 4.4% |
| Composition | heating replacement | 64 | 5.7% |
| **Slack indicator** | **job vacancy rate** | **425 of 1,125** | **37.8%** |
| Edition | 2025 | not run | |

**The ratings are robust to the shock size, the thresholds and the composition, and not robust to the slack indicator.** Swapping the DG ECFIN survey share for the Eurostat job vacancy rate changes more than a third of ratings: 242 lines go from tight to clear and 165 from clear to tight. The vacancy rate is published only by NACE section, so every industry in a section gets the same reading; it also rates lines the surveys do not cover, which drops the unrated share of jobs from a median of 14% to under 1%. The two indicators measure different things (firms reporting labour as limiting, against open posts as a share of all posts), and they disagree about which industries are under strain. This is the main robustness finding for the reviewer. The headline is less affected than the ratings, ranging 67% to 98% with the vacancy rate against 59% to 86%, because construction is tight or binding under both.

## Dependencies

`dependencies.csv` lists, for each member state's programme, the required output in seven manufacturing industries, with no rating. Summed over all 27 programmes:

| Industry | Required output (EUR m) | At home | Rest of EU | Outside EU |
| :--- | ---: | ---: | ---: | ---: |
| C28 Machinery, including heat pumps | 23,828 | 42% | 40% | 19% |
| C25 Fabricated metal products | 11,113 | 58% | 27% | 15% |
| C24 Basic metals | 9,203 | 28% | 35% | 37% |
| C23 Non-metallic mineral products | 9,057 | 74% | 15% | 12% |
| C22 Rubber and plastics | 5,528 | 50% | 31% | 19% |
| C27 Electrical equipment | 4,840 | 34% | 36% | 30% |
| C16 Wood products | 3,230 | 62% | 24% | 14% |

Basic metals and electrical equipment are the most dependent on production outside the EU.

## Six-group aggregation (proposed)

Each of the 64 industries carries a `six_group` column. No published mapping was found in the project documents, so this one is proposed for the reviewer and Stephen Hinton:

| Group | Industries |
| :--- | :--- |
| extraction | A01 to A03, B |
| production | all of C, and F |
| energy | D35 |
| recycling | E37-39 |
| distribution | E36 (water supply), G45 to G47, H49 to H53 |
| use | all other services, public administration, households |

The group plays no part in any rating.

## Plausibility: France and Ireland

`plausibility.csv`, from the base run's persons per million euros. The model is linear, so these scale to any programme size.

**Neither official source could be checked.** Both documents refuse scripted downloads from this machine (the France Stratégie note redirects to a missing page; the Fiscal Council paper returns HTTP 403). The job figures are the brief's; the French programme size, 20 to 30 billion euros of additional investment a year, comes from search extracts of the note and is unverified. Each reference is marked `verified: false` in `engine/plausibility_refs.yaml`, and the stopping rule's third test is not applied until Chris saves both documents and checks the figures.

**France.** For a programme of 20 to 30 billion euros a year, the model gives:

| Model measure | Persons |
| :--- | ---: |
| Construction jobs in France | 79,900 to 119,800 |
| All jobs in France, including supply chains | 176,400 to 264,600 |
| All jobs in the EU | 211,200 to 316,800 |

The official estimate is 170,000 to 250,000. Against construction jobs alone the model is about half the official figure, just outside a factor of two; against all jobs in France it is within 6%. **Which measure the official estimate corresponds to decides the test**, and that has to be read from the note itself: whether its 170,000 to 250,000 counts only building trades or includes design, manufacturing and other supply-chain jobs. The reference file currently compares construction jobs, the stricter choice; Chris or the reviewer should confirm it.

**Ireland.** The Fiscal Council paper's spending figure is not held, so the check cannot be run. The model needs about 28 billion euros of Irish programme to add 80,000 construction workers in Ireland (2.85 construction persons per million euros), which can be compared with the paper's investment requirement once it is read.

## Sweden (Phase 5)

`sweden_*.csv` for the base run, and the Sweden page in the web app. The 48,600 extra persons on Swedish lines split into 430 occupations. The largest are carpenters (2,800, 5.2% of the occupation's employees), electricians (2,100, 5.0%), cleaners (1,200), plumbers (1,200, 4.8%) and warehouse staff (1,100). Arbetsförmedlingen rates electricians and plumbers as shortage occupations with growing demand over five years; carpenters are in balance. Cleaners and warehouse staff appear because Statistics Sweden's 16 groups give architecture and engineering the occupation mix of all business services, a limit stated on the page. The ELA 2025 report has no occupation list for Sweden, so it is not compared. Konjunkturinstitutet's construction series agrees with the DG ECFIN series almost exactly where they overlap, but it is not published here until its licence is confirmed (gate 1 decision 4). Sweden is a demonstration, not a validation.

## Stopping rule

| Test | Status |
| :--- | :--- |
| Labour constraint series missing for more than a third of member states | Did not fire (gate 1) |
| More than a quarter of ratings change between two FIGARO editions | Cannot be applied: 2025 edition awaited |
| French and Irish checks differ from official estimates by more than a factor of two | Not applied: sources unverified. France is within a factor of two on one measure and just outside on the other. |
| No reviewer outside the MMT community agrees to comment | Package sent; reply awaited |

A related warning, not a stopping-rule test: the slack indicator changes 38% of ratings, more than the quarter the rule uses for editions.

## Gate 3

Gate 3 is "reviewer comments received or a date set for them". For Chris:

1. **Save the two plausibility documents** by hand and check the figures in `engine/plausibility_refs.yaml`, in particular what the French estimate counts.
2. **Decide whether the vacancy-rate finding goes to the reviewer** as a question: which availability indicator, or whether results should show both.
3. **Confirm or amend the threshold alternatives and the six-group mapping.**
4. Once a composition is confirmed, `python -m engine results` (without `--provisional`) regenerates every table here.
