"""
pymfx.convert.from_gpx — Import GPX 1.0/1.1 to MfxFile

Zero external dependencies (uses stdlib xml.etree.ElementTree).
"""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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


def _parse_iso(s: str) -> datetime | None:
    """Parse an ISO 8601 datetime string to a timezone-aware datetime."""
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(s.rstrip("Z"), fmt.rstrip("Z")).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
    return None


def _tag(ns: str, name: str) -> str:
    return f"{{{ns}}}{name}" if ns else name


def from_gpx(source: str | Path) -> MfxFile:
    """
    Import a GPX file and convert it to MfxFile.

    Reads the first <trk>/<trkseg> as the trajectory.
    <wpt> elements are converted to Events, placed at the closest trajectory point.

    Args:
        source: path to a .gpx file (str or Path), or raw GPX XML string

    Returns:
        MfxFile — fill in meta fields (drone_id, pilot_id, etc.) after import
    """
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    elif isinstance(source, str) and "\n" not in source and Path(source).exists():
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = source

    root = ET.fromstring(text)
    raw_tag = root.tag
    ns = raw_tag[1 : raw_tag.index("}")] if raw_tag.startswith("{") else ""

    def find(el: ET.Element, *path: str) -> ET.Element | None:
        for name in path:
            result = el.find(_tag(ns, name))
            if result is None:
                return None
            el = result
        return el

    def findall(el: ET.Element, *path: str) -> list[ET.Element]:
        if not path:
            return []
        parent = find(el, *path[:-1]) if len(path) > 1 else el
        if parent is None:
            return []
        return parent.findall(_tag(ns, path[-1]))

    # --- Metadata ---
    meta_el = find(root, "metadata")
    name = ""
    date_start = ""
    if meta_el is not None:
        name_el = find(meta_el, "name")
        if name_el is not None and name_el.text:
            name = name_el.text.strip()
        time_el = find(meta_el, "time")
        if time_el is not None and time_el.text:
            date_start = time_el.text.strip()

    # --- Track points ---
    points: list[TrajectoryPoint] = []
    raw_lines: list[str] = []
    t0_dt: datetime | None = None

    for trkpt in findall(root, "trk", "trkseg", "trkpt"):
        lat = float(trkpt.get("lat", 0))
        lon = float(trkpt.get("lon", 0))

        ele_el = find(trkpt, "ele")
        alt_m = float(ele_el.text) if ele_el is not None and ele_el.text else None

        t: float
        time_el = find(trkpt, "time")
        if time_el is not None and time_el.text:
            pt_dt = _parse_iso(time_el.text.strip())
            if pt_dt is not None:
                if t0_dt is None:
                    t0_dt = pt_dt
                    if not date_start:
                        date_start = time_el.text.strip()
                t = round((pt_dt - t0_dt).total_seconds(), 3)
            else:
                t = float(len(points))
        else:
            t = float(len(points))

        speed_ms: float | None = None
        heading: float | None = None
        ext_el = find(trkpt, "extensions")
        if ext_el is not None:
            for child in ext_el:
                local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if local == "speed" and child.text:
                    try:
                        speed_ms = float(child.text)
                    except ValueError:
                        pass
                elif local in ("course", "heading") and child.text:
                    try:
                        heading = float(child.text)
                    except ValueError:
                        pass

        p = TrajectoryPoint(
            t=t, lat=lat, lon=lon, alt_m=alt_m, speed_ms=speed_ms, heading=heading
        )
        points.append(p)

        vals = [f"{t:.3f}", str(lat), str(lon)]
        if alt_m is not None:
            vals.append(str(alt_m))
        raw_lines.append(" | ".join(vals))

    # --- Waypoints → Events ---
    events_list: list[Event] = []
    for wpt in findall(root, "wpt"):
        wlat = float(wpt.get("lat", 0))
        wlon = float(wpt.get("lon", 0))
        wname_el = find(wpt, "name")
        wdesc_el = find(wpt, "desc")
        wname = wname_el.text.strip() if wname_el is not None and wname_el.text else "event"
        wdesc = wdesc_el.text.strip() if wdesc_el is not None and wdesc_el.text else ""
        # Closest point by geographic distance (squared)
        t_closest = 0.0
        if points:
            closest = min(
                points, key=lambda p: (p.lat - wlat) ** 2 + (p.lon - wlon) ** 2
            )
            t_closest = closest.t
        events_list.append(Event(t=t_closest, type=wname, detail=wdesc or None))

    # --- Schema fields ---
    has_alt = any(p.alt_m is not None for p in points)
    has_speed = any(p.speed_ms is not None for p in points)
    has_heading = any(p.heading is not None for p in points)

    schema_fields = [
        SchemaField("t",   "float", ["no_null"]),
        SchemaField("lat", "float", ["no_null", "range=-90..90"]),
        SchemaField("lon", "float", ["no_null", "range=-180..180"]),
    ]
    if has_alt:
        schema_fields.append(SchemaField("alt_m", "float"))
    if has_speed:
        schema_fields.append(SchemaField("speed_ms", "float"))
    if has_heading:
        schema_fields.append(SchemaField("heading", "float", ["range=0..360"]))

    # --- Auto-detect frequency ---
    frequency_hz: float | None = None
    if len(points) >= 2:
        total_t = points[-1].t - points[0].t
        if total_t > 0:
            frequency_hz = round((len(points) - 1) / total_t, 2)

    if not date_start:
        date_start = "1970-01-01T00:00:00Z"

    meta = Meta(
        id=f"uuid:{uuid.uuid4()}",
        drone_id=name or "unknown",
        drone_type="unknown",
        pilot_id="unknown",
        date_start=date_start,
        status="complete",
        application="unknown",
        location="unknown",
        sensors=[],
        data_level="raw",
        license="unknown",
        contact="unknown",
        source_format="gpx",
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
            SchemaField("t",      "float", ["no_null"]),
            SchemaField("type",   "str"),
            SchemaField("detail", "str"),
        ]
        ev_raw = [
            f"{e.t:.3f} | {e.type or ''} | {e.detail or ''}" for e in events_list
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
