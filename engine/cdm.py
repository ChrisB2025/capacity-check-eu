"""Writers for the Real Capital Canonical Data Model baseline v1.6.2.

Produces the seven baseline tables this project populates, with the
baseline's exact field names and nothing else: Region, AssetPortfolio,
AssetManagementObjective, LifecycleActivity, EconomicActivity,
RealResourceConstraint and UnitOfMeasure.

Where the baseline has no field for something the project produces (the
required quantity, the three-band rating, the basis of the availability
figure), nothing is squeezed into another field: those stay in the project's
own results tables, and change requests are recorded in docs/cdm-mapping.md.
Fields this project does not produce are left empty (None).

Identifiers are deterministic UUIDs derived from the run id, so writing the
same run twice gives the same rows.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd

from engine import concordance
from engine.rating import BINDING, NO_RATING
from engine.sources._common import RAW_DIR

NAMESPACE = uuid.UUID("8f0d3c1e-6f1b-4c0e-9a59-3c3a1d2b7e10")  # project constant

# fmt: off
FIELDS = {
    "Region": ["region_id", "region_name", "region_type", "population", "area_km2",
               "geographic_boundary"],
    "AssetPortfolio": ["asset_id", "asset_type", "asset_subtype", "official_name",
                       "steward_organization", "linked_property_id", "region_id",
                       "geographic_scope", "current_maturity_level",
                       "criticality_score", "in_service_date", "modified_date"],
    "AssetManagementObjective": ["objective_id", "linked_asset_id",
                                 "required_service_output",
                                 "required_service_output_natural_units",
                                 "target_maturity_level", "target_date",
                                 "required_human_capital", "required_natural_capital",
                                 "within_planetary_boundaries",
                                 "resource_constraint_risk"],
    "LifecycleActivity": ["activity_id", "asset_id", "activity_type",
                          "intervention_intent", "target_entity_type",
                          "activity_description", "required_maturity",
                          "linked_performance_record_id", "target_performance_value",
                          "performance_target_unit", "scheduled_start",
                          "scheduled_end"],
    "EconomicActivity": ["activity_id", "nace_code", "nace_label", "nace_section",
                         "nace_division", "activity_description"],
    "RealResourceConstraint": ["constraint_id", "linked_activity_id", "resource_type",
                               "resource_name", "available_quantity",
                               "unit_of_measure", "replenishment_rate",
                               "ecological_threshold", "is_binding_constraint"],
    "UnitOfMeasure": ["unit_code", "unit_name", "dimension"],
}
# fmt: on


def _id(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, "/".join(parts)))


def country_names() -> dict[str, str]:
    """EU27 country names from Eurostat's FIGARO description workbook."""
    hits = sorted(RAW_DIR.glob("figaro-description_*.xlsx"))
    if not hits:
        raise FileNotFoundError("FIGARO description workbook not imported")
    sheet = pd.read_excel(
        Path(hits[-1]), sheet_name="Geographical areas", header=None, engine="calamine"
    )
    names = {}
    for code, label in zip(sheet[1], sheet[2], strict=True):
        if isinstance(code, str) and len(code) == 2 and isinstance(label, str):
            names[code] = label
    return names


def economic_activity() -> pd.DataFrame:
    """One row per FIGARO industry; independent of any run."""
    a64 = concordance.load()
    rows = []
    for r in a64.itertuples():
        divs = r.nace_divisions.split()
        rows.append(
            {
                "activity_id": _id("EconomicActivity", r.figaro_code),
                "nace_code": r.nama_code,
                "nace_label": r.label,
                "nace_section": f"{r.nace_section}, {r.section_label}",
                # The baseline expects one 2-digit division; aggregates of the
                # 64-industry level give the range (change request CR-7).
                "nace_division": divs[0] if len(divs) == 1 else f"{divs[0]}-{divs[-1]}",
                "activity_description": r.label,
            }
        )
    return pd.DataFrame(rows, columns=FIELDS["EconomicActivity"])


def write(result) -> dict[str, pd.DataFrame]:
    """The baseline tables for one run (a ``pipeline.Result``)."""
    rid = result.run_id
    p = result.params
    names = country_names()
    created = result.manifest["created"]
    countries = result.tables["countries"].set_index("country")
    lines = result.tables["lines"]

    region, asset, objective, activity = [], [], [], []
    for c in p.countries:
        region_id = _id("Region", c)
        asset_id = _id("AssetPortfolio", c)
        activity_id = _id("LifecycleActivity", rid, c)
        persons = countries.at[c, "extra_persons_eu"]
        region.append(
            {
                "region_id": region_id,
                "region_name": names.get(c, c),
                "region_type": None,  # NUTS0 is not in the enum (CR-4)
                "population": None,
                "area_km2": None,
                "geographic_boundary": None,
            }
        )
        asset.append(
            {
                "asset_id": asset_id,
                "asset_type": "Built",
                "asset_subtype": "Residential_Building_Stock",
                "official_name": f"{names.get(c, c)} residential building stock",
                "steward_organization": "to be confirmed",
                "linked_property_id": None,
                "region_id": region_id,
                "geographic_scope": None,
                "current_maturity_level": None,  # not produced by this project
                "criticality_score": None,  # not produced by this project
                "in_service_date": None,
                "modified_date": created,
            }
        )
        objective.append(
            {
                "objective_id": _id("AssetManagementObjective", rid, c),
                "linked_asset_id": asset_id,
                "required_service_output": (
                    "Housing and energy renovation programme, standard shock"
                ),
                "required_service_output_natural_units": None,
                "target_maturity_level": None,
                "target_date": None,
                "required_human_capital": (
                    f"{persons:,.0f} extra persons employed in the EU in one year "
                    f"(run {rid})"
                ),
                "required_natural_capital": None,
                "within_planetary_boundaries": None,
                "resource_constraint_risk": None,
            }
        )
        activity.append(
            {
                "activity_id": activity_id,
                "asset_id": asset_id,
                "activity_type": "ENH",
                "intervention_intent": "Expand_Capacity",
                # Performance as the brief specifies; the baseline then expects a
                # linked performance record, which this project has not (CR-5).
                "target_entity_type": "Performance",
                "activity_description": (
                    f"Additional public spending of {p.shock_pct:g}% of "
                    f"{p.gdp_year} GDP in one year on housing and energy "
                    f"renovation, composition '{p.composition}'; FIGARO "
                    f"{p.edition} edition, reference year {p.ref_year}; run {rid}"
                ),
                "required_maturity": None,
                "linked_performance_record_id": None,
                "target_performance_value": None,
                "performance_target_unit": None,
                "scheduled_start": None,
                "scheduled_end": None,
            }
        )

    a64 = concordance.load().set_index("figaro_code")
    constraint = []
    for r in lines.itertuples():
        constraint.append(
            {
                "constraint_id": _id(
                    "RealResourceConstraint", rid, r.economy, r.industry
                ),
                # Linked to the programme of the member state where the industry
                # sits; under simultaneous application other programmes add to
                # the same pressure (see docs/cdm-mapping.md).
                "linked_activity_id": _id("LifecycleActivity", rid, r.economy),
                "resource_type": "Human_Labor_Skill",
                "resource_name": a64.at[r.industry, "label"],
                "available_quantity": r.persons_employment,
                "unit_of_measure": "PERSONS",
                "replenishment_rate": None,  # training capacity unknown
                "ecological_threshold": None,
                "is_binding_constraint": (
                    None if r.rating == NO_RATING else r.rating == BINDING
                ),
            }
        )

    units = [{"unit_code": "PERSONS", "unit_name": "persons", "dimension": "Resource"}]
    out = {
        "Region": pd.DataFrame(region),
        "AssetPortfolio": pd.DataFrame(asset),
        "AssetManagementObjective": pd.DataFrame(objective),
        "LifecycleActivity": pd.DataFrame(activity),
        "EconomicActivity": economic_activity(),
        "RealResourceConstraint": pd.DataFrame(constraint),
        "UnitOfMeasure": pd.DataFrame(units),
    }
    for name, df in out.items():
        out[name] = df.reindex(columns=FIELDS[name])
    return out
