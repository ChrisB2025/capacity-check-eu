"""Build the SVG outlines for the headline map from Eurostat GISCO boundaries.

Usage: python web/tools/build_map.py <NUTS_RG_20M_2024_4326_LEVL_0.geojson>

Source: Eurostat GISCO, NUTS 2024, 1:20 million, level 0,
https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_4326_LEVL_0.geojson
(c) EuroGeographics for the administrative boundaries. The outlines are
display only; no number is derived from them.

Projects to a Lambert azimuthal equal-area projection centred on 10E 52N,
the centre used by EPSG:3035, drops outermost regions outside the European
frame, and writes ``web/results/static/results/map.json``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

LON0, LAT0 = math.radians(10), math.radians(52)
FRAME = (-25.0, 34.0, 45.0, 72.0)  # lon min, lat min, lon max, lat max
SCALE = 1000.0
OUT = (
    Path(__file__).resolve().parents[1] / "results" / "static" / "results" / "map.json"
)


def project(lon: float, lat: float) -> tuple[float, float]:
    lam, phi = math.radians(lon), math.radians(lat)
    k = math.sqrt(
        2
        / (
            1
            + math.sin(LAT0) * math.sin(phi)
            + math.cos(LAT0) * math.cos(phi) * math.cos(lam - LON0)
        )
    )
    x = k * math.cos(phi) * math.sin(lam - LON0)
    y = k * (
        math.cos(LAT0) * math.sin(phi)
        - math.sin(LAT0) * math.cos(phi) * math.cos(lam - LON0)
    )
    return x * SCALE, -y * SCALE


def _inside(ring) -> bool:
    lon = sum(p[0] for p in ring) / len(ring)
    lat = sum(p[1] for p in ring) / len(ring)
    return FRAME[0] <= lon <= FRAME[2] and FRAME[1] <= lat <= FRAME[3]


def main(path: str) -> None:
    raw = Path(path).read_bytes()
    gj = json.loads(raw)
    paths, xs, ys = {}, [], []
    for f in gj["features"]:
        code = f["properties"]["NUTS_ID"]
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        parts = []
        for poly in polys:
            if not _inside(poly[0]):
                continue
            for ring in poly:
                pts = [project(lon, lat) for lon, lat in ring]
                xs += [p[0] for p in pts]
                ys += [p[1] for p in pts]
                parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
        if parts:
            paths[code] = "".join(parts)
    pad = 10
    box = [min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 2 * pad,
           max(ys) - min(ys) + 2 * pad]  # fmt: skip
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "viewBox": " ".join(f"{v:.0f}" for v in box),
                "paths": paths,
                "source": "Eurostat GISCO, NUTS 2024, 1:20 million, level 0. "
                "(c) EuroGeographics for the administrative boundaries.",
                "source_sha256": hashlib.sha256(raw).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    print(OUT, len(paths))


if __name__ == "__main__":
    main(sys.argv[1])
