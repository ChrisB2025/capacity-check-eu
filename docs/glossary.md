# Glossary

Generated from `engine/text/glossary.yaml` by `python -m engine glossary`; edit that file, not this one. The same text drives the tooltips and the glossary page in the web app. Values shown are the defaults; in the web app they follow the run being viewed.

**Ratings are estimated risk categories: risk indicators, not factual judgements about whether a programme can be delivered.**

## The question

### Shock

The extra public spending tested: 1% of each member state's 2024 GDP, spent in one year on housing and energy renovation.

*Why it matters.* A shock of the same size relative to each economy puts every member state on the same footing. It is an identical financial shock, not an identical physical programme.

*Limit.* One shock cannot match each country's climate, housing stock, tenure, income or habits. Compare relative pressure, not what each country would need to spend or do.

*Source.* [Eurostat, GDP and main components (nama_10_gdp)](https://ec.europa.eu/eurostat/databrowser/view/nama_10_gdp/default/table): B1GQ, current prices, million euros, 2024.

### Composition

How the shock is split between the things bought directly: construction work, heating equipment, the trade margin on that equipment, and design and supervision. The same split is used in every member state.

*Why it matters.* It is the main judgement in the method. It decides which industries the money reaches first.

*Source.* [Composition table (docs/composition-table.md)](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/composition-table.md): Quirion (2013) for France and the KfW retrofit monitoring (2016) for Germany.

*Also used by.* [Quirion (2013), input-output allocation of deep renovation in France](https://negawatt.org/IMG/pdf/etude_p.quirion_emplois_et_scenario_negawatt_28-03-2013.pdf); [Cambridge Econometrics et al. (2015) for DG ENER, split of energy efficiency spending by sector](https://circabc.europa.eu/rest/download/4ba02aea-682c-4872-ab92-2d0284786e91).

### Risk indicator

What every result here is: an early signal of where a programme could run into labour shortages, built from two published measures. It is not a forecast and not a verdict on whether a programme can be delivered.

*Why it matters.* The tool screens for real resource risk before a programme is designed, so that the industries flagged can be looked at more closely.

*Source.* [Method note (docs/method-note.md)](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): Sections: Risk indicators, not judgements; Where the tool sits.

## The model

### Input-output table

A table of who buys what from whom: each industry's purchases from every other industry, at home and abroad, and what goes to final users such as households, government and investment.

*Why it matters.* It lets the model follow spending down supply chains, so renovation also shows up as demand for cement, machinery and transport.

*Source.* [Eurostat, FIGARO inter-country input-output tables](https://ec.europa.eu/eurostat/cache/metadata/en/naio_10_fcp_esms.htm): 2026 edition, industry by industry, reference year 2024.

*Also used by.* [Quirion (2013), employment effect of the energy transition in France](https://negawatt.org/IMG/pdf/etude_p.quirion_emplois_et_scenario_negawatt_28-03-2013.pdf); [Cambridge Econometrics et al. (2015), employment and social impact of energy efficiency, for DG ENER](https://circabc.europa.eu/rest/download/4ba02aea-682c-4872-ab92-2d0284786e91).

### FIGARO

Eurostat's input-output tables for the EU: 50 economies (the 27 member states, 22 other economies and the rest of the world) by 64 industries, one table per year.

*Why it matters.* It is the official source that links every member state's industries to each other and to imports, so spending in one country can press on industries in another.

*Limit.* The 2024 table rests largely on Eurostat projections. 2023, which rests on more reported data, is run as a check.

*Source.* [Eurostat, FIGARO (naio_10_fcp)](https://ec.europa.eu/eurostat/cache/metadata/en/naio_10_fcp_esms.htm): 2026 edition, reference year 2024.

*Also used by.* [Eurostat and the European Commission's Joint Research Centre, which built it, for analysis of trade and value added](https://ec.europa.eu/eurostat/cache/metadata/en/naio_10_fcp_esms.htm).

### NACE A64

The EU's list of industries (NACE Rev. 2) grouped into 64 industries. Construction, for example, is one industry, F, which covers NACE divisions 41 (buildings), 42 (civil engineering) and 43 (specialised trades such as installation and finishing).

*Why it matters.* It is the finest detail at which both the input-output tables and the employment figures exist for all 27 member states, so no result can be more detailed than this.

*Limit.* Construction cannot be split into the trades renovation needs. The Sweden layer shows how far an occupational register can do it.

*Source.* [Concordance used by the engine (engine/concordances/a64.csv)](https://github.com/ChrisB2025/capacity-check-eu/blob/main/engine/concordances/a64.csv): FIGARO codes, NACE sections and divisions, national accounts codes.

### Line

One industry in one member state, for example construction in Germany. Pressure, shortage level and estimated risk category are given per line.

*Why it matters.* Labour is counted where the work is done, so each line is scored against its own workforce.

*Source.* [Concordance used by the engine (engine/concordances/a64.csv)](https://github.com/ChrisB2025/capacity-check-eu/blob/main/engine/concordances/a64.csv): 27 member states by 64 industries.

### Direct purchases

The shock split by product, following the composition, and by where each product comes from, following where the member state already buys it for investment.

*Why it matters.* Part of the money leaves the country at the first step, through imported equipment.

*Source.* [Eurostat, FIGARO](https://ec.europa.eu/eurostat/cache/metadata/en/naio_10_fcp_esms.htm): Each member state's existing purchases for gross fixed capital formation (P51G).

### Required output

The output every industry must produce to meet the shock, directly and through its supply chain, in million euros. It is computed with the Leontief inverse of the input-output table.

*Why it matters.* It is the demand side of the comparison: what the programme asks of each industry.

*Source.* [Eurostat, FIGARO](https://ec.europa.eu/eurostat/cache/metadata/en/naio_10_fcp_esms.htm): 2026 edition, reference year 2024.

*Also used by.* [Cambridge Econometrics et al. (2015), for DG ENER](https://circabc.europa.eu/rest/download/4ba02aea-682c-4872-ab92-2d0284786e91).

### At home, rest of EU, outside EU

Where the required output is produced: in the member state that spends, in other member states, or outside the EU. Each is a share of the total.

*Why it matters.* Pressure falls where the work is done, which is not always where the money is spent.

*Source.* [Eurostat, FIGARO](https://ec.europa.eu/eurostat/cache/metadata/en/naio_10_fcp_esms.htm): 2026 edition, reference year 2024.

### Simultaneous or own application

Simultaneous: all member states in the run spend at once, so the pressure on an industry adds up demand from every programme. Own: each member state's industries see only its own programme.

*Why it matters.* A Europe-wide programme would draw on the same suppliers, for example German machinery for French and Italian renovation.

*Source.* [Method note, step 2](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): Simultaneous is the default.

### Jobs conversion

Required output turned into persons employed, using each industry's current persons employed per million euros of output in that member state.

*Why it matters.* Shortages are about people, so the demand has to be expressed in people before the two can be compared.

*Limit.* A job estimate is not a hire. Firms can move existing staff from other work, and households or housing cooperatives can swap grant-funded work for work they had already planned, such as postponing a roof replacement to insulate. A high estimated risk category signals a risk of pressure, not certain hiring.

*Source.* [Eurostat, employment by 64 industries (nama_10_a64_e)](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64_e/default/table): EMP_DC, thousand persons, 2024, with FIGARO output for the same year.

*Also used by.* [Quirion (2013), jobs per million euros of renovation in France](https://negawatt.org/IMG/pdf/etude_p.quirion_emplois_et_scenario_negawatt_28-03-2013.pdf); [Irish Fiscal Advisory Council (2024), construction workers needed for Ireland's infrastructure plans](https://fiscalcouncil.ie/wp-content/uploads/2024/10/Irelands-Infrastructure-Demands.pdf).

### Employment multiplier

Persons employed per million euros of spending, counting the whole supply chain. It comes from applying each industry's persons per million euros of output to the required output.

*Why it matters.* It differs between member states because wages and productivity differ, which is one reason the same financial shock occupies different numbers of people.

*Source.* [Eurostat, nama_10_a64_e and FIGARO](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64_e/default/table): 2024.

## Measures shown

### Extra persons

The number of people the shock would occupy for a year, at today's output per person, in the EU or on one line.

*Why it matters.* It is the size of the demand in the same unit as the workforce, so it can be set against it.

*Limit.* Not new hires. Firms can reprioritise existing capacity, and households can swap grant-funded work for work they had already planned.

*Source.* [Eurostat, nama_10_a64_e and FIGARO](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64_e/default/table): 2024.

### Pressure

Extra persons on a line as a share of the persons it employs now. 6% means the industry would need 6 more workers for every 100 it has.

*Why it matters.* It shows how large the programme is for that industry, which is one of the two signals behind the estimated risk category.

*Source.* [Eurostat, nama_10_a64_e](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64_e/default/table): EMP_DC, thousand persons, 2024.

### Labour shortage indicator (slack)

The share of firms that name labour as a factor limiting their activity, from the European Commission's business surveys of construction, industry and services in each member state.

*Why it matters.* It is the only shortage measure published in the same way for every member state and most industries, monthly or quarterly, over many years.

*Limit.* It counts firms, not missing workers. A firm reporting no shortage has not shown that it could take on a large new workload.

*Source.* [European Commission (DG ECFIN), business and consumer surveys](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/overarching-methodological-concepts_en): Release of October 2026; construction question 2, industry question 8, services question 7.

*Also used by.* [European Commission, business and consumer survey reports](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/download-business-and-consumer-survey-data/subsector-data_en); [Sveriges Riksbank (2023), new indicators of resource utilisation](https://www.riksbank.se/globalassets/media/rapporter/ekonomiska-kommentarer/svenska/2023/nya-indikatorer-pa-resursutnyttjandet.pdf).

### Shortage share now

The share of firms naming labour as a limiting factor, averaged over the latest four complete quarters.

*Why it matters.* Averaging a full year removes most seasonal swings.

*Source.* [European Commission (DG ECFIN), business and consumer surveys](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/overarching-methodological-concepts_en): Release of October 2026, not seasonally adjusted.

### Percentile in its own history

Where the shortage share now sits in the series' own history. 90% means the share has been lower in nine of every ten periods since the series began.

*Why it matters.* Firms in different countries answer the survey differently, so each series is compared with its own past, not with other countries.

*Source.* [European Commission (DG ECFIN), business and consumer surveys](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/overarching-methodological-concepts_en): Whole history of each series; at least 5 years needed.

### Shortage level (low, elevated, high)

Low: at or below the median of the series' history. Elevated: above it. High: in the top quarter of its history.

*Why it matters.* It is the second signal behind the estimated risk category: whether firms already report more labour shortages than usual.

*Source.* [European Commission (DG ECFIN), business and consumer surveys](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/overarching-methodological-concepts_en): Release of October 2026.

### Jobs on tight or binding lines

The headline for a member state: the share of the jobs its programme creates anywhere in the EU that fall on lines rated tight or binding.

*Why it matters.* It sums up, in one number, how much of the programme's work lands where there are signs of labour pressure.

*Limit.* Member states are separated only weakly by it: construction is under pressure everywhere, and shortage reports are high in most industries in 2025 and 2026.

*Source.* [Engine output, countries table](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): Computed from the two signals above.

### Jobs on unrated lines

The share of the programme's jobs that fall on lines with no estimated risk category, mostly because the business surveys do not cover that industry.

*Why it matters.* A low headline can come from missing evidence rather than from spare capacity; this shows how much is missing.

*Source.* [Concordance of survey divisions to the 64 industries](https://github.com/ChrisB2025/capacity-check-eu/blob/main/engine/concordances/a64.csv): 48 of 64 industries have a survey series.

### Data quality

A grade for each member state's result. Good: at most 10% of its jobs on unrated lines or lines with estimated employment, and no construction note. Limited: up to a third, or a construction note. Poor: more.

*Why it matters.* It tells you how far to trust one member state's result before comparing it with others.

*Source.* [Method note, data quality flag](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): Grades set by the team; reasons listed with each grade.

## Estimated risk categories

### Thresholds

The four cut-offs that turn the two signals into categories: pressure of 2% (tight from here) and 5% (binding above this), and shortage reports above the median or in the top quarter of their own history.

*Why it matters.* They are judgements made by the team. Each has a stated reason, and the threshold page shows how the results change when they move.

*Reasoning.* Why 2%, the default for tight: from 2011 to 2024, an industry's workforce in a member state grew by 2% or more in a year in about 31% of cases, weighted by employment (29% for construction). An extra 2% is within what industries sometimes manage, but large enough to notice on top of normal growth. Why 5%, the default for binding: growth of 5% or more in a year happened in about 9% of cases (9% for construction), so it asks an industry for something it rarely does. Why the median: above it, more firms than usual already report labour as a limit. Why the top quarter: it is the tightest quarter of periods on record for that series, and binding needs it as well as high pressure.

*Source.* [Eurostat, nama_10_a64_e (reference figures) and DG ECFIN surveys](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/results/threshold_reference.csv): docs/results/threshold_reference.csv.

### Estimated risk category

Clear, tight or binding: how strongly the two signals, pressure and shortage level, point to labour pressure on a line. Lines without evidence get no category.

*Why it matters.* It flags where to look first. It is a risk indicator, not a factual judgement about whether a programme can be delivered.

*Source.* [Method note, step 6](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): Rule proposed in the specification and tested here.

### Clear

The shock adds less than 2% to the line's workforce, and firms report labour shortages no more often than the median of the series' history.

*Why it matters.* Neither signal points to a problem.

*Limit.* It does not show that the extra workers exist, or are willing and qualified.

*Source.* [Method note, rating glossary](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): Pressure from nama_10_a64_e and FIGARO; shortage level from DG ECFIN surveys.

### Tight

Either the shock adds 2% or more to the line's workforce, or firms already report labour shortages more often than the median of the series' history.

*Why it matters.* At least one signal points to pressure.

*Limit.* It cannot say whether a shortfall would be met by longer hours, hiring from other industries, migration or delay, or how prices would respond.

*Source.* [Method note, rating glossary](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): Pressure from nama_10_a64_e and FIGARO; shortage level from DG ECFIN surveys.

### Binding

The shock adds more than 5% to the line's workforce, and shortage reports are in the top quarter of their own history.

*Why it matters.* Both signals at once: the programme as specified, in one year, is likely to meet a labour constraint in that industry.

*Limit.* It cannot show that the work could not be done over a longer period, or with workers from elsewhere.

*Source.* [Method note, rating glossary](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): Pressure from nama_10_a64_e and FIGARO; shortage level from DG ECFIN surveys.

### No rating

The shortage evidence is missing, too short (under five years) or not comparable, or there is no employment figure. No category is forced.

*Why it matters.* Missing evidence is shown as missing, not as clear.

*Source.* [Method note, step 5](https://github.com/ChrisB2025/capacity-check-eu/blob/main/docs/method-note.md): 16 of the 64 industries have no survey question.

## Sweden

### Share of the occupation's employees

Extra persons in a Swedish occupation as a share of the people employed in it now, splitting each industry's extra persons by its current occupation mix.

*Why it matters.* It is the occupational version of pressure, and the only place the tool can show trades such as electricians or insulation workers.

*Limit.* Counts employees only; the self-employed, common in construction, are outside the mix.

*Source.* [Statistics Sweden, occupational register (YREG54BAS)](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__AM__AM0208__AM0208E/): Employees by occupation (SSYK 2012) and industry group, 2024.

### Recruitment situation and outlook

The Swedish Public Employment Service's assessment of each occupation: job prospects, whether employers find it hard to recruit, and the five-year outlook.

*Why it matters.* It is an independent, occupation-level view to set beside the model's estimate.

*Source.* [Arbetsförmedlingen, Yrkesbarometer](https://jobtechdev.se/en/components/yrkesprognoser?q=Dataset): Round 2026-1, open data.
