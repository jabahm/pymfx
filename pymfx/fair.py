"""
pymfx.fair — FAIR compliance scoring for .mfx v1.0 files

Implements Section 5 of the .mfx paper:

    S(f) = α·F(f) + β·A(f) + γ·I(f) + δ·R(f),   α+β+γ+δ = 1

Each dimension F, A, I, R ∈ [0, 1] is the fraction of points earned out of 25.
Point allocation follows Table 7 of the paper (uniform default α₀=β₀=γ₀=δ₀=¼).

Usage::

    import pymfx
    mfx = pymfx.parse("mission.mfx")
    score = pymfx.fair_score(mfx)
    print(score)                 # FairScore object
    print(score.S)               # composite score in [0, 1]
    print(score.breakdown())     # per-dimension detail
"""
from __future__ import annotations

import re
import uuid as _uuid_mod
from dataclasses import dataclass, field

from .checksum import verify_checksum
from .models import MfxFile


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class FairScore:
    """FAIR compliance score for a .mfx file.

    Attributes:
        F: Findability score in [0, 1]
        A: Accessibility score in [0, 1]
        I: Interoperability score in [0, 1]
        R: Reusability score in [0, 1]
        S: Composite score in [0, 1] (weighted sum)
        alpha: weight of F
        beta:  weight of A
        gamma: weight of I
        delta: weight of R
        details: per-criterion result (criterion → (points_earned, max_points, passed))
    """
    F: float
    A: float
    I: float
    R: float
    S: float
    alpha: float
    beta: float
    gamma: float
    delta: float
    details: dict[str, tuple[int, int, bool]] = field(default_factory=dict)

    def breakdown(self) -> str:
        """Return a formatted breakdown table."""
        lines = [
            f"{'Criterion':<45} {'Pts':>4} {'Max':>4}  {'Pass'}",
            "-" * 60,
        ]
        dims = {
            "F": ["id_uuid", "bbox_present", "meta_first"],
            "A": ["license_spdx", "contact_present", "status_present"],
            "I": ["schema_present", "crs_declared", "sensors_vocab", "altitude_ref_declared"],
            "R": ["checksum_valid", "data_level_declared", "producer_declared", "source_format_declared"],
        }
        labels = {
            "id_uuid":                   "F  id is a valid UUID",
            "bbox_present":              "F  [index] bbox present",
            "meta_first":                "F  [meta] is first section",
            "license_spdx":              "A  license present and SPDX-valid",
            "contact_present":           "A  contact present",
            "status_present":            "A  status declared",
            "schema_present":            "I  @schema present in [trajectory]",
            "crs_declared":              "I  crs declared",
            "sensors_vocab":             "I  sensors from controlled vocabulary",
            "altitude_ref_declared":     "I  altitude_ref declared",
            "checksum_valid":            "R  @checksum valid in [trajectory]",
            "data_level_declared":       "R  data_level declared",
            "producer_declared":         "R  producer + producer_version",
            "source_format_declared":    "R  source_format declared",
        }
        for _dim, keys in dims.items():
            for k in keys:
                pts, mx, ok = self.details.get(k, (0, 0, False))
                mark = "✓" if ok else "✗"
                lines.append(f"  {labels[k]:<43} {pts:>4} {mx:>4}  {mark}")
            lines.append("")

        score_line = (
            f"  F={self.F:.2f}  A={self.A:.2f}  I={self.I:.2f}  R={self.R:.2f}"
            f"   →  S₀ = {self.S:.2f}"
        )
        lines.append("-" * 60)
        lines.append(score_line)
        return "\n".join(lines)

    def __str__(self) -> str:
        return (
            f"FairScore(F={self.F:.2f}, A={self.A:.2f}, "
            f"I={self.I:.2f}, R={self.R:.2f}, S={self.S:.2f})"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_valid_uuid(id_val: str | None) -> bool:
    if not isinstance(id_val, str) or not id_val.startswith('uuid:'):
        return False
    try:
        _uuid_mod.UUID(id_val[5:])
        return True
    except ValueError:
        return False


def _is_spdx_like(license_val: str | None) -> bool:
    """Lightweight check: non-empty string that looks like an SPDX id or URL."""
    if not isinstance(license_val, str) or not license_val.strip():
        return False
    # Accept SPDX identifiers (e.g. "CC-BY-4.0", "MIT", "Apache-2.0") or URLs
    return bool(re.match(r'^[A-Za-z0-9\-\+\.]+$', license_val.strip()) or
                license_val.startswith('http'))


# Controlled vocabulary for sensors (paper examples: rgb, thermal, lidar)
_SENSOR_VOCAB = {
    'rgb', 'thermal', 'lidar', 'multispectral', 'hyperspectral',
    'sar', 'radar', 'sonar', 'imu', 'gps', 'video', 'ir', 'nir',
}


def _sensors_from_vocab(sensors: list | None) -> bool:
    if not sensors or not isinstance(sensors, list):
        return False
    return all(s.lower() in _SENSOR_VOCAB for s in sensors)


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def fair_score(
    mfx: MfxFile,
    alpha: float = 0.25,
    beta: float = 0.25,
    gamma: float = 0.25,
    delta: float = 0.25,
) -> FairScore:
    """Compute the FAIR compliance score for a .mfx file.

    Implements Section 5 and Table 7 of the .mfx paper.

    Args:
        mfx:   parsed MfxFile object
        alpha: weight of F (Findability),     default ¼
        beta:  weight of A (Accessibility),   default ¼
        gamma: weight of I (Interoperability),default ¼
        delta: weight of R (Reusability),     default ¼

    Returns:
        FairScore with per-dimension scores and composite score S.

    Raises:
        ValueError: if weights do not sum to 1 (tolerance 1e-6).
    """
    if abs(alpha + beta + gamma + delta - 1.0) > 1e-6:
        raise ValueError(
            f"Weights must sum to 1, got {alpha + beta + gamma + delta}"
        )

    meta = mfx.meta
    traj = mfx.trajectory
    details: dict[str, tuple[int, int, bool]] = {}

    # ------------------------------------------------------------------
    # F — Findability (25 pts total)
    # ------------------------------------------------------------------
    # F1: id is a valid UUID — 10 pts
    ok = _is_valid_uuid(meta.id)
    details["id_uuid"] = (10 if ok else 0, 10, ok)

    # F4: [index] bbox present — 8 pts
    ok = mfx.index is not None and mfx.index.bbox is not None
    details["bbox_present"] = (8 if ok else 0, 8, ok)

    # F3: [meta] is first section (always true if file was parsed successfully) — 7 pts
    ok = True  # parser raises ParseError if [meta] is not first
    details["meta_first"] = (7, 7, ok)

    f_earned = sum(v[0] for v in [details["id_uuid"], details["bbox_present"], details["meta_first"]])
    F = f_earned / 25.0

    # ------------------------------------------------------------------
    # A — Accessibility (25 pts total)
    # ------------------------------------------------------------------
    # A1: license present and SPDX-valid — 10 pts
    ok = _is_spdx_like(meta.license)
    details["license_spdx"] = (10 if ok else 0, 10, ok)

    # A2: contact present — 8 pts
    ok = bool(meta.contact and str(meta.contact).strip())
    details["contact_present"] = (8 if ok else 0, 8, ok)

    # A1: status declared — 7 pts
    ok = bool(meta.status and str(meta.status).strip())
    details["status_present"] = (7 if ok else 0, 7, ok)

    a_earned = sum(v[0] for v in [details["license_spdx"], details["contact_present"], details["status_present"]])
    A = a_earned / 25.0

    # ------------------------------------------------------------------
    # I — Interoperability (25 pts total)
    # ------------------------------------------------------------------
    # I1: @schema present in [trajectory] — 8 pts
    ok = len(traj.schema_fields) > 0
    details["schema_present"] = (8 if ok else 0, 8, ok)

    # I2: crs declared — 7 pts
    ok = bool(meta.crs and str(meta.crs).strip())
    details["crs_declared"] = (7 if ok else 0, 7, ok)

    # I2: sensors from controlled vocabulary — 5 pts
    ok = _sensors_from_vocab(meta.sensors)
    details["sensors_vocab"] = (5 if ok else 0, 5, ok)

    # I2: altitude_ref declared — 5 pts
    ok = bool(meta.altitude_ref and str(meta.altitude_ref).strip())
    details["altitude_ref_declared"] = (5 if ok else 0, 5, ok)

    i_earned = sum(v[0] for v in [
        details["schema_present"], details["crs_declared"],
        details["sensors_vocab"], details["altitude_ref_declared"],
    ])
    I = i_earned / 25.0

    # ------------------------------------------------------------------
    # R — Reusability (25 pts total)
    # ------------------------------------------------------------------
    # R1: @checksum valid in [trajectory] — 8 pts
    if traj.checksum and traj.raw_lines:
        ok = verify_checksum(traj.raw_lines, traj.checksum)
    else:
        ok = False
    details["checksum_valid"] = (8 if ok else 0, 8, ok)

    # R1: data_level declared — 7 pts
    ok = bool(meta.data_level and str(meta.data_level).strip())
    details["data_level_declared"] = (7 if ok else 0, 7, ok)

    # R1: producer + producer_version — 5 pts
    ok = bool(meta.producer and meta.producer_version)
    details["producer_declared"] = (5 if ok else 0, 5, ok)

    # R1: source_format declared — 5 pts
    ok = bool(meta.source_format and str(meta.source_format).strip())
    details["source_format_declared"] = (5 if ok else 0, 5, ok)

    r_earned = sum(v[0] for v in [
        details["checksum_valid"], details["data_level_declared"],
        details["producer_declared"], details["source_format_declared"],
    ])
    R = r_earned / 25.0

    # ------------------------------------------------------------------
    # Composite score
    # ------------------------------------------------------------------
    S = alpha * F + beta * A + gamma * I + delta * R

    return FairScore(
        F=round(F, 4),
        A=round(A, 4),
        I=round(I, 4),
        R=round(R, 4),
        S=round(S, 4),
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        delta=delta,
        details=details,
    )
