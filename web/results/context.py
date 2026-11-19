from django.conf import settings

from engine.text import RISK_LABEL

# The method note's "what the result does not claim" list, shown on every page.
NOT_CLAIMED = (
    "It locates pressure. It does not size price changes, because input-output "
    "analysis assumes fixed proportions and no price response.",
    "It has no deficit or debt term.",
    "It makes no claim about fiscal space. Eurozone members are rules-bound "
    "issuers of the euro: their central banks belong to the Eurosystem, but "
    "the Treaty, including Article 123's ban on central bank financing of "
    "governments, limits how they spend. The model takes those rules as given.",
    "It cannot see constraints in permits, grid connections, planning or "
    "training capacity.",
    "It scores against labour available in the country. Migration and posted "
    "workers are a named limitation, not part of the model.",
    "At 64 industries, results are bands, not point estimates.",
    "It applies one shock to 27 countries with different climates, housing "
    "stock, tenure, incomes and habits. It compares relative pressure under "
    "the same financial shock, not what each country would need to spend or do.",
    "Extra jobs are not new hires: firms can reprioritise existing work, and "
    "households can swap grant-funded work for work already planned.",
)


def site(request):
    return {
        "PUBLIC_READ_ONLY": settings.PUBLIC_READ_ONLY,
        "NOT_CLAIMED": NOT_CLAIMED,
        "RISK_LABEL": RISK_LABEL,
        "MML_EU_LABS_URL": settings.MML_EU_LABS_URL,
        "REPO_URL": "https://github.com/ChrisB2025/capacity-check-eu",
    }
