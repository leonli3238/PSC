"""Explicit k-star interpretations shared by GT and agent execution.

The floor/tight interpretation is a reconstruction candidate, not verified
author code. Degree and triangle retain their original mechanism in every
profile. ``legacy`` preserves the pre-alignment k-star behavior and RNG use.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class DegreeBound:
    raw_max: float
    sensitivity_degree: float
    projection_degree: int


@dataclass(frozen=True)
class MechanismProfile:
    name: str
    rounding: str
    gs_mode: str
    physical_cap: bool
    base_bound: str
    description: str
    # (task, margin) pairs; margin is in units of the degree-report scale 1/eps2.
    node_margin: tuple[tuple[str, float], ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)

    def node_projection_degrees(self, reports, projection_degree, task: str, eps2: float):
        """Per-node thresholds ``D_i = min(D, floor(y_i + margin / eps2))``, or ``None``.

        ``D_i`` is post-processing of node i's own published noisy degree and the
        public global bound, so a round-2 report calibrated to ``C(D_i-1, k-1)``
        composes to ``eps2 + eps3``. Accepts arrays (``projection_degree`` must
        broadcast against ``reports``).
        """
        margin = dict(self.node_margin).get(task)
        if margin is None:
            return None
        y = np.asarray(reports, dtype=float)
        if not np.all(np.isfinite(y)) or not math.isfinite(eps2) or eps2 <= 0:
            raise ValueError("node thresholds need finite reports and a positive eps2")
        return np.minimum(projection_degree, np.maximum(0.0, np.floor(y + margin / eps2))).astype(int)

    def degree_bound(self, reports: Sequence[float], task: str) -> DegreeBound:
        if len(reports) == 0 or not all(math.isfinite(x) for x in reports):
            raise ValueError("noisy degree reports must be nonempty and finite")
        raw = float(max(reports))
        if task not in ("2-star", "3-star") or self.name == "legacy":
            d = max(1, math.ceil(raw))
            return DegreeBound(raw, float(d), d)
        maximum = min(max(raw, 0.0), len(reports) - 1.0) if self.physical_cap else max(0.0, raw)
        d = math.floor(maximum) if self.rounding == "floor" else math.ceil(maximum)
        gs_degree = maximum if self.gs_mode == "continuous" else float(d)
        return DegreeBound(raw, gs_degree, d)

    def kstar_sensitivity(
        self, k: int, n: int, projection_degree: int | None,
        sensitivity_degree: float | None = None,
    ) -> float:
        if k not in (2, 3) or n < 1:
            raise ValueError("k must be 2 or 3, and n must be positive")
        if projection_degree is None:
            d = float(n if self.base_bound == "n" else n - 1)
        else:
            d = float(projection_degree if sensitivity_degree is None else sensitivity_degree)
        if not math.isfinite(d) or d < 0:
            raise ValueError("sensitivity degree must be finite and nonnegative")
        if self.gs_mode == "tight":
            return float(math.comb(max(0, int(d) - 1), k - 1))
        if self.gs_mode == "continuous":
            # Below degree 1 the clipped count is constant; avoid negative GS.
            return max(0.0, d if k == 2 else d * (d - 1) / 2)
        return float(math.comb(int(d), k - 1))


PROFILES = {
    "legacy": MechanismProfile(
        "legacy", "ceil", "bound", False, "n",
        "Original implementation: ceil maximum, C(D,k-1), C(n,k-1) without GS optimization.",
    ),
    "floor_bound": MechanismProfile(
        "floor_bound", "floor", "bound", True, "n_minus_one",
        "Integer bound from the cited algorithm: floor maximum and C(D,k-1).",
    ),
    "continuous_bound": MechanismProfile(
        "continuous_bound", "floor", "continuous", True, "n_minus_one",
        "Cited C++ interpretation: floor projection, continuous maximum for GS.",
    ),
    "floor_tight": MechanismProfile(
        "floor_tight", "floor", "tight", True, "n_minus_one",
        "Floor projection with the tight sensitivity C(D-1,k-1) of clipped degree counts.",
    ),
    "adaptive_2star": MechanismProfile(
        "adaptive_2star", "floor", "tight", True, "n_minus_one",
        "floor_tight; 2-star nodes clip at min(D, floor(y_i + 2/eps2)) from their own noisy "
        "degree and use C(D_i-1,1). DP-valid; margin selected to approximate the paper tables.",
        node_margin=(("2-star", 2.0),),
    ),
}
MECHANISMS = tuple(PROFILES)
DEFAULT_MECHANISM = "floor_tight"


def get_mechanism(value: str | MechanismProfile = DEFAULT_MECHANISM) -> MechanismProfile:
    if isinstance(value, MechanismProfile):
        return value
    try:
        return PROFILES[value]
    except KeyError:
        raise ValueError(f"unknown mechanism {value!r}; choose from {MECHANISMS}") from None
