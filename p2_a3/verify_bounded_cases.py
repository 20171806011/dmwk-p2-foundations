"""Finite A3 pointwise contract tests; no previous-stage verifier is run."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
import random
import time

from a3_runtime import get_fp
from bounded_contracts import pointwise_report, POLICY

SEED = 20261114


def run_checks():
    start = time.perf_counter()
    rng = random.Random(SEED)
    fp = get_fp()
    checks = 0
    samples = []
    refusals = []
    for fmt in ("BF16", "FP32"):
        enc = lambda x: fp.round_fraction(x, fmt)
        for i in range(80):
            k, d = rng.randint(1, 3), rng.randint(1, 4)
            row = lambda: tuple(enc(Fraction(rng.randint(-32, 32), 8)) for _ in range(d))
            old = tuple(row() for _ in range(k)); new = tuple(row() for _ in range(k))
            h = row()
            b = tuple(enc(Fraction(rng.randint(-16, 16), 8)) for _ in range(k))
            bp = b if i % 2 else tuple(enc(Fraction(rng.randint(-16,16),8)) for _ in range(k))
            result = pointwise_report(old,new,h,fmt,old_bias_words=b,new_bias_words=bp)
            assert result['authorizes_commit'] is False
            assert len(result['rows']) == k
            checks += 2
            for r in result['rows']:
                assert abs(Fraction(r['actual_output_difference'])) <= Fraction(r['absolute_output_bound'])
                assert Fraction(r['actual_output_difference']) == (Fraction(r['exact_effective_affine_response'])+Fraction(r['new_error'])-Fraction(r['old_error']))
                checks += 2
            samples.append({'format':fmt,'index':i,'shape':[k,d],'report':result})
        # Single-input equality can coexist with a nonzero exact difference.
        one=enc(1); zero=enc(0)
        invisible=pointwise_report(((one,zero),),((one,1),),(one,one),fmt)
        assert invisible['all_output_words_equal_on_this_input']
        assert Fraction(invisible['rows'][0]['exact_effective_affine_response']) != 0
        assert invisible['authorizes_commit'] is False
        checks += 3
        samples.append({'format':fmt,'id':'rounding_invisible_exact_change','report':invisible})
        # Preserve exact affine bias order and demonstrate an actual bias edit.
        bias=pointwise_report(((zero,),),((zero,),),(one,),fmt,
                              old_bias_words=(one,),new_bias_words=(enc(2),))
        assert bias['rows'][0]['actual_output_difference']=='1'
        assert bias['rows'][0]['exact_effective_affine_response']=='1'
        checks += 2
        samples.append({'format':fmt,'id':'explicit_bias_endpoint','report':bias})
        def refuse(label, fn):
            nonlocal checks
            try: fn()
            except (ValueError, TypeError, OverflowError) as exc:
                refusals.append({'format':fmt,'case':label,'error_type':type(exc).__name__})
                checks += 1
            else: raise AssertionError('Invalid report accepted: '+label)
        base=(((one,),),((one,),),(one,),fmt)
        for policy in ('fma','pairwise','fused','sample_global'):
            refuse(policy,lambda p=policy:pointwise_report(*base,policy=p))
        refuse('boolean_word',lambda:pointwise_report(((True,),),((one,),),(one,),fmt))
        refuse('negative_zero',lambda:pointwise_report(((fp.get_format(fmt).sign_mask,),),((one,),),(one,),fmt))
        refuse('mismatched_shape',lambda:pointwise_report(((one,),),((one,zero),),(one,),fmt))
        refuse('overflow',lambda:pointwise_report(((fp.get_format(fmt).max_finite_word,),),((one,),),(enc(2),),fmt))
    return {'status':'passed','seed':SEED,'checks':checks,
            'seeded_pointwise_cases':160,'deterministic_cases':4,
            'expected_refusals':len(refusals),'unexpected_failures':0,
            'records':samples,'refusals':refusals,
            'elapsed_seconds':time.perf_counter()-start,
            'scope':'A posteriori pointwise reports, never commit authorization; separate handwritten theorem',
            'SMT_queries':0}


if __name__=='__main__':
    if not __debug__: raise SystemExit('Run without -O/-OO')
    result=run_checks()
    out=Path(__file__).resolve().parent/'bounded_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','refusals')}))
