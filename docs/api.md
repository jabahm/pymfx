# API reference

## Core

### `pymfx.parse(source)`

Parse a `.mfx` file and return a `MfxFile` object.

```python
mfx = pymfx.parse("flight.mfx")      # file path (str or Path)
```

Raises `ParseError` on malformed input.

---

### `pymfx.write(mfx, path)`

Serialize a `MfxFile` to a `.mfx` file. SHA-256 checksums are computed automatically.

```python
pymfx.write(mfx, "out.mfx")
```

---

### `pymfx.validate(mfx)`

Run all 21 validation rules (V01–V21) against a `MfxFile`.

```python
result = pymfx.validate(mfx)
result.is_valid   # bool
result.errors     # list[ValidationIssue]
result.warnings   # list[ValidationIssue]
```

---

### `pymfx.compute_checksum(lines)`

Compute the SHA-256 checksum of a list of raw data lines, as defined in the `.mfx` spec §7.

```python
checksum = pymfx.compute_checksum(raw_lines)
```

---

## Conversion — `pymfx.convert`

All functions accept a `MfxFile` and return a `str`.

| Function | Output format |
|---|---|
| `pymfx.convert.to_geojson(mfx)` | GeoJSON FeatureCollection |
| `pymfx.convert.to_gpx(mfx)` | GPX 1.1 |
| `pymfx.convert.to_kml(mfx)` | KML |
| `pymfx.convert.to_csv(mfx)` | CSV (one row per trajectory point) |

---

## Statistics

### `pymfx.flight_stats(mfx)`

Compute aggregated flight metrics. Returns a `FlightStats` dataclass.

```python
stats = pymfx.flight_stats(mfx)
```

**`FlightStats` fields:**

| Field | Type | Description |
|---|---|---|
| `point_count` | `int` | Number of trajectory points |
| `duration_s` | `float` | Flight duration in seconds |
| `total_distance_m` | `float` | Great-circle distance in metres |
| `total_distance_km` | `float` | Property — `total_distance_m / 1000` |
| `alt_max_m` | `float` | Maximum altitude |
| `alt_min_m` | `float` | Minimum altitude |
| `alt_mean_m` | `float` | Mean altitude |
| `speed_max_ms` | `float` | Maximum speed |
| `speed_mean_ms` | `float` | Mean speed |

---

## Data science — `MfxFile` / `Trajectory`

### `mfx.trajectory.to_dataframe(events=None)`

Convert trajectory points to a `pandas.DataFrame`. Requires `pandas`.

```python
df = mfx.trajectory.to_dataframe()
df = mfx.trajectory.to_dataframe(events=mfx.events)  # nearest-time merge
```

### `mfx.to_dict()`

Recursively convert the entire `MfxFile` to a plain Python `dict`.

### `mfx.to_json(indent=2)`

Serialize the `MfxFile` to a JSON string.

---

## Visualization — `pymfx.viz`

Requires `pip install pymfx[viz]`.

| Function | Returns | Description |
|---|---|---|
| `viz.trajectory_map(mfx)` | `folium.Map` | Interactive GPS trace |
| `viz.speed_heatmap(mfx)` | `folium.Map` | Segments coloured by speed |
| `viz.compare_map(flights, labels)` | `folium.Map` | Multiple flights, one map |
| `viz.flight_profile(mfx)` | `Figure` | Altitude / speed / heading over time |
| `viz.events_timeline(mfx)` | `Figure` | Horizontal events timeline |
| `viz.flight_3d(mfx, color_by)` | `Figure` | 3-D lon / lat / alt |

All map and plot functions accept `show_events=True/False`.

---

## Utilities

### `pymfx.generate_index(mfx)`

Compute the `[index]` section from the trajectory and events data.

```python
mfx.index = pymfx.generate_index(mfx)
```

Returns an `Index(bbox, anomalies)` where `bbox = (lon_min, lat_min, lon_max, lat_max)`.

---

### `pymfx.merge(mfx1, mfx2, gap_s=0.0)`

Concatenate two flights in temporal order. The `t` values of `mfx2` are shifted so the time axis stays strictly increasing.

```python
combined = pymfx.merge(leg1, leg2, gap_s=5.0)
```

---

### `pymfx.diff(mfx1, mfx2)`

Structured comparison between two `.mfx` files. Returns a `DiffResult`.

```python
result = pymfx.diff(mfx1, mfx2)
print(result)               # box-drawing table
result.has_differences      # bool
result.meta_diffs           # list of (field, val1, val2)
```

---

## Data models

### `MfxFile`

| Field | Type |
|---|---|
| `version` | `str` |
| `encoding` | `str` |
| `meta` | `Meta` |
| `trajectory` | `Trajectory` |
| `events` | `Events \| None` |
| `index` | `Index \| None` |

### `Meta` — key fields

`id`, `drone_id`, `drone_type`, `pilot_id`, `date_start`, `date_end`, `duration_s`, `status`, `application`, `location`, `sensors`, `data_level`, `license`, `contact`

### `TrajectoryPoint`

`t`, `lat`, `lon`, `alt_m`, `speed_ms`, `heading`, `roll`, `pitch` (all optional except `t`, `lat`, `lon`)

### `Event`

`t`, `type`, `severity`, `detail`

### `Index`

`bbox` (`tuple[float,float,float,float] | None`), `anomalies` (`int`)
