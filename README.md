# pymfx

Python reference library for the **Mission Flight Exchange** (`.mfx`) v1.0 format.

> `.mfx` is an open, text-based, self-describing format for encapsulating UAV mission data in a single file.
> It is to drone missions what GPX is to GPS tracks: a minimal, immediately adoptable, community-extensible standard.

---

## Installation

```bash
pip install pymfx
```

With optional extras:

```bash
pip install pymfx[viz]        # folium + matplotlib (maps & 3-D plots)
pip install pymfx[ds]         # pandas (DataFrame export)
pip install pymfx[notebooks]  # all extras + jupyter
```

Or from source:

```bash
git clone https://github.com/jabahm/pymfx
cd pymfx
pip install -e .
```

**Requirements:** Python ≥ 3.10, no mandatory external dependencies.

---

## Quick start

```python
import pymfx

# Read a file
mfx = pymfx.parse("mission.mfx")

print(mfx.meta.drone_id)            # "Parrot-Anafi-SN987654"
print(mfx.meta.date_start)          # "2026-03-16T08:30:00Z"
print(len(mfx.trajectory.points))   # 3

for point in mfx.trajectory.points:
    print(point.t, point.lat, point.lon, point.alt_m)

# Validate
result = pymfx.validate(mfx)
if result.is_valid:
    print("✓ Valid file")
else:
    for issue in result.issues:
        print(issue)

# Write (checksums are auto-computed)
mfx.meta.contact = "new@lab.fr"
pymfx.write(mfx, "mission_v2.mfx")
```

---

## Features

### Parse / Write / Validate

```python
import pymfx

mfx   = pymfx.parse("flight.mfx")    # accepts str path, Path, or raw text
valid = pymfx.validate(mfx)           # ValidationResult with .is_valid / .issues
pymfx.write(mfx, "out.mfx")          # SHA-256 checksums auto-computed
```

### Format conversion

Export `.mfx` data to widely-used geospatial formats:

```python
geojson_str = pymfx.to_geojson(mfx)
gpx_str     = pymfx.to_gpx(mfx)
kml_str     = pymfx.to_kml(mfx)
csv_str     = pymfx.to_csv(mfx)

# Save directly to a file via the CLI (see below)
```

### Flight statistics

Aggregated metrics computed in pure Python (no extra dependencies):

```python
stats = pymfx.flight_stats(mfx)

print(stats.duration_s)          # e.g. 300.0
print(stats.total_distance_km)   # e.g. 1.245
print(stats.alt_max_m)           # e.g. 102.3
print(stats.speed_max_ms)        # e.g. 8.5
print(stats)                     # pretty-printed summary table
```

`FlightStats` fields: `point_count`, `duration_s`, `total_distance_m`, `total_distance_km`,
`alt_max_m`, `alt_min_m`, `alt_mean_m`, `speed_max_ms`, `speed_mean_ms`.

### Data science — pandas / JSON export

```python
# pandas DataFrame (requires: pip install pymfx[ds])
df = mfx.trajectory.to_dataframe()

# Nearest-time merge: events appear as extra columns alongside trajectory rows
df_with_events = mfx.trajectory.to_dataframe(events=mfx.events)

# Serialise the whole file to a plain dict or JSON string
d    = mfx.to_dict()
json = mfx.to_json(indent=2)
```

### Visualization

All map functions return a `folium.Map` (save to `.html` or display inline in Jupyter).
All plot functions return a `matplotlib.Figure`.

```python
import pymfx.viz as viz

# --- Interactive maps (requires folium) ---
m = viz.trajectory_map(mfx)                       # basic GPS trace
m = viz.speed_heatmap(mfx)                        # segments coloured green → red by speed
m = viz.compare_map([mfx1, mfx2],
                    labels=["Leg 1", "Leg 2"])    # multiple flights, one map

m.save("map.html")    # standalone HTML

# --- Matplotlib plots ---
fig = viz.flight_profile(mfx)                     # altitude / speed / heading over time
fig = viz.events_timeline(mfx)                    # horizontal events timeline
fig = viz.flight_3d(mfx, color_by="speed")        # 3-D lon / lat / alt

fig.savefig("plot.png", dpi=150)
```

### Utilities

```python
# Auto-compute [index] (bounding box + anomaly count) from the trajectory/events data
mfx.index = pymfx.generate_index(mfx)
pymfx.write(mfx, "with_index.mfx")

# Concatenate two flights in temporal order
combined = pymfx.merge(leg1, leg2, gap_s=5.0)
pymfx.write(combined, "combined.mfx")

# Structured comparison between two .mfx files
result = pymfx.diff(flight_a, flight_b)
print(result)                   # box-drawing diff table
if result.has_differences:
    print("Flights differ!")
```

`DiffResult` fields: `meta_diffs`, `point_count_1/2`, `duration_s_1/2`,
`total_distance_m_1/2`, `frequency_hz_1/2`, `event_count_1/2`, `has_differences`.

---

## CLI

```bash
# Core
pymfx flight.mfx --validate           # validate (rules V01–V21)
pymfx flight.mfx --checksum           # verify SHA-256 checksums
pymfx flight.mfx --info               # human-readable summary
pymfx flight.mfx --stats              # aggregated flight statistics

# Comparison
pymfx flight.mfx --diff other.mfx     # structured diff between two files

# Export (stdout by default, -o to write a file)
pymfx flight.mfx --export geojson
pymfx flight.mfx --export gpx  -o flight.gpx
pymfx flight.mfx --export kml  -o flight.kml
pymfx flight.mfx --export csv  -o flight.csv
```

---

## Notebooks

Seven Jupyter notebooks are included in `notebooks/`:

| Notebook | Description |
|---|---|
| `01_quickstart.ipynb` | Parse, inspect, validate and write a `.mfx` file |
| `02_build_from_scratch.ipynb` | Build a complete `.mfx` file from raw Python data |
| `03_visualization.ipynb` | `trajectory_map` · `flight_profile` · `events_timeline` |
| `04_convert.ipynb` | Export to GeoJSON, GPX, KML and CSV |
| `05_stats_datascience.ipynb` | `flight_stats` · pandas DataFrame · `to_dict` / `to_json` |
| `06_viz_advanced.ipynb` | `speed_heatmap` · `compare_map` · `flight_3d` |
| `07_utils.ipynb` | `generate_index` · `merge` · `diff` |

```bash
pip install pymfx[notebooks]
jupyter notebook notebooks/
```

---

## Validation rules

The validator implements all 21 rules from the `.mfx` v1.0 spec:

| ID | Severity | Description |
|----|----------|-------------|
| V01 | Error | Valid @mfx version |
| V02 | Error | [trajectory] checksum correct |
| V03 | Error | [events] checksum correct |
| V04 | Error | [meta] present and in first position |
| V05 | Error | [trajectory] present |
| V06 | Error | date_end present and after date_start if status=complete |
| V07 | Error | t strictly increasing, max 3 decimal places |
| V08 | Error | Field types conform to the defined vocabulary |
| V09 | Error | Number of values per row equals number of schema fields |
| V10 | Error | [no_null] fields do not contain `-` |
| V11 | Warning | [range] constraints respected |
| V12 | Warning | [enum] constraints respected |
| V13 | Warning | Extension sections prefixed with `x_` |
| V14 | Warning | frequency_hz ≥ 1 |
| V15 | Warning | duration_s consistent with date_end − date_start (±5s) |
| V16 | Warning | id is a valid RFC 4122 UUID |
| V17 | Warning | bbox contains all [trajectory] points |
| V18 | Warning | Gap between declared and measured frequency_hz ≤ 20% |
| V19 | Warning | anomalies in [index] matches actual count |
| V20 | Warning | source_format_detail present if source_format=other |
| V21 | Warning | [index] is the last section |

---

## Package structure

```
pymfx/
├── pymfx/
│   ├── __init__.py           Public API
│   ├── models.py             Dataclasses (MfxFile, Meta, Trajectory, …)
│   ├── parser.py             .mfx → Python objects
│   ├── writer.py             Python objects → .mfx
│   ├── validator.py          Rules V01–V21
│   ├── checksum.py           SHA-256 per spec
│   ├── stats.py              flight_stats() → FlightStats
│   ├── utils.py              generate_index · merge · diff · DiffResult
│   ├── cli.py                CLI interface
│   ├── convert/              to_geojson · to_gpx · to_kml · to_csv
│   └── viz/
│       ├── map.py            trajectory_map · speed_heatmap · compare_map
│       ├── profile.py        flight_profile
│       ├── timeline.py       events_timeline
│       └── trajectory_3d.py  flight_3d
├── notebooks/
│   ├── 01_quickstart.ipynb
│   ├── 02_build_from_scratch.ipynb
│   ├── 03_visualization.ipynb
│   ├── 04_convert.ipynb
│   ├── 05_stats_datascience.ipynb
│   ├── 06_viz_advanced.ipynb
│   └── 07_utils.ipynb
└── tests/
    ├── example_minimal.mfx
    ├── test_parser.py
    ├── test_writer.py
    ├── test_validator.py
    ├── test_stats.py
    ├── test_viz_extra.py
    └── test_utils.py
```

---

## License

CC BY 4.0 — See the `.mfx` v1.0 specification for details.

**Format spec:** `mfx_spec_v1.0_final.md`
**MIME type:** `application/x-mfx`
**Reference implementation:** `pymfx` — `github.com/jabahm/pymfx`
