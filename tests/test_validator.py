"""Tests for pymfx validator — rules V01–V21"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pymfx import parse, validate
from pymfx.checksum import compute_checksum

EXAMPLE = (Path(__file__).parent / "example_minimal.mfx").read_text()


def _valid_mfx():
    """Return a parsed MfxFile with correct checksums."""
    mfx = parse(EXAMPLE)
    mfx.trajectory.checksum = compute_checksum(mfx.trajectory.raw_lines)
    if mfx.events:
        mfx.events.checksum = compute_checksum(mfx.events.raw_lines)
    return mfx


def test_valid_file_has_no_errors():
    mfx = _valid_mfx()
    result = validate(mfx, raw_text=EXAMPLE)
    assert result.is_valid, f"Unexpected errors: {result.errors}"


def test_v01_bad_version():
    mfx = _valid_mfx()
    mfx.version = "bad"
    result = validate(mfx)
    assert any(i.rule == "V01" for i in result.errors)


def test_v01_missing_version():
    mfx = _valid_mfx()
    mfx.version = ""
    result = validate(mfx)
    assert any(i.rule == "V01" for i in result.errors)


def test_v02_bad_trajectory_checksum():
    mfx = _valid_mfx()
    mfx.trajectory.checksum = "sha256:000000"
    result = validate(mfx)
    assert any(i.rule == "V02" for i in result.errors)


def test_v02_no_checksum_is_ok():
    mfx = _valid_mfx()
    mfx.trajectory.checksum = None
    result = validate(mfx)
    assert not any(i.rule == "V02" for i in result.errors)


def test_v06_missing_date_end():
    mfx = _valid_mfx()
    mfx.meta.date_end = None
    result = validate(mfx)
    assert any(i.rule == "V06" for i in result.errors)


def test_v06_date_end_before_start():
    mfx = _valid_mfx()
    mfx.meta.date_end = "2026-03-16T07:00:00Z"
    result = validate(mfx)
    assert any(i.rule == "V06" for i in result.errors)


def test_v07_t_not_strictly_increasing():
    mfx = _valid_mfx()
    mfx.trajectory.points[1].t = 0.0
    mfx.trajectory.raw_lines = [
        "0.000 | 45.7640 | 4.8357 | 0.0 | 0.0",
        "0.000 | 45.7640 | 4.8357 | 1.2 | 1.5",
        "0.400 | 45.7641 | 4.8358 | 4.8 | 4.2",
    ]
    result = validate(mfx)
    assert any(i.rule == "V07" for i in result.errors)


def test_v10_no_null_violation():
    mfx = _valid_mfx()
    mfx.trajectory.raw_lines[0] = "- | 45.7640 | 4.8357 | 0.0 | 0.0"
    result = validate(mfx)
    assert any(i.rule == "V10" for i in result.errors)


def test_v11_range_warning():
    mfx = _valid_mfx()
    mfx.trajectory.raw_lines[0] = "0.000 | 95.0 | 4.8357 | 0.0 | 0.0"
    result = validate(mfx)
    assert any(i.rule == "V11" for i in result.warnings)


def test_v12_enum_warning():
    mfx = _valid_mfx()
    if mfx.events:
        mfx.events.raw_lines[0] = "0.000 | UNKNOWN_TYPE | info | nominal"
        result = validate(mfx)
        assert any(i.rule == "V12" for i in result.warnings)


def test_v14_frequency_too_low():
    mfx = _valid_mfx()
    mfx.trajectory.frequency_hz = 0.5
    result = validate(mfx)
    assert any(i.rule == "V14" for i in result.warnings)


def test_v15_duration_inconsistent():
    mfx = _valid_mfx()
    mfx.meta.duration_s = 9999
    result = validate(mfx)
    assert any(i.rule == "V15" for i in result.warnings)


def test_v16_invalid_uuid():
    mfx = _valid_mfx()
    mfx.meta.id = "uuid:not-a-uuid"
    result = validate(mfx)
    assert any(i.rule == "V16" for i in result.warnings)


def test_v19_anomalies_mismatch():
    mfx = _valid_mfx()
    if mfx.index and mfx.events:
        mfx.index.anomalies = 99
        result = validate(mfx)
        assert any(i.rule == "V19" for i in result.warnings)


def test_v20_source_format_other_no_detail():
    mfx = _valid_mfx()
    mfx.meta.source_format = "other"
    mfx.meta.source_format_detail = None
    result = validate(mfx)
    assert any(i.rule == "V20" for i in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
