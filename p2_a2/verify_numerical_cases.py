"""P2-A2 numerical experiments and adversarial examples, called by main verifier."""
from __future__ import annotations
from fractions import Fraction
import random
import time
import numpy as np
from exact_projection import (matrix,eye,zeros,sub,add,matmul,transpose,projection,
                              rank,serialize,frobenius_squared)
from numerical_projection import (quantize_matrix,stored_words,svd_projection,
    dot,dot_words,executed_matmul,commit_weights,perturbation_certificate,
    norm_upper,sqrt_upper,qstr,NumericalRejected,from_numpy)
from p1_runtime import get_fp

SEED=20261114

class Checks:
    def __init__(self):self.total=0;self.expected_rejections=0
    def __call__(self,condition,message):
        self.total+=1
        if not condition:raise AssertionError(message)
    def rejects(self,action,message,classes=(ValueError,)):
        self.total+=1
        try:action()
        except classes:self.expected_rejections+=1;return
        raise AssertionError(message)


def _column(values):return matrix(tuple((Fraction(x),) for x in values))


def quantized_projectors(check):
    cases=[]
    for fmt in ('BF16','FP32'):
        for n in (3,6):
            h=_column((1,)*n);cert=projection(h);q,words=quantize_matrix(cert.P_perp,fmt)
            residual=matmul(q,h)
            output,operations=executed_matmul(q,h,fmt)
            idem=sub(matmul(q,q),q)
            check(q!=cert.P_perp,'Non-dyadic projector must not round identically')
            check(idem!=zeros(n,n),'Rounded projector not generally idempotent')
            if n==3:
                check(residual==zeros(n,1),'Power-of-two coefficient relation preserves this particular kernel')
                check(output==zeros(n,1),'The measured 1/3 row reduction should be zero in this specified order')
            else:
                check(residual!=zeros(n,1),'Six-coordinate quantization should break kernel')
                expected=Fraction(-3,1024) if fmt=='BF16' else Fraction(-3,67108864)
                check(all(row[0]==expected for row in residual.rows),'Expected exact decoded six-coordinate residual')
            scaled_probe=None
            if n==3:
                fp=get_fp();eta=fp.decode_word(1,fmt);small_h=_column((eta,)*3)
                small_output,small_ops=executed_matmul(q,small_h,fmt)
                check(matmul(q,small_h)==zeros(3,1),'Scaled input remains in the exact quantized kernel')
                check(small_output==small_h,'Underflow makes each ordered output equal min subnormal')
                check(all(not op.relative_model_holds and op.gamma_bound is None for op in small_ops),
                      'Scaled-input rounding cannot use relative-only gamma certificate')
                scaled_probe={'id':'C3c_basis_probe_zero_but_other_legal_input_leaks',
                    'declared_legal_test_set':'{ones(3), eta*ones(3)}; eta is the target min positive subnormal',
                    'input':serialize(small_h),'exact_decoded_residual':serialize(matmul(q,small_h)),
                    'ordered_output':serialize(small_output),'output_raw_words_hex':[hex(op.output_word) for op in small_ops],
                    'row_executions':[op.record() for op in small_ops],
                    'meaning':'Zero floating residual at the generating vector does not certify floating zero on the entire legal activation set sharing its span.'}
            # Standalone representable nonzero zero-sum row exists even though P cannot be stored.
            v=matrix(((1,-1)+(0,)*(n-2),))
            check(stored_words(v,fmt) and matmul(v,h)==zeros(1,1), 'Projector representability differs from null-vector representability')
            cases.append({'id':'C3_nonrepresentable_projector' if n==3 else 'C3b_quantization_breaks_kernel',
                'format':fmt,'H':serialize(h),'exact_projector':serialize(cert.P_perp),
                'quantized_projector':serialize(q),'quantized_words_hex':[[hex(x) for x in row] for row in words],
                'exact_decoded_residual':serialize(residual),'ordered_actual_residual':serialize(output),
                'exact_idempotence_defect_F_squared':qstr(frobenius_squared(idem)),
                'exact_projector_error_F_squared':qstr(frobenius_squared(sub(q,cert.P_perp))),
                'representable_nonzero_null_row':serialize(v),
                'ordered_row_executions':[r.record() for r in operations],
                'scaled_stored_input_probe':scaled_probe,
                'status':'passed','scope':'Explicit finite projector/format instance; no automatic bitwise patch approval'})
    return cases


def svd_cases(check):
    fixtures=[('zero',zeros(2,2)),('identity',eye(2)),
        ('repeated_and_zero_columns',matrix(((1,1,0),(1,1,0),(1,1,0)))),
        ('near_full_rank_diagonal',matrix(((1,0),(0,Fraction(1,2**30))))),
        ('input_conversion_collapse',matrix(((1,1),(1,1+Fraction(1,2**30)))))]
    records=[]
    for name,h in fixtures:
        for dtype in ('float64','float32'):
            for rtol in (1e-6,1e-12):
                item=svd_projection(h,dtype,rtol=rtol,atol=0)
                p=item['proposal'];diag=item['diagnostics']
                check(diag['original_exact_rank']==rank(h),'Original rank ground truth')
                check(diag['dtype']==dtype,'Actual numerical input dtype')
                if dtype=='float32':check('f->fff' in diag['solver_dispatch'],'Must explicitly dispatch single precision, not public promoted API')
                if name=='near_full_rank_diagonal':
                    expected=1 if rtol==1e-6 else 2
                    check(diag['numerical_effective_rank']==expected,'Threshold determines apparent capacity')
                    check(rank(h)==2,'Near-rank-deficient input remains exact full rank')
                if name=='input_conversion_collapse' and dtype=='float32':
                    check(diag['converted_input_exact_rank']==1,'FP32 input conversion loses original small direction')
                bfq,_=quantize_matrix(p,'BF16')
                bh,_=quantize_matrix(h,'BF16')
                diag.update(name=name,H=serialize(h),
                    BF16_quantized_projector=serialize(bfq),
                    BF16_quantized_projector_original_H_residual=serialize(matmul(bfq,h)),
                    BF16_input_exact_rank=rank(bh),
                    status='passed',
                    id='C5_numerical_rank_misclassification' if name in ('near_full_rank_diagonal','input_conversion_collapse') else 'SVD_comparison')
                records.append(diag)
    boundary=svd_projection(eye(2),'float32',rtol=1-2**-30)
    check(boundary['diagnostics']['numerical_effective_rank']==2,
          'Recorded binary64 cutoff must not be silently rounded up to float32')
    # Sign and basis choice cancel algebraically; floating basis multiplication has its own error.
    q=matrix(((1,0),(0,1),(0,0)));rotation=matrix(((Fraction(3,5),Fraction(-4,5)),(Fraction(4,5),Fraction(3,5))))
    qr=matmul(q,rotation)
    check(matmul(q,transpose(q))==matmul(qr,transpose(qr)), 'Exact orthogonal basis rotation leaves projector invariant')
    a=np.array([[1.,0.],[0.,1.],[0.,0.]],dtype=np.float32)
    check(np.array_equal(a@a.T,(-a)@(-a).T),'Concrete SVD sign flip cancels in projector')
    return {'cases':records,'sample_count':len(records),'passed':len(records),'unexpected_failures':0,
        'threshold_comparison_boundary':boundary['diagnostics'],
        'basis_choice_checks':2,
        'scope':'Two explicit threshold choices; five fixtures; FP64 and forced single-precision SVD interface. BF16 quantizes inputs/proposals; no native BF16 SVD is claimed.'}


def zero_dot_and_optimizations(check):
    fp=get_fp();records=[];changed=[]
    for fmt,p in (('BF16',8),('FP32',24)):
        a=1<<p;row=(a,1,-a,-1);h=(1,1,1,1)
        result=dot(row,h,fmt)
        check(result.exact_dot==0 and result.decoded_output==-1,'Ordered zero-dot counterexample')
        if fmt=='FP32':check(result.audit['native_oracle_checks']==8,'Eight actual scalar FP32 operations')
        records.append({'id':'C4_zero_exact_dot_ordered_nonzero','format':fmt,'row':row,'h':h,
            'execution':result.record(),'status':'passed',
            'contract':'Zero bias; products and accumulations in listed index order; no FMA; canonical zeros'})
        # Alternate tree: pair terms 0+2 and 1+3, then add the pairs.
        audit=fp.Audit();prod=[fp.mul_words(fp.round_fraction(x,fmt),fp.round_fraction(1,fmt),fmt,audit) for x in row]
        left=fp.add_words(prod[0],prod[2],fmt,audit);right=fp.add_words(prod[1],prod[3],fmt,audit)
        alternate=fp.add_words(left,right,fmt,audit)
        check(fp.decode_word(alternate,fmt)==0,'Different reduction tree produces different value')
        k=5 if fmt=='BF16' else 13
        x=1+Fraction(1,2**k);y=1-Fraction(1,2**k);c=Fraction(-1)
        sep=fp.add_words(fp.mul_words(fp.round_fraction(x,fmt),fp.round_fraction(y,fmt),fmt),fp.round_fraction(c,fmt),fmt)
        fused=fp.round_fraction(x*y+c,fmt)
        check(fp.decode_word(sep,fmt)==0 and fp.decode_word(fused,fmt)==-Fraction(1,2**(2*k)), 'One-round FMA differs from separate operations')
        check.rejects(lambda:dot(row,h,fmt,policy='pairwise'),'Uncertified reduction must be rejected')
        check.rejects(lambda:dot(row,h,fmt,policy='fma'),'Uncertified FMA policy must be rejected')
        changed.append({'id':'C8_changed_reduction_or_fma','format':fmt,'left_to_right_result':qstr(result.decoded_output),
            'alternate_tree_result':qstr(fp.decode_word(alternate,fmt)),
            'alternate_tree':'(product[0]+product[2])+(product[1]+product[3])',
            'fma_inputs':[qstr(x),qstr(y),qstr(c)],'separate_result':qstr(fp.decode_word(sep,fmt)),
            'fused_one_round_reference_result':qstr(fp.decode_word(fused,fmt)),
            'fma_execution_scope':'Exact rational single-RNE software reference, not native FMA certification',
            'unsupported_policy_refusals':2,'status':'passed'})
    return {'zero_dot_cases':records,'optimization_cases':changed}


def commit_counterexamples(check):
    records=[];capacity=[]
    fp=get_fp()
    for fmt,p in (('BF16',8),('FP32',24)):
        h=_column((1,1));cert=projection(h)
        g=matrix(((1,-1),(0,0)));ideal=matmul(g,cert.P_perp)
        w=matrix(((1<<p,0),(0,0)))
        commit=commit_weights(w,ideal,fmt)
        check(matmul(ideal,h)==zeros(2,1),'Ideal update lies in nullspace')
        residual=matmul(commit['effective'],h)
        check(residual.rows==((Fraction(-1),),(Fraction(0),)),'Effective update breaks nullspace after quantization')
        bound=perturbation_certificate(w,g,cert.P_perp,cert.P_perp,ideal,h,fmt)
        check(bound['exact_observed_output_difference']['rows'][0][0]=='-1','Actual ordered output changed')
        records.append({'id':'C6_commit_quantization_breaks_null','format':fmt,'H':serialize(h),
            'ideal_update':serialize(ideal),'actual_effective_residual':serialize(residual),
            'certificate':bound,'status':'passed'})
        # A difference of stored weights can have more significant bits than a single stored word.
        a=(1<<p)-1
        H=matrix(((1,0),(a,1),(0,a)))
        nullrow=matrix(((a*a,-a,1),))
        W=matrix(((-1,0,0),));Wp=matrix(((a*a-1,-a,1),))
        check(matmul(nullrow,H)==zeros(1,2),'Primitive annihilator example')
        check(sub(Wp,W)==nullrow,'Stored-weight difference equals unrepresentable ideal row')
        check(quantize_matrix(nullrow,fmt)[0]!=nullrow,'Primitive row is not standalone representable')
        check(quantize_matrix(W,fmt)[0]==W and quantize_matrix(Wp,fmt)[0]==Wp,'Both endpoint weight rows exactly stored')
        capacity.append({'format':fmt,'H':serialize(H),'a':a,'primitive_null_row':serialize(nullrow),
            'W':serialize(W),'W_prime':serialize(Wp),'standalone_null_row_representable':False,
            'endpoint_rows_representable':True,'algebraic_effective_residual':serialize(matmul(sub(Wp,W),H)),
            'scope':'Finite-word endpoint/difference example. Universal absence of a standalone nonzero row requires the separate odd-significand proof; no FP execution invariance asserted.'})
        # Optional native-probe eligibility must not change ideal single-round commit domain.
        maxv=fp.decode_word(fp.get_format(fmt).max_finite_word,fmt)
        huge=commit_weights(matrix(((-maxv,),)),matrix(((2*maxv,),)),fmt)
        check(huge['new']==matrix(((maxv,),)) and not huge['candidate_exactly_storable'],
              'Ideal delta may overflow alone while W+delta rounds finitely')
        capacity[-1]['nonstorable_delta_but_finite_final_sum_checked']=True
    return {'commit_cases':records,'stored_difference_capacity':capacity}


def perturbation_bounds(check):
    rng=random.Random(SEED);records=[];detailed=[]
    for fmt in ('BF16','FP32'):
        for case in range(20):
            h=_column((1,1,2));cert=projection(h);q,_=quantize_matrix(cert.P_perp,fmt)
            g=matrix(tuple(tuple(Fraction(rng.randrange(-4,5),2**rng.randrange(0,3)) for j in range(3)) for i in range(3)))
            w=matrix(tuple(tuple(Fraction(rng.randrange(-8,9),4) for j in range(3)) for i in range(3)))
            candidate,ops=executed_matmul(g,q,fmt)
            proof=perturbation_certificate(w,g,cert.P_perp,q,candidate,h,fmt)
            check(proof['exact_error_decomposition_holds'],'T3 exact decomposition')
            check(proof['bound_verified_by_rational_squared_comparison'],'T3 rational norm bound')
            check(Fraction(proof['actual_output_2norm_squared'])<=Fraction(proof['output_2norm_upper'])**2,'Independent final squared comparison')
            records.append({'format':fmt,'case':case,'candidate_product_error_F_squared':qstr(frobenius_squared(sub(candidate,matmul(g,q)))),
                'actual_output_2norm_squared':proof['actual_output_2norm_squared'],'output_2norm_upper':proof['output_2norm_upper'],
                'components':proof['norm_upper_components'],'status':'passed'})
            if case==0:detailed.append(proof)
    check(any(Fraction(x['candidate_product_error_F_squared'])!=0 for x in records),'Actual candidate-product rounding error observed')
    return {'seed':SEED,'cases':records,'sample_count':len(records),'passed':len(records),'unexpected_failures':0,
            'detailed_certificates':detailed,'scope':'40 fixed-seed stored-input pointwise certificates; not a global worst-case or bitwise theorem'}


def subnormal_and_rejections(check):
    fp=get_fp();records=[]
    for fmt in ('BF16','FP32'):
        fmtobj=fp.get_format(fmt);eta=fp.decode_word(1,fmt)
        # Exactly half the smallest positive subnormal rounds to canonical +0.
        result=dot((eta,),(Fraction(1,2),),fmt)
        check(result.decoded_output==0 and result.signed_error==-eta/2,'Subnormal half-way tie to zero')
        check(result.local_absolute_error_bound==eta/2 and not result.relative_model_holds,'Relative-only model must not cover this underflow')
        check(result.gamma_bound is None,'Gamma bound refused when relative model fails')
        negativezero=fmtobj.sign_mask
        zero=dot_words((negativezero,),(fp.round_fraction(1,fmt),),fmt)
        check(zero.output_word==0,'Declared arithmetic zero normalization')
        for raw in ((fmtobj.exponent_mask<<fmtobj.fraction_bits),
                    (fmtobj.exponent_mask<<fmtobj.fraction_bits)|1):
            check.rejects(lambda raw=raw:dot_words((raw,),(0,),fmt),'Nonfinite operand must be rejected')
        maxv=fp.decode_word(fmtobj.max_finite_word,fmt)
        check.rejects(lambda:dot((maxv,),(2,),fmt),'Overflow operation must be rejected')
        check.rejects(lambda:dot((Fraction(1,3),),(1,),fmt),'Nonstored operand must not be silently quantized')
        records.append({'format':fmt,'min_subnormal':qstr(eta),'underflow_case':result.record(),
            'negative_zero_input_normalized_word':hex(zero.output_word),'scope':'Explicit gradual-underflow and canonical-zero policy; native FP32 audited against rational RNE'})
    check.rejects(lambda:svd_projection(eye(2),'float16'),'Unsupported SVD precision refused')
    check.rejects(lambda:svd_projection(eye(2),'float64',rtol=-1),'Negative cutoff refused')
    check.rejects(lambda:svd_projection(matrix(((4,0),(0,4))),'float64',rtol=1e308),
                  'Overflowing computed cutoff refused rather than recording Infinity')
    return records


def run_checks():
    started=time.perf_counter();check=Checks();sections={};times={}
    jobs=[('quantized_projectors',quantized_projectors),('svd',svd_cases),
          ('zero_dot_and_optimizations',zero_dot_and_optimizations),('commit_and_capacity',commit_counterexamples),
          ('perturbation_bounds',perturbation_bounds),('subnormal_and_rejections',subnormal_and_rejections)]
    for name,fn in jobs:
        before=time.perf_counter();sections[name]=fn(check);times[name]=time.perf_counter()-before
    return {'status':'passed','checks':check.total,'expected_rejections':check.expected_rejections,
        'unexpected_failures':0,'seed':SEED,'runtime_seconds':time.perf_counter()-started,
        'section_seconds':times,'sections':sections,
        'environment':{'numpy':np.__version__,'float32_svd_dispatch':'numpy.linalg._umath_linalg.svd_f signature f->fff',
            'public_numpy_float32_svd_uses_double_in_this_version':True},
        'evidence_scope':{'exact_algebra':'decoded rational diagnostics only; universal proofs separate',
            'BF16':'software RNE; no native BF16 SVD or hardware arithmetic',
            'FP32':'single-real SVD dispatch and separately audited native scalar operations; no full library/hardware certification',
            'FMA':'software one-round comparison only; production contract rejects FMA',
            'global_bitwise_safety':False,'SMT_queries':0}}

if __name__=='__main__':
    import json
    from pathlib import Path
    if not __debug__:raise SystemExit('Verification requires ordinary Python, not optimization')
    result=run_checks();path=Path(__file__).with_name('numerical_verification_results.json')
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'checks':result['checks'],'expected_rejections':result['expected_rejections'],
                      'seconds':result['runtime_seconds'],'output':str(path)}))
