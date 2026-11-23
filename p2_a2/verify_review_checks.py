"""Independent finite review checks for P2-A2.

The rank/projector oracle uses determinants, minors and cofactors rather than
production Gaussian elimination. The rounding oracle searches ordered positive
IEEE words rather than reusing the production rounding implementation.
These checks are finite evidence, not a proof of arbitrary programs/backends.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
import hashlib
import importlib
import json
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
P1_ROOT = ROOT.parent / 'dmwk-p1-foundations'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def det(rows):
    n = len(rows)
    if n == 0:
        return Fraction(1)
    if n == 1:
        return Fraction(rows[0][0])
    return sum(((-1)**j * rows[0][j] * det(tuple(
        tuple(row[k] for k in range(n) if k != j) for row in rows[1:]))
        for j in range(n)), Fraction(0))


def minor_rank(rows, width):
    for size in range(min(len(rows), width), 0, -1):
        for ri in combinations(range(len(rows)), size):
            for ci in combinations(range(width), size):
                if det(tuple(tuple(rows[i][j] for j in ci) for i in ri)):
                    return size
    return 0


def independent_projector(rows, width):
    """Return the exact complement projector and rank using a cofactor inverse."""
    d = len(rows)
    chosen = []
    for j in range(width):
        trial = chosen + [j]
        candidate = tuple(tuple(row[k] for k in trial) for row in rows)
        if minor_rank(candidate, len(trial)) > len(chosen):
            chosen.append(j)
    rank = len(chosen)
    if rank == 0:
        return tuple(tuple(Fraction(i == j) for j in range(d)) for i in range(d)), 0
    b = tuple(tuple(row[j] for j in chosen) for row in rows)
    gram = tuple(tuple(sum((b[k][i]*b[k][j] for k in range(d)), Fraction(0))
                       for j in range(rank)) for i in range(rank))
    denominator = det(gram)
    require(denominator > 0, 'Independent Gram determinant must be positive')
    inverse = tuple(tuple(((-1)**(i+j) * det(tuple(
        tuple(gram[x][y] for y in range(rank) if y != i)
        for x in range(rank) if x != j))) / denominator
        for j in range(rank)) for i in range(rank))
    result = tuple(tuple(Fraction(i == j) - sum((b[i][a]*inverse[a][c]*b[j][c]
                     for a in range(rank) for c in range(rank)), Fraction(0))
                    for j in range(d)) for i in range(d))
    return result, rank


def fp_parameters(fmt):
    if fmt == 'BF16':
        return 8
    if fmt == 'FP32':
        return 24
    raise ValueError('Unknown format')


def reference_decode(word, fmt):
    p = fp_parameters(fmt)
    fraction_bits = p-1
    sign_bit = 1 << (p+7)
    sign = -1 if word & sign_bit else 1
    magnitude = word & (sign_bit-1)
    exponent = magnitude >> fraction_bits
    trailing = magnitude & ((1 << fraction_bits)-1)
    if exponent == 255:
        raise ValueError('Nonfinite input is excluded')
    if exponent == 0:
        return sign * Fraction(trailing, 1 << (126+fraction_bits))
    significand = (1 << fraction_bits)+trailing
    scale = exponent-127-fraction_bits
    return sign * (Fraction(significand << scale) if scale >= 0
                   else Fraction(significand, 1 << (-scale)))


def reference_round(value, fmt):
    """Independent monotone-word binary search, RNE, gradual underflow, +0."""
    value = Fraction(value)
    if not value:
        return 0
    p = fp_parameters(fmt)
    sign_bit = 1 << (p+7)
    sign = sign_bit if value < 0 else 0
    value = abs(value)
    largest_word = (255 << (p-1))-1
    largest = reference_decode(largest_word, fmt)
    spacing = largest-reference_decode(largest_word-1, fmt)
    if value >= largest+spacing/2:
        raise OverflowError('Correct RNE result would be nonfinite')
    low, high = 0, largest_word
    while low < high:
        mid = (low+high+1)//2
        if reference_decode(mid, fmt) <= value:
            low = mid
        else:
            high = mid-1
    if low == largest_word:
        chosen = low
    else:
        lower = reference_decode(low, fmt)
        upper = reference_decode(low+1, fmt)
        dl, du = value-lower, upper-value
        chosen = low if dl < du or (dl == du and low % 2 == 0) else low+1
    return (chosen | sign) if chosen else 0


def reference_dot(row, activation, fmt):
    acc = 0
    words = []
    for a, b in zip(row, activation):
        operand_a, operand_b = reference_round(a, fmt), reference_round(b, fmt)
        prod = reference_round(reference_decode(operand_a, fmt)*reference_decode(operand_b, fmt), fmt)
        acc = reference_round(reference_decode(acc, fmt)+reference_decode(prod, fmt), fmt)
        words.append(acc)
    return reference_decode(acc, fmt), tuple(words)


def projection_checks():
    import exact_projection as exact
    cases = 0
    rank_histogram = {}
    # Every binary 3x3 matrix, including zero, repeated and dependent columns.
    for flat in product((0, 1), repeat=9):
        rows = tuple(tuple(Fraction(flat[3*i+j]) for j in range(3)) for i in range(3))
        expected, rank = independent_projector(rows, 3)
        result = exact.projection(exact.matrix(rows))
        require(result.P_perp.rows == expected, 'Projector disagrees with cofactor oracle')
        require(result.rank == rank == minor_rank(rows, 3), 'Protected rank disagrees with minors')
        alternative = exact.project_via_nullspace(exact.matrix(rows))
        require(alternative.rows == expected, 'Nullspace projector differs from cofactor oracle')
        rank_histogram[str(rank)] = rank_histogram.get(str(rank), 0)+1
        cases += 1
    special = [(((), (), ()), 0), ((), 3),
               (((Fraction(1),), (Fraction(1),), (Fraction(1),)), 1),
               (((Fraction(1),), (Fraction(3),)), 1),
               (((Fraction(1), Fraction(1)), (Fraction(0), Fraction(1, 2**30))), 2),
               (((Fraction(1, 3), Fraction(2, 3)), (Fraction(2, 7), Fraction(4, 7))), 2)]
    for rows, width in special:
        expected, rank = independent_projector(rows, width)
        result = exact.projection(exact.matrix(rows, ncols=width))
        require(result.P_perp.rows == expected and result.rank == rank,
                'Special shaped/rational projector case differs')
    # Independent learning-response and sharing checks with rational arithmetic.
    h = ((Fraction(1),), (Fraction(1),))
    p, rank = independent_projector(h, 1)
    a = (Fraction(1), Fraction(0))
    response = tuple(sum((p[i][j]*a[j] for j in range(2)), Fraction(0)) for i in range(2))
    require(response == (Fraction(1, 2), Fraction(-1, 2)), 'Nonzero complementary response')
    require(all(sum((p[i][j] for j in range(2)), Fraction(0)) == 0 for i in range(2)),
            'Protected input response must vanish')
    merged, merged_rank = independent_projector(((Fraction(1), Fraction(0)),
                                                (Fraction(0), Fraction(1))), 2)
    require(merged_rank == 2 and all(x == 0 for row in merged for x in row),
            'Merged full-rank sites must have zero complementary projector')
    return {'scope': 'Independent cofactor/minor oracle against production exact projector and nullspace route',
            'exhaustive_binary_3x3_matrices': cases, 'rank_histogram': rank_histogram,
            'special_empty_and_rational_matrices': len(special),
            'protected_vs_learning_response_checks': 1, 'merged_site_counterexamples': 1}


def rounding_checks():
    sys.path.insert(0, str(P1_ROOT))
    from p1_c3 import execution
    require(Path(execution.__file__).resolve() == P1_ROOT/'p1_c3/execution.py', 'P1 rounding dependency identity')
    rows = []
    for fmt in ('BF16', 'FP32'):
        p = fp_parameters(fmt)
        eta = Fraction(1, 1 << (126+p-1))
        mxword = (255 << (p-1))-1
        maximum = reference_decode(mxword, fmt)
        spacing = maximum-reference_decode(mxword-1, fmt)
        samples = [Fraction(0), Fraction(1), Fraction(-1), Fraction(1, 3), Fraction(2, 3),
                   Fraction(1, 10), Fraction(3, 10), Fraction(9, 10), Fraction(1, 6), Fraction(5, 6),
                   Fraction(1 << p), Fraction((1 << p)+1), Fraction((1 << p)+3),
                   eta/2, -eta/2, eta*Fraction(3, 2), -eta*Fraction(3, 2),
                   eta, maximum, maximum+spacing/4, -maximum]
        for value in samples:
            require(reference_round(value, fmt) == execution.round_fraction(value, fmt),
                    'Production quantizer disagrees with independent word-search RNE')
        overflows = 0
        for value in (maximum+spacing/2, -maximum-spacing/2):
            try:
                reference_round(value, fmt)
            except OverflowError:
                pass
            else:
                raise AssertionError('Independent overflow threshold failed')
            try:
                execution.round_fraction(value, fmt)
            except execution.ArithmeticRejected:
                overflows += 1
            else:
                raise AssertionError('Production overflow must reject')
        a = 1 << p
        dot, words = reference_dot((a, 1, -a, -1), (1, 1, 1, 1), fmt)
        require(dot == -1, 'Ordered dot counterexample must give -1')
        w, ideal = (Fraction(a), Fraction(0)), (Fraction(1), Fraction(-1))
        written = tuple(reference_decode(reference_round(x+y, fmt), fmt) for x,y in zip(w,ideal))
        effective = tuple(x-y for x,y in zip(written,w))
        require(sum(ideal) == 0 and sum(effective) == -1, 'Commit destroys ideal orthogonality')
        ones_projector, _ = independent_projector(((Fraction(1),),)*3, 1)
        quantized = tuple(tuple(reference_decode(reference_round(x,fmt),fmt) for x in row) for row in ones_projector)
        require(all(sum(row) == 0 for row in quantized), '1/3 projector can retain its exact row sums')
        require(quantized != ones_projector, '1/3 projector is not exactly represented')
        unequal_projector, _ = independent_projector(((Fraction(1),),(Fraction(3),)), 1)
        stored = tuple(tuple(reference_decode(reference_round(x,fmt),fmt) for x in row) for row in unequal_projector)
        residual = tuple(row[0]+3*row[1] for row in stored)
        require(any(residual), 'Different quantized projector loses its kernel')
        rows.append({'format':fmt, 'rounding_values_checked':len(samples), 'overflow_rejections':overflows,
                     'zero_dot_ordered_result':str(dot), 'zero_dot_accumulator_words':[hex(x) for x in words],
                     'commit_effective_delta':[str(x) for x in effective],
                     'thirds_projector_exact_stored_kernel_residual':['0','0','0'],
                     'unequal_basis_quantized_kernel_residual':[str(x) for x in residual],
                     'scope':'Independent exact arithmetic/reference expectations; production RNE is compared on listed values only'})
    return rows



def structural_checks():
    import safe_update as safe
    from p1_runtime import get_fp
    fp = get_fp()
    records = []
    for fmt in ('BF16', 'FP32'):
        one = reference_round(1, fmt)
        trace_count = tick_pairs = commits = 0
        # Independent Boolean state recurrence; no production test helper.
        for start in (0, 1):
            for inputs in product((0, 1), repeat=5):
                plain = safe.StructuralKernel(fmt, start)
                changed = safe.StructuralKernel(fmt, start)
                expected = start
                for t, incoming in enumerate(inputs):
                    theta = (2, -3, 1, 0, 2)[t]
                    word = reference_round(theta, fmt)
                    before = changed.snapshot()
                    candidate = (changed.weights[0], (0, word))
                    changed.commit_words(candidate, expected_version=changed.version,
                                         format_name=fmt)
                    commits += 1
                    require(before[5] == changed.state_word and before[6] == changed.ticks,
                            'Weight commit must preserve D state and clock')
                    require(changed.a_output(one) == word,
                            'Changed A output differs from independent stored theta')
                    require(changed.a_output(0) == 0, 'Zero A input must remain canonical zero')
                    expected ^= incoming
                    raw = one if incoming else 0
                    pword, cword = plain.d_tick(raw), changed.d_tick(raw)
                    tick_pairs += 1
                    require(pword == cword == (one if expected else 0),
                            'Protected trace differs from independent XOR recurrence')
                require(changed.ticks == plain.ticks == 5, 'Completed clock count mismatch')
                trace_count += 1
        kernel = safe.StructuralKernel(fmt)
        flags = {'callback':False}
        class CallbackCounter(int):
            def __add__(self, other):
                flags['callback'] = True
                raise AssertionError('Untrusted counter callback was invoked')
        class CallbackList(list):
            def append(self, value):
                flags['callback'] = True
                raise AssertionError('Untrusted event callback was invoked')
        counter_audit = fp.Audit(); counter_audit.native_multiply = CallbackCounter(0)
        list_audit = fp.Audit(); list_audit.events = CallbackList()
        p = fp_parameters(fmt)
        negative_zero = 1 << (p+7)
        infinity = 255 << (p-1)
        valid = kernel.weights
        invalid_actions = [
            lambda: kernel.commit_words(((0,0),valid[1]),expected_version=0,format_name=fmt),
            lambda: kernel.commit_words((valid[0],(0,negative_zero)),expected_version=0,format_name=fmt),
            lambda: kernel.commit_words((valid[0],(0,infinity)),expected_version=0,format_name=fmt),
            lambda: kernel.commit_words((valid[0],(0,infinity+1)),expected_version=0,format_name=fmt),
            lambda: kernel.commit_words((valid[0],(0,True)),expected_version=0,format_name=fmt),
            lambda: kernel.commit_words(valid,expected_version=1,format_name=fmt),
            lambda: kernel.commit_words(valid,expected_version=0,format_name=fmt,route='algebraic_projection'),
            lambda: kernel.commit_words(valid,expected_version=0,format_name=fmt,policy='fused'),
            lambda: kernel.d_tick(negative_zero),
            lambda: kernel.d_tick(one,policy='reassociated'),
            lambda: kernel.d_tick(one,audit=object()),
            lambda: kernel.d_tick(one,audit=counter_audit),
            lambda: kernel.a_output(one,audit=list_audit),
            lambda: kernel.__init__(fmt,1),
        ]
        refusals = 0
        for action in invalid_actions:
            before = kernel.snapshot()
            try:
                action()
            except safe.UpdateRejected:
                refusals += 1
            else:
                raise AssertionError('Structural malformed request was accepted')
            require(kernel.snapshot() == before, 'Rejected operation changed protected bank')
        require(not flags['callback'], 'Validation invoked an untrusted audit callback')
        old_snapshot = kernel.snapshot()
        kernel.commit_theta_ideal(2, expected_version=kernel.version)
        require(old_snapshot[3][1][1] == one and old_snapshot[2] == 0,
                'Immutable prior snapshot changed after later commit')
        require(kernel.a_output(one) == reference_round(2,fmt), 'Nonzero A response not witnessed')
        records.append({'format':fmt, 'all_length_five_input_sequences_per_initial_state':32,
                        'initial_states':2, 'trace_pairs':trace_count, 'protected_tick_pairs':tick_pairs,
                        'interleaved_nontrivial_or_zero_theta_commits':commits,
                        'expected_refusals_with_unchanged_snapshot':refusals,
                        'audit_callbacks_invoked':False,
                        'prior_snapshot_remained_immutable':True,
                        'scope':'Finite independent Boolean oracle traces and public API boundary checks; not a universal/concurrent proof'})
    return records



def numerical_certificate_checks():
    import exact_projection as exact
    import numerical_projection as numeric
    cases = []
    for fmt in ('BF16','FP32'):
        p = fp_parameters(fmt)
        a = 1 << p
        protected = exact.matrix(((1,), (1,)))
        independently_expected, _ = independent_projector(protected.rows,1)
        projector = exact.matrix(independently_expected)
        w = exact.matrix(((a,0),(0,0)))
        g = exact.matrix(((1,-1),(0,0)))
        candidate = g  # Independent algebra: rows annihilate (1,1).
        certificate = numeric.perturbation_certificate(w,g,projector,projector,
                                                     candidate,protected,fmt)
        expected_new = tuple(tuple(reference_decode(reference_round(w.rows[i][j]+candidate.rows[i][j],fmt),fmt)
                                   for j in range(2)) for i in range(2))
        old_y = tuple(reference_dot(row,(1,1),fmt)[0] for row in w.rows)
        new_y = tuple(reference_dot(row,(1,1),fmt)[0] for row in expected_new)
        difference = tuple(b-a for a,b in zip(old_y,new_y))
        observed_record = tuple(Fraction(row[0]) for row in certificate['exact_observed_output_difference']['rows'])
        require(observed_record == difference == (Fraction(-1),Fraction(0)),
                'T3 observed difference disagrees with independent word-search execution')
        upper = Fraction(certificate['output_2norm_upper'])
        require(sum((x*x for x in difference),Fraction(0)) <= upper*upper,
                'T3 bound does not enclose independent output')
        components = {k:Fraction(v) for k,v in certificate['norm_upper_components'].items()}
        require(components['projection'] == components['candidate_product'] == 0,
                'Exact algebraic candidate unexpectedly carries projection/generation error')
        require(components['old_execution'] == components['new_execution'] == 0,
                'Exactly represented dot should have zero local execution error')
        require(components['commit_quantization']**2 >= 2,
                'Certified Frobenius storage term underestimates ||S||F||h||2')
        maximum = reference_decode((255 << (p-1))-1,fmt)
        committed = numeric.commit_weights(exact.matrix(((-maximum,),)),
                                            exact.matrix(((2*maximum,),)),fmt)
        require(committed['new'].rows == ((maximum,),),
                'Finite final sum must not be rejected due to oversized ideal increment')
        require(not committed['candidate_exactly_storable'],
                'Oversized ideal increment is not a stored-word increment')
        eta = Fraction(1,1 << (126+p-1))
        subnormal = numeric.dot((eta,), (Fraction(1,2),), fmt)
        require(subnormal.decoded_output == 0 and subnormal.exact_dot == eta/2,
                'Subnormal tie differs from independent expectation')
        require(subnormal.local_absolute_error_bound == eta/2 and subnormal.gamma_bound is None,
                'Invalid relative model must not receive a gamma bound')
        retained = numeric.dot((eta,), (1,), fmt)
        scaled_retained = numeric.dot((2*eta,), (Fraction(1,2),), fmt)
        require(retained.decoded_output == scaled_retained.decoded_output == eta,
                'Nonzero gradual-underflow witness was flushed to zero')
        # A basis-vector execution residual cannot certify all legal vectors in its span.
        thirds = tuple(tuple(reference_decode(reference_round(
            Fraction(1 if i == j else 0)-Fraction(1,3), fmt),fmt)
                             for j in range(3)) for i in range(3))
        require(all(sum(row,Fraction(0)) == 0 for row in thirds),
                'This fixture must preserve its exact decoded kernel')
        basis_outputs = tuple(reference_dot(row,(1,1,1),fmt)[0] for row in thirds)
        tiny_outputs = tuple(reference_dot(row,(eta,eta,eta),fmt)[0] for row in thirds)
        actual_tiny = tuple(numeric.dot(row,(eta,eta,eta),fmt) for row in thirds)
        require(basis_outputs == (0,0,0) and tiny_outputs == (eta,eta,eta),
                'Independent rounding did not distinguish the two legal activations')
        require(all(result.decoded_output == eta and result.gamma_bound is None
                    for result in actual_tiny),
                'Production execution or relative-model guard disagrees with independent subnormal case')
        cases.append({'format':fmt,'independent_T3_output_difference':[str(x) for x in difference],
                      'reported_output_norm_upper':str(upper),
                      'finite_sum_with_unstorable_ideal_increment_accepted':True,
                      'subnormal_tie_local_error':str(eta/2),'invalid_gamma_bound_absent':True,
                      'nonzero_subnormal_results_retained':2,
                      'basis_residual_zero_does_not_certify_all_legal_activations':True,
                      'tiny_activation_ordered_output_words':['0x1']*3})
    near = exact.matrix(((1,1),(0,Fraction(1,2**30))))
    expected, exact_rank = independent_projector(near.rows,2)
    require(exact_rank == 2 and not any(x for row in expected for x in row),
            'Near-rank case must be exactly full rank')
    d64 = numeric.svd_projection(near,'float64')['diagnostics']
    d32 = numeric.svd_projection(near,'float32')['diagnostics']
    require(d64['numerical_effective_rank']==2 and d32['numerical_effective_rank']==1,
            'Explicit single/double precision threshold distinction missing')
    require('f->fff' in d32['solver_dispatch'], 'FP32 SVD must select an actual single precision dispatch')
    require(d32['converted_input_exact_rank']==2, 'False capacity must not be due to input rank collapse')
    cutoff = float(Fraction(1)-Fraction(1,2**53))
    boundary = numeric.svd_projection(exact.matrix(((1,0),(0,1))), 'float32', rtol=cutoff)['diagnostics']
    require(boundary['numerical_effective_rank']==2 and boundary['threshold']==cutoff,
            'FP32 singular values must be compared against the recorded binary64 cutoff')
    threshold_rejected = False
    try:
        numeric.svd_projection(exact.matrix(((2,0),(0,1))),'float64',rtol=1e308)
    except numeric.NumericalRejected:
        threshold_rejected = True
    require(threshold_rejected, 'Overflowing threshold must be refused')
    return {'pointwise_certificates':cases,
            'near_rank_exact_rank':exact_rank,
            'FP64_default_effective_rank':d64['numerical_effective_rank'],
            'FP32_default_effective_rank':d32['numerical_effective_rank'],
            'FP32_solver_dispatch':d32['solver_dispatch'],
            'threshold_overflow_rejected':threshold_rejected,
            'binary64_cutoff_comparison_boundary_verified':True,
            'scope':'Independent finite T3 output/RNE and exact-rank comparisons; not a universal or interval-certified SVD result'}


def run_checks():
    started = time.perf_counter()
    result = {'schema':'dmwk-p2-a2-independent-review-v1', 'status':'running',
              'evidence_type':'Finite independent implementation checks; not a universal machine proof',
              'projection':projection_checks(), 'rounding':rounding_checks(),
              'structural':structural_checks(),
              'numerical_certificates':numerical_certificate_checks()}
    result.update(status='passed', elapsed_seconds=time.perf_counter()-started,
                  source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                 for name in ('verify_review_checks.py','exact_projection.py','safe_update.py','p1_runtime.py','numerical_projection.py')},
                  p1_rounding_sha256=hashlib.sha256((P1_ROOT/'p1_c3/execution.py').read_bytes()).hexdigest(),
                  not_proved=['All arbitrary rational matrices','General GPU/native BF16 behavior',
                              'Full compiler refinement','General weight patch safety','Any P2-A3 result'])
    return result


def main():
    result = run_checks()
    output = ROOT/'review_results.json'
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],
                      'binary_projector_cases':result['projection']['exhaustive_binary_3x3_matrices'],
                      'formats_checked':len(result['rounding']), 'output':str(output)}))


if __name__ == '__main__':
    main()
