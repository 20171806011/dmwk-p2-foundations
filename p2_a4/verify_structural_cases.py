"""Finite A4 row-mask and reserved-layout checks; no old suite is run."""
from __future__ import annotations

from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import time

from a4_runtime import get_fp, load_a2
import structural_budget as sb

SEED = 20261114
xp = load_a2("exact_projection")


def _constraint_budget(h, masks, x):
    """A separate flattened-entry constraint matrix, not the row formula."""
    cells = [(i, j) for i, mask in enumerate(masks) for j in mask]
    c = xp.matrix(tuple(tuple(h.rows[j][col] if i == out else Fraction(0)
                             for i,j in cells)
                        for out in range(len(masks)) for col in range(h.ncols)),
                  ncols=len(cells))
    z = xp.nullspace(c)
    response = xp.matrix(tuple(tuple(x.rows[j][col] if i == out else Fraction(0)
                                    for i,j in cells)
                               for out in range(len(masks)) for col in range(x.ncols)),
                         ncols=len(cells))
    return len(cells)-xp.rank(c), xp.rank(xp.matmul(response, z))


def run_checks():
    start = time.perf_counter(); rng = random.Random(SEED); fp = get_fp()
    checks = 0; mask_cases = 0; random_cases = 0
    masks = tuple(tuple(j for j in range(3) if bitmask & (1 << j)) for bitmask in range(8))
    x = xp.matrix(((1, 0), (0, 0), (0, 1)))
    for coeffs in product((-1, 0, 1), repeat=3):
        h = xp.matrix(tuple((v,) for v in coeffs))
        for row_masks in product(masks, repeat=2):
            result = sb.mask_budget(h, row_masks, x)
            dim, response = _constraint_budget(h, row_masks, x)
            assert result['masked_update_space_dimension'] == dim
            assert result['masked_target_response_dimension'] == response
            assert result['masked_update_space_dimension'] <= result['geometric_update_space_dimension']
            assert result['authorizes_live_commit'] is False
            checks += 4; mask_cases += 1
    for _ in range(60):
        d, n, m, a = rng.randint(1, 4), rng.randint(1, 3), rng.randint(0, 3), rng.randint(0, 3)
        h = xp.matrix(tuple(tuple(Fraction(rng.randint(-3,3), rng.randint(1,3)) for _ in range(m))
                            for _ in range(d)), ncols=m)
        x = xp.matrix(tuple(tuple(Fraction(rng.randint(-3,3), rng.randint(1,3)) for _ in range(a))
                            for _ in range(d)), ncols=a)
        row_masks = tuple(tuple(j for j in range(d) if rng.randrange(2)) for _ in range(n))
        result = sb.mask_budget(h,row_masks,x)
        dim,response = _constraint_budget(h,row_masks,x)
        assert result['masked_update_space_dimension']==dim
        assert result['masked_target_response_dimension']==response
        checks += 2; random_cases += 1

    layouts = [sb.layout_budget(name) for name in sb.MODELS]
    assert layouts[0]['protected_rank']==2 and layouts[0]['geometric_update_space_dimension']==2
    assert layouts[1]['protected_rank']==1 and layouts[1]['geometric_update_space_dimension']==4
    assert all(x['masked_update_space_dimension']==2 for x in layouts)
    assert [x['mask_dimension_loss'] for x in layouts]==[0,2]
    checks += 4
    no_coordinate = sb.mask_budget(xp.matrix(((1,), (1,), (1,))), ((), ()))
    assert no_coordinate['geometric_update_space_dimension']==4 and no_coordinate['masked_update_space_dimension']==0
    checks += 1

    formats=[];refusals=[]
    for fmt in ('BF16','FP32'):
        spec=fp.get_format(fmt); one=fp.encode_constant(1,fmt)
        base=sb.initial_bank(fmt)
        theta_alphabet=tuple(fp.encode_constant(t,fmt) for t in (-2,-1,0,1,2))
        response_set=set(); pair_cases=0; point_cases=0
        for theta in product(theta_alphabet,repeat=2):
            bank=sb.reserved_bank(theta,fmt)
            pair=sb.validate_reserved_pair(base,bank,fmt)
            assert pair['protected_read_words_unchanged'] and not pair['authorizes_live_commit']
            response,_=sb.a_output(bank,fmt)
            silent,_=sb.a_output(bank,fmt,target='e1')
            assert response==theta and silent==(one,0)
            checks += 2; response_set.add(response); pair_cases += 1
            for model in sb.MODELS:
                for q,u in product((0,one),repeat=2):
                    before,_=sb.d_call(base,q,u,fmt,model)
                    after,_=sb.d_call(bank,q,u,fmt,model)
                    assert before==after==(q,u if model=='axis_reserve_v1' else q)
                    checks += 1;point_cases += 1
        assert len(response_set)==25
        checks += 1
        # Endpoint-word coverage includes actual scalar multiply-by-one/add-zero.
        boundary={0,1,spec.sign_mask|1,one,fp.encode_constant(-1,fmt),
                  spec.fraction_mask,(1<<spec.fraction_bits),spec.max_finite_word,
                  spec.sign_mask|spec.max_finite_word,spec.sign_mask,
                  spec.exponent_mask<<spec.fraction_bits,
                  (spec.exponent_mask<<spec.fraction_bits)|1}
        raw_words=range(1<<16) if fmt=='BF16' else sorted(boundary|{rng.getrandbits(32) for _ in range(512)})
        accepted=0;rejected=0;transcript=hashlib.sha256();audit_sum={k:0 for k in
            ('native_multiply','native_add','software_multiply','software_add','exact_sums','native_oracle_checks')}
        word_start=time.perf_counter()
        for raw in raw_words:
            is_finite=((raw>>spec.fraction_bits)&spec.exponent_mask)!=spec.exponent_mask
            expected=is_finite and raw!=spec.sign_mask
            try: output,audit=sb.probe_reserved_scalar(raw,fmt)
            except ValueError:
                assert not expected
                rejected+=1;transcript.update(f'{raw}:refused;'.encode('ascii'))
            else:
                assert expected and output==raw
                accepted+=1;transcript.update(f'{raw}:{output};'.encode('ascii'))
                for k in audit_sum:audit_sum[k]+=audit[k]
            checks+=1
        if fmt=='BF16':
            assert accepted==sb.canonical_finite_word_count(fmt)==65279 and rejected==257
            checks+=1
        word_seconds=time.perf_counter()-word_start
        # Compare both pure executions against a separate Boolean recurrence.
        trace_count=ticks=bank_replacements=0
        for model in sb.MODELS:
            for initial in (0,1):
                for inputs in product((0,1),repeat=5):
                    q0=q1=one if initial else 0;oracle=initial
                    for index,u in enumerate(inputs):
                        theta=(theta_alphabet[(index+initial)%5],theta_alphabet[(index+u+2)%5])
                        bank=sb.reserved_bank(theta,fmt)
                        old_obs,q0,_=sb.tick_snapshot(base,q0,one if u else 0,fmt,model)
                        new_obs,q1,_=sb.tick_snapshot(bank,q1,one if u else 0,fmt,model)
                        oracle ^= u
                        assert old_obs==new_obs and q0==q1==(one if oracle else 0)
                        checks+=1;ticks+=1;bank_replacements+=1
                    trace_count+=1
        changed=sb.reserved_bank((one,fp.encode_constant(2,fmt)),fmt)
        before,_=sb.a_output(base,fmt);after,witness_audit=sb.a_output(changed,fmt)
        assert before==(0,0) and after==(one,fp.encode_constant(2,fmt))
        checks+=1
        def refuse(label,fn):
            nonlocal checks
            try:fn()
            except (ValueError,TypeError) as exc:
                refusals.append({'format':fmt,'case':label,'exception':type(exc).__name__})
                checks+=1
            else:raise AssertionError('Invalid layout request accepted: '+label)
        refuse('protected_coordinate_edit',lambda:sb.validate_reserved_pair(base,((one,one,0),(0,one,0)),fmt))
        refuse('negative_zero',lambda:sb.reserved_bank((spec.sign_mask,0),fmt))
        refuse('nonfinite',lambda:sb.reserved_bank((spec.exponent_mask<<spec.fraction_bits,0),fmt))
        refuse('boolean_word',lambda:sb.reserved_bank((True,0),fmt))
        refuse('mutable_bank_rows',lambda:sb.d_call([list(r) for r in base],0,0,fmt))
        refuse('invalid_input_bit',lambda:sb.tick_snapshot(base,1,0,fmt))
        refuse('unknown_model',lambda:sb.d_call(base,0,0,fmt,'sampled_model'))
        refuse('unknown_A_target',lambda:sb.a_output(base,fmt,target='arbitrary_vector'))
        for policy in ('dense_gemm','fma','fused','pairwise'):
            refuse(policy,lambda p=policy:sb.tick_snapshot(base,0,0,fmt,policy=p))
        formats.append({'format':fmt,'small_endpoint_pair_cases':pair_cases,
                        'small_endpoint_distinct_A_e3_responses':len(response_set),
                        'small_endpoint_distinct_A_e1_responses':1,
                        'protected_model_input_cases':point_cases,
                        'stored_scalar_word_coverage':{'scope':'all 65536 BF16 raw words' if fmt=='BF16' else '512 seeded FP32 draws plus deduplicated boundary words',
                            'words':accepted+rejected,'accepted':accepted,'rejected':rejected,
                            'output_identity_digest':transcript.hexdigest(),'arithmetic_counts':audit_sum,
                            'elapsed_seconds':word_seconds},
                        'theorem_counts':sb.finite_reserved_counts(fmt),
                        'paired_trace_count':trace_count,'paired_ticks':ticks,
                        'pure_bank_replacements':bank_replacements,
                        'nonzero_A_response':{'old_words':list(before),'new_words':list(after),'target':'e3','audit':witness_audit},
                        'transaction_scope':'Pure immutable endpoint substitutions only; A3 live certificate/rollback tests are separate'})
    for bad_masks in (((0,0),),((1,0),),((True,),),((3,),),([0],)):
        try:sb.mask_budget(xp.matrix(((1,),(0,),(0,))),bad_masks)
        except ValueError:checks+=1
        else:raise AssertionError('Malformed mask accepted')
    return {'schema':'dmwk-p2-a4-structural-verification-v1','status':'passed','seed':SEED,
            'checks':checks,'unexpected_failures':0,'exhaustive_row_mask_cases':mask_cases,
            'seeded_rectangular_mask_cases':random_cases,'layouts':layouts,
            'no_independent_coordinate_example':no_coordinate,'formats':formats,
            'explicit_refusals':len(refusals)+5,'refusals':refusals,
            'runtime_seconds':time.perf_counter()-start,'SMT_queries':0,
            'scope':'Finite mask/layout implementation evidence; general budget and full-format pair counts are separately proved by hand'}


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run without -O/-OO')
    result=run_checks()
    out=Path(__file__).resolve().parent/'structural_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('layouts','formats','refusals','no_independent_coordinate_example')}))
