# Mapping to the Real Capital Canonical Data Model, baseline v1.6.2

Draft for Stephen Hinton, 29 October 2026.

This project writes its results into seven tables of the frozen baseline (`docs/cdm-v1.6.2-baseline.md`), using the baseline's exact field names. `engine/cdm.py` produces them for every run, and a test checks the field names against the baseline document. Where the baseline has no place for something the project produces, nothing is squeezed into another field. The project's own results tables stay the system of record, and each gap is raised below as a Baseline Change Request.

## Mapping

| Baseline table | Rows | How the fields are filled |
| :--- | :--- | :--- |
| Region | One per member state | `region_name` from Eurostat's FIGARO description workbook. `region_type` is empty: the enum has no NUTS0 (CR-4). Population, area and boundary are not produced. |
| AssetPortfolio | One per member state | `asset_type` Built; `asset_subtype` Residential_Building_Stock; `official_name` "<Country> residential building stock"; `steward_organization` "to be confirmed"; `region_id` the member state's Region row. `current_maturity_level` and `criticality_score` are **not produced by this project and stay empty**. |
| AssetManagementObjective | One per member state and run | `required_service_output` "Housing and energy renovation programme, standard shock". `required_human_capital` is text giving the extra persons employed in the EU and the run id. Other fields are empty. |
| LifecycleActivity | One per member state and run | `activity_type` ENH; `intervention_intent` Expand_Capacity; `target_entity_type` Performance; `activity_description` names the shock size, GDP year, composition, FIGARO edition, reference year and run id. Other fields are empty (see CR-5). |
| EconomicActivity | One per FIGARO industry, 64 rows | `nace_code` as in Eurostat national accounts (for example C10-C12); `nace_label` and `nace_section` from Eurostat's code list; `nace_division` the division, or the range for aggregates (CR-7). |
| RealResourceConstraint | One per member state and industry per run | `resource_type` Human_Labor_Skill; `resource_name` the industry's NACE label; `available_quantity` current persons employed; `unit_of_measure` PERSONS; `replenishment_rate` empty, because training capacity is unknown to this project; `is_binding_constraint` true when the rating is binding, false when clear or tight, empty when unrated. |
| UnitOfMeasure | PERSONS only | The baseline's existing row. |

Identifiers are deterministic UUIDs derived from the run id, so a run written twice gives the same rows.

**Linking constraints to activities.** Each RealResourceConstraint row is linked to the LifecycleActivity of the member state where the industry sits. Under the default "simultaneous" application, programmes in other member states also press on that industry, and one link cannot say so (CR-8).

## Baseline Change Requests

Proposed by the Capacity Check Europe project. Until they are accepted, the project's own results tables hold this information.

### CR-1: `required_quantity` on RealResourceConstraint

**Gap.** The baseline records the available quantity of a resource but not the quantity the activity requires, so a constraint cannot be assessed from the table.

**Proposal.** Add `required_quantity` (Decimal), in the same `unit_of_measure` as `available_quantity`. For this project it holds the extra persons employed that the shock requires in that industry.

### CR-2: `assessment_category` on RealResourceConstraint

**Gap.** `is_binding_constraint` is a boolean. The project's rating has four values (clear, tight, binding, no rating), and "no rating" must stay distinct from "not binding".

**Proposal.** Add `assessment_category` (Enum: Clear, Tight, Binding, Not_Rated) and `assessment_method` (String, naming the rule and thresholds). Keep `is_binding_constraint` derived from it.

### CR-3: `availability_basis` on RealResourceConstraint

**Gap.** Nothing says what kind of evidence the availability judgement rests on. Here it is a survey share of firms reporting labour shortages, which is a proxy, not a measure of spare capacity.

**Proposal.** Add `availability_basis` (Enum: Measured_Spare_Capacity, Survey_Proxy, Vacancy_Rate, Administrative_Register, Expert_Judgement) and `availability_source` (String).

### CR-4: NUTS0 in `Region.region_type`

**Gap.** The enum is NUTS1, NUTS2, NUTS3, Biogeographical and Administrative. Member states are NUTS0, so the project leaves `region_type` empty rather than misclassify them.

**Proposal.** Add NUTS0 to the enum.

### CR-5: Performance target without a performance record

**Gap.** Section 1.2 requires `linked_performance_record_id` whenever `target_entity_type` is Performance or Both. The project's activity is a programme that expands capacity. It has no measured service gap, so there is no AssetPerformanceRecord to link to. Following the project brief, the rows say Performance and leave the link empty, which breaks the constraint.

**Proposal.** Either add a `Capacity` value to `target_entity_type` for activities assessed by their resource needs rather than against a performance or maturity target, or relax the constraint for planned programmes.

### CR-6: Hours worked as a unit

**Gap.** UnitOfMeasure has PERSONS but no unit for hours worked, which the project also estimates.

**Proposal.** Add `HOURS_WORKED` (hours, Resource), and optionally `FTE`.

### CR-7: Aggregated NACE industries in EconomicActivity

**Gap.** `nace_division` holds one two-digit division. Eurostat's 64-industry level combines several divisions in some industries, for example C10-C12. The project writes the range (10-12) in the field.

**Proposal.** Allow a range in `nace_division`, or add `nace_level` (Enum: Section, A64, Division, Group) so aggregates are explicit.

### CR-8: Several activities pressing on one constraint

**Gap.** RealResourceConstraint links to one LifecycleActivity. When several programmes draw on the same industry, as when every member state runs the shock at once, the pressure on one constraint comes from many activities.

**Proposal.** Add a link table, for example ConstraintDemand (constraint_id, activity_id, required_quantity), so each activity's share of the requirement can be recorded.

### CR-9: Link from a constraint to its economic activity

**Gap.** RealResourceConstraint names the resource by text (`resource_name`) and cannot point to the EconomicActivity whose workforce it describes. So the two tables this project fills cannot be joined.

**Proposal.** Add `economic_activity_id` (UUID, FK to EconomicActivity.activity_id) to RealResourceConstraint.
