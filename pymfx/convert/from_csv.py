"""
pymfx.convert.from_csv — Import CSV to MfxFile

Zero external dependencies (uses stdlib csv).
Column names are configurable to handle various CSV conventions.
"""
from __future__ import annotations

import csv
import io
import uuid
from pathlib import Path

from ..models import Meta, MfxFile, SchemaField, Trajectory, TrajectoryPoint


def from_csv(
    source: str | Path,
    lat_col: str = "lat",
    lon_col: str = "lon",
    alt_col: str = "alt_m",
    t_col: str = "t",
    speed_col: str = "speed_ms",
    heading_col: str = "heading",
    roll_col: str = "roll",
    pitch_col: str = "pitch",
    frequency_hz: float | None = None,
    delimiter: str = ",",
) -> MfxFile:
    """
    Import a CSV file and convert it to MfxFile.

    Each row becomes a TrajectoryPoint. If no ``t`` column is present,
    a synthetic time axis (0, 1, 2, …) is used.

    Args:
        source:       path to a CSV file (str or Path), or raw CSV string
        lat_col:      column name for latitude (required)
        lon_col:      column name for longitude (required)
        alt_col:      column name for altitude in metres (optional)
        t_col:        column name for time in seconds (optional)
        speed_col:    column name for speed in m/s (optional)
        heading_col:  column name for heading in degrees (optional)
        roll_col:     column name for roll in degrees (optional)
        pitch_col:    column name for pitch in degrees (optional)
        frequency_hz: declared sampling frequency (auto-detected if None)
        delimiter:    CSV delimiter character (default: comma)

    Returns:
        MfxFile — fill in meta fields (drone_id, pilot_id, etc.) after import
    """
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    elif isinstance(source, str) and "\n" not in source and Path(source).exists():
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = source

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)

    if not rows:
        raise ValueError("CSV has no data rows")

    cols = set(reader.fieldnames or [])
    has_t       = t_col       in cols
    has_alt     = alt_col     in cols
    has_speed   = speed_col   in cols
    has_heading = heading_col in cols
    has_roll    = roll_col    in cols
    has_pitch   = pitch_col   in cols

    known = {lat_col, lon_col, alt_col, t_col, speed_col,
             heading_col, roll_col, pitch_col}

    points: list[TrajectoryPoint] = []
    raw_lines: list[str] = []

    for i, row in enumerate(rows):
        try:
            lat = float(row[lat_col])
            lon = float(row[lon_col])
        except (KeyError, ValueError):
            continue  # skip rows without valid lat/lon

        def _f(col: str, present: bool) -> float | None:
            if not present:
                return None
            v = row.get(col, "").strip()
            if not v or v == "-":
                return None
            try:
                return float(v)
            except ValueError:
                return None

        t        = _f(t_col,       has_t)       if has_t       else float(i)
        if t is None:
            t = float(i)
        alt_m   = _f(alt_col,     has_alt)
        speed_ms = _f(speed_col,   has_speed)
        heading  = _f(heading_col, has_heading)
        roll     = _f(roll_col,    has_roll)
        pitch    = _f(pitch_col,   has_pitch)

        # Any extra columns become the point's extra dict
        extra: dict = {}
        for k, v in row.items():
            if k not in known and v and v.strip():
                try:
                    extra[k] = float(v)
                except ValueError:
                    extra[k] = v

        p = TrajectoryPoint(
            t=round(t, 3), lat=lat, lon=lon,
            alt_m=alt_m, speed_ms=speed_ms,
            heading=heading, roll=roll, pitch=pitch,
            extra=extra,
        )
        points.append(p)

        vals = [f"{t:.3f}", str(lat), str(lon)]
        if has_alt:
            vals.append(str(alt_m) if alt_m is not None else "-")
        raw_lines.append(" | ".join(vals))

    if not points:
        raise ValueError(
            f"No valid rows found. Check that columns '{lat_col}' and '{lon_col}' exist."
        )

    # --- Schema fields ---
    schema_fields = [
        SchemaField("t",   "float", ["no_null"]),
        SchemaField("lat", "float", ["no_null", "range=-90..90"]),
        SchemaField("lon", "float", ["no_null", "range=-180..180"]),
    ]
    if has_alt:
        schema_fields.append(SchemaField("alt_m",    "float"))
    if has_speed:
        schema_fields.append(SchemaField("speed_ms", "float"))
    if has_heading:
        schema_fields.append(SchemaField("heading",  "float", ["range=0..360"]))
    if has_roll:
        schema_fields.append(SchemaField("roll",     "float"))
    if has_pitch:
        schema_fields.append(SchemaField("pitch",    "float"))

    # --- Auto-detect frequency ---
    if frequency_hz is None and len(points) >= 2:
        total_t = points[-1].t - points[0].t
        if total_t > 0:
            frequency_hz = round((len(points) - 1) / total_t, 2)

    meta = Meta(
        id=f"uuid:{uuid.uuid4()}",
        drone_id="unknown",
        drone_type="unknown",
        pilot_id="unknown",
        date_start="1970-01-01T00:00:00Z",
        status="complete",
        application="unknown",
        location="unknown",
        sensors=[],
        data_level="raw",
        license="unknown",
        contact="unknown",
        source_format="csv",
    )

    trajectory = Trajectory(
        frequency_hz=frequency_hz,
        schema_fields=schema_fields,
        points=points,
        raw_lines=raw_lines,
    )

    return MfxFile(
        version="1.0",
        encoding="UTF-8",
        meta=meta,
        trajectory=trajectory,
    )
