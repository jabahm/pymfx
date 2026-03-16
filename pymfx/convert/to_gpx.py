"""
pymfx.convert.to_gpx — Export MfxFile to GPX 1.1

Zero external dependencies (uses stdlib xml.etree.ElementTree).
"""
from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from ..models import MfxFile

_GPX_NS = "http://www.topografix.com/GPX/1/1"


def _parse_date_start(date_str: str) -> datetime | None:
    """Try to parse date_start as ISO 8601 datetime."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.rstrip("Z"), fmt.rstrip("Z")).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
    return None


def to_gpx(mfx: MfxFile) -> str:
    """
    Export a MfxFile to GPX 1.1 format.

    The trajectory is exported as a <trk> element.
    Events are exported as <wpt> waypoints at the closest trajectory position.

    Returns:
        GPX XML string (UTF-8)
    """
    ET.register_namespace("", _GPX_NS)

    gpx = ET.Element("gpx", {
        "version": "1.1",
        "creator": "pymfx",
        "xmlns": _GPX_NS,
    })

    # --- Metadata ---
    meta_el = ET.SubElement(gpx, "metadata")
    ET.SubElement(meta_el, "name").text = f"{mfx.meta.drone_id} — {mfx.meta.date_start}"
    ET.SubElement(meta_el, "desc").text = (
        f"Application: {mfx.meta.application} | "
        f"Status: {mfx.meta.status} | "
        f"Location: {mfx.meta.location}"
    )
    ET.SubElement(meta_el, "time").text = mfx.meta.date_start

    t0_dt = _parse_date_start(mfx.meta.date_start)

    # --- Track ---
    trk = ET.SubElement(gpx, "trk")
    ET.SubElement(trk, "name").text = f"{mfx.meta.drone_id} flight"
    ET.SubElement(trk, "desc").text = f"id: {mfx.meta.id}"
    trkseg = ET.SubElement(trk, "trkseg")

    for p in mfx.trajectory.points:
        if p.lat is None or p.lon is None:
            continue
        trkpt = ET.SubElement(trkseg, "trkpt", {
            "lat": str(p.lat),
            "lon": str(p.lon),
        })
        if p.alt_m is not None:
            ET.SubElement(trkpt, "ele").text = str(p.alt_m)
        if t0_dt is not None and p.t is not None:
            ts = t0_dt + timedelta(seconds=p.t)
            ms = int(p.t * 1000) % 1000
            ET.SubElement(trkpt, "time").text = (
                ts.strftime("%Y-%m-%dT%H:%M:%S") + f".{ms:03d}Z"
            )
        ext_data = {}
        if p.speed_ms is not None:
            ext_data["speed"] = str(p.speed_ms)
        if p.heading is not None:
            ext_data["course"] = str(p.heading)
        if ext_data:
            ext = ET.SubElement(trkpt, "extensions")
            for k, v in ext_data.items():
                ET.SubElement(ext, k).text = v

    # --- Events as waypoints ---
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
            wpt = ET.SubElement(gpx, "wpt", {
                "lat": str(closest.lat),
                "lon": str(closest.lon),
            })
            if closest.alt_m is not None:
                ET.SubElement(wpt, "ele").text = str(closest.alt_m)
            ET.SubElement(wpt, "name").text = e.type or "event"
            ET.SubElement(wpt, "desc").text = (
                f"t={e.t:.3f}s | severity: {e.severity} | {e.detail or ''}"
            )
            ET.SubElement(wpt, "sym").text = "Flag, Blue"

    tree = ET.ElementTree(gpx)
    ET.indent(tree, space="  ")
    buf = io.StringIO()
    buf.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    tree.write(buf, encoding="unicode", xml_declaration=False)
    return buf.getvalue()
