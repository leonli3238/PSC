"""Compare original C++ functions with the independent Python translation.

Compile upstream_function_harness.cpp to /tmp/psc_upstream_function_harness
first. The C++ contains the original two functions; its sampler is replaced
with a prescribed standard Laplace tape. No assertion about RNG equivalence.
"""
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from psc.graph import load_dataset

OUT=Path(__file__).parent
rng=np.random.default_rng(9282028)
cases=[]
expected=[]
for dataset in ('CU','Do','ML','CS','EE','PM'):
    g=load_dataset(ROOT/'data',dataset)['2-star'].graph()
    degree=np.array(g.degrees())
    for eps2 in (.2,.4):
        for i in range(100):
            z=rng.laplace(size=3*g.n)
            M=float(np.clip(np.max(degree+z[:g.n]/eps2),0,g.n-1))
            used=np.minimum(degree,math.floor(M))
            assert M>=1
            raw2=float(np.sum(used*(used-1)/2))
            raw3=float(np.sum(used*(used-1)*(used-2)/6))
            gs2,gs3=M,M*(M-1)/2
            result2=raw2+gs2/(2-eps2)*z[g.n::2].sum()
            result3=raw3+gs3/(2-eps2)*z[g.n+1::2].sum()
            expected.append([result2,result3,gs2,gs3,len(z)])
            cases.append(f'{g.n} {eps2}\n'+' '.join(map(str,degree))+'\n'+' '.join(map(str,z)))
input_text=str(len(cases))+'\n'+'\n'.join(cases)+'\n'
p=subprocess.run(['/tmp/psc_upstream_function_harness'],input=input_text,text=True,capture_output=True,check=True)
actual=np.array([[float(x) for x in line.split()] for line in p.stdout.splitlines()])
expected=np.array(expected)
assert actual.shape==expected.shape
assert np.allclose(actual,expected,rtol=2e-12,atol=1e-7)
result={'cases':len(cases),'datasets':6,'eps2':[.2,.4],
        'max_absolute_difference_by_column':np.max(np.abs(actual-expected),axis=0).tolist(),
        'columns':['estimate_2star','estimate_3star','gs_2star','gs_3star','sampler_calls'],
        'scope':'Original C++ CalcNSMaxDeg/CalcNLocSt function bodies with injected shared noise; verifies Python translation, not StatsLib RNG.'}
(OUT/'upstream_translation_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
