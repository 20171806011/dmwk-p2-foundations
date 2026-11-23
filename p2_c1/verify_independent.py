"""Independent C1 source, word, algebra and serial-publication references.

This verifier never imports a previous verification suite.  Its expected source
values do not call the compiler's source interpreter or lowering implementation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as Q
from functools import lru_cache
import hashlib
import importlib.util
from itertools import combinations, permutations, product
import json
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114
CHECKS = 0


def require(condition, message):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(message)


def load_current(name):
    path = ROOT / (name + ".py")
    if name in sys.modules:
        module = sys.modules[name]
        require(Path(module.__file__).resolve() == path, "Wrong current-module source: " + name)
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    require(Path(module.__file__).resolve() == path, "Wrong imported source: " + name)
    return module


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ident(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def qrecord(value):
    value = Q(value)
    return [value.numerator, value.denominator]


def power_two(exponent):
    return Q(1 << exponent) if exponent >= 0 else Q(1, 1 << -exponent)


def format_shape(fmt):
    if fmt == "BF16":
        return 7, 16
    if fmt == "FP32":
        return 23, 32
    raise ValueError("Unsupported independent format")


@lru_cache(maxsize=None)
def word_value(word, fmt):
    fraction_bits, width = format_shape(fmt)
    if type(word) is not int or not 0 <= word < (1 << width):
        raise ValueError("Not a raw built-in word")
    sign = word >> (width - 1)
    exponent = (word >> fraction_bits) & 255
    tail = word & ((1 << fraction_bits) - 1)
    if exponent == 255:
        raise ValueError("Nonfinite independent word")
    if exponent == 0:
        value = Q(tail) * power_two(-126 - fraction_bits)
    else:
        value = Q((1 << fraction_bits) + tail) * power_two(exponent - 127 - fraction_bits)
    if sign and value == 0:
        raise ValueError("Stored negative zero is not canonical")
    return -value if sign else value


@lru_cache(maxsize=None)
def round_word(value, fmt):
    """Nearest-even via ordered positive-word search, independent of producer RNE."""
    value = Q(value)
    fraction_bits, width = format_shape(fmt)
    negative = value < 0
    value = abs(value)
    maximum = (254 << fraction_bits) | ((1 << fraction_bits) - 1)
    greatest = word_value(maximum, fmt)
    overflow_midpoint = greatest + power_two(127 - fraction_bits - 1)
    if value >= overflow_midpoint:
        raise OverflowError("Independent finite-result overflow")
    if value >= greatest:
        chosen = maximum
    else:
        lo, hi = 0, maximum
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if word_value(mid, fmt) <= value:
                lo = mid
            else:
                hi = mid
        below, above = word_value(lo, fmt), word_value(hi, fmt)
        dl, dh = value - below, above - value
        chosen = lo if dl < dh or (dl == dh and lo % 2 == 0) else hi
    return chosen | ((1 << (width - 1)) if negative and chosen else 0)


def add_word(a, b, fmt):
    return round_word(word_value(a, fmt) + word_value(b, fmt), fmt)


def mul_word(a, b, fmt):
    return round_word(word_value(a, fmt) * word_value(b, fmt), fmt)


def linear_word(coefficients, values, fmt):
    result = 0
    for coefficient, value in zip(coefficients, values):
        result = add_word(result, mul_word(coefficient, value, fmt), fmt)
    return result


def source_value(expression, state, inputs):
    op = expression[0]
    if op == "const":
        return expression[1]
    if op == "state":
        return state[expression[1]]
    if op == "input":
        return inputs[expression[1]]
    args = [source_value(e, state, inputs) for e in expression[1:]]
    if op == "not":
        return int(not args[0])
    if op == "and":
        return int(all(args))
    if op == "or":
        return int(any(args))
    if op == "xor":
        return int(args[0] != args[1])
    if op == "mux":
        return args[1] if args[0] else args[2]
    raise ValueError("Unknown source operator in reference")


def source_reference(source, state, inputs):
    # No partially computed next value is passed to another expression.
    old = tuple(state)
    return (tuple(source_value(e, old, inputs) for e in source["next_state"]),
            tuple(source_value(e, old, inputs) for e in source["outputs"]))


def gate_cost(expression):
    op = expression[0]
    if op in ("const", "state", "input"):
        return 0
    return {"not": 1, "and": 1, "or": 4, "xor": 7, "mux": 7}[op] + sum(
        gate_cost(child) for child in expression[1:])


def program(next_expressions, output_expressions=None, input_count=1, initials=None):
    state_count = len(next_expressions)
    return {"schema": "dmwk-p2-c1-bool-fsm-v1",
            "state_ports": ["s" + str(i) for i in range(state_count)],
            "input_ports": ["u" + str(i) for i in range(input_count)],
            "output_ports": ["o" + str(i) for i in range(len(output_expressions or [["state", 0]]))],
            "initial_states": [list(x) for x in (initials if initials is not None else product((0, 1), repeat=state_count))],
            "next_state": deepcopy(next_expressions),
            "outputs": deepcopy(output_expressions or [["state", 0]])}


def one_operator_family():
    atoms = [["const", 0], ["const", 1], ["state", 0], ["input", 0]]
    result = deepcopy(atoms)
    result += [["not", deepcopy(a)] for a in atoms]
    result += [[op, deepcopy(a), deepcopy(b)] for op, a, b in product(("and", "or", "xor"), atoms, atoms)]
    result += [["mux", deepcopy(a), deepcopy(b), deepcopy(c)] for a, b, c in product(atoms, repeat=3)]
    return result


def determinant(matrix):
    n = len(matrix)
    if n == 0:
        return Q(1)
    result = Q(0)
    for order in permutations(range(n)):
        inversions = sum(order[i] > order[j] for i in range(n) for j in range(i + 1, n))
        term = Q(-1 if inversions % 2 else 1)
        for i, j in enumerate(order):
            term *= matrix[i][j]
        result += term
    return result


def rank_by_minors(matrix):
    if not matrix:
        return 0
    rows, columns = len(matrix), len(matrix[0])
    for size in range(min(rows, columns), 0, -1):
        for rr in combinations(range(rows), size):
            for cc in combinations(range(columns), size):
                if determinant(tuple(tuple(Q(matrix[i][j]) for j in cc) for i in rr)):
                    return size
    return 0


def decoded_words(words, fmt):
    return tuple(tuple(word_value(w, fmt) for w in row) for row in words)


def subtract(a, b):
    return tuple(tuple(x - y for x, y in zip(ar, br)) for ar, br in zip(a, b))


def expect_refusal(action, label, records):
    try:
        action()
    except (ValueError, TypeError, OverflowError) as exc:
        records.append({"case": label, "type": type(exc).__name__, "reason": str(exc)})
        require(True, "Expected refusal")
        return
    raise AssertionError("Accepted an expected refusal: " + label)


def check_frozen_b1():
    path = ROOT.parent / "p2_b1" / "training_results.json"
    value = json.loads(path.read_text())
    require(value["status"] == "passed", "Frozen B1 evidence status changed")
    rejected = [entry for run in value["runs"] for entry in run["records"] if entry["status"] == "refused"]
    require(len(rejected) == 21 and value["refused_candidates_passing_registered_BIT_diagnostic"] == 21,
            "Frozen B1 refusal count lost")
    require(all(e["proposed_ALG_annihilation"] is False and
                e["proposed_complete_D"]["all_protected_observations_equal"] is True for e in rejected),
            "B1 refusals relabeled as observed BIT drift")
    dense = [run for run in value["runs"] if run["format"] == "FP32" and run["optimizer"] == "adamw" and
             run["route"] == "final_update_projected_certified"]
    require(len(dense) == 1, "Frozen dense AdamW route ambiguous")
    run = dense[0]
    require(run["accepted_commits"] == 0 and run["refused_attempts"] == 8 and
            run["initial_loss"] == run["final_loss"] == "5/2", "Frozen AdamW failure lost")
    return {"source_sha256": digest(path), "saved_rejections": 21,
            "all_saved_rejections_BIT_equal_ALG_false": True,
            "dense_FP32_AdamW_accepted": 0, "dense_FP32_AdamW_refused": 8,
            "dense_FP32_AdamW_initial_final_loss": "5/2",
            "scope": "Read-only inspection of saved evidence; no prior optimizer or verifier execution"}


def random_expression(rng, states, inputs, depth):
    leaves = [["const", 0], ["const", 1]] + [["state", i] for i in range(states)] + [["input", i] for i in range(inputs)]
    if depth == 0 or rng.random() < Q(1, 3):
        return deepcopy(rng.choice(leaves))
    op = rng.choice(("not", "and", "or", "xor", "mux"))
    arity = {"not": 1, "and": 2, "or": 2, "xor": 2, "mux": 3}[op]
    return [op] + [random_expression(rng, states, inputs, depth - 1) for _ in range(arity)]


def check_compile_refusals(cc):
    records = []
    source = program([["xor", ["state", 0], ["input", 0]]])
    base = cc.default_budget(2, 2)
    for fmt in ("BF16", "FP32"):
        cases = []
        def changed(label, fn):
            value = deepcopy(source); fn(value); cases.append((label, value))
        changed("missing_source_expression", lambda p: p["next_state"].clear())
        changed("port_alias", lambda p: p["input_ports"].__setitem__(0, "s0"))
        changed("unknown_external_effect", lambda p: p.__setitem__("external_calls", []))
        changed("wrong_schema", lambda p: p.__setitem__("schema", "arbitrary-host-program"))
        changed("host_bool_constant", lambda p: p["next_state"].__setitem__(0, ["const", True]))
        changed("host_float_constant", lambda p: p["next_state"].__setitem__(0, ["const", 1.0]))
        changed("nonboolean_constant", lambda p: p["next_state"].__setitem__(0, ["const", 2]))
        changed("out_of_range_state", lambda p: p["next_state"].__setitem__(0, ["state", 1]))
        changed("A_to_D_read", lambda p: p["next_state"].__setitem__(0, ["A", 0]))
        changed("hard_float_guard", lambda p: p["next_state"].__setitem__(0, ["threshold", ["input", 0], 0]))
        changed("no_initial_state", lambda p: p.__setitem__("initial_states", []))
        changed("bad_initial_bit", lambda p: p.__setitem__("initial_states", [[2]]))
        changed("cyclic_expression", lambda p: p["next_state"].__setitem__(0, ["not"]))
        cases[-1][1]["next_state"][0].append(cases[-1][1]["next_state"][0])
        for label, value in cases:
            expect_refusal(lambda value=value: cc.compile_program(value, base, fmt), fmt + ":" + label, records)
        for key, value in (("d_row_budget", 1), ("d_col_budget", 2), ("parameter_budget", 19),
                           ("call_budget", 6), ("min_A_response_dimension", 5), ("required_update_rank", 3),
                           ("a_rows", 0), ("a_cols", 3), ("call_budget", True), ("parameter_budget", -1)):
            budget = deepcopy(base); budget[key] = value
            expect_refusal(lambda budget=budget: cc.compile_program(source, budget, fmt),
                           fmt + ":budget_" + key + "_" + str(value), records)
        extra_budget = deepcopy(base); extra_budget["allow_FMA"] = True
        expect_refusal(lambda: cc.compile_program(source, extra_budget, fmt), fmt + ":unbound_policy_budget", records)
        for mode in ("geometric", "rotated", "dense_optimized"):
            expect_refusal(lambda mode=mode: cc.compile_program(source, base, fmt, mode=mode),
                           fmt + ":unsupported_mode_" + mode, records)
        requests = (
            ("zero_to_nonzero", {"inputs": [[0, 0]], "outputs": [[[1, 1], [0, 1]]]}),
            ("duplicate_conflicting_anchor", {"inputs": [[1, 0], [1, 0]], "outputs": [[[0, 1], [0, 1]], [[1, 1], [0, 1]]]}),
            ("exact_third_not_storable", {"inputs": [[1, 0]], "outputs": [[[1, 3], [0, 1]]]}),
            ("noncanonical_fraction", {"inputs": [[1, 0]], "outputs": [[[2, 4], [0, 1]]]}),
            ("unproved_dense_A_domain", {"inputs": [[1, 1]], "outputs": [[[1, 1], [0, 1]]]}),
        )
        for label, request in requests:
            expect_refusal(lambda request=request: cc.compile_program(source, base, fmt, response_request=request),
                           fmt + ":" + label, records)
    expect_refusal(lambda: cc.compile_program(source, base, "TF32"), "unsupported_internal_precision", records)
    return {"expected_refusals": records, "scope": "Specific malformed sources, unsupported modes and infeasible construction/anchor requests"}


def wire_value(wire, states, inputs, selected, fmt):
    kind, index = wire
    if kind == "const":
        require(index in (0, 1), "Graph constant is nonboolean")
        return round_word(index, fmt)
    if kind == "state":
        require(0 <= index < len(states), "State wire index invalid")
        return states[index]
    if kind == "input":
        require(0 <= index < len(inputs), "Input wire index invalid")
        return inputs[index]
    require(kind == "gate" and 0 <= index < len(selected), "Graph depends on a future or unknown wire")
    return selected[index]


def inspect_execution(cc, artifact, words, state, inputs, fmt):
    old = tuple(round_word(x, fmt) for x in state)
    incoming = tuple(round_word(x, fmt) for x in inputs)
    actual = cc.execute_d(artifact, words, old, incoming)
    expected_next, expected_output = source_reference(artifact["source"], state, inputs)
    require(tuple(actual["next_state_words"]) == tuple(round_word(x, fmt) for x in expected_next),
            "Compiled successor differs from independent source interpretation")
    require(tuple(actual["output_words"]) == tuple(round_word(x, fmt) for x in expected_output),
            "Compiled observation differs from old-state source interpretation")
    require(actual["same_old_snapshot"] is True, "No old-snapshot guarantee recorded")
    calls = artifact["graph"]["D_calls"]
    require(len(actual["site_traces"]) == len(calls), "Emitted call omitted from actual trace")
    selected, activations = [], []
    for k, (call, trace) in enumerate(zip(calls, actual["site_traces"])):
        require(call["id"] == "d_gate_" + format(k, "04d") and trace["id"] == call["id"],
                "Gate identity/order changed")
        require(call["bank_id"] == "shared_weights" and call["rows"] == [0, 1] and call["columns"] == [0, 1, 2],
                "A shared call or sparse deterministic frame changed")
        require(call["bias_words"] == [0, 0] and call["activation"] == "coordinate_relu", "Gate bias or activation changed")
        a, b = (wire_value(wire, old, incoming, selected, fmt) for wire in call["args"])
        require(call["op"] in ("and", "not") and (call["op"] != "not" or b == 0), "Primitive type/preparation invalid")
        physical = (a, b, round_word(1, fmt)) + (0,) * artifact["layout"]["a_cols"]
        pre = tuple(linear_word(row[:3], physical[:3], fmt) for row in words[:2])
        post = tuple(0 if word_value(x, fmt) < 0 else x for x in pre)
        row = 0 if call["op"] == "and" else 1
        require(tuple(trace["argument_words"]) == (a, b) and tuple(trace["physical_activation_words"]) == physical,
                "Actual preparation differs from independent wire evaluation")
        require(tuple(trace["preactivation_words"]) == pre and tuple(trace["D_output_words"]) == post,
                "Fixed gate's actual ordered arithmetic differs from independent RNE")
        require(call["selected_row"] == trace["selected_row"] == row and trace["result_word"] == post[row],
                "Wrong gate row selection")
        require(all(x in (0, round_word(1, fmt)) for x in post), "Gate lost canonical Boolean closure")
        selected.append(post[row])
        activations.append(tuple(int(word_value(x, fmt)) for x in physical))
    next_by_wires = tuple(wire_value(w, old, incoming, selected, fmt) for w in artifact["graph"]["next_state_wires"])
    out_by_wires = tuple(wire_value(w, old, incoming, selected, fmt) for w in artifact["graph"]["output_wires"])
    require(next_by_wires == tuple(actual["next_state_words"]) and out_by_wires == tuple(actual["output_words"]),
            "Graph port selection differs from its recorded call values")
    counts = actual["arithmetic_counts"]
    mode = "software" if fmt == "BF16" else "native"
    other = "native" if fmt == "BF16" else "software"
    require(counts[mode + "_multiply"] == counts[mode + "_add"] == 6 * len(calls), "Gate arithmetic count/order mismatch")
    require(counts[other + "_multiply"] == counts[other + "_add"] == 0, "Wrong actual backend arithmetic type")
    require(counts["exact_sums"] == 0, "An exact accumulator replaced the specified graph")
    if fmt == "FP32":
        require(counts["native_oracle_checks"] == 12 * len(calls), "Native operations lack the recorded exact audit")
    return actual, activations


def inspect_program(cc, source, fmt, p=2, c=2, response_request=None, label=None):
    budget = cc.default_budget(p, c)
    artifact = cc.compile_program(source, budget, fmt, response_request=response_request)
    cc.check_artifact(artifact, source, budget, fmt, response_request=response_request)
    require(artifact["source"] == source and artifact["source_sha256"] == ident(source), "Source identity changed")
    require(artifact["graph_sha256"] == ident(artifact["graph"]), "Graph identity does not bind its full value")
    require(artifact["layout"]["full_shape"] == [2 + p, 3 + c], "Compiled shape exceeds the stated construction")
    expected_cells = {(i, j) for i in range(2, 2 + p) for j in range(3, 3 + c)}
    require(set(map(tuple, artifact["layout"]["writable_cells"])) == expected_cells, "Wrong editable region")
    words = cc.initial_weights(artifact)
    coefficients = ((1, 1, -1), (-1, 0, 1))
    for i, row in enumerate(words):
        for j, value in enumerate(row):
            word_value(value, fmt)
            if (i, j) not in expected_cells:
                expected = coefficients[i][j] if i < 2 and j < 3 else 0
                require(value == round_word(expected, fmt), "Compiled immutable/cross-region coefficient differs")
    expected_gates = sum(gate_cost(e) for e in source["next_state"] + source["outputs"])
    require(len(artifact["graph"]["D_calls"]) == expected_gates, "Macro/source call completeness cost mismatch")
    cost, capacity = artifact["cost"], artifact["capacity"]
    require(cost["dense_matrix_word_slots"] == (2 + p) * (3 + c) and cost["editable_word_slots"] == p * c,
            "Dense and editable capacity receipts mixed")
    require(cost["primitive_D_calls_per_tick"] == expected_gates and
            cost["D_binary_float_operations_per_tick"] == 12 * expected_gates and
            cost["D_relu_word_operations_per_tick"] == 2 * expected_gates,
            "Source complexity disappeared from compiler cost")
    require(cost["A_binary_float_operations_per_call"] == 2 * p * c and cost["physical_shared_banks"] == 1,
            "A or sharing cost receipt wrong")
    require(capacity["protected_containing_rank"] == 3 and capacity["structural_update_dimension"] == p * c and
            capacity["full_output_annihilator_dimension"] == (2 + p) * c and
            capacity["maximum_structural_update_rank"] == min(p, c) and
            capacity["A_full_basis_response_dimension"] == p * c, "Capacity objects conflated")
    alphabet = 2 * 255 * (1 << format_shape(fmt)[0]) - 1
    require(capacity["canonical_word_alphabet_size"] == alphabet and
            int(capacity["structural_endpoint_count_decimal"]) == alphabet ** (p * c) and
            int(capacity["full_basis_stored_response_signature_count_decimal"]) == alphabet ** (p * c),
            "Finite structural alphabet cardinality wrong")
    contexts = 0
    site_sets = [set() for _ in range(expected_gates)]
    all_activations = set()
    results = []
    for state in product((0, 1), repeat=len(source["state_ports"])):
        for inputs in product((0, 1), repeat=len(source["input_ports"])):
            actual, activations = inspect_execution(cc, artifact, words, state, inputs, fmt)
            for k, h in enumerate(activations):
                site_sets[k].add(h); all_activations.add(h)
            contexts += 1
            results.append({"state": list(state), "input": list(inputs), "next": list(actual["next_state_words"]),
                            "output": list(actual["output_words"]), "site_trace_sha256": ident(actual["site_traces"])})
    coverage = artifact["proof"]["coverage"]
    require(coverage["state_input_contexts"] == contexts and coverage["D_call_observations"] == contexts * expected_gates,
            "Coverage record omits legal state/input/site combinations")
    require(coverage["samples_used"] is False and coverage["all_shared_D_sites_covered"] is True and
            coverage["exact_reachable_span_claimed"] is False, "Envelope mislabeled as sampling/reachable exactness")
    require(coverage["all_state_activation_bits"] == [list(h) for h in sorted(all_activations)], "Global activation union omitted a site")
    for k, row in enumerate(coverage["per_site"]):
        require(row["id"] == artifact["graph"]["D_calls"][k]["id"] and
                row["activation_bits"] == [list(h) for h in sorted(site_sets[k])], "Per-site activation set differs")
    rank = rank_by_minors(tuple(tuple(h[i] for h in sorted(all_activations)) for i in range(3))) if all_activations else 0
    require(coverage["all_state_call_span_rank"] == capacity["all_state_call_span_rank"] == rank,
            "Envelope rank differs from independent minors")
    expected_A_bits = [(0,) * c] + [tuple(int(i == j) for i in range(c)) for j in range(c)]
    require(len(artifact["graph"]["A_calls"]) == c + 1, "A legal call domain incomplete")
    for bits, call in zip(expected_A_bits, artifact["graph"]["A_calls"]):
        require(tuple(call["input_bits"]) == bits and call["columns"] == list(range(3, 3 + c)) and
                call["rows"] == list(range(2, 2 + p)) and call["activation"] == "identity" and
                tuple(call["physical_activation_bits"]) == (0, 0, 0) + bits, "A call crosses into D coordinates")
        actual = cc.evaluate_a(artifact, words, tuple(round_word(x, fmt) for x in bits))
        expected = tuple(linear_word(row[3:], tuple(round_word(x, fmt) for x in bits), fmt) for row in words[2:])
        require(tuple(actual["output_words"]) == expected, "A interface differs from exact word reference")
    return {"label": label, "format": fmt, "source_sha256": ident(source), "source": source,
            "artifact_sha256": ident(artifact), "contexts": contexts, "primitive_calls": expected_gates,
            "complete_site_observations": contexts * expected_gates, "envelope_rank": rank,
            "reserved_rank": 3, "structural_dimension": p * c, "dense_words": (2 + p) * (3 + c),
            "D_results_sha256": ident(results)}, artifact


def check_sources(cc):
    records = []
    family = one_operator_family()
    require(len(family) == 120 and len({canonical(e) for e in family}) == 120, "Named expression family incomplete")
    for fmt in ("BF16", "FP32"):
        for index, expr in enumerate(family):
            row, _ = inspect_program(cc, program([expr]), fmt, label="complete_one_operator_" + str(index))
            records.append(row)
    extra, rng = [], random.Random(SEED)
    named = [
        ("simultaneous_swap", program([["state", 1], ["state", 0]], [["state", 0], ["state", 1]], 0)),
        ("explicit_reset_hold", program([["mux", ["input", 0], ["const", 0], ["xor", ["state", 0], ["input", 1]]]], input_count=2)),
        ("proper_initial_subset", program([["const", 0]], [["not", ["state", 0]]], 0, [(0,)])),
    ]
    for fmt in ("BF16", "FP32"):
        for label, source in named:
            row, _ = inspect_program(cc, source, fmt, label=label)
            if label == "proper_initial_subset":
                require(row["envelope_rank"] == 2, "All-state envelope was replaced by initial-state sampling")
                row["reachable_rank_of_this_simple_source"] = 1
            extra.append(row)
        for index in range(12):
            source = program([random_expression(rng, 2, 2, 3) for _ in range(2)],
                             [random_expression(rng, 2, 2, 2) for _ in range(2)], 2)
            row, _ = inspect_program(cc, source, fmt, label="seeded_program_" + str(index))
            extra.append(row)
    return {"complete_program_format_pairs": len(records), "complete_state_input_cases": sum(r["contexts"] for r in records),
            "complete_site_observations": sum(r["complete_site_observations"] for r in records),
            "additional_named_and_seeded_program_format_pairs": len(extra),
            "additional_state_input_cases": sum(r["contexts"] for r in extra), "seed": SEED,
            "records": records, "additional_records": extra,
            "scope": "All120 specified one-operator expressions, all Boolean state/input pairs; separate named/seeded deeper sources, not all admitted programs"}


def check_owner(cc, co):
    records, refusals = [], []
    rng = random.Random(SEED + 1)
    for fmt in ("BF16", "FP32"):
        source = program([["xor", ["state", 0], ["input", 0]]])
        budget = cc.default_budget(2, 1)
        opt = co.cu.OptimizerConfig("momentum", Q(1, 4), momentum=Q(1, 2))
        owner = co.CompiledOwner(source, budget, fmt, opt, max_updates=10)
        state = (0,)
        theta, moment = [Q(0), Q(0)], [Q(0), Q(0)]
        target = (Q(1), Q(-1))
        initial_loss = Q(*owner.evaluate_a()["loss"])
        require(initial_loss == 1, "Unexpected initial toy loss")
        full_checks = 0
        for k in range(10):
            before = owner.snapshot()
            grad = [x - y for x, y in zip(theta, target)]
            moments = [(m + g) / 2 for m, g in zip(moment, grad)]
            new_words = [round_word(x - m / 4, fmt) for x, m in zip(theta, moments)]
            moment = moments
            theta = [word_value(w, fmt) for w in new_words]
            req = co.optimizer_request(owner.toy_gradient())
            prepared = owner.prepare(req)
            require(before == owner.snapshot(), "Prepare mutated the owner")
            receipt = owner.commit(prepared)
            require(receipt["accepted"] and receipt["effective_rank"] == int(new_words != [r[3] for r in before["weights"][2:]]),
                    "Effective update rank mismatch")
            require([row[3] for row in owner.weights[2:]] == new_words, "Independent recurrent optimizer endpoint mismatch")
            require(owner.evaluate_a()["loss"] == qrecord(sum((x-y)**2 for x, y in zip(theta,target))/2),
                    "Independent A response loss mismatch")
            for q, u in product((0,1),repeat=2):
                record = cc.execute_d(owner.artifact, owner.weights, (round_word(q,fmt),), (round_word(u,fmt),))
                expected = source_reference(source,(q,),(u,))
                require(tuple(record["next_state_words"]) == tuple(round_word(i,fmt) for i in expected[0])
                        and tuple(record["output_words"]) == tuple(round_word(i,fmt) for i in expected[1]),
                        "Accepted patch changed a legal Boolean context")
                full_checks += 1
            u = (rng.randrange(2),)
            state, out = source_reference(source,state,u)
            tick = owner.tick(tuple(round_word(x,fmt) for x in u))
            require(tuple(owner.state_words) == tuple(round_word(x,fmt) for x in state)
                    and tuple(tick["trace"]["output_words"]) == tuple(round_word(x,fmt) for x in out),
                    "Accepted-patch feedback history diverged")
            live = owner.snapshot()
            require(live["optimizer_state"]["step"] == live["ticks"] == live["weight_version"] == k+1,
                    "Optimizer/endpoint/tick counters disagree")
            require([r[3] for r in live["optimizer_state"]["m"]["rows"][2:]] == [qrecord(m) for m in moment],
                    "Committed moments differ from independent recurrence")
            if k == 0:
                next_prepared = owner.prepare(req)
                for key in ("source_sha256","graph_sha256","schedule","claim","new_weight_version",
                            "unchanged_D_state_words","new_optimizer_state","new_accepted_event","old_snapshot"):
                    packet = json.loads(next_prepared)
                    packet["payload"][key] = None
                    packet["payload_sha256"] = ident(packet["payload"])
                    expect_refusal(lambda: owner.commit(canonical(packet)),fmt+":rehashed_"+key,refusals)
                    require(owner.snapshot() == live, "Rehashed mutation partially published data")
                expect_refusal(lambda: owner.commit(prepared),fmt+":replay_of_accepted_candidate",refusals)
                require(owner.snapshot() == live,"Replay damaged owner")
        live = owner.snapshot()
        expect_refusal(lambda: owner.prepare(req),fmt+":late_full_history_limit",refusals)
        require(owner.snapshot() == live, "Late history limit damaged nonzero optimizer moments")
        changed = deepcopy(live["weights"]); changed[0][-1] = round_word(1,fmt)
        expect_refusal(lambda: owner.prepare(co.endpoint_request(changed)),fmt+":cross_block_edit",refusals)
        require(owner.snapshot() == live, "Cross-block refusal mutated owner")
        expect_refusal(lambda: owner.commit(canonical({"payload":{"schema":"read_only_numerical"},"payload_sha256":"0"})),
                       fmt+":read_only_evidence_as_commit",refusals)
        require(owner.snapshot() == live, "Read-only receipt mutated owner")
        records.append({"format":fmt,"accepted":10,"paired_ticks":10,"all_context_checks_after_commits":full_checks,
                        "initial_loss":str(initial_loss),"final_loss":str(Q(*owner.evaluate_a()["loss"])),
                        "final_A":list(map(str,theta)), "final_paired_state":list(state)})
    return {"runs":records,"expected_refusals":refusals,"scope":"Ten momentum updates per format, four D contexts per update"}


def check_numeric(cc):
    rows, refusals = [], []
    for fmt in ("BF16","FP32"):
        width, _ = format_shape(fmt)
        F = Q(2)**(width+1)
        one = round_word(1,fmt)
        h = (one,one,one)
        require(sum((F,Q(1),-F)) == 1 and linear_word(tuple(round_word(x,fmt) for x in (F,1,-F)),h,fmt) == 0,
                "Exact constant-dot preservation failed to expose rounding drift")
        eta = word_value(1,fmt)
        for a,b in product((0,1),repeat=2):
            binput = tuple(round_word(x,fmt) for x in (a,b,1))
            w = linear_word((round_word(-1,fmt),1,one),binput,fmt)
            require(word_value(w,fmt) == 1-a,"Subnormal edit changed declared Boolean output")
        maximum_word = 255*(1<<width)-1
        high = word_value(maximum_word,fmt)
        source = program([["and",["const",1],["const",1]]])
        budget = cc.default_budget(1,2)
        request = {"inputs":[[1,0],[0,1]],"outputs":[[qrecord(-high)],[qrecord(eta)]]}
        artifact = cc.compile_program(source,budget,fmt,response_request=request)
        bank = cc.initial_weights(artifact)
        probes = [((0,0),0),((one,0),round_word(-high,fmt)),((0,one),1)]
        for z, expected in probes:
            out = cc.evaluate_a(artifact,bank,z)["output_words"]
            require(tuple(out) == (expected,), "Extreme representable A anchor failed")
        for label, column in (("ALG_but_changed_word",[round_word(F,fmt),one,round_word(-F,fmt)]),
                              ("BIT_but_fails_mask", [round_word(-1,fmt),1,one])):
            changed = [list(row) for row in bank]
            changed[int(label.startswith("BIT"))][:3] = column
            expect_refusal(lambda: cc.validate_endpoint(artifact,changed),fmt+":"+label,refusals)
        rows.append({"format":fmt,"F":str(F),"eta":str(eta),"ALG_case_exact_output":"1",
                     "changed_rounded_output":"0","BIT_case_checked_contexts":4,"extreme_A_word_probes":len(probes)})
    return {"cases":rows,"expected_refusals":refusals}


def main():
    global CHECKS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"independent_results.json")
    args = parser.parse_args()
    start = time.perf_counter()
    CHECKS = 0
    sources = ("verify_independent.py","c1_compiler.py","c1_runtime.py","compiled_owner.py")
    result = {"schema":"dmwk-p2-c1-independent-v1","seed":SEED,"started_utc":datetime.now(timezone.utc).isoformat(),
              "status":"running","sections":{},"section_seconds":{},"source_sha256":{n:digest(ROOT/n) for n in sources},
              "old_suites_rerun":False,"SMT_queries":0,"general_proofs_machine_checked":False,"P2_C2_started":False}
    phase = "load"
    try:
        require(__debug__, "Independent verification requires standard interpreter mode")
        cc = load_current("c1_compiler")
        co = load_current("compiled_owner")
        rt = load_current("c1_runtime")
        result["environment"] = rt.environment_metadata()
        for phase, task in (("programs",lambda:check_sources(cc)),("compile_refusals",lambda:check_compile_refusals(cc)),
                            ("owner",lambda:check_owner(cc,co)),("numerics",lambda:check_numeric(cc)),("frozen_B1",check_frozen_b1)):
            t0, initial = time.perf_counter(), CHECKS
            value = task()
            value["checks"] = CHECKS-initial
            result["sections"][phase] = value
            result["section_seconds"][phase] = time.perf_counter()-t0
        phase = "postflight"
        require(result["source_sha256"] == {n:digest(ROOT/n) for n in sources},"Independent source bindings changed during run")
        result["status"] = "passed"
    except Exception as exc:
        result.update(status="failed",failure={"phase":phase,"type":type(exc).__name__,"message":str(exc)})
    result["checks"] = CHECKS
    result["unexpected_failures"] = int(result["status"] != "passed")
    result["expected_refusals"] = sum(len(v.get("expected_refusals",[])) for v in result["sections"].values())
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    result["total_seconds"] = time.perf_counter()-start
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:result.get(k) for k in ("status","checks","expected_refusals","total_seconds","failure")}))
    return result["unexpected_failures"]


if __name__ == "__main__":
    raise SystemExit(main())
