"""Fault injection on the certificate path: what does the node's own check stop?

The curator ships each program with a certificate (:func:`certicount.dsl.sensitivity.certify`);
the node calibrates its Laplace noise with the GS it accepts. This script tampers with the
certificates of real programs -- every distinct program the Qwen3-8B curator had accepted in the
CS9 design runs (each release candidate) plus the library references -- and compares three nodes:

* ``trust``    -- no node check: the node uses the curator's claimed GS (a trusted curator);
* ``legacy``   -- the node check before 2026-11-23 (re-derive with the certificate's own facts,
                  compare GS; no check of the number itself);
* ``hardened`` -- :func:`certicount.binding.check_program`: finite nonnegative GS, the node's own
                  environment facts, then re-derivation.

Outcome of a case: ``rejected``; accepted ``safe`` (noise GS >= the GS the node's deriver gives
under the true environment); accepted ``violation`` (noise GS below it: the release costs
``true GS / used GS`` times ε3); accepted ``invalid`` (NaN, infinite or negative noise scale:
no meaningful release, an availability failure). ``safe`` / ``violation`` are relative to the
deriver (its soundness is supported by the falsifier and the fuzz runs, not proven).

Tampering kinds: honest, overstate (x2), understate (x0.5, x0.1, 0), nan, inf, negative, a
certificate of another program, a certificate for a smaller published bound D, and facts the
environment does not guarantee (curator certifies with every fact, the environment lacks one).

CPU only, no model calls:

    ../.venv/bin/python scripts/run_cert_tamper.py --tag cert_tamper
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from certicount.artifacts import markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.binding import BindingViolation, check_program  # noqa: E402
from certicount.dsl.lang import DSLError, Program, parse_program_text  # noqa: E402
from certicount.dsl.library import NODE_PROGRAMS, PROGRAMS  # noqa: E402
from certicount.dsl.matrix import REFERENCE_EPS1  # noqa: E402
from certicount.dsl.sensitivity import (Certificate, Facts, PublicParams, SensitivityError,  # noqa: E402
                                        certify, derive)

RESULTS = ROOT / "results"
DEFAULT_TAGS = ("cs9_node_generic_sim_tri_ow", "cs9_node_generic_sim_ext", "cs9_node_generic_sim_4cycle",
                "cs9_node_v1alt_sim_ow")
ENVIRONMENTS = {"all facts": Facts(), "no symmetric rows": Facts(symmetric_rows=False),
                "self may be in P": Facts(self_not_in_private=False)}
REGIMES = ("trust", "legacy", "hardened")
OUTCOMES = ("rejected", "safe", "violation", "invalid")


def load_programs(tags: list[str]) -> list[tuple[str, Program]]:
    """Distinct accepted programs (every release candidate) of the design runs, plus the references."""
    seen: dict[str, tuple[str, Program]] = {}

    def add(origin: str, text: str | None) -> None:
        if not text:
            return
        try:
            prog = parse_program_text(text)
        except DSLError:
            return
        seen.setdefault(prog.digest, (origin, prog))

    for tag in tags:
        path = RESULTS / "dsl_eval" / tag / "designs.jsonl"
        if not path.exists():
            print(f"skip {tag}: no designs.jsonl")
            continue
        for line in path.open(encoding="utf-8"):
            r = json.loads(line)
            add(f"{tag}/{r['task']}", r.get("program"))
            for c in (r.get("selection") or {}).get("candidates") or []:
                add(f"{tag}/{r['task']}", c.get("program"))
    for lib, name in ((PROGRAMS, "library"), (NODE_PROGRAMS, "library-node")):
        for task, src in lib.items():
            prog = src.parse()
            seen.setdefault(prog.digest, (f"{name}/{task}", prog))
    return list(seen.values())


def legacy_check(prog: Program, cert: Certificate, params: PublicParams) -> float:
    """The node check before 2026-11-23 (verify_certificate + check_program), kept for comparison."""
    if cert.program_digest != prog.digest:
        raise BindingViolation("certificate_rejected", "different program")
    if cert.params != params:
        raise BindingViolation("certificate_rejected", "different parameters")
    try:
        own = derive(prog, params, cert.facts)
    except SensitivityError as exc:
        raise BindingViolation("certificate_rejected", str(exc)) from None
    if cert.gs + 1e-9 < own.gs:
        raise BindingViolation("certificate_rejected", "GS below the derived GS")
    return max(cert.gs, own.gs)


def node_gs(regime: str, prog: Program, cert: Certificate, params: PublicParams, env: Facts) -> float | None:
    """GS the node calibrates its noise with; None: rejected."""
    try:
        if regime == "trust":
            return cert.gs
        if regime == "legacy":
            return legacy_check(prog, cert, params)
        return check_program(prog, cert, params, env)
    except BindingViolation:
        return None


def outcome(used, true_gs: float) -> tuple[str, float | None]:
    if used is None:
        return "rejected", None
    if isinstance(used, bool) or not isinstance(used, (int, float)) or not math.isfinite(used) or used < 0:
        return "invalid", None
    if used + 1e-9 >= true_gs:
        return "safe", None
    return "violation", (math.inf if used == 0 else true_gs / used)


def cases(prog: Program, others: list[Program], params: PublicParams, smaller: PublicParams, rng: random.Random):
    """(kind, environment, certificate) of one program under one public parameter set."""
    env_all = ENVIRONMENTS["all facts"]
    honest = certify(prog, params)
    yield "honest", "all facts", honest
    yield "overstate x2", "all facts", replace(honest, gs=honest.gs * 2)
    if honest.gs > 0:
        yield "understate x0.5", "all facts", replace(honest, gs=honest.gs * 0.5)
        yield "understate x0.1", "all facts", replace(honest, gs=honest.gs * 0.1)
        yield "understate to 0", "all facts", replace(honest, gs=0.0)
    yield "nan", "all facts", replace(honest, gs=math.nan)
    yield "inf", "all facts", replace(honest, gs=math.inf)
    yield "negative", "all facts", replace(honest, gs=-honest.gs - 1.0)
    other = rng.choice(others)
    try:
        yield "other program", "all facts", certify(other, params)
    except SensitivityError:
        pass
    try:
        yield "smaller bound D", "all facts", certify(prog, smaller)
    except SensitivityError:
        pass
    for name, env in ENVIRONMENTS.items():
        if env == env_all:
            continue
        yield "unguaranteed facts", name, honest  # certified with every fact, the environment lacks one
        try:
            yield "honest (reduced env)", name, certify(prog, params, env)
        except SensitivityError:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tags", default=",".join(DEFAULT_TAGS), help="dsl_eval runs whose accepted programs are used")
    ap.add_argument("--n", default="49,143,453", help="public graph sizes")
    ap.add_argument("--bounds", default="5,10,20", help="published degree bounds D = dmax")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    programs = load_programs([t for t in args.tags.split(",") if t])
    print(f"{len(programs)} distinct programs")
    out = out_dir("trust", args.tag, "cert_tamper")
    write_manifest(out, {**vars(args), "programs": len(programs)})
    rng = random.Random(args.seed)
    ns, bounds = [int(x) for x in args.n.split(",")], [int(x) for x in args.bounds.split(",")]
    progs = [p for _, p in programs]
    counts: dict[tuple[str, str], dict[str, int]] = {}
    ratios: dict[tuple[str, str], list[float]] = {}
    seconds: list[float] = []
    skipped = 0
    details = []
    for origin, prog in programs:
        others = [p for p in progs if p.digest != prog.digest]
        for n in ns:
            for d in bounds:
                params = PublicParams(n, D=d, dmax=d, eps1=REFERENCE_EPS1)
                smaller = PublicParams(n, D=max(2, d // 2), dmax=max(2, d // 2), eps1=REFERENCE_EPS1)
                try:
                    certify(prog, params)
                except SensitivityError:
                    skipped += 1
                    continue
                for kind, env_name, cert in cases(prog, others, params, smaller, rng):
                    env = ENVIRONMENTS[env_name]
                    try:
                        true_gs = derive(prog, params, env).gs
                    except SensitivityError:
                        continue
                    for regime in REGIMES:
                        t0 = time.perf_counter()
                        used = node_gs(regime, prog, cert, params, env)
                        if regime == "hardened":
                            seconds.append(time.perf_counter() - t0)
                        res, ratio = outcome(used, true_gs)
                        c = counts.setdefault((kind, regime), dict.fromkeys(OUTCOMES, 0))
                        c[res] += 1
                        if ratio is not None:
                            ratios.setdefault((kind, regime), []).append(ratio)
                        if res in ("violation", "invalid") and regime == "hardened":
                            details.append({"origin": origin, "program": prog.text(), "n": n, "D": d, "kind": kind,
                                            "env": env_name, "claimed": cert.gs, "true_gs": true_gs, "outcome": res})

    rows = []
    kinds = list(dict.fromkeys(k for k, _ in counts))
    for kind in kinds:
        row = {"tampering": kind}
        for regime in REGIMES:
            c = counts.get((kind, regime), dict.fromkeys(OUTCOMES, 0))
            total = sum(c.values())
            row["cases"] = total
            bad = c["violation"] + c["invalid"]
            row[f"{regime}_rejected"] = c["rejected"]
            row[f"{regime}_violation"] = c["violation"]
            row[f"{regime}_invalid"] = c["invalid"]
            row[f"{regime}_accepted_unsafe"] = f"{bad}/{total}"
            r = ratios.get((kind, regime), [])
            row[f"{regime}_max_eps3_multiple"] = max(r) if r else None
        rows.append(row)
    timing = {"verify_calls": len(seconds), "median_ms": 1000 * statistics.median(seconds),
              "p95_ms": 1000 * sorted(seconds)[int(0.95 * (len(seconds) - 1))], "max_ms": 1000 * max(seconds)}
    write_json({"settings": vars(args), "programs": len(programs), "skipped_parameter_sets": skipped,
                "table": rows, "timing": timing, "hardened_failures": details}, out / "summary.json")
    cols_short = ["tampering", "cases"] + [f"{r}_accepted_unsafe" for r in REGIMES] + \
                 [f"{r}_rejected" for r in REGIMES]
    cols_detail = ["tampering", "cases"] + [f"{r}_{k}" for r in REGIMES for k in ("violation", "invalid")] + \
                  [f"{r}_max_eps3_multiple" for r in REGIMES]
    md = [
        "# Certificate fault injection (node-side verification)", "",
        f"{len(programs)} distinct programs (accepted release candidates of {args.tags} and the library "
        f"references) x n in {{{args.n}}} x D = dmax in {{{args.bounds}}} ({skipped} program/parameter sets without "
        "a finite GS skipped). Regimes: `trust` = the node uses the claimed GS; `legacy` = node check before "
        "2026-11-23 (re-derives with the certificate's facts); `hardened` = `binding.check_program` (finite "
        "nonnegative GS, the environment's own facts). `accepted_unsafe` = accepted with a noise GS below the GS "
        "derived under the true environment (privacy violation, `violation`) or with a NaN / infinite / negative "
        "noise scale (`invalid`, availability failure). `max_eps3_multiple` = true GS / used GS: the realised "
        "privacy loss of the count release in units of ε3. Relative to the deriver (supported by the falsifier and "
        "fuzz runs, not proven).", "",
        "## Unsafe acceptances and rejections", "", markdown_table(rows, cols_short), "",
        "## Breakdown", "", markdown_table(rows, cols_detail), "",
        f"Node-side verification cost (hardened, per certificate): median {timing['median_ms']:.2f} ms, "
        f"p95 {timing['p95_ms']:.2f} ms, max {timing['max_ms']:.1f} ms over {timing['verify_calls']} checks.", "",
        f"Hardened failures: {len(details)} (listed in summary.json).", "",
    ]
    (out / "table.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print(f"results in {out}")


if __name__ == "__main__":
    main()
