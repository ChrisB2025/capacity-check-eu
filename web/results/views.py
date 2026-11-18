"""Pages. Every figure shown comes from a stored engine table; views only select,
sort and lay out rows."""

from __future__ import annotations

import csv as csvlib
import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from engine import concordance, sensitivity, shock, text
from engine.params import RunParams, Thresholds
from engine.sources._common import EU27
from web.results import bridge
from web.results.forms import QUESTIONS, FeedbackForm
from web.results.models import Feedback, ResultRow, Run

MAP_FILE = Path(__file__).parent / "static" / "results" / "map.json"
# Headline bins for the map, and the sequential blue ramp (light to dark).
MAP_BINS = (0.0, 0.6, 0.7, 0.75, 0.8, 0.85)
MAP_COLOURS = ("#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#104281")
FOCUS = (("F", "Construction"), ("M71", "Architecture and engineering"),
         ("C28", "Machinery, incl. heat pumps"))  # fmt: skip


def health(request):
    return JsonResponse({"status": "ok", "phase": 4})


def _rows(run: Run, table: str, country: str | None = None) -> list[dict]:
    qs = ResultRow.objects.filter(run=run, table=table)
    if country:
        qs = qs.filter(country=country)
    return [r.data for r in qs]


def _run(run_id: str) -> Run:
    return get_object_or_404(Run, run_id=run_id)


def _first(run: Run, table: str) -> dict | None:
    return next(iter(_rows(run, table)), None)


def _allocation(run: Run) -> tuple[list[dict], str]:
    """The run's allocation table with the reason for each line."""
    notes = text.composition_notes()
    rows = _rows(run, "allocation")
    for a in rows:
        a["note"] = notes["codes"].get(a["code"], "")
    name = run.composition.name if run.composition else run.params["composition"]
    comp_note = notes["compositions"].get(
        name,
        "This spending mix was edited on the inputs page, so the run is a "
        "user-defined shock, not the standard one.",
    )
    return rows, comp_note


def _trades(run: Run) -> list[dict]:
    """Construction trades from the run's full Swedish occupation table."""
    occ = {str(r["ssyk"]): r for r in _rows(run, "sweden_occupations")}
    out = []
    for g in text.trades_se() if occ else []:
        rows = [
            {**occ[code], "ssyk": code, "label": label}
            for code, label in g["codes"].items()
            if code in occ
        ]
        rows.sort(key=lambda r: -(r.get("extra_persons") or 0))
        if rows:
            out.append({"name": g["name"], "rows": rows})
    return out


def _summary(run: Run, names: dict) -> dict:
    sm = _first(run, "summary")
    if not sm:
        return {"sm": None}
    return {
        "sm": sm,
        "min_name": names.get(sm["headline_min_country"]),
        "max_name": names.get(sm["headline_max_country"]),
    }


@lru_cache(maxsize=1)
def _map() -> dict:
    return json.loads(MAP_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _names() -> dict:
    try:
        from engine.cdm import country_names

        return country_names()
    except FileNotFoundError:
        return {}


def _bin(v):
    if v is None:
        return None
    k = sum(1 for b in MAP_BINS if v >= b) - 1
    return max(k, 0)


def _legend():
    edges = [*MAP_BINS[1:], None]
    out = []
    for i, colour in enumerate(MAP_COLOURS):
        lo, hi = MAP_BINS[i], edges[i]
        label = (
            f"under {hi:.0%}"
            if i == 0
            else (f"{lo:.0%} to {hi:.0%}" if hi else f"{lo:.0%} and over")
        )
        out.append({"colour": colour, "label": label})
    return out


def _shapes(run: Run, by_c: dict) -> list[dict]:
    """Map outlines filled by headline bin; ``by_c`` rows carry ``name``."""
    shapes = []
    for code, d in _map()["paths"].items():
        row = by_c.get(code)
        if row is None:
            shapes.append({"code": code, "d": d, "fill": None, "title": ""})
            continue
        v = row["headline_tight_or_binding_share"]
        k = _bin(v)
        shapes.append(
            {
                "code": code,
                "d": d,
                "fill": MAP_COLOURS[k] if k is not None else "nodata",
                "title": f"{row['name']}: "
                + (f"{v:.0%} of jobs on tight or binding lines" if v is not None
                   else "no headline"),  # fmt: skip
                "url": f"/run/{run.run_id}/country/{code}/",
            }
        )
    shapes.sort(key=lambda s: s["fill"] is not None)  # EU states drawn last
    return shapes


def _base_run() -> Run | None:
    """The run with the default parameters, if it has been stored."""
    params = json.loads(json.dumps(RunParams().as_dict()))
    return Run.objects.filter(params=params).first()


def overview(request):
    """Front page: the premise, then how it works, then the way into the runs.
    Every figure is a cell of the base run's engine ``overview`` table."""
    run = _base_run()
    ov = next(iter(_rows(run, "overview")), None) if run else None
    if ov is None:
        return render(request, "results/overview.html", {"run": run, "ov": None})
    names = _names()
    countries = _rows(run, "countries")
    for c in countries:
        c["name"] = names.get(c["country"], c["country"])
    by_c = {c["country"]: c for c in countries}
    m = _map()
    total = sum(ov[f"lines_{k}"] for k in ("binding", "tight", "clear", "no_rating"))
    return render(
        request,
        "results/overview.html",
        {
            "run": run,
            "p": run.params,
            "ov": ov,
            "lines_total": total,
            "example_name": names.get(ov["example_country"], ov["example_country"]),
            "min_name": names.get(ov["headline_min_country"]),
            "max_name": names.get(ov["headline_max_country"]),
            "shapes": _shapes(run, by_c),
            "viewbox": m["viewBox"],
            "map_source": m["source"],
            "legend": _legend(),
            **_summary(run, names),
        },
    )


def runs(request):
    items = []
    for run in Run.objects.select_related("composition"):
        p = run.params
        items.append({"run": run, "p": p, "n_countries": len(p["countries"])})
    return render(request, "results/runs.html", {"items": items})


def _form_defaults(request):
    comps = bridge.compositions()
    name = request.GET.get("composition") or request.POST.get("composition")
    name = name if name in comps else "standard"
    return comps, name


def new_run(request):
    if settings.PUBLIC_READ_ONLY:
        return HttpResponseForbidden("Public read-only mode: no new runs.")
    comps, comp_name = _form_defaults(request)
    eds = bridge.editions()
    names = _names()
    ctx = {
        "compositions": comps,
        "composition": comps[comp_name],
        "comp_name": comp_name,
        "editions": eds,
        "countries": [(c, names.get(c, c)) for c in EU27],
        "defaults": RunParams(),
        # Pressure thresholds are entered in per cent.
        "defaults_pressure_low": f"{RunParams().thresholds.pressure_low * 100:g}",
        "defaults_pressure_high": f"{RunParams().thresholds.pressure_high * 100:g}",
        "values": request.POST or {},
        "selected": set(request.POST.getlist("countries")) or set(EU27),
    }
    if request.method != "POST":
        return render(request, "results/new.html", ctx)
    try:
        params = _params_from_post(request.POST, comps)
    except (ValueError, KeyError) as exc:
        messages.error(request, str(exc))
        return render(request, "results/new.html", ctx, status=400)
    run = bridge.execute(params)
    return redirect("run", run_id=run.run_id)


def _params_from_post(post, comps) -> RunParams:
    base = comps[post["composition"]]
    shares = {
        ln.code: float(post.get(f"share_{ln.code}", ln.share)) for ln in base.lines
    }
    edited = any(abs(shares[ln.code] - ln.share) > 1e-12 for ln in base.lines)
    composition = bridge.user_composition(base, shares) if edited else base.name
    if edited:
        shock.load_composition(composition)  # validates shares sum to one
    edition, year = post["edition"].split(":")
    countries = tuple(c for c in EU27 if c in post.getlist("countries"))
    if not countries:
        raise ValueError("Choose at least one member state.")
    return RunParams(
        shock_pct=float(post["shock_pct"]),
        edition=edition,
        ref_year=int(year),
        composition=composition,
        application=post["application"],
        slack_indicator=post["slack_indicator"],
        thresholds=Thresholds(
            pressure_low=float(post["pressure_low"]) / 100,
            pressure_high=float(post["pressure_high"]) / 100,
            slack_median_quantile=float(post["slack_median_quantile"]),
            slack_top_quantile=float(post["slack_top_quantile"]),
        ),
        countries=countries,
    )


@require_GET
def composition_total(request):
    total = 0.0
    for k, v in request.GET.items():
        if k.startswith("share_"):
            try:
                total += float(v)
            except ValueError:
                return HttpResponse('<span class="text-red-700">not a number</span>')
    ok = abs(total - 1.0) <= shock.SHARE_TOLERANCE
    cls = "text-emerald-800" if ok else "text-red-700"
    note = "" if ok else " (must be 1)"
    return HttpResponse(f'<span class="{cls}">Total {total:.6f}{note}</span>')


def run_detail(request, run_id):
    run = _run(run_id)
    names = _names()
    countries = _rows(run, "countries")
    for c in countries:
        c["name"] = names.get(c["country"], c["country"])
    by_c = {c["country"]: c for c in countries}
    lines = ResultRow.objects.filter(
        run=run, table="lines", industry__in=[f for f, _ in FOCUS],
        country__in=list(by_c),
    )  # fmt: skip
    focus = {}
    for r in lines:
        focus.setdefault(r.country, {})[r.industry] = r.data
    for c in countries:
        c["focus"] = [focus.get(c["country"], {}).get(code, {}) for code, _ in FOCUS]

    m = _map()
    shapes = _shapes(run, by_c)
    deps = _rows(run, "dependencies")
    tables = sorted(
        set(ResultRow.objects.filter(run=run).values_list("table", flat=True))
    )
    alloc, comp_note = _allocation(run)
    return render(
        request,
        "results/run.html",
        {
            "run": run,
            "p": run.params,
            "countries": countries,
            "focus_labels": FOCUS,
            "shapes": shapes,
            "viewbox": m["viewBox"],
            "map_source": m["source"],
            "legend": _legend(),
            "deps": deps,
            "tables": tables,
            "has_sweden": "sweden_occupations" in tables,
            "has_sensitivity": "sensitivity" in tables,
            "alloc": alloc,
            "comp_note": comp_note,
            "construction_limit": text.composition_notes()["construction_limit"],
            "trades": _trades(run),
            "responses": text.responses(),
            **_summary(run, names),
        },
    )


def country(request, run_id, country):
    run = _run(run_id)
    if country not in run.params["countries"]:
        raise Http404
    names = _names()
    summary = next(iter(_rows(run, "countries", country)), None)
    rows = _rows(run, "country_lines", country)
    rows.sort(key=lambda r: -(r.get("extra_persons_all") or 0))
    show_all = request.GET.get("all") == "1"
    binding = [r for r in rows if r.get("rating") == "binding"]
    tight = [r for r in rows if r.get("rating") == "tight"]
    labels = {a["code"]: a["line"] for a in _rows(run, "allocation")}
    direct = _rows(run, "direct_demand", country)
    for d in direct:
        d["line"] = labels.get(d["code"], "")
    return render(
        request,
        "results/country.html",
        {
            "run": run,
            "country": country,
            "name": names.get(country, country),
            "summary": summary,
            "rows": rows if show_all else rows[:20],
            "show_all": show_all,
            "n_rows": len(rows),
            "direct": direct,
            "binding_lines": binding,
            "tight_lines": tight[:5],
            "more_tight": max(len(tight) - 5, 0),
            "responses": text.responses(),
        },
    )


def sweden(request, run_id):
    run = _run(run_id)
    occ = _rows(run, "sweden_occupations")
    if not occ:
        raise Http404
    konj = [r for r in _rows(run, "sweden_konj") if r.get("publishable")]
    return render(
        request,
        "results/sweden.html",
        {
            "run": run,
            "forecasts": _rows(run, "sweden_forecasts"),
            "education": _rows(run, "sweden_education"),
            "konj": konj,
            "unknown": next((r for r in occ if not r.get("known_occupation")), None),
            "trades": _trades(run),
        },
    )


def csv(request, run_id, table):
    run = _run(run_id)
    rows = _rows(run, table)
    if not rows:
        raise Http404
    if table == "sweden_konj":
        rows = [r for r in rows if r.get("publishable")]
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{run_id}_{table}.csv"'
    resp.write(f"# run {run_id}; provisional={run.provisional}; "
               f"sources in /run/{run_id}/ and the run manifest\n")  # fmt: skip
    resp.write(f"# {text.RISK_LABEL}\n")
    w = csvlib.DictWriter(resp, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return resp


def about(request):
    a64 = concordance.load()
    return render(
        request, "results/about.html", {"industries": len(a64), "base": _base_run()}
    )


def glossary(request):
    """Every term in engine/text/glossary.yaml, with the default values."""
    vals = text.values()
    groups = [
        {
            "name": g,
            "terms": [
                text.filled(t["slug"], vals) for t in text.glossary() if t["group"] == g
            ],
        }
        for g in text.groups()
    ]
    return render(request, "results/glossary.html", {"groups": groups})


def thresholds(request, run_id):
    """How the estimated risk categories change when the thresholds move."""
    run = _run(run_id)
    rows = _rows(run, "sensitivity")
    if not rows:
        raise Http404
    ref = sensitivity.load_reference()
    vals = text.values(run.params)
    return render(
        request,
        "results/thresholds.html",
        {
            "run": run,
            "p": run.params,
            "pressure": [r for r in rows if r["kind"] == "pressure"],
            "slack": [r for r in rows if r["kind"] == "slack"],
            "ref": (
                ref.sort_values(["cutoff", "scope"]).to_dict(orient="records")
                if ref is not None
                else []
            ),
            "reasoning": text.filled("thresholds", vals)["reasoning"],
        },
    )


def reviewers(request):
    """For reviewers: what to look at, the questions, and the feedback form."""
    form = FeedbackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not form.cleaned_data.get("website"):  # honeypot left empty
            fb = form.save(commit=False)
            fb.page = (request.POST.get("page") or "")[:300]
            fb.save()
        return redirect(reverse("reviewers") + "?sent=1#feedback")
    return render(
        request,
        "results/reviewers.html",
        {
            "form": form,
            "questions": QUESTIONS,
            "sent": request.GET.get("sent") == "1",
            "base": _base_run(),
        },
        status=400 if request.method == "POST" else 200,
    )


def feedback_list(request):
    """Feedback received; staff accounts only, not the shared login."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponseForbidden("Staff only.")
    items = Feedback.objects.all()
    if request.GET.get("format") == "csv":
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="feedback.csv"'
        fields = ["created", "name", "organisation", "email",
                  *[k for k, _ in QUESTIONS], "page"]  # fmt: skip
        w = csvlib.writer(resp, lineterminator="\n")
        w.writerow(fields)
        for f in items:
            w.writerow([getattr(f, k) for k in fields])
        return resp
    return render(
        request,
        "results/feedback_list.html",
        {"items": items, "questions": QUESTIONS},
    )
