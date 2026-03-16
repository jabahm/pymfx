"""
pymfx.convert.to_kml — Export MfxFile to KML (Google Earth compatible)

Zero external dependencies (uses stdlib xml.etree.ElementTree).
"""
from __future__ import annotations

import io
import xml.etree.ElementTree as ET

from ..models import MfxFile

_KML_NS = "http://www.opengis.net/kml/2.2"

# Severity → KML icon color (AABBGGRR)
_SEVERITY_COLOR = {
    "info":     "ffebb434",   # blue
    "warning":  "ff0088ff",   # orange
    "critical": "ff0000ff",   # red
}


def to_kml(mfx: MfxFile) -> str:
    """
    Export a MfxFile to KML format (Google Earth compatible).

    The trajectory is exported as a LineString Placemark.
    Events are exported as Point Placemarks in a Folder.

    Returns:
        KML XML string (UTF-8)
    """
    ET.register_namespace("", _KML_NS)

    kml = ET.Element("kml", {"xmlns": _KML_NS})
    doc = ET.SubElement(kml, "Document")
    ET.SubElement(doc, "name").text = f"{mfx.meta.drone_id} — {mfx.meta.date_start}"
    ET.SubElement(doc, "description").text = (
        f"Location: {mfx.meta.location}\n"
        f"Application: {mfx.meta.application}\n"
        f"Status: {mfx.meta.status}\n"
        f"Pilot: {mfx.meta.pilot_id}\n"
        f"ID: {mfx.meta.id}"
    )

    # --- Trajectory style ---
    style = ET.SubElement(doc, "Style", {"id": "trajStyle"})
    ls = ET.SubElement(style, "LineStyle")
    ET.SubElement(ls, "color").text = "ffeb7a1a"  # blue-ish
    ET.SubElement(ls, "width").text = "3"

    # --- Trajectory LineString ---
    pm = ET.SubElement(doc, "Placemark")
    ET.SubElement(pm, "name").text = "Trajectory"
    ET.SubElement(pm, "styleUrl").text = "#trajStyle"
    line = ET.SubElement(pm, "LineString")
    ET.SubElement(line, "altitudeMode").text = "absolute"
    ET.SubElement(line, "tessellate").text = "1"

    coord_parts: list[str] = []
    for p in mfx.trajectory.points:
        if p.lat is None or p.lon is None:
            continue
        alt = p.alt_m if p.alt_m is not None else 0
        coord_parts.append(f"{p.lon},{p.lat},{alt}")
    ET.SubElement(line, "coordinates").text = " ".join(coord_parts)

    # --- Events as Placemarks ---
    if mfx.events:
        folder = ET.SubElement(doc, "Folder")
        ET.SubElement(folder, "name").text = "Events"

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

            # Per-event style
            sev = e.severity or "info"
            color = _SEVERITY_COLOR.get(sev, "ffebb434")
            ev_style_id = f"evStyle_{sev}"
            if doc.find(f"Style[@id='{ev_style_id}']") is None:
                ev_style = ET.SubElement(doc, "Style", {"id": ev_style_id})
                icon_style = ET.SubElement(ev_style, "IconStyle")
                ET.SubElement(icon_style, "color").text = color
                icon = ET.SubElement(icon_style, "Icon")
                ET.SubElement(icon, "href").text = (
                    "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
                )

            e_pm = ET.SubElement(folder, "Placemark")
            ET.SubElement(e_pm, "name").text = f"{e.type or 'event'} @ t={e.t:.1f}s"
            ET.SubElement(e_pm, "styleUrl").text = f"#{ev_style_id}"
            ET.SubElement(e_pm, "description").text = (
                f"Time: {e.t:.3f}s\n"
                f"Type: {e.type}\n"
                f"Severity: {e.severity}\n"
                f"Detail: {e.detail or '-'}"
            )
            pt = ET.SubElement(e_pm, "Point")
            alt = closest.alt_m if closest.alt_m is not None else 0
            ET.SubElement(pt, "coordinates").text = f"{closest.lon},{closest.lat},{alt}"

    tree = ET.ElementTree(kml)
    ET.indent(tree, space="  ")
    buf = io.StringIO()
    buf.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    tree.write(buf, encoding="unicode", xml_declaration=False)
    return buf.getvalue()
