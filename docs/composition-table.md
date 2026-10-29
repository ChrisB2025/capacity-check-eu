# Composition table

Draft for the outside reviewer, 29 October 2026. **Status: proposed.** No results have been run with any of these compositions. The engine refuses to run one until its status is set to confirmed, which Chris does after the reviewer has seen this table.

## What the table does

The standard shock is public spending equal to 1% of a member state's 2024 GDP on housing and energy renovation. The composition table splits that spending across the products bought directly. The same split is used in every member state.

**The split is final demand by product, in input-output terms.** FIGARO's tables are industry by industry, so each purchase is assigned to the industry with the same two-digit code. The supply chain of each industry is then added by the Leontief inverse. This has one consequence that drives the whole table:

> Construction (F) in FIGARO already buys its own materials through its supply chain. If insulation is bought from a contractor at its full installed price and assigned to F, the insulation material is counted inside F's inputs. Listing the material again as a separate purchase would count it twice.

So a product is listed separately only when it is bought separately from the installer's price, or when the construction industry's average supply chain would not contain it. Heat pumps are the clearest case of the second: the average purchases of the construction industry contain little machinery.

Each composition is a file in `engine/compositions/`. The codes are FIGARO industry codes.

## Sources

All were opened on 29 October 2026. The quotations below were checked against the documents.

| Key | Source | What it gives |
| :--- | :--- | :--- |
| Q2013 | Quirion, P. (2013), *L'effet net sur l'emploi de la transition énergétique en France: une analyse input-output du scénario négaWatt*, CIRED Working Paper 46-2013, Table A.1, p. 38. https://negawatt.org/IMG/pdf/etude_p.quirion_emplois_et_scenario_negawatt_28-03-2013.pdf | An input-output allocation of deep residential renovation, 450 €/m², France, 2011 prices: "Dont isolation 315 €/m²" to building construction (H01); "Dont équipements chauffage ventilation 53 €/m²" and "Dont installation chauffage ventilation 45 €/m²" to mechanical equipment (E22); "Dont distribution chauffage ventilation 37 €/m²" to trade (J30). Source given: "Calculs d'après Enertech (2010) et Ademe (2012)". VAT basis not stated. |
| KFW2016 | Diefenbach, N. et al., IWU and Fraunhofer IFAM (2016), *Monitoring der KfW-Programme "Energieeffizient Sanieren" und "Energieeffizient Bauen" 2015*, section I.6.1, p. 54, and Anlage 5, p. 5-1. https://www.iwu.de/fileadmin/publikationen/gebaeudebestand/kfw/KfW_Monitoringbericht_fuer_2015.pdf | Retrofit spending split "im Verhältnis 0/80/20, weil hier die Hoch- und Tiefbauarbeiten keine Rolle spielen": 80% installation and finishing trades (Ausbaugewerbe), 20% planning and site supervision. Gross, including VAT. Germany, 2015. |
| CE2015 | Cambridge Econometrics et al. (2015), *Assessing the Employment and Social Impact of Energy Efficiency*, final report for DG ENER, Table 4.2, p. 59. https://circabc.europa.eu/rest/download/4ba02aea-682c-4872-ab92-2d0284786e91 | The GEM-E3 model's split of energy efficiency spending by producing sector, per cent: ferrous metals 4, non-ferrous metals 4, chemical products 7, non-metallic minerals 8, electric goods 2, construction 60, market services 15. "Sources: E3M Lab estimations." EU28, all energy efficiency projects, not only housing. |
| DEA2026 | Danish Energy Agency (2026), *Technology Data: Heating installations*, version 0007, p. 76. https://ens.dk/media/8516/download | "Typically, about 30% of the total price of a heat pump is soft cost (installation, sales and marketing, customer support and service, administration etc.) and about 70% is equipment costs. In this equation, installation accessories are considered as equipment costs." Denmark, existing single-family houses, excluding VAT. |
| ADEME2018 | ADEME et al., *Rénovation énergétique des logements: étude des prix*, synthesis report, Tableau 6, p. 19. https://www.precarite-energie.org/wp-content/uploads/2019/11/renovation-energetique-logements-etude-prix-2019.pdf | Labour share of the price of loft insulation ("combles perdues"), 200 observations: lower quartile 0.14, median 0.29, upper quartile 0.51. Excluding VAT ("Tous les prix s'entendent en hors taxe"). France, 2017 to 2018. |
| BEIS2018 | Delta-ee for BEIS (2018), *Cost of installing heating measures in domestic properties*, Table 5, p. 7. https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/913508/cost-of-installing-heating-measures-in-domestic-properties.pdf | "8kW air source heat pump (ASHP) fully installed including fittings, buffer tank, cylinder and controls, excluding the heat distribution system £8,750", excluding VAT. UK. |

ADEME2018 and BEIS2018 are supporting evidence. They are not used to set any share.

No European source was found that splits a whole deep renovation into envelope, heating and fees at once. The fee evidence is German only. Gaps are listed at the end.

## Standard composition

The standard combines the only source that allocates residential renovation to products for an input-output model (Q2013) with the only source for design and supervision fees in a retrofit programme (KFW2016). Q2013 has no fee line.

1. Design, planning and site supervision (M71): 20% (KFW2016).
2. The remaining 80% follows Q2013's 450 €/m²:
   - **Insulation work, 315, and heating installation, 45, to construction (F).** Installation is labour by a contractor, which this project assigns to F. Q2013 assigns it to mechanical equipment.
   - **Heating and ventilation equipment, 53, to machinery (C28).**
   - **Distribution, 37, to wholesale trade (G46).** This is the trade margin on the equipment.

| Code | Product | Share | Arithmetic |
| :--- | :--- | ---: | :--- |
| F | Construction work, including insulation and heating installation | 0.640000 | 0.8 × (315 + 45) / 450 |
| C28 | Heating and ventilation equipment | 0.094222 | 0.8 × 53 / 450 |
| G46 | Distribution margin on heating equipment | 0.065778 | 0.8 × 37 / 450 |
| M71 | Design, planning and site supervision | 0.200000 | KFW2016 |
| | **Total** | **1.000000** | |

**Building materials and components have no separate line** in the standard. Insulation is bought as installed work, so its materials enter through construction's supply chain. Q2013 assigns insulation entirely to building construction, and KFW2016 notes that the finishing trades buy proportionally more material ("im Ausbaugewerbe anteilig mehr Material bezogen wird"). Alternative B tests the opposite assumption.

## Alternatives for the sensitivity test

**A. Contractor-led (`alt_contractor`).** KFW2016 as it stands: construction 0.80, design and supervision 0.20. All materials and equipment are bought by the contractors, so heat pumps enter only through construction's average supply chain. This is the lower bound for demand on manufacturing.

| Code | Share |
| :--- | ---: |
| F | 0.80 |
| M71 | 0.20 |

**B. Materials bought directly (`alt_materials`).** CE2015's GEM-E3 split, mapped to FIGARO codes. Chemical products are mapped to rubber and plastics (C22), on the assumption that foam insulation is the relevant chemical product. Ferrous and non-ferrous metals are combined in basic metals (C24). Market services are mapped to design and engineering (M71). This is the upper bound for demand on materials. It covers all energy efficiency projects, not only housing, and it double counts to the extent that the construction share also buys materials.

| Code | Share |
| :--- | ---: |
| F | 0.60 |
| C23 | 0.08 |
| C22 | 0.07 |
| C24 | 0.08 |
| C27 | 0.02 |
| M71 | 0.15 |

**C. Heating replacement (`alt_heating`).** A programme of heat pump installations without envelope work, split by DEA2026: equipment 0.70 to machinery (C28), soft cost 0.30 to construction (F). DEA2026's soft cost includes sales and administration, which are assigned here to F with the installation. This tests a different kind of programme rather than a different estimate of the same one.

| Code | Share |
| :--- | ---: |
| C28 | 0.70 |
| F | 0.30 |

## Questions for the reviewer

1. **Double counting.** Is the principle above right: list a product separately only when it is bought separately from the installer, or when construction's average supply chain lacks it?
2. **The fee share.** KFW2016's 20% for planning and site supervision is a programme assumption, derived from stimulus spending data, and includes VAT. Is it representative of a large public renovation programme, or too high for staged renovations with little design work?
3. **Trade margins.** Should the distribution margin on equipment be kept as a separate purchase from wholesale trade (G46), as in the standard, or folded into the equipment line?
4. **Age and place of the evidence.** The standard rests on French 2011 prices and a German 2015 assumption. Is there a more recent or more European allocation we have missed?
5. **VAT.** KFW2016 includes VAT; ADEME2018, BEIS2018 and DEA2026 exclude it; Q2013 and CE2015 do not say. The shock is a spending total, and VAT is returned to the government, not paid to an industry. Should the shock be reduced by VAT before it is split? This is the same question as the basic and purchasers' prices question in the method note.

## Gaps in the evidence

- No European source splits a whole deep renovation into envelope, heating and fees at once.
- The heat pump evidence is from the UK, Denmark and France only. Labour shares differ widely between them, partly because Denmark counts sales and administration as soft cost.
- No EU-wide statistic on design and supervision fees in renovation was found.
- No recent EU allocation of residential retrofit spending to products exists in the sources found. Q2013 has no fee line; KFW2016 puts all materials inside construction; CE2015 has no machinery line and is not housing-specific.

## Confirming a composition

After the reviewer has commented, Chris edits the composition file and sets `status: confirmed`, `confirmed_by` and `confirmed_on`, adjusting shares if the review calls for it. The commit records the change, and the run manifest records the composition file's checksum.
