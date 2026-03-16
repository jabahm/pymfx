"""
pymfx.models — Dataclasses representing the structure of a .mfx v1.0 file
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Meta:
    id: str
    drone_id: str
    drone_type: str
    pilot_id: str
    date_start: str
    status: str
    application: str
    location: str
    sensors: list[str]
    data_level: str
    license: str
    contact: str

    manufacturer: str | None = None
    date_end: str | None = None
    duration_s: int | None = None
    crs: str = "WGS84"
    altitude_ref: str = "MSL"
    processing_tools: str | None = None
    producer: str | None = None
    producer_version: str | None = None
    source_format: str | None = None
    source_format_detail: str | None = None

    # Extra fields not defined in the official schema
    extra: dict = field(default_factory=dict)


@dataclass
class SchemaField:
    name: str
    type: str
    constraints: list[str] = field(default_factory=list)


@dataclass
class TrajectoryPoint:
    t: float
    lat: float
    lon: float
    alt_m: float | None = None
    speed_ms: float | None = None
    heading: float | None = None
    roll: float | None = None
    pitch: float | None = None
    extra: dict = field(default_factory=dict)  # additional schema fields


@dataclass
class Trajectory:
    frequency_hz: float | None
    schema_fields: list[SchemaField]
    points: list[TrajectoryPoint]
    checksum: str | None = None  # sha256:<hex>
    raw_lines: list[str] = field(default_factory=list)  # raw data lines for checksum


@dataclass
class Event:
    t: float
    type: str | None = None
    severity: str | None = None
    detail: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class Events:
    schema_fields: list[SchemaField]
    events: list[Event]
    checksum: str | None = None
    raw_lines: list[str] = field(default_factory=list)


@dataclass
class Index:
    bbox: tuple[float, float, float, float] | None = None  # lon_min, lat_min, lon_max, lat_max
    anomalies: int | None = None


@dataclass
class Extension:
    name: str  # e.g. "x_weather"
    fields: dict = field(default_factory=dict)


@dataclass
class MfxFile:
    version: str
    encoding: str
    meta: Meta
    trajectory: Trajectory
    events: Events | None = None
    index: Index | None = None
    extensions: list[Extension] = field(default_factory=list)
