"""Per-node degree bounds by edge clipping (Imola, Murakami, Chaudhuri, USENIX Security 2022).

PSC bounds the private list of every node by one public value, the noisy
maximum degree ``d̂max`` (Algorithm 2; Imola et al. USENIX Security 2021). As a
maximum of ``n`` noisy values it overestimates the degree of most nodes, and the
sensitivity of a k-star count grows as ``C(D-1, k-1)``.

Edge clipping replaces the global bound by one bound per node: every node
publishes its noisy degree and clips its own neighbour list to

    D_i = floor( max(d_i + Lap(1/ε2), 0) + α ),

keeping at most ``D_i`` neighbours; its report is calibrated to the
sensitivity of the program at ``D_i``. ``α ≥ 0`` is a public, data-independent
hyperparameter that makes clipping of true neighbours rarer (more bias for
α = 0, more noise for large α).

Privacy (edge LDP of node ``i``): the noisy degree is ε2-DP (sensitivity 1);
``D_i`` is post-processing of it; given ``D_i`` the report is ε3-DP because the
certificate of the program at the public ``D_i`` bounds the change of the local
count over neighbouring lists (the deriver's projection coupling: one random
priority order independent of ``P``). With the RR rows (ε1) the three steps
compose sequentially to ε1 + ε2 + ε3 = ε. The budget split is fixed in advance.

Programs that read the noisy rows ``N(j)`` keep PSC's public row bound: the RR
graph is projected to ``d̂max`` computed from the same released noisy degrees
(post-processing), so ``dmax`` stays global and only ``D`` becomes per node. The
library triangle program does not call ``project(P, D)``: its GS ``dmax - 1``
and its estimate are unchanged by per-node bounds. The edge-clipping triangle
estimator of Imola et al. 2022 (unbiased RR matrix, sensitivity ``κ·d̃_i``) is
the reproduction's GT-TriTR (:func:`psc.ground_truth.gt_tritr`).
"""

from __future__ import annotations

import math
from typing import Sequence


def edge_clipping_bounds(noisy_degrees: Sequence[float], alpha: float = 0.0) -> list[int]:
    """``D_i = floor(max(y_i, 0) + alpha)`` for the published ``y_i = d_i + Lap(1/ε2)``."""
    if alpha < 0:
        raise ValueError("alpha must be nonnegative")
    return [int(math.floor(max(float(y), 0.0) + alpha)) for y in noisy_degrees]
