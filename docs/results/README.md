# Results tables

**Ratings are estimated risk categories: risk indicators, not factual judgements about whether a programme can be delivered.**

These tables are written by `python -m engine results` for the base run (1% of 2024 GDP, standard composition, FIGARO 2026 edition, reference year 2024), except `matrix.csv` and `robustness.csv`, which cover every run in the matrix. All results are **provisional** while the composition is unconfirmed; `summary.json` says which.

Before comparing member states, read the named limits in `docs/method-note.md`: the same financial shock is applied to 27 countries with different climates, building stock, tenure, incomes and habits, so the tables compare relative pressure under an identical shock, not what each country would need to spend or do. Extra persons are not new hires. Every term is defined in `docs/glossary.md`.

| File | Contents |
| :--- | :--- |
| `summary.csv` | The figures behind the executive summary |
| `overview.csv` | EU totals and the worked example on the web app's front page |
| `allocation.csv` | Each composition line, its amount, origin split and the NACE divisions it maps to |
| `countries.csv` | Per member state: headline, requirement total, data quality |
| `lines.csv` | Per member state and industry: requirement, pressure, shortage level, estimated risk category |
| `dependencies.csv` | Required output in the manufacturing industries the programme leans on, with no rating |
| `sensitivity.csv` | Estimated risk categories under other pressure thresholds and shortage cut-offs |
| `threshold_reference.csv` | How often industries' employment has grown by each pressure threshold in one year, 2011 to 2024 |
| `robustness.csv` | Ratings changed against the base run, by test |
| `matrix.csv` | Every run in the matrix with its parameters and results |
| `plausibility.csv` | France and Ireland against official job estimates |
| `sweden_*.csv` | The Sweden layer |
| `summary.json` | Run ids, sources and checksums |
