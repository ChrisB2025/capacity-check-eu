"""The project's own tables: the system of record for every result.

A run's figures are stored exactly as the engine produced them, one
``ResultRow`` per row of each engine table, so the pages and the CSV
downloads show the engine's numbers and nothing computed here.
"""

from django.db import models


class DataEdition(models.Model):
    """A data file a run read, identified by its checksum."""

    file = models.CharField(max_length=300)
    sha256 = models.CharField(max_length=64)
    role = models.CharField(max_length=100)

    class Meta:
        unique_together = [("file", "sha256", "role")]

    def __str__(self):
        return self.file


class CompositionTable(models.Model):
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=32)
    sha256 = models.CharField(max_length=64, unique=True)
    confirmed_by = models.CharField(max_length=200, null=True, blank=True)
    confirmed_on = models.CharField(max_length=32, null=True, blank=True)
    user_defined = models.BooleanField(default=False)
    lines = models.JSONField()

    def __str__(self):
        return f"{self.name} ({self.status})"


class Run(models.Model):
    run_id = models.CharField(max_length=12, unique=True)
    created = models.DateTimeField()
    params = models.JSONField()
    manifest = models.JSONField()
    provisional = models.BooleanField()
    user_defined = models.BooleanField(default=False)
    composition = models.ForeignKey(CompositionTable, on_delete=models.PROTECT)
    editions = models.ManyToManyField(DataEdition)
    seconds = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.run_id


class RunInput(models.Model):
    """One parameter of a run, as text, for listing and filtering."""

    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="inputs")
    name = models.CharField(max_length=100)
    value = models.TextField()


class ResultRow(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="rows")
    table = models.CharField(max_length=40)
    position = models.IntegerField()
    country = models.CharField(max_length=8, blank=True)
    industry = models.CharField(max_length=16, blank=True)
    data = models.JSONField()

    class Meta:
        ordering = ["position"]
        indexes = [models.Index(fields=["run", "table", "country"])]


class RequirementExtension(models.Model):
    """The three change-request fields, kept outside the CDM tables.

    CR-1 required_quantity, CR-2 assessment_category, CR-3 availability_basis,
    keyed to the baseline RealResourceConstraint row they would extend.
    """

    constraint_id = models.UUIDField(unique=True)
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    required_quantity = models.FloatField(null=True)
    assessment_category = models.CharField(max_length=16)
    availability_basis = models.CharField(max_length=200, null=True)
