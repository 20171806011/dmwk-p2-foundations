"""B4 exact-rational envelopes for explicit stored-endpoint histories.

Update index k and execution time t remain separate. Every tick rebuilds
joint old/new domains and both arithmetic-error accounts. No result here
authorizes a live update or weakens exact deterministic protection.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json

from b4_runtime import get_fp, load_b3, load_b2

pb = load_b3("propagation_bounds")
cb = load_b2("certified_bounds")
POLICY = pb.POLICY
SCHEDULE = "p2-b4-monotone-version-indexed-synchronous-ticks-v1"
MAX_HORIZON = 64
MAX_VERSIONS = 128
MAX_FAMILY = 16


class SwitchingRefused(ValueError):
    """A required domain, endpoint, schedule or numerical premise failed."""


class BudgetExceeded(SwitchingRefused):
    def __init__(self, ledger):
        self.ledger = ledger
        super().__init__("Read-only prefix budget exhausted at time " + str(ledger["first_exhausted_index"]))


def require(ok, message):
    if not ok:
        raise SwitchingRefused(message)


def _q(value):
    require(type(value) in (int, Fraction), "Exact rational scalar required")
    return Fraction(value)


def _nonnegative(value, name):
    value = _q(value)
    require(value >= 0, name + " must be nonnegative")
    return value


def _box(values, dimension, name):
    require(type(values) in (tuple, list) and len(values) == dimension,
            name + " box dimension/type mismatch")
    return tuple(_nonnegative(v, name + " radius") for v in values)


def record(value):
    return pb.record(value)


def _key(value):
    return json.dumps(record(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_key(value).encode("ascii")).hexdigest()


def _network(graph, banks, fmt):
    try:
        return pb.validate_network(graph, banks, fmt)
    except (ValueError, OverflowError) as exc:
        raise SwitchingRefused("Endpoint/graph validation refused: " + str(exc)) from None


def _history(graph, history, fmt):
    require(type(history) in (tuple, list) and 1 <= len(history) <= MAX_VERSIONS,
            "History must contain 1..128 stored endpoint versions")
    result, base = [], None
    for banks in history:
        desc = _network(graph, banks, fmt)
        shapes = {key: (len(bank["weights"]), len(bank["weights"][0]))
                  for key, bank in desc["banks"].items()}
        signature = (desc["physical_bank_ids"], desc["input_dimension"], desc["output_dimension"], shapes)
        require(base is None or signature == base, "A physical bank shape/layout changed between versions")
        base = signature
        result.append(desc["banks"])
    return tuple(result)


def _schedule(values, versions):
    require(type(values) in (tuple, list) and len(values) <= MAX_HORIZON,
            "Schedule must contain 0..64 execution ticks")
    result = tuple(values)
    require(all(type(k) is int and 0 <= k < versions for k in result),
            "Schedule version index is invalid")
    require(all(a <= b for a, b in zip(result, result[1:])),
            "Version schedule must be nondecreasing; mode revisits need new stored versions")
    return result


def _comparison(old, new, old_schedule, new_schedule, comparison):
    require(type(comparison) is str and comparison in (
        "original_reference", "adjacent_endpoints", "two_histories"), "Unknown comparison reference")
    require(len(old_schedule) == len(new_schedule), "Compared histories need the same execution horizon")
    if comparison == "original_reference":
        require(len(old) == 1 and all(k == 0 for k in old_schedule),
                "Original reference must use its single fixed original endpoint")
        require(old[0] == new[0], "New version zero is not the declared original endpoint")
    elif comparison == "adjacent_endpoints":
        require(old == new, "Adjacent comparison requires the same complete stored version history")
        require(all(b == a+1 for a, b in zip(old_schedule, new_schedule)),
                "Each adjacent comparison must select consecutive endpoint versions")


def _layout(graph, old, new, fmt, state_dimension, input_bounds):
    require(type(state_dimension) is int and state_dimension in (1, 2),
            "Reference state dimension must be one or two")
    old_desc, new_desc = _network(graph, old[0], fmt), _network(graph, new[0], fmt)
    require(old_desc["physical_bank_ids"] == new_desc["physical_bank_ids"], "Physical bank IDs differ between histories")
    for key in old_desc["physical_bank_ids"]:
        ao, an = old[0][key]["weights"], new[0][key]["weights"]
        require((len(ao), len(ao[0])) == (len(an), len(an[0])), "Compared bank shapes differ")
    require(old_desc["output_dimension"] == new_desc["output_dimension"] == state_dimension,
            "Complete graph output must be exactly the next-state dimension")
    external = old_desc["input_dimension"]-state_dimension
    require(external >= 0 and new_desc["input_dimension"] == old_desc["input_dimension"],
            "Graph input must concatenate declared state and shared external inputs")
    inputs = _box(input_bounds, external, "External input")
    return old_desc, inputs


def _network_bound(graph, old, new, old_bounds, new_bounds, fmt, error, state_dimension):
    try:
        return pb.network_bound(graph, old, new, old_bounds, new_bounds, fmt,
                                initial_error=error,
                                first_difference_columns=tuple(range(state_dimension)))
    except (ValueError, OverflowError) as exc:
        raise SwitchingRefused("Changing-history joint range/rounding proof refused: " + str(exc)) from None


def _within(values, cap):
    return all(v <= c for v, c in zip(values, cap))


def endpoint_difference(old_banks, new_banks, fmt):
    """Exact differences of validated decoded endpoints; no ideal proposal added."""
    result = {}
    require(type(old_banks) is dict and type(new_banks) is dict and set(old_banks) == set(new_banks),
            "Endpoint difference needs the same physical bank IDs")
    try:
        for key in sorted(old_banks):
            old, new = old_banks[key], new_banks[key]
            A, B = cb.decode_matrix(old["weights"], fmt), cb.decode_matrix(new["weights"], fmt)
            require(A.shape == B.shape, "Endpoint difference shapes differ")
            a, b = cb.decode_vector(old["bias"], fmt), cb.decode_vector(new["bias"], fmt)
            require(len(a) == len(b) == A.nrows, "Endpoint difference bias shapes differ")
            result[key] = {"weights": cb.xp.sub(B, A), "bias": tuple(v-u for u, v in zip(a, b))}
    except (cb.BoundRefused, KeyError) as exc:
        raise SwitchingRefused("Cannot decode endpoint difference: " + str(exc)) from None
    return result


def budget_ledger(error_bounds, budget=None):
    require(type(error_bounds) in (tuple, list) and len(error_bounds) >= 1,
            "Budget ledger needs every prefix including initial time zero")
    values = tuple(_nonnegative(v, "Prefix error bound") for v in error_bounds)
    cap = None if budget is None else _nonnegative(budget, "Absolute infinity budget")
    entries, maxima, peak, first = [], [], Fraction(0), None
    for t, value in enumerate(values):
        peak = max(peak, value)
        maxima.append(peak)
        within = None if cap is None else peak <= cap
        if within is False and first is None:
            first = t
        entries.append({"time": t, "error_bound": value, "prefix_max": peak,
                        "remaining_budget": None if cap is None else cap-peak,
                        "within_budget": within})
    accepted = None if cap is None else first is None
    return {"budget": cap, "budget_requested": cap is not None,
            "entries": entries, "prefix_maxima": tuple(maxima), "observed_bound": peak,
            "accepted": accepted, "budget_satisfied": accepted,
            "first_exhausted_index": first, "includes_initial_time_zero": True,
            "observation": "full state at every time 0..T",
            "scope": "read-only sufficient numerical budget; no live authority",
            "authorizes_commit": False}


def _common_family(graph, old, new, fmt, state_dimension, inputs, cap, family, e0):
    if family is None:
        candidates = old+new
    else:
        candidates = _history(graph, family, fmt)
    modes, keys = [], set()
    for banks in candidates:
        normalized = _network(graph, banks, fmt)["banks"]
        key = _key(normalized)
        if key not in keys:
            modes.append(normalized); keys.add(key)
    require(1 <= len(modes) <= MAX_FAMILY, "Common proof supports 1..16 distinct stored modes")
    require(all(_key(banks) in keys for banks in old+new),
            "Common family omits a declared history version, including unused versions")
    # All modes must implement the same physical layout, including explicitly
    # supplied future modes not yet used by either finite schedule.
    for banks in modes:
        _layout(graph, (old[0],), (banks,), fmt, state_dimension, inputs)
    self_records, pair_records = [], []
    for index, banks in enumerate(modes):
        proof = _network_bound(graph, banks, banks, cap+inputs, cap+inputs, fmt, 0, state_dimension)
        require(_within(proof["old_output_bounds"], cap) and _within(proof["new_output_bounds"], cap),
                "A common-family mode image exits the proposed invariant box")
        self_records.append({"mode": index, "endpoint_sha256": _digest(banks), "proof": proof})
    L, beta = Fraction(0), Fraction(0)
    for i, old_mode in enumerate(modes):
        for j, new_mode in enumerate(modes):
            proof = _network_bound(graph, old_mode, new_mode, cap+inputs, cap+inputs, fmt, 0, state_dimension)
            L, beta = max(L, proof["lipschitz_product"]), max(beta, proof["forcing_bound"])
            pair_records.append({"old_mode": i, "new_mode": j,
                                 "L": proof["lipschitz_product"], "beta": proof["forcing_bound"],
                                 "proof": proof})
    uniform = max(e0, beta/(1-L)) if L < 1 else None
    return {"state_box": cap, "input_bounds": inputs, "family": tuple(modes),
            "mode_count": len(modes), "ordered_pair_count": len(pair_records),
            "mode_inclusion_proofs": self_records, "ordered_pair_proofs": pair_records,
            "all_history_versions_covered": True, "common_invariant_verified": True,
            "common_norm": "linf", "uniform_L": L, "uniform_beta": beta,
            "strict_common_contraction": L < 1, "uniform_in_time_bound": uniform,
            "uniform_scope": ("Every finite continuation selecting only declared family modes, under the same state/input domains and fixed graph/policy; not infinite hardware operation"
                              if uniform is not None else None),
            "no_uniform_contraction_reason": None if L < 1 else "No common infinity-norm gain strictly below one was proved"}


def analyze_switching(graph, old_history, new_history, old_schedule, new_schedule, fmt, *,
                      state_dimension, old_initial_bounds, new_initial_bounds, input_bounds,
                      initial_error=0, comparison="two_histories", method="tube", state_box=None,
                      common_family=None, budget=None):
    old, new = _history(graph, old_history, fmt), _history(graph, new_history, fmt)
    os, ns = _schedule(old_schedule, len(old)), _schedule(new_schedule, len(new))
    _comparison(old, new, os, ns, comparison)
    descriptor, inputs = _layout(graph, old, new, fmt, state_dimension, input_bounds)
    initial_old = _box(old_initial_bounds, state_dimension, "Old initial state")
    initial_new = _box(new_initial_bounds, state_dimension, "New initial state")
    e0 = _nonnegative(initial_error, "Initial paired difference")
    require(type(method) is str and method in ("tube", "common_invariant"), "Unknown switching proof method")
    require(method == "common_invariant" or common_family is None,
            "A declared common family requires the common_invariant proof method")
    cap = None if state_box is None else _box(state_box, state_dimension, "State cap")
    require(method != "common_invariant" or cap is not None, "Common invariant requires an explicit state box")
    require(cap is None or (_within(initial_old, cap) and _within(initial_new, cap)),
            "State cap excludes an admitted initial domain")
    family = (_common_family(graph, old, new, fmt, state_dimension, inputs, cap, common_family, e0)
              if method == "common_invariant" else None)
    old_state, new_state = initial_old, initial_new
    old_tube, new_tube, errors = [initial_old], [initial_new], [e0]
    steps, gains, betas = [], [], []
    for t, (ko, kn) in enumerate(zip(os, ns)):
        proof = _network_bound(descriptor["graph"], old[ko], new[kn], old_state+inputs,
                               new_state+inputs, fmt, errors[-1], state_dimension)
        old_state, new_state = proof["old_output_bounds"], proof["new_output_bounds"]
        require(cap is None or (_within(old_state, cap) and _within(new_state, cap)),
                "A recomputed endpoint tube exits the supplied state cap; no clipping allowed")
        L, beta = proof["lipschitz_product"], proof["forcing_bound"]
        if family is not None:
            require(L <= family["uniform_L"] and beta <= family["uniform_beta"],
                    "Finite-step coefficients exceeded the independently proved common-family envelope")
        gains.append(L); betas.append(beta); errors.append(proof["final_error_bound"])
        old_tube.append(old_state); new_tube.append(new_state)
        steps.append({"execution_time": t, "old_update_index": ko, "new_update_index": kn,
                      "old_endpoint_sha256": _digest(old[ko]), "new_endpoint_sha256": _digest(new[kn]),
                      "actual_endpoint_delta": endpoint_difference(old[ko], new[kn], fmt),
                      "L": L, "beta": beta, "previous_error": errors[-2], "next_error": errors[-1],
                      "network_proof": proof})
    try:
        recurrence = pb.propagate_recurrence(gains, betas, e0)
    except ValueError as exc:
        raise SwitchingRefused("Exact recurrence could not be checked: " + str(exc)) from None
    require(tuple(errors) == recurrence["error_bounds"], "Per-tick propagation and direct product-sum disagree")
    ledger = budget_ledger(errors, budget)
    if ledger["accepted"] is False:
        raise BudgetExceeded(ledger)
    uniform = None if family is None else family["uniform_in_time_bound"]
    require(uniform is None or max(errors) <= uniform, "Finite prefix exceeds certified uniform envelope")
    return {"schema": "dmwk-p2-b4-switching-analysis-v1", "format": fmt,
            "graph": descriptor["graph"], "physical_bank_ids": descriptor["physical_bank_ids"],
            "old_history": old, "new_history": new, "old_schedule": os, "new_schedule": ns,
            "comparison": comparison, "method": method, "horizon": len(os),
            "old_version_count": len(old), "new_version_count": len(new),
            "old_ticks_per_version": tuple(os.count(k) for k in range(len(old))),
            "new_ticks_per_version": tuple(ns.count(k) for k in range(len(new))),
            "old_zero_runtime_versions": tuple(k for k in range(len(old)) if k not in os),
            "new_zero_runtime_versions": tuple(k for k in range(len(new)) if k not in ns),
            "state_dimension": state_dimension, "input_bounds": inputs,
            "initial_relation": {"old_initial_bounds": initial_old, "new_initial_bounds": initial_new,
                                 "linf_difference_at_most": e0, "same_initial_state": e0 == 0,
                                 "scope": "every admitted raw initial pair satisfying both boxes and the stated relation"},
            "initial_error": e0, "error_bounds": tuple(errors), "final_error_bound": errors[-1],
            "observed_bound": max(errors), "old_state_tube": tuple(old_tube), "new_state_tube": tuple(new_tube),
            "Ls": tuple(gains), "betas": tuple(betas), "product_sum": recurrence,
            "steps": steps, "state_box": cap, "common_family_proof": family,
            "common_invariant_verified": family is not None, "uniform_in_time_bound": uniform,
            "budget_ledger": ledger, "norm": "linf", "observation": "full state at every time 0..T",
            "numerical_policy": POLICY, "schedule_policy": SCHEDULE, "schedule": SCHEDULE,
            "domain_containment_proved": True, "totality_proved": True,
            "global_arbitrary_program_domain_verified": False,
            "endpoint_premise": "exact supplied stored snapshots selected by the declared schedule; updates preserve state between ticks",
            "authorizes_commit": False, "claims_BIT": False, "claims_program_noninterference": False}


def model_descriptor(model_id, fmt):
    require(type(fmt) is str and fmt in ("BF16", "FP32"), "Unsupported numerical format")
    require(type(model_id) is str and model_id in (
        "scalar_switching_v1", "relu_scalar_switching_v1", "nilpotent_switching_v1", "shared_relu_switching_v1"),
        "Unknown or uncertified switching model")
    if model_id in ("scalar_switching_v1", "relu_scalar_switching_v1"):
        state_dimension, inputs, init = 1, (Fraction(1),), (Fraction(1),)
        graph = ({"call_id": "state_affine", "bank_id": "dynamics",
                  "activation": "relu" if model_id.startswith("relu") else "identity"},)
        shapes = {"dynamics": (1, 2)}
    elif model_id == "nilpotent_switching_v1":
        state_dimension, inputs, init = 2, (), (Fraction(1, 8),)*2
        graph = ({"call_id": "state_affine", "bank_id": "dynamics", "activation": "identity"},)
        shapes = {"dynamics": (2, 2)}
    else:
        state_dimension, inputs, init = 2, (), (Fraction(1, 4),)*2
        graph = ({"call_id": "shared_relu", "bank_id": "shared", "activation": "relu"},
                 {"call_id": "shared_identity", "bank_id": "shared", "activation": "identity"})
        shapes = {"shared": (2, 2)}
    return {"registry_schema": "dmwk-p2-b4-switching-model-v1", "model_id": model_id, "format": fmt,
            "graph": graph, "physical_bank_shapes": shapes, "state_dimension": state_dimension,
            "old_initial_bounds": init, "new_initial_bounds": init, "input_bounds": inputs,
            "domain_id": model_id+":all-canonical-input-histories-and-initial-box-pairs-v1",
            "input_history": "every finite common canonical raw input history satisfying the coordinate bounds",
            "initial_relation": "all pairs inside the two initial boxes with stated infinity difference bound",
            "state_preparation": "state coordinates first, common external input coordinates last",
            "state_commit": "all next-state coordinates read one old snapshot and commit together",
            "numerical_policy": POLICY, "schedule_policy": SCHEDULE, "schedule": SCHEDULE,
            "version_schedule": "nondecreasing update indices per tick; skipped and repeated versions explicit",
            "observation": "full state at every time 0..T", "norm": "linf",
            "generic_branch_analyzer": False, "authorizes_commit": False}


def initial_banks(model_id, fmt):
    model_descriptor(model_id, fmt)
    fp = get_fp()
    def enc(x): return fp.encode_constant(Fraction(x), fmt)
    if model_id in ("scalar_switching_v1", "relu_scalar_switching_v1"):
        return {"dynamics": {"weights": ((enc(Fraction(1, 2)), enc(Fraction(1, 8))),), "bias": (0,)}}
    if model_id == "nilpotent_switching_v1":
        return {"dynamics": {"weights": ((0, enc(2)), (0, 0)), "bias": (0, 0)}}
    return {"shared": {"weights": ((enc(Fraction(1, 2)), 0), (0, enc(Fraction(1, 2)))), "bias": (0, 0)}}


def _registered_history(descriptor, history, fmt):
    normalized = _history(descriptor["graph"], history, fmt)
    for banks in normalized:
        shapes = {key: (len(bank["weights"]), len(bank["weights"][0])) for key, bank in banks.items()}
        require(shapes == descriptor["physical_bank_shapes"], "Stored history does not match registered physical shapes")
    return normalized


def analyze_model(model_id, fmt, old_history, new_history, old_schedule, new_schedule,
                  initial_error=0, comparison="two_histories", method="tube", state_box=None,
                  common_family=None, budget=None):
    descriptor = model_descriptor(model_id, fmt)
    old = _registered_history(descriptor, old_history, fmt)
    new = _registered_history(descriptor, new_history, fmt)
    family = None if common_family is None else _registered_history(descriptor, common_family, fmt)
    result = analyze_switching(descriptor["graph"], old, new, old_schedule, new_schedule, fmt,
                              state_dimension=descriptor["state_dimension"],
                              old_initial_bounds=descriptor["old_initial_bounds"],
                              new_initial_bounds=descriptor["new_initial_bounds"],
                              input_bounds=descriptor["input_bounds"], initial_error=initial_error,
                              comparison=comparison, method=method, state_box=state_box,
                              common_family=family, budget=budget)
    return {"descriptor": descriptor, **result}


def trace_history(graph, history, schedule, initial_state_words, input_sequence, fmt, *,
                  state_dimension, initial_state_bounds, input_bounds):
    normalized = _history(graph, history, fmt)
    indices = _schedule(schedule, len(normalized))
    descriptor, inputs = _layout(graph, normalized, normalized, fmt, state_dimension, input_bounds)
    initial = _box(initial_state_bounds, state_dimension, "Initial state")
    require(type(initial_state_words) in (tuple, list) and len(initial_state_words) == state_dimension,
            "Point initial state shape/type mismatch")
    require(type(input_sequence) in (tuple, list) and len(input_sequence) == len(indices),
            "Point external input history must match execution horizon")
    state = tuple(initial_state_words)
    try:
        decoded = cb.decode_vector(state, fmt)
        require(all(abs(v) <= b for v, b in zip(decoded, initial)), "Point initial state is outside the declared initial box")
        states, ticks = [state], []
        for t, (index, inp) in enumerate(zip(indices, input_sequence)):
            require(type(inp) in (tuple, list) and len(inp) == len(inputs), "Point external input dimension/type mismatch")
            values = cb.decode_vector(inp, fmt)
            require(all(abs(v) <= b for v, b in zip(values, inputs)), "Point external input is outside the declared domain")
            proof = pb.trace_network(descriptor["graph"], normalized[index], state+tuple(inp), fmt)
            state = proof["output_words"]
            states.append(state)
            ticks.append({"execution_time": t, "update_index": index,
                          "endpoint_sha256": _digest(normalized[index]), "network_trace": proof})
    except (cb.BoundRefused, pb.PropagationRefused, OverflowError) as exc:
        raise SwitchingRefused("Actual changing-history trace refused: " + str(exc)) from None
    return {"format": fmt, "history": normalized, "version_schedule": indices,
            "states": tuple(states), "output_words": state, "ticks": ticks,
            "input_sequence": tuple(tuple(v) for v in input_sequence),
            "initial_state_words": tuple(initial_state_words),
            "numerical_policy": POLICY, "schedule_policy": SCHEDULE,
            "scope": "one explicit finite stored trajectory; no sampled invariant inference",
            "authorizes_commit": False}


def trace_model(model_id, fmt, history, schedule, initial_state_words, input_sequence, side="old"):
    descriptor = model_descriptor(model_id, fmt)
    require(type(side) is str and side in ("old", "new"), "Initial-domain side must be old or new")
    normalized = _registered_history(descriptor, history, fmt)
    result = trace_history(descriptor["graph"], normalized, schedule, initial_state_words, input_sequence, fmt,
                           state_dimension=descriptor["state_dimension"],
                           initial_state_bounds=descriptor[side+"_initial_bounds"],
                           input_bounds=descriptor["input_bounds"])
    return {"descriptor": descriptor, **result}


def compare_model_traces(model_id, fmt, old_history, new_history, old_schedule, new_schedule,
                         old_initial_state_words, new_initial_state_words, input_sequence,
                         initial_error=0, comparison="two_histories"):
    descriptor = model_descriptor(model_id, fmt)
    old, new = _registered_history(descriptor, old_history, fmt), _registered_history(descriptor, new_history, fmt)
    os, ns = _schedule(old_schedule, len(old)), _schedule(new_schedule, len(new))
    _comparison(old, new, os, ns, comparison)
    e0 = _nonnegative(initial_error, "Initial paired difference")
    try:
        xo, xn = cb.decode_vector(old_initial_state_words, fmt), cb.decode_vector(new_initial_state_words, fmt)
    except cb.BoundRefused as exc:
        raise SwitchingRefused(str(exc)) from None
    require(len(xo) == len(xn) == descriptor["state_dimension"], "Compared initial state dimensions differ")
    actual_initial = max(abs(a-b) for a, b in zip(xo, xn))
    require(actual_initial <= e0, "Actual initial pair violates the declared initial difference relation")
    left = trace_model(model_id, fmt, old, os, old_initial_state_words, input_sequence, side="old")
    right = trace_model(model_id, fmt, new, ns, new_initial_state_words, input_sequence, side="new")
    errors, raw_equal = [], []
    for a, b in zip(left["states"], right["states"]):
        av, bv = cb.decode_vector(a, fmt), cb.decode_vector(b, fmt)
        errors.append(max(abs(x-y) for x, y in zip(av, bv)))
        raw_equal.append(a == b)
    return {"descriptor": descriptor, "old_trace": left, "new_trace": right,
            "comparison": comparison, "initial_error_bound": e0,
            "actual_initial_difference": actual_initial, "actual_error_bounds": tuple(errors),
            "actual_observed_difference": max(errors), "raw_state_equal": tuple(raw_equal),
            "same_input_sequence": True, "scope": "one actual paired finite trajectory",
            "authorizes_commit": False}
