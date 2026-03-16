"""
pymfx.viz.map — Interactive trajectory map using folium

Renders the GPS trace of a .mfx flight on an interactive Leaflet map.
Points are color-graded from green (start) to red (end).
Events are shown as markers with popups.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import MfxFile

if TYPE_CHECKING:
    import folium

# Severity colors for event markers
_SEVERITY_COLOR = {
    "info":     "blue",
    "warning":  "orange",
    "critical": "red",
}

# Event type icons (Font Awesome subset supported by folium)
_EVENT_ICON = {
    "takeoff":  "plane",
    "landing":  "plane",
    "waypoint": "map-marker",
    "anomaly":  "exclamation-triangle",
    "rtl":      "undo",
    "abort":    "stop",
}


def _gradient_color(i: int, total: int) -> str:
    """Return a hex color interpolated from green → yellow → red."""
    ratio = i / max(total - 1, 1)
    if ratio < 0.5:
        r = int(255 * ratio * 2)
        g = 200
    else:
        r = 200
        g = int(200 * (1 - (ratio - 0.5) * 2))
    return f"#{r:02x}{g:02x}40"


def trajectory_map(
    mfx: MfxFile,
    tile: str = "OpenStreetMap",
    line_weight: int = 3,
    show_points: bool = True,
    show_events: bool = True,
) -> folium.Map:
    """
    Build an interactive Leaflet map of the flight trajectory.

    Args:
        mfx:          parsed MfxFile
        tile:         map tile provider ("OpenStreetMap", "CartoDB positron", ...)
        line_weight:  width of the trajectory line in pixels
        show_points:  draw a small circle at each trajectory point
        show_events:  draw event markers with popups

    Returns:
        folium.Map — call .save("map.html") or display in Jupyter with display(m)

    Example:
        m = pymfx.viz.trajectory_map(mfx)
        m.save("flight.html")
    """
    try:
        import folium
    except ImportError as exc:
        raise ImportError(
            "folium is required for trajectory maps.\n"
            "Install it with: pip install pymfx[viz]  or  pip install folium"
        ) from exc

    points = mfx.trajectory.points
    if not points:
        raise ValueError("No trajectory points to display.")

    coords = [(p.lat, p.lon) for p in points if p.lat is not None and p.lon is not None]
    if not coords:
        raise ValueError("Trajectory points have no valid lat/lon values.")

    # Center map on the mean position
    center_lat = sum(c[0] for c in coords) / len(coords)
    center_lon = sum(c[1] for c in coords) / len(coords)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles=tile)

    # --- Trajectory line ---
    folium.PolyLine(
        locations=coords,
        color="#1a73e8",
        weight=line_weight,
        opacity=0.85,
        tooltip=f"{mfx.meta.drone_id} — {len(coords)} points",
    ).add_to(m)

    # --- Start / end markers ---
    folium.Marker(
        location=coords[0],
        tooltip="Start — t=0s",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(m)

    folium.Marker(
        location=coords[-1],
        tooltip=f"End — t={points[-1].t:.1f}s",
        icon=folium.Icon(color="red", icon="stop", prefix="fa"),
    ).add_to(m)

    # --- Individual trajectory points ---
    if show_points:
        for i, p in enumerate(points):
            if p.lat is None or p.lon is None:
                continue
            parts = [f"t = {p.t:.3f}s", f"lat = {p.lat}", f"lon = {p.lon}"]
            if p.alt_m is not None:
                parts.append(f"alt = {p.alt_m}m")
            if p.speed_ms is not None:
                parts.append(f"speed = {p.speed_ms}m/s")
            folium.CircleMarker(
                location=(p.lat, p.lon),
                radius=3,
                color=_gradient_color(i, len(points)),
                fill=True,
                fill_opacity=0.7,
                tooltip="<br>".join(parts),
            ).add_to(m)

    # --- Event markers ---
    if show_events and mfx.events:
        for e in mfx.events.events:
            if e.t is None:
                continue
            # Find the closest trajectory point by time (skip points with no lat or t)
            closest = min(
                (p for p in points if p.lat is not None and p.t is not None),
                key=lambda p: abs(p.t - e.t),  # type: ignore[operator]
                default=None,
            )
            if closest is None:
                continue

            color = _SEVERITY_COLOR.get(e.severity or "info", "blue")
            icon_name = _EVENT_ICON.get(e.type or "", "info-circle")

            popup_html = (
                f"<b>{e.type}</b><br>"
                f"t = {e.t:.3f}s<br>"
                f"severity = {e.severity}<br>"
                f"detail = {e.detail}"
            )

            folium.Marker(
                location=(closest.lat, closest.lon),
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"{e.type} @ t={e.t:.1f}s",
                icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
            ).add_to(m)

    # --- Bounding box from index ---
    if mfx.index and mfx.index.bbox:
        lon_min, lat_min, lon_max, lat_max = mfx.index.bbox
        folium.Rectangle(
            bounds=[[lat_min, lon_min], [lat_max, lon_max]],
            color="#555",
            weight=1,
            dash_array="6",
            fill=False,
            tooltip="Bounding box",
        ).add_to(m)

    # --- Fit map to trajectory bounds ---
    m.fit_bounds([[min(c[0] for c in coords), min(c[1] for c in coords)],
                  [max(c[0] for c in coords), max(c[1] for c in coords)]])

    return m
