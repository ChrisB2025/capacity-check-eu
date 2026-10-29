"""Display formatting only. Rounds for reading; never changes a stored value."""

from django import template

register = template.Library()


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


@register.filter
def pct(v, digits=0):
    f = _num(v)
    return "n/a" if f is None else f"{f * 100:.{int(digits)}f}%"


@register.filter
def num(v, digits=0):
    f = _num(v)
    return "n/a" if f is None else f"{f:,.{int(digits)}f}"


@register.filter
def hundreds(v):
    """Persons to the nearest hundred, as in the reports."""
    f = _num(v)
    return "n/a" if f is None else f"{round(f, -2):,.0f}"


@register.filter
def get(d, key):
    return d.get(key) if hasattr(d, "get") else None


@register.filter
def rating_class(r):
    return {
        "binding": "rating-binding",
        "tight": "rating-tight",
        "clear": "rating-clear",
    }.get(r, "rating-none")
