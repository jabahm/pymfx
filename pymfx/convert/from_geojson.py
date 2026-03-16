"""
pymfx.convert.from_geojson — Import GeoJSON to MfxFile

Zero external dependencies (uses stdlib json).
Supports FeatureCollection, single Feature, LineString, and MultiLineString.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from ..models import (
    Event,
    Events,
    Meta,
    MfxFile,
    SchemaField,
    Trajectory,
    TrajectoryPoint,
)


def from_geojson(source: str | Path) -> MfxFile:
    """
    Import a GeoJSON file and convert it to MfxFile.

    The first LineString (or first segment of a MultiLineString) becomes the trajectory.
    Point features with ``feature_type == "event"`` become Events.
    Meta fields (drone_id, date_start, etc.) are read from the LineString's properties
    if present (as written by ``to_geojson()``).

    Args:
        source: path to a .geojson file (str or Path), or raw GeoJSON string

    Returns:
        MfxFile — fill in meta fields after import if needed
    """
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    elif isinstance(source, str) and "\n" not in source and Path(source).exists():
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = source

    data: dict = json.loads(text)

    # Normalize to a flat list of features
    features: list[dict] = []
    gtype = data.get("type", "")
    if gtype == "FeatureCollection":
        features = data.get("features", [])
    elif gtype == "Feature":
        features = [data]
    elif gtype in ("LineString", "MultiLineString"):
        features = [{"type": "Feature", "geometry": data, "properties": {}}]

    # --- Find trajectory (first LineString / MultiLineString) ---
    line_coords: list[list[float]] = []
    meta_props: dict = {}

    for f in features:
        geom = f.get("geometry") or {}
        gt = geom.get("type", "")
        if gt == "LineString":
            line_coords = geom.get("coordinates", [])
            meta_props = f.get("properties") or {}
            break
        if gt == "MultiLineString":
            segs = geom.get("coordinates", [])
            if segs:
                line_coords = segs[0]
                meta_props = f.get("properties") or {}
            break

    if not line_coords:
        raise ValueError(
            "No LineString geometry found in GeoJSON. "
            "Provide a FeatureCollection or Feature with a LineString geometry."
        )

    # --- Build trajectory points ---
    points: list[TrajectoryPoint] = []
    raw_lines: list[str] = []

    for i, coord in enumerate(line_coords):
        lon = float(coord[0])
        lat = float(coord[1])
        alt_m = float(coord[2]) if len(coord) > 2 else None
        t = float(i)  # synthetic t; no timestamp in basic GeoJSON
        p = TrajectoryPoint(t=t, lat=lat, lon=lon, alt_m=alt_m)
        points.append(p)
        vals = [f"{t:.3f}", str(lat), str(lon)]
        if alt_m is not None:
            vals.append(str(alt_m))
        raw_lines.append(" | ".join(vals))

    # --- Events from Point features ---
    events_list: list[Event] = []
    for f in features:
        geom = f.get("geometry") or {}
        props = f.get("properties") or {}
        if geom.get("type") != "Point":
            continue
        # Accept points tagged as events (from to_geojson output) or with a "type" field
        if props.get("feature_type") != "event" and "type" not in props:
            continue
        t_ev = float(props.get("t", 0))
        events_list.append(Event(
            t=t_ev,
            type=props.get("type"),
            severity=props.get("severity"),
            detail=props.get("detail"),
        ))

    # --- Schema fields ---
    has_alt = any(p.alt_m is not None for p in points)
    schema_fields = [
        SchemaField("t",   "float", ["no_null"]),
        SchemaField("lat", "float", ["no_null", "range=-90..90"]),
        SchemaField("lon", "float", ["no_null", "range=-180..180"]),
    ]
    if has_alt:
        schema_fields.append(SchemaField("alt_m", "float"))

    # --- Auto-detect frequency ---
    frequency_hz: float | None = None
    if len(points) >= 2:
        total_t = points[-1].t - points[0].t
        if total_t > 0:
            frequency_hz = round((len(points) - 1) / total_t, 2)

    meta = Meta(
        id=meta_props.get("id", f"uuid:{uuid.uuid4()}"),
        drone_id=str(meta_props.get("drone_id", "unknown")),
        drone_type=str(meta_props.get("drone_type", "unknown")),
        pilot_id=str(meta_props.get("pilot_id", "unknown")),
        date_start=str(meta_props.get("date_start", "1970-01-01T00:00:00Z")),
        date_end=meta_props.get("date_end"),
        status=str(meta_props.get("status", "complete")),
        application=str(meta_props.get("application", "unknown")),
        location=str(meta_props.get("location", "unknown")),
        sensors=[],
        data_level="raw",
        license="unknown",
        contact="unknown",
        source_format="geojson",
    )

    trajectory = Trajectory(
        frequency_hz=frequency_hz,
        schema_fields=schema_fields,
        points=points,
        raw_lines=raw_lines,
    )

    events_obj: Events | None = None
    if events_list:
        ev_schema = [
            SchemaField("t",        "float", ["no_null"]),
            SchemaField("type",     "str"),
            SchemaField("severity", "str"),
            SchemaField("detail",   "str"),
        ]
        ev_raw = [
            f"{e.t:.3f} | {e.type or ''} | {e.severity or ''} | {e.detail or ''}"
            for e in events_list
        ]
        events_obj = Events(
            schema_fields=ev_schema, events=events_list, raw_lines=ev_raw
        )

    return MfxFile(
        version="1.0",
        encoding="UTF-8",
        meta=meta,
        trajectory=trajectory,
        events=events_obj,
    )
