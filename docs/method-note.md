# Method note

Capacity Check Europe (working name), Season 1 demonstrator. Draft for review, 29 October 2026. Updated through Phase 7.

## The question

When the same public spending shock is applied in every EU member state, which industries does it press on, and are those industries already short of labour?

The standard shock is additional public spending equal to 1% of each member state's 2024 GDP, in one year, on housing and energy renovation. The composition of the products bought directly is the same in every country. Test runs use 0.5% and 2%.

**This is an identical financial shock, not an identical physical programme.** One per cent of GDP buys different amounts of renovation in different countries, because prices, wages and the building stock differ. The result says where the money would press, not how many homes would be renovated.

## What the result claims and does not claim

- It locates pressure. It does not size price changes, because input-output analysis assumes fixed proportions and no price response.
- It has no deficit or debt term.
- It makes no claim about fiscal space for eurozone members, which are currency users.
- It cannot see constraints in permits, grid connections, planning or training capacity.
- It scores against labour available in the country. Migration and posted workers are a named limitation, not part of the model.
- At 64 industries, results are bands, not point estimates.
- Requirement (what the shock needs) and availability (what firms report about labour) are shown separately before they are combined into a rating.

Of the five programme questions (what a policy requires, what exists, what can be mobilised, over what time, within what limits), this method answers the first, gives a partial answer to the second, and does not answer the last three. Survey shares of firms reporting shortages are evidence about the second question, not a measure of how much labour could be mobilised.

## From shock to rating

The engine is a Python package in `engine/`. Every step below names its module, and every parameter is in `engine/params.py` with the default shown here.

### 1. Direct demand (`engine/shock.py`)

For member state *c*, the shock is *s* per cent of 2024 GDP at current prices (`nama_10_gdp`, B1GQ, million euros). It is split across products by the composition table (`docs/composition-table.md`).

FIGARO's tables are industry by industry, so a purchase of a product is assigned to the industry with the same two-digit code. For example, construction work (CPA F) is assigned to construction (F).

Each product's purchases are then split by origin economy. The split uses the shares in which *c* already buys that product for gross fixed capital formation (P51G) in the FIGARO table. If *c* records no such purchases, it falls back to all final demand of *c*, and then to all-domestic. The basis used is reported for every product and country.

### 2. Supply chains (`engine/io_model.py`)

The inter-country table has 50 economies (the 27 member states, 22 other economies, and the rest of the world) by 64 industries. Technical coefficients are *A = Z / x* by column, where *Z* is intermediate flows and *x* total output. The Leontief inverse *L = (I - A)^-1* is computed once per edition and reference year and cached.

Required output for direct demand *y* is *L y*: the output each industry in each economy must produce, directly and through its supply chain. For each member state's shock, required output is split into home, rest of the EU and outside the EU.

**Application.** By default all 27 member states apply the shock at once, so the pressure on an industry adds up demand from every programme. For example, German machinery serves French and Italian renovation as well as German. The alternative, "own", counts only the member state's own programme.

### 3. Jobs (`engine/jobs.py`)

Extra persons employed in industry *i* of member state *c* equal required output times persons employed per million euros of output. Persons come from `nama_10_a64_e` (EMP_DC, THS_PER) for the FIGARO reference year, and output from FIGARO for the same year. Hours worked (THS_HW) are computed the same way and shown where published.

Where national accounts give no figure for an industry, the ratio for its NACE section is used and the line is flagged. Economies outside the EU get output requirements but no jobs estimate.

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

The thresholds are parameters. A rating is never forced: missing or unusable evidence gives "no rating".

### 7. Headline

For each member state's shock, the headline is the share of the jobs it creates in the EU that fall on lines rated tight or binding. The share of jobs on unrated lines is reported beside it.

### 8. Sweden (`engine/sweden.py`, Phase 5)

Swedish industry jobs are split into four-digit occupations using Statistics Sweden table YREG54BAS. The occupation mix of each of its 16 industry groups is applied to every one of the 64 industries in the group. The largest occupations are compared with Arbetsförmedlingen's Yrkesbarometer and the ELA shortages report. Sweden is a demonstration, not a validation.

### 9. Robustness (`engine/robustness.py`)

Steps 2 to 7 are repeated on:

- the previous FIGARO edition
- the alternative composition tables
- alternative thresholds
- the vacancy-based slack indicator

The report counts how many ratings change. Lines unrated in either run are counted separately, so a test cannot look stable by producing more unrated lines.

### 10. Plausibility (`engine/plausibility.py`, Phase 3)

The French and Irish results are scaled to their official programme sizes and compared with the official job estimates. These are, for France, 170,000 to 250,000 extra full-time jobs for building renovation by 2030; for Ireland, almost 80,000 extra construction workers, according to the Fiscal Advisory Council.

## Rating glossary

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
| Composition | standard | Two alternatives for sensitivity |
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
