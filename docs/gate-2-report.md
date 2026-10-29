# Gate 2 report: model engine

Date: 29 October 2026.

> **Provisional and unreviewed.** These results use the *proposed* standard composition, which the reviewer has not yet seen and Chris has not confirmed. Chris asked for the run ahead of review to check the engine end to end. Every figure here will change if the composition does, and the whole report is regenerated once a composition is confirmed.

Every figure comes from the tables in `docs/gate-2/`, produced by `python -m engine gate2 --provisional`. `docs/gate-2/summary.json` gives each run's id, parameters, composition status and the checksum of every data file read. The base run is `dbe55db9208e`. Persons are rounded to the nearest hundred.

## Summary

| Gate 2 item | Status |
| :--- | :--- |
| Engine runs end to end on the 2026 FIGARO edition for all 27 member states | **Yes.** A full run takes about ten seconds. |
| Requirement and availability reported separately | **Yes**, in separate tables and sections below. |
| First robustness run against the previous edition | **Not run.** The 2025 edition is not held; it has been requested from Eurostat. |
| Second stopping-rule test | **Cannot be applied** until the previous edition is held. |
| Composition table, method note, data-model mapping | Drafted; with the reviewer next. |
| Fixed test set | Built: 8 cases, all reproduce exactly. Its fixtures are provisional and will be regenerated once a composition is confirmed. |

## The run

Standard shock: 1% of 2024 GDP in each member state, proposed standard composition, FIGARO 2026 edition with reference year 2024, all 27 programmes at once. Slack comes from the DG ECFIN labour series, not seasonally adjusted, with a minimum history of five years. The thresholds are the proposed defaults: 2% and 5% pressure, and the median and upper quartile of each series' history. The parameters are listed in `docs/method-note.md`.

Across the EU, the shock totals €181,312 million and adds 2,133,800 persons employed in EU member states in one year.

## Requirement: what the shock needs

`requirement_by_country.csv`

- **Output multiplier.** Every euro of direct purchases requires between 2.07 and 2.72 euros of output across the supply chain, counting all economies.
- **Where the output sits.** Between 44% (Ireland) and 83% (Italy) of required output is in the member state itself. Ireland is the outlier: 35% of its required output is outside the EU.
- **Jobs per million euros of shock.** These range from 6.3 (Ireland) to 23.2 (Bulgaria), following wage and productivity levels.
- **Which industries carry the jobs.** Across all 27 programmes, construction carries 40% of the extra persons, architecture and engineering (M71) 15%, and wholesale trade 6%. Machinery, which includes heat pumps, carries 3%.
- **Pressure.** The shock adds between 3.4% (Romania) and 9.4% (Greece, Ireland) to construction employment. It adds between 5.4% and 28.6% to architecture and engineering, and between 2.0% and 4.0% to machinery.

**The pressure on architecture and engineering comes from the 20% design and supervision share in the proposed composition**, applied to a small industry. It is the result most sensitive to the composition, and it is reviewer question 2 in `docs/composition-table.md`.

## Availability: what firms report

`availability_by_country.csv`

The share of construction firms naming labour as a limiting factor, measured as the mean of the latest four complete quarters, sits in its own history as follows:

- **Top quarter of its history (high)**: 13 member states
- **Above its median (elevated)**: 10
- **At or below its median (low)**: Estonia, France, Ireland and Lithuania

Across all 64 industries, lines with a survey series are mostly above their median: 515 high, 292 elevated and 325 low. A further 596 country and industry lines have no usable series. These are mainly the 16 industries the surveys do not cover, plus gaps by country.

## Rating

`ratings_by_country.csv`

| Rating | Construction | Architecture and engineering | Machinery |
| :--- | ---: | ---: | ---: |
| Binding | 12 | 11 | 0 |
| Tight | 15 | 15 | 26 |
| Clear | 0 | 0 | 1 (Finland) |
| No rating | 0 | 1 (Luxembourg) | 0 |

Across all 1,728 member state and industry lines: 25 binding, 812 tight, 295 clear, 596 no rating.

The table below gives each member state's construction line in full, and the headline: the share of the jobs its programme creates in the EU that fall on tight or binding lines.

| Country | Shock (EUR m) | Extra persons in the EU | Home share of required output | Construction pressure | Construction slack | Construction rating | Headline | Unrated | Data quality |
| :--- | ---: | ---: | ---: | ---: | :--- | :--- | ---: | ---: | :--- |
| AT | 4,999 | 49,600 | 71% | 5.7% | elevated (67%) | tight | 78% | 13% | limited |
| BE | 6,194 | 52,600 | 72% | 6.0% | high (86%) | binding | 72% | 14% | limited |
| BG | 1,053 | 24,500 | 63% | 4.6% | high (89%) | tight | 79% | 19% | limited |
| CY | 363 | 5,700 | 66% | 5.3% | high (100%) | binding | 84% | 14% | limited |
| CZ | 3,212 | 52,200 | 71% | 5.3% | high (87%) | binding | 83% | 14% | limited |
| DE | 43,869 | 455,800 | 80% | 6.7% | high (96%) | binding | 79% | 15% | limited |
| DK | 4,003 | 34,800 | 66% | 5.3% | elevated (65%) | tight | 76% | 17% | limited |
| EE | 399 | 6,400 | 61% | 5.0% | low (25%) | tight | 74% | 19% | limited |
| EL | 2,377 | 50,500 | 67% | 9.4% | high (98%) | binding | 82% | 14% | limited |
| ES | 15,986 | 225,100 | 77% | 6.1% | high (99%) | binding | 83% | 15% | limited |
| FI | 2,762 | 28,500 | 68% | 5.2% | elevated (55%) | tight | 68% | 17% | limited |
| FR | 29,352 | 310,000 | 72% | 5.8% | low (36%) | tight | 75% | 14% | limited |
| HR | 873 | 14,300 | 64% | 4.8% | elevated (69%) | tight | 82% | 15% | limited |
| HU | 2,062 | 45,400 | 60% | 5.6% | elevated (68%) | tight | 82% | 14% | limited |
| IE | 5,619 | 35,700 | 44% | 9.4% | low (16%) | tight | 84% | 11% | limited |
| IT | 22,106 | 271,800 | 83% | 5.6% | high (96%) | binding | 82% | 13% | limited |
| LT | 798 | 14,300 | 61% | 4.9% | low (48%) | tight | 82% | 13% | limited |
| LU | 873 | 7,800 | 55% | 6.2% | high (85%) | binding | 59% | 37% | poor |
| LV | 411 | 8,000 | 69% | 5.9% | elevated (67%) | tight | 80% | 15% | limited |
| MT | 231 | 3,400 | 62% | 7.9% | high (81%) | binding | 84% | 13% | limited |
| NL | 11,153 | 98,400 | 70% | 6.2% | high (94%) | binding | 81% | 13% | limited |
| PL | 8,522 | 143,700 | 70% | 5.2% | elevated (62%) | tight | 86% | 12% | limited |
| PT | 2,912 | 52,300 | 69% | 6.5% | elevated (74%) | tight | 82% | 12% | limited |
| RO | 3,553 | 58,700 | 64% | 3.4% | elevated (51%) | tight | 73% | 17% | limited |
| SE | 5,636 | 51,800 | 71% | 5.5% | elevated (58%) | tight | 76% | 14% | limited |
| SI | 675 | 10,000 | 67% | 5.9% | high (88%) | binding | 84% | 13% | limited |
| SK | 1,320 | 22,400 | 68% | 5.7% | high (87%) | binding | 85% | 13% | limited |

## What drives the headline, and a finding for the reviewer

The headline ranges from 59% (Luxembourg) to 86% (Poland), with a median of 82%. **It separates member states very little.** Three things explain this:

1. **Construction is tight or binding everywhere.** It holds 40% of the jobs, and pressure on it exceeds the 2% threshold in every member state. Half of all jobs on tight or binding lines are in construction.
2. **The rule rates a line tight when shortage reports are above their median, whatever the pressure.** Of the jobs on tight or binding lines, 24% are on lines where the shock adds less than 2% to employment. Shortage reports in 2025 and 2026 are above their long-run median in most industries and countries, so much of the headline reflects the current state of labour markets rather than the shock.
3. **Architecture and engineering is tight or binding in 26 member states**, driven by the proposed fee share.

The rating rule is reviewer question 6 in the method note. These results suggest asking specifically whether elevated slack alone, with negligible pressure, should make a line tight.

## Data quality

Every member state is graded "limited" except Luxembourg, which is graded "poor". The main reason is that wholesale and retail trade have no survey question, so their lines are unrated, and trade carries a share of the jobs through the composition's distribution margin and through supply chains.

- 14% of all the shock's EU jobs are on unrated lines, 9 percentage points of them in trade.
- Ireland's construction series has eight years of complete quarters, below the ten years that trigger a note.
- Luxembourg's architecture and engineering line has no services series, and 37% of its jobs are unrated.

## Checks on the engine

- **The Leontief inverse** takes about one second to compute and reproduces total output from final demand with a largest relative error of the order of 10^-15. It has no negative entries.
- **Five industry cells** in the FIGARO table use more intermediate inputs than their output, meaning negative value added. The largest in output terms is Luxembourg's rubber and plastics (C22). The inverse stays non-negative, so no correction was applied. The point is noted for the reviewer.
- **Very small industries** can show large pressure from a handful of jobs. For example, Slovenian refined petroleum employs 10 persons, and three extra persons make 32%. It is unrated and does not affect any headline. A minimum industry size for rating is a possible addition, for the reviewer to decide.
- **Integration tests** confirm the accounting on the real data. Direct demand adds up to the shock in every member state. The home, rest-of-EU and non-EU shares sum to one. Industry detail adds up to each country's total.
- **The run is deterministic.** The same inputs give the same run id and identical outputs, which the fixed test set checks for 8 cases.

## Robustness against the previous edition

**Not run.** The 2025 FIGARO edition has been withdrawn from every public source; it was requested from Eurostat (`docs/gate-1-report.md`). The comparison code is written and tested (`engine/robustness.py`): when the file arrives, `python -m engine import-figaro` registers it and `python -m engine gate2` runs the test and applies the stopping rule.

**A substitute check, which is not the edition test**, compares the same edition with reference year 2023 instead of 2024 (run `88b333547bc7`). Of 1,132 lines rated in both runs, 3 change rating (0.3%), and no headline moves by more than 1.5 percentage points. Both runs use the same survey readings, so only the requirement side varies. This shows the ratings are not fragile to a year's change in the table's structure. It says nothing about Eurostat's revisions between editions, which is what the stopping rule tests.

## Stopping rule

| Test | Status |
| :--- | :--- |
| Labour constraint series missing for more than a third of member states | Did not fire (gate 1) |
| More than a quarter of ratings change between two FIGARO editions | Cannot be applied yet |
| French and Irish checks differ from official estimates by more than a factor of two | Phase 3 |
| No reviewer outside the MMT community agrees to comment | Open |

## Gate 2

The brief's gate is that the outside reviewer and Ciaran McKenna see the composition table and method note, and Chris says go once their comments are incorporated or logged. Before that:

1. **Send the review package.** Send `docs/composition-table.md` and `docs/method-note.md` to the reviewer and to Ciaran. This report can go with them as an illustration of what the engine produces, clearly marked provisional, if you judge that useful.
2. **Confirm a composition** once comments are in. I then regenerate this report and the test set with the confirmed composition.
3. **The edition test** runs when Eurostat supplies the 2025 edition. If it cannot, a substitute must be agreed with the reviewer.
