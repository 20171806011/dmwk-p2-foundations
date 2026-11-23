"""Independent B4 finite algebra, word arithmetic, switching and ownership checks.

Earlier verification suites are not imported or executed. Current modules are
loaded by exact file path to prevent predecessor module-name collisions.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from fractions import Fraction as Q
from functools import lru_cache
import hashlib
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114
CHECKS = 0


def require(ok, message):
    global CHECKS
    CHECKS += 1
    if not ok:
        raise AssertionError(message)


def load_current(name):
    path = ROOT / (name + ".py")
    if name in sys.modules:
        module = sys.modules[name]
        require(Path(module.__file__).resolve() == path, "Current module path mismatch")
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "Cannot locate current module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def determinant(a):
    if not a:
        return Q(1)
    if len(a) == 1:
        return Q(a[0][0])
    return sum(((-1) ** j * a[0][j] * determinant(tuple(tuple(row[k] for k in range(len(a)) if k != j)
                                                     for row in a[1:])) for j in range(len(a))), Q(0))


def rank(a):
    rows = tuple(tuple(Q(x) for x in row) for row in a)
    width = len(rows[0]) if rows else 0
    for size in range(min(len(rows), width), 0, -1):
        for ii, jj in product(combinations(range(len(rows)), size), combinations(range(width), size)):
            if determinant(tuple(tuple(rows[i][j] for j in jj) for i in ii)):
                return size
    return 0


def matmul(a, b, width=None):
    width = len(b[0]) if b else (0 if width is None else width)
    return tuple(tuple(sum((Q(row[k]) * Q(b[k][j]) for k in range(len(b))), Q(0))
                       for j in range(width)) for row in a)


def minus(a, b):
    return tuple(tuple(Q(x) - Q(y) for x, y in zip(ar, br)) for ar, br in zip(a, b))


def concat(*matrices):
    return tuple(sum((tuple(matrix[i]) for matrix in matrices), ()) for i in range(len(matrices[0])))


def zeros(n, d):
    return tuple((Q(0),) * d for _ in range(n))


def all_zero(a):
    return all(x == 0 for row in a for x in row)


def compatible(anchor_inputs, anchor_values):
    """Each requested output row must be in the input matrix's row space."""
    base = rank(anchor_inputs)
    return all(rank(tuple(anchor_inputs) + (tuple(row),)) == base for row in anchor_values)


def precision(fmt):
    return {"BF16": 8, "FP32": 24}[fmt]


@lru_cache(maxsize=None)
def word_value(raw, fmt):
    p = precision(fmt)
    f = p - 1
    require(type(raw) is int and 0 <= raw < 1 << (p + 8), "Reference word range")
    require(raw != 1 << (p + 7), "Reference rejects negative zero")
    exponent = raw >> f & 255
    fraction = raw & ((1 << f) - 1)
    require(exponent != 255, "Reference rejects nonfinite word")
    sign = -1 if raw >> (p + 7) else 1
    if exponent:
        fraction += 1 << f
        power = exponent - 127 - f
    else:
        power = 1 - 127 - f
    return sign * Q(fraction) * Q(2) ** power


def constants(fmt):
    p = precision(fmt)
    raw = (254 << (p - 1)) | ((1 << (p - 1)) - 1)
    return Q(1, 1 << p), word_value(1, fmt), word_value(raw, fmt), raw


@lru_cache(maxsize=None)
def round_word(value, fmt):
    value = Q(value)
    if value == 0:
        return 0
    sign = 1 << (precision(fmt) + 7) if value < 0 else 0
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
    lo_gap, hi_gap = value - word_value(lower, fmt), word_value(upper, fmt) - value
    nearest = lower if lo_gap < hi_gap or (lo_gap == hi_gap and lower % 2 == 0) else upper
    return sign | nearest if nearest else 0


def encode_matrix(a, fmt):
    return tuple(tuple(round_word(Q(x), fmt) for x in row) for row in a)


def decode_matrix(a, fmt):
    return tuple(tuple(word_value(x, fmt) for x in row) for row in a)


def affine_reference(weights, bias, inputs, fmt, activation="identity"):
    require(activation in ("identity", "relu"), "Unsupported independent activation")
    result = []
    for row, b in zip(weights, bias):
        current = b
        for w, x in zip(row, inputs):
            multiplication = round_word(word_value(w, fmt) * word_value(x, fmt), fmt)
            current = round_word(word_value(current, fmt) + word_value(multiplication, fmt), fmt)
        if activation == "relu" and word_value(current, fmt) < 0:
            current = 0
        result.append(current)
    return tuple(result)


def interval_reference(bank, bounds, fmt, activation="identity"):
    unit, eta, maximum, _ = constants(fmt)
    radii, errors = [], []
    for row, bias in zip(bank["weights"], bank["bias"]):
        center = word_value(bias, fmt)
        acc, error, exact_radius = abs(center), Q(0), Q(0)
        for w, radius in zip(row, bounds):
            x = abs(word_value(w, fmt)) * radius
            exact_radius += x
            if x > maximum:
                raise OverflowError("Unproved independent product range")
            pe = unit * x + eta / 2
            y = acc + min(maximum, x + pe)
            if y > maximum:
                raise OverflowError("Unproved independent addition range")
            ae = unit * y + eta / 2
            acc = min(maximum, y + ae)
            error += pe + ae
        lo, hi = max(-acc, center - exact_radius - error), min(acc, center + exact_radius + error)
        if activation == "relu":
            lo, hi = max(Q(0), lo), max(Q(0), hi)
        radii.append(max(abs(lo), abs(hi)))
        errors.append(error)
    return tuple(radii), tuple(errors)


def direct_product_sum(gains, forcing, initial):
    products = []
    for j in range(len(gains) + 1):
        p = Q(1)
        for gain in gains[j:]:
            p *= gain
        products.append(p)
    return Q(initial) * products[0] + sum((x * products[j + 1] for j, x in enumerate(forcing)), Q(0))


def expect_refusal(action, label, records):
    try:
        action()
    except (ValueError, TypeError, OverflowError) as exc:
        records.append({"case": label, "type": type(exc).__name__, "reason": str(exc)})
    else:
        raise AssertionError("Expected refusal absent: " + label)


def check_sequence(us, runtime):
    cu = runtime.load_b1("constrained_updates")
    ok = runtime.load_b1("optimizer_kernel")
    records, refusals = [], []
    accepted = ticks = full_calls = 0
    rng = random.Random(SEED)
    for fmt in ("BF16", "FP32"):
        config = cu.OptimizerConfig("sgd", Q(1, 4))
        owner = us.SequenceKernel(fmt, config, max_updates=64)
        baseline = owner.snapshot()
        # The caller still owns its configuration; live state must have a copy.
        object.__setattr__(config, "learning_rate", Q(7))
        require(owner.snapshot() == baseline, "Caller configuration aliases owned optimizer")
        theta = tuple(row[2] for row in baseline["kernel"]["weights"])
        state = 0
        path = Q(0)
        for step in range(16):
            before = owner.snapshot()
            exact_theta = tuple(word_value(v, fmt) for v in theta)
            gradient = cu.Matrix(((Q(0), Q(0), exact_theta[0] - 1),
                                  (Q(0), Q(0), exact_theta[1] + 1)), 3)
            request = ok.optimizer_request(gradient, "structural")
            expected_theta = tuple(round_word(x + Q(1, 4) * (target - x), fmt)
                                   for x, target in zip(exact_theta, (Q(1), Q(-1))))
            preview = owner.preview(request)
            require(owner.snapshot() == before, "Preview published an endpoint or ledger")
            preview["candidate_kernel"]["weights"][0][0] = 0
            preview["candidate_event"]["new_A"]["loss"] = [999, 1]
            require(owner.snapshot() == before, "Preview aliases live state")
            text = owner.prepare(request)
            require(owner.snapshot() == before, "Prepare published a staged value")
            receipt = owner.commit(text)
            snapshot = owner.snapshot()
            theta = expected_theta
            expected_words = ((round_word(1, fmt), 0, theta[0]), (0, round_word(1, fmt), theta[1]))
            require(owner.weights == expected_words, "Stored SGD endpoint differs from independent RNE update")
            require(snapshot["accepted_updates"] == step + 1 and snapshot["kernel"]["weight_version"] == step + 1,
                    "Accepted update count/version mismatch")
            require(snapshot["kernel"]["optimizer_state"]["step"] == step + 1, "Optimizer time mismatch")
            event = snapshot["accepted_ledger"][-1]
            old_words = tuple(map(tuple, before["kernel"]["weights"]))
            delta = minus(decode_matrix(expected_words, fmt), decode_matrix(old_words, fmt))
            require(event["actual_effective_rank"] == rank(delta), "Event update rank mismatch")
            require(tuple(tuple(Q(*x) for x in row) for row in event["actual_effective_delta"]["rows"]) == delta,
                    "Event uses a proposed rather than effective stored update")
            path += max(sum(map(abs, row), Q(0)) for row in delta)
            require(Q(*event["path_increment_norm_sum"]) == path, "Adjacent-update path ledger is wrong")
            expected_loss = sum(((word_value(v, fmt) - target) ** 2 for v, target in zip(theta, (1, -1))), Q(0)) / 2
            require(Q(*owner.evaluate_a()["loss"]) == expected_loss, "Toy A loss differs from independent decoding")
            for observation in owner.full_D():
                q, u = observation["q_word"], observation["u_word"]
                trace = observation["trace"]
                require(trace["state_output_words"] == [q, q] and trace["input_output_words"] == [u, u],
                        "Protected shared-call outputs changed")
                require(trace["next_state_word"] == (round_word(1, fmt) if bool(q) != bool(u) else 0),
                        "Protected feedback differs from Boolean reference")
                full_calls += 1
            bit = rng.randrange(2)
            state ^= bit
            owner.tick(round_word(bit, fmt))
            require(owner.state_word == round_word(state, fmt) and owner.ticks == step + 1,
                    "Paired protected tick diverged")
            require(owner.accepted_count == step + 1, "Tick changed update count")
            records.append({"format": fmt, "accepted_index": step + 1, "tick": step + 1,
                            "theta_words": list(theta), "loss": str(expected_loss), "delta_rank": rank(delta)})
            accepted += 1
            ticks += 1
        actual = owner.snapshot()
        detached = owner.snapshot()
        detached["accepted_ledger"].clear()
        detached["kernel"]["optimizer_state"]["m"]["rows"][0][0] = [7, 1]
        require(owner.snapshot() == actual, "Returned snapshot aliases owned ledger/moments")
        require(actual["capacity"]["reserved_column_dimension"] == 2 and
                actual["capacity"]["unrestricted_annihilator_dimension"] == 4,
                "Fixed-space dimension was incorrectly consumed by update count")
        # A representable proposed increment can still round away at an endpoint.
        tiny = cu.Matrix(((Q(0), Q(0), constants(fmt)[1]), (Q(0), Q(0), Q(0))), 3)
        noop = ok.ai_request(tiny, "structural")
        before = owner.snapshot()
        owner.commit(owner.prepare(noop))
        after = owner.snapshot()
        require(after["kernel"]["weights"] == before["kernel"]["weights"] and
                after["accepted_updates"] == before["accepted_updates"] + 1 and
                after["nonzero_stored_updates"] == before["nonzero_stored_updates"] and
                after["accepted_ledger"][-1]["actual_effective_rank"] == 0,
                "Stored no-op misreported as new response or omitted from accepted version history")
        accepted += 1
        # Distinct late-failure fixture: nonzero moments are already live.
        adam = cu.OptimizerConfig("adamw", Q(1), beta1=Q(0), beta2=Q(0), epsilon=Q(7))
        limited = us.SequenceKernel(fmt, adam, max_updates=1)
        g = cu.Matrix(((Q(0), Q(0), Q(1)), (Q(0), Q(0), Q(-1))), 3)
        request = ok.optimizer_request(g, "structural")
        limited.commit(limited.prepare(request)); limited.tick(round_word(1, fmt))
        live = limited.snapshot()
        require(live["kernel"]["optimizer_state"]["m"]["rows"][0][2] == [1, 1] and
                live["kernel"]["optimizer_state"]["v"]["rows"][0][2] == [1, 1], "Nonzero moment fixture failed")
        expect_refusal(lambda: limited.prepare(request), fmt + ":late_ledger_limit_after_inner_commit", refusals)
        require(limited.snapshot() == live, "Late ledger refusal partially published B1 or optimizer state")
        expect_refusal(lambda: limited.tick(round_word(Q(1, 2), fmt)), fmt + ":illegal_tick", refusals)
        require(limited.snapshot() == live, "Failed protected tick changed combined snapshot")
        # Rehashed semantic inconsistencies still fail complete recomputation.
        good = owner.prepare(ok.ai_request(cu.Matrix(((0, 0, Q(1, 64)), (0, 0, Q(-1, 64))), 3), "structural"))
        stable = owner.snapshot()
        mutations = {
            "event_loss": lambda p: p["new_accepted_event"]["new_A"].__setitem__("loss", [0, 1]),
            "staged_moment": lambda p: p["new_kernel_snapshot"]["optimizer_state"]["m"]["rows"][0].__setitem__(2, [99, 1]),
            "event_effective_rank": lambda p: p["new_accepted_event"].__setitem__("actual_effective_rank", 0),
            "omitted_shared_call": lambda p: p["D_descriptor"]["sites"].pop(),
            "changed_schedule": lambda p: p.__setitem__("schedule", "asynchronous"),
            "changed_task": lambda p: p["task"]["target_exact"].__setitem__(0, [9, 1]),
            "old_accepted_ledger": lambda p: p["old_combined_snapshot"]["accepted_ledger"].pop(),
        }
        for label, mutate in mutations.items():
            packet = json.loads(good)
            mutate(packet["payload"])
            packet["payload_sha256"] = hashlib.sha256(canonical(packet["payload"]).encode()).hexdigest()
            expect_refusal(lambda packet=packet: owner.commit(canonical(packet)), fmt + ":" + label, refusals)
            require(owner.snapshot() == stable, "Tampered update changed combined state")
        owner.tick(round_word(0, fmt))
        newer = owner.snapshot()
        expect_refusal(lambda: owner.commit(good), fmt + ":stale_tick_snapshot", refusals)
        require(owner.snapshot() == newer, "Stale candidate damaged newer state")
        unsafe = ok.ai_request(cu.Matrix(((Q(1), 0, 0), (0, 0, 0)), 3), "none")
        expect_refusal(lambda: owner.prepare(unsafe), fmt + ":changed_protected_fixed_column", refusals)
        require(owner.snapshot() == newer, "Unsafe candidate changed owner")
    return {"accepted_repeated_and_noop_updates": accepted, "learning_steps": 32,
            "paired_feedback_ticks": ticks, "complete_D_call_observations": full_calls,
            "seed": SEED, "records": records, "expected_refusals": refusals,
            "nonzero_moment_late_rollback_fixtures": 2,
            "scope": "fixed registered D and toy target; no universal learning benefit or newly admitted task"}


def check_algebra(ch):
    budgets = responses = anchors = 0
    identity = ((Q(1), Q(0)), (Q(0), Q(1)))
    X = ch.xp.matrix(identity)
    for entries in product((-1, 0, 1), repeat=4):
        h = (entries[:2], entries[2:])
        H = ch.xp.matrix(h)
        r = rank(h)
        for n, cap in product((1, 2), (0, 1, 2)):
            result = ch.algebra_budget(H, n, X, cap)
            require(result["protected_rank"] == r and result["unrestricted_update_space_dimension"] == n * (2 - r),
                    "Budget differs from independent minor rank")
            require(result["maximum_rank_under_cap"] == min(n, cap, 2 - r) and
                    result["unrestricted_response_image_dimension"] == n * (2 - r), "Rank/response budget mismatch")
            require(result["global_provenance_verified"] is False, "Supplied algebraic span gained global authority")
            budgets += 1
    protected = (((0,), (0,)), ((1,), (0,)), ((1,), (1,)), identity)
    for h in protected:
        for xe, re, cap in product(product((0, 1), repeat=4), product((0, 1), repeat=2), (0, 1)):
            x = (xe[:2], xe[2:]); r = (re,)
            constraints = concat(h, x)
            targets = (tuple(0 for _ in h[0]) + tuple(re),)
            expected = compatible(constraints, targets) and rank(r) <= cap
            answer = ch.response_feasibility(ch.xp.matrix(h), ch.xp.matrix(x), ch.xp.matrix(r), cap)
            require(answer["feasible"] == expected, "Response feasibility differs from direct row equations")
            if expected:
                solution = answer["solution"].rows
                require(all_zero(matmul(solution, h)) and matmul(solution, x) == tuple(tuple(Q(v) for v in row) for row in r),
                        "Constructed response fails independent direct equations")
                require(rank(solution) == rank(r), "Response construction not minimum rank")
            responses += 1
    lines = (((Q(1),), (Q(0),)), ((Q(0),), (Q(1),)), ((Q(1),), (Q(1),)))
    for labels in product((-1, 0, 1), repeat=3):
        tasks = tuple((ch.xp.matrix(h), ch.xp.matrix(((y,),))) for h, y in zip(lines, labels))
        result = ch.joint_task_feasibility(tasks)
        expected = labels[2] == labels[0] + labels[1]
        require(result["compatible"] == expected, "Three-task relation missed")
        for i, j in combinations(range(3), 2):
            require(ch.joint_task_feasibility((tasks[i], tasks[j]))["compatible"] is True,
                    "Distinct-line pair should have a common anchor")
        if expected:
            solution = result["particular_solution"].rows
            require(matmul(solution, concat(*lines)) == (tuple(Q(y) for y in labels),), "Anchor construction fails")
            require(result["solution_affine_dimension"] == 0, "Joint full-rank anchor dimension")
        else:
            witness = result["impossibility_witness"]
            alpha = witness["alpha"].rows
            require(all_zero(matmul(concat(*lines), alpha)) and
                    not all_zero(matmul((tuple(Q(y) for y in labels),), alpha)), "Anchor relation witness invalid")
        anchors += 1
    return {"minor_rank_budget_cases": budgets, "response_relation_and_rank_cases": responses,
            "three_task_anchor_cases": anchors, "pairwise_anchor_subchecks": anchors * 3,
            "scope": "named exact small rational matrices; generic span coverage is not inferred"}


def check_histories(ch):
    checked = 0
    witnesses = []
    for fmt in ("BF16", "FP32"):
        choices = tuple(product((-1, 0, 1), repeat=2))
        h1, h2 = ((Q(1),), (Q(0),)), ((Q(0),), (Q(1),))
        for w1, w2 in product(choices, repeat=2):
            exact = (((Q(0), Q(0)),), (tuple(Q(x) for x in w1),), (tuple(Q(x) for x in w2),))
            raw = tuple(encode_matrix(w, fmt) for w in exact)
            for mode, hs in (("fixed", (h1,)), ("cumulative", (h1, h2)), ("moving", (h1, h2))):
                result = ch.analyze_history(raw, fmt, tuple(ch.xp.matrix(h) for h in hs), mode, rank_cap=1)
                current_ok = []
                for k, step in enumerate(result["steps"]):
                    protection = hs[0] if mode == "fixed" else (concat(*hs[:k + 1]) if mode == "cumulative" else hs[k])
                    increment = minus(exact[k + 1], exact[k])
                    prefix = minus(exact[k + 1], exact[0])
                    safe = all_zero(matmul(increment, protection))
                    require(step["effective_delta"].rows == increment and step["prefix_delta"].rows == prefix,
                            "History uses incorrect actual increment or prefix")
                    require(step["annihilates_current_space"] == safe and step["update_rank"] == rank(increment) and
                            step["prefix_rank"] == rank(prefix), "History rank/annihilation mismatch")
                    current_ok.append(safe)
                require(result["all_current_space_checks_pass"] == all(current_ok), "Current-space conjunction mismatch")
                expected_prefixes = all(all_zero(matmul(minus(w, exact[0]), hs[0])) for w in exact)
                require(result["every_prefix_preserves_initial_space"] == expected_prefixes,
                        "Final sum substituted for prefix safety")
                for anchor in result["task_anchors"]:
                    arrival = anchor["arrival_index"]
                    h = hs[0] if mode == "fixed" else hs[arrival]
                    expected = all(all_zero(matmul(minus(w, exact[arrival]), h)) for w in exact[arrival:])
                    require(anchor["preserved_since_arrival"] == expected, "Task admission anchor shifted to W0")
                checked += 1
        zero = ((0, 0, 0),) * 3
        first = ((0, 0, 0), (0, 1, 0), (0, 0, 0))
        last = ((0, 0, 0), (0, 1, 0), (0, 0, 1))
        H = ch.xp.matrix(((1,), (0,), (0,)))
        growth = ch.analyze_history(tuple(encode_matrix(x, fmt) for x in (zero, first, last)), fmt, (H,), rank_cap=1)
        require(growth["all_current_space_checks_pass"] and growth["final_rank"] == 2 and
                growth["fixed_space_cap_bound"] == 2 and all(x["update_rank"] == 1 for x in growth["steps"]),
                "Rank-one increments incorrectly constrain cumulative rank to one")
        cancellation = ch.analyze_history(tuple(encode_matrix(((x,),), fmt) for x in (0, 1, 0)), fmt,
                                           (ch.xp.matrix(((1,),)),))
        require(cancellation["final_preserves_initial_space"] and not cancellation["every_prefix_preserves_initial_space"],
                "Final cancellation witness lost")
        arrival = ch.analyze_history(tuple(encode_matrix((x,), fmt) for x in ((0, 0), (0, 1), (0, 1))), fmt,
                                    (ch.xp.matrix(h1), ch.xp.matrix(h2)), "cumulative")
        require(arrival["all_arrival_anchors_preserved"] and not arrival["steps"][-1]["prefix_preserves_seen_union_relative_W0"],
                "New task current anchor confused with original endpoint")
        wrong_anchor = ch.task_anchor_check(encode_matrix(((0, 1),), fmt), fmt, ch.xp.matrix(h2), ch.xp.matrix(((0,),)))
        require(not wrong_anchor["anchor_satisfied"] and not wrong_anchor["future_annihilating_updates_can_repair_mismatch"],
                "Freezing directions incorrectly repairs an unsatisfied task")
        moving = ch.analyze_history(tuple(encode_matrix((x,), fmt) for x in ((0, 0), (0, 1), (1, 1))), fmt,
                                    (ch.xp.matrix(h1), ch.xp.matrix(h2)), "moving")
        require(moving["all_current_space_checks_pass"] and not moving["all_arrival_anchors_preserved"],
                "Moving-space historical failure missing")
        witnesses.append({"format": fmt, "rank_one_step_sum_rank": 2, "final_cancellation_is_not_prefix_safe": True,
                          "cumulative_arrival_anchor_preserved_but_not_W0": True, "moving_space_loses_old_anchor": True})
    return {"stored_history_mode_cases": checked, "witnesses": witnesses,
            "scope": "all named 1x2 two-step endpoints in {-1,0,1}; separate higher-dimensional constructions"}


def declared_calls(model, fmt):
    one = round_word(1, fmt)
    return {
        "duplicate_feedback_v1": (("state", (0, 0)), ("state", (one, one)), ("input", (0, 0)), ("input", (one, one))),
        "split_feedback_v1": (("state", (0, 0)), ("state", (one, one)), ("input", (0, 0)), ("input", (one, 0))),
        "shared_axis_v1": (("axis_0", (one, 0)), ("axis_1", (0, one))),
    }[model]


def inspect_endpoint_family(ch, model, fmt, old, palette):
    result = ch.enumerate_endpoint_family(model, fmt, old, palette)
    calls = declared_calls(model, fmt)
    described = tuple((site["id"], tuple(h)) for site in result["descriptor"]["sites"] for h in site["activations"])
    require(described == calls, "Finite registry call coverage changed")
    h = tuple(tuple(word_value(inputs[i], fmt) for _, inputs in calls) for i in range(2))
    targets = tuple(tuple(x) for x in result["targets"])
    target_values = tuple(tuple(word_value(target[i], fmt) for target in targets) for i in range(2))
    old_signature = tuple(affine_reference(old, (0, 0), inputs, fmt) for _, inputs in calls)
    expected_candidates = {tuple(tuple(choice[2 * i + j] for j in range(2)) for i in range(2))
                           for choice in product(palette, repeat=4)}
    seen = set()
    members = {name: set() for name in ("storable", "ALG", "BIT", "ALG_AND_BIT", "ALG_NOT_BIT", "BIT_NOT_ALG")}
    ranks = {name: {} for name in members}
    exact_responses = {name: set() for name in members}
    raw_responses = {name: set() for name in members}
    for row in result["records"]:
        endpoint = tuple(tuple(v) for v in row["endpoint_words"])
        require(endpoint not in seen, "Duplicate endpoint enumeration")
        seen.add(endpoint)
        delta = minus(decode_matrix(endpoint, fmt), decode_matrix(old, fmt))
        alg = all_zero(matmul(delta, h))
        signature = tuple(affine_reference(endpoint, (0, 0), inputs, fmt) for _, inputs in calls)
        bit = signature == old_signature
        require(row["ALG"] == alg and row["BIT"] == bit and row["rank_effective_difference"] == rank(delta),
                "Endpoint classification differs from direct equations/word RNE")
        response = matmul(delta, target_values)
        raw_response = tuple(affine_reference(endpoint, (0, 0), target, fmt) for target in targets)
        require(tuple(tuple(x) for x in row["A_new_output_words"]) == raw_response, "A outputs differ from independent words")
        predicates = {"storable": True, "ALG": alg, "BIT": bit, "ALG_AND_BIT": alg and bit,
                      "ALG_NOT_BIT": alg and not bit, "BIT_NOT_ALG": bit and not alg}
        for name, select in predicates.items():
            if select:
                members[name].add(endpoint)
                r = str(rank(delta))
                ranks[name][r] = ranks[name].get(r, 0) + 1
                exact_responses[name].add(response)
                raw_responses[name].add(raw_response)
    require(seen == expected_candidates and result["enumerated_candidates"] == len(seen),
            "Named Cartesian family not completely enumerated")
    for name in members:
        group = result["groups"][name]
        require(group["endpoints"] == len(members[name]) and group["effective_rank_histogram"] == ranks[name],
                "Finite group count/rank histogram wrong")
        require(group["exact_A_response_image_count"] == len(exact_responses[name]) and
                group["raw_A_response_image_count"] == len(raw_responses[name]), "Finite response-image cardinality wrong")
        require(group["A_execution_refusals"] == 0, "Small finite family unexpectedly has non-total A output")
    return result, members


def check_discrete(ch):
    cases = families = 0
    records = []
    for fmt in ("BF16", "FP32"):
        one = round_word(1, fmt)
        initial = ((one, 0), (0, one))
        for palette_name, values in (("integer", (-1, 0, 1)), ("tiny", (Q(0), constants(fmt)[1], Q(1)))):
            palette = tuple(round_word(v, fmt) for v in values)
            for model in ("duplicate_feedback_v1", "split_feedback_v1", "shared_axis_v1"):
                result, members = inspect_endpoint_family(ch, model, fmt, initial, palette)
                records.append({"format": fmt, "model": model, "palette": palette_name,
                                "counts": {name: len(value) for name, value in members.items()}})
                cases += result["enumerated_candidates"]; families += 1
                if model == "duplicate_feedback_v1" and palette_name == "integer":
                    swapped = ((0, one), (one, 0))
                    other, other_members = inspect_endpoint_family(ch, model, fmt, swapped, palette)
                    require(other["absolute_family_sha256"] == result["absolute_family_sha256"],
                            "Fixed-family comparison silently changed universe")
                    require(other_members["ALG"] == members["ALG"] and other_members["BIT"] == members["BIT"],
                            "Safe fixed-anchor movement consumed absolute equivalence-class members")
                    cases += other["enumerated_candidates"]; families += 1
        zero = ((0, 0), (0, 0))
        separated = ch.enumerate_endpoint_family("duplicate_feedback_v1", fmt, zero, (0,))
        require(separated["groups"]["BIT"]["endpoints"] == 1 and separated["groups"]["E_CERT"]["endpoints"] == 0,
                "Raw BIT equivalence was equated with stronger valid-bank certificate acceptance")
        cases += 1; families += 1
        proposal = ch.xp.matrix(((Q(1, 1 << (precision(fmt) + 1)),),))
        old = ((one,),)
        stalled = ch.quantize_proposal(old, proposal, fmt)
        require(stalled["stored_noop"] and stalled["nonzero_ideal_increment"] and
                tuple(map(tuple, stalled["new_words"])) == old and all_zero(stalled["effective_delta"].rows),
                "Nonzero proposal quantization stall not retained")
        large = Q(1 << precision(fmt))
        changed = ch.quantize_proposal(encode_matrix(((large, 0),), fmt), ch.xp.matrix(((1, -1),)), fmt)
        require(changed["effective_delta"].rows == ((Q(0), Q(-1)),), "Effective endpoint quantization counterexample")
    return {"named_families": families, "enumerated_endpoints": cases, "records": records,
            "scope": "complete named finite palettes only; raw BIT and E_CERT explicitly separated"}


def network_oracle(graph, old, new, old_bounds, new_bounds, fmt, error, state_dimension):
    old_bounds, new_bounds = tuple(old_bounds), tuple(new_bounds)
    gain_total, forcing_total = Q(1), Q(0)
    details = []
    for index, call in enumerate(graph):
        a, b = old[call["bank_id"]], new[call["bank_id"]]
        joint = tuple(max(x, y) for x, y in zip(old_bounds, new_bounds))
        old_next, _ = interval_reference(a, old_bounds, fmt, call["activation"])
        new_next, _ = interval_reference(b, new_bounds, fmt, call["activation"])
        _, errors_old = interval_reference(a, joint, fmt, call["activation"])
        _, errors_new = interval_reference(b, joint, fmt, call["activation"])
        columns = range(state_dimension) if index == 0 else range(len(joint))
        gain = max(sum((abs(word_value(row[j], fmt)) for j in columns), Q(0)) for row in b["weights"])
        drift = max(abs(word_value(nb, fmt) - word_value(ob, fmt)) +
                    sum((abs(word_value(nw, fmt) - word_value(ow, fmt)) * radius
                         for ow, nw, radius in zip(arow, brow, joint)), Q(0))
                    for arow, brow, ob, nb in zip(a["weights"], b["weights"], a["bias"], b["bias"]))
        force = drift + max(errors_old) + max(errors_new)
        error = gain * error + force
        gain_total, forcing_total = gain * gain_total, gain * forcing_total + force
        details.append({"L": gain, "beta": force, "rho_old": max(errors_old), "rho_new": max(errors_new),
                        "old_output_bounds": old_next, "new_output_bounds": new_next})
        old_bounds, new_bounds = old_next, new_next
    return old_bounds, new_bounds, error, gain_total, forcing_total, details


def history_reference(graph, history, schedule, state, inputs, fmt):
    states = [tuple(state)]
    for index, external in zip(schedule, inputs):
        current = states[-1] + tuple(external)
        for call in graph:
            bank = history[index][call["bank_id"]]
            current = affine_reference(bank["weights"], bank["bias"], current, fmt, call["activation"])
        states.append(current)
    return tuple(states)


def inspect_switching(sb, model, fmt, old, new, old_schedule, new_schedule, e0=Q(0), **kwargs):
    result = sb.analyze_model(model, fmt, old, new, old_schedule, new_schedule, initial_error=e0, **kwargs)
    descriptor = sb.model_descriptor(model, fmt)
    old_radius, new_radius = tuple(descriptor["old_initial_bounds"]), tuple(descriptor["new_initial_bounds"])
    inputs, dimension = tuple(descriptor["input_bounds"]), descriptor["state_dimension"]
    errors, gains, forces = [e0], [], []
    for t, (ko, kn, step) in enumerate(zip(old_schedule, new_schedule, result["steps"])):
        a, b, error, gain, force, calls = network_oracle(descriptor["graph"], old[ko], new[kn],
            old_radius + inputs, new_radius + inputs, fmt, errors[-1], dimension)
        require(step["execution_time"] == t and step["old_update_index"] == ko and step["new_update_index"] == kn,
                "Patch and execution indices conflated")
        require(step["L"] == gain and step["beta"] == force and step["next_error"] == error,
                "Switching coefficients differ from independent endpoint proof")
        for actual, expected in zip(step["network_proof"]["calls"], calls):
            require(actual["L"] == expected["L"] and actual["rho_old"] == expected["rho_old"] and
                    actual["rho_new"] == expected["rho_new"], "Switching call gain/rounding omitted")
        require(tuple(result["old_state_tube"][t + 1]) == a and tuple(result["new_state_tube"][t + 1]) == b,
                "Endpoint tube differs from independent interval propagation")
        old_radius, new_radius = a, b
        errors.append(error); gains.append(gain); forces.append(force)
    require(tuple(result["error_bounds"]) == tuple(errors) and result["observed_bound"] == max(errors),
            "Switching prefix observation mismatch")
    require(result["final_error_bound"] == direct_product_sum(gains, forces, e0), "Changing-history product sum mismatch")
    require(tuple(result["new_zero_runtime_versions"]) == tuple(k for k in range(len(new)) if k not in new_schedule),
            "Skipped or unused versions silently dropped")
    return result


def check_switching(sb):
    analyses = trajectories = family_pairs = 0
    refusals, witnesses = [], []
    for fmt in ("BF16", "FP32"):
        model = "scalar_switching_v1"
        first = sb.initial_banks(model, fmt)
        second = copy.deepcopy(first)
        second["dynamics"]["bias"] = (round_word(Q(1, 32), fmt),)
        tail = copy.deepcopy(first)
        tail["dynamics"]["weights"] = encode_matrix(((Q(1, 4), Q(1, 8)),), fmt)
        new = (first, second, first, tail)
        old = (first,)
        graph = sb.model_descriptor(model, fmt)["graph"]
        schedules = tuple(x for x in product(range(3), repeat=3) if all(a <= b for a, b in zip(x, x[1:])))
        histories = tuple(tuple((round_word(x, fmt),) for x in h) for h in product((-1, 0, 1), repeat=3))
        for schedule in schedules:
            result = inspect_switching(sb, model, fmt, old, new, (0, 0, 0), schedule, Q(1, 2),
                                       comparison="original_reference")
            analyses += 1
            for initial_pair, inputs in product(((Q(0), Q(0)), (Q(-1, 4), Q(1, 4))), histories):
                a0, b0 = tuple(round_word(x, fmt) for x in initial_pair)
                a = history_reference(graph, old, (0, 0, 0), (a0,), inputs, fmt)
                b = history_reference(graph, new, schedule, (b0,), inputs, fmt)
                observed = sb.compare_model_traces(model, fmt, old, new, (0, 0, 0), schedule,
                    (a0,), (b0,), inputs, initial_error=Q(1, 2), comparison="original_reference")
                require(tuple(observed["old_trace"]["states"]) == a and tuple(observed["new_trace"]["states"]) == b,
                        "Changing-bank trajectory differs from independent RNE")
                errors = tuple(abs(word_value(x[0], fmt) - word_value(y[0], fmt)) for x, y in zip(a, b))
                require(tuple(observed["actual_error_bounds"]) == errors and
                        all(error <= bound for error, bound in zip(errors, result["error_bounds"])),
                        "Actual switching errors escape declared per-prefix bound")
                trajectories += 1
        common = inspect_switching(sb, model, fmt, old, new, (0, 0, 0), (0, 1, 2), Q(1, 2),
                                    comparison="original_reference", method="common_invariant", state_box=(Q(2),))
        family = common["common_family_proof"]
        modes = family["family"]
        require(family["mode_count"] == 3 and family["ordered_pair_count"] == 9,
                "Common family lost an unused endpoint or ordered pair")
        gains, forces = [], []
        for i, a in enumerate(modes):
            ao, an, *_ = network_oracle(graph, a, a, (Q(2), Q(1)), (Q(2), Q(1)), fmt, Q(0), 1)
            require(max(ao + an) <= 2, "Common mode does not preserve its box")
            for j, b in enumerate(modes):
                _, _, _, gain, force, _ = network_oracle(graph, a, b, (Q(2), Q(1)), (Q(2), Q(1)), fmt, Q(0), 1)
                gains.append(gain); forces.append(force); family_pairs += 1
        require(family["uniform_L"] == max(gains) and family["uniform_beta"] == max(forces) and
                common["uniform_in_time_bound"] == max(Q(1, 2), max(forces) / (1 - max(gains))),
                "Common-norm uniform envelope differs from independent pair analysis")
        analyses += 1
        expect_refusal(lambda: sb.analyze_model(model, fmt, old, new, (0,), (0,), method="common_invariant",
                       state_box=(Q(2),), common_family=(first, second)), fmt + ":unused_family_version_omitted", refusals)
        expect_refusal(lambda: sb.analyze_model(model, fmt, old, new, (0, 0), (1, 0)), fmt + ":decreasing_version", refusals)
        expect_refusal(lambda: sb.analyze_model(model, fmt, old, new, (0,), (1,), comparison="adjacent_endpoints"),
                       fmt + ":wrong_adjacent_reference", refusals)
        ledger = sb.budget_ledger((Q(0), Q(1), Q(0)), Q(1, 2))
        require(ledger["accepted"] is False and ledger["first_exhausted_index"] == 1 and
                ledger["observed_bound"] == 1, "Final cancellation erased earlier budget excess")
        expect_refusal(lambda: sb.analyze_model(model, fmt, old, new, (), (), initial_error=Q(1, 2), budget=Q(1, 4)),
                       fmt + ":initial_time_budget_excess", refusals)
        # Stable nilpotent modes in separate norms; their alternating product grows.
        A, B = ((Q(0), Q(2)), (Q(0), Q(0))), ((Q(0), Q(0)), (Q(2), Q(0)))
        require(all_zero(matmul(A, A)) and all_zero(matmul(B, B)) and matmul(B, A) == ((0, 0), (0, 4)),
                "Nilpotent switching witness algebra")
        nil_model = "nilpotent_switching_v1"
        modes_n = tuple({"dynamics": {"weights": encode_matrix(x, fmt), "bias": (0, 0)}} for x in (A, B))
        history = (modes_n[0], modes_n[1]) * 3
        zero = ({"dynamics": {"weights": encode_matrix(zeros(2, 2), fmt), "bias": (0, 0)}},)
        proof = inspect_switching(sb, nil_model, fmt, zero, history, (0,) * 6, tuple(range(6)))
        initial = (0, round_word(Q(1, 8), fmt))
        inputs = ((),) * 6
        direct = history_reference(sb.model_descriptor(nil_model, fmt)["graph"], history, tuple(range(6)), initial, inputs, fmt)
        require(tuple(word_value(x, fmt) for x in direct[-1]) == (0, 8), "Finite nilpotent switching growth")
        actual = sb.compare_model_traces(nil_model, fmt, zero, history, (0,) * 6, tuple(range(6)), initial, initial, inputs)
        require(tuple(actual["new_trace"]["states"]) == direct and actual["actual_observed_difference"] == 8 and
                proof["observed_bound"] >= 8, "Nilpotent actual/bound comparison")
        analyses += 1; trajectories += 1
        expect_refusal(lambda: sb.analyze_model(nil_model, fmt, zero, history, (0,), (0,),
                       method="common_invariant", state_box=(Q(1), Q(1))), fmt + ":separate_stability_not_common_box", refusals)
        for nonlinear in ("relu_scalar_switching_v1", "shared_relu_switching_v1"):
            nfirst = sb.initial_banks(nonlinear, fmt)
            nsecond = copy.deepcopy(nfirst)
            key = next(iter(nsecond))
            dimension = sb.model_descriptor(nonlinear, fmt)["state_dimension"]
            nsecond[key]["bias"] = tuple(round_word(Q(1 if i == 0 else -1, 32), fmt) for i in range(dimension))
            nh = (nfirst, nsecond)
            radius = Q(1, 2) if dimension == 1 else Q(0)
            nproof = inspect_switching(sb, nonlinear, fmt, (nfirst,), nh, (0, 0, 0), (0, 1, 1),
                                      radius, comparison="original_reference")
            if dimension == 1:
                fixtures = tuple(((round_word(Q(-1, 4), fmt),), (round_word(Q(1, 4), fmt),), h)
                                 for h in histories)
            else:
                fixtures = tuple((tuple(round_word(x, fmt) for x in s), tuple(round_word(x, fmt) for x in s), ((),) * 3)
                                 for s in ((Q(1, 8), 0), (0, Q(1, 8)), (Q(-1, 8), Q(1, 8))))
            for left, right, inp in fixtures:
                graph_n = sb.model_descriptor(nonlinear, fmt)["graph"]
                a = history_reference(graph_n, (nfirst,), (0, 0, 0), left, inp, fmt)
                b = history_reference(graph_n, nh, (0, 1, 1), right, inp, fmt)
                observed = sb.compare_model_traces(nonlinear, fmt, (nfirst,), nh, (0, 0, 0), (0, 1, 1),
                                                   left, right, inp, radius, comparison="original_reference")
                require(tuple(observed["old_trace"]["states"]) == a and tuple(observed["new_trace"]["states"]) == b,
                        "Nonlinear/shared changing-history words differ")
                require(all(error <= bound for error, bound in zip(observed["actual_error_bounds"], nproof["error_bounds"])),
                        "Nonlinear/shared trajectory escapes bound")
                trajectories += 1
            analyses += 1
        witnesses.append({"format": fmt, "nilpotent_six_tick_state": ["0", "8"],
                          "prefix_budget_first_violation": 1, "unused_versions_bound": True})
    return {"analyses": analyses, "complete_named_schedule_input_initial_pairs": trajectories,
            "common_family_ordered_pair_oracles": family_pairs, "expected_refusals": refusals,
            "witnesses": witnesses,
            "scope": "all named monotone three-tick schedules and ternary inputs plus finite switching witnesses"}


def check_receipts(sc, sb, us, runtime):
    cu, ok = runtime.load_b1("constrained_updates"), runtime.load_b1("optimizer_kernel")
    records, refusals = [], []
    for fmt in ("BF16", "FP32"):
        config = cu.OptimizerConfig("adamw", Q(1), beta1=Q(0), beta2=Q(0), epsilon=Q(7))
        owner = us.SequenceKernel(fmt, config)
        gradient = cu.Matrix(((0, 0, Q(1)), (0, 0, Q(-1))), 3)
        owner.commit(owner.prepare(ok.optimizer_request(gradient, "structural")))
        owner.tick(round_word(1, fmt))
        live = owner.snapshot()
        external = {"kind": "B4_exact_D_identity_only", "snapshot": live}
        primary = None
        for model in ("scalar_switching_v1", "relu_scalar_switching_v1",
                      "nilpotent_switching_v1", "shared_relu_switching_v1"):
            first = sb.initial_banks(model, fmt)
            second = copy.deepcopy(first)
            key = next(iter(second))
            second[key]["bias"] = tuple(round_word(Q(1, 64), fmt) for _ in second[key]["bias"])
            old, new, so, sn = (first,), (first, second), (0, 0), (0, 1)
            proof = inspect_switching(sb, model, fmt, old, new, so, sn, comparison="original_reference")
            budget = proof["observed_bound"] + 1
            dim = sb.model_descriptor(model, fmt)["state_dimension"]
            options = {"comparison": "original_reference", "version": 3,
                       "initial_pair": ((0,) * dim, (0,) * dim), "external_context": external}
            text = sc.make_sequence_certificate(model, fmt, old, new, so, sn, budget, **options)
            receipt = sc.check_sequence_certificate(text, model, fmt, old, new, so, sn, budget, **options)
            payload = json.loads(text)["payload"]
            require(receipt["accepted_numerical_evidence"] is True and
                    all(receipt[name] is False for name in ("authorizes_commit", "claims_BIT",
                                                           "claims_exact_ALG", "claims_program_noninterference")),
                    "Numerical receipt acquired protected publication authority")
            require(Q(*receipt["bound"]) == proof["observed_bound"] and
                    payload["horizon"] == 2 and payload["same_input_history"] is True and
                    payload["domain_provenance"]["samples"] is False,
                    "Receipt changed initial/history/domain observation scope")
            require(owner.snapshot() == live, "Numerical analysis mutated external owner")
            records.append({"model": model, "format": fmt, "method": "tube", "horizon": 2,
                            "bound": str(proof["observed_bound"]), "budget": str(budget)})
            if model == "scalar_switching_v1":
                primary = (text, model, old, new, so, sn, budget, options)
                common_options = dict(options, method="common_invariant", state_box=Q(2))
                common = inspect_switching(sb, model, fmt, old, new, so, sn,
                    comparison="original_reference", method="common_invariant", state_box=(Q(2),))
                common_budget = common["observed_bound"] + 1
                ct = sc.make_sequence_certificate(model, fmt, old, new, so, sn, common_budget, **common_options)
                cr = sc.check_sequence_certificate(ct, model, fmt, old, new, so, sn, common_budget, **common_options)
                require(Q(*cr["bound"]) == common["observed_bound"] and cr["authorizes_commit"] is False,
                        "Common invariant receipt mismatch")
                records.append({"model": model, "format": fmt, "method": "common_invariant", "horizon": 2,
                                "bound": str(common["observed_bound"]), "budget": str(common_budget)})
        text, model, old, new, so, sn, budget, options = primary
        mutations = {
            "unused_history": lambda p: p["new_history"].append(copy.deepcopy(p["new_history"][0])),
            "schedule": lambda p: p["new_schedule"].__setitem__(1, 0),
            "domain_samples": lambda p: p["domain_provenance"].__setitem__("samples", True),
            "reference": lambda p: p.__setitem__("comparison", "adjacent_endpoints"),
            "first_state": lambda p: p["initial_pair"][1].__setitem__(0, round_word(Q(1, 2), fmt)),
            "proof_bound": lambda p: p["proof"].__setitem__("observed_bound", [0, 1]),
            "live_authority": lambda p: p.__setitem__("authorizes_commit", True),
            "external_moment": lambda p: p["external_context"]["snapshot"]["kernel"]["optimizer_state"]["m"]["rows"][0].__setitem__(2, [99, 1]),
        }
        for label, change in mutations.items():
            packet = json.loads(text)
            change(packet["payload"])
            packet["payload_sha256"] = hashlib.sha256(canonical(packet["payload"]).encode()).hexdigest()
            expect_refusal(lambda packet=packet: sc.check_sequence_certificate(canonical(packet), model, fmt,
                           old, new, so, sn, budget, **options), fmt + ":numeric_" + label, refusals)
            require(owner.snapshot() == live, "Receipt tampering modified combined owner")
        stale = dict(options, version=4)
        expect_refusal(lambda: sc.check_sequence_certificate(text, model, fmt, old, new, so, sn, budget, **stale),
                       fmt + ":numeric_stale_version", refusals)
        expect_refusal(lambda: owner.commit(text), fmt + ":numeric_receipt_not_B4_commit", refusals)
        require(owner.snapshot() == live, "Numeric receipt changed B4 nonzero moments or ledger")
        expect_refusal(lambda: sc.make_sequence_certificate(model, fmt, old, new, so, sn, 0, **options),
                       fmt + ":positive_bound_zero_budget", refusals)
        bad = dict(options, initial_pair=((0,), (round_word(Q(1, 2), fmt),)))
        expect_refusal(lambda: sc.make_sequence_certificate(model, fmt, old, new, so, sn, budget, **bad),
                       fmt + ":initial_pair_outside_zero_relation", refusals)
        zero_options = {"initial_error": Q(1, 2), "initial_pair": ((0,), (round_word(Q(1, 2), fmt),))}
        zt = sc.make_sequence_certificate(model, fmt, old, new, (), (), Q(1, 2), **zero_options)
        zr = sc.check_sequence_certificate(zt, model, fmt, old, new, (), (), Q(1, 2), **zero_options)
        require(Q(*zr["bound"]) == Q(1, 2) and zr["horizon"] == 0,
                "Zero-horizon receipt omitted nonzero initial relation")
        records.append({"model": model, "format": fmt, "method": "tube", "horizon": 0,
                        "bound": "1/2", "budget": "1/2"})
    return {"accepted_readonly_receipts": len(records), "records": records,
            "expected_refusals": refusals, "nonzero_moment_full_B4_rollback_fixtures": 2,
            "scope": "complete registered-domain proofs; external exact-D snapshot is identity only, not a state mapping"}


def check_frozen_b1():
    path = ROOT.parent / "p2_b1" / "training_results.json"
    require(digest(path) == "b417741ab974752d7858c978bc75197f3199312e9bdf118c232dcbd8cef7cfb1",
            "Frozen B1 trajectory evidence changed")
    data = json.loads(path.read_text())
    count = calls = 0
    for run in data["runs"]:
        if not run["safe_live_route"]:
            continue
        for step in run["records"]:
            if step["status"] != "refused":
                continue
            fmt = run["format"]
            old, new = tuple(map(tuple, step["old_weights"])), tuple(map(tuple, step["candidate_weights"]))
            delta = minus(decode_matrix(new, fmt), decode_matrix(old, fmt))
            require(not all_zero(matmul(delta, ((Q(1),), (Q(1),)))) and rank(delta) == 2,
                    "Frozen refusal was recast as exact annihilation")
            for q, u in product((0, round_word(1, fmt)), repeat=2):
                for v in (q, u):
                    a = affine_reference(old, (0, 0), (v, v), fmt)
                    b = affine_reference(new, (0, 0), (v, v), fmt)
                    require(a == b == (v, v), "Frozen refused proposal changed its registered D output")
                calls += 1
            count += 1
    target = [r for r in data["runs"] if r["safe_live_route"] and r["format"] == "FP32" and
              r["optimizer"] == "adamw" and r["model"] == "duplicate_feedback_v1"]
    require(count == 21 and len(target) == 1 and target[0]["accepted_commits"] == 0 and
            target[0]["refused_attempts"] == 8 and Q(target[0]["final_loss"]) == Q(5, 2),
            "Frozen FP32 AdamW 0/8 fact changed")
    return {"source": str(path), "sha256": digest(path), "refused_pairs_redecoded": count,
            "complete_state_input_pairs": calls, "all_BIT_equal_but_ALG_false": True,
            "FP32_AdamW_accepted": 0, "FP32_AdamW_refused": 8, "FP32_AdamW_final_loss": "5/2",
            "optimizer_reexecuted": False, "prior_verifier_imported": False}


def main():
    global CHECKS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "independent_results.json")
    args = parser.parse_args()
    start = time.perf_counter()
    CHECKS = 0
    word_value.cache_clear(); round_word.cache_clear()
    result = {"schema": "dmwk-p2-b4-independent-v1", "status": "running", "seed": SEED,
              "started_utc": datetime.now(timezone.utc).isoformat(), "sections": {}, "section_seconds": {},
              "prior_stage_suites_rerun": False, "prior_optimizer_trajectories_regenerated": False,
              "SMT_queries": 0, "proof_assistant_checked": False, "P2_C1_started": False}
    phase = "preflight"
    try:
        require(__debug__, "Run independent verification without -O/-OO")
        require(Path(__file__).resolve() == ROOT / "verify_independent.py", "Wrong independent source")
        paths = sorted(ROOT.glob("*.py"))
        before = {p.name: digest(p) for p in paths}
        result["source_sha256"] = before
        evidence = ("capacity_results.json", "switching_results.json", "transaction_results.json")
        result["producer_sha256"] = {p: digest(ROOT / p) for p in evidence}
        runtime = load_current("b4_runtime")
        ch = load_current("capacity_history")
        sb = load_current("switching_bounds")
        us = load_current("update_sequence")
        sc = load_current("sequence_certificate")
        result["environment"] = runtime.environment_metadata()
        sections = (("algebra", lambda: check_algebra(ch)),
                    ("stored_histories", lambda: check_histories(ch)),
                    ("finite_endpoint_families", lambda: check_discrete(ch)),
                    ("exact_D_transactions", lambda: check_sequence(us, runtime)),
                    ("switching", lambda: check_switching(sb)),
                    ("readonly_receipts", lambda: check_receipts(sc, sb, us, runtime)),
                    ("frozen_B1", check_frozen_b1))
        for phase, function in sections:
            before_count, t0 = CHECKS, time.perf_counter()
            result["sections"][phase] = function()
            result["sections"][phase]["checks"] = CHECKS - before_count
            result["section_seconds"][phase] = time.perf_counter() - t0
        phase = "postflight"
        require(before == {p.name: digest(p) for p in paths}, "Source changed during independent run")
        require(result["producer_sha256"] == {p: digest(ROOT / p) for p in evidence},
                "Producer evidence changed during independent run")
        loaded = sorted({str(Path(m.__file__).resolve()) for m in tuple(sys.modules.values())
                         if getattr(m, "__file__", None) and str(Path(m.__file__).resolve()).startswith("/workspace/")
                         and Path(m.__file__).name.startswith("verify")})
        require(all(Path(p).parent == ROOT or p == "/workspace/p1_a1/verify_gates.py" for p in loaded),
                "A predecessor verification suite was imported")
        result["verification_module_paths"] = loaded
        result["pure_P1_backend_exception"] = "/workspace/p1_a1/verify_gates.py"
        result["checks"] = CHECKS
        result["expected_refusals"] = sum(len(v.get("expected_refusals", [])) for v in result["sections"].values())
        result["unexpected_failures"] = 0
        result["status"] = "passed"
    except Exception as exc:
        result["status"] = "failed"
        result["checks"] = CHECKS
        result["failure"] = {"phase": phase, "type": type(exc).__name__, "message": str(exc)}
        result["unexpected_failures"] = 1
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    result["total_seconds"] = time.perf_counter() - start
    result["evidence_scope"] = {
        "oracles": "Own exact minors/direct equations, word RNE search, interval recurrences and weighted product sums.",
        "counts": "Checks include reference-domain guards; named case counts are recorded per section.",
        "finite": "Named small families and histories only; no exhaustive all-format or all-program verification.",
        "excluded": "GPU, native BF16, general concurrency/crash safety, arbitrary compiler optimizations and universal learning."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "checks": result["checks"],
                      "seconds": result["total_seconds"], "failure": result.get("failure"),
                      "output": str(args.output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
