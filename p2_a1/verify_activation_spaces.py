"""Reproduce P2-A1 finite examples, exact algebra, and compiler observations.

Run with Python 3.12 and NumPy 2.3.5. No P1 suite is invoked or modified.
The finite model checks do not certify an arbitrary compiler/backend or P2-A2.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import platform
import random
import sys
import time

sys.dont_write_bytecode = True
from activation_spaces import (Basis, Call, affine_lift, enumerate_reachable,
                               homogeneous, invariant_linear_hull, matrix_apply,
                               span, vector)

ROOT = Path(__file__).resolve().parent
SEED = 20261113


class Checks:
    def __init__(self):
        self.count = 0
    def __call__(self, condition, message):
        self.count += 1
        if not condition:
            raise AssertionError(message)
    def rejects(self, callback, message):
        self.count += 1
        try:
            callback()
        except ValueError:
            return
        raise AssertionError(message)


check = Checks()


def determinant(matrix):
    """Independent Leibniz formula, deliberately small and exponential."""
    n = len(matrix)
    total = Fraction(0)
    for p in itertools.permutations(range(n)):
        inversions = sum(p[i] > p[j] for i in range(n) for j in range(i+1, n))
        term = Fraction(-1 if inversions % 2 else 1)
        for i, j in enumerate(p):
            term *= matrix[i][j]
        total += term
    return total


def minor_rank(rows, width):
    for k in range(min(len(rows), width), 0, -1):
        for selected_rows in itertools.combinations(rows, k):
            for columns in itertools.combinations(range(width), k):
                square = [[r[j] for j in columns] for r in selected_rows]
                if determinant(square):
                    return k
    return 0


def algebra_checks():
    rng = random.Random(SEED)
    tests = []
    for _ in range(80):
        width, count = rng.randrange(1, 5), rng.randrange(0, 5)
        rows = [tuple(Fraction(rng.randrange(-3, 4), rng.randrange(1, 4)) for _ in range(width))
                for _ in range(count)]
        b = span(rows, width)
        check(b.rank == minor_rank(rows, width), 'Fraction elimination differs from determinant-minor oracle')
        check(all(b.contains(v) for v in rows), 'Basis lost an original vector')
        shuffled = rows.copy(); rng.shuffle(shuffled)
        check(b.rows == span(shuffled, width).rows, 'RREF depends on row presentation order')
        tests.append({'rows': count, 'dimension': width, 'rank': b.rank,
                      'peak_stored_rational_bits': b.peak_rational_bits})
    check.rejects(lambda: span([(1.0,)], 1), 'Host float must not be admitted as exact input')
    check.rejects(lambda: span([(True,)], 1), 'Host bool must not be admitted as exact scalar')
    check.rejects(lambda: span([(1, 2)], 1), 'Bad shape must be rejected')
    return {'scope': '80 seeded finite rational matrices, not all matrices', 'seed': SEED,
            'oracle': 'exact Leibniz determinants of all candidate minors', 'cases': tests}


def static_case(name, activations, dimension, expected_rank, expected_homogeneous_rank):
    rows = tuple(vector(v) for v in activations)
    b, hb = span(rows, dimension), span(tuple(homogeneous(v) for v in rows), dimension+1)
    check(b.rank == expected_rank, name+' rank')
    check(hb.rank == expected_homogeneous_rank, name+' homogeneous rank')
    return {'name': name, 'evidence': 'exhaustive declared finite activation domain',
            'activation_count': len(rows), 'linear': b.summary(), 'homogeneous': hb.summary(),
            'affine_dimension': hb.rank-1 if rows else None,
            'activation_domain': [[str(x) for x in v] for v in rows]}


def finite_activation_examples():
    boolean3 = tuple(itertools.product((0, 1), repeat=3))
    correlated = ((0, 0), (1, 1))
    onehot3 = tuple(tuple(int(i == j) for i in range(3)) for j in range(3))
    onehot8 = tuple(tuple(int(i == j) for i in range(8)) for j in range(8))
    product = tuple((a, b, a*b) for a, b in itertools.product((0, 1), repeat=2))
    pc_inputs = tuple(tuple(bits)+(tuple(int(i == j) for i in range(3)))+(u,)
                      for bits in itertools.product((0, 1), repeat=2)
                      for j in range(3) for u in (0, 1))
    return [static_case('all_boolean_3', boolean3, 3, 3, 4),
            static_case('correlated_two_bits', correlated, 2, 1, 2),
            static_case('one_hot_3', onehot3, 3, 3, 3),
            static_case('no_calls', (), 3, 0, 0),
            static_case('only_zero', ((0, 0, 0),), 3, 0, 1),
            static_case('scalar_packed_0_through_7', tuple((v,) for v in range(8)), 1, 1, 2),
            static_case('one_hot_8_codes', onehot8, 8, 8, 8),
            static_case('nonlinear_product_feature', product, 3, 3, 4),
            static_case('two_register_bits_one_hot_3_pc_one_input', pc_inputs, 6, 6, 6)]


def sharing_and_state_examples():
    universe = frozenset((0, 1))
    def sharing_step(q, u):
        # One 1x2 matrix identifier, two sites in the same physical coordinates.
        return u, (Call('shared_1x2', 'left', (q, 0)), Call('shared_1x2', 'right', (0, q)))
    both = enumerate_reachable((0,), lambda q: (0, 1), sharing_step, universe=universe)
    summary = both.spaces()
    check(len(both.states) == 2 and len(both.edges) == 4, 'Sharing reachable model')
    check(summary['per_matrix']['shared_1x2']['rank_Q_equals_rank_R'] == 2, 'Sharing union must be full rank')
    check(all(x['rank_Q_equals_rank_R'] == 1 for x in summary['per_call_site']), 'Each sharing site rank one')
    restricted = enumerate_reachable((0,), lambda q: (0,), sharing_step, universe=universe)
    check(restricted.spaces()['per_matrix']['shared_1x2']['rank_Q_equals_rank_R'] == 0, 'Input contract changes span')
    broad_init = enumerate_reachable((0, 1), lambda q: (0,), sharing_step, universe=universe)
    check(broad_init.spaces()['per_matrix']['shared_1x2']['rank_Q_equals_rank_R'] == 2, 'Initial-state contract changes span')

    # Correlation is preserved by toggle, but a reset to (1,0) creates a new direction.
    pair_universe = frozenset(itertools.product((0, 1), repeat=2))
    def reset_step(q, reset):
        target = (1, 0) if reset else (1-q[0], 1-q[1])
        return target, (Call('pair', 'read_old', q),)
    no_reset = enumerate_reachable(((0, 0),), lambda q: (0,), reset_step, universe=pair_universe)
    reset = enumerate_reachable(((0, 0),), lambda q: (0, 1), reset_step, universe=pair_universe)
    check(no_reset.spaces()['per_matrix']['pair']['rank_Q_equals_rank_R'] == 1, 'Toggle correlation')
    check(reset.spaces()['per_matrix']['pair']['rank_Q_equals_rank_R'] == 2, 'Reset destroys rank deficiency')

    # An explicit history monitor: alternating legal input sequence 0,1,0,1,... .
    monitor_universe = frozenset(itertools.product((0, 1), repeat=2))
    def monitored_step(q, u):
        return (u, 1-q[1]), (Call('history', 'old_and_input', (q[0], u)),)
    monitored = enumerate_reachable(((0, 0),), lambda q: (q[1],), monitored_step,
                                   universe=monitor_universe)
    check(len(monitored.states) == 3 and len(monitored.edges) == 3, 'Finite monitor is part of state')
    check.rejects(lambda: enumerate_reachable((0,), lambda q: (0, 1), sharing_step,
                                              universe=universe, state_limit=1), 'Partial exploration must fail')
    check.rejects(lambda: enumerate_reachable((0,), lambda q: [0], sharing_step,
                                              universe=universe), 'Unbounded/implicit input iterable rejected')
    check.rejects(lambda: enumerate_reachable((0,), lambda q: (0,), lambda q,u:(2,()),
                                              universe=universe), 'Out-of-universe state rejected')
    never_called = enumerate_reachable((0,), lambda q: (), lambda q,u: (q,()),
        universe=frozenset((0,)), matrix_dimensions={'unreachable_matrix': 3},
        declared_sites=(('unreachable_matrix','unreachable_site'),))
    never_summary = never_called.spaces()
    check(never_summary['per_matrix']['unreachable_matrix']['rank_Q_equals_rank_R'] == 0,
          'Declared but uncalled matrix has zero span')
    check(never_summary['per_call_site'][0]['rank_Q_equals_rank_R'] == 0,
          'Declared but unreachable call site has zero span')
    check.rejects(lambda: enumerate_reachable((0,), lambda q: (0,), sharing_step,
        universe=universe,matrix_dimensions={'other':2}), 'Unknown matrix cannot enter declared registry')
    return {'declared_never_called_matrix': never_summary,
            'shared_two_sites': summary, 'restricted_inputs': restricted.spaces(),
            'expanded_initial_states': broad_init.spaces(), 'no_reset': no_reset.spaces(),
            'reset_allowed': reset.spaces(), 'explicit_alternating_input_monitor': monitored.spaces(),
            'scope': 'Exhaustive finite transition systems including their explicit monitor state'}


def delayed_direction():
    threshold = 8
    def step(q, u):
        return min(q+1, threshold), (Call('delayed', 'clocked_read', (1, int(q == threshold))),)
    result = enumerate_reachable((0,), lambda q: (None,), step,
                                 universe=frozenset(range(threshold+1)))
    rows = [c.activation for c in result.calls]
    check(span(rows[:threshold], 2).rank == 1, 'Finite prefix low rank')
    check(span(rows, 2).rank == 2, 'All-time delayed direction')
    return {'threshold': threshold, 'clock_states': len(result.states),
            'observed_first_8_call_rank': 1, 'full_reachable_call_rank': 2,
            'first_unseen_direction_call_index_zero_based': threshold,
            'full_spaces': result.spaces(),
            'meaning': 'This single exhaustive counterexample refutes inference from an 8-call sample; a handwritten family extends it to every finite sampling horizon.'}


def invariant_examples():
    initial = (homogeneous((0, 0)),)
    identity = ((1, 0), (0, 1))
    generators = (affine_lift(identity, (1, 1)), affine_lift(((0, 0), (0, 0)), (0, 0)))
    hull, certificate = invariant_linear_hull(initial, generators, 3)
    check(hull.rank == 2, 'Diagonal affine invariant hull')
    check(all(hull.contains(homogeneous((n, n))) for n in range(-5, 6)), 'Independent diagonal samples')
    # Independent syntactic row certificates: x-y is annihilated and homogeneous last row is preserved.
    for m in generators:
        check(tuple(m[0][j]-m[1][j] for j in range(3)) in ((1, -1, 0), (0, 0, 0)),
              'Diagonal invariant symbolic row difference')
        check(m[2] == (0, 0, 1), 'Homogeneous-coordinate invariant')
    expanded, expanded_cert = invariant_linear_hull(initial,
        generators + (affine_lift(((0, 0), (0, 0)), (1, 0)),), 3)
    check(expanded.rank == 3, 'Additional reset removes affine invariant')
    # Conservative unconstrained transitions may overapproximate unreachable branches.
    branch_ignored, cert2 = invariant_linear_hull((homogeneous((0, 0)),),
        (affine_lift(identity, (1, 0)), affine_lift(identity, (0, 1)),
         affine_lift(identity, (0, 0))), 3)
    check(branch_ignored.rank == 3, 'All affine branches conservatively admitted')
    guarded = enumerate_reachable(((0,0),),lambda q:(None,),
        lambda q,u:((1,0),(Call('guarded','old_state',homogeneous(q)),)),
        universe=frozenset(((0,0),(1,0))),matrix_dimensions={'guarded':3},
        declared_sites=(('guarded','old_state'),))
    exact_guarded = span((c.activation for c in guarded.calls),3)
    check(exact_guarded.rank == 2, 'A guard-restricted bounded example has smaller span')
    check(len(guarded.states)==2 and len(guarded.edges)==2,'Guarded system exhaustively enumerated')
    check(all(branch_ignored.contains(c.activation) for c in guarded.calls),'Guard relaxation contains exact reachable span')
    v = (1, -1); line = span((v,), 2); relu_v = (1, 0)
    check(not line.contains(relu_v), 'ReLU need not preserve a linear subspace')
    basis_vectors=((1,1,0),(0,1,1));nonlinear_plane=span(basis_vectors,3)
    check(all(tuple(max(0,x) for x in v)==v for v in basis_vectors),
          'ReLU fixes both chosen basis vectors')
    difference=(1,0,-1);relu_difference=(1,0,0)
    check(nonlinear_plane.contains(difference),'Signed combination belongs to the plane')
    check(not nonlinear_plane.contains(relu_difference),'Basis-only ReLU check fails on a signed combination')
    empty, empty_cert = invariant_linear_hull((), generators, 3)
    check(empty.rank == 0, 'Empty initial set has empty span')
    return {'diagonal_affine_family': {'hull': hull.summary(), 'certificate': certificate},
            'added_reset': {'hull': expanded.summary(), 'certificate': expanded_cert},
            'guard_relaxation': {'conservative': branch_ignored.summary(), 'certificate': cert2,
                'guarded_two_state_span': exact_guarded.summary(),'exact_guarded_graph':guarded.spaces(),
                'guarded_model': 'q=(0,0) takes translation +(1,0); q=(1,0) takes the identity generator. Translation +(0,1) is disabled everywhere. Ignoring those guards yields the declared three-generator family.'},
            'nonlinear_counterexample': {'input_vector': v, 'relu_vector': relu_v,
                'input_span_rank': 1, 'relu_in_input_span': False},
            'basis_only_nonlinear_check_counterexample':{'basis_vectors':basis_vectors,
                'both_basis_vectors_fixed_by_relu':True,'signed_combination':difference,
                'relu_of_signed_combination':relu_difference,'relu_result_in_original_plane':False,
                'plane_equation':'coordinate_1 = coordinate_0 + coordinate_2'},
            'empty_initial_set': {'hull': empty.summary(), 'certificate': empty_cert},
            'scope': 'Rational affine generator family. Unbounded translation is algebraic only, not a claim of indefinitely exact finite-FP addition.'}


def load_p1(p1_root):
    sys.path.insert(0, str(p1_root))
    from p1_a4 import compiler
    from p1_c3 import execution
    import numpy as np
    check(Path(compiler.__file__).resolve() == (p1_root/'p1_a4/compiler.py').resolve(), 'Compiler provenance')
    check(Path(execution.__file__).resolve() == (p1_root/'p1_c3/execution.py').resolve(), 'Arithmetic provenance')
    return compiler, execution, np


def compiled_example(comp, np, name, program, initial, legal_inputs, format_name):
    compiled = comp.compile_program(program)
    source_universe = frozenset(comp.State(tuple(values), pc)
        for values in itertools.product(*(range(1 << typ.width) for _,typ in program.registers))
        for pc in range(len(program.blocks)))
    native = comp.Executor(format_name)
    observed = comp.Executor(format_name)
    # Explicit new sharing adapter: row keys include bias and ordered coefficients.
    registry, site_to_shared = {}, {}
    for index, node in enumerate(compiled.nodes):
        signature = tuple(c for _, c in node.terms)+(node.bias,)
        registry.setdefault(signature, (f'row_{len(registry):03d}', signature))
        site_to_shared[index] = registry[signature]
    intrinsic_calls = []
    input_summaries = []
    zero_words_checked = 0
    def traced_step(state, input_values):
        nonlocal zero_words_checked
        state_bits = observed.encode_state(compiled, state)
        input_bits = observed.encode_inputs(compiled, input_values)
        old_state_words = tuple(int(x) for x in observed.words(state_bits))
        old_input_words = tuple(int(x) for x in observed.words(input_bits))
        wires = list(state_bits.copy())+list(input_bits.copy())
        events = []
        for index, node in enumerate(compiled.nodes):
            mid, row = site_to_shared[index]
            check(row is registry[tuple(c for _,c in node.terms)+(node.bias,)][1], 'Adapter row identity')
            activation = tuple(Fraction(observed._value(wires[w])) for w,_ in node.terms)+(Fraction(1),)
            intrinsic_calls.append(Call(f'node_{index:03d}', f'node_{index:03d}', activation))
            events.append(Call(mid, f'node_{index:03d}', activation))
            accumulator = observed.const(row[-1])
            for (wire, _), coefficient in zip(node.terms, row[:-1]):
                product = observed._op('multiply', observed.const(coefficient), wires[wire])
                accumulator = observed._op('add', accumulator, product)
            value = observed._value(accumulator)
            if (node.activation == 'relu' and value <= 0) or value == 0:
                accumulator = observed.const(0)
            check(observed._value(accumulator) in (0, 1), 'Observed node Boolean closure')
            raw = observed.scalar_bits(accumulator)
            if observed._value(accumulator) == 0:
                check(raw == 0, 'Observed node canonical +0'); zero_words_checked += 1
            wires.append(accumulator)
        actual = np.array([wires[i] for i in compiled.outputs], dtype=observed.dtype)
        expected = native.tick(compiled, state_bits, input_bits)
        check(np.array_equal(observed.words(actual), native.words(expected)), 'Instrumented shared adapter vs actual P1 tick bits')
        check(tuple(int(x) for x in observed.words(state_bits)) == old_state_words, 'Input state snapshot unchanged')
        check(tuple(int(x) for x in observed.words(input_bits)) == old_input_words, 'External input snapshot unchanged')
        next_state = observed.decode_state(compiled, actual)
        check(next_state == comp.source_step(program, state, input_values), 'Actual graph matches source transition for explored edge')
        input_summaries.append(tuple(Fraction(observed._value(x)) for x in list(state_bits)+list(input_bits)))
        return next_state, tuple(events)
    reach = enumerate_reachable((initial,), lambda state: legal_inputs, traced_step, universe=source_universe,
        matrix_dimensions={mid:len(row) for mid,row in registry.values()},
        declared_sites=tuple((site_to_shared[i][0],f'node_{i:03d}') for i in range(len(compiled.nodes))))
    tied_summary = reach.spaces()
    from activation_spaces import Reachability
    intrinsic_summary = Reachability(reach.states, reach.edges, tuple(intrinsic_calls), reach.depths,
        {f'node_{i:03d}':len(node.terms)+1 for i,node in enumerate(compiled.nodes)},
        tuple((f'node_{i:03d}',f'node_{i:03d}') for i in range(len(compiled.nodes)))).spaces()
    intrinsic_operand_summary = Reachability(reach.states, reach.edges,
        tuple(Call(c.matrix_id,c.site_id,c.activation[:-1]) for c in intrinsic_calls), reach.depths,
        {f'node_{i:03d}':len(node.terms) for i,node in enumerate(compiled.nodes)},
        tuple((f'node_{i:03d}',f'node_{i:03d}') for i in range(len(compiled.nodes)))).spaces()
    tied_operand_summary = Reachability(reach.states, reach.edges,
        tuple(Call(c.matrix_id,c.site_id,c.activation[:-1]) for c in reach.calls),reach.depths,
        {mid:len(row)-1 for mid,row in registry.values()},
        tuple((site_to_shared[i][0],f'node_{i:03d}') for i in range(len(compiled.nodes)))).spaces()
    check(len(reach.calls) == len(reach.edges)*len(compiled.nodes), 'Every node called every tick, including inactive source blocks')
    input_basis = span(input_summaries, compiled.input_count)
    input_homogeneous = span(tuple(homogeneous(v) for v in input_summaries), compiled.input_count+1)
    row_metadata = []
    for signature, (mid, row) in registry.items():
        sites = [i for i,(other_mid,_) in site_to_shared.items() if other_mid == mid]
        data = tied_summary['per_matrix'][mid]
        site_ranks = [intrinsic_summary['per_matrix'][f'node_{i:03d}']['rank_Q_equals_rank_R'] for i in sites]
        distinct_activations=sorted({c.activation for c in reach.calls if c.matrix_id==mid})
        row_metadata.append({'matrix_id':mid,'coefficients_in_term_order':list(row[:-1]),'bias':row[-1],
            'distinct_operand_activations':[[int(x) for x in v[:-1]] for v in distinct_activations],
            'distinct_augmented_activations':[[int(x) for x in v] for v in distinct_activations],
            'call_sites':sites,'per_site_ranks':site_ranks,'merged_rank':data['rank_Q_equals_rank_R'],
            'ambient_augmented_input_dimension':len(row),
            'operand_only_merged_rank':tied_operand_summary['per_matrix'][mid]['rank_Q_equals_rank_R'],
            'operand_only_per_site_ranks':[intrinsic_operand_summary['per_matrix'][f'node_{i:03d}']['rank_Q_equals_rank_R'] for i in sites],
            'ambient_operand_only_dimension':len(row)-1})
    if name=='two_bit_counter_to_two':
        by_id={g['matrix_id']:g for g in row_metadata}
        expanding, deficient=by_id['row_003'],by_id['row_005']
        check(expanding['coefficients_in_term_order']==[1,1,-2],'Counter expanding row identity')
        check(max(expanding['operand_only_per_site_ranks'])==2 and expanding['operand_only_merged_rank']==3,
              'Every individual counter row site deficient but shared operand span full')
        check(max(expanding['per_site_ranks'])==3 and expanding['merged_rank']==4,
              'Counter shared augmented span full')
        check(deficient['coefficients_in_term_order']==[1,1,-1],'Counter deficient row identity')
        check(deficient['operand_only_merged_rank']==2 and deficient['merged_rank']==3,
              'Counter shared row retains one missing direction')
        check(all(v[2]==0 for v in deficient['distinct_operand_activations']),
              'Counter deficient row third operand is zero over all reachable calls')
    return {'name':name,'format':format_name,
        'arithmetic_backend': 'P1 A4 software BF16 raw words with exact small-integer [-4,4] certificates' if format_name=='BF16' else 'P1 A4 native CPU NumPy float32 scalar multiply/add, each raw result checked against its small-integer certificate',
        'source_program':comp.source_to_dict(program),
        'allowed_initial_state':{'values':initial.values,'pc':initial.pc},'legal_inputs_every_tick':legal_inputs,
        'scheduler':'One complete fixed DAG evaluation and same-snapshot state commit per admitted tick; all reachable PCs admit ticks, including the absorbing HALT PC. A stop-clock-on-HALT policy would be a different legal-trace contract.',
        'halt_old_state_edges':sum(state.pc in compiled.halt_pcs for state,_,_ in reach.edges),
        'finite_declared_state_universe_size':len(source_universe),'compiled_nodes':len(compiled.nodes),
        'compiled_input_dimension':compiled.input_count,'reachable_states':len(reach.states),
        'legal_edges':len(reach.edges),'complete_exploration':True,
        'reachable_state_list':[{'values':s.values,'pc':s.pc} for s in reach.states],
        'boundary_input_span':input_basis.summary(),'boundary_input_homogeneous_span':input_homogeneous.summary(),
        'intrinsic_distinct_node_rows':intrinsic_summary,'explicit_shared_row_adapter':tied_summary,
        'operand_only_distinct_node_rows':intrinsic_operand_summary,
        'operand_only_shared_row_adapter':tied_operand_summary,
        'shared_row_registry':row_metadata,'original_tick_operations':native.operations,
        'original_tick_arithmetic_checks':native.arithmetic_checks,'original_tick_state_bit_checks':native.state_bit_checks,
        'instrumented_arithmetic_checks':observed.arithmetic_checks,'canonical_zero_node_checks':zero_words_checked,
        'scope':['Every legal reachable transition of this specified finite source model is enumerated.',
                 'The unchanged original Executor.tick is run once per edge and compared bitwise with a separately instrumented adapter.',
                 'A4 stores distinct Node records; numerical row equality alone does not establish physical sharing.',
                 'The explicit adapter deliberately interns ordered coefficient-plus-bias tuples and uses that same tuple at its declared sites.',
                 'Term ordering, bias-first arithmetic, post-row activation, input wire binding and same-snapshot state semantics are unchanged.',
                 'Reported augmented row activation is (ordered term operands,1); this algebraic layout does not change bias-first execution order.',
                 'The compiler gate/intermediate checks are consumed as reference code, not newly certified for all programs.']}


def compiler_checks(comp, np):
    counter = comp.counter_program(2, 2)
    feedback = comp.Program((('x',comp.BOOL),('y',comp.BOOL)),(('u',comp.BOOL),),
        (comp.Assign((('x',comp.XOR(comp.R('x'),comp.I('u'))),('y',comp.R('x'))),0),))
    records=[]
    for fmt in ('BF16','FP32'):
        records.append(compiled_example(comp,np,'two_bit_counter_to_two',counter,comp.State((0,),0),((),),fmt))
        records.append(compiled_example(comp,np,'two_register_feedback_with_input',feedback,comp.State((0,0),0),((0,),(1,)),fmt))
    for name in ('two_bit_counter_to_two','two_register_feedback_with_input'):
        pair=[r for r in records if r['name']==name]
        check(pair[0]['intrinsic_distinct_node_rows']==pair[1]['intrinsic_distinct_node_rows'], 'BF16/FP32 per-node spaces agree')
        check(pair[0]['explicit_shared_row_adapter']==pair[1]['explicit_shared_row_adapter'], 'BF16/FP32 merged spaces agree')
        check(pair[0]['operand_only_distinct_node_rows']==pair[1]['operand_only_distinct_node_rows'], 'BF16/FP32 operand-only per-node spaces agree')
        check(pair[0]['operand_only_shared_row_adapter']==pair[1]['operand_only_shared_row_adapter'], 'BF16/FP32 operand-only merged spaces agree')
    return records



def finite_affine_fp_bridge(comp, np):
    """Finite exact Boolean toggle/hold/reset model, with an affine certificate."""
    identity=((1,0),(0,1));zero=((0,0),(0,0))
    generators=(affine_lift(identity,(0,0)),affine_lift(((-1,0),(0,-1)),(1,1)),
                affine_lift(zero,(0,0)))
    hull,certificate=invariant_linear_hull((homogeneous((0,0)),),generators,3)
    check(hull.rank==2,'Finite affine family homogeneous hull rank')
    records=[]
    for fmt in ('BF16','FP32'):
        executor=comp.Executor(fmt)
        def step(old,mode):
            source=np.array([executor.const(x) for x in old],dtype=executor.dtype)
            before=tuple(int(x) for x in executor.words(source))
            candidate=[]
            for x in source:
                if mode=='hold':value=x
                elif mode=='reset':value=executor.const(0)
                else:
                    value=executor._op('add',executor.const(1),
                        executor._op('multiply',executor.const(-1),x))
                if executor._value(value)==0:value=executor.const(0)
                check(executor.scalar_bits(value) in (executor.encoded[0],executor.encoded[1]),
                      'Finite affine bridge canonical Boolean output')
                candidate.append(value)
            next_state=tuple(executor._value(v) for v in candidate)
            exact_old=homogeneous(old)
            generator=generators[('hold','toggle','reset').index(mode)]
            check(matrix_apply(generator,exact_old)==homogeneous(next_state),
                  'FP transition equals one declared exact affine generator')
            check(hull.contains(homogeneous(next_state)),'Exact invariant contains FP next state')
            check(tuple(int(x) for x in executor.words(source))==before,'Finite affine old snapshot unchanged')
            return next_state,(Call('pair','read_old',old),Call('pair_augmented','read_old',homogeneous(old)))
        reach=enumerate_reachable(((0,0),),lambda old:('hold','toggle','reset'),step,
            universe=frozenset(itertools.product((0,1),repeat=2)),
            matrix_dimensions={'pair':2,'pair_augmented':3},
            declared_sites=(('pair','read_old'),('pair_augmented','read_old')))
        spaces=reach.spaces()
        check(len(reach.states)==2 and len(reach.edges)==6,'Finite affine reachable graph')
        check(spaces['per_matrix']['pair']['rank_Q_equals_rank_R']==1,'Finite affine operand rank')
        check(spaces['per_matrix']['pair_augmented']['rank_Q_equals_rank_R']==2,'Finite affine augmented rank')
        check(spaces['per_matrix']['pair_augmented']['basis']==hull.summary()['basis'],
              'Exact reachable homogeneous span equals invariant generator hull')
        records.append({'format':fmt,
            'arithmetic_backend':'P1 A4 small-integer software BF16 word model' if fmt=='BF16' else 'P1 A4 native CPU NumPy float32 scalar operations',
            'operations':executor.operations,'arithmetic_checks':executor.arithmetic_checks,
            'declared_state_universe':4,'reachable_states':2,'legal_edges':6,'spaces':spaces,
            'dtype':str(executor.dtype),'scope':'Every reachable edge of finite Boolean hold/toggle/reset; source preserved and FP raw words checked'})
    return {'generators':{'hold':'q','toggle':'(1,1)-q','reset':'(0,0)'},
            'initial_state':[0,0],'homogeneous_hull':hull.summary(),'certificate':certificate,
            'backends':records,
            'all_time_bridge':'The listed finite transition family is exhaustive on this declared model; induction uses the separately stated P1 storage/scheduling contracts. This is not a proof for arbitrary FP affine maps.'}


def floating_counterexamples(execution):
    records=[]
    for fmt,p in (('BF16',8),('FP32',24)):
        row=(1<<p,1,-(1<<p),-1);activation=(1,1,1,1)
        exact=sum(Fraction(a)*b for a,b in zip(row,activation))
        audit=execution.Audit();acc=execution.encode_constant(0,fmt);words=[]
        for a,b in zip(row,activation):
            product=execution.mul_words(execution.encode_constant(a,fmt),execution.encode_constant(b,fmt),fmt,audit)
            acc=execution.add_words(acc,product,fmt,audit);words.append(acc)
        value=execution.decode_word(acc,fmt)
        check(exact==0 and value==-1,'Exact zero dot is not a floating zero dot')
        if fmt=='FP32':
            check(audit.native_oracle_checks==8 and len(audit.events)==8,'Actual CPU scalar RNE checks')
            check(all(e['result_dtype']=='float32' for e in audit.events),'No dtype promotion in FP32 counterexample')
        else:
            check(audit.software_multiply==4 and audit.software_add==4,'Software BF16 operation scope')
        records.append({'format':fmt,'precision_bits':p,'row':row,'activation':activation,
            'exact_rational_dot':str(exact),'ordered_fp_result':str(value),'result_raw_hex':hex(acc),
            'accumulator_raw_hex':[hex(x) for x in words],
            'numeric_policy':'bias +0 then separate RNE products and left-to-right RNE additions, canonical arithmetic zeros',
            'audit':asdict(audit),
            'scope':'Numerical counterexample only. This row is not asserted to be an admitted D-program update; no patch is applied.'})
    return records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--p1-root',type=Path,default=ROOT.parent/'dmwk-p1-foundations')
    parser.add_argument('--output',type=Path,default=ROOT/'verification_results.json')
    args=parser.parse_args();p1=args.p1_root.resolve()
    started=time.perf_counter();times={};report={'schema':'dmwk-p2-a1-verification-v1','status':'running',
        'started_utc':datetime.now(timezone.utc).isoformat(),'seed':SEED,'stages':{}}
    comp,execution,np=load_p1(p1)
    jobs=[('rational_algebra',algebra_checks),('finite_activation_examples',finite_activation_examples),
          ('sharing_and_state_examples',sharing_and_state_examples),('delayed_direction',delayed_direction),
          ('invariant_examples',invariant_examples),('actual_compiler_examples',lambda:compiler_checks(comp,np)),
          ('finite_affine_fp_bridge',lambda:finite_affine_fp_bridge(comp,np)),
          ('floating_null_dot_counterexamples',lambda:floating_counterexamples(execution))]
    try:
        for name,job in jobs:
            before=time.perf_counter();report['stages'][name]=job();times[name]=time.perf_counter()-before
        source_paths=[Path(__file__),ROOT/'activation_spaces.py',p1/'p1_a4/compiler.py',p1/'p1_c3/execution.py',p1/'p1_b2/canonicalize.py']
        source_hashes={('p2_a1/'+p.name if p.parent==ROOT else 'p1_reference/'+str(p.relative_to(p1))):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
        report.update(status='passed',completed_utc=datetime.now(timezone.utc).isoformat(),checks=check.count,
            timings_seconds=times,total_seconds=time.perf_counter()-started,
            environment={'python':platform.python_version(),'platform':platform.platform(),'numpy':np.__version__,
                         'p1_reference_root':str(p1),'backend_metadata':execution.backend_metadata()},
            source_sha256=source_hashes,
            evidence_scope={'handwritten_proofs':'Separate Markdown statements; not machine checked by this script',
                'exhaustive_models':'Declared finite activation domains and finite reachable transition systems only',
                'SMT':'No SMT queries executed in P2-A1',
                'random_samples':'80 seeded rational matrices test the algebra implementation only',
                'BF16':'Software reference operations; no native BF16 kernel executed',
                'FP32':'Local CPU NumPy scalar operations with exact-bit checks; no BLAS/GPU/FMA certification',
                'hardware_or_system_certification':False,'P2_A2_implemented':False})
    except Exception as exc:
        report.update(status='failed',checks=check.count,total_seconds=time.perf_counter()-started,
                      failure={'type':type(exc).__name__,'message':str(exc)})
        args.output.write_text(json.dumps(report,indent=2)+'\n')
        raise
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'checks':check.count,'seconds':report['total_seconds'],
                      'output':str(args.output),'compiler_models':len(report['stages']['actual_compiler_examples']),
                      'SMT_queries':0,'P2_A2_implemented':False}))


if __name__=='__main__':
    if not __debug__:
        raise SystemExit('Verification requires ordinary Python, not -O/-OO')
    main()
