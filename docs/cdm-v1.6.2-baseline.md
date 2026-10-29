# CDM v1.6.2 Baseline A+B+F

## Baseline Specification Document (Patched)

Author: Stephen Hinton
Project: MMLAB Europe
Status: Frozen Baseline (Analytically Complete and Audited)
Date: 2026-10-27
Based on Canonical Version: Real Capital Canonical Data Model v1.6
Scope: Core CDM + Module A (MMT) + Module B (Translation Layer) + Module F (Territorial Resilience) + AssetPressure Extension.
Source: https://docs.google.com/document/d/1x2gTUbIbQ_oQzMVxe-HlcNY59TbBD74TQMyyL4tt0Ug/edit (copied to markdown 2026-10-29; the Google Doc is the master)

Version Note: This document (v1.6.2) incorporates the three patches required to close the Maturity-Performance analytical gap identified during project scoping: the addition of target_entity_type, linked_performance_record_id, and the target performance metrics to LifecycleActivity. It is the definitive, structurally and analytically sound specification for the project.

---

## 1. Scope Statement and Analytical Clarifications

This document specifies a frozen baseline of the Real Capital Canonical Data Model (CDM) for use in MMLAB Europe.

### 1.1 The Maturity-Performance Distinction (New in v1.6.2)

The baseline explicitly recognizes that an asset can have a high maturity (good physical capability) but poor performance (failing to deliver the required service). The model now provides parallel analytical chains for both:

1. Maturity Closure Chain: target_maturity_level → current_maturity_level → LifecycleActivity (where target_entity_type = 'Maturity') → allocation_id.
2. Performance Closure Chain: performance_gap → AssetPerformanceRecord → LifecycleActivity (where target_entity_type = 'Performance') → allocation_id.

### 1.2 Logical Constraints (To be enforced at the application layer)

1. Maturity Target Constraint: For target_entity_type = 'Maturity' or 'Both', required_maturity must be <= the target_maturity_level of the linked AssetManagementObjective.
2. Performance Target Constraint: For target_entity_type = 'Performance' or 'Both', linked_performance_record_id must not be NULL, and target_performance_value must be a valid number in the specified performance_target_unit.

### 1.3 Glossary Clarification: Pressure vs. Risk

- AssetPressure defines an ongoing process (e.g., "Nutrient runoff"). It is a continuous driver.
- AssetRisk defines a potential event (e.g., "Algal bloom"). It is a discrete threat.

---

## 2. Data Dictionary: Core CDM

### 2.1 AssetPortfolio

(Unchanged from v1.6.1)

| Attribute Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| asset_id | UUID | Primary Key. | a0eebc99... |
| asset_type | Enum | [Natural, Built, Social, Human] | Built |
| asset_subtype | String | Further classification. | Public_Office_Building |
| official_name | String | Formal designation. | HQ Building A |
| steward_organization | String | Accountable entity. | Swedish Property Agency |
| linked_property_id | UUID (FK) | Links to RealEstate.property_id. | PROP-SE-001 |
| region_id | UUID (FK) | Links to Region.region_id. | SE-NUTS-SE04 |
| geographic_scope | GeoJSON | Physical boundary. | { "type": "Polygon", ... } |
| current_maturity_level | Integer (1-5) | Current capability. | 3 |
| criticality_score | Decimal (0.0-10.0) | Importance to national objectives. | 8.7 |
| in_service_date | ISO 8601 Date | When operational. | 1995-06-01 |
| modified_date | ISO 8601 Timestamp | Last update. | 2023-11-27T14:30:00Z |

### 2.2 NaturalCapital_Attributes

(Unchanged from v1.6.1)

| Attribute | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| resource_category | Enum | [Lithospheric, Hydrospheric, Atmospheric, Biotic] | Hydrospheric |
| renewability_rate | String | Renewal class. | Slow_Renewal |
| carrying_capacity | Float | Sustainable yield limit. | 15.5 |
| extraction_limit | Float | Mandatory cap. | 12.0 |
| baseline_condition_year | Integer | Reference year. | 1950 |
| eu_art17_status | Enum | Original Art.17 status. | FV |
| eu_nrr_condition | Enum | Original NRR condition. | Good |
| source_authority | String | Assessment authority. | EU_Art17 |
| translation_confidence | Enum | Confidence in mapping. | High |

### 2.3 BuiltCapital_Attributes

(Unchanged from v1.6.1)

| Attribute | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| asset_class | String | Functional classification. | Office_Building |
| condition_index | Decimal (0-100) | Physical state. | 68.5 |
| design_capacity | String/Number | Max service output. | 500 (persons) |
| utilization_factor | Decimal | Load vs. capacity. | 0.85 |
| next_major_renewal | ISO 8601 Date | Next refurbishment. | 2030-05-01 |

### 2.4 SocialCapital_Attributes

(Unchanged from v1.6.1)

| Attribute | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| organization_type | Enum | [Governmental, Judicial, Educational, Healthcare, Financial] | Judicial |
| governance_model | String | Governance structure. | Independent |
| institutional_knowledge_index | Decimal (0-10) | Knowledge retention. | 7.2 |
| network_strength | Decimal (0-10) | Collaboration quality. | 6.8 |
| service_coverage_pct | Decimal | Population access. | 92.5 |

### 2.5 HumanCapital_Attributes

(Unchanged from v1.6.1)

| Attribute | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| population_cohort | String | Defined group. | Licensed_Water_Operators |
| avg_capability_level | Decimal (1-5) | Average competency. | 3.8 |
| health_status_index | Decimal (0-100) | Public health metric. | 82.0 |
| knowledge_currency_score | Decimal (0-10) | Training recency. | 5.5 |
| attrition_rate_pct | Decimal | Workforce loss rate. | 4.2 |

### 2.6 AssetManagementObjective

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| objective_id | UUID | Primary Key. | OBJ-001 |
| linked_asset_id | UUID (FK) | Links to AssetPortfolio.asset_id. | SE-DH-001 |
| required_service_output | Text | Service description. | Warm, healthy homes |
| required_service_output_natural_units | Text | Biophysical output. | <= 110 kWh/m2 |
| target_maturity_level | Integer (1-5) | Target maturity. | 3 |
| target_date | ISO 8601 Date | Target achievement date. | 2032-12-31 |
| required_human_capital | Text | Human resource needs. | 15,000 installers |
| required_natural_capital | Text | Material needs. | 1.2M tonnes insulation |
| within_planetary_boundaries | Boolean | Ecological check. | TRUE |
| resource_constraint_risk | Enum | Inflation risk. | Medium |

### 2.7 AssetPerformanceRecord

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| record_id | UUID | Primary Key. | PERF-001 |
| asset_id | UUID (FK) | Links to AssetPortfolio.asset_id. | SE-HOSP-001 |
| service_demand_volume | Decimal | Demand level. | 1500 (patients/day) |
| service_delivered_volume | Decimal | Delivery level. | 1100 (patients/day) |
| performance_gap | Decimal | Demand vs. delivery. | -400 |
| measurement_period | Date Range | Period covered. | 2026-Q1 |

### 2.8 AssetHealthIndicator

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| indicator_id | UUID | Primary Key. | HLTH-001 |
| asset_id | UUID (FK) | Links to AssetPortfolio.asset_id. | SE-HOSP-001 |
| condition_score | Decimal | Assessed condition. | 85 |
| condition_trend | Enum | [Improving, Stable, Declining, Uncertain, Unknown] | Stable |
| degradation_mechanism | String | Cause of degradation. | None; well-maintained |
| assessment_date | Date | Assessment date. | 2026-01-15 |
| assessed_by | String | Assessor. | National Audit Office |

### 2.9 AssetRisk

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| risk_id | UUID | Primary Key. | RISK-001 |
| asset_id | UUID (FK) | Links to AssetPortfolio.asset_id. | SE-HOSP-001 |
| risk_scenario | String | Risk description. | Patient wait times exceed safe limits |
| likelihood | Enum | [Rare, Unlikely, Possible, Likely, Almost_Certain] | Likely |
| consequence | Enum | [Insignificant, Minor, Moderate, Major, Severe] | Major |
| mitigation_activity_id | UUID (FK) | Links to LifecycleActivity.activity_id. | ACT-PERF-001 |

### 2.10 LifecycleActivity (Modified in v1.6.2)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| activity_id | UUID | Primary Key. | ACT-PERF-001 |
| asset_id | UUID (FK) | Links to AssetPortfolio.asset_id. | SE-HOSP-001 |
| activity_type | Enum | [ACQ, CRE, ENH, MNT, RES, OPR, RNW, DEC, RISK, STU] | MNT |
| intervention_intent | Enum | [Remove_Pressure, Restore_Capacity, Restore_Function, Expand_Capacity] | Restore_Function |
| target_entity_type | Enum | NEW: [Maturity, Performance, Both] | Performance |
| activity_description | Text | Description. | Optimize patient triage workflow |
| required_maturity | Integer (1-5) | (Nullable) Target maturity if target_entity_type includes Maturity. | NULL |
| linked_performance_record_id | UUID (FK) | NEW: Links to AssetPerformanceRecord.record_id if targeting Performance. | PERF-001 |
| target_performance_value | Decimal | NEW: The target value for the performance metric. | 1400 |
| performance_target_unit | String (FK) | NEW: Links to UnitOfMeasure.unit_code. | PATIENTS_DAY |
| scheduled_start | Date | Planned start. | 2026-05-01 |
| scheduled_end | Date | Planned end. | 2026-12-31 |

### 2.11 FinancialResourceAllocation

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| allocation_id | UUID | Primary Key. | FRA-002 |
| activity_id | UUID (FK) | Links to LifecycleActivity.activity_id. | ACT-PERF-001 |
| fiscal_instrument | Enum | Funding taxonomy. | DIRECT_SPENDING |
| fiscal_year | Integer | Budget year. | 2026 |
| allocated_amount | Decimal | Amount. | 5000000 |
| net_spending_created | Decimal | Currency injected. | 5000000 |
| tax_offset_applied | Decimal | Currency drained. | 0 |
| inflation_impact_assessment | Text | Price pressure. | Low |
| justification | Text | Policy basis. | Healthcare access improvement |

### 2.12 AssetPressure

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| pressure_id | UUID | Primary Key. | AP-001 |
| asset_id | UUID (FK) | Links to AssetPortfolio.asset_id. | SE-FOREST-01 |
| activity_id | UUID (FK) | Links to EconomicActivity.activity_id. | EA-AGRI-01 |
| pressure_type | Enum | [Nutrient_Runoff, Land_Conversion, Water_Extraction, Pollution, Physical_Disturbance, Climate_Stress] | Nutrient_Runoff |
| pressure_direction | Enum | [Degrading, Restoring, Neutral] | Degrading |
| pressure_intensity | Decimal | Magnitude of pressure per unit. | 0.8 |
| pressure_unit | String (FK) | Links to UnitOfMeasure.unit_code. | KG_N_HA_YEAR |
| pressure_share_pct | Decimal | % of total pressure on asset. | 65.0 |
| attribution_method | Enum | [Direct_Measurement, Model_Based, Expert_Judgement, Proxy] | Model_Based |
| attribution_source | String | Source of attribution. | SLU Water Quality Model |
| attribution_year | Integer | Year of assessment. | 2026 |
| condition_impact | Decimal | Observed impact on condition score. | -0.3 |
| condition_impact_unit | Enum | The unit of the impact. [Maturity_Level, Condition_Index, Biophysical_Measure] | Maturity_Level |
| notes | Text | Caveats. | Exceeds critical load threshold |

### 2.13 AssetMaturityHistory

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| history_id | UUID | Primary Key. | AMH-001 |
| asset_id | UUID (FK) | Links to AssetPortfolio.asset_id. | SE-DH-001 |
| assessment_date | ISO 8601 Date | Date the maturity was assessed. | 2025-12-31 |
| maturity_level | Integer (1-5) | The assessed level at that date. | 1 |
| source_activity_id | UUID (FK) | (Optional) The activity that caused the change. | ACT-001 |
| condition_score | Decimal | (Optional) The associated condition index at that time. | 35 |
| notes | Text | Context for the change. | Baseline assessment |

### 2.14 EconomicActivity (Simplified)

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| activity_id | UUID | Primary Key. | EA-AGRI-01 |
| nace_code | String | NACE Rev. 2 code. | A01 |
| nace_label | String | Official NACE label. | Crop and animal production |
| nace_section | String | NACE section. | A, Agriculture, forestry and fishing |
| nace_division | String | NACE 2-digit division. | 01 |
| activity_description | Text | Detailed description. | Cultivation of cereals, livestock, etc. |

---

## 3. Data Dictionary: Module A (MMT)

### 3.1 RealResourceConstraint

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| constraint_id | UUID | Primary Key. | RRC-001 |
| linked_activity_id | UUID (FK) | Links to the LifecycleActivity requiring this resource. | ACT-001 |
| resource_type | Enum | [Human_Labor_Skill, Natural_Material, Energy, Ecological_Capacity, Built_Capacity, Land_Area] | Human_Labor_Skill |
| resource_name | String | Resource name. | Certified retrofit installers |
| available_quantity | Decimal | Available amount. | 12000 |
| unit_of_measure | String (FK) | Links to UnitOfMeasure.unit_code. | PERSONS |
| replenishment_rate | Decimal | Renewal rate. | 2000 |
| ecological_threshold | Decimal | Hard boundary. | NULL |
| is_binding_constraint | Boolean | Is this limiting? | TRUE |

### 3.2 InflationMonitoring

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| monitoring_id | UUID | Primary Key. | IM-001 |
| period | Date Range | Reporting period. | 2025-Q2 |
| sector | String | Economic sector. | Construction |
| price_index_change | Decimal | Price change. | 4.5 |
| attributed_fiscal_activity | UUID (FK) | Links to LifecycleActivity.activity_id. | ACT-001 |
| corrective_action_taken | Text | Action description. | Increased carbon tax |

---

## 4. Data Dictionary: Module B (Translation)

### 4.1 EnumMapping

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| mapping_id | UUID | Primary Key. | MAP-004 |
| source_authority | String | Authority. | EU_Art17 |
| source_enum_value | String | Enum value. | FV |
| source_enum_label | String | Human-readable label. | Favourable |
| cdm_maturity_level | Integer (1-5) | Translated level. | 5 |
| cdm_trend_default | Enum | Default trend. | Stable |
| translation_confidence | Enum | [High, Medium, Low] | High |
| notes | Text | Rationale. | Best possible status |

### 4.2 ReconciliationRules

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| rule_id | UUID | Primary Key. | REC-001 |
| asset_type | Enum | Capital type. | Natural |
| priority_1 | String | Primary source. | EU_Art17 |
| priority_2 | String | Secondary source. | EU_NRR |
| priority_3 | String | Tertiary source. | Regional_GIS |
| rationale | Text | Reasoning. | Art.17 is most detailed |

---

## 5. Data Dictionary: Module F (Territorial)

### 5.1 RealEstate

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| property_id | UUID | Primary Key. | PROP-SE-001 |
| cadastral_reference | String | Land registry ID. | SE-0123-4567 |
| land_use_category | Enum (NACE) | Designated use. | A01 |
| area_hectares | Decimal | Size. | 150.5 |
| geographic_boundary | GeoJSON | Cadastral polygon. | { "type": "Polygon", ... } |
| owner_entity | String | Legal owner. | State Forest Agency |
| tenure_type | Enum | [Freehold, Leasehold, Customary, Public, Communal] | Public |
| taxable_value | Decimal | Cadastral value. | 12500000 |
| currency_code | String | ISO 4217. | SEK |
| valuation_year | Integer | Valuation year. | 2025 |
| linked_asset_id | UUID (FK) | Links to AssetPortfolio.asset_id. | SE-FOREST-01 |
| region_id | UUID (FK) | Links to Region.region_id. | SE-NUTS-SE04 |

### 5.2 Region

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| region_id | UUID | Primary Key. | SE-NUTS-SE04 |
| region_name | String | Name. | Stockholm County |
| region_type | Enum | [NUTS1, NUTS2, NUTS3, Biogeographical, Administrative] | NUTS3 |
| population | Integer | Population. | 2400000 |
| area_km2 | Decimal | Area. | 6519 |
| geographic_boundary | GeoJSON | Boundary. | { "type": "Polygon", ... } |

### 5.3 LandUseProfile

(Unchanged from v1.6.1)

| Attribute | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| profile_id | UUID | Primary Key. | LUP-SE-04 |
| region_id | UUID (FK) | Links to Region.region_id. | SE-NUTS-SE04 |
| agricultural_land_ha | Decimal | Agricultural land. | 120000 |
| forest_land_ha | Decimal | Forest land. | 380000 |
| built_up_land_ha | Decimal | Built-up land. | 45000 |
| green_space_ha | Decimal | Green space. | 22000 |
| protected_area_ha | Decimal | Protected area. | 18000 |
| assessment_year | Integer | Year. | 2025 |

---

## 6. Reference Tables

### 6.1 MaturityScale

(Unchanged from v1.6.1)

| scale_id | label | description |
| :--- | :--- | :--- |
| 1 | Non-functional | No capability; original standard. |
| 2 | Severely Depleted | Major gaps. |
| 3 | Depleted | Some functions and capacity |
| 4 | Pressured | Pressured but functions and capacity maintained. |
| 5 | Mature | Meeting needs |

### 6.2 UnitOfMeasure (Updated)

| unit_code | unit_name | dimension |
| :--- | :--- | :--- |
| KG_N_HA_YEAR | kg N / ha / year | Pressure |
| TONNES_CO2E | tonnes CO2e | Pressure |
| PERSONS | persons | Resource |
| HECTARES | hectares | Area |
| SEK | Swedish Krona | Currency |
| PATIENTS_DAY | patients / day | Performance |
| VEHICLES_DAY | vehicles / day | Performance |
| MWH_YEAR | MWh / year | Performance |

---

## 7. Baseline Entity-Relationship Diagram

(Not present in the source document.)

---

## 8. Analytical Capabilities Enabled by this Baseline

With the addition of target_entity_type and performance linkage, the baseline now supports a dual-chain analysis.

Query 1: Identify high maturity / low performance assets (The "Sleeping Giants").

```sql
SELECT
    a.asset_id,
    a.official_name,
    a.current_maturity_level,
    ms.label AS maturity_label,
    apr.performance_gap,
    la.activity_description,
    la.target_entity_type,
    la.target_performance_value,
    uom.unit_name AS target_unit
FROM AssetPortfolio a
JOIN MaturityScale ms ON a.current_maturity_level = ms.scale_id
JOIN AssetPerformanceRecord apr ON a.asset_id = apr.asset_id
LEFT JOIN LifecycleActivity la ON a.asset_id = la.asset_id
LEFT JOIN UnitOfMeasure uom ON la.performance_target_unit = uom.unit_code
WHERE a.current_maturity_level >= 4
AND apr.performance_gap < 0;
```

Query 2: Are we funding the right interventions for the right gaps?

```sql
SELECT
    a.official_name,
    (o.target_maturity_level - a.current_maturity_level) AS maturity_gap,
    apr.performance_gap,
    la.activity_description,
    la.target_entity_type,
    fra.allocated_amount
FROM AssetPortfolio a
JOIN AssetManagementObjective o ON a.asset_id = o.linked_asset_id
JOIN AssetPerformanceRecord apr ON a.asset_id = apr.asset_id
JOIN LifecycleActivity la ON a.asset_id = la.asset_id
JOIN FinancialResourceAllocation fra ON la.activity_id = fra.activity_id
WHERE (o.target_maturity_level - a.current_maturity_level) > 0
  AND apr.performance_gap < 0
  AND la.target_entity_type = 'Maturity';
```

(Interpretation: If this query returns results, it means the project is funding maturity improvements on assets that also have performance gaps. If the performance gap is severe, the intervention may need to be re-scoped to Both.)

---

## 9. Governance Record

This baseline is registered in the CDM Version Control Register.

| Version | Status | Date | Contains | Supersedes | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1.6-Baseline | Frozen Baseline | 2026-10-27 | Core + A + B + F + AssetPressure | none | Initial scoped baseline. |
| 1.6.1-Baseline | Patched and Audited | 2026-10-27 | Added Reference Tables, AssetMaturityHistory, FK constraints. | 1.6-Baseline | Structural soundness patched. |
| 1.6.2-Baseline | Analytically Complete | 2026-10-27 | Added performance closure chain (target_entity_type, linked_performance_record_id, target_performance_value). | 1.6.1-Baseline | Final frozen baseline. Closes the maturity/performance analytical gap. Approved for project use. |

### Change Control for the Baseline

- Changes to the baseline do not affect the canonical model.
- If the project requires a field or entity not in this baseline, it must submit a Baseline Change Request.
- When the project completes, any extensions or modifications will be reviewed for inclusion in the next canonical version.
