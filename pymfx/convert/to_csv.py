"""
pymfx.convert.to_csv — Export MfxFile trajectory to CSV

Zero external dependencies (uses stdlib csv).
"""
from __future__ import annotations

import csv
import io

from ..models import MfxFile


def to_csv(mfx: MfxFile, include_events: bool = False) -> str:
    """
    Export MfxFile trajectory points to CSV.

    Column order follows the @schema field order if defined,
    otherwise uses the standard fields (t, lat, lon, alt_m, speed_ms, heading, roll, pitch).

    Args:
        mfx:            parsed MfxFile
        include_events: if True, append events as a second CSV block after a blank line

    Returns:
        CSV string (UTF-8)
    """
    buf = io.StringIO()

    # Determine columns from schema or use defaults
    if mfx.trajectory.schema_fields:
        columns = [f.name for f in mfx.trajectory.schema_fields]
    else:
        columns = ["t", "lat", "lon", "alt_m", "speed_ms", "heading", "roll", "pitch"]

    writer = csv.DictWriter(
        buf, fieldnames=columns, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()

    _std = {"t", "lat", "lon", "alt_m", "speed_ms", "heading", "roll", "pitch"}

    for p in mfx.trajectory.points:
        row: dict = {
            "t":        p.t if p.t is not None else "",
            "lat":      p.lat if p.lat is not None else "",
            "lon":      p.lon if p.lon is not None else "",
            "alt_m":    p.alt_m if p.alt_m is not None else "",
            "speed_ms": p.speed_ms if p.speed_ms is not None else "",
            "heading":  p.heading if p.heading is not None else "",
            "roll":     p.roll if p.roll is not None else "",
            "pitch":    p.pitch if p.pitch is not None else "",
        }
        for k, v in p.extra.items():
            if k in columns:
                row[k] = v
        writer.writerow(row)

    if include_events and mfx.events and mfx.events.events:
        buf.write("\n")
        ev_cols = ["t", "type", "severity", "detail"]
        ev_writer = csv.DictWriter(
            buf, fieldnames=ev_cols, extrasaction="ignore", lineterminator="\n"
        )
        ev_writer.writeheader()
        for e in mfx.events.events:
            ev_writer.writerow({
                "t":        e.t if e.t is not None else "",
                "type":     e.type or "",
                "severity": e.severity or "",
                "detail":   e.detail or "",
            })

    return buf.getvalue()
