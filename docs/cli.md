# CLI reference

## Usage

```bash
pymfx <file.mfx> [command] [options]
```

## Commands

### `--validate`

Run all 21 validation rules. Exits with code 1 if errors are found.

```bash
pymfx flight.mfx --validate
```

```
✓ Valid file — no issues found.
```

---

### `--checksum`

Verify the SHA-256 checksums of `[trajectory]` and `[events]` sections.

```bash
pymfx flight.mfx --checksum
```

---

### `--info`

Print a human-readable summary of the file metadata.

```bash
pymfx flight.mfx --info
```

---

### `--stats`

Print aggregated flight statistics (duration, distance, altitude, speed).

```bash
pymfx flight.mfx --stats
```

```
┌─ Flight Statistics ────────────────┐
│ Points          :   3 600          │
│ Duration        :  360.0 s         │
│ Distance        : 1 245.3 m        │
│ Altitude max    :  102.3 m         │
│ Altitude min    :   48.1 m         │
│ Altitude mean   :   75.4 m         │
│ Speed max       :    8.5 m/s       │
│ Speed mean      :    6.2 m/s       │
└────────────────────────────────────┘
```

---

### `--diff <file2.mfx>`

Structured comparison between two `.mfx` files. Exits with code 1 if differences are found.

```bash
pymfx flight_a.mfx --diff flight_b.mfx
```

---

### `--export <format> [-o <output>]`

Export the trajectory to another format. Prints to stdout by default; use `-o` to write to a file.

```bash
pymfx flight.mfx --export geojson
pymfx flight.mfx --export gpx  -o flight.gpx
pymfx flight.mfx --export kml  -o flight.kml
pymfx flight.mfx --export csv  -o flight.csv
```

Supported formats: `geojson`, `gpx`, `kml`, `csv`.
