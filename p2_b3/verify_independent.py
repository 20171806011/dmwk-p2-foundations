"""Independent finite B3 review: word RNE, direct sums, and paired trajectories.

No producer test modules or earlier verification suites are imported. Exact
references in this file are separate from the implementation under review.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from fractions import Fraction as Q
from functools import lru_cache
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def precision(fmt):
    return {"BF16": 8, "FP32": 24}[fmt]


@lru_cache(maxsize=None)
def word_value(raw, fmt):
    p = precision(fmt)
    f = p - 1
    require(type(raw) is int and 0 <= raw < 1 << (p + 8), "Reference word range")
    require(raw != 1 << (p + 7), "Reference rejects stored negative zero")
    sign = -1 if raw >> (p + 7) else 1
    exponent = (raw >> f) & 255
    mantissa = raw & ((1 << f) - 1)
    require(exponent != 255, "Reference rejects nonfinite word")
    if exponent:
        mantissa += 1 << f
        power = exponent - 127 - f
    else:
        power = 1 - 127 - f
    return sign * Q(mantissa) * Q(2) ** power


def constants(fmt):
    p = precision(fmt)
    maxword = (254 << (p - 1)) | ((1 << (p - 1)) - 1)
    return Q(1, 1 << p), word_value(1, fmt), word_value(maxword, fmt), maxword


@lru_cache(maxsize=None)
def round_word(value, fmt):
    value = Q(value)
    if not value:
        return 0
    p = precision(fmt)
    sign = (1 << (p + 7)) if value < 0 else 0
    value = abs(value)
    _, _, maximum, upper = constants(fmt)
    gap = maximum - word_value(upper - 1, fmt)
    if value >= maximum + gap / 2:
        raise OverflowError("Reference rounded nonfinite result")
    if value >= maximum:
        return sign | upper
    lower = 0
    while lower + 1 < upper:
        middle = (lower + upper) // 2
        if word_value(middle, fmt) <= value:
            lower = middle
        else:
            upper = middle
    dl = value - word_value(lower, fmt)
    du = word_value(upper, fmt) - value
    chosen = lower if dl < du or (dl == du and lower % 2 == 0) else upper
    return sign | chosen if chosen else 0


def encode_rows(rows, fmt):
    return tuple(tuple(round_word(Q(v), fmt) for v in row) for row in rows)


def infnorm(values):
    return max(map(abs, values), default=Q(0))


def affine_reference(weights, biases, inputs, fmt, activation="identity"):
    """Separate target-format multiply/add; exact local residual attribution."""
    require(activation in ("identity", "relu"), "Reference activation")
    xs = tuple(word_value(x, fmt) for x in inputs)
    outputs, ideals, errors, traces = [], [], [], []
    for row, bias in zip(weights, biases):
        require(len(row) == len(inputs), "Reference affine shape")
        accumulator = bias
        ideal = word_value(bias, fmt) + sum((word_value(w, fmt) * x for w, x in zip(row, xs)), Q(0))
        events = []
        for j, (weight, x) in enumerate(zip(row, xs)):
            multiply_arg = word_value(weight, fmt) * x
            multiplied = round_word(multiply_arg, fmt)
            addition_arg = word_value(accumulator, fmt) + word_value(multiplied, fmt)
            accumulated = round_word(addition_arg, fmt)
            events.append((j, multiply_arg, multiplied, addition_arg, accumulated))
            accumulator = accumulated
        rounded_affine = word_value(accumulator, fmt)
        output = accumulator if activation == "identity" or rounded_affine >= 0 else 0
        exact_activated = ideal if activation == "identity" else max(ideal, Q(0))
        outputs.append(output)
        ideals.append(exact_activated)
        errors.append(word_value(output, fmt) - exact_activated)
        traces.append(events)
    return {"words": tuple(outputs), "exact": tuple(ideals), "error": tuple(errors), "events": traces}


def exact_product_sum(lipschitz, forcing, initial):
    require(len(lipschitz) == len(forcing), "Reference recurrence shape")
    product_all = Q(1)
    for coefficient in lipschitz:
        product_all *= coefficient
    total = Q(initial) * product_all
    for j, term in enumerate(forcing):
        suffix = Q(1)
        for coefficient in lipschitz[j + 1:]:
            suffix *= coefficient
        total += term * suffix
    return total


def decode_record(value):
    if isinstance(value, list) and len(value) == 2 and all(type(x) is int for x in value):
        return Q(*value)
    return value


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def interval_endpoint_reference(bank, radius, fmt):
    """Independent symbolic proof recurrence, using decoded exact coefficients."""
    unit, eta, maximum, _ = constants(fmt)
    row_errors, outputs = [], []
    for row, bias in zip(bank["weights"], bank["bias"]):
        accumulator = abs(word_value(bias, fmt))
        error = Q(0)
        for weight, bound in zip(row, radius):
            product_magnitude = abs(word_value(weight, fmt)) * bound
            if product_magnitude > maximum:
                raise OverflowError("Reference cannot prove product totality")
            product_error = unit * product_magnitude + eta / 2
            rounded_product_magnitude = min(maximum, product_magnitude + product_error)
            addition_magnitude = accumulator + rounded_product_magnitude
            if addition_magnitude > maximum:
                raise OverflowError("Reference cannot prove addition totality")
            addition_error = unit * addition_magnitude + eta / 2
            accumulator = min(maximum, addition_magnitude + addition_error)
            error += product_error + addition_error
        outputs.append(accumulator)
        row_errors.append(error)
    return tuple(outputs), tuple(row_errors)


def ordered_interval_reference(bank, bounds, fmt, activation):
    """Tighter monotone RNE interval extension, independent of mixed-error budget."""
    results = []
    for row, bias in zip(bank["weights"], bank["bias"]):
        lo = hi = word_value(bias, fmt)
        for weight, radius in zip(row, bounds):
            edge = abs(word_value(weight, fmt)) * radius
            p_lo = word_value(round_word(-edge, fmt), fmt)
            p_hi = word_value(round_word(edge, fmt), fmt)
            lo = word_value(round_word(lo + p_lo, fmt), fmt)
            hi = word_value(round_word(hi + p_hi, fmt), fmt)
        if activation == "relu":
            lo, hi = max(Q(0), lo), max(Q(0), hi)
        results.append((lo, hi))
    return tuple(results)


def signed_enclosure_reference(bank, radius, fmt, activation):
    magnitude, errors = interval_endpoint_reference(bank, radius, fmt)
    outputs = []
    for row, bias, mag, error in zip(bank["weights"], bank["bias"], magnitude, errors):
        center = word_value(bias, fmt)
        extent = sum((abs(word_value(w, fmt)) * r for w, r in zip(row, radius)), Q(0))
        lo, hi = max(-mag, center - extent - error), min(mag, center + extent + error)
        if activation == "relu":
            lo, hi = max(Q(0), lo), max(Q(0), hi)
        outputs.append(max(abs(lo), abs(hi)))
    return tuple(outputs)


def graph_reference(graph, banks, inputs, fmt):
    current = tuple(inputs)
    calls = []
    for site in graph:
        bank = banks[site["bank_id"]]
        result = affine_reference(bank["weights"], bank["bias"], current, fmt, site["activation"])
        calls.append(result)
        current = result["words"]
    return current, calls


def model_reference(pb, model, banks, initial, inputs, fmt):
    descriptor = pb.model_descriptor(model, fmt)
    graph = descriptor["graph"]
    if model in ("two_layer_relu_v1", "shared_relu_v1"):
        return (graph_reference(graph, banks, inputs[0], fmt)[0],)
    states = [tuple(initial)]
    for u in inputs:
        next_state, _ = graph_reference(graph, banks, states[-1] + tuple(u), fmt)
        states.append(next_state)
    return tuple(states)


def exact_graph_reference(graph, banks, inputs, fmt):
    current = tuple(Q(v) for v in inputs)
    for site in graph:
        bank = banks[site["bank_id"]]
        current = tuple(word_value(bias, fmt) + sum((word_value(w, fmt) * x for w, x in zip(row, current)), Q(0))
                        for row, bias in zip(bank["weights"], bank["bias"]))
        if site["activation"] == "relu":
            current = tuple(max(Q(0), x) for x in current)
    return current


def make_bank(weights, fmt, bias=None):
    rows = encode_rows(weights, fmt)
    return {"weights": rows,
            "bias": tuple(round_word(Q(x), fmt) for x in (bias if bias is not None else (0,) * len(rows)))}


def check_recurrences(pb):
    exhaustive = 0
    zeros = (Q(0), Q(1, 4), Q(1))
    coefficients = tuple(product((Q(0), Q(1, 2), Q(1), Q(2)), (Q(0), Q(1, 8), Q(1))))
    for length in range(4):
        for sequence in product(coefficients, repeat=length):
            gains = tuple(x[0] for x in sequence)
            forcing = tuple(x[1] for x in sequence)
            for initial in zeros:
                result = pb.propagate_recurrence(gains, forcing, initial)
                expected = tuple(exact_product_sum(gains[:j], forcing[:j], initial) for j in range(length + 1))
                require(tuple(result["error_bounds"]) == expected, "Recurrence differs from direct weighted sum")
                require(result["final_error_bound"] == expected[-1], "Recurrence final value")
                exhaustive += 1
    constant = 0
    for gain, force, initial, horizon in product((Q(0), Q(1, 2), Q(1), Q(2)),
                                                (Q(0), Q(1, 8), Q(1)), zeros, (0, 1, 2, 5, 9)):
        result = pb.constant_recurrence(gain, force, horizon, initial)
        expected = exact_product_sum((gain,) * horizon, (force,) * horizon, initial)
        require(result["final_error_bound"] == expected, "Constant recurrence differs from direct sum")
        constant += 1
    return {"exhaustive_sequences_and_initial_values": exhaustive, "constant_envelopes": constant,
            "scope": "all named rational coefficient sequences through length three; named constant horizons"}


def inspect_network_bound(pb, graph, old, new, old_radius, new_radius, fmt, initial=Q(0), columns=None):
    result = pb.network_bound(graph, old, new, old_radius, new_radius, fmt,
                              initial_error=initial, first_difference_columns=columns)
    old_radius, new_radius = tuple(old_radius), tuple(new_radius)
    e = Q(initial)
    gains, forces = [], []
    for index, (site, call) in enumerate(zip(graph, result["calls"])):
        old_bank, new_bank = old[site["bank_id"]], new[site["bank_id"]]
        joint = tuple(max(a, b) for a, b in zip(old_radius, new_radius))
        old_next = signed_enclosure_reference(old_bank, old_radius, fmt, site["activation"])
        new_next = signed_enclosure_reference(new_bank, new_radius, fmt, site["activation"])
        _, old_errors = interval_endpoint_reference(old_bank, joint, fmt)
        _, new_errors = interval_endpoint_reference(new_bank, joint, fmt)
        selected = tuple(range(len(joint))) if index or columns is None else tuple(columns)
        gain = max((sum((abs(word_value(row[j], fmt)) for j in selected), Q(0))
                    for row in new_bank["weights"]), default=Q(0))
        drift = max((abs(word_value(nb, fmt) - word_value(ob, fmt)) +
                     sum((abs(word_value(nw, fmt) - word_value(ow, fmt)) * r
                          for ow, nw, r in zip(orow, nrow, joint)), Q(0))
                     for orow, nrow, ob, nb in zip(old_bank["weights"], new_bank["weights"],
                                                 old_bank["bias"], new_bank["bias"])), default=Q(0))
        force = drift + max(old_errors, default=Q(0)) + max(new_errors, default=Q(0))
        e = gain * e + force
        require(tuple(call["old_input_bounds"]) == old_radius and tuple(call["new_input_bounds"]) == new_radius,
                "Endpoint input enclosure is not inherited from previous layer")
        require(tuple(call["joint_input_bounds"]) == joint, "Joint input envelope misses endpoint")
        require(call["L"] == gain and call["beta"] == force, "Layer gain or forcing differs from independent proof")
        require(tuple(call["old_output_bounds"]) == old_next and tuple(call["new_output_bounds"]) == new_next,
                "Endpoint range enclosure differs from symbolic recurrence")
        for bank, radius, next_radius in ((old_bank, old_radius, old_next), (new_bank, new_radius, new_next)):
            tight = ordered_interval_reference(bank, radius, fmt, site["activation"])
            require(all(max(abs(lo), abs(hi)) <= r for (lo, hi), r in zip(tight, next_radius)),
                    "Independent monotone-RNE interval escapes certified output box")
        old_radius, new_radius = old_next, new_next
        gains.append(gain); forces.append(force)
    require(result["final_error_bound"] == e == exact_product_sum(gains, forces, initial),
            "Network bound omits a layer or propagated earlier error")
    require(tuple(result["old_output_bounds"]) == old_radius and tuple(result["new_output_bounds"]) == new_radius,
            "Final endpoint box differs")
    require(result["domain_containment_proved"] is True and result["totality_proved"] is True,
            "Missing totality or containment")
    return result


def inspect_trace(pb, graph, banks, inputs, fmt):
    expected, _ = graph_reference(graph, banks, inputs, fmt)
    result = pb.trace_network(graph, banks, inputs, fmt)
    require(tuple(result["output_words"]) == expected, "Network actual words differ from independent RNE")
    return expected


def check_networks(pb):
    pairs = traces = generic = 0
    records = []
    rng = random.Random(SEED)
    for fmt in ("BF16", "FP32"):
        eta = constants(fmt)[1]
        points = list(product((Q(-1), Q(0), Q(1)), repeat=2)) + [(eta, -eta), (2 * eta, eta), (Q(1, 3), -Q(1, 3))]
        for model in ("two_layer_relu_v1", "shared_relu_v1"):
            graph = pb.model_descriptor(model, fmt)["graph"]
            for variant in range(6):
                old = pb.initial_banks(model, fmt)
                new = copy.deepcopy(old)
                name = "first" if model == "two_layer_relu_v1" else "shared"
                weights = [list(row) for row in new[name]["weights"]]
                weights[variant % 2][(variant // 2) % 2] = round_word(
                    word_value(weights[variant % 2][(variant // 2) % 2], fmt) + Q(variant - 2, 16), fmt)
                new[name]["weights"] = tuple(tuple(row) for row in weights)
                if variant == 5:
                    new[name]["bias"] = (round_word(Q(1, 8), fmt), round_word(Q(-1, 8), fmt))
                bound = inspect_network_bound(pb, graph, old, new, (Q(1),) * 2, (Q(1),) * 2, fmt)
                analyzed = pb.analyze_model(model, fmt, old, new)
                require(analyzed["observed_bound"] == bound["final_error_bound"], "Feedforward observation is not final bound")
                maximum = Q(0)
                for point in points:
                    raw = tuple(round_word(x, fmt) for x in point)
                    a = inspect_trace(pb, graph, old, raw, fmt)
                    b = inspect_trace(pb, graph, new, raw, fmt)
                    gap = infnorm(tuple(word_value(y, fmt) - word_value(x, fmt) for x, y in zip(a, b)))
                    maximum = max(maximum, gap)
                    require(gap <= bound["final_error_bound"], "Finite nonlinear point escapes bound")
                    traces += 1
                pairs += 1
                records.append({"model": model, "format": fmt, "variant": variant,
                                "bound": str(bound["final_error_bound"]), "finite_max": str(maximum)})
        for iteration in range(12):
            graph = ({"call_id": "first", "bank_id": "a", "activation": "relu"},
                     {"call_id": "second", "bank_id": "b", "activation": "identity"})
            a = tuple(tuple(Q(rng.randrange(-3, 4), 4) for _ in range(2)) for _ in range(3))
            b = tuple(tuple(Q(rng.randrange(-3, 4), 4) for _ in range(3)) for _ in range(2))
            old = {"a": make_bank(a, fmt), "b": make_bank(b, fmt)}
            new = copy.deepcopy(old)
            new["b"]["bias"] = (round_word(Q(1, 16), fmt), round_word(Q(-1, 16), fmt))
            result = inspect_network_bound(pb, graph, old, new, (Q(1),) * 2, (Q(3, 2),) * 2,
                                           fmt, initial=Q(1, 2))
            require(result["final_error_bound"] >= 0, "Negative certified bound")
            generic += 1
    return {"registered_endpoint_pairs": pairs, "registered_point_pairs": traces,
            "seeded_rectangular_networks": generic, "seed": SEED, "records": records,
            "scope": "complete named ternary inputs plus subnormal/thirds probes; seeded rectangular graphs"}


def expect_refusal(action, label, results):
    try:
        action()
    except (ValueError, TypeError, OverflowError) as exc:
        results.append({"case": label, "type": type(exc).__name__, "reason": str(exc)})
    else:
        raise AssertionError("Expected refusal was accepted: " + label)


def check_recurrent(pb):
    analyses = pairs = trace_runs = invariants = 0
    refusals, family_records = [], []
    for fmt in ("BF16", "FP32"):
        initial_values = (Q(-1, 4), Q(0), Q(1, 4))
        initial_words = tuple(round_word(v, fmt) for v in initial_values)
        histories = tuple(tuple((round_word(v, fmt),) for v in history)
                          for history in product((Q(-1), Q(0), Q(1)), repeat=3))
        for model in ("contractive_scalar_v1", "neutral_scalar_v1", "amplifying_scalar_v1"):
            old = pb.initial_banks(model, fmt)
            new = copy.deepcopy(old)
            new["update"]["bias"] = (round_word(Q(1, 32), fmt),)
            graph = pb.model_descriptor(model, fmt)["graph"]
            tables = []
            for banks in (old, new):
                table = {}
                for state, history in product(initial_words, histories):
                    reference = model_reference(pb, model, banks, (state,), history, fmt)
                    executed = pb.trace_model(model, fmt, banks, (state,), history)
                    require(tuple(tuple(v) for v in executed["states"]) == reference,
                            "Recurrent trace differs from independent word stepping")
                    table[(state, history)] = reference
                    trace_runs += 1
                tables.append(table)
            for initial_error in (Q(0), Q(1, 2)):
                result = pb.analyze_model(model, fmt, old, new, horizon=3, initial_error=initial_error)
                gains, forces = [], []
                old_radius = new_radius = (Q(1),)
                current_error = initial_error
                for step in result["steps"]:
                    ref = inspect_network_bound(pb, graph, old, new, old_radius + (Q(1),),
                                                new_radius + (Q(1),), fmt, current_error, columns=(0,))
                    require(step["final_error_bound"] == ref["final_error_bound"], "Time-step mismatch")
                    gains.append(ref["lipschitz_product"])
                    forces.append(ref["forcing_bound"])
                    old_radius, new_radius = tuple(ref["old_output_bounds"]), tuple(ref["new_output_bounds"])
                    current_error = ref["final_error_bound"]
                expected = tuple(exact_product_sum(gains[:t], forces[:t], initial_error) for t in range(4))
                require(tuple(result["error_bounds"]) == expected, "Time product-sum mismatch")
                require(result["observed_bound"] == max(expected), "Full-prefix bound omits earlier state")
                require(result["uniform_in_time_bound"] is None, "Finite tube mislabeled all-time")
                maximum = Q(0)
                for left, right, history in product(initial_words, initial_words, histories):
                    if abs(word_value(right, fmt) - word_value(left, fmt)) > initial_error:
                        continue
                    a, b = tables[0][(left, history)], tables[1][(right, history)]
                    for t, (av, bv) in enumerate(zip(a, b)):
                        gap = abs(word_value(av[0], fmt) - word_value(bv[0], fmt))
                        require(gap <= expected[t], "Actual paired state escapes relational bound")
                        require(abs(word_value(av[0], fmt)) <= result["old_state_tube"][t][0] and
                                abs(word_value(bv[0], fmt)) <= result["new_state_tube"][t][0],
                                "Actual endpoint state escapes its own tube")
                        maximum = max(maximum, gap)
                    pairs += 1
                family_records.append({"model": model, "format": fmt, "initial_error": str(initial_error),
                                       "observed_bound": str(result["observed_bound"]),
                                       "finite_max": str(maximum), "horizon": 3})
                analyses += 1
                for horizon in (0, 1):
                    shorter = pb.analyze_model(model, fmt, old, new, horizon=horizon, initial_error=initial_error)
                    require(tuple(shorter["error_bounds"]) == expected[:horizon + 1], "Horizon prefix changed")
                    require(shorter["observed_bound"] == max(expected[:horizon + 1]), "Short-horizon observation")
                    analyses += 1
            if model == "contractive_scalar_v1":
                result = pb.analyze_model(model, fmt, old, new, horizon=5, initial_error=Q(1, 2),
                                          method="invariant", state_box=Q(2))
                proof = inspect_network_bound(pb, graph, old, new, (Q(2), Q(1)), (Q(2), Q(1)),
                                               fmt, Q(0), columns=(0,))
                require(max(proof["old_output_bounds"] + proof["new_output_bounds"]) <= 2,
                        "Common invariant does not contain both images")
                expected_uniform = max(Q(1, 2), proof["forcing_bound"] / (1 - proof["lipschitz_product"]))
                require(result["common_invariant_verified"] is True and
                        result["uniform_in_time_bound"] == expected_uniform, "Uniform contraction certificate")
                invariants += 1
        neutral = pb.initial_banks("neutral_scalar_v1", fmt)
        expect_refusal(lambda: pb.analyze_model("neutral_scalar_v1", fmt, neutral, neutral,
                                                method="invariant", state_box=1),
                       fmt + ":conservative_identity_invariant", refusals)
        point = pb.trace_model("neutral_scalar_v1", fmt, neutral, (round_word(1, fmt),), ((0,),) * 3)
        require(all(s == (round_word(1, fmt),) for s in point["states"]), "Identity fixture unexpectedly exits")
        old = pb.initial_banks("contractive_scalar_v1", fmt)
        new = {"update": make_bank(((Q(3, 2), Q(1, 8)),), fmt)}
        expect_refusal(lambda: pb.analyze_model("contractive_scalar_v1", fmt, old, new, horizon=1, state_box=1),
                       fmt + ":new_endpoint_exits_old_cap", refusals)
        old_point = model_reference(pb, "contractive_scalar_v1", old, (round_word(1, fmt),), ((round_word(1, fmt),),), fmt)
        new_point = model_reference(pb, "contractive_scalar_v1", new, (round_word(1, fmt),), ((round_word(1, fmt),),), fmt)
        require(word_value(old_point[-1][0], fmt) < 1 < word_value(new_point[-1][0], fmt), "Domain exit witness")
    return {"analyses": analyses, "complete_initial_pair_history_cases": pairs,
            "independent_word_trajectory_runs": trace_runs, "common_invariants": invariants,
            "refusals": refusals, "families": family_records,
            "scope": "all three-valued input histories of length three and declared three-valued initial pairs; not full raw-state enumeration"}


def check_control(cf):
    margins = pairs = seeded = 0
    refusals, witnesses = [], []
    rng = random.Random(SEED + 1)
    for fmt in ("BF16", "FP32"):
        unit, eta, _, _ = constants(fmt)
        for sign in (-1, 1):
            old = make_bank(((Q(1, 4), Q(-1, 8)),), fmt, (sign * Q(2),))
            new = make_bank(((Q(1, 4), Q(-1, 16)),), fmt, (sign * Q(33, 16),))
            row, rowp = old["weights"][0], new["weights"][0]
            bias, biasp = old["bias"][0], new["bias"][0]
            proof = cf.certify_guard_margin(row, rowp, bias, biasp, fmt,
                                            (Q(1), Q(1)), (Q(5, 4), Q(5, 4)), Q(1, 4))
            _, error_old = interval_endpoint_reference(old, (Q(1), Q(1)), fmt)
            _, error_new = interval_endpoint_reference(new, (Q(5, 4), Q(5, 4)), fmt)
            drift = Q(1, 8)
            gain = Q(5, 16)
            expected_change = drift + gain / 4 + error_old[0] + error_new[0]
            expected_margin = Q(2) - Q(3, 8) - error_old[0]
            require(proof["guard_change_bound"] == expected_change and proof["margin"] == expected_margin,
                    "Guard margin terms differ from independent exact derivation")
            require(proof["global_trajectory_containment_verified"] is False and
                    proof["authorizes_live_commit"] is False, "Guard helper overclaims provenance or authority")
            finite = []
            for x, increment in product(product((-1, 0, 1), repeat=2), product((Q(-1, 4), Q(0), Q(1, 4)), repeat=2)):
                old_input = tuple(round_word(v, fmt) for v in x)
                new_input = tuple(round_word(Q(v) + d, fmt) for v, d in zip(x, increment))
                finite.append((old_input, new_input))
            diagnostic = cf.diagnose_finite_pairs(row, rowp, bias, biasp, finite, fmt,
                                                  old_box=(Q(1), Q(1)), new_box=(Q(5, 4), Q(5, 4)),
                                                  input_radius=Q(1, 4))
            for (left, right), observed in zip(finite, diagnostic["pairs"]):
                a = affine_reference((row,), (bias,), left, fmt)
                b = affine_reference((rowp,), (biasp,), right, fmt)
                require(observed["old_output_word"] == a["words"][0] and observed["new_output_word"] == b["words"][0],
                        "Guard point words differ from independent RNE")
                av, bv = word_value(a["words"][0], fmt), word_value(b["words"][0], fmt)
                require((av > 0) == (bv > 0) == (sign > 0) and abs(bv - av) <= expected_change,
                        "Certified branch margin fails on admitted pair")
                pairs += 1
            margins += 1
        for _ in range(16):
            row = tuple(Q(rng.randrange(-2, 3), 16) for _ in range(2))
            rowp = tuple(v + Q(rng.randrange(-1, 2), 64) for v in row)
            old = make_bank((row,), fmt, (Q(3),))
            new = make_bank((rowp,), fmt, (Q(49, 16),))
            proof = cf.certify_guard_margin(old["weights"][0], new["weights"][0], old["bias"][0],
                                            new["bias"][0], fmt, (Q(1),) * 2, (Q(1),) * 2, Q(1, 2))
            require(proof["margin"] > proof["guard_change_bound"], "Seeded accepted guard lacks strict margin")
            seeded += 1
        half = make_bank(((Q(1, 2),),), fmt)
        a = affine_reference(half["weights"], half["bias"], (1,), fmt)
        b = affine_reference(half["weights"], half["bias"], (2,), fmt)
        require(a["words"] == (0,) and b["words"] == (1,), "Subnormal staircase witness")
        require(eta > Q(1, 2) * eta, "Exact Lipschitz failure not strict")
        x = unit
        dx = 2 * unit * unit
        shifted = make_bank(((Q(1),),), fmt, (Q(1),))
        aa = affine_reference(shifted["weights"], shifted["bias"], (round_word(x, fmt),), fmt)
        bb = affine_reference(shifted["weights"], shifted["bias"], (round_word(x + dx, fmt),), fmt)
        gap = word_value(bb["words"][0], fmt) - word_value(aa["words"][0], fmt)
        old_error, new_error = abs(aa["error"][0]), abs(bb["error"][0])
        require(gap == 2 * unit == dx + old_error + new_error and
                gap > dx + old_error and gap > dx + new_error, "Both rounding terms necessity")
        zero, positive = (round_word(0, fmt),), (round_word(eta, fmt),)
        branch = cf.diagnose_finite_pairs((round_word(1, fmt),), (round_word(1, fmt),), 0, 0,
                                          ((zero, positive),), fmt)
        require(branch["branch_changes"] == 1, "Finite zero/eta branch jump not recorded")
        expect_refusal(lambda: cf.strict_margin(eta, eta), fmt + ":non_strict_margin", refusals)
        expect_refusal(lambda: cf.diagnose_finite_pairs((round_word(1, fmt),), (round_word(1, fmt),), 0, 0,
                                                       ((zero, positive),), fmt, old_box=(0,), new_box=(0,), input_radius=eta),
                       fmt + ":new_guard_domain_omitted", refusals)
        expect_refusal(lambda: cf.trace_guard((round_word(1, fmt),), 0, (1 << (precision(fmt) + 7),), fmt),
                       fmt + ":negative_zero_guard_input", refusals)
        values = (round_word(1, fmt), round_word(-1, fmt))
        rotated = (round_word(1, fmt), round_word(1, fmt))
        require(cf.relu_words(rotated, fmt) != (0, cf.relu_words(values, fmt)[0]), "ReLU rotation unexpectedly commutes")
        witnesses.append({"format": fmt, "eta": str(eta), "half_map_actual_gap": str(eta),
                          "shifted_map_input_gap": str(dx), "shifted_map_output_gap": str(gap),
                          "old_error": str(old_error), "new_error": str(new_error)})
    return {"uniform_margin_certificates": margins, "complete_guard_pair_cases": pairs,
            "seeded_margin_certificates": seeded, "seed": SEED + 1,
            "refusals": refusals, "witnesses": witnesses,
            "scope": "declared two-box pair relations; no surrounding program reachability inferred"}


def check_receipts(pb, pc):
    from b3_runtime import load_b1
    count = 0
    refusals, records = [], []
    for fmt in ("BF16", "FP32"):
        for model in pb.MODELS:
            old = pb.initial_banks(model, fmt)
            new = copy.deepcopy(old)
            name = next(iter(new))
            bias = list(new[name]["bias"])
            bias[0] = round_word(Q(1, 32), fmt)
            new[name]["bias"] = tuple(bias)
            recurrent = model not in pb.MODELS[:2]
            horizon, e0 = (3, Q(1, 2)) if recurrent else (1, Q(0))
            for method in (("tube", "invariant") if model == "contractive_scalar_v1" else ("tube",)):
                state_box = Q(2) if method == "invariant" else None
                analysis = pb.analyze_model(model, fmt, old, new, horizon, e0, method, state_box)
                budget = analysis["observed_bound"]
                descriptor = pb.model_descriptor(model, fmt)
                width = 1 if recurrent else 2
                context = {"schema": pc.CONTEXT_SCHEMA, "model_id": model, "format": fmt,
                           "weight_version": 9, "old_banks": old, "new_banks": new,
                           "old_initial_words": (0,) * width,
                           "new_initial_words": (round_word(Q(1, 4), fmt),) if recurrent else (0,) * width,
                           "ticks": 4, "schedule": descriptor["schedule"]}
                text = pc.make_propagation_certificate(model, fmt, old, new, budget, horizon, e0, method,
                                                       state_box, 9, context)
                receipt = pc.check_propagation_certificate(text, model, fmt, old, new, budget, horizon, e0,
                                                          method, state_box, 9, context)
                require(receipt["authorizes_commit"] is False and receipt["claims_BIT"] is False and
                        receipt["claims_exact_ALG"] is False and receipt["claims_program_noninterference"] is False,
                        "Propagation receipt grants unproved authority")
                require(Q(*receipt["bound"]) == budget, "Receipt bound differs from propagation proof")
                records.append({"format": fmt, "model": model, "method": method,
                                "horizon": horizon, "initial_error": str(e0), "bound": str(budget)})
                count += 1
        model = "shared_relu_v1"
        old = pb.initial_banks(model, fmt)
        new = copy.deepcopy(old)
        new["shared"]["bias"] = (round_word(Q(1, 16), fmt), 0)
        budget = pb.analyze_model(model, fmt, old, new)["observed_bound"]
        text = pc.make_propagation_certificate(model, fmt, old, new, budget, version=2)
        def tampered(change):
            packet = json.loads(text)
            change(packet["payload"])
            packet["payload_sha256"] = hashlib.sha256(canonical(packet["payload"]).encode()).hexdigest()
            return canonical(packet)
        mutations = {
            "omitted_shared_call": lambda p: p["descriptor"]["graph"].pop(),
            "sampled_domain": lambda p: p["descriptor"].__setitem__("source_domain", "samples_only"),
            "initial_relation": lambda p: p["descriptor"].__setitem__("initial_relation", "unrelated_states"),
            "changed_policy": lambda p: p["descriptor"].__setitem__("numerical_policy", "FMA"),
            "changed_schedule": lambda p: p["descriptor"].__setitem__("schedule", "asynchronous"),
            "incomplete_observation": lambda p: p["observation"]["ports"].pop(),
            "false_BIT": lambda p: p.__setitem__("claims_BIT", True),
            "false_authority": lambda p: p.__setitem__("authorizes_commit", True),
            "lowered_bound": lambda p: p["proof"].__setitem__("observed_bound", [0, 1]),
            "changed_horizon": lambda p: p.__setitem__("horizon", 2),
            "false_domain_proof": lambda p: p["proof"].__setitem__("domain_containment_proved", False),
            "changed_endpoint": lambda p: p["new_banks"]["shared"]["bias"].__setitem__(0, 0),
        }
        for label, mutate in mutations.items():
            expect_refusal(lambda mutate=mutate: pc.check_propagation_certificate(
                tampered(mutate), model, fmt, old, new, budget, version=2), fmt + ":" + label, refusals)
        expect_refusal(lambda: pc.make_propagation_certificate(model, fmt, old, new, budget / 2),
                       fmt + ":budget_too_small", refusals)
        expect_refusal(lambda: pc.check_propagation_certificate(text, model, fmt, old, new, budget, version=3),
                       fmt + ":stale_version", refusals)
        expect_refusal(lambda: pc.make_propagation_certificate("sample_model", fmt, old, new, budget),
                       fmt + ":unknown_domain", refusals)
        # New B3 interface fixture: epsilon seven produces exact (-1/16,+1/16)
        # after projection. This does not replay any saved optimizer experiment.
        ok, cu = load_b1("optimizer_kernel"), load_b1("constrained_updates")
        config = cu.OptimizerConfig("adamw", Q(1), beta1=Q(0), beta2=Q(0), epsilon=Q(7))
        kernel = ok.OptimizerKernel("duplicate_feedback_v1", fmt, config)
        gradient = cu.Matrix(((Q(1), Q(0)), (Q(0), Q(0))), 2)
        kernel.commit(kernel.prepare(ok.optimizer_request(gradient, "projected")))
        kernel.tick(round_word(1, fmt))
        snapshot = kernel.snapshot()
        require(snapshot["weights"] == [[round_word(Q(15, 16), fmt), round_word(Q(1, 16), fmt)], [0, round_word(1, fmt)]] and
                snapshot["optimizer_state"]["m"]["rows"][0][0] == [1, 1] and
                snapshot["optimizer_state"]["v"]["rows"][0][0] == [1, 1], "B3 nonzero-moment fixture differs")
        external = {"kind": "B1_identity_only", "snapshot": snapshot}
        bound_record = pc.make_propagation_certificate(model, fmt, old, new, budget,
                                                       version=kernel.version, external_context=external)
        expect_refusal(lambda: kernel.commit(bound_record), fmt + ":B1_rejects_readonly_receipt", refusals)
        require(kernel.snapshot() == snapshot, "Readonly receipt changed B1 composite state")
        partial = copy.deepcopy(external)
        del partial["snapshot"]["schedule"]
        expect_refusal(lambda: pc.make_propagation_certificate(model, fmt, old, new, budget, external_context=partial),
                       fmt + ":missing_external_schedule", refusals)
        kernel.tick(round_word(1, fmt))
        later = kernel.snapshot()
        expect_refusal(lambda: pc.check_propagation_certificate(bound_record, model, fmt, old, new, budget,
                       version=kernel.version, external_context={"kind": "B1_identity_only", "snapshot": later}),
                       fmt + ":changed_external_snapshot", refusals)
        require(kernel.snapshot() == later, "Stale-context refusal changed B1 state")
        model_r = "contractive_scalar_v1"
        banks = pb.initial_banks(model_r, fmt)
        descriptor = pb.model_descriptor(model_r, fmt)
        context = {"schema": pc.CONTEXT_SCHEMA, "model_id": model_r, "format": fmt, "weight_version": 0,
                   "old_banks": banks, "new_banks": banks, "old_initial_words": (0,),
                   "new_initial_words": (round_word(Q(1, 4), fmt),), "ticks": 0, "schedule": descriptor["schedule"]}
        expect_refusal(lambda: pc.make_propagation_certificate(model_r, fmt, banks, banks, Q(2),
                                                               initial_error=0, state_context=context),
                       fmt + ":same_box_is_not_same_initial_state", refusals)
    return {"registered_receipts": count, "records": records, "expected_refusals": refusals,
            "full_nonzero_moment_B1_rollback_fixtures": 2,
            "scope": "complete registered analytic domains; pure evidence, no live authorization"}


def check_frozen_B1():
    path = ROOT.parent / "p2_b1" / "training_results.json"
    original = path.read_bytes()
    document = json.loads(original)
    records = []
    for run in document["runs"]:
        for step in run["records"]:
            if step["status"] != "refused":
                continue
            require(run["model"] == "duplicate_feedback_v1", "Unexpected frozen refusal domain")
            fmt = run["format"]
            old, new = tuple(map(tuple, step["old_weights"])), tuple(map(tuple, step["candidate_weights"]))
            exact_ones = tuple(sum((word_value(n, fmt) - word_value(o, fmt) for o, n in zip(a, b)), Q(0))
                               for a, b in zip(old, new))
            require(any(exact_ones), "Frozen joint refusal no longer fails ALG")
            for site in ("state", "input"):
                for h in ((0, 0), (round_word(1, fmt),) * 2):
                    a = affine_reference(old, (0, 0), h, fmt)
                    b = affine_reference(new, (0, 0), h, fmt)
                    require(a["words"] == b["words"], "Frozen rejected candidate no longer BIT-equal")
            require(step["proposed_ALG_annihilation"] is False and
                    step["proposed_complete_D"]["all_protected_observations_equal"] is True,
                    "Frozen classification differs")
            records.append({"format": fmt, "exact_ones_residual": [str(v) for v in exact_ones], "protected_calls": 4})
    require(len(records) == 21, "Frozen refusal count changed")
    target = [run for run in document["runs"] if run["format"] == "FP32" and
              run["model"] == "duplicate_feedback_v1" and run["optimizer"] == "adamw" and run["safe_live_route"] is True]
    require(len(target) == 1, "Frozen FP32 Adam run not unique")
    target = target[0]
    require(target["accepted_commits"] == 0 and target["refused_attempts"] == 8 and Q(target["final_loss"]) == Q(5, 2),
            "Frozen FP32 Adam zero progress changed")
    require(path.read_bytes() == original, "Frozen training evidence changed during reading")
    return {"endpoint_pairs": 21, "protected_call_checks": 84, "all_actual_BIT_equal": True,
            "all_exact_ALG_fail": True, "FP32_Adam_accepted": 0, "FP32_Adam_refused": 8,
            "FP32_Adam_final_loss": "5/2", "source_sha256": digest(path), "records": records,
            "scope": "read-only raw endpoints; no optimizer generation or old-suite replay"}


def check_adversaries(pb):
    refusals, repeated = [], []
    for fmt in ("BF16", "FP32"):
        graph = ({"call_id": "one", "bank_id": "shared", "activation": "relu"},
                 {"call_id": "two", "bank_id": "shared", "activation": "identity"})
        old = {"shared": make_bank(((1, 0), (0, 1)), fmt)}
        new = {"shared": make_bank(((Q(5, 4), 0), (0, Q(5, 4))), fmt)}
        h = (round_word(1, fmt), 0)
        a, b = inspect_trace(pb, graph, old, h, fmt), inspect_trace(pb, graph, new, h, fmt)
        gap = word_value(b[0], fmt) - word_value(a[0], fmt)
        require(gap == Q(9, 16) > Q(1, 4), "Shared update loses repeated-use term")
        bound = inspect_network_bound(pb, graph, old, new, (Q(1),) * 2, (Q(1),) * 2, fmt)
        repeated.append({"format": fmt, "two_call_exact_and_actual_gap": str(gap),
                         "single_call_gap": "1/4", "bound": str(bound["final_error_bound"])})
        duplicate = ({"call_id": "same", "bank_id": "shared", "activation": "relu"},
                     {"call_id": "same", "bank_id": "shared", "activation": "identity"})
        expect_refusal(lambda: pb.validate_network(duplicate, old, fmt), fmt + ":duplicate_call_label", refusals)
        expect_refusal(lambda: pb.validate_network(graph, {**old, "unused": old["shared"]}, fmt),
                       fmt + ":unreferenced_physical_bank", refusals)
        expect_refusal(lambda: pb.validate_network(graph, {}, fmt), fmt + ":missing_shared_bank", refusals)
        hard = ({"call_id": "branch", "bank_id": "shared", "activation": "hard_step"},)
        expect_refusal(lambda: pb.validate_network(hard, old, fmt), fmt + ":unsupported_hard_branch", refusals)
        negative_zero = copy.deepcopy(old)
        negative_zero["shared"]["bias"] = (1 << (precision(fmt) + 7), 0)
        expect_refusal(lambda: pb.validate_network(graph, negative_zero, fmt), fmt + ":negative_zero_endpoint", refusals)
        expect_refusal(lambda: pb.network_bound(graph, old, new, (1, 1), (1, 1), fmt,
                                                first_difference_columns=(0, 0)), fmt + ":duplicate_difference_column", refusals)
        expect_refusal(lambda: pb.network_bound(graph, old, new, (1, 1), (1, 1), fmt, initial_error=-1),
                       fmt + ":negative_initial_radius", refusals)
        expect_refusal(lambda: pb.network_bound(graph, old, new, (1.0, 1), (1, 1), fmt),
                       fmt + ":host_float_box", refusals)
        model = "contractive_scalar_v1"
        banks = pb.initial_banks(model, fmt)
        expect_refusal(lambda: pb.analyze_model(model, fmt, banks, banks, horizon=65), fmt + ":unsupported_horizon", refusals)
        expect_refusal(lambda: pb.analyze_model(model, fmt, banks, banks, horizon=True), fmt + ":boolean_horizon", refusals)
        expect_refusal(lambda: pb.trace_model(model, fmt, banks, (0,), ((round_word(2, fmt),),)),
                       fmt + ":illegal_external_input", refusals)
        unit, eta, maximum, _ = constants(fmt)
        saturated = {"w": make_bank(((maximum, maximum),), fmt)}
        single = ({"call_id": "saturated", "bank_id": "w", "activation": "identity"},)
        point = inspect_trace(pb, single, saturated, (round_word(Q(1, 2), fmt),) * 2, fmt)
        require(word_value(point[0], fmt) == maximum, "Saturated finite point mismatch")
        expect_refusal(lambda: pb.network_bound(single, saturated, saturated, (Q(1, 2),) * 2,
                                                (Q(1, 2),) * 2, fmt), fmt + ":conservative_totality_refusal", refusals)
        expect_refusal(lambda: pb.trace_network(single, saturated, (round_word(2, fmt), 0), fmt),
                       fmt + ":actual_overflow", refusals)
    return {"expected_refusals": refusals, "shared_call_witnesses": repeated,
            "scope": "schema/domain/totality failures are distinct from proven trajectory violations"}


def load_current(name):
    """Explicit-path import prevents a predecessor's same-name verifier alias."""
    import importlib.util
    path = ROOT / (name + ".py")
    if name in sys.modules:
        module = sys.modules[name]
        require(Path(module.__file__).resolve() == path.resolve(), "Unexpected current-stage module provenance")
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "Cannot load current-stage module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_checks():
    require(__debug__, "Run independent verification without -O/-OO")
    require(ROOT.name == "p2_b3" and Path(__file__).resolve() == ROOT / "verify_independent.py",
            "Independent B3 entry path mismatch")
    pb = load_current("propagation_bounds")
    cf = load_current("control_flow")
    pc = load_current("propagation_certificate")
    runtime = load_current("b3_runtime")
    started = datetime.now(timezone.utc).isoformat()
    begin = time.perf_counter()
    sections, costs = {}, {}
    for name, action in (
        ("recurrences", lambda: check_recurrences(pb)),
        ("networks", lambda: check_networks(pb)),
        ("recurrent_execution", lambda: check_recurrent(pb)),
        ("control", lambda: check_control(cf)),
        ("receipts", lambda: check_receipts(pb, pc)),
        ("frozen_B1", check_frozen_B1),
        ("adversaries", lambda: check_adversaries(pb)),
    ):
        t = time.perf_counter()
        sections[name] = action()
        costs[name] = time.perf_counter() - t
    forbidden = []
    for name, module in sys.modules.copy().items():
        file = getattr(module, "__file__", None)
        if file is None:
            continue
        path = Path(file).resolve()
        if path.parent != ROOT and path.name.startswith(("verify_", "review_")) and workspace_contains(path):
            forbidden.append(str(path))
    require(not forbidden, "Successful independent run imported previous verifier module")
    sources = ("verify_independent.py", "propagation_bounds.py", "propagation_certificate.py", "control_flow.py", "b3_runtime.py")
    evidence = ("propagation_results.json", "control_results.json", "certificate_results.json")
    return {"schema": "dmwk-p2-b3-independent-v1", "status": "passed", "seed": SEED,
            "started_utc": started, "elapsed_seconds": time.perf_counter() - begin, "section_seconds": costs,
            "sections": sections, "environment": runtime.environment_metadata(),
            "source_sha256": {name: digest(ROOT / name) for name in sources},
            "producer_evidence_sha256": {name: digest(ROOT / name) for name in evidence},
            "prior_stage_suites_rerun": False, "prior_optimizer_trajectories_replayed": False,
            "old_verifier_modules_imported_in_this_run": forbidden,
            "SMT_queries": 0, "proof_assistant_checked": False,
            "scope": "independent finite algebra, RNE, intervals, trajectory and interface evidence; universal results remain handwritten proofs"}


def workspace_contains(path):
    return path.is_relative_to(ROOT.parent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "independent_results.json")
    args = parser.parse_args()
    try:
        result = run_checks()
    except Exception as exc:
        result = {"schema": "dmwk-p2-b3-independent-v1", "status": "failed",
                  "failure": {"type": type(exc).__name__, "message": str(exc)}}
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        raise
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "elapsed_seconds": result["elapsed_seconds"],
                      "sections": list(result["sections"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()

