from django.conf import settings

# The method note's "what the result does not claim" list, shown on every page.
NOT_CLAIMED = (
    "It locates pressure. It does not size price changes, because input-output "
    "analysis assumes fixed proportions and no price response.",
    "It has no deficit or debt term.",
    "It makes no claim about fiscal space for eurozone members, which are "
    "currency users.",
    "It cannot see constraints in permits, grid connections, planning or "
    "training capacity.",
    "It scores against labour available in the country. Migration and posted "
    "workers are a named limitation, not part of the model.",
    "At 64 industries, results are bands, not point estimates.",
)


def site(request):
    return {
        "PUBLIC_READ_ONLY": settings.PUBLIC_READ_ONLY,
        "NOT_CLAIMED": NOT_CLAIMED,
        "REPO_URL": "https://github.com/ChrisB2025/capacity-check-eu",
    }
