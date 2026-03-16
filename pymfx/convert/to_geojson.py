"""
pymfx.convert.to_geojson — Export MfxFile to GeoJSON FeatureCollection

Zero external dependencies (uses stdlib json).
"""
from __future__ import annotations

import json

from ..models import MfxFile


def to_geojson(mfx: MfxFile, indent: int = 2, include_points: bool = False) -> str:
    """
    Export a MfxFile to GeoJSON FeatureCollection.

    The trajectory is exported as a LineString feature.
    Events are exported as Point features placed at the closest trajectory coordinate.
    Optionally, each trajectory point is also exported as an individual Point feature.

    Args:
        mfx:            parsed MfxFile
        indent:         JSON indentation (use None for compact output)
        include_points: if True, include each trajectory point as a Point feature

    Returns:
        GeoJSON string (UTF-8)
    """
    features: list[dict] = []

    # --- Trajectory as LineString ---
    coords: list[list[float]] = []
    for p in mfx.trajectory.points:
        if p.lat is None or p.lon is None:
            continue
        c: list[float] = [p.lon, p.lat]
        if p.alt_m is not None:
            c.append(p.alt_m)
        coords.append(c)

    if coords:
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "feature_type": "trajectory",
                "drone_id": mfx.meta.drone_id,
                "drone_type": mfx.meta.drone_type,
                "pilot_id": mfx.meta.pilot_id,
                "date_start": mfx.meta.date_start,
                "date_end": mfx.meta.date_end,
                "status": mfx.meta.status,
                "application": mfx.meta.application,
                "location": mfx.meta.location,
                "frequency_hz": mfx.trajectory.frequency_hz,
                "point_count": len(mfx.trajectory.points),
            },
        })

    # --- Optional: individual trajectory points ---
    if include_points:
        for p in mfx.trajectory.points:
            if p.lat is None or p.lon is None:
                continue
            c2: list[float] = [p.lon, p.lat]
            if p.alt_m is not None:
                c2.append(p.alt_m)
            props: dict = {"feature_type": "point", "t": p.t}
            if p.speed_ms is not None:
                props["speed_ms"] = p.speed_ms
            if p.heading is not None:
                props["heading"] = p.heading
            if p.roll is not None:
                props["roll"] = p.roll
            if p.pitch is not None:
                props["pitch"] = p.pitch
            props.update(p.extra)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": c2},
                "properties": props,
            })

    # --- Events as Point features ---
    if mfx.events:
        valid_pts = [
            p for p in mfx.trajectory.points
            if p.lat is not None and p.lon is not None and p.t is not None
        ]
        for e in mfx.events.events:
            if e.t is None:
                continue
            closest = min(valid_pts, key=lambda p: abs(p.t - e.t), default=None)
            if closest is None:
                continue
            c3: list[float] = [closest.lon, closest.lat]
            if closest.alt_m is not None:
                c3.append(closest.alt_m)
            eprops: dict = {
                "feature_type": "event",
                "t": e.t,
                "type": e.type,
                "severity": e.severity,
                "detail": e.detail,
            }
            eprops.update(e.extra)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": c3},
                "properties": eprops,
            })

    fc = {
        "type": "FeatureCollection",
        "properties": {
            "generator": "pymfx",
            "version": mfx.version,
            "id": mfx.meta.id,
        },
        "features": features,
    }
    return json.dumps(fc, indent=indent, ensure_ascii=False)
