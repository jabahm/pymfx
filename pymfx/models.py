"""
pymfx.models — Dataclasses representing the structure of a .mfx v1.0 file
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


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

    manufacturer: Optional[str] = None
    date_end: Optional[str] = None
    duration_s: Optional[int] = None
    crs: str = "WGS84"
    altitude_ref: str = "MSL"
    processing_tools: Optional[str] = None
    producer: Optional[str] = None
    producer_version: Optional[str] = None
    source_format: Optional[str] = None
    source_format_detail: Optional[str] = None

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
    alt_m: Optional[float] = None
    speed_ms: Optional[float] = None
    heading: Optional[float] = None
    roll: Optional[float] = None
    pitch: Optional[float] = None
    extra: dict = field(default_factory=dict)  # additional schema fields


@dataclass
class Trajectory:
    frequency_hz: Optional[float]
    schema_fields: list[SchemaField]
    points: list[TrajectoryPoint]
    checksum: Optional[str] = None  # sha256:<hex>
    raw_lines: list[str] = field(default_factory=list)  # raw data lines for checksum


@dataclass
class Event:
    t: float
    type: Optional[str] = None
    severity: Optional[str] = None
    detail: Optional[str] = None
    extra: dict = field(default_factory=dict)


@dataclass
class Events:
    schema_fields: list[SchemaField]
    events: list[Event]
    checksum: Optional[str] = None
    raw_lines: list[str] = field(default_factory=list)


@dataclass
class Index:
    bbox: Optional[tuple[float, float, float, float]] = None  # lon_min, lat_min, lon_max, lat_max
    anomalies: Optional[int] = None


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
    events: Optional[Events] = None
    index: Optional[Index] = None
    extensions: list[Extension] = field(default_factory=list)
