"""A3 adversarial examples using read-only arithmetic primitives, not old suites.

Each numerical record distinguishes exact endpoint algebra, pointwise local
rounding error, and a new A3 complete-domain certificate decision. This module
does not import any previous stage's verifier or infer span-wide floating
equality from basis probes.
"""
from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114


def run_checks() -> dict:
    from a3_runtime import get_fp, load_a2
    from certificate_kernel import (CertificateRejected, CertificateKernel,
                                    initial_weights, make_certificate)

    exact = load_a2('exact_projection')
    numeric = load_a2('numerical_projection')
    fp = get_fp()
    started = time.perf_counter()
    checks = 0
    rejections = []
    records = []
    extra_boundaries = []

    def check(value, label):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError(label)

    def refused(label, function, exception=CertificateRejected):
        try:
            function()
        except exception as error:
            check(True, label)
            item = {'case': label, 'exception': type(error).__name__,
                    'reason': str(error)}
            rejections.append(item)
            return item
        raise AssertionError('Expected refusal was absent: ' + label)

    def pointwise(old_row, new_row, activation, fmt):
        old = numeric.dot(tuple(old_row), tuple(activation), fmt)
        new = numeric.dot(tuple(new_row), tuple(activation), fmt)
        effective_linear = sum(((b-a)*x for a,b,x in
                                zip(old_row,new_row,activation)), Fraction(0))
        observed = new.decoded_output-old.decoded_output
        check(observed == effective_linear+new.signed_error-old.signed_error,
              'Pointwise exact endpoint/execution decomposition')
        bound = (abs(effective_linear)+old.local_absolute_error_bound+
                 new.local_absolute_error_bound)
        check(abs(observed) <= bound, 'Exact rational local absolute bound')
        return {'old': old.record(), 'new': new.record(),
                'effective_linear_change': str(effective_linear),
                'observed_numeric_change': str(observed),
                'absolute_change_upper_bound': str(bound),
                'scope': 'This stored input only; no global/bitwise authorization'}

    for fmt, p, fused_k in (('BF16',8,5),('FP32',24,13)):
        word = lambda x: fp.round_fraction(Fraction(x), fmt)
        value = lambda x: fp.decode_word(x, fmt)
        one, zero = word(1), word(0)

        # C1: ideal annihilation survives neither endpoint quantization nor
        # the actual complete-domain acceptance check.
        old = exact.matrix(((2**p,0),(0,0)))
        ideal = exact.matrix(((1,-1),(0,0)))
        h = exact.matrix(((1,),(1,)))
        commit = numeric.commit_weights(old,ideal,fmt)
        check(exact.matmul(ideal,h) == exact.zeros(2,1), 'Ideal patch is null')
        residual = exact.matmul(commit['effective'],h)
        check(residual == exact.matrix(((-1,),(0,))), 'Actual committed patch leaks')
        old_words = numeric.stored_words(old,fmt)
        check(initial_weights('commit_rounding_v1',fmt)==old_words,
              'C1 matches trusted complete-domain registry')
        rejection = refused(fmt+'_commit_rounding', lambda: make_certificate(
            'commit_rounding_v1',fmt,old_words,commit['new_words'],version=0))
        executions = [pointwise(a,b,(Fraction(1),Fraction(1)),fmt)
                      for a,b in zip(old.rows,commit['new'].rows)]
        check(executions[0]['observed_numeric_change']=='-1','C1 actual output change')
        records.append({'id':'A3-C1_commit_endpoint_difference','format':fmt,
                        'old_weights':exact.serialize(old),'ideal_delta':exact.serialize(ideal),
                        'stored_new_weights':exact.serialize(commit['new']),
                        'effective_delta':exact.serialize(commit['effective']),
                        'protected_activation':exact.serialize(h),
                        'exact_effective_residual':exact.serialize(residual),
                        'executions':executions,'certificate_refusal':rejection,
                        'native_commit_additions_checked':commit['native_FP32_additions_checked']})

        # C2: one finite generating basis probe is not equivalent to all
        # legal floating activations, even when exact algebra is null there.
        basis = exact.matrix(((1,),(1,),(1,)))
        projector = exact.projection(basis).P_perp
        rounded, rounded_words = numeric.quantize_matrix(projector,fmt)
        old = exact.zeros(3,3)
        old_words = numeric.stored_words(old,fmt)
        eta = value(1)
        small = exact.matrix(((eta,),(eta,),(eta,)))
        check(exact.matmul(rounded,basis)==exact.zeros(3,1),'C2 basis algebra zero')
        check(exact.matmul(rounded,small)==exact.zeros(3,1),'C2 small algebra zero')
        basis_exec=[pointwise(a,b,(Fraction(1),)*3,fmt)
                    for a,b in zip(old.rows,rounded.rows)]
        tiny_exec=[pointwise(a,b,(eta,)*3,fmt) for a,b in zip(old.rows,rounded.rows)]
        check(all(x['new']['output_word_hex']=='0x0' for x in basis_exec),
              'C2 generating basis FP result is canonical zero')
        check(all(x['new']['output_word_hex']=='0x1' for x in tiny_exec),
              'C2 other legal input FP result is nonzero')
        check(all(x['new']['gamma_bound'] is None for x in tiny_exec),
              'C2 unsupported relative-only bound absent')
        check(initial_weights('thirds_two_inputs_v1',fmt)==old_words,
              'C2 registry endpoint matches')
        rejection=refused(fmt+'_basis_only_probe',lambda:make_certificate(
            'thirds_two_inputs_v1',fmt,old_words,rounded_words,version=0))
        records.append({'id':'A3-C2_basis_zero_but_legal_subnormal_nonzero','format':fmt,
                        'legal_domain':[[str(x)]*3 for x in (Fraction(1),eta)],
                        'global_span_rank':1,'old_weights':exact.serialize(old),
                        'new_weights':exact.serialize(rounded),
                        'exact_null_on_entire_declared_span':True,
                        'basis_execution':basis_exec,'tiny_execution':tiny_exec,
                        'certificate_refusal':rejection,
                        'domain_note':'Exactly two legal stored inputs; no assumed real-linear closure'})

        # C3: the first site alone suggests safety, but all shared sites do not.
        old=exact.eye(2); new=exact.matrix(((1,0),(0,2)))
        h1=(Fraction(1),Fraction(0));h2=(Fraction(0),Fraction(1))
        local=[pointwise(a,b,h1,fmt) for a,b in zip(old.rows,new.rows)]
        other=[pointwise(a,b,h2,fmt) for a,b in zip(old.rows,new.rows)]
        check(all(x['observed_numeric_change']=='0' for x in local),'C3 first site same')
        check(other[1]['observed_numeric_change']=='1','C3 omitted site changes')
        old_words=numeric.stored_words(old,fmt);new_words=numeric.stored_words(new,fmt)
        check(initial_weights('shared_axis_v1',fmt)==old_words,'C3 registry endpoint matches')
        rejection=refused(fmt+'_missing_shared_site',lambda:make_certificate(
            'shared_axis_v1',fmt,old_words,new_words,version=0))
        records.append({'id':'A3-C3_shared_call_site_omission','format':fmt,
                        'old_weights':exact.serialize(old),'new_weights':exact.serialize(new),
                        'site_1_activation':['1','0'],'site_2_activation':['0','1'],
                        'local_rank':1,'merged_rank':2,'first_site':local,'second_site':other,
                        'certificate_refusal':rejection})

        # C4: an allowed future state, not just the initial state, belongs in
        # the domain. This illustrative recurrence deliberately fails closure
        # after an uncertified patch; it is not an accepted kernel execution.
        old_q=new_q=zero
        trace=[]
        audit=fp.Audit()
        for tick in range(2):
            old_y=numeric.dot((Fraction(1),Fraction(0)),(value(old_q),Fraction(0)),fmt)
            new_y=numeric.dot((Fraction(2),Fraction(0)),(value(new_q),Fraction(0)),fmt)
            next_old=fp.add_words(one,word(-old_y.decoded_output),fmt,audit)
            next_new=fp.add_words(one,word(-new_y.decoded_output),fmt,audit)
            trace.append({'tick':tick,'old_q_word':hex(old_q),'patched_q_word':hex(new_q),
                          'old_output':str(old_y.decoded_output),'patched_output':str(new_y.decoded_output),
                          'old_next_word':hex(next_old),'patched_next_word':hex(next_new)})
            old_q,new_q=next_old,next_new
        check(trace[0]['old_output']==trace[0]['patched_output']=='0','C4 initial sample passes')
        check(value(old_q)==0 and value(new_q)==-1,'C4 next reachable call breaks state invariant')
        canonical_old=initial_weights('duplicate_feedback_v1',fmt)
        bad_words=numeric.stored_words(exact.matrix(((2,0),(0,1))),fmt)
        rejection=refused(fmt+'_reachable_boolean_domain_omission',lambda:make_certificate(
            'duplicate_feedback_v1',fmt,canonical_old,bad_words,version=0))
        records.append({'id':'A3-C4_reachable_state_omission','format':fmt,
                        'illustrative_transition':'q_next=1-row_weight*(q,0)',
                        'initial_state':'0','reference_invariant':['0','1'],
                        'old_row':['1','0'],'patched_row':['2','0'],'trace':trace,
                        'extra_transition_arithmetic_audit':asdict(audit),
                        'separate_registered_model_refusal':rejection,
                        'scope':'Trace is a separate scalar recurrence; registry refusal checks the same unsafe first-row edit over its complete Boolean domain'})

        # C5: a protected linear map can be unchanged while an unmodeled
        # A-to-D channel changes the argument supplied to it.
        audit=fp.Audit()
        old_a=numeric.dot((Fraction(1),),(Fraction(1),),fmt)
        new_a=numeric.dot((Fraction(2),),(Fraction(1),),fmt)
        old_h=fp.add_words(old_a.output_word,word(-1),fmt,audit)
        new_h=fp.add_words(new_a.output_word,word(-1),fmt,audit)
        old_d=numeric.dot((Fraction(1),),(value(old_h),),fmt)
        new_d=numeric.dot((Fraction(1),),(value(new_h),),fmt)
        check(old_h==zero and new_h==one,'C5 changed legal D inputs')
        check(old_d.decoded_output==0 and new_d.decoded_output==1,'C5 D state/output changed')
        records.append({'id':'A3-C5_unmodeled_A_to_D_input_feedback','format':fmt,
                        'D_old_weight':'1','D_new_weight':'1','D_effective_delta':'0',
                        'A_theta_before_after':['1','2'],'D_input_rule':'h=A_output-1',
                        'old_input_word':hex(old_h),'new_input_word':hex(new_h),
                        'D_output_before_after':['0','1'],'input_preparation_audit':asdict(audit),
                        'failed_premise':'Same protected input at corresponding calls / no unmodeled A-to-D influence',
                        'scope':'Not an accepted update of the closed registered graph'})

        # C6: if biases are mutable, checking Delta_W alone is insufficient.
        old_product=numeric.dot((Fraction(1),),(Fraction(1),),fmt)
        audit=fp.Audit()
        old_output=fp.add_words(zero,old_product.output_word,fmt,audit)
        new_output=fp.add_words(one,old_product.output_word,fmt,audit)
        check(value(new_output)-value(old_output)==1,'C6 omitted bias changes linear-affine output')
        augmented_delta=exact.matrix(((0,1),))
        augmented_h=exact.matrix(((1,),(1,)))
        check(exact.matmul(augmented_delta,augmented_h)==exact.matrix(((1,),)),
              'C6 augmented exact check detects bias')
        records.append({'id':'A3-C6_bias_omission','format':fmt,'delta_W':'0','delta_bias':'1',
                        'activation':'1','old_output_word':hex(old_output),
                        'new_output_word':hex(new_output),'augmented_residual':'1',
                        'bias_addition_audit':asdict(audit),
                        'scope':'Arithmetic witness; delivered protected registry has fixed bias and rejects changed model descriptors'})

        # C7: order is part of the program. Both policies are evaluated,
        # while only the ordered policy is accepted by the imported executor.
        row=tuple(map(Fraction,(2**p,1,-2**p,-1)))
        ordered=numeric.dot(row,(Fraction(1),)*4,fmt)
        words=tuple(word(x) for x in row);audit=fp.Audit()
        left=fp.add_words(words[0],words[2],fmt,audit)
        right=fp.add_words(words[1],words[3],fmt,audit)
        tree=fp.add_words(left,right,fmt,audit)
        check(ordered.exact_dot==0 and ordered.decoded_output==-1,'C7 ordered exact-zero dot leaks')
        check(value(tree)==0,'C7 alternate reduction result differs')
        refusal=refused(fmt+'_changed_reduction_policy',lambda:numeric.dot(
            row,(Fraction(1),)*4,fmt,policy='pairwise'),numeric.NumericalRejected)
        records.append({'id':'A3-C7_changed_reduction','format':fmt,'row':[str(x) for x in row],
                        'activation':['1']*4,'ordered':ordered.record(),
                        'alternate_tree':'(p0+p2)+(p1+p3)','alternate_word':hex(tree),
                        'alternate_audit':asdict(audit),'arithmetic_policy_refusal':refusal})

        # C8: single-round fused reference is deliberately not called native FMA.
        x=1+Fraction(1,2**fused_k);y=1-Fraction(1,2**fused_k)
        separate=numeric.dot((x,Fraction(-1)),(y,Fraction(1)),fmt)
        fused=word(x*y-1)
        check(separate.decoded_output==0,'C8 separate product/add zero')
        check(value(fused)==-Fraction(1,2**(2*fused_k)),'C8 fused reference differs')
        refusal=refused(fmt+'_changed_fma_policy',lambda:numeric.dot(
            (x,Fraction(-1)),(y,Fraction(1)),fmt,policy='fma'),numeric.NumericalRejected)
        records.append({'id':'A3-C8_fusion_policy_change','format':fmt,
                        'x':str(x),'y':str(y),'c':'-1','separate':separate.record(),
                        'fused_reference_word':hex(fused),'fused_reference_value':str(value(fused)),
                        'fused_scope':'Exact rational expression rounded once in software; no native FMA execution',
                        'arithmetic_policy_refusal':refusal})

        # Extra converse boundary: full exact rank does not rule out all
        # observationally equivalent finite-domain endpoint changes. This
        # single fixture is not a classification of A4 rank/capacity.
        old=exact.eye(2);new=exact.matrix(((1,eta),(0,1)))
        h_full=exact.matrix(((1,1),(0,1)))
        residual=exact.matmul(exact.sub(new,old),h_full)
        check(exact.rank(h_full)==2,'Extra boundary protected span full rank')
        check(residual!=exact.zeros(2,2),'Extra boundary exact linear condition fails')
        reference=CertificateKernel(fmt,'split_feedback_v1',initial_bit=0)
        patched=CertificateKernel(fmt,'split_feedback_v1',initial_bit=0)
        candidate_words=numeric.stored_words(new,fmt)
        before_a=reference.a_output((zero,one))
        certificate=patched.prepare(candidate_words)
        checked=json.loads(certificate)
        check(checked['payload']['proof']['exact_effective_delta_annihilates_registered_span'] is False,
              'Extra boundary certificate records algebraic failure explicitly')
        patched.commit(certificate)
        after_a=patched.a_output((zero,one))
        check(before_a==(zero,one) and after_a==(1,one),
              'Extra boundary legal A response changes by eta')
        trace=[]
        for u in (0,1,0,1,1,0):
            ref=reference.d_tick(word(u));new_obs=patched.d_tick(word(u))
            check(ref==new_obs,'Extra boundary actual protected feedback outputs remain equal')
            trace.append({'input':u,'reference_observation':ref,'patched_observation':new_obs})
        extra_boundaries.append({'id':'A3-X1_full_rank_bitwise_equivalence_not_algebraic_null',
                                 'format':fmt,'old_weights':exact.serialize(old),
                                 'new_weights':exact.serialize(new),'global_generators':exact.serialize(h_full),
                                 'exact_rank':2,'exact_effective_residual':exact.serialize(residual),
                                 'accepted_certificate_sha256':hashlib.sha256(certificate.encode()).hexdigest(),
                                 'certificate_payload_sha256':checked['payload_sha256'],
                                 'complete_certificate_call_cases':checked['payload']['proof']['call_case_count'],
                                 'complete_certificate_transition_cases':checked['payload']['proof']['transition_case_count'],
                                 'certificate_records_algebraic_annihilation':False,
                                 'A_input':['0','1'],'A_before_words':[hex(x) for x in before_a],
                                 'A_after_words':[hex(x) for x in after_a],
                                 'protected_trace':trace,
                                 'scope':'Complete registered finite-domain bitwise acceptance; not exact real-linear equality or A4 capacity classification'})

    return {'schema':'dmwk-p2-a3-counterexamples-v1','status':'passed','checks':checks,
            'check_unit':'Explicit A3 counterexample assertions; imported arithmetic internal checks are not added',
            'seed':SEED,'random_sampling':False,'deterministic_format_cases':len(records),
            'counterexample_classes':8,'expected_refusals':len(rejections),
            'unexpected_failures':0,'records':records,'refusals':rejections,
            'extra_boundaries':extra_boundaries,
            'runtime_seconds':time.perf_counter()-started,
            'backend':fp.backend_metadata(),
            'scope':'New A3 adversarial acceptance/refusal and pointwise arithmetic cases; no old verification suite rerun',
            'SMT_queries':0,'proof_assistant_checked':False}


if __name__ == '__main__':
    if not __debug__:
        raise SystemExit('Run this verifier without -O/-OO')
    result=run_checks()
    result['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (ROOT/'verify_counterexample_cases.py',
                                       ROOT/'certificate_kernel.py',ROOT/'a3_runtime.py')}
    target=ROOT/'counterexample_results.json'
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'checks':result['checks'],
                     'format_cases':result['deterministic_format_cases'],
                     'expected_refusals':result['expected_refusals'],'output':str(target)}))
