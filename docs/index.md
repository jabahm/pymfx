# pymfx

Python library for the **Mission Flight Exchange** (`.mfx`) v1.0 format.

---

## Installation

```bash
pip install pymfx
pip install pymfx[viz]        # folium + matplotlib
pip install pymfx[ds]         # pandas
pip install pymfx[notebooks]  # all extras + jupyter
```

---

## Features

| Feature | API |
|---|---|
| Parse / Write / Validate | `pymfx.parse()` · `pymfx.write()` · `pymfx.validate()` |
| Format conversion | `pymfx.convert.to_geojson/gpx/kml/csv()` |
| Flight statistics | `pymfx.flight_stats()` |
| Pandas DataFrame | `mfx.trajectory.to_dataframe()` |
| JSON serialisation | `mfx.to_dict()` · `mfx.to_json()` |
| Interactive maps | `viz.trajectory_map()` · `viz.speed_heatmap()` · `viz.compare_map()` |
| Matplotlib plots | `viz.flight_profile()` · `viz.events_timeline()` · `viz.flight_3d()` |
| Utilities | `generate_index()` · `merge()` · `diff()` |
| CLI | `pymfx flight.mfx --validate / --stats / --export / --diff` |

---

## Package structure

```
pymfx/
├── pymfx/
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   ├── writer.py
│   ├── validator.py
│   ├── checksum.py
│   ├── stats.py
│   ├── utils.py
│   ├── cli.py
│   ├── convert/
│   └── viz/
├── docs/
├── notebooks/
└── tests/
```

---

## License

CC BY 4.0 — **Format spec:** `mfx_spec_v1.0_final.md` · **MIME:** `application/x-mfx`
