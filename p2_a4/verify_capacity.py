"""Aggregate A4 evidence while preserving all previous-stage artifacts."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114
SECTIONS = (
    ("exact_algebra", "verify_algebra_cases"),
    ("discrete_endpoints", "verify_discrete_cases"),
    ("structural_budget", "verify_structural_cases"),
    ("capacity_boundaries", "verify_boundary_cases"),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_previous():
    saved = json.loads((ROOT/'dependency_baseline.json').read_text())
    for name, expected in saved['files'].items():
        p = ROOT.parent/name
        if not p.is_file() or sha(p) != expected:
            raise ValueError('Previous artifact missing or changed: '+name)
    return len(saved['files'])


def sources():
    files = sorted(ROOT.glob('*.py'))+[ROOT/'requirements.txt', ROOT/'dependency_baseline.json']
    return {p.name:sha(p) for p in files}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'verification_results.json')
    args=ap.parse_args();start=time.perf_counter();phase='preflight'
    result={'schema':'dmwk-p2-a4-verification-v1','status':'running','seed':SEED,
            'started_utc':datetime.now(timezone.utc).isoformat(),
            'planned_sections':[x for x,_ in SECTIONS],'attempted_sections':[],
            'sections':{},'section_seconds':{},'SMT_queries':0,
            'proof_assistant_checked':False,'prior_stage_suites_rerun':False,
            'P2_B1_started':False}
    try:
        if not __debug__:raise ValueError('Run verification without -O/-OO')
        import numpy as np
        if np.__version__!='2.3.5':raise ValueError('Recorded reference requires NumPy 2.3.5')
        result['unchanged_prior_artifacts']=check_previous()
        before=sources();result['source_sha256']=before
        from a4_runtime import environment_metadata
        result['environment']=environment_metadata()
        for name,module in SECTIONS:
            phase=name;result['attempted_sections'].append(name);t0=time.perf_counter()
            value=importlib.import_module(module).run_checks()
            if type(value) is not dict or value.get('status')!='passed':
                raise ValueError('Section did not pass: '+name)
            if value.get('seed',SEED)!=SEED:raise ValueError('Unexpected seed: '+name)
            if value.get('failures',0)!=0 or value.get('unexpected_failures',0)!=0:
                raise ValueError('Unexpected failures: '+name)
            json.dumps(value,allow_nan=False)
            result['sections'][name]=value
            result['section_seconds'][name]=time.perf_counter()-t0
        phase='postflight'
        if sources()!=before:raise ValueError('A4 source changed during execution')
        if check_previous()!=result['unchanged_prior_artifacts']:
            raise ValueError('Prior artifact inventory changed')
        result['status']='passed'
    except Exception as exc:
        result['status']='failed'
        result['failure']={'phase':phase,'type':type(exc).__name__,'message':str(exc)}
    result['completed_sections']=len(result['sections'])
    result['unexecuted_sections']=[n for n,_ in SECTIONS if n not in result['attempted_sections']]
    result['completed_utc']=datetime.now(timezone.utc).isoformat()
    result['total_seconds']=time.perf_counter()-start
    result['evidence_scope']={
        'exact':'Finite checks of exact rational constructions; universal algebra theorems are separate handwritten proofs.',
        'discrete':'Counts of explicit endpoint families, not all FP32 banks unless a separate full-format proof is given.',
        'structural':'Small fixed layout and protected arithmetic graph, not a completed compiler/backend project.',
        'response':'Distinct attainable outputs and exact quotient response dimensions, not learning-performance evidence.',
        'BF16':'Software RNE; no native BF16 certification.',
        'FP32':'Local scalar CPU execution audited against exact rational RNE.',
        'excluded':'GPU, general concurrency, arbitrary compiler optimization, full host-stack machine proof and later stages.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'completed_sections':result['completed_sections'],
                      'unexecuted_sections':result['unexecuted_sections'],'seconds':result['total_seconds'],
                      'failure':result.get('failure'),'output':str(args.output)}))
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
