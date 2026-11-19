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
def bn(v):
    """Millions of euros as billions, to the nearest billion."""
    f = _num(v)
    return "n/a" if f is None else f"{f / 1000:,.0f}"


@register.filter
def millions(v, digits=1):
    """Persons as millions."""
    f = _num(v)
    return "n/a" if f is None else f"{f / 1e6:,.{int(digits)}f}"


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


@register.filter
def attr_of(obj, name):
    return getattr(obj, name, None)


@register.filter
def ordinal(v):
    """A share as an ordinal percentile: 0.863 becomes "86th"."""
    f = _num(v)
    if f is None:
        return "n/a"
    n = int(round(f * 100))
    suffix = (
        "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    )
    return f"{n}{suffix}"
