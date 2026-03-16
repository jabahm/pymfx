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

    # Compute checksum for a data[] block
    cs = pymfx.compute_checksum(lines)
"""

from .checksum import compute_checksum, verify_checksum
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
from .validator import ValidationIssue, ValidationResult, validate
from .writer import write

__version__ = "1.0.0"
__all__ = [
    "parse", "ParseError",
    "write",
    "validate", "ValidationResult", "ValidationIssue",
    "compute_checksum", "verify_checksum",
    "MfxFile", "Meta", "Trajectory", "TrajectoryPoint",
    "Events", "Event", "Index", "Extension", "SchemaField",
]
