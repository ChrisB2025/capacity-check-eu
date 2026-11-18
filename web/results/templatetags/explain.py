"""Tooltips and rating chips, filled from the glossary (engine/text/glossary.yaml).

``{% term "pressure" %}`` shows the term's name with a small "?" button;
``{% term "pressure" "Pressure on construction" %}`` shows other words.
``{% rating_chip r.rating %}`` shows the rating chip itself as the button.
Both open a popover with the definition, why it matters, the limit, the
source and a link to the glossary page. Values such as the thresholds follow
the run in the template context (``p`` or ``run.params``), else the defaults.
"""

from __future__ import annotations

import itertools

from django import template
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from engine import text

register = template.Library()

_ids = itertools.count(1)
RATING_SLUGS = {"clear": "clear", "tight": "tight", "binding": "binding"}


def _vals(context) -> dict:
    cached = context.get("_glossary_values")
    if cached is not None:
        return cached
    params = context.get("p")
    if not params and context.get("run") is not None:
        params = context["run"].params
    vals = text.values(params or None)
    context["_glossary_values"] = vals
    return vals


def _tip(context, slug: str, tip_id: str, extra=None):
    t = text.filled(slug, _vals(context))
    src = t["source"]
    parts = [
        format_html('<span class="term-def">{}</span>', t["definition"]),
        format_html(
            '<span class="term-why"><b>Why it matters.</b> {}</span>', t["why"]
        ),
    ]
    if t.get("caveat"):
        parts.append(
            format_html('<span class="term-why"><b>Limit.</b> {}</span>', t["caveat"])
        )
    if extra:
        parts.append(extra)
    parts.append(
        format_html(
            '<span class="term-src"><b>Source.</b> <a href="{}" target="_blank" '
            'rel="noopener">{}</a>, {}.</span>',
            src["url"],
            src["name"],
            src["detail"],
        )
    )
    parts.append(
        format_html(
            '<a class="term-more" href="{}#{}">In the glossary</a>',
            reverse("glossary"),
            slug,
        )
    )
    return format_html(
        '<span role="tooltip" id="{}" class="term-tip">{}</span>',
        tip_id,
        format_html_join("", "{}", ((p,) for p in parts)),
    )


@register.simple_tag(takes_context=True)
def term(context, slug: str, label: str | None = None):
    t = text.term(slug)
    tip_id = f"tip-{next(_ids)}"
    return format_html(
        '<span class="term">{}<button type="button" class="term-btn" '
        'aria-describedby="{}" aria-label="What is {}?">?</button>{}</span>',
        label if label is not None else t["term"],
        tip_id,
        t["term"],
        _tip(context, slug, tip_id),
    )


def _brief_tip(context, slug: str, tip_id: str):
    """Definition and a glossary link only, for chips repeated down a table."""
    t = text.filled(slug, _vals(context))
    return format_html(
        '<span role="tooltip" id="{}" class="term-tip"><span class="term-def">{}'
        '</span><a class="term-more" href="{}#{}">Why these cut-offs, and the '
        "limits</a></span>",
        tip_id,
        t["definition"],
        reverse("glossary"),
        slug,
    )


@register.simple_tag(takes_context=True)
def rating_chip(context, rating, brief=False):
    """The chip as a button. ``brief=True`` in long tables keeps pages light."""
    rating = rating or "no rating"
    slug = RATING_SLUGS.get(rating, "no-rating")
    cls = {"binding": "rating-binding", "tight": "rating-tight",
           "clear": "rating-clear"}.get(rating, "rating-none")  # fmt: skip
    tip_id = f"tip-{next(_ids)}"
    if brief:
        return format_html(
            '<span class="term"><button type="button" class="rating {} '
            'term-chip" aria-describedby="{}">{}</button>{}</span>',
            cls,
            tip_id,
            rating,
            _brief_tip(context, slug, tip_id),
        )
    extra = None
    run = context.get("run")
    if slug != "no-rating" and run is not None:
        extra = format_html(
            '<span class="term-why"><b>Estimated risk category, not a '
            'judgement.</b> <a href="{}">How it changes if the thresholds '
            "move</a>.</span>",
            reverse("thresholds", args=[run.run_id]),
        )
    return format_html(
        '<span class="term"><button type="button" class="rating {} term-chip" '
        'aria-describedby="{}">{}</button>{}</span>',
        cls,
        tip_id,
        rating,
        _tip(context, slug, tip_id, extra),
    )
