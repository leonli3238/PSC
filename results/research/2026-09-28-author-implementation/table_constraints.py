"""Read-only paper-table constraints for choosing GT-PSC reconstruction cases.

The GT-Naive inversion approximates mean absolute RE by the signed overcount
RE. It is a consistency check, not recovery of the author's actual truth.
PSC-B scale inversion assumes exact raw counts, iid equal-scale Laplace
reports, sum aggregation and a final nonnegative clamp. It is diagnostic only.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import runpy
import sys

OUT=Path(__file__).parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from psc.graph import load_dataset
from psc.experiments import DATASETS, PAPER_TABLE2, PAPER_TABLE3

exact_re=runpy.run_path(str(OUT/'research_mechanism.py'))['exact_re']
p=1/(1+math.exp(2))
q=1-2*p
naive=[]
for index,dataset in enumerate(DATASETS):
    g=load_dataset(ROOT/'data',dataset)['2-star'].graph()
    n,N=g.n,g.n-1
    additive2=q*p*(N-1)*2*g.m+n*math.comb(N,2)*p*p
    t2=additive2/(1+PAPER_TABLE2['2-star']['GT-Naive'][index]-q*q)
    additive3=q*q*p*(N-2)*t2+q*p*p*math.comb(N-1,2)*2*g.m+n*math.comb(N,3)*p**3
    t3=additive3/(1+PAPER_TABLE2['3-star']['GT-Naive'][index]-q**3)
    for k,inferred in ((2,t2),(3,t3)):
        truth=g.count_kstars(k)
        naive.append({'dataset':dataset,'k':k,'local_truth':truth,
                      'approx_truth_from_paper_naive':inferred,
                      'relative_difference':inferred/truth-1})

psc_b=[]
for dataset in ('CU','Do'):
    g=load_dataset(ROOT/'data',dataset)['2-star'].graph()
    for k in (2,3):
        truth=g.count_kstars(k)
        paper=PAPER_TABLE3[(f'{k}-star',dataset)][2]
        lo,hi=0.,float(math.comb(g.n,k-1))
        for _ in range(65):
            b=(lo+hi)/2
            if exact_re(truth,truth,b,g.n)[0]>paper:
                hi=b
            else:
                lo=b
        current=math.comb(g.n,k-1)/2
        psc_b.append({'dataset':dataset,'k':k,'paper_gt_psc_b':paper,
                      'current_expected_re':float(exact_re(truth,truth,current,g.n)[0]),
                      'current_scale':current,'scale_implied_by_paper_point':b,
                      'implied_to_current_scale_ratio':b/current})

result={'naive_truth_consistency':naive,'psc_b_scale_diagnostics':psc_b,
        'notes':[
            'Naive inversion treats paper finite-run mean RE as signed population overcount. This approximation does not identify the author graph.',
            'PSC-B scale inversion treats a published finite-run mean as a population value; it is not a measured author noise scale.',
            'Do not install inferred scales as production coefficients. Different ratios motivate joint checking of tables and finite-sample uncertainty.',
        ]}
(OUT/'table_constraints.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
