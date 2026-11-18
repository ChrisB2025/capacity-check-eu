# Method note

Capacity Check Europe (working name), Season 1 demonstrator. Draft for review, 29 October 2026. Updated through Phase 7, and on 18 November 2026 after the first reviewer feedback: named limits, the mapping from spending to industries, the reasoning for each threshold, the jobs caveat and the risk-indicator framing. Every term used here is defined in the [glossary](glossary.md).

## The question

When the same public spending shock is applied in every EU member state, which industries does it press on, and are those industries already short of labour?

The standard shock is additional public spending equal to 1% of each member state's 2024 GDP, in one year, on housing and energy renovation. The composition of the products bought directly is the same in every country. Test runs use 0.5% and 2%.

**This is an identical financial shock, not an identical physical programme.** One per cent of GDP buys different amounts of renovation in different countries, because prices, wages and the building stock differ. The result says where the money would press, not how many homes would be renovated.

## What the result claims and does not claim

- It locates pressure. It does not size price changes, because input-output analysis assumes fixed proportions and no price response.
- It has no deficit or debt term.
- It makes no claim about fiscal space. Eurozone members are rules-bound issuers of the euro: their central banks belong to the Eurosystem, but the Treaty, including Article 123 TFEU's ban on central bank financing of governments, limits how they spend. The model takes those rules as given.
- It cannot see constraints in permits, grid connections, planning or training capacity.
- It scores against labour available in the country. Migration and posted workers are a named limitation, not part of the model.
- At 64 industries, results are bands, not point estimates.
- Requirement (what the shock needs) and availability (what firms report about labour) are shown separately before they are combined into a rating.

Of the five programme questions (what a policy requires, what exists, what can be mobilised, over what time, within what limits), this method answers the first, gives a partial answer to the second, and does not answer the last three. Survey shares of firms reporting shortages are evidence about the second question, not a measure of how much labour could be mobilised.

## Risk indicators, not judgements

Every rating is an **estimated risk category**: clear, tight or binding. Each is a risk indicator, built from two published signals (how large the shock is for an industry's workforce, and how often its firms already report labour shortages). None is a factual judgement that a programme can or cannot be delivered. The web app states this on every results page and on the second line of every CSV it exports; `docs/results/README.md` states it for the published tables.

## Where the tool sits in the policy process

The tool is an early screen of real resource risk, used before a programme is designed. It shows which industries to look at more closely, and where training, phasing or a different spending mix might be needed. It is not a forecast of what will happen, and it does not replace a country's own assessment of a real programme. Readers range from researchers to people facing an urgent policy choice, so the web app presents results in layers: a short summary, a plain-language explanation, then the method and data.

## Named limits

These limits bound what any result can claim. They are stated on the results pages, not only here.

1. **One shock, 27 different countries.** Every member state gets the same shock: the same share of GDP with the same spending mix. Countries differ in climate, building stock, tenure (Finland's well-insulated cooperative flats are not Sweden's detached houses), incomes and habits; household water and energy use differ between neighbouring countries for reasons that are cultural, not physical. The renovation work a uniform shock implies may therefore be badly out of line with what any one country would actually do. A proper baseline would need energy use by building type, income group and season, which Season 1 does not attempt.
   - *Valid comparisons*: where the same financial shock presses hardest relative to each industry's workforce and its own shortage history; which industries are tight or binding in many member states and which in few; how much of each programme's work is done outside the spending country.
   - *Invalid comparisons*: what each country would need to spend or how many homes it would need to renovate; whether one country's programme is more feasible than another's; the size of any country's real renovation need.
   - The uniform shock is deliberate. It makes cross-country variation visible and gives each country a common starting point. The method is built to be rerun with each country's own composition and data.
2. **Construction is one industry.** See step 1: FIGARO cannot split construction into the trades renovation needs.
3. **Jobs are not hires.** See step 3.
4. **Survey shares count firms, not missing workers** (step 5).
5. The limits listed under "What the result claims and does not claim" above.

## From shock to rating

The engine is a Python package in `engine/`. Every step below names its module, and every parameter is in `engine/params.py` with the default shown here.

### 1. Direct demand (`engine/shock.py`)

For member state *c*, the shock is *s* per cent of 2024 GDP at current prices (`nama_10_gdp`, B1GQ, million euros). It is split across products by the composition table (`docs/composition-table.md`).

FIGARO's tables are industry by industry, so a purchase of a product is assigned to the industry with the same two-digit code. For example, construction work (CPA F) is assigned to construction (F).

**How the shock is allocated.** The standard composition maps to four industries:

| Spending line | Share | FIGARO industry | NACE divisions | Why this line, and why this industry |
| :--- | ---: | :--- | :--- | :--- |
| Construction work, including insulation and heating installation | 64.0% | F Construction | 41, 42, 43 | Insulation and installation are bought from contractors at their installed price. Materials come in through construction's own supply chain, so they are not listed again. |
| Heating and ventilation equipment | 9.4% | C28 Machinery and equipment n.e.c. | 28 | Heat pumps, boilers and ventilation units. Listed separately because construction's average supply chain contains little machinery. |
| Distribution margin on heating equipment | 6.6% | G46 Wholesale trade | 46 | The wholesale margin on the equipment, kept as its own purchase. |
| Design, planning and site supervision | 20.0% | M71 Architectural and engineering activities | 71 | The KfW programme assumption for planning and supervision. |

The shares and sources are derived in `docs/composition-table.md`; the alternatives tested are there too. The web app shows the same table for every run ("How the shock is allocated"), with the euro amounts and the share made at home. The reasons are kept in `engine/text/composition_notes.yaml`, so the files the engine runs, and their checksums, do not change.

**Construction cannot be split at A64.** FIGARO has one construction industry, F, covering NACE divisions 41 (buildings), 42 (civil engineering) and 43 (specialised trades such as installation and finishing). The input-output layer therefore cannot separate insulation from heating installation, or renovation trades from road building: the construction line carries the average supply chain and workforce of all construction. The business surveys do publish divisions 41 to 43, but the tool uses the construction total because the demand side has no split to match. This is a limit of the data, not a choice. Where an occupational register exists, as in Sweden, the construction workforce can be broken down into trades (step 8): carpenters, electricians, plumbers and heating fitters, insulation workers, heat pump technicians and others. The web app shows these trades from the full Swedish occupation table, including those outside the 25 largest occupations.

Each product's purchases are then split by origin economy. The split uses the shares in which *c* already buys that product for gross fixed capital formation (P51G) in the FIGARO table. If *c* records no such purchases, it falls back to all final demand of *c*, and then to all-domestic. The basis used is reported for every product and country.

### 2. Supply chains (`engine/io_model.py`)

The inter-country table has 50 economies (the 27 member states, 22 other economies, and the rest of the world) by 64 industries. Technical coefficients are *A = Z / x* by column, where *Z* is intermediate flows and *x* total output. The Leontief inverse *L = (I - A)^-1* is computed once per edition and reference year and cached.

Required output for direct demand *y* is *L y*: the output each industry in each economy must produce, directly and through its supply chain. For each member state's shock, required output is split into home, rest of the EU and outside the EU.

**Application.** By default all 27 member states apply the shock at once, so the pressure on an industry adds up demand from every programme. For example, German machinery serves French and Italian renovation as well as German. The alternative, "own", counts only the member state's own programme.

### 3. Jobs (`engine/jobs.py`)

Extra persons employed in industry *i* of member state *c* equal required output times persons employed per million euros of output. Persons come from `nama_10_a64_e` (EMP_DC, THS_PER) for the FIGARO reference year, and output from FIGARO for the same year. Hours worked (THS_HW) are computed the same way and shown where published.

Where national accounts give no figure for an industry, the ratio for its NACE section is used and the line is flagged. Economies outside the EU get output requirements but no jobs estimate.

**Jobs are not hires.** The extra persons measure the work the shock asks for, at today's output per person. They do not translate one for one into hiring. Firms can reprioritise existing capacity, moving staff from other work, and households or housing cooperatives can swap grant-funded work for work they had already planned (postponing a roof replacement to insulate, for example). Where that happens, the same work is done by people who were already employed, and the pressure shows up as displaced work rather than vacancies. A high estimated risk category therefore signals a risk of pressure, not certain hiring demand. The web app places this caveat beside every jobs figure.

### 4. Pressure (`engine/rating.py`)

Pressure is extra persons as a share of the industry's current persons employed in that member state.

### 5. Starting slack (`engine/slack.py`)

The primary indicator is the share of firms naming labour as a factor limiting activity, from the DG ECFIN business surveys, not seasonally adjusted:

- construction: question 2, answer F4
- industry: question 8, answer F3
- services: question 7, answer F3

These codes are read from each workbook's code book, not assumed. Monthly series are averaged to complete quarters.

- **Multi-division industries.** An industry made of several NACE divisions takes the simple mean of the divisions with data in each quarter.
- **Construction** uses the survey's total for the sector.
- **Current level.** The current level is the mean of the latest four quarters. It is placed within the history of the same four-quarter rolling mean over the whole series.
- **Classes.** The class is *low* at or below the history's median, *elevated* above the median, and *high* in the top quarter.
- **No class.** A line with no series, or with less history than the minimum, gets no slack class.

The alternative indicator is the Eurostat job vacancy rate (`jvs_q_nace2`) for the industry's NACE section, treated the same way.

### 6. Rating (`engine/rating.py`)

| Rating | Rule |
| :--- | :--- |
| Binding | Pressure above 5%, and slack in the top quarter of its history |
| Tight | Pressure of 2% or more, or slack above its median |
| Clear | Pressure below 2%, and slack at or below its median |
| No rating | No slack class, or no jobs estimate |

The 2% and 5% are defaults: the thresholds are parameters, and the web app fills in the values of the run being shown. A rating is never forced: missing or unusable evidence gives "no rating". The bands are called **estimated risk categories** throughout.

### Why these thresholds

The team set the four cut-offs. They are judgements, and the reasoning for each is below so that reviewers can challenge it.

- **Pressure of 2%: tight from here.** From 2011 to 2024, an industry's workforce in a member state grew by 2% or more in a year in about 31% of cases, weighted by employment (39% counting each country, industry and year once; 29% weighted, for construction alone). An extra 2% from one programme, on top of whatever growth the industry would have had anyway, is within what industries sometimes manage but large enough to notice.
- **Pressure of 5%: binding above this, if shortages are also high.** Growth of 5% or more in a year happened in about 9% of cases weighted by employment (19% unweighted; 9% weighted for construction). Adding that much in one year asks an industry for something it rarely does.
- **The median of each shortage series: elevated above it.** Firms in different countries answer the survey differently, so each series is compared with its own past, not with other countries. Above the median, more firms than usual already report labour as a limit.
- **The top quarter of each series: high, and needed for binding.** It is the tightest quarter of periods on record for that series. Binding needs both this and pressure above 5%, so a single signal never makes a line binding.

The reference figures are computed by `engine/sensitivity.py:employment_reference` from the national accounts series already used for jobs (`nama_10_a64_e`, persons, EMP_DC), and written to `docs/results/threshold_reference.csv`. They describe ordinary year-on-year changes, recessions included, not the capacity of an industry to grow under a programme.

**How much rests on them.** For the standard run, `engine/sensitivity.py` re-rates every line with the thresholds moved, and the web app's threshold page shows the result:

| Change | Ratings changed | EU jobs on tight or binding lines |
| :--- | ---: | ---: |
| Defaults (2% and 5%, median and top quarter) | none | 79.5% |
| Pressure 1% and 3% | 40 (3.5%) | 80.9% |
| Pressure 3% and 8% | 25 (2.2%) | 78.4% |
| Pressure 2% and 8% | 14 (1.2%) | 79.5% |
| High from the top third (0.67) | 11 (1.0%) | 79.5% |
| High from the top fifth (0.80) | 9 (0.8%) | 79.4% |
| Elevated above the 60% point, high from the top quarter | 91 (8.0%) | 76.6% |

Moving the pressure thresholds changes few ratings, because the shock adds little to most of the 64 industries: most tight lines are tight on the shortage signal alone. The jobs sit mainly where pressure is higher (the gate 2 report finds 24% of the jobs on tight or binding lines on lines under 2%). The elevated cut-off for shortage reports matters more, and is reviewer question 6.

### 7. Headline

For each member state's shock, the headline is the share of the jobs it creates in the EU that fall on lines rated tight or binding. The share of jobs on unrated lines is reported beside it.

### 8. Sweden (`engine/sweden.py`, Phase 5)

Sweden is a demonstration, not a validation: no Swedish programme with documented bottlenecks exists to test against.

- **Occupations.** The extra persons on Swedish lines are split into four-digit SSYK 2012 occupations using Statistics Sweden table YREG54BAS for the latest year (2024). The occupation mix of each of its 16 industry groups is applied to every one of the 64 industries in the group. Employees in the "unknown industry" group are left out of the mixes. The "unknown occupation" code (0002) is kept as its own row and flagged; it holds under 1% of the extra jobs in the standard run. The extra jobs follow the run's application: with all 27 programmes applied together, they are the jobs on Swedish lines from every programme.
- **Comparison with forecasts.** The 25 largest occupations are joined to Arbetsförmedlingen's Yrkesbarometer at national level by SSYK code: job prospects, the recruitment situation (shortage, balance, surplus or paradox) and the five-year outlook, as published, translated to English. Where several Yrkesbarometer occupations share one SSYK code, their assessments are listed together. Some occupations have no Yrkesbarometer assessment.
- **ELA shortages report.** The 2025 report publishes no shortage status by occupation for Sweden. Its occupation tables are EU-wide (for example the ten most widespread shortage occupations), and the country lists behind them are not in the report. The ELA column is therefore left empty. Using the EU-wide tables would need an ISCO 2008 to SSYK 2012 concordance and would not describe Sweden.
- **Fields of education.** YREG52BAS gives employees by occupation and ten broad fields of education. For each of the 25 largest occupations, the table shows the most common field among its workers and how many people with that field work in other occupations. The fields are broad (for example "engineering and manufacturing" covers about 1.15 million employees), so this is an upper bound on people who might be qualified, not a count of trained workers outside the trade.
- **Cross-check of construction slack.** Konjunkturinstitutet's monthly construction survey (question 1084, labour as a limiting factor, not adjusted) is set beside the DG ECFIN construction series for Sweden, by SNI 41, 42, 43 and in total. Both are placed in their own history with the same rule as step 5, using twelve-month means. Konjunkturinstitutet collects the Swedish data for DG ECFIN, and over the 58 months in common the two series correlate at above 0.999, so the check confirms the ECFIN series rather than adding evidence. Konjunkturinstitutet's series starts in January 2022, under the five-year minimum, so it gets no class.

Limits:

- YREG54BAS counts employees, not all persons employed. Self-employed workers, common in construction, are outside the mix.
- Industries share their group's mix. Architecture and engineering (M71) takes the mix of all business services (sections M and N), whose largest occupations include cleaners and warehouse staff. Occupations reached mainly through that group, such as cleaners, should be read with this in mind; the table shows which group contributes most to each occupation.
- Konjunkturinstitutet states no reuse licence (gate 1, decision 4). Its values are computed for the cross-check but marked not publishable until the licence is confirmed.

### 9. Robustness (`engine/robustness.py`)

Steps 2 to 7 are repeated on:

- the previous FIGARO edition
- the alternative composition tables
- alternative thresholds
- the vacancy-based slack indicator

The report counts how many ratings change. Lines unrated in either run are counted separately, so a test cannot look stable by producing more unrated lines.

For every run, `engine/sensitivity.py` also re-rates the run's own lines under a grid of pressure thresholds (tight from 1%, 2% or 3%; binding above 3%, 5% or 8%) and of slack cut-offs (elevated above the 50% or 60% point; high from the 67%, 75% or 80% point). Pressure does not depend on the thresholds, so the pressure grid is exact without rerunning the model; the slack grid reruns step 5 only. The results are stored with the run and shown on its threshold page.

### 10. Plausibility (`engine/plausibility.py`, Phase 3)

The French and Irish results are scaled to their official programme sizes and compared with the official job estimates. These are, for France, 170,000 to 250,000 extra full-time jobs for building renovation by 2030; for Ireland, almost 80,000 extra construction workers, according to the Fiscal Advisory Council.

## Rating glossary

The full glossary, which also drives the tooltips in the web app, is [glossary.md](glossary.md). The entries below use the default thresholds.

**Clear.** The shock adds less than 2% to the industry's employment, and firms in the industry report labour as a limiting factor no more often than usual for that series. *Evidence*: both conditions hold. *Cannot establish*: that the extra workers exist and are willing and qualified; only that neither signal points to a problem.

**Tight.** Either the shock adds 2% or more to employment, or firms already report labour shortages more often than the series' median. *Evidence*: at least one of the two signals. *Cannot establish*: whether the shortfall would be met by longer hours, hiring from other industries, migration or delay; or how prices would respond.

**Binding.** The shock adds more than 5% to employment, and the shortage share is in the top quarter of its own history. *Evidence*: both signals at once. *Cannot establish*: that the work could not be done over a longer period, or with workers from elsewhere. Binding means the programme as specified, in one year, is likely to meet a labour constraint in that industry.

**No rating.** The availability evidence is missing, too short, or not comparable, or there is no employment figure. *Cannot establish*: anything about availability; the requirement is still reported.

A rating is a category of estimated risk, not a finding that a programme can or cannot be delivered. Survey shares count firms, not missing workers, and a firm reporting no shortage does not show that it could absorb a large new workload.

## Parameters and defaults

| Parameter | Default | Note |
| :--- | :--- | :--- |
| Shock size | 1% of 2024 GDP | 0.5% and 2% as tests |
| FIGARO edition and reference year | 2026 edition, 2024 | 2023 as a sensitivity; recent years are largely Eurostat projections |
| Composition | standard | Three alternatives for sensitivity |
| Application | simultaneous | "own" as a variant |
| Origin split | gross fixed capital formation (P51G) | Falls back as described in step 1 |
| Slack indicator | DG ECFIN labour share | Job vacancy rate as the alternative |
| Seasonal adjustment | not adjusted | The four-quarter mean removes most seasonality |
| Current slack window | 4 quarters | |
| Minimum slack history | 5 years | Provisional |
| Jobs measure | persons | Provisional; hours shown where published |
| Pressure thresholds | 2% and 5% | |
| Slack thresholds | median and upper quartile of the series' history | |

## Data quality flag

Each member state's row carries a grade, built from the share of that state's shock jobs that sit on weak lines and from notes on construction:

- **good**: at most 10% of the jobs on unrated lines and at most 10% on lines whose employment uses a section ratio, with no construction note
- **limited**: the worst of those shares is at most a third, or a construction note applies
- **poor**: otherwise

Construction notes are raised when the construction slack series is missing or shorter than ten years. The flag text lists the shares and notes behind the grade.

## Concordances

- **FIGARO and national accounts codes** map mechanically, for example `C10-12` to `C10-C12` (`engine/concordances/a64.csv`).
- **DG ECFIN divisions and the 64 industries.** Of the 64 industries, 48 contain divisions the surveys cover. The other 16 have no survey question and are unrated under the primary indicator: agriculture, mining, energy, water and waste, wholesale and retail trade, public administration, education, health and social care, households, and extraterritorial bodies.
- **Statistics Sweden groups and the 64 industries**: 16 groups, so occupation mixes are shared within manufacturing and within business services.
- **Products and industries**: see step 1.

## Questions for the reviewer

1. **Simultaneous or own application** as the default.
2. **Origin of purchases.** Is gross fixed capital formation the right basis for splitting purchases between home and imports?
3. **Combining survey divisions.** Is a simple mean acceptable, or should divisions be weighted by employment, which would need another dataset?
4. **Reference year.** 2024 matches the shock year but is largely projected by Eurostat; 2023 rests on more reported data.
5. **Prices.** FIGARO is at basic prices, while spending is at purchasers' prices. The shock is applied without removing taxes and margins, which overstates required output slightly. Should the shock be converted?
6. **The rating rule**, in particular whether "tight" should follow from elevated slack alone even when pressure is tiny. Under the rule as written it does, but its weight in the headline is only the jobs on that line.
7. **The minimum history for slack**, five years by default. Ireland's survey series start in 2016.
8. **The threshold reasoning** above. Is year-on-year employment growth a fair reference for the pressure thresholds, or is there a better one, such as the growth industries achieved in past expansions?
