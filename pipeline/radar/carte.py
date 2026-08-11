"""Projection du contour simplifié des départements (métropole) en chemins SVG pour le site.

Source : gregoiredavid/france-geojson (dérivé d'Admin Express IGN, Licence Ouverte).
Usage : python -m radar.carte <departements-version-simplifiee.geojson>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from . import config

W = 1000  # largeur du repère SVG
LAT0 = 46.5  # latitude de référence (projection équirectangulaire corrigée)


def project(lon: float, lat: float) -> tuple[float, float]:
    return lon * math.cos(math.radians(LAT0)), -lat


def build(src: Path) -> dict:
    gj = json.loads(src.read_text())
    feats = gj["features"]
    pts = [project(*c) for f in feats for poly in _polys(f["geometry"]) for ring in poly for c in ring]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    scale = W / (max(xs) - x0)
    height = round((max(ys) - y0) * scale)
    out = {}
    for f in feats:
        d = []
        for poly in _polys(f["geometry"]):
            for ring in poly:
                prev = None
                seg = []
                for lon, lat in ring:
                    x, y = project(lon, lat)
                    p = (round((x - x0) * scale, 1), round((y - y0) * scale, 1))
                    if p != prev:
                        seg.append(p)
                        prev = p
                if len(seg) >= 3:
                    d.append("M" + "L".join(f"{a:g},{b:g}" for a, b in seg) + "Z")
        cx = sum((project(*c)[0] - x0) * scale for c in _polys(f["geometry"])[0][0]) / len(_polys(f["geometry"])[0][0])
        cy = sum((project(*c)[1] - y0) * scale for c in _polys(f["geometry"])[0][0]) / len(_polys(f["geometry"])[0][0])
        out[f["properties"]["code"]] = {"nom": f["properties"]["nom"], "d": "".join(d), "cx": round(cx, 1), "cy": round(cy, 1)}
    return {"width": W, "height": height, "source": "gregoiredavid/france-geojson (Admin Express IGN, Licence Ouverte)",
            "departements": out}


def _polys(geom: dict) -> list:
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def main(argv: list[str]) -> None:
    data = build(Path(argv[1]))
    dest = config.SITE_DATA / "carte_departements.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    (config.REFERENCE / "carte_departements.json").write_text(dest.read_text())
    print(f"{len(data['departements'])} départements, {dest.stat().st_size / 1e3:.0f} Ko")


if __name__ == "__main__":
    main(sys.argv)
