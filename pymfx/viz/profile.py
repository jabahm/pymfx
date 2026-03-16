"""
pymfx.viz.profile — Flight profile plots using matplotlib

Renders altitude, speed and heading as a function of time (t in seconds).
Each available channel gets its own subplot. Missing data (None values) are
rendered as gaps rather than zero.
"""
from __future__ import annotations

try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    from matplotlib.figure import Figure
except ImportError as e:
    raise ImportError(
        "matplotlib is required for flight profiles.\n"
        "Install it with: pip install pymfx[viz]  or  pip install matplotlib"
    ) from e

from ..models import MfxFile

# Default style constants
_LINE_COLOR   = "#1a73e8"
_FILL_ALPHA   = 0.12
_GRID_ALPHA   = 0.3
_FONT_TITLE   = 12
_FONT_LABEL   = 9


def flight_profile(
    mfx: MfxFile,
    figsize: tuple[float, float] | None = None,
    dpi: int = 120,
    show_events: bool = True,
) -> Figure:
    """
    Plot altitude, speed and heading over time.

    Only channels that have at least one non-None value are rendered.
    Events are overlaid as vertical lines with labels.

    Args:
        mfx:          parsed MfxFile
        figsize:      (width, height) in inches — auto-computed if None
        dpi:          figure resolution
        show_events:  overlay event markers as vertical dashed lines

    Returns:
        matplotlib.figure.Figure

    Example:
        fig = pymfx.viz.flight_profile(mfx)
        fig.savefig("profile.png", dpi=150)
        plt.show()
    """
    points = mfx.trajectory.points
    if not points:
        raise ValueError("No trajectory points to display.")

    t = [p.t for p in points]

    # Build channel list — only include channels with data
    channels = []
    alt    = [p.alt_m    for p in points]
    speed  = [p.speed_ms for p in points]
    head   = [p.heading  for p in points]
    roll   = [p.roll     for p in points]
    pitch  = [p.pitch    for p in points]

    if any(v is not None for v in alt):
        channels.append(("Altitude (m)",      alt,   "#1a73e8", "m"))
    if any(v is not None for v in speed):
        channels.append(("Speed (m/s)",       speed, "#34a853", "m/s"))
    if any(v is not None for v in head):
        channels.append(("Heading (°)",       head,  "#fbbc04", "°"))
    if any(v is not None for v in roll):
        channels.append(("Roll (°)",          roll,  "#ea4335", "°"))
    if any(v is not None for v in pitch):
        channels.append(("Pitch (°)",         pitch, "#9c27b0", "°"))

    if not channels:
        raise ValueError(
            "No plottable channels found (alt_m, speed_ms, heading, roll, pitch all None)."
        )

    n = len(channels)
    if figsize is None:
        figsize = (12, 2.8 * n)

    fig, axes = plt.subplots(n, 1, figsize=figsize, dpi=dpi, sharex=True)
    if n == 1:
        axes = [axes]

    fig.suptitle(
        f"{mfx.meta.drone_id}  ·  {mfx.meta.date_start}  ·  {mfx.meta.location}",
        fontsize=_FONT_TITLE,
        fontweight="bold",
        y=1.01,
    )

    # Event vertical lines
    event_data = []
    if show_events and mfx.events:
        for e in mfx.events.events:
            event_data.append(e)

    _SEVERITY_STYLE = {
        "info":     ("#1565c0", "--", 0.6),
        "warning":  ("#e65100", "-.", 0.8),
        "critical": ("#b71c1c", "-",  1.0),
    }

    for ax, (label, values, color, unit) in zip(axes, channels):
        # Replace None with float("nan") for clean gaps
        y = [float("nan") if v is None else v for v in values]

        ax.plot(t, y, color=color, linewidth=1.4, zorder=3)
        ax.fill_between(t, y, alpha=_FILL_ALPHA, color=color, zorder=2)

        ax.set_ylabel(label, fontsize=_FONT_LABEL)
        ax.grid(True, alpha=_GRID_ALPHA, linestyle=":")
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
        ax.spines[["top", "right"]].set_visible(False)

        # Overlay events
        for e in event_data:
            sev = e.severity or "info"
            ec, ls, alpha = _SEVERITY_STYLE.get(sev, ("#555", "--", 0.5))
            ax.axvline(x=e.t, color=ec, linestyle=ls, linewidth=0.9,
                       alpha=alpha, zorder=4)

    # Event labels on top axes only
    if event_data:
        ax_top = axes[0]
        ylim = ax_top.get_ylim()
        label_y = ylim[1] - (ylim[1] - ylim[0]) * 0.05
        for e in event_data:
            sev = e.severity or "info"
            ec, _, _ = _SEVERITY_STYLE.get(sev, ("#555", "--", 0.5))
            ax_top.text(
                e.t, label_y,
                f" {e.type}",
                fontsize=7,
                color=ec,
                rotation=90,
                va="top",
                ha="left",
                zorder=5,
            )

    axes[-1].set_xlabel("Time (s)", fontsize=_FONT_LABEL)

    # Duration annotation
    total_t = t[-1] - t[0]
    axes[-1].annotate(
        f"Duration: {total_t:.1f}s   |   {len(points)} points   |   "
        f"{mfx.trajectory.frequency_hz or '?'} Hz",
        xy=(0.01, -0.28),
        xycoords="axes fraction",
        fontsize=7,
        color="#777",
    )

    fig.tight_layout()
    return fig
