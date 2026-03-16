"""Tests for pymfx writer"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pymfx import parse, write, validate
from pymfx.checksum import compute_checksum

EXAMPLE = (Path(__file__).parent / "example_minimal.mfx").read_text()


def test_write_produces_string():
    mfx = parse(EXAMPLE)
    out = write(mfx)
    assert isinstance(out, str)
    assert len(out) > 0


def test_write_starts_with_mfx_header():
    mfx = parse(EXAMPLE)
    out = write(mfx)
    assert out.startswith("@mfx 1.0")


def test_write_contains_all_sections():
    mfx = parse(EXAMPLE)
    out = write(mfx)
    assert "[meta]" in out
    assert "[trajectory]" in out
    assert "[events]" in out
    assert "[index]" in out


def test_roundtrip_parse_write_parse():
    """parse → write → parse should produce identical content."""
    mfx1 = parse(EXAMPLE)
    out = write(mfx1)
    mfx2 = parse(out)

    assert mfx2.version == mfx1.version
    assert mfx2.meta.id == mfx1.meta.id
    assert mfx2.meta.drone_id == mfx1.meta.drone_id
    assert len(mfx2.trajectory.points) == len(mfx1.trajectory.points)
    assert mfx2.trajectory.points[0].t == mfx1.trajectory.points[0].t
    assert mfx2.trajectory.points[0].lat == pytest.approx(mfx1.trajectory.points[0].lat)


def test_write_computes_valid_checksum():
    """Checksums computed by write() must be valid when re-read."""
    mfx = parse(EXAMPLE)
    out = write(mfx, compute_checksums=True)
    mfx2 = parse(out)
    result = validate(mfx2, raw_text=out)
    assert not any(i.rule in ("V02", "V03") for i in result.errors), \
        f"Invalid checksum after write: {result.errors}"


def test_write_index_last():
    """[index] must be the last section."""
    mfx = parse(EXAMPLE)
    out = write(mfx)
    idx_pos = out.rfind("[index]")
    after = out[idx_pos + len("[index]"):]
    import re
    assert not re.search(r'^\[(?!index\])\w', after, re.MULTILINE), \
        "[index] is not the last section"


def test_write_without_checksums():
    mfx = parse(EXAMPLE)
    mfx.trajectory.checksum = None
    out = write(mfx, compute_checksums=False)
    assert "@checksum" not in out


def test_write_extension():
    from pymfx.models import Extension
    mfx = parse(EXAMPLE)
    mfx.extensions.append(Extension(name="x_weather", fields={"wind_ms": 3.2, "temperature_c": 18.5}))
    out = write(mfx)
    assert "[x_weather]" in out
    assert "wind_ms" in out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
