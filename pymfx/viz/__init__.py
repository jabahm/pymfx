"""
pymfx.viz — Optional visualization module for .mfx files

Requires: folium, matplotlib
Install:  pip install pymfx[viz]

Functions:
    trajectory_map(mfx)     → folium.Map  — interactive GPS trace
    flight_profile(mfx)     → matplotlib Figure — altitude / speed / heading over time
    events_timeline(mfx)    → matplotlib Figure — events on the flight timeline
"""

from .map import trajectory_map
from .profile import flight_profile
from .timeline import events_timeline

__all__ = ["trajectory_map", "flight_profile", "events_timeline"]
