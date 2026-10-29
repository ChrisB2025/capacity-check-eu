# **Real Resource Scoring for Europe: Season 1 Demonstrator Specification**

Oct 9, 2026 · @ChrisB

## **Executive summary**

Real resource scoring asks a different question of public spending: not what it costs in money, but whether the people, skills and productive capacity exist to deliver it. This initiative is a proof of concept (PoC) that tests whether that question can be answered for Europe from open official data. It is proposed as the Mission & Strategy Season 1 objective, to report by early December 2026\.

**Aims**

* Find out early whether EU data are robust enough to support real resource scoring.  
* Show, with one worked case, what a resource score looks like for all 27 member states.  
* Give the Funding WG evidence on whether this can become a grant project.  
* Create a concrete basis for collaboration with the Swedish network and its planned research application.

**Initial scope**

* **One standard shock.** Additional public spending of 1% of GDP on housing and energy renovation, applied identically in every member state. It is comparable across countries and tied to no party or programme.  
* **An EU-wide layer.** For 64 industries in each of the 27 member states, where the shock lands and whether firms there already report labour shortages.  
* **A Sweden layer.** The same result broken down into named occupations, using Statistics Sweden tables.  
* **Not included.** Scoring real bills or budgets, open public intake of proposals, materials and energy limits, and any inflation forecast.

**Key conditions of the PoC**

1. **One-off.** A demonstrator on a small hosted web app that can be switched off, not a standing service.  
2. **Standalone.** Its own name, repository and method, with no code, brand or hosting shared with the US project.  
3. **Open.** Code, data versions, assumptions and rating thresholds are all published.  
4. **Reviewed from outside.** An input-output economist outside the MMT community checks the method before results are run.  
5. **Published either way.** The result is released even if it shows a popular programme running into binding limits.  
6. **Modest claims.** It is a resource risk indicator. It is not an inflation forecast, and for eurozone members it makes no claim about fiscal space.  
7. **No funding needed.** Under EUR 1,000 in cash for the season: a reviewer's fee, Railway hosting and Anthropic API use. The real cost is about 28 to 42 volunteer days.  
8. **A stopping rule.** The work stops and reports why if the data fail agreed tests.

**Likely output**

* A short report with one results table per country and a map of where the shock meets constrained industries.  
* A headline figure per country: the share of the shock's jobs that falls on industries rated tight or binding.  
* For Sweden, the occupations most in demand, set against official shortage forecasts.  
* A robustness finding: how far results move when Eurostat revises its tables.  
* A web app where a user can change the shock and see the results, with a method note and a public repository that anyone can rerun.

**Why it is useful**

* **It settles the data question.** Either result is informative: a pass justifies a specification for something larger, and a fail saves the association from building on weak ground.  
* **It gives allies something usable.** Unions, housing and climate organisations can see which trades and industries a programme would need first. That turns "can we afford it" into "what must be trained and sequenced".  
* **It fills a real gap.** National bodies in Germany, Ireland and the Netherlands assess capacity one country and one programme at a time. No open method applies the same test across member states.  
* **It makes funding possible later.** No funder found will pay a new, unstaffed association to build this. A published proof, with first-year accounts in early 2027, is what a credible application needs.  
* **It strengthens the Swedish link.** The Sweden layer is a ready contribution to the 2045 production model application and a reason for Stephen Hinton to lead.

**Recommendation.** Adopt the PoC as the Mission & Strategy Season 1 objective at the General Meeting on 13 October 2026, with the Research WG checking the method. The viability assessment of 9 October 2026 found the concept viable with conditions, and this scope stays inside them.

## **The brief and decisions taken**

The Mission & Strategy meeting on 8 October 2026 proposed an EU counterpart to the US resource scoring specification as the Season 1 objective. The aim was to find out early whether EU data are robust enough, and whether this could become a grant project for the Funding WG.

Mission & Strategy generates ideas and does not necessarily deliver them, so the Research WG is involved from the start.

| Question | Decision (9 October 2026\) |
| :---- | :---- |
| Product | A one-off demonstrator, not a periodic indicator or a standing service |
| Geography | EU-wide as the ideal, with Sweden as the detailed case. France, then Ireland and Italy, are later options |
| What is scored | A standard shock applied to every member state, not a real programme |
| Relationship to the US project | Standalone, for political reasons |
| Infrastructure | A small Railway-hosted web app with a browser interface and Anthropic API connections |

## **Scope**

The demonstrator answers one question: when the same spending shock is applied in each member state, which industries and countries does it press on, and are those already short of labour or capacity?

**In scope**

* One shock, 27 member states, 64 industries, one reference year.  
* A banded rating per industry and country: clear, tight or binding.  
* Occupation detail for Sweden only.  
* A robustness test across data editions.  
* A hosted web interface for inputs and results, a short report, a method note and open code.

**Out of scope for Season 1**

* Scoring real bills, budgets or manifestos.  
* User accounts and open public intake of proposals.  
* Materials, energy and grid constraints, beyond naming them as limits.  
* Regional detail below country level.  
* Any inflation forecast.

**How it differs from the US specification**

|  | US specification | EU demonstrator |
| :---- | :---- | :---- |
| Object scored | Federal bills | One standard shock |
| Industry detail | About 400 industries | 64 industries |
| Occupation detail | About 800 occupations nationally | Sweden only, 4-digit occupations by 16 industry groups |
| Spending bridge | Past federal spending records | Built by hand and published |
| Cross-border supply chains | Not modelled | Modelled for 49 economies |
| Product | A service in four phases | A one-off proof |

**Framing for the eurozone.** Eurozone members are currency users, so the US argument for a resource score beside the deficit score does not carry over. The demonstrator makes no claim about how spending is financed. It reports whether the work could be delivered and where price pressure is likely. Sweden, with its own currency, is the cleaner case for the wider argument.

## **The standard shock**

The shock is additional public spending of 1% of each member state's GDP in one year on housing and energy renovation, with the same composition in every country.

**Why housing and renovation**

* European bottleneck cases concentrate in work that cannot be imported: construction labour, installation and care. The viability assessment found this in every case reviewed.  
* Official estimates exist to check against. France has an official range of 170,000 to 250,000 extra full-time jobs for building renovation by 2030\. The Irish Fiscal Advisory Council estimates almost 80,000 extra construction workers for Ireland's infrastructure needs.  
* It is relevant in every member state and belongs to no single political family.  
* Stephen Hinton's Real Capital post uses housing insulation as its own worked example, which gives the two projects a shared case.

**How the shock is defined**

1. **Size.** 1% of 2024 GDP per member state, from Eurostat national accounts. Runs at 0.5% and 2% test whether ratings change with scale.  
2. **Composition.** A fixed split across the products bought directly: construction work, building materials and components, heating equipment, and design and engineering services. The split is set from published renovation cost breakdowns and recorded in one table with its sources.  
3. **Imports.** Each country's existing purchase pattern in the Eurostat tables decides how much of each product is bought at home, elsewhere in the EU, or outside it.

The composition table is the main judgement in the project. It is published in full and sent to the outside reviewer before any results are run.

**Known weakness.** A stylised shock has no outcome to test against. The checks are plausibility against the French and Irish estimates, scaled to their programme sizes, and stability across data editions.

## **Data**

Every input is free and published by an official body. Eurostat data can be republished with attribution; the other licences are confirmed in stage 1\.

**EU-wide layer**

| Source | What it gives | Known limit |
| :---- | :---- | :---- |
| [Eurostat FIGARO tables](https://ec.europa.eu/eurostat/cache/metadata/en/naio_10_fcp_esms.htm), 2026 edition | Who buys what from whom: 64 industries, 49 economies, 2010 to 2024 | Whole series revised each year; Eurostat states accuracy as not available |
| [Eurostat national accounts employment](https://db.nomics.world/Eurostat/nama_10_a64_e?tab=table) | Persons and hours worked by the same 64 industries, per country, to 2024 | Some country-years are estimated |
| [Commission business surveys](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/overarching-methodological-concepts_en) (DG ECFIN) | Quarterly share of firms naming labour, materials or demand as the factor limiting activity; capacity utilisation | Shares of firms, not quantities; [sector files](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/download-business-and-consumer-survey-data/subsector-data_en) not fully validated |
| [Eurostat job vacancy statistics](https://ec.europa.eu/eurostat/cache/metadata/en/jvs_esms.htm) | Vacancy rates by broad sector | Incomplete for France, Italy and Denmark |
| [European Labour Authority shortage report 2025](https://www.ela.europa.eu/sites/default/files/2026-06/labour-shortages-report-ela-2025.pdf) | Shortage status of 436 occupations in 28 countries | Each country uses its own method; no headcounts |

**Sweden layer**

| Source | What it gives | Known limit |
| :---- | :---- | :---- |
| [Statistics Sweden occupational register](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__AM__AM0208__AM0208E/), table YREG54BAS | Employees by 4-digit occupation and industry, 2020 to 2024 | Industry in 16 broad groups, so construction is one group |
| Same register, table YREG52BAS | Occupation by field of education, which shows qualified people working elsewhere | Not yet tested for this use |
| [Swedish Public Employment Service forecasts](https://jobtechdev.se/en/components/yrkesprognoser?q=Dataset) | Outlook for about 170 occupations, as open data | Coverage of construction trades to confirm |
| [National Institute of Economic Research business survey](https://statistik.konj.se/PxWeb/pxweb/sv/KonjBar/KonjBar__ftgkvartal/Bartotq.px) | Quarterly labour shortage indicator since 1987 | The table read covers the whole business sector; sector tables to locate |
| [Riksbank resource utilisation indicator](https://www.riksbank.se/globalassets/media/rapporter/ekonomiska-kommentarer/svenska/2023/nya-indikatorer-pa-resursutnyttjandet.pdf) | An official reference for what counts as high resource use | Economy-wide only |

**Gaps the demonstrator does not close**

* No EU-wide occupation by industry table at useful detail. Outside Sweden, results stop at the industry.  
* No data on training capacity or time to competence, so the result cannot say how fast a shortage could ease.  
* Eurostat keeps only the latest version of each dataset. Every download is saved with its date and a checksum.

## **Method**

The shock is traced through supply chains to industries, converted to jobs, and compared with what firms in each industry already report about shortages.

**From shock to rating**

1. **Direct demand.** Apply the composition table to 1% of each country's GDP. This gives euros of direct purchases by product.  
2. **Supply chains.** Run the direct purchases through the FIGARO tables using standard input-output analysis. This gives the output required from each of 64 industries in each of 49 economies, split into home, rest of EU and outside the EU.  
3. **Jobs.** Multiply each industry's required output by its jobs and hours per euro of output, from national accounts.  
4. **Pressure.** Express the extra jobs as a share of that industry's current employment in that country.  
5. **Starting slack.** Take the share of firms in that industry and country naming labour as the factor limiting activity. Compare it with the same series' own history.  
6. **Rating.** Rate each line as clear, tight or binding from pressure and starting slack together.  
7. **Headline.** For each country, report the share of the shock's jobs that falls on tight or binding lines.  
8. **Sweden.** Split Swedish industry jobs into 4-digit occupations using the occupational register. Compare the largest occupations with the Employment Service forecasts and the European shortage list.  
9. **Robustness.** Repeat steps 2 to 7 on the previous FIGARO edition and report how many ratings change.  
10. **Plausibility.** Scale the French and Irish results to their official programme sizes and compare with the official job estimates.

**Proposed rating rule (to be tested, not final)**

| Rating | Pressure: extra jobs as share of industry employment | Starting slack: firms naming labour as the limit |
| :---- | :---- | :---- |
| Clear | Under 2% | At or below the series' long-run median |
| Tight | 2% to 5%, or | Above the long-run median |
| Binding | Over 5%, and | In the top quarter of the series' history |

The thresholds are judgement calls. The report shows how results change when they move, and the outside reviewer is asked to challenge them.

**What the result claims**

* It locates pressure. It does not size price changes, because input-output analysis assumes fixed proportions and no price response.  
* It has no deficit or debt term.  
* It scores against labour available in the country. Migration and posted workers are a named limitation, not part of the model.  
* It cannot see constraints that sit in permits, grid connections or planning capacity.  
* At 64 industries, results are bands, not point estimates.

## **Build and tooling**

The demonstrator is a small web application hosted on Railway. A user sets the shock in a browser, the server runs the model, and the page shows the results. The Anthropic API handles language tasks where they help. It never produces a number.

**Environment**

| Part | Choice | Reason |
| :---- | :---- | :---- |
| Hosting | A new Railway project: one web service, one PostgreSQL database, one volume for data files | Familiar platform; kept apart from every other MML and US service |
| Web framework | Django with HTMX | The stack already in use, so no new skills are needed |
| Model engine | A plain Python package using [pymrio](https://pypi.org/project/pymrio/) or [MARIO](https://mario-suite.readthedocs.io/en/latest/) | Maintained open libraries; the package also runs without the web app, so anyone can reproduce a result |
| Speed | Supply chain matrices are computed once per data edition and stored | A run is then a multiplication and should return in seconds |
| Background worker | None at first | Added only if runs prove slow |
| Database | PostgreSQL holds saved runs, their inputs, composition tables and data edition records | Every result can be traced to its inputs |
| Data files | Each download stored with source, edition, date and checksum | Eurostat keeps no past versions |
| AI | Anthropic API, called from the server; key held as a Railway variable; monthly spend cap | Keeps the key out of the browser and the cost bounded |
| Access | Shared login until the reviewer signs off, then public and read-only | Avoids unreviewed results circulating |
| Code | New public repository, open licence | No link to the US codebase |
| Name | Neutral, with no reference to modern money. Working options: Capacity Check Europe, Real Resource Check | The logic should stand without the label |

**Web interface: inputs**

* Shock size, from 0.5% to 2% of GDP.  
* Composition of the shock, starting from the published standard table.  
* Countries to show.  
* Data edition, so the robustness test can be run from the page.  
* Rating thresholds, with the proposed values as defaults.

**Web interface: outputs**

* A country table with the headline share of jobs on tight or binding industries.  
* A map of the same figure.  
* Industry detail for any country, split into home, rest of EU and outside the EU.  
* For Sweden, the occupations most in demand beside official forecasts.  
* Download of every table as CSV, and a link that reopens a saved run.  
* A plain-language briefing drafted by AI and labelled as such.

**Where the Anthropic API is used**

| Use | What it does | Control |
| :---- | :---- | :---- |
| Briefing | Drafts a one-page summary of a run from the result tables | Figures are inserted from the tables and checked against them by code |
| Shock builder | Turns a spending package described in words into a proposed composition | The user confirms or edits it before any run; the result is marked as user-defined, not the standard shock |
| Explanation | Answers questions about a run, such as why an industry is rated tight | Answers draw only on that run's data and the method note |
| Translation | Renders a briefing in Swedish, French or another language | The figures and ratings are not translated or changed |

**AI guardrails**

* Every number comes from the model engine. The API never produces or adjusts a figure.  
* Prompts state the resource frame and bar any claim about inflation forecasts or fiscal space.  
* A fixed set of test runs is rechecked whenever a prompt changes.  
* AI text is labelled on screen and in downloads.  
* Calls are rate limited, and no personal data is sent.

**Not built in Season 1\.** User accounts, open public intake of proposals, scoring of real bills, occupation detail beyond Sweden, and a link to a stock-flow model for supply response.

## **Season 1 work plan**

Four stages end on 4 December 2026, each with a check that can stop the work. Dates are proposals for the working groups to agree.

1. **Agree and staff (by 13 October).** Present the objective at the General Meeting. Confirm a project lead and a Research WG contact. Invite Stephen Hinton to lead.  
2. **Data check (by 30 October).** Create the repository and the Railway project. Download and save every source. Confirm three things:  
   * the Commission sector files hold the labour constraint question for most member states;  
   * an earlier FIGARO edition can still be obtained for the robustness test;  
   * the Swedish occupation tables load and join to the 64 industries.  
3. **EU-wide run (by 20 November).** Agree the composition table with the reviewer. Run steps 1 to 7 and the robustness test. Deploy the web app behind a shared login and circulate the first results.  
4. **Sweden and write-up (by 4 December).** Run the Sweden layer and the plausibility check. Take reviewer comments. Add the briefing and shock builder. Finish the report and method note. Decide on publication and on the funding path.

**Stopping rule (proposed).** Stop and report the reason if any of these holds:

* The labour constraint series is missing for more than a third of member states.  
* More than a quarter of ratings change between two FIGARO editions.  
* The French and Irish checks differ from the official estimates by more than a factor of two with no explanation.  
* No reviewer outside the MMT community agrees to comment.

A stop is a useful result. It answers the data question that prompted the project.

## **People and roles**

The project needs a lead, a builder, a method checker and one outside reviewer. Only the builder is settled.

| Role | Proposed | Status |
| :---- | :---- | :---- |
| Sponsor | Mission & Strategy WG | Proposed on 8 October |
| Project lead | Stephen Hinton | Not yet asked |
| Build and data | Chris Bland | Agreed |
| Method and data checking | Research WG, through Johannes Borgström | To confirm |
| Swedish sources and language | Swedish-speaking WG members | To confirm |
| Outside reviewer | An input-output economist outside the MMT community | To find |
| Academic link | The Göttingen connection | To confirm who holds it |

**Why Stephen Hinton is the natural lead**

His post [Modelling Real Capital with system dynamics](https://www.patreon.com/StephenHinton/posts/modelling-real-171738423) describes real capital by its functional state, from fully functional through pressured to degraded. The demonstrator's clear, tight and binding ratings are a measured reading of the same idea for one kind of capital: the workforce and firms that deliver a programme.

* **A shared case.** His post uses housing insulation as its example of one investment moving several capitals at once. The standard shock is that investment, applied in 27 countries.  
* **Each fills the other's gap.** The demonstrator shows where pressure lands today but not how supply responds over time. His state-transition modelling treats training and maintenance as flows that restore capacity. Together they give a starting state and a path.  
* **A use for the Swedish work.** The Sweden layer could supply the human capital starting state for a 2045 production model.

The two models stay separate. A stock-flow tool does not replace the input-output step, and the demonstrator does not need one to report in December.

**Outside reviewer.** Candidates to approach: the MARIO team at Politecnico di Milano, the pymrio maintainers, and economists who have published on capacity and the EU fiscal rules, such as Philipp Heimberger at wiiw or Dezernat Zukunft. None has been contacted.

## **Costs and funding path**

Season 1 costs under EUR 1,000 in cash, including hosting and AI use, and needs no grant. Figures are planning estimates, not quotes.

| Item | Estimate |
| :---- | :---- |
| Data, libraries, repository | EUR 0 |
| Railway hosting, October to December | EUR 30 to 90 |
| Anthropic API use, with a monthly cap | EUR 20 to 60 |
| Outside reviewer fee | EUR 500 to 700 |
| Contingency | EUR 100 |
| Running cost after December, if left online | About EUR 15 to 40 a month |
| Volunteer time, model, data and web app | About 20 to 30 days |
| Volunteer time, checking, Swedish sources and write-up | About 8 to 12 days |

**Funding path after Season 1**

The viability assessment found no funder likely to pay a new, unstaffed association to build this before it has a published proof and a first set of accounts. The realistic order is:

1. **December 2026\.** Publish the proof, whichever way it falls.  
2. **Early 2027\.** Close first-year accounts and the activity report, which most funders ask for.  
3. **5 March 2027\.** Consider an [Erasmus+ small-scale partnership](https://erasmus-plus.ec.europa.eu/programme-guide/part-b/key-action-2/small-scale-partnerships): EUR 30,000 or 60,000 for two organisations in two countries. It funds adult education, so the proof would be the teaching material. A Swedish partner would fit the two-country rule.  
4. **Later in 2027\.** Approach new-economy foundations for a pilot, with a university partner as lead applicant where a scheme requires one.

**The Swedish application**

The application of about SEK 500,000 for a human-centred production model for 2045 is led by a researcher outside MML EU. The Swedish funders checked pay through a Swedish host organisation, so MML EU's possible roles are:

* a named collaborator with a letter of support;  
* a subcontractor delivering the Sweden layer as a defined piece of work;  
* no formal role, with results shared openly.

Which call it targets and who the host is are not yet known. Stephen Hinton has discussed it with the researcher and is the route to find out.

## **Risks and limits**

The two largest risks are claiming more than the method can show and being dismissed as advocacy. Both are handled by choices made before the first run.

| Risk | Why it matters | Mitigation |
| :---- | :---- | :---- |
| Read as an inflation forecast or a fiscal space claim | The method locates pressure only; eurozone members are currency users | Call it a risk indicator; no deficit term; state limits in the report |
| Seen as built to show room to spend | An MMT-linked association will be assumed to want one answer | Neutral name, open code, outside reviewer, publish results that cut either way |
| Thresholds look arbitrary | Output gap estimates lost credibility the same way | Tie them to each series' own history; show sensitivity; invite challenge |
| Claiming novelty that others contradict | Germany's QuBe project already scored the 2025 investment package for occupational bottlenecks ([BMAS FB 683](https://www.bmas.de/DE/Service/Publikationen/Forschungsberichte/fb683-szenario-zu-den-auswirkungen-der-grundgesetzaenderungen.html)) | Claim only an open, comparable, cross-country method; read the German report first |
| The composition table drives the result | It is built by hand | Publish it with sources; reviewer signs it off before results |
| Data revisions change ratings | FIGARO revises its whole series each year | The robustness test is part of the result |
| Sweden has no test case | No Swedish programme with documented bottlenecks was found | Present Sweden as a demonstration, not a validation |
| Volunteer capacity | About 13 volunteers and no staff | One-off scope; stopping rule; a small app that can be switched off after the season |
| A stylised shock is ignored | No real programme means no news hook | Benchmark against French and Irish official figures; offer the method for real programmes later |

## **Open questions and next 30 days**

**Open questions**

* ☐ Will Stephen Hinton lead, and does he want the Sweden layer tied to the 2045 application?  
* ☐ Which call does the Swedish application target, and who is the host?  
* ☐ Who holds the Göttingen link, Johannes Borgström or Dirk Ehnts, and would the university review the method?  
* ☐ Who outside the MMT community will review, and will they be named?  
* ☐ Will the association commit in advance to publishing the result whichever way it falls?  
* ☐ Which name is used?  
* ☐ Do the stopping rule and the rating thresholds stand as proposed?

**Week of 12 October**

* ☐ Present the objective at the General Meeting on 13 October.  
* ☐ Send this specification to Stephen Hinton with an invitation to lead.  
* ☐ Ask the Research WG to nominate a method checker.

**By 30 October**

* ☐ Create the repository and the Railway project, and save every data source with date and checksum.  
* ☐ Confirm the three data checks in stage 2 of the work plan.  
* ☐ Draft the composition table with sources.  
* ☐ Approach two reviewer candidates.  
* ☐ Read the German QuBe report (BMAS FB 683\) in full.

**By 9 November**

* ☐ Agree the composition table with the reviewer.  
* ☐ First EU-wide run on the 2026 FIGARO edition.

## **Sources**

The viability assessment of 9 October 2026 ("EU real resource scoring viability") holds the full evidence, including 25 items that were not verified. The pages below were opened for this specification or for that assessment.

* [Eurostat, FIGARO metadata](https://ec.europa.eu/eurostat/cache/metadata/en/naio_10_fcp_esms.htm) (editions, coverage, revisions, accuracy statement)  
* [Eurostat, employment by 64 industries](https://db.nomics.world/Eurostat/nama_10_a64_e?tab=table)  
* [DG ECFIN, business and consumer survey methodology](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/overarching-methodological-concepts_en) and [sector data](https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/download-business-and-consumer-survey-data/subsector-data_en)  
* [Eurostat, job vacancy statistics metadata](https://ec.europa.eu/eurostat/cache/metadata/en/jvs_esms.htm)  
* [European Labour Authority, labour shortages report 2025](https://www.ela.europa.eu/sites/default/files/2026-06/labour-shortages-report-ela-2025.pdf)  
* [Statistics Sweden, occupational register tables](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__AM__AM0208__AM0208E/)  
* [Swedish Public Employment Service, occupational forecasts](https://jobtechdev.se/en/components/yrkesprognoser?q=Dataset)  
* [National Institute of Economic Research, business survey database](https://statistik.konj.se/PxWeb/pxweb/sv/KonjBar/KonjBar__ftgkvartal/Bartotq.px)  
* [Riksbank, new indicators of resource utilisation](https://www.riksbank.se/globalassets/media/rapporter/ekonomiska-kommentarer/svenska/2023/nya-indikatorer-pa-resursutnyttjandet.pdf)  
* [Irish Fiscal Advisory Council, Ireland's infrastructure demands](https://fiscalcouncil.ie/wp-content/uploads/2024/10/Irelands-Infrastructure-Demands.pdf)  
* [France Stratégie and Dares estimate, reported by XPair](https://conseils.xpair.com/actualite_experts/renovation-energetique-batiments-besoins-main-oeuvre-2030.htm)  
* [BMAS research report FB 683, QuBe scenarios](https://www.bmas.de/DE/Service/Publikationen/Forschungsberichte/fb683-szenario-zu-den-auswirkungen-der-grundgesetzaenderungen.html) (summary page only)   
* [Erasmus+ programme guide, small-scale partnerships](https://erasmus-plus.ec.europa.eu/programme-guide/part-b/key-action-2/small-scale-partnerships)  
* [pymrio](https://pypi.org/project/pymrio/) and [MARIO](https://mario-suite.readthedocs.io/en/latest/)  
* Stephen Hinton, [Modelling Real Capital with system dynamics](https://www.patreon.com/StephenHinton/posts/modelling-real-171738423), read from the shared copy  
* Real Resource Scoring for US Legislation, 2 October 2026 (the US specification)