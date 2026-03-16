"""Tests for pymfx parser"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pymfx import parse, ParseError
from pymfx.models import MfxFile

EXAMPLE = (Path(__file__).parent / "example_minimal.mfx").read_text()


def test_parse_returns_mfxfile():
    mfx = parse(EXAMPLE)
    assert isinstance(mfx, MfxFile)


def test_version():
    mfx = parse(EXAMPLE)
    assert mfx.version == "1.0"


def test_meta_required_fields():
    mfx = parse(EXAMPLE)
    assert mfx.meta.id == "uuid:550e8400-e29b-41d4-a716-446655440000"
    assert mfx.meta.drone_id == "Parrot-Anafi-SN987654"
    assert mfx.meta.drone_type == "multirotor"
    assert mfx.meta.pilot_id == "FR-PILOT-0099"
    assert mfx.meta.status == "complete"
    assert mfx.meta.license == "CC-BY-4.0"
    assert mfx.meta.contact == "pilot@lab.fr"


def test_meta_sensors_is_list():
    mfx = parse(EXAMPLE)
    assert isinstance(mfx.meta.sensors, list)
    assert "rgb" in mfx.meta.sensors


def test_trajectory_points():
    mfx = parse(EXAMPLE)
    assert len(mfx.trajectory.points) == 3
    p0 = mfx.trajectory.points[0]
    assert p0.t == 0.0
    assert p0.lat == pytest.approx(45.7640)
    assert p0.lon == pytest.approx(4.8357)
    assert p0.alt_m == pytest.approx(0.0)


def test_trajectory_frequency():
    mfx = parse(EXAMPLE)
    assert mfx.trajectory.frequency_hz == 5.0


def test_events_parsed():
    mfx = parse(EXAMPLE)
    assert mfx.events is not None
    assert len(mfx.events.events) == 2
    assert mfx.events.events[0].type == "takeoff"
    assert mfx.events.events[1].type == "landing"


def test_index_parsed():
    mfx = parse(EXAMPLE)
    assert mfx.index is not None
    assert mfx.index.anomalies == 0
    assert len(mfx.index.bbox) == 4


def test_parse_error_no_header():
    with pytest.raises(ParseError):
        parse("[meta]\nid: test")


def test_parse_error_missing_meta():
    with pytest.raises(ParseError):
        parse("@mfx 1.0\n[trajectory]\nfrequency_hz: 1\n@schema point: {t:float}\ndata[]:\n0.000")


def test_t_values_are_floats():
    mfx = parse(EXAMPLE)
    for p in mfx.trajectory.points:
        assert isinstance(p.t, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
