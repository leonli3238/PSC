"""Research candidate: unbiased polynomial estimates from Laplace degrees.

NOT a reconstruction of PSC author code. This uses the per-node epsilon-edge
LDP definition, and postprocessing of a single released noisy degree. It does
not assert the same epsilon for relationship DP, nor protect raw debug traces.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from psc.graph import load_dataset

OUT=Path(__file__).parent
EPS=2.0
SCALE=1/EPS
RUNS=100000
DATASETS=('CU','Do','ML','CS','EE','PM')
PAPER={2:[.1062,.0585,.0444,.121,.0295,.0284],3:[.8035,.3434,.2077,.541,.1647,.129]}


def coefficients(d,k,b):
    # Corrected estimate as a polynomial in standard-valued noise L.
    # E[L^(2j)]=(2j)!b^(2j); odd moments are zero.
    if k==2:
        return [d*(d-1)/2-b*b,d-.5,.5]
    return [d*(d-1)*(d-2)/6-b*b*(d-1),
            (3*d*d-6*d+2)/6-b*b,(d-1)/2,1/6]


def moment(k,b):
    return 0.0 if k%2 else math.factorial(k)*b**k


def moments(d,k,b):
    c=coefficients(d,k,b)
    mean=sum(ci*moment(i,b) for i,ci in enumerate(c))
    second=sum(ci*cj*moment(i+j,b) for i,ci in enumerate(c) for j,cj in enumerate(c))
    return mean,max(0.0,second-mean*mean)


checks=[]
for k in (2,3):
    for d in range(454):
        expected=math.comb(d,k)
        mean,var=moments(d,k,SCALE)
        assert math.isclose(mean,expected,rel_tol=1e-12,abs_tol=1e-9)
    checks.append({'k':k,'degree_range':[0,453],'analytic_mean_checks':454})

rows=[]
for index,dataset in enumerate(DATASETS):
    g=load_dataset(ROOT/'data',dataset)['2-star'].graph()
    d=np.array(g.degrees())
    rng=np.random.default_rng([9282029,index])
    arrays={2:[],3:[]}
    for offset in range(0,RUNS,2048):
        size=min(2048,RUNS-offset)
        y=d[None,:]+rng.laplace(0,SCALE,size=(size,g.n))
        corrected2=y*(y-1)/2-SCALE**2
        corrected3=y*(y-1)*(y-2)/6-SCALE**2*(y-1)
        for k,x in ((2,corrected2),(3,corrected3)):
            arrays[k].append(x.sum(axis=1))
    for k in (2,3):
        estimates=np.concatenate(arrays[k])
        truth=g.count_kstars(k)
        errors=np.abs(np.maximum(0,estimates)-truth)/truth
        exact_var=sum(moments(int(degree),k,SCALE)[1] for degree in d)
        mc_mean_se=math.sqrt(exact_var/RUNS)
        assert abs(estimates.mean()-truth)<6*mc_mean_se
        rows.append({'dataset':dataset,'k':k,'epsilon':EPS,'runs':RUNS,
                     'mean_re':float(errors.mean()),'se_re':float(errors.std(ddof=1)/math.sqrt(RUNS)),
                     'paper_gt_re':PAPER[k][index],'truth':truth,
                     'unclamped_mean':float(estimates.mean()),
                     'unclamped_bias_se_units':float((estimates.mean()-truth)/mc_mean_se),
                     'analytic_unclamped_variance':exact_var,
                     'empirical_unclamped_variance':float(estimates.var(ddof=1)),
                     'zero_fraction':float(np.mean(estimates<0))})
    print(dataset,[(k,round(float(np.mean(np.abs(np.maximum(0,np.concatenate(arrays[k]))-g.count_kstars(k))/g.count_kstars(k))),6)) for k in (2,3)],flush=True)

result={'name':'Laplace-degree polynomial moment correction',
        'status':'Independent research candidate; not paper reproduction; no novelty claim',
        'assumptions':['Per-node single-bit edge LDP as in PSC definition; degree sensitivity 1.',
                       'One noisy degree y=d+Lap(1/epsilon) is released per node.',
                       'Only postprocessing of noisy degrees; do not additionally release raw counts or spend epsilon again.',
                       'Do not clip noisy degrees or per-node corrected estimates; optional final nonnegative clamp.',
                       'Both star estimates can reuse the same release without additional privacy budget.',
                       'Worst-case dependence on high degrees remains; superiority here is dataset-specific.'],
        'formulas':{'2star':'sum_i [y_i(y_i-1)/2-b^2]',
                    '3star':'sum_i [y_i(y_i-1)(y_i-2)/6-b^2(y_i-1)]','b':'1/epsilon'},
        'analytic_checks':checks,'results':rows}
(OUT/'noisy_degree_candidate.json').write_text(json.dumps(result,indent=2)+'\n')
