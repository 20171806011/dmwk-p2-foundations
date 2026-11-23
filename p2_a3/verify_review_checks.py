"""Independent finite A3 review oracles.

No production verifier or its assertions is imported. Rank uses minors;
rounding searches the ordered finite IEEE words; state evolution uses an
independent Boolean recurrence. These are finite checks, not machine proofs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
from itertools import combinations, product
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def determinant(rows):
    size = len(rows)
    if size == 0:
        return Fraction(1)
    if size == 1:
        return rows[0][0]
    return sum(((-1)**j * rows[0][j] * determinant(tuple(
        tuple(row[c] for c in range(size) if c != j)
        for row in rows[1:])) for j in range(size)), Fraction(0))


def rank_by_minors(rows, width):
    for size in range(min(len(rows), width), 0, -1):
        for ri in combinations(range(len(rows)), size):
            for ci in combinations(range(width), size):
                if determinant(tuple(tuple(rows[r][c] for c in ci) for r in ri)):
                    return size
    return 0


def independent_basis(columns, dimension):
    basis = []
    for col in columns:
        trial = basis + [col]
        rows = tuple(tuple(c[i] for c in trial) for i in range(dimension))
        if rank_by_minors(rows, len(trial)) > len(basis):
            basis.append(col)
    return tuple(basis)


def matvec(rows, vector):
    return tuple(sum((w*x for w, x in zip(row, vector)), Fraction(0))
                 for row in rows)


def dyadic(integer, exponent):
    return Fraction(integer * 2**exponent) if exponent >= 0 else Fraction(integer, 2**(-exponent))


def format_parameters(fmt):
    if fmt == 'BF16':
        return 7, 16
    if fmt == 'FP32':
        return 23, 32
    raise ValueError('Independent oracle only supports BF16 and FP32')


def decode_reference(word, fmt):
    fraction_bits, width = format_parameters(fmt)
    require(type(word) is int and 0 <= word < 2**width, 'Bad oracle word')
    sign = -1 if word >> (width - 1) else 1
    magnitude = word & (2**(width-1)-1)
    exponent = magnitude >> fraction_bits
    require(exponent != 255, 'Nonfinite oracle word')
    fraction = magnitude & (2**fraction_bits-1)
    if exponent == 0:
        return sign * dyadic(fraction, 1-127-fraction_bits)
    return sign * dyadic(2**fraction_bits+fraction, exponent-127-fraction_bits)


def round_reference(value, fmt):
    """Nearest-even using independent monotone-word search, canonical zero."""
    value = Fraction(value)
    if not value:
        return 0
    fraction_bits, width = format_parameters(fmt)
    negative = value < 0
    x = abs(value)
    largest = (254 << fraction_bits) | (2**fraction_bits-1)
    maximum = decode_reference(largest, fmt)
    overflow_boundary = maximum + dyadic(1, 127-fraction_bits-1)
    if x >= overflow_boundary:
        raise ValueError('Independent RNE result would be nonfinite')
    low, high = 0, largest
    while low < high:
        middle = (low+high+1)//2
        if decode_reference(middle, fmt) <= x:
            low = middle
        else:
            high = middle-1
    if low == largest or decode_reference(low, fmt) == x:
        result = low
    else:
        lower, upper = decode_reference(low, fmt), decode_reference(low+1, fmt)
        dl, du = x-lower, upper-x
        result = low if dl < du or (dl == du and low % 2 == 0) else low+1
    return result | (int(negative) << (width-1)) if result else 0


def independent_dot(row_words, input_words, fmt, bias_word=0):
    acc = bias_word
    trace = []
    for w, x in zip(row_words, input_words):
        p = round_reference(decode_reference(w, fmt)*decode_reference(x, fmt), fmt)
        acc = round_reference(decode_reference(acc, fmt)+decode_reference(p, fmt), fmt)
        trace.append(acc)
    return acc, tuple(trace)


def independent_dense(words, vector, fmt):
    return tuple(independent_dot(row, vector, fmt)[0] for row in words)


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def algebra_checks():
    import linear_contracts as lc
    checked = 0
    rank_histogram = {}
    for entries in product((0, 1), repeat=4):
        rows = tuple(tuple(Fraction(x) for x in entries[2*i:2*i+2]) for i in range(2))
        columns = tuple(tuple(rows[i][j] for i in range(2)) for j in range(2))
        basis = independent_basis(columns, 2)
        rank_histogram[str(len(basis))] = rank_histogram.get(str(len(basis)), 0)+1
        h = lc.matrix(rows)
        for delta_values in product((-1, 0, 1), repeat=4):
            delta = tuple(tuple(Fraction(x) for x in delta_values[2*i:2*i+2]) for i in range(2))
            expected = all(all(x == 0 for x in matvec(delta, c)) for c in columns)
            from_basis = all(all(x == 0 for x in matvec(delta, c)) for c in basis)
            require(expected == from_basis, 'Independent linear basis logic disagrees')
            result = lc.exact_linear_report(lc.matrix(((0,0),(0,0))), lc.matrix(delta), h)
            require(result['annihilates_supplied_span'] is expected, 'Production exact annihilation mismatch')
            require(result['protected_rank'] == len(basis), 'Production exact rank mismatch')
            require(result['algebraic_update_space_dimension'] == 2*(2-len(basis)), 'Algebraic dimension mismatch')
            require(result['authorizes_bitwise_commit'] is False and result['global_domain_provenance_verified'] is False,
                    'Arithmetic report became an authorization or provenance assertion')
            checked += 1
    rectangular = 0
    for entries in product((0, 1), repeat=6):
        rows = tuple(tuple(Fraction(x) for x in entries[3*i:3*i+3]) for i in range(2))
        columns = tuple(tuple(rows[i][j] for i in range(2)) for j in range(3))
        independent_rank = len(independent_basis(columns, 2))
        for d in product((-1,0,1), repeat=2):
            result = lc.exact_linear_report(lc.matrix(((0,0),)),lc.matrix((d,)),lc.matrix(rows))
            expected = all(matvec((d,), c) == (0,) for c in columns)
            require(result['annihilates_supplied_span'] is expected, 'Rectangular result mismatch')
            require(result['protected_rank'] == independent_rank, 'Rectangular rank mismatch')
            rectangular += 1
    affine = 0
    for mask in range(8):
        activation = tuple(Fraction(x) for x in range(3) if mask & (1<<x))
        lifted = tuple((x,Fraction(1)) for x in activation)
        for delta_weight, delta_bias in product((-1,0,1), repeat=2):
            r = lc.exact_affine_report(lc.matrix(((0,),)),lc.matrix(((delta_weight,),)),
                                      (Fraction(0),),(Fraction(delta_bias),),lc.matrix((activation,),ncols=len(activation)))
            direct = all(delta_weight*x+delta_bias == 0 for x in activation)
            require(r['annihilates_supplied_span'] is direct, 'Affine activation equality mismatch')
            require(r['protected_rank'] == len(independent_basis(lifted,2)), 'Affine lifted-rank mismatch')
            affine += 1
    full_affine = lc.exact_affine_report(lc.matrix(((0,),)),lc.matrix(((1,),)),(0,),(-1,),lc.matrix(((1,2),)))
    compressed = lc.exact_affine_report(lc.matrix(((0,),)),lc.matrix(((1,),)),(0,),(-1,),lc.matrix(((1,),)))
    require(not full_affine['annihilates_supplied_span'] and compressed['annihilates_supplied_span'],
            'Affine basis-before-augmentation counterexample missing')
    true = lc.exact_linear_report(lc.matrix(((0,0),)),lc.matrix(((0,1),)),lc.matrix(((1,),(0,))))
    upper = lc.exact_linear_report(lc.matrix(((0,0),)),lc.matrix(((0,1),)),lc.matrix(((1,0),(0,1))))
    require(true['annihilates_supplied_span'] and not upper['annihilates_supplied_span'],
            'Conservative superspace sufficiency mistaken for necessity')
    return {'exhaustive_binary_2x2_H_ternary_2x2_delta_pairs':checked,
            'H_rank_histogram':rank_histogram,
            'exhaustive_binary_2x3_H_ternary_1x2_delta_pairs':rectangular,
            'affine_all_subsets_0_1_2_and_ternary_changes':affine,
            'affine_basis_before_augmentation_counterexample':True,
            'conservative_superspace_not_necessary_counterexample':True,
            'scope':'Independent determinant/minor basis and direct rational outputs; finite instances only'}


def rounding_and_bound_checks():
    from a3_runtime import get_fp
    from bounded_contracts import pointwise_report
    fp = get_fp()
    records = []
    for fmt in ('BF16','FP32'):
        fraction_bits, width = format_parameters(fmt)
        p = fraction_bits+1
        eta = decode_reference(1, fmt)
        maximum_word = (254<<fraction_bits) | (2**fraction_bits-1)
        maximum = decode_reference(maximum_word,fmt)
        values = (Fraction(0), Fraction(1), Fraction(-1), Fraction(1,3), Fraction(2,3),
                  eta, -eta, eta/2, -eta/2, 3*eta/2, -3*eta/2,
                  decode_reference((1<<fraction_bits)-1,fmt),
                  decode_reference(1<<fraction_bits,fmt),
                  Fraction(2**p+1),Fraction(2**p-1), maximum,-maximum)
        for x in values:
            require(round_reference(x,fmt)==fp.round_fraction(x,fmt),'Independent RNE mismatch')
        overflow_values = (maximum+dyadic(1,127-fraction_bits-1), -2*maximum)
        for x in overflow_values:
            try:round_reference(x,fmt)
            except ValueError:pass
            else:raise AssertionError('Independent overflow unexpectedly accepted')
            try:fp.round_fraction(x,fmt)
            except fp.ExecutionError:pass
            else:raise AssertionError('Production overflow unexpectedly accepted')
        one = round_reference(1,fmt)
        a = 2**p
        fixtures = [
            ('affine_bias_first', ((a,1),), ((a,-1),), (1,1),(-a,),(-a,)),
            ('commit_effective_delta', ((a,0),), ((a,-1),), (1,1),(0,),(0,)),
            ('subnormal_thirds', ((0,0,0),), ((Fraction(2,3),Fraction(-1,3),Fraction(-1,3)),),
             (eta,eta,eta),(0,),(0,)),
        ]
        bounds = []
        for name,old,new,h,b,bp in fixtures:
            old_w = tuple(tuple(round_reference(x,fmt) for x in row) for row in old)
            new_w = tuple(tuple(round_reference(x,fmt) for x in row) for row in new)
            h_w = tuple(round_reference(x,fmt) for x in h)
            b_w = tuple(round_reference(x,fmt) for x in b)
            bp_w = tuple(round_reference(x,fmt) for x in bp)
            result = pointwise_report(old_w,new_w,h_w,fmt,old_bias_words=b_w,new_bias_words=bp_w)
            require(result['authorizes_commit'] is False, 'Pointwise bound authorized a commit')
            for i,row in enumerate(result['rows']):
                yo = independent_dot(old_w[i],h_w,fmt,b_w[i])[0]
                yn = independent_dot(new_w[i],h_w,fmt,bp_w[i])[0]
                difference = decode_reference(yn,fmt)-decode_reference(yo,fmt)
                exact_effect = (sum((decode_reference(wp,fmt)-decode_reference(w,fmt))*decode_reference(x,fmt)
                                    for w,wp,x in zip(old_w[i],new_w[i],h_w))
                                +decode_reference(bp_w[i],fmt)-decode_reference(b_w[i],fmt))
                require(row['old_output_word']==yo and row['new_output_word']==yn,'Bound uses wrong execution words')
                require(Fraction(row['actual_output_difference'])==difference,'Bound output mismatch')
                require(Fraction(row['exact_effective_affine_response'])==exact_effect,'Bound affine endpoint mismatch')
                require(abs(difference)<=Fraction(row['absolute_output_bound']),'Bound is below independent output difference')
                require(difference==exact_effect+Fraction(row['new_error'])-Fraction(row['old_error']),
                        'Bound decomposition mismatch')
            bounds.append({'fixture':name,'old_words':[hex(r['old_output_word']) for r in result['rows']],
                           'new_words':[hex(r['new_output_word']) for r in result['rows']],
                           'differences':[r['actual_output_difference'] for r in result['rows']],
                           'absolute_bounds':[r['absolute_output_bound'] for r in result['rows']]})
        zero_dot = tuple(round_reference(x,fmt) for x in (a,1,-a,-1))
        z,trace = independent_dot(zero_dot,(one,)*4,fmt)
        require(decode_reference(z,fmt)==-1,'Independent zero-dot counterexample failed')
        records.append({'format':fmt,'RNE_values':len(values),'overflow_refusals':len(overflow_values),
                        'pointwise_cases':bounds,'zero_dot_result':str(decode_reference(z,fmt)),
                        'zero_dot_trace_words':[hex(x) for x in trace],
                        'scope':'Independent word-search RNE and exact affine expressions; finite values only'})
    return records


def canonical_record(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)


def resign(envelope):
    envelope['payload_sha256']=hashlib.sha256(canonical_record(envelope['payload']).encode('ascii')).hexdigest()
    return canonical_record(envelope)


def encode_rows(rows,fmt):
    return tuple(tuple(round_reference(Fraction(x),fmt) for x in row) for row in rows)


def certificate_checks():
    import certificate_kernel as ck
    records=[]
    for fmt in ('BF16','FP32'):
        one=round_reference(1,fmt)
        old=encode_rows(((1,0),(0,1)),fmt)
        witness=encode_rows(((0,1),(2,-1)),fmt)
        accepted=refused=0
        for values in product((-2,-1,0,1,2),repeat=4):
            candidate=encode_rows((values[:2],values[2:]),fmt)
            expected=all(independent_dense(candidate,h,fmt)==independent_dense(old,h,fmt)
                         for h in ((0,0),(one,one)))
            try:
                text=ck.make_certificate('duplicate_feedback_v1',fmt,old,candidate)
                packet=ck.check_certificate(text,'duplicate_feedback_v1',fmt,old)
            except ck.CertificateRejected:
                require(not expected,'Complete checker refused an independently safe small case')
                refused+=1
            else:
                require(expected,'Complete checker accepted an independently unsafe small case')
                require(packet['payload']['proof']['call_case_count']==4,'Both sites not covered')
                require(packet['payload']['proof']['transition_case_count']==4,'Complete bit domain not covered')
                accepted+=1
        trace_pairs=ticks=commits=0
        for initial in (0,1):
            for inputs in product((0,1),repeat=5):
                base=ck.CertificateKernel(fmt,initial_bit=initial)
                patched=ck.CertificateKernel(fmt,initial_bit=initial)
                q=initial
                for step,u in enumerate(inputs):
                    candidate=witness if step%2==0 else old
                    patched.commit(patched.prepare(candidate))
                    commits+=1
                    lhs=base.d_tick(one if u else 0)
                    rhs=patched.d_tick(one if u else 0)
                    expected=((one,one) if q else (0,0),
                              (one,one) if u else (0,0),
                              one if q!=u else 0)
                    require(lhs==rhs==expected,'Protected full outputs/state differ from independent recurrence')
                    q=int(q!=u)
                    require(base.state_word==patched.state_word==(one if q else 0),'Feedback state mismatch')
                    ticks+=1
                trace_pairs+=1
        kernel=ck.CertificateKernel(fmt)
        before=kernel.snapshot()
        a_old=kernel.a_output((one,0))
        valid=kernel.prepare(witness)
        kernel.commit(valid)
        a_new=kernel.a_output((one,0))
        require(a_old==(one,0) and a_new==(0,round_reference(2,fmt)),'Nonzero A-output witness failed')
        require(before[-2]==kernel.state_word,'Commit changed protected state')
        require(before[5]==old,'Previously returned primitive snapshot changed')
        try:kernel.commit(valid)
        except ck.CertificateRejected:pass
        else:raise AssertionError('Stale certificate replay accepted')

        tiny=((one,1),(0,one))
        tiny_evidence=[]
        for model in ('duplicate_feedback_v1','split_feedback_v1'):
            text=ck.make_certificate(model,fmt,old,tiny)
            p=ck.check_certificate(text,model,fmt,old)['payload']['proof']
            require(p['exact_effective_delta_annihilates_registered_span'] is False,
                    'Bitwise-only tiny update incorrectly declared algebraically zero')
            tiny_evidence.append({'model':model,'bitwise_accepted':True,'exact_annihilation':False})
        try:ck.make_certificate('shared_axis_v1',fmt,old,tiny)
        except ck.CertificateRejected:pass
        else:raise AssertionError('Axis e2 failed to expose tiny changed coefficient')

        kernel=ck.CertificateKernel(fmt)
        good=kernel.prepare(witness)
        preserved=kernel.snapshot()
        refusal_cases=[]
        def reject(name,call):
            snapshot=kernel.snapshot()
            try:call()
            except (ck.CertificateRejected,ValueError,TypeError):pass
            else:raise AssertionError('Adversarial input accepted: '+name)
            require(kernel.snapshot()==snapshot,'Refusal changed live snapshot: '+name)
            refusal_cases.append(name)
        mutations=[
          ('claim_algebra',lambda p:p.__setitem__('claim','exact_algebra_only')),
          ('claim_pointwise',lambda p:p.__setitem__('claim','pointwise_bounded')),
          ('version',lambda p:p.__setitem__('expected_weight_version',1)),
          ('old_endpoint',lambda p:p['old_weights'][0].__setitem__(0,0)),
          ('unsafe_new_endpoint',lambda p:p['new_weights'][0].__setitem__(0,one)),
          ('fake_effective_delta',lambda p:p['effective_delta'][0].__setitem__(0,[0,1])),
          ('model_id',lambda p:p.__setitem__('model_id','split_feedback_v1')),
          ('wrong_format',lambda p:p.__setitem__('format','FP32' if fmt=='BF16' else 'BF16')),
          ('missing_site',lambda p:p['descriptor']['sites'].pop()),
          ('missing_activation',lambda p:p['descriptor']['sites'][0]['activations'].pop()),
          ('missing_initial_state',lambda p:p['descriptor']['legal_initial_state_words'].pop()),
          ('sample_only',lambda p:p['descriptor'].__setitem__('coverage','observed_samples')),
          ('changed_domain',lambda p:p['descriptor'].__setitem__('domain_id','caller_domain')),
          ('changed_invariant',lambda p:p['descriptor'].__setitem__('invariant_id','caller_claim')),
          ('changed_shared_matrix',lambda p:p['descriptor'].__setitem__('physical_matrix_id','other_W')),
          ('graph_reduction',lambda p:p['descriptor']['graph'].__setitem__('matrix_evaluation','pairwise')),
          ('graph_fma',lambda p:p['descriptor']['graph'].__setitem__('arithmetic','fma')),
          ('graph_fusion',lambda p:p['descriptor']['graph'].__setitem__('transition','fused_transition')),
          ('site_order',lambda p:p['descriptor']['graph']['site_order'].reverse()),
          ('policy',lambda p:p['descriptor'].__setitem__('numerical_policy','flush_to_zero')),
          ('schedule',lambda p:p['descriptor'].__setitem__('schedule','inplace')),
          ('forged_proof',lambda p:p['proof']['call_cases'].pop()),
          ('forged_code_digest',lambda p:p['implementation_sha256'].__setitem__('certificate_kernel.py','0'*64)),
        ]
        for name,mutation in mutations:
            envelope=json.loads(good)
            mutation(envelope['payload'])
            # Recompute both publicly computable checksums: they are not authorization.
            envelope['payload']['descriptor_sha256']=hashlib.sha256(canonical_record(envelope['payload']['descriptor']).encode('ascii')).hexdigest()
            forged=resign(envelope)
            reject(name,lambda forged=forged:kernel.commit(forged))
        reject('noncanonical_json',lambda:kernel.commit(json.dumps(json.loads(good),indent=2)))
        reject('duplicate_key',lambda:kernel.commit('{"payload":{},"payload":{},"payload_sha256":""}'))
        reject('nonfinite_JSON',lambda:kernel.commit('{"payload":{"x":NaN},"payload_sha256":""}'))
        reject('oversized_JSON',lambda:kernel.commit(' '*100001))
        reject('invalid_bit',lambda:kernel.d_tick(True))
        reject('reordered_tick',lambda:kernel.d_tick(one,schedule='inplace'))
        reject('fused_tick',lambda:kernel.d_tick(one,policy='fma'))
        reject('reinitialize',lambda:kernel.__init__(fmt))
        reject('invalid_A_domain',lambda:kernel.a_output((one,one)))
        callbacks=[]
        class HostileStr(str):
            def __len__(self):
                callbacks.append('str_len')
                return super().__len__()
        class HostileTuple(tuple):
            def __len__(self):
                callbacks.append('tuple_len')
                return super().__len__()
        reject('callback_string',lambda:kernel.commit(HostileStr(good)))
        reject('callback_candidate',lambda:kernel.prepare(HostileTuple(witness)))
        require(callbacks==[],'Caller callbacks executed before rejection')
        require(kernel.snapshot()==preserved,'Adversarial cases changed baseline')
        # Global certificates remain valid after a legal state tick at unchanged weight version.
        kernel.d_tick(one)
        state_before_commit=kernel.state_word
        kernel.commit(good)
        require(kernel.state_word==state_before_commit==one,'Global certificate failed after legal state advance')

        # The old zero matrix and new rounded thirds map agree at the first input
        # but fail at the registered minimum-subnormal input.
        thirds_old=ck.initial_weights('thirds_two_inputs_v1',fmt)
        thirds_new=encode_rows(tuple(tuple(Fraction(2,3) if i==j else Fraction(-1,3)
                                            for j in range(3)) for i in range(3)),fmt)
        require(independent_dense(thirds_new,(one,)*3,fmt)==(0,)*3,'Thirds basis reference not zero')
        require(independent_dense(thirds_new,(1,)*3,fmt)==(1,)*3,'Thirds tiny reference not nonzero')
        try:ck.make_certificate('thirds_two_inputs_v1',fmt,thirds_old,thirds_new)
        except ck.CertificateRejected:pass
        else:raise AssertionError('Complete tiny activation omission was accepted')
        p=format_parameters(fmt)[0]+1
        commit_old=ck.initial_weights('commit_rounding_v1',fmt)
        commit_new=encode_rows(((2**p,-1),(0,0)),fmt)
        try:ck.make_certificate('commit_rounding_v1',fmt,commit_old,commit_new)
        except ck.CertificateRejected:pass
        else:raise AssertionError('Effective commit leak accepted')
        try:ck.make_certificate('split_feedback_v1',fmt,old,witness)
        except ck.CertificateRejected:pass
        else:raise AssertionError('Second shared call mismatch accepted')
        invalid_old=((0,0),(0,0))
        try:ck.make_certificate('duplicate_feedback_v1',fmt,invalid_old,invalid_old)
        except ck.CertificateRejected:pass
        else:raise AssertionError('Pairwise equality alone accepted an invalid stateful invariant')
        records.append({'format':fmt,'exhaustive_small_candidate_matrices':accepted+refused,
                        'independent_safe_candidates':accepted,'independent_unsafe_refusals':refused,
                        'trace_pairs':trace_pairs,'paired_ticks':ticks,'interleaved_commits':commits,
                        'A_response_before_words':list(a_old),'A_response_after_words':list(a_new),
                        'resigned_tampering_and_public_API_refusals':refusal_cases,
                        'refusal_count':len(refusal_cases),'callbacks_invoked':callbacks,
                        'stale_replay_refused':True,'global_certificate_survives_legal_state_advance':True,
                        'bitwise_without_algebra_examples':tiny_evidence,'shared_axis_exposes_tiny_update':True,
                        'subnormal_complete_domain_counterexample_refused':True,
                        'effective_commit_counterexample_refused':True,'additional_shared_site_counterexample_refused':True,
                        'equal_endpoints_with_wrong_stateful_invariant_refused':True})
    return records


def run_checks():
    started=time.perf_counter()
    import a3_runtime
    result={'schema':'dmwk-p2-a3-independent-review-v1','status':'passed',
            'evidence_type':'Finite independent implementation checks, not a universal machine proof',
            'started_utc':datetime.now(timezone.utc).isoformat(),
            'algebra':algebra_checks(),'rounding_and_bounds':rounding_and_bound_checks(),
            'certificates':certificate_checks(),
            'sampling':'None in this verifier; exhaustive declared small sets and deterministic adversarial fixtures',
            'SMT_queries':0,'proof_assistant_checked':False,'prior_stage_suites_rerun':False,
            'environment':a3_runtime.environment_metadata(),
            'elapsed_seconds':time.perf_counter()-started,
            'source_sha256':{name:checksum(ROOT/name) for name in
                ('verify_review_checks.py','linear_contracts.py','bounded_contracts.py','certificate_kernel.py','a3_runtime.py')},
            'not_proved':['Universal correctness of Python/NumPy/hardware','GPU/native BF16 execution',
                          'General concurrent or adversarial host-runtime safety','Arbitrary compiler optimization',
                          'All global-domain claims for arbitrary programs','Any P2-A4 result']}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'review_results.json')
    args=parser.parse_args()
    result=run_checks()
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'output':str(args.output),
                      'elapsed_seconds':result['elapsed_seconds']}))


if __name__=='__main__':
    main()

