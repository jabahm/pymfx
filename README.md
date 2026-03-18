# pymfx

[![CI](https://github.com/jabahm/pymfx/actions/workflows/ci.yml/badge.svg)](https://github.com/jabahm/pymfx/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pymfx)](https://pypi.org/project/pymfx/)
[![Coverage](https://codecov.io/gh/jabahm/pymfx/branch/main/graph/badge.svg)](https://codecov.io/gh/jabahm/pymfx)
[![Docs](https://img.shields.io/badge/docs-jabahm.github.io/pymfx-blue)](https://jabahm.github.io/pymfx)

Python library for the **Mission Flight Exchange** (`.mfx`) format — an open plain-text format for UAV mission data designed for FAIR compliance.

```bash
pip install pymfx
pip install pymfx[viz]   # maps + plots
pip install pymfx[ds]    # pandas
```

## Usage

```python
import pymfx

mfx = pymfx.parse("flight.mfx")
pymfx.validate(mfx)
pymfx.write(mfx, "out.mfx")

# Convert
pymfx.convert.to_geojson(mfx)
pymfx.convert.to_gpx(mfx)

# Stats
print(pymfx.flight_stats(mfx))

# FAIR score
score = pymfx.fair_score(mfx)
print(score.S)             # composite score in [0, 1]
print(score.breakdown())

# DataFrame (requires pandas)
df = mfx.trajectory.to_dataframe(events=mfx.events)

# Viz (requires folium + matplotlib)
import pymfx.viz as viz
viz.trajectory_map(mfx)
viz.flight_profile(mfx)
viz.flight_3d(mfx, color_by="speed")
```

## CLI

```bash
pymfx flight.mfx --validate
pymfx flight.mfx --stats
pymfx flight.mfx --export geojson -o out.geojson
pymfx flight.mfx --diff other.mfx
```

## License

MIT · Format spec: CC BY 4.0
