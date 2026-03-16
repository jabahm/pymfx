"""
pymfx.cli — Command-line interface

Usage:
    pymfx --validate <file.mfx>
    pymfx --checksum <file.mfx>
    pymfx --info <file.mfx>
"""
import argparse
import sys
from pathlib import Path

from .parser import parse, ParseError
from .validator import validate
from .checksum import compute_checksum


def cmd_validate(path: Path) -> int:
    """Validate a .mfx file and print issues."""
    raw_text = path.read_text(encoding='utf-8')
    try:
        mfx = parse(raw_text)
    except ParseError as e:
        print(f"✗ Parse error: {e}", file=sys.stderr)
        return 1

    result = validate(mfx, raw_text=raw_text)
    print(str(result))
    return 0 if result.is_valid else 1


def cmd_checksum(path: Path) -> int:
    """Compute and display SHA-256 checksums for all data[] blocks in a .mfx file."""
    raw_text = path.read_text(encoding='utf-8')
    try:
        mfx = parse(raw_text)
    except ParseError as e:
        print(f"✗ Parse error: {e}", file=sys.stderr)
        return 1

    print(f"File: {path}")
    traj = mfx.trajectory
    checksum = compute_checksum(traj.raw_lines)
    declared = traj.checksum or "(not declared)"
    match = "✓" if traj.checksum and traj.checksum == checksum else ("✗" if traj.checksum else "—")
    print(f"  [trajectory] data[] : {checksum}")
    print(f"    declared          : {declared} {match}")

    if mfx.events:
        ev_checksum = compute_checksum(mfx.events.raw_lines)
        ev_declared = mfx.events.checksum or "(not declared)"
        ev_match = "✓" if mfx.events.checksum and mfx.events.checksum == ev_checksum else ("✗" if mfx.events.checksum else "—")
        print(f"  [events] data[]    : {ev_checksum}")
        print(f"    declared         : {ev_declared} {ev_match}")

    return 0


def cmd_info(path: Path) -> int:
    """Print a summary of a .mfx file."""
    raw_text = path.read_text(encoding='utf-8')
    try:
        mfx = parse(raw_text)
    except ParseError as e:
        print(f"✗ Parse error: {e}", file=sys.stderr)
        return 1

    m = mfx.meta
    print(f"File     : {path}")
    print(f"Version  : {mfx.version}")
    print(f"ID       : {m.id}")
    print(f"Drone    : {m.drone_id} ({m.drone_type})")
    print(f"Pilot    : {m.pilot_id}")
    print(f"Start    : {m.date_start}")
    if m.date_end:
        print(f"End      : {m.date_end}")
    print(f"Status   : {m.status}")
    print(f"App      : {m.application}")
    print(f"Location : {m.location}")
    print(f"Sensors  : {m.sensors}")
    t = mfx.trajectory
    print(f"\n[trajectory]")
    print(f"  Points       : {len(t.points)}")
    print(f"  frequency_hz : {t.frequency_hz}")
    if t.points:
        print(f"  t range      : {t.points[0].t:.3f}s — {t.points[-1].t:.3f}s")
    if mfx.events:
        print(f"\n[events]  : {len(mfx.events.events)} event(s)")
    if mfx.index:
        print(f"\n[index]")
        if mfx.index.bbox:
            print(f"  bbox      : {mfx.index.bbox}")
        if mfx.index.anomalies is not None:
            print(f"  anomalies : {mfx.index.anomalies}")
    if mfx.extensions:
        print(f"\nExtensions : {[e.name for e in mfx.extensions]}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        prog='pymfx',
        description='Read, validate and manage .mfx v1.0 mission files'
    )
    parser.add_argument('file', type=Path, help='.mfx file to process')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--validate', action='store_true',
                       help='Validate the file (rules V01–V21)')
    group.add_argument('--checksum', action='store_true',
                       help='Compute and verify SHA-256 checksums')
    group.add_argument('--info', action='store_true',
                       help='Print a summary of the file')

    args = parser.parse_args()

    if not args.file.exists():
        print(f"✗ File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    if args.validate:
        sys.exit(cmd_validate(args.file))
    elif args.checksum:
        sys.exit(cmd_checksum(args.file))
    elif args.info:
        sys.exit(cmd_info(args.file))


if __name__ == '__main__':
    main()
