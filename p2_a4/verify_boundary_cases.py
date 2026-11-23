"""Constructive A4 capacity boundaries, not a rerun of earlier stage suites."""
from __future__ import annotations
from fractions import Fraction
from pathlib import Path
import json
import time

from a4_runtime import get_fp, load_a2, load_a3

SEED = 20261114


def run_checks():
    start = time.perf_counter()
    fp = get_fp(); xp = load_a2('exact_projection'); ck = load_a3('certificate_kernel')
    checks = 0; records = []

    def check(condition, message):
        nonlocal checks
        if not condition: raise AssertionError(message)
        checks += 1

    def decoded(rows, fmt):
        return xp.matrix(tuple(tuple(fp.decode_word(x,fmt) for x in row) for row in rows))

    def dense(rows, h, fmt):
        result = []; audit = fp.Audit()
        for row in rows:
            acc = 0
            for a,b in zip(row,h):
                acc = fp.add_words(acc,fp.mul_words(a,b,fmt,audit),fmt,audit)
            result.append(acc)
        return tuple(result)

    for fmt in ('BF16','FP32'):
        spec = fp.get_format(fmt); enc = lambda x: fp.round_fraction(x,fmt)
        one = enc(1)
        # The candidate family, not all F^(3x3), is exhaustively classified.
        H = xp.matrix(((1,),(1,),(1,)))
        P = xp.projection(H).P_perp
        Q = tuple(tuple(enc(x) for x in row) for row in P.rows)
        old = ((0,0,0),)*3
        protected = ((one,)*3,(1,)*3)
        classes = []
        for candidate in (old,Q):
            delta = xp.sub(decoded(candidate,fmt),decoded(old,fmt))
            alg = xp.matmul(delta,H)==xp.zeros(3,1)
            try:
                cert=ck.make_certificate('thirds_two_inputs_v1',fmt,old,candidate)
                ck.check_certificate(cert,'thirds_two_inputs_v1',fmt,old)
                bit=True
            except ck.CertificateRejected: bit=False
            actual=tuple(dense(candidate,h,fmt) for h in protected)
            classes.append({'candidate_words':candidate,'ALG':alg,'BIT':bit,
                            'protected_outputs':actual,'A_e1_output':dense(candidate,(one,0,0),fmt)})
        check([x['ALG'] for x in classes]==[True,True],'Thirds stored algebra family')
        check([x['BIT'] for x in classes]==[True,False],'Thirds complete-domain BIT family')
        check(classes[1]['protected_outputs'][0]==(0,0,0),'Thirds basis output zero')
        check(classes[1]['protected_outputs'][1]==(1,1,1),'Thirds tiny input leaks')
        records.append({'id':'ALG_not_BIT_family','format':fmt,'candidate_count':2,
                        'ALG_count':2,'BIT_count':1,'intersection_count':1,
                        'protected_rank':1,'algebraic_dimension':6,'records':classes,
                        'scope':'Complete two-endpoint candidate family on the fixed registered stateless domain'})

        # Full protected span does not force a singleton finite BIT class.
        old2=((one,0),(0,one)); tiny=((one,1),(0,one))
        H2=xp.matrix(((1,1),(1,0)))
        d=xp.sub(decoded(tiny,fmt),decoded(old2,fmt))
        check(xp.rank(H2)==2,'Split protected full rank')
        check(xp.matmul(d,H2)!=xp.zeros(2,2),'Tiny edit is not ALG')
        cert=ck.make_certificate('split_feedback_v1',fmt,old2,tiny)
        checked=ck.check_certificate(cert,'split_feedback_v1',fmt,old2)
        check(not checked['payload']['proof']['exact_effective_delta_annihilates_registered_span'],
              'Certificate must not relabel BIT as ALG')
        kernel=ck.CertificateKernel(fmt,'split_feedback_v1'); reference=ck.CertificateKernel(fmt,'split_feedback_v1')
        before=kernel.a_output((0,one)); kernel.commit(cert); after=kernel.a_output((0,one))
        check(before==(0,one) and after==(1,one),'Tiny accepted A response')
        for bit in (0,1,1,0,1,0,0,1):
            check(kernel.d_tick(enc(bit))==reference.d_tick(enc(bit)),'Tiny D feedback equality')
        records.append({'id':'full_rank_BIT_not_ALG_family','format':fmt,'candidate_count':2,
                        'ALG_count':1,'BIT_count':2,'intersection_count':1,
                        'protected_rank':2,'algebraic_dimension':0,
                        'old_words':old2,'new_words':tiny,'A_old_words':before,'A_new_words':after,
                        'paired_feedback_ticks':8,'scope':'Two-endpoint family; full registered domain per certificate'})

        # Positive real freedom, but no distinct exact-safe endpoint anywhere
        # in the complete finite target format at this saturated old bank.
        maximum=spec.max_finite_word; maximum_value=fp.decode_word(maximum,fmt)
        saturated=((maximum,maximum),(maximum,maximum))
        half=(enc(Fraction(1,2)),)*2
        check(dense(saturated,half,fmt)==(maximum,maximum),'Saturated baseline finite execution')
        near=((maximum-1,maximum),(maximum,maximum))
        delta=xp.sub(decoded(near,fmt),decoded(saturated,fmt))
        hhalf=xp.matrix(((Fraction(1,2),),(Fraction(1,2),)))
        residual=xp.matmul(delta,hhalf)
        check(residual.rows[0][0]<0,'Adjacent stored endpoint violates exact constraint')
        N=2*(255*(1<<(spec.p-1)))-1
        zero=((0,0),(0,0)); cancel=((one,enc(-1)),(enc(2),enc(-2)))
        check(dense(cancel,half,fmt)==(0,0),'Stored cancellation witness at zero baseline')
        check(xp.matmul(decoded(cancel,fmt),hhalf)==xp.zeros(2,1),'Exact cancellation witness')
        records.append({'id':'same_rank_different_complete_format_ALG_counts','format':fmt,
                        'protected_activation_words':half,'protected_rank':1,'algebraic_dimension':2,
                        'canonical_finite_word_count':N,
                        'zero_old_endpoint_ALG_count_proved':N*N,
                        'saturated_old_endpoint_ALG_count_proved':1,
                        'maximum_value':str(maximum_value),'old_saturated_words':saturated,
                        'near_candidate_words':near,'near_exact_residual':xp.serialize(residual),
                        'zero_old_words':zero,'nonzero_cancel_words':cancel,
                        'count_evidence':'Handwritten full-format counting/impossibility proof; only displayed execution probes run',
                        'scope':'Declared stateless half-ones diagnostic; not a new A3 registry or live authorization'})

        # A proposed null delta must not be substituted for the effective one.
        a=1<<spec.p
        old_commit=((enc(a),0),(0,0)); new_commit=((enc(a+1),enc(-1)),(0,0))
        ideal=xp.matrix(((1,-1),(0,0))); hc=xp.matrix(((1,),(1,)))
        eff=xp.sub(decoded(new_commit,fmt),decoded(old_commit,fmt))
        check(xp.matmul(ideal,hc)==xp.zeros(2,1),'Ideal commit proposal null')
        check(xp.matmul(eff,hc).rows[0][0]==-1,'Actual commit difference nonnull')
        try:ck.make_certificate('commit_rounding_v1',fmt,old_commit,new_commit)
        except ck.CertificateRejected:rejected=True
        else:rejected=False
        check(rejected,'Actual commit endpoint must refuse')
        records.append({'id':'ideal_not_effective_rank_budget','format':fmt,
                        'old_words':old_commit,'new_words':new_commit,
                        'effective_difference':xp.serialize(eff),'candidate_refused':rejected})

    # Target quotient relations restrict desired responses, not just ranks.
    H=xp.matrix(((1,),(0,)))
    X=xp.matrix(((0,1),(1,1)))
    alpha=xp.matrix(((-1,),(1,)))
    feasible=xp.matrix(((0,1),)); good=xp.matrix(((1,1),)); bad=xp.matrix(((1,2),))
    check(xp.matmul(X,alpha)==H,'Target relation differs only by protected input')
    check(xp.matmul(feasible,H)==xp.zeros(1,1),'Constructed response protects D')
    check(xp.matmul(feasible,X)==good,'Feasible tied target response')
    check(xp.matmul(bad,alpha).rows[0][0]==1,'Impossible target violates quotient relation')
    records.append({'id':'target_compatibility_not_rank_alone','H':xp.serialize(H),'X':xp.serialize(X),
                    'relation':xp.serialize(alpha),'feasible_response':xp.serialize(good),
                    'impossible_response':xp.serialize(bad),'constructive_update':xp.serialize(feasible),
                    'scope':'Exact rational construction and explicit impossibility witness'})

    return {'status':'passed','seed':SEED,'random_sampling':False,'checks':checks,
            'format_case_count':8,'additional_exact_target_cases':1,'records':records,
            'unexpected_failures':0,'elapsed_seconds':time.perf_counter()-start,
            'scope':'Constructive A4 capacity boundaries; finite candidate counts versus separate full-format proofs',
            'SMT_queries':0}


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run without -O/-OO')
    result=run_checks();out=Path(__file__).resolve().parent/'boundary_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'}))
