"""Independent finite review oracles for A4, not a universal machine proof.

Rank uses determinant/minor row-basis selection, rather than the production
Gaussian elimination. Floating operations use an independent positive-word
binary-search RNE oracle, rather than the prior arithmetic implementation.
No production verification module or prior-stage suite is imported.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction as Q
from functools import lru_cache
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import random
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114


def require(test, message):
    if not test:
        raise AssertionError(message)


def det(a):
    n = len(a)
    if n == 0:
        return Q(1)
    if n == 1:
        return a[0][0]
    return sum(((-1)**j * a[0][j] * det(tuple(
        tuple(row[k] for k in range(n) if k != j) for row in a[1:]))
        for j in range(n)), Q(0))


def row_basis(rows, width=None):
    width = len(rows[0]) if rows else (0 if width is None else width)
    selected = []
    for row in rows:
        if len(selected) == width:
            break
        trial = selected + [tuple(Q(x) for x in row)]
        size = len(trial)
        if any(det(tuple(tuple(r[j] for j in cols) for r in trial)) != 0
               for cols in combinations(range(width), size)):
            selected = trial
    return tuple(selected)


def rank(rows, width=None):
    return len(row_basis(rows, width))


def mul(a, b, *, out_width=None):
    m = len(b[0]) if b else (0 if out_width is None else out_width)
    return tuple(tuple(sum((row[t] * b[t][j] for t in range(len(b))), Q(0))
                       for j in range(m)) for row in a)


def zero(rows):
    return all(x == 0 for row in rows for x in row)


def concat(a, b):
    return tuple(tuple(x)+tuple(y) for x,y in zip(a,b))


def safe_response_exists(h, x, response):
    joined = concat(h,x)
    r = rank(joined)
    zero_prefix = (Q(0),) * len(h[0])
    return all(rank(joined + (zero_prefix+tuple(row),)) == r for row in response)


def reshape(values, n, d):
    return tuple(tuple(Q(x) for x in values[i*d:(i+1)*d]) for i in range(n))


def decode_matrix(record):
    return tuple(tuple(Q(x) for x in row) for row in record['rows'])


def check_algebra():
    import capacity_algebra as ca
    binary_h = [reshape(v,2,2) for v in product((0,1),repeat=4)]
    ternary_delta = [reshape(v,2,2) for v in product((-1,0,1),repeat=4)]
    response_sweeps = 0
    solver_cases = 0
    for h in binary_h:
        hm = ca.matrix(h)
        r = rank(h)
        candidates = [a for a in ternary_delta if zero(mul(a,h))]
        candidate_span = rank(tuple(tuple(x for row in a for x in row) for a in candidates))
        require(candidate_span == 2*(2-r), 'Independent annihilator enumeration dimension')
        report = ca.budget_report(hm,2)
        require(report['protected_rank']==r and
                report['unrestricted_update_space_dimension']==candidate_span,
                'Production abstract budget disagrees with independent enumeration')
        require(report['authorizes_bitwise_commit'] is False,
                'Algebra budget unexpectedly authorizes execution')
        for cap in (0,1,2,3):
            for q in range(min(cap,2-r)+1):
                a=ca.attaining_update(hm,2,cap,requested_rank=q)
                require(rank(a.rows)==q and zero(mul(a.rows,h)),
                        'Rank-attaining map failed independent output check')
        for x in binary_h:
            xm=ca.matrix(x)
            s=rank(concat(h,x))-r
            images=[mul(a,x) for a in candidates]
            image_dimension=rank(tuple(tuple(v for row in y for v in row) for y in images))
            silent=[a for a,y in zip(candidates,images) if zero(y)]
            silent_dimension=rank(tuple(tuple(v for row in a for v in row) for a in silent))
            budget=ca.budget_report(hm,2,x=xm)
            require(budget['target_quotient_rank']==s and
                    budget['unrestricted_response_image_dimension']==image_dimension==2*s and
                    budget['target_silent_update_space_dimension']==silent_dimension==2*(2-r-s),
                    'Response/silent dimensions differ from independent spans')
            response_sweeps+=1
            # All four binary output columns of each row give sixteen target
            # response matrices. Feasibility oracle uses row-space constraints.
            for response in binary_h:
                expected=safe_response_exists(h,x,response)
                q=rank(response)
                a, evidence=ca.solve_response(hm,xm,ca.matrix(response))
                require((a is not None)==expected,'Response feasibility mismatch')
                if expected:
                    require(zero(mul(a.rows,h)) and mul(a.rows,x)==response,
                            'Constructed response violates equations')
                    require(rank(a.rows)==q==evidence['minimum_required_update_rank'],
                            'Constructed update fails minimum-rank claim')
                    low,low_evidence=ca.solve_response(hm,xm,ca.matrix(response),max(0,q-1))
                    require((low is not None)==(q==0),'Rank cap did not constrain response')
                else:
                    witness=evidence['impossibility_witness']
                    alpha=decode_matrix(witness['alpha'])
                    xa=mul(x,alpha);ra=mul(response,alpha)
                    require(rank(concat(h,xa))==r and not zero(ra),
                            'Infeasible-response witness is invalid')
                solver_cases+=1
    rng=random.Random(SEED)
    random_cases=0
    for _ in range(40):
        n,d,m,t=(rng.randint(1,3),rng.randint(1,3),rng.randint(0,3),rng.randint(0,3))
        h=tuple(tuple(Q(rng.randint(-3,3),rng.randint(1,4)) for _ in range(m)) for _ in range(d))
        x=tuple(tuple(Q(rng.randint(-3,3),rng.randint(1,4)) for _ in range(t)) for _ in range(d))
        hm=ca.matrix(h,ncols=m);xm=ca.matrix(x,ncols=t)
        r=rank(h);c=d-r
        a=ca.attaining_update(hm,n)
        require(rank(a.rows)==min(n,c) and zero(mul(a.rows,h)),
                'Rational/rectangular attainment failure')
        response=mul(a.rows,x)
        constructed,evidence=ca.solve_response(hm,xm,ca.matrix(response,ncols=t))
        require(constructed is not None and zero(mul(constructed.rows,h)) and
                mul(constructed.rows,x)==response and rank(constructed.rows)==rank(response),
                'Rational/rectangular minimum response failure')
        random_cases+=1
    return {'binary_generator_matrices':16,'ternary_update_matrices_per_generator':81,
            'direct_annihilator_pairs':1296,'target_space_sweeps':response_sweeps,
            'prescribed_binary_response_cases':solver_cases,
            'seeded_rational_rectangular_cases':random_cases,
            'seed':SEED,'method':'Determinant/minor independent row basis, direct constraint consistency, finite update/response spans',
            'scope':'Finite exact checks; universal algebraic theorems remain handwritten'}


def format_parameters(fmt):
    if fmt=='BF16': return 8
    if fmt=='FP32': return 24
    raise ValueError('Unsupported independent format')


@lru_cache(maxsize=None)
def word_value(raw,fmt):
    p=format_parameters(fmt);f=p-1
    sign=-1 if raw & (1 << (p+7)) else 1
    exponent=(raw >> f)&255;fraction=raw&((1<<f)-1)
    if exponent==255:raise ValueError('Nonfinite word')
    if exponent==0:integer=fraction;power=-126-f
    else:integer=(1<<f)+fraction;power=exponent-127-f
    value=Q(integer*(1<<power)) if power>=0 else Q(integer,1<<(-power))
    return sign*value


@lru_cache(maxsize=None)
def round_word(value,fmt):
    value=Q(value);p=format_parameters(fmt);f=p-1
    negative=value<0;value=abs(value)
    maximum=(254<<f)|((1<<f)-1)
    largest=word_value(maximum,fmt)
    gap=largest-word_value(maximum-1,fmt)
    if value>=largest+gap/2:raise OverflowError('Independent RNE overflow')
    if value>=largest:raw=maximum
    else:
        lo,hi=0,maximum
        while lo+1<hi:
            middle=(lo+hi)//2
            if word_value(middle,fmt)<=value:lo=middle
            else:hi=middle
        dl=value-word_value(lo,fmt);dh=word_value(hi,fmt)-value
        raw=lo if dl<dh or (dl==dh and lo%2==0) else hi
    if negative and raw:raw|=1<<(p+7)
    return raw


def dense_words(weights,activation,fmt):
    result=[]
    for row in weights:
        acc=0
        for w,h in zip(row,activation):
            prod=round_word(word_value(w,fmt)*word_value(h,fmt),fmt)
            acc=round_word(word_value(acc,fmt)+word_value(prod,fmt),fmt)
        result.append(acc)
    return tuple(result)


def independent_domain(model,one):
    if model=='duplicate_feedback_v1':return ((0,0),(one,one))
    if model=='split_feedback_v1':return ((0,0),(one,one),(one,0))
    if model=='shared_axis_v1':return ((one,0),(0,one))
    raise ValueError('Unsupported independent model')


def check_discrete():
    import capacity_discrete as cd
    from a4_runtime import get_fp, load_a3
    ck=load_a3('certificate_kernel');fp=get_fp()
    rows=[]
    for fmt in ('BF16','FP32'):
        one=round_word(Q(1),fmt);eta=word_value(1,fmt)
        old=((one,0),(0,one))
        for alphabet in ((-1,0,1,2),(0,eta,1)):
            for model in ('duplicate_feedback_v1','split_feedback_v1','shared_axis_v1'):
                result=cd.enumerate_family(model,fmt,alphabet)
                domain=independent_domain(model,one)
                targets=((one,0),(0,one),(0,0))
                own=[]
                for record in result['records']:
                    candidate=tuple(tuple(row) for row in record['endpoint_words'])
                    delta=tuple(tuple(word_value(b,fmt)-word_value(a,fmt) for a,b in zip(ro,rn))
                                for ro,rn in zip(old,candidate))
                    alg=all(all(sum((delta[i][j]*word_value(h[j],fmt) for j in range(2)),Q(0))==0
                                for i in range(2)) for h in domain)
                    bit=all(dense_words(old,h,fmt)==dense_words(candidate,h,fmt) for h in domain)
                    actual=tuple(dense_words(candidate,h,fmt) for h in targets)
                    exact=tuple(tuple(sum((delta[i][j]*word_value(h[j],fmt) for j in range(2)),Q(0))
                                      for i in range(2)) for h in targets)
                    require(record['ALG']==alg and record['BIT']==bit and record['ALG_and_BIT']==(alg and bit),
                            'Independent endpoint ALG/BIT classification differs')
                    require(record['rank_effective_difference']==rank(delta),'Endpoint rank differs')
                    require(record['A_execution_total'] and tuple(tuple(r) for r in record['A_new_output_words'])==actual,
                            'Independent A output differs')
                    require(tuple(tuple(Q(v) for v in r) for r in record['exact_A_response'])==exact,
                            'Independent exact response differs')
                    own.append((alg,bit,rank(delta),actual,exact,any(x for row in delta for x in row)))
                for name,predicate in [
                    ('all_stored_candidates',lambda v:True),('ALG',lambda v:v[0]),
                    ('BIT',lambda v:v[1]),('ALG_and_BIT',lambda v:v[0] and v[1]),
                    ('ALG_not_BIT',lambda v:v[0] and not v[1]),
                    ('BIT_not_ALG',lambda v:v[1] and not v[0])]:
                    selected=[v for v in own if predicate(v)];g=result['groups'][name]
                    require(g['endpoints']==len(selected),'Endpoint cardinality differs')
                    require(g['raw_A_output_image_cardinality']==len({v[3] for v in selected}),
                            'Raw response cardinality differs')
                    require(g['exact_A_response_image_cardinality']==len({v[4] for v in selected}),
                            'Exact response cardinality differs')
                    hist={}
                    for v in selected:hist[str(v[2])]=hist.get(str(v[2]),0)+1
                    require(g['rank_histogram']==hist,'Rank histogram differs')
                rows.append({'format':fmt,'model':model,'alphabet':[str(Q(v)) for v in alphabet],
                             'endpoints':len(own),
                             'ALG':sum(v[0] for v in own),'BIT':sum(v[1] for v in own),
                             'intersection':sum(v[0] and v[1] for v in own),
                             'raw_BIT_responses':len({v[3] for v in own if v[1]}),
                             'every_endpoint_compared':True})
        # Independent full-format storage-collapse witness, not a search of
        # all finite endpoints: each coordinate is <= Fmax.
        p=format_parameters(fmt);f=p-1;maximum=(254<<f)|((1<<f)-1)
        largest=word_value(maximum,fmt)
        half=round_word(Q(1,2),fmt)
        require(dense_words(((maximum,maximum),),(half,half),fmt)==(maximum,),
                'Maximum endpoint fixture did not execute finitely')
        require(round_word(largest,fmt)==maximum,'Largest word mismatch')
        # Independent A3 live transactions and complete-domain boundaries.
        kernel=ck.CertificateKernel(fmt,'duplicate_feedback_v1',initial_bit=0)
        baseline=ck.CertificateKernel(fmt,'duplicate_feedback_v1',initial_bit=0)
        candidate=((0,one),(round_word(Q(2),fmt),round_word(Q(-1),fmt)))
        cert=kernel.prepare(candidate)
        before=kernel.snapshot();kernel.commit(cert)
        require(kernel.a_output((one,0))==(0,round_word(Q(2),fmt)),
                'Nonzero live A response absent')
        state=0
        for u in (0,1,1,0,1,0,0,1):
            observation=kernel.d_tick(one if u else 0)
            reference=baseline.d_tick(one if u else 0)
            state^=u
            require(observation==reference and kernel.state_word==(one if state else 0),
                    'Independent live recurrence failed')
        refused=[]
        def reject(label, action):
            old=kernel.snapshot()
            try:action()
            except (ValueError,TypeError,OverflowError):
                require(kernel.snapshot()==old,'Refusal mutated live bank')
                refused.append(label)
            else:raise AssertionError('Expected refusal absent: '+label)
        reject('stale_replay',lambda:kernel.commit(cert))
        fresh=kernel.prepare(old)
        def mutate(field,value):
            packet=json.loads(fresh)
            packet['payload']['descriptor'][field]=value
            # A checksum is publicly recomputable; semantic rechecking must
            # still reject false descriptors.
            canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
            packet['payload']['descriptor_sha256']=hashlib.sha256(canonical(packet['payload']['descriptor']).encode()).hexdigest()
            packet['payload_sha256']=hashlib.sha256(canonical(packet['payload']).encode()).hexdigest()
            return canonical(packet)
        reject('omitted_sites',lambda:kernel.commit(mutate('sites',[])))
        reject('sample_domain',lambda:kernel.commit(mutate('coverage','observed_samples')))
        reject('changed_policy',lambda:kernel.commit(mutate('numerical_policy','fma')))
        reject('changed_schedule',lambda:kernel.commit(mutate('schedule','in_place')))
        tiny=((one,1),(0,one))
        split=ck.CertificateKernel(fmt,'split_feedback_v1')
        packet=split.prepare(tiny)
        require(json.loads(packet)['payload']['proof']['exact_effective_delta_annihilates_registered_span'] is False,
                'Tiny finite equivalence incorrectly labeled algebraic')
        split.commit(packet)
        require(split.a_output((0,one))==(1,one),'Tiny A response lost')
        # ALG but not BIT: exact thirds null rows, tiny legal activation leaks.
        thirds=tuple(tuple(round_word(Q(2,3) if i==j else Q(-1,3),fmt) for j in range(3)) for i in range(3))
        require(all(sum((word_value(v,fmt) for v in row),Q(0))==0 for row in thirds),
                'Thirds stored row is not exact null')
        require(dense_words(thirds,(one,one,one),fmt)==(0,0,0) and
                dense_words(thirds,(1,1,1),fmt)==(1,1,1),'Thirds rounding boundary failed')
        try:ck.make_certificate('thirds_two_inputs_v1',fmt,((0,0,0),)*3,thirds)
        except ck.CertificateRejected:pass
        else:raise AssertionError('Tiny protected input was omitted')
        a=1<<p
        old_commit=((round_word(Q(a),fmt),0),(0,0))
        new_commit=((round_word(Q(a+1),fmt),round_word(Q(-1),fmt)),(0,0))
        residual=sum((word_value(b,fmt)-word_value(a0,fmt)
                      for a0,b in zip(old_commit[0],new_commit[0])),Q(0))
        require(residual==-1 and
                word_value(dense_words(new_commit,(one,one),fmt)[0],fmt)-
                word_value(dense_words(old_commit,(one,one),fmt)[0],fmt)==-1,
                'Independent effective commit leak failed')
        try:ck.make_certificate('commit_rounding_v1',fmt,old_commit,new_commit)
        except ck.CertificateRejected:pass
        else:raise AssertionError('Effective commit leakage accepted')
        rows.append({'format':fmt,'fixture':'full_format_and_transactions',
                     'full_format_ALG_endpoint_count_at_maximum':1,
                     'proof_reason':'x+y=2*Fmax with x,y<=Fmax forces x=y=Fmax',
                     'actual_maximum_dot_word':hex(maximum),'live_trace_ticks':8,
                     'refusals_preserved_snapshot':refused,
                     'full_rank_BIT_not_ALG':True,'ALG_not_BIT':True,
                     'ideal_null_commit_effective_residual':str(residual),
                     'effective_commit_certificate_refused':True})
    return {'families':[r for r in rows if 'endpoints' in r],
            'total_endpoint_comparisons':sum(r.get('endpoints',0) for r in rows),
            'boundary_records':[r for r in rows if 'fixture' in r],
            'method':'Independent exact IEEE decoding, word-search RNE, direct null products and response images',
            'scope':'Complete named candidate alphabets; theorem-only count for maximum endpoint fixture'}


def check_structural():
    import structural_budget as sb
    from a4_runtime import get_fp
    fp=get_fp();masks=tuple(tuple(i for i in range(3) if flags[i]) for flags in product((False,True),repeat=3))
    x=((Q(1),Q(0)),(Q(0),Q(1)),(Q(1),Q(1)))
    cases=0;independent_mask_rows=0
    for flat in product((0,1),repeat=6):
        h=reshape(flat,3,2);hm=sb.xp.matrix(h);xm=sb.xp.matrix(x)
        expected={}
        for mask in masks:
            admissible=[];images=[]
            for values in product((-1,0,1),repeat=len(mask)):
                v=[Q(0)]*3
                for j,a in zip(mask,values):v[j]=Q(a)
                if zero(mul((tuple(v),),h)):
                    admissible.append(tuple(v));images.append(mul((tuple(v),),x)[0])
            expected[mask]=(rank(tuple(admissible)),rank(tuple(images)))
            independent_mask_rows+=1
        for left in masks:
            for right in masks:
                report=sb.mask_budget(hm,(left,right),xm)
                require(report['masked_update_space_dimension']==expected[left][0]+expected[right][0],
                        'Masked algebra dimension differs from independent vector enumeration')
                require(report['masked_target_response_dimension']==expected[left][1]+expected[right][1],
                        'Masked response dimension differs from independent response spans')
                cases+=1
    formats=[]
    for fmt in ('BF16','FP32'):
        p=format_parameters(fmt);count=255*(1<<p)-1
        record=sb.finite_reserved_counts(fmt)
        require(record['canonical_finite_words']==count and record['reserved_endpoint_count']==count**2
                and record['A_e3_response_count']==count**2 and record['A_e1_response_count']==1,
                'Reserved full-format theorem count mismatch')
        one=round_word(Q(1),fmt);maximum=(254<<(p-1))|((1<<(p-1))-1)
        edge=(0,1,one,round_word(Q(-1),fmt),maximum,maximum|(1<<(p+7)),1<<(p+7)|1)
        pair_cases=0;tick_cases=0
        for theta in product(edge,repeat=2):
            bank=sb.reserved_bank(theta,fmt)
            exact=sb.validate_reserved_pair(sb.initial_bank(fmt),bank,fmt)
            require(exact['authorizes_live_commit'] is False,'Layout diagnostic grants live permission')
            out,_=sb.a_output(bank,fmt,target='e3')
            require(out==theta,'Reserved A output not injective')
            fixed,_=sb.a_output(bank,fmt,target='e1')
            require(fixed==(one,0),'Protected A target unexpectedly changed')
            for model in ('axis_reserve_v1','correlated_reserve_v1'):
                for q,u in product((0,1),repeat=2):
                    out,next_word,_=sb.tick_snapshot(bank,one if q else 0,one if u else 0,fmt,model)
                    expected=(one if q else 0,one if (u if model=='axis_reserve_v1' else q) else 0)
                    require(out==expected and next_word==(one if q!=u else 0),'Reserved layout state/output changed')
                    tick_cases+=1
            pair_cases+=1
        formats.append({'format':fmt,'canonical_finite_words_theorem':count,
                        'reserved_pair_cardinality_theorem':count**2,
                        'boundary_endpoint_pairs_executed':pair_cases,'state_input_layout_cases':tick_cases,
                        'A_e3_is_injective_on_checked_words':True,
                        'scope':'Full-format count proved separately; only listed edge pairs executed'})
    return {'binary_3x2_H_cases':64,'single_mask_row_enumerations':independent_mask_rows,
            'two_row_mask_reports':cases,'formats':formats,
            'read_scope':'D arithmetic excludes reserved entries after pure total admitted-bank validation; not entire Python instruction trace equality'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checks():
    started=time.perf_counter()
    names=('verify_review_checks.py','capacity_algebra.py','capacity_discrete.py','structural_budget.py','a4_runtime.py')
    before={name:digest(ROOT/name) for name in names}
    result={'schema':'dmwk-p2-a4-independent-review-v1','status':'running',
            'started_utc':datetime.now(timezone.utc).isoformat(),
            'evidence_type':'Independent finite exact/rounding/endpoint checks, not universal machine proof',
            'algebra':check_algebra(),'discrete':check_discrete(),
            'structural':check_structural()}
    require({name:digest(ROOT/name) for name in names}==before,'Reviewed source changed during execution')
    from a4_runtime import environment_metadata
    result.update({'status':'passed','elapsed_seconds':time.perf_counter()-started,
                   'SMT_queries':0,'proof_assistant_checked':False,'prior_stage_suites_rerun':False,
                   'source_sha256':before,'environment':environment_metadata(),
                   'sampling':'Exact section has 40 seeded rational cases; other independent sections exhaust named small sets or declared deterministic boundaries'})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'review_results.json')
    args=parser.parse_args()
    if not __debug__:raise SystemExit('Run without Python -O/-OO')
    result=run_checks()
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'seconds':result['elapsed_seconds'],'output':str(args.output)}))


if __name__=='__main__':
    main()
