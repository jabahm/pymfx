"""
pymfx.viz.timeline — Events timeline using matplotlib

Renders all flight events on a horizontal timeline, color-coded by severity,
with the full trajectory duration as a background bar.
"""
from __future__ import annotations

try:
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.figure import Figure
except ImportError as e:
    raise ImportError(
        "matplotlib is required for event timelines.\n"
        "Install it with: pip install pymfx[viz]  or  pip install matplotlib"
    ) from e

from ..models import MfxFile


_SEVERITY_COLOR = {
    "info":     "#1a73e8",
    "warning":  "#f9ab00",
    "critical": "#d93025",
}

_EVENT_MARKER = {
    "takeoff":  "▲",
    "landing":  "▼",
    "waypoint": "◆",
    "anomaly":  "✕",
    "rtl":      "↩",
    "abort":    "[X]",
}


def events_timeline(
    mfx: MfxFile,
    figsize: tuple[float, float] | None = None,
    dpi: int = 120,
) -> Figure:
    """
    Render all flight events on a horizontal timeline.

    The full flight duration is shown as a background bar.
    Events are plotted as colored markers, staggered vertically to avoid
    label overlap. Severity is encoded by color (info=blue, warning=amber,
    critical=red).

    Args:
        mfx:     parsed MfxFile
        figsize: (width, height) in inches — auto-computed if None
        dpi:     figure resolution

    Returns:
        matplotlib.figure.Figure

    Example:
        fig = pymfx.viz.events_timeline(mfx)
        fig.savefig("timeline.png", dpi=150)
        plt.show()
    """
    if not mfx.events or not mfx.events.events:
        raise ValueError("No events to display.")

    events = mfx.events.events
    points = mfx.trajectory.points

    # Flight duration from trajectory
    t_start = points[0].t if points else 0.0
    t_end   = points[-1].t if points else max(e.t for e in events)

    if figsize is None:
        width = max(10, (t_end - t_start) / 30 + 4)
        figsize = (width, 3.8)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # --- Background flight bar ---
    ax.barh(
        y=0, left=t_start, width=t_end - t_start,
        height=0.18, color="#e8f0fe", edgecolor="#c5cae9",
        linewidth=0.8, zorder=1, label="_nolegend_",
    )

    # Start / end ticks
    ax.axvline(t_start, color="#34a853", linewidth=1.5, zorder=2)
    ax.axvline(t_end,   color="#ea4335", linewidth=1.5, zorder=2)
    ax.text(t_start, 0.14, " takeoff", fontsize=7.5, color="#34a853", va="bottom")
    ax.text(t_end,   0.14, "landing ", fontsize=7.5, color="#ea4335",
            va="bottom", ha="right")

    # --- Event markers ---
    # Stagger labels vertically to reduce overlap
    # Track last label x-position per "lane"
    lanes = [None, None, None]   # 3 vertical lanes

    for e in events:
        color = _SEVERITY_COLOR.get(e.severity or "info", "#888")
        glyph = _EVENT_MARKER.get(e.type or "", "●")

        ax.plot(
            e.t, 0, marker="o", markersize=9,
            color=color, zorder=5, clip_on=False,
        )

        # Choose the least-crowded lane
        lane_idx = _best_lane(e.t, lanes, min_gap=max((t_end - t_start) / 20, 1.0))
        lane_y   = 0.30 + lane_idx * 0.20

        lanes[lane_idx] = e.t

        label = f"{glyph} {e.type}"
        if e.detail and e.detail not in ("-", "nominal"):
            label += f"\n{e.detail}"

        ax.annotate(
            label,
            xy=(e.t, 0),
            xytext=(e.t, lane_y),
            fontsize=7.5,
            color=color,
            ha="center",
            va="bottom",
            arrowprops=dict(
                arrowstyle="-",
                color=color,
                lw=0.7,
                alpha=0.6,
            ),
            zorder=6,
        )

    # --- Axes styling ---
    ax.set_xlim(t_start - (t_end - t_start) * 0.03,
                t_end   + (t_end - t_start) * 0.03)
    ax.set_ylim(-0.3, 1.0)
    ax.set_yticks([])
    ax.set_xlabel("Time (s)", fontsize=9)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True, nbins=12))

    # --- Legend (severity) ---
    legend_patches = [
        mpatches.Patch(color=c, label=sev.capitalize())
        for sev, c in _SEVERITY_COLOR.items()
        if any(e.severity == sev for e in events)
    ]
    if legend_patches:
        ax.legend(handles=legend_patches, loc="lower right",
                  fontsize=7.5, framealpha=0.7)

    ax.set_title(
        f"Events timeline — {mfx.meta.drone_id}  ·  {len(events)} event(s)  ·  "
        f"{mfx.meta.date_start}",
        fontsize=10,
        fontweight="bold",
        pad=10,
    )

    fig.tight_layout()
    return fig


def _best_lane(t: float, lanes: list, min_gap: float) -> int:
    """Return the index of the least-crowded vertical lane for label placement."""
    for i, last_t in enumerate(lanes):
        if last_t is None or abs(t - last_t) >= min_gap:
            return i
    return 0  # fallback to first lane
