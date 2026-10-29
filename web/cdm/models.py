"""The seven Real Capital Canonical Data Model v1.6.2 tables this project writes.

Field names and types mirror docs/cdm-v1.6.2-baseline.md exactly. Foreign keys
are kept as plain UUID or code columns with the baseline's names, because a
Django ForeignKey would rename the attribute. Enum fields carry the baseline's
values. Nothing outside the baseline is added here: the required quantity, the
rating and the availability basis live in the project's own tables until the
change requests in docs/cdm-mapping.md are accepted.
"""

from django.db import models

DECIMAL = {"max_digits": 24, "decimal_places": 6, "null": True, "blank": True}


def _enum(*values: str) -> models.CharField:
    return models.CharField(
        max_length=32, choices=[(v, v) for v in values], null=True, blank=True
    )


class Region(models.Model):
    region_id = models.UUIDField(primary_key=True)
    region_name = models.CharField(max_length=200, null=True, blank=True)
    # The baseline enum has no NUTS0 (change request CR-4), so it stays null.
    region_type = _enum("NUTS1", "NUTS2", "NUTS3", "Biogeographical", "Administrative")
    population = models.BigIntegerField(null=True, blank=True)
    area_km2 = models.DecimalField(**DECIMAL)
    geographic_boundary = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "Region"


class AssetPortfolio(models.Model):
    asset_id = models.UUIDField(primary_key=True)
    asset_type = _enum("Natural", "Built", "Social", "Human")
    asset_subtype = models.CharField(max_length=200, null=True, blank=True)
    official_name = models.CharField(max_length=300, null=True, blank=True)
    steward_organization = models.CharField(max_length=300, null=True, blank=True)
    linked_property_id = models.UUIDField(null=True, blank=True)
    region_id = models.UUIDField(null=True, blank=True)
    geographic_scope = models.JSONField(null=True, blank=True)
    current_maturity_level = models.IntegerField(null=True, blank=True)
    criticality_score = models.DecimalField(**DECIMAL)
    in_service_date = models.DateField(null=True, blank=True)
    modified_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "AssetPortfolio"


class AssetManagementObjective(models.Model):
    objective_id = models.UUIDField(primary_key=True)
    linked_asset_id = models.UUIDField(null=True, blank=True)
    required_service_output = models.TextField(null=True, blank=True)
    required_service_output_natural_units = models.TextField(null=True, blank=True)
    target_maturity_level = models.IntegerField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    required_human_capital = models.TextField(null=True, blank=True)
    required_natural_capital = models.TextField(null=True, blank=True)
    within_planetary_boundaries = models.BooleanField(null=True, blank=True)
    resource_constraint_risk = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        db_table = "AssetManagementObjective"


class LifecycleActivity(models.Model):
    activity_id = models.UUIDField(primary_key=True)
    asset_id = models.UUIDField(null=True, blank=True)
    activity_type = _enum(
        "ACQ", "CRE", "ENH", "MNT", "RES", "OPR", "RNW", "DEC", "RISK", "STU"
    )
    intervention_intent = _enum(
        "Remove_Pressure", "Restore_Capacity", "Restore_Function", "Expand_Capacity"
    )
    target_entity_type = _enum("Maturity", "Performance", "Both")
    activity_description = models.TextField(null=True, blank=True)
    required_maturity = models.IntegerField(null=True, blank=True)
    linked_performance_record_id = models.UUIDField(null=True, blank=True)
    target_performance_value = models.DecimalField(**DECIMAL)
    performance_target_unit = models.CharField(max_length=32, null=True, blank=True)
    scheduled_start = models.DateField(null=True, blank=True)
    scheduled_end = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "LifecycleActivity"


class EconomicActivity(models.Model):
    activity_id = models.UUIDField(primary_key=True)
    nace_code = models.CharField(max_length=32, null=True, blank=True)
    nace_label = models.CharField(max_length=300, null=True, blank=True)
    nace_section = models.CharField(max_length=300, null=True, blank=True)
    nace_division = models.CharField(max_length=32, null=True, blank=True)
    activity_description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "EconomicActivity"


class RealResourceConstraint(models.Model):
    constraint_id = models.UUIDField(primary_key=True)
    linked_activity_id = models.UUIDField(null=True, blank=True)
    resource_type = _enum(
        "Human_Labor_Skill",
        "Natural_Material",
        "Energy",
        "Ecological_Capacity",
        "Built_Capacity",
        "Land_Area",
    )
    resource_name = models.CharField(max_length=300, null=True, blank=True)
    available_quantity = models.DecimalField(**DECIMAL)
    unit_of_measure = models.CharField(max_length=32, null=True, blank=True)
    replenishment_rate = models.DecimalField(**DECIMAL)
    ecological_threshold = models.DecimalField(**DECIMAL)
    is_binding_constraint = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = "RealResourceConstraint"


class UnitOfMeasure(models.Model):
    unit_code = models.CharField(max_length=32, primary_key=True)
    unit_name = models.CharField(max_length=200, null=True, blank=True)
    dimension = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "UnitOfMeasure"


MODELS = {
    m.__name__: m
    for m in (
        Region,
        AssetPortfolio,
        AssetManagementObjective,
        LifecycleActivity,
        EconomicActivity,
        RealResourceConstraint,
        UnitOfMeasure,
    )
}
