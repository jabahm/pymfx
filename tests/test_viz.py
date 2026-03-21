"""Tests for pymfx.viz - trajectory_map, flight_profile, events_timeline"""
import sys
import math
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import matplotlib
import matplotlib.pyplot
matplotlib.use("Agg")  # non-interactive backend for CI


@pytest.fixture(autouse=True)
def close_figures():
    """Close all matplotlib figures after each test to prevent memory leaks."""
    yield
    matplotlib.pyplot.close("all")

from pymfx.models import (
    MfxFile, Meta, Trajectory, TrajectoryPoint, SchemaField,
    Events, Event, Index
)
from pymfx import compute_checksum
from pymfx import viz


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

def _make_mfx(n_points: int = 30, with_events: bool = True,
              with_heading: bool = True) -> MfxFile:
    """Build a minimal but complete MfxFile for viz tests."""
    FREQ = 5
    BASE_LAT, BASE_LON = 43.48, -1.56

    raw_pts = []
    for i in range(n_points):
        t   = round(i / FREQ, 3)
        lat = round(BASE_LAT + i * 0.00004, 6)
        lon = round(BASE_LON + math.sin(i * 0.4) * 0.0002, 6)
        alt = round(40.0 + math.sin(i * 0.3) * 3.0, 1)
        spd = round(7.0  + math.cos(i * 0.2) * 1.0, 1)
        hdg = round((i * 12) % 360, 1)
        raw_pts.append((t, lat, lon, alt, spd, hdg))

    schema_fields = [
        SchemaField("t",        "float",   ["no_null"]),
        SchemaField("lat",      "float",   ["range=-90..90", "no_null"]),
        SchemaField("lon",      "float",   ["range=-180..180", "no_null"]),
        SchemaField("alt_m",    "float32", ["range=0..10000"]),
        SchemaField("speed_ms", "float32", ["range=0..200"]),
    ]
    if with_heading:
        schema_fields.append(SchemaField("heading", "float32", ["range=0..360"]))

    points = [
        TrajectoryPoint(
            t=r[0], lat=r[1], lon=r[2], alt_m=r[3], speed_ms=r[4],
            heading=r[5] if with_heading else None,
        )
        for r in raw_pts
    ]
    if with_heading:
        raw_lines = [f"{r[0]:.3f} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]}" for r in raw_pts]
    else:
        raw_lines = [f"{r[0]:.3f} | {r[1]} | {r[2]} | {r[3]} | {r[4]}" for r in raw_pts]

    event_schema = [
        SchemaField("t",        "float", ["no_null"]),
        SchemaField("type",     "str"),
        SchemaField("severity", "str"),
        SchemaField("detail",   "str"),
    ]
    event_list = [
        Event(t=0.0,                        type="takeoff",  severity="info",    detail="nominal"),
        Event(t=round((n_points//2)/FREQ,3),type="anomaly",  severity="warning", detail="gust"),
        Event(t=round((n_points-1)/FREQ,3), type="landing",  severity="info",    detail="nominal"),
    ]
    ev_raw = [f"{e.t:.3f} | {e.type} | {e.severity} | {e.detail}" for e in event_list]

    lats = [p.lat for p in points]
    lons = [p.lon for p in points]
    bbox = (round(min(lons),6), round(min(lats),6), round(max(lons),6), round(max(lats),6))

    traj = Trajectory(
        frequency_hz=FREQ,
        schema_fields=schema_fields,
        points=points,
        checksum=compute_checksum(raw_lines),
        raw_lines=raw_lines,
    )
    evs = Events(
        schema_fields=event_schema,
        events=event_list if with_events else [],
        checksum=compute_checksum(ev_raw) if with_events else None,
        raw_lines=ev_raw if with_events else [],
    )
    return MfxFile(
        version="1.0",
        encoding="UTF-8",
        meta=Meta(
            id=f"uuid:{uuid.uuid4()}",
            drone_id="Test-Drone-001",
            drone_type="multirotor",
            pilot_id="TEST-PILOT",
            date_start="2026-04-01T09:00:00Z",
            date_end="2026-04-01T09:05:00Z",
            status="complete",
            application="test",
            location="Test Location",
            sensors=["rgb"],
            data_level="raw",
            license="CC-BY-4.0",
            contact="test@test.com",
        ),
        trajectory=traj,
        events=evs if with_events else None,
        index=Index(bbox=bbox, anomalies=1 if with_events else 0),
    )


# ---------------------------------------------------------------------------
# trajectory_map tests
# ---------------------------------------------------------------------------

class TestTrajectoryMap:
    def test_returns_folium_map(self):
        import folium
        mfx = _make_mfx()
        m = viz.trajectory_map(mfx)
        assert isinstance(m, folium.Map)

    def test_map_with_events(self):
        import folium
        mfx = _make_mfx(with_events=True)
        m = viz.trajectory_map(mfx, show_events=True)
        assert isinstance(m, folium.Map)

    def test_map_without_events(self):
        import folium
        mfx = _make_mfx(with_events=False)
        m = viz.trajectory_map(mfx, show_events=False)
        assert isinstance(m, folium.Map)

    def test_map_renders_to_html(self):
        mfx = _make_mfx()
        m = viz.trajectory_map(mfx)
        html = m._repr_html_()
        assert "<html" in html.lower() or "leaflet" in html.lower()

    def test_empty_trajectory_raises(self):
        mfx = _make_mfx()
        mfx.trajectory.points = []
        with pytest.raises(ValueError, match="No trajectory points"):
            viz.trajectory_map(mfx)

    def test_different_tiles(self):
        import folium
        mfx = _make_mfx()
        m = viz.trajectory_map(mfx, tile="CartoDB positron")
        assert isinstance(m, folium.Map)

    def test_save_to_file(self, tmp_path):
        mfx = _make_mfx()
        m = viz.trajectory_map(mfx)
        out = tmp_path / "map.html"
        m.save(str(out))
        assert out.exists()
        assert out.stat().st_size > 1000


# ---------------------------------------------------------------------------
# flight_profile tests
# ---------------------------------------------------------------------------

class TestFlightProfile:
    def test_returns_figure(self):
        from matplotlib.figure import Figure
        mfx = _make_mfx()
        fig = viz.flight_profile(mfx)
        assert isinstance(fig, Figure)

    def test_figure_has_subplots_for_each_channel(self):
        mfx = _make_mfx(with_heading=True)
        fig = viz.flight_profile(mfx)
        # alt + speed + heading = 3 axes
        assert len(fig.axes) == 3

    def test_figure_without_heading(self):
        from matplotlib.figure import Figure
        mfx = _make_mfx(with_heading=False)
        fig = viz.flight_profile(mfx)
        assert isinstance(fig, Figure)
        # alt + speed = 2 axes
        assert len(fig.axes) == 2

    def test_events_overlay(self):
        from matplotlib.figure import Figure
        mfx = _make_mfx(with_events=True)
        fig = viz.flight_profile(mfx, show_events=True)
        assert isinstance(fig, Figure)

    def test_no_events_overlay(self):
        from matplotlib.figure import Figure
        mfx = _make_mfx(with_events=True)
        fig = viz.flight_profile(mfx, show_events=False)
        assert isinstance(fig, Figure)

    def test_empty_trajectory_raises(self):
        mfx = _make_mfx()
        mfx.trajectory.points = []
        with pytest.raises(ValueError, match="No trajectory points"):
            viz.flight_profile(mfx)

    def test_all_none_channels_raises(self):
        mfx = _make_mfx()
        for p in mfx.trajectory.points:
            p.alt_m = None
            p.speed_ms = None
            p.heading = None
            p.roll = None
            p.pitch = None
        with pytest.raises(ValueError, match="No plottable channels"):
            viz.flight_profile(mfx)

    def test_custom_figsize(self):
        mfx = _make_mfx()
        fig = viz.flight_profile(mfx, figsize=(8, 4))
        assert fig.get_size_inches()[0] == pytest.approx(8)

    def test_save_to_file(self, tmp_path):
        mfx = _make_mfx()
        fig = viz.flight_profile(mfx)
        out = tmp_path / "profile.png"
        fig.savefig(str(out))
        assert out.exists()
        assert out.stat().st_size > 5000


# ---------------------------------------------------------------------------
# events_timeline tests
# ---------------------------------------------------------------------------

class TestEventsTimeline:
    def test_returns_figure(self):
        from matplotlib.figure import Figure
        mfx = _make_mfx(with_events=True)
        fig = viz.events_timeline(mfx)
        assert isinstance(fig, Figure)

    def test_no_events_raises(self):
        mfx = _make_mfx(with_events=False)
        with pytest.raises(ValueError, match="No events"):
            viz.events_timeline(mfx)

    def test_empty_events_raises(self):
        mfx = _make_mfx(with_events=True)
        mfx.events.events = []
        with pytest.raises(ValueError, match="No events"):
            viz.events_timeline(mfx)

    def test_single_event(self):
        from matplotlib.figure import Figure
        mfx = _make_mfx(with_events=True)
        mfx.events.events = [Event(t=0.0, type="takeoff", severity="info", detail="nominal")]
        fig = viz.events_timeline(mfx)
        assert isinstance(fig, Figure)

    def test_custom_figsize(self):
        mfx = _make_mfx(with_events=True)
        fig = viz.events_timeline(mfx, figsize=(14, 4))
        assert fig.get_size_inches()[0] == pytest.approx(14)

    def test_save_to_file(self, tmp_path):
        mfx = _make_mfx(with_events=True)
        fig = viz.events_timeline(mfx)
        out = tmp_path / "timeline.png"
        fig.savefig(str(out))
        assert out.exists()
        assert out.stat().st_size > 5000

    def test_all_severity_levels(self):
        from matplotlib.figure import Figure
        mfx = _make_mfx(with_events=True)
        mfx.events.events = [
            Event(t=0.0, type="takeoff",  severity="info",     detail="ok"),
            Event(t=1.0, type="anomaly",  severity="warning",  detail="wind"),
            Event(t=2.0, type="abort",    severity="critical", detail="motor"),
            Event(t=3.0, type="landing",  severity="info",     detail="ok"),
        ]
        fig = viz.events_timeline(mfx)
        assert isinstance(fig, Figure)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
