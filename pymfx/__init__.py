"""
pymfx — Python library for the Mission Flight Exchange (.mfx) v1.0 format

Quick start:

    import pymfx

    # Read a file
    mfx = pymfx.parse("mission.mfx")

    # Validate
    result = pymfx.validate(mfx)
    print(result)

    # Write
    pymfx.write(mfx, "out.mfx")

    # Convert
    geojson = pymfx.convert.to_geojson(mfx)
    mfx2    = pymfx.convert.from_gpx("flight.gpx")

    # Flight statistics
    stats = pymfx.flight_stats(mfx)
    print(stats)

    # Data science
    df = mfx.trajectory.to_dataframe()   # pandas DataFrame
    d  = mfx.to_dict()                   # plain dict
    js = mfx.to_json()                   # JSON string

    # Utilities
    mfx.index = pymfx.generate_index(mfx)  # compute bbox + anomaly count
    combined  = pymfx.merge(leg1, leg2)    # concatenate two flights
    delta     = pymfx.diff(mfx1, mfx2)    # compare two flights
    print(delta)

    # FAIR compliance scoring (Section 5 of the .mfx paper)
    score = pymfx.fair_score(mfx)         # uniform weights α=β=γ=δ=¼
    print(score.S)                         # composite score in [0, 1]
    print(score.breakdown())               # per-criterion detail table
    # Custom weights:
    score = pymfx.fair_score(mfx, alpha=0.4, beta=0.2, gamma=0.2, delta=0.2)
"""

from . import convert
from .checksum import compute_checksum, verify_checksum
from .fair import FairScore, fair_score
from .models import (
    Event,
    Events,
    Extension,
    Index,
    Meta,
    MfxFile,
    SchemaField,
    Trajectory,
    TrajectoryPoint,
)
from .parser import ParseError, parse
from .stats import FlightStats, flight_stats
from .utils import DiffResult, diff, generate_index, merge
from .validator import ValidationIssue, ValidationResult, validate
from .writer import write

__version__ = "1.0.0"
__all__ = [
    "parse", "ParseError",
    "write",
    "validate", "ValidationResult", "ValidationIssue",
    "compute_checksum", "verify_checksum",
    "convert",
    "flight_stats", "FlightStats",
    "generate_index", "merge", "diff", "DiffResult",
    "fair_score", "FairScore",
    "MfxFile", "Meta", "Trajectory", "TrajectoryPoint",
    "Events", "Event", "Index", "Extension", "SchemaField",
]
