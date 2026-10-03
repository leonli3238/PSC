"""Exact risk and source-derived k-star diagnostics; no model/API calls.

Run from repo root with .venv/bin/python. This script is an independent
mathematical implementation, not PSC author code. The risk envelope applies
only to degree clipping + a common scale + independent per-node Laplace reports
+ summation + a final nonnegative clamp, on the current dataset.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from psc.graph import load_dataset

OUT = Path(__file__).parent
DATASETS = ('CU', 'Do', 'ML', 'CS', 'EE', 'PM')
PAPER = {2: [.1062,.0585,.0444,.1210,.0295,.0284],
         3: [.8035,.3434,.2077,.5410,.1647,.1290]}


def count(degrees, k):
    if k == 2:
        return degrees * (degrees - 1) / 2
    return degrees * (degrees - 1) * (degrees - 2) / 6


def laplace_sum_positive_part(t, n):
    """E[(S-t)+], t>=0, S=sum of n independent Laplace(0,1).

    For s>=0, density of S is a finite mixture of Gamma(j+1,1) densities,
    with coefficients .5*w_j, j=0..n-1, sum w_j=1. Integrating (s-t)+
    gives a Poisson-polynomial expression evaluated with log probabilities.
    """
    t = np.atleast_1d(np.asarray(t, dtype=float))
    assert np.all(t >= 0)
    j = np.arange(n)
    lw = np.array([math.lgamma(2*n-1-int(x))-math.lgamma(n-int(x))
                   -math.lgamma(n)-(2*n-2-int(x))*math.log(2) for x in j])
    w = np.exp(lw)
    assert abs(w.sum()-1) < 1e-10
    w /= w.sum()
    reverse = np.cumsum(w[::-1])[::-1]
    reverse_weighted = np.cumsum(((j+1)*w)[::-1])[::-1]
    coeff = np.maximum(0, reverse_weighted - j*reverse)
    log_probability = (-t[:,None] + np.log(np.maximum(t,1e-300))[:,None]*j
                       - np.array([math.lgamma(x+1) for x in j])[None,:])
    probability = np.exp(log_probability)
    probability[t==0,1:] = 0
    return .5 * (probability @ coeff)


def exact_re(raw, truth, b, n, clamp=True):
    """Expected |max(0,raw+b*S)-truth|/truth for 0<=raw<=truth."""
    raw, b = np.broadcast_arrays(np.asarray(raw, dtype=float), np.asarray(b, dtype=float))
    raw, b = raw.ravel(), b.ravel()
    bias = np.maximum(0, truth - raw)
    out = bias.copy()
    pos = b > 0
    out[pos] += 2*b[pos]*laplace_sum_positive_part(bias[pos]/b[pos], n)
    if clamp:
        out[pos] -= b[pos]*laplace_sum_positive_part(raw[pos]/b[pos], n)
    return out/truth


def exact_checks():
    rng = np.random.default_rng(9826101)
    checks = []
    for n in (1, 2, 49, 77, 143, 453):
        closed = math.exp(math.lgamma(n+.5)-math.lgamma(n))/math.sqrt(math.pi)
        h0 = laplace_sum_positive_part(0,n)[0]
        assert math.isclose(h0,closed,rel_tol=2e-11)
        # Gamma difference is exactly distributed as the sum of n Laplace
        # variables. Use it for an independent, cheap Monte Carlo check.
        S = rng.gamma(n, size=300000) - rng.gamma(n, size=300000)
        for raw,truth,b in ((8.,10.,2.),(10.,10.,2.),(0.,10.,2.),(0.,10.,0.)):
            theoretical = float(exact_re(raw,truth,b,n)[0])
            empirical = np.abs(np.maximum(0,raw+b*S)-truth)/truth
            se = float(empirical.std(ddof=1)/math.sqrt(len(S)))
            difference = float(empirical.mean()-theoretical)
            assert abs(difference) < 6*se+1e-10
            checks.append({'n':n,'raw':raw,'truth':truth,'scale':b,
                           'exact_mean_re':theoretical,'mc_mean_re':float(empirical.mean()),
                           'mc_se':se,'mc_runs':len(S)})
    assert np.allclose(laplace_sum_positive_part([0,1,3],1),.5*np.exp(-np.array([0,1,3])))
    return checks


def envelopes():
    rows=[]
    for index,dataset in enumerate(DATASETS):
        g=load_dataset(ROOT/'data',dataset)['2-star'].graph()
        degrees=np.array(g.degrees())
        D=np.arange(g.n)
        for k in (2,3):
            truth=float(count(degrees,k).sum())
            raw=count(np.minimum(degrees[None,:],D[:,None]),k).sum(axis=1)
            for eps3 in (1.6,2.0):
                for tight in (False,True):
                    x=np.maximum(0,D-int(tight))
                    gs=x if k==2 else x*(x-1)/2
                    re=exact_re(raw,truth,gs/eps3,g.n)
                    idx=int(re.argmin())
                    rows.append({'dataset':dataset,'k':k,'eps3':eps3,'tight_gs':tight,
                                 'best_D':int(D[idx]),'min_expected_re':float(re[idx]),
                                 'paper_gt_re':PAPER[k][index],
                                 'optimal_raw_fraction':float(raw[idx]/truth),
                                 'extends_to_all_smaller_eps3':bool(re[idx]<.25 and raw[idx]>=truth/2),
                                 'scope':'oracle choice among every integer D=0..n-1; not a private algorithm or bound over all LDP mechanisms'})
    return rows


def source_variants():
    rows=[]
    runs=50000
    seed=9282027
    for index,dataset in enumerate(DATASETS):
        g=load_dataset(ROOT/'data',dataset)['2-star'].graph()
        degrees=np.array(g.degrees())
        rng=np.random.default_rng([seed,index])
        arrays={}
        variants=[
            ('current',.4,'ceil','integer',True),
            ('imola_cpp_rounding_psc_budget',.4,'floor','continuous',True),
            ('imola_paper_rounding_psc_budget',.4,'floor','integer',True),
            ('imola_cpp_native',.2,'floor','continuous',False),
            ('imola_cpp_native_with_final_clamp',.2,'floor','continuous',True),
        ]
        for offset in range(0,runs,2048):
            size=min(2048,runs-offset)
            degree_z=rng.laplace(size=(size,g.n))
            report_z=rng.laplace(size=(size,g.n)).sum(axis=1)
            for name,eps2,rounding,gs_mode,clamp in variants:
                m=(degrees[None,:]+degree_z/eps2).max(axis=1)
                if name!='current':
                    m=np.clip(m,0,g.n-1)
                D=np.maximum(1,np.ceil(m)) if rounding=='ceil' else np.floor(m)
                d_used=np.minimum(degrees[None,:],D[:,None])
                gs_D=m if gs_mode=='continuous' else D
                for k in (2,3):
                    truth=float(count(degrees,k).sum())
                    raw=count(d_used,k).sum(axis=1)
                    gs=gs_D if k==2 else gs_D*(gs_D-1)/2
                    assert np.all(gs>=0)
                    estimate=raw+gs/(2-eps2)*report_z
                    if clamp:estimate=np.maximum(0,estimate)
                    error=np.abs(estimate-truth)/truth
                    arrays.setdefault((k,name),[]).append(error)
        for (k,name),parts in arrays.items():
            x=np.concatenate(parts)
            rows.append({'dataset':dataset,'k':k,'variant':name,'runs':runs,'seed':seed,
                         'mean_re':float(x.mean()),'se':float(x.std(ddof=1)/math.sqrt(runs)),
                         'paper_gt_re':PAPER[k][index]})
        print(dataset,[(r['k'],r['variant'],round(r['mean_re'],5)) for r in rows if r['dataset']==dataset],flush=True)
    return rows


if __name__=='__main__':
    result={'exact_risk_checks':exact_checks(),
            'oracle_integer_threshold_envelopes':envelopes(),
            'source_derived_variants':source_variants(),
            'cautions':[
                'Author PSC code was not found. Imola source variants are independently translated from cited 2021 code.',
                'Risk envelope is a population expectation for this mechanism family, not a prohibition on finite-sample means.',
                'A shared random D independent of reporting noise is a mixture of conditional risks and cannot improve below their minimum.',
                'Full eps3=2 and oracle D deliberately favor accuracy; threshold-estimation cost is ignored.',
                'Extension to all smaller eps3: when raw>=truth/2 risk increases with scale; when raw<truth/2 half the noise draws give risk >=(truth-raw)/truth, so expected RE>.25. All optimistic 2-star minima are below .25.',
                'Arbitrary estimators, correlated/heterogeneous reports, and other datasets are outside the risk envelope.',
            ]}
    (OUT/'mechanism_research.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Saved',OUT/'mechanism_research.json')
