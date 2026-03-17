# Quick start

## Parse, validate, write

```python
import pymfx

mfx = pymfx.parse("flight.mfx")

print(mfx.meta.drone_id)
print(mfx.meta.date_start)
print(len(mfx.trajectory.points))

result = pymfx.validate(mfx)
if result.is_valid:
    print("✓ Valid")
else:
    for issue in result.issues:
        print(issue)

pymfx.write(mfx, "out.mfx")
```

## Convert

```python
geojson = pymfx.convert.to_geojson(mfx)
gpx     = pymfx.convert.to_gpx(mfx)
kml     = pymfx.convert.to_kml(mfx)
csv     = pymfx.convert.to_csv(mfx)
```

## Flight statistics

```python
stats = pymfx.flight_stats(mfx)
print(stats.duration_s)
print(stats.total_distance_km)
print(stats)   # formatted table
```

## Pandas DataFrame

```python
# requires: pip install pymfx[ds]
df = mfx.trajectory.to_dataframe()
df = mfx.trajectory.to_dataframe(events=mfx.events)
```

## JSON serialisation

```python
d  = mfx.to_dict()
js = mfx.to_json(indent=2)
```

## Visualization

```python
# requires: pip install pymfx[viz]
import pymfx.viz as viz

viz.trajectory_map(mfx)
viz.speed_heatmap(mfx)
viz.compare_map([mfx1, mfx2], labels=["A", "B"])

viz.flight_profile(mfx)
viz.events_timeline(mfx)
viz.flight_3d(mfx, color_by="speed")
```

## Utilities

```python
mfx.index = pymfx.generate_index(mfx)
combined  = pymfx.merge(leg1, leg2, gap_s=5.0)
result    = pymfx.diff(mfx1, mfx2)
print(result)
```
