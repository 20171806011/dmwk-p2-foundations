"""B3 fixed-endpoint infinity-norm propagation with proved joint domains.

Exact-map Lipschitz constants are never applied directly to rounded staircases.
Both endpoint rounding contributions are retained at every call. All helpers
are pure diagnostics and authorize no live update or change of safety policy.
"""
from __future__ import annotations

from fractions import Fraction

from b3_runtime import get_fp, load_b2

cb = load_b2("certified_bounds")
xp = cb.xp
POLICY = "p2-b3-affine-relu-identity-bias-first-separate-rne-canonical-zero-v1"
SCHEDULE = "p2-b3-fixed-banks-ordered-calls-same-old-state-synchronous-commit-v1"
MAX_HORIZON = 64
MODELS = ("two_layer_relu_v1", "shared_relu_v1", "contractive_scalar_v1",
          "neutral_scalar_v1", "amplifying_scalar_v1")


class PropagationRefused(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise PropagationRefused(message)


def _q(x):
    require(type(x) in (int, Fraction), "Exact rational scalar required")
    return Fraction(x)


def _bounds(values, dimension):
    require(type(values) in (list, tuple) and len(values) == dimension, "Box dimension mismatch")
    answer = tuple(_q(x) for x in values)
    require(all(x >= 0 for x in answer), "Box radii must be nonnegative")
    return answer


def _initial_error(value):
    value = _q(value)
    require(value >= 0, "Initial difference bound must be nonnegative")
    return value


def record(value):
    return cb.record(value)


def _format(fmt):
    require(type(fmt) is str and fmt in ("BF16", "FP32"), "Unsupported numerical format")
    return get_fp().get_format(fmt)


def _bank(value, fmt):
    require(type(value) is dict and set(value) == {"weights", "bias"}, "Physical affine-bank schema mismatch")
    matrix = cb.decode_matrix(value["weights"], fmt)
    require(matrix.nrows > 0 and matrix.ncols > 0, "Positive layer dimensions required")
    require(type(value["bias"]) in (tuple, list) and len(value["bias"]) == matrix.nrows, "Bias shape mismatch")
    cb.decode_vector(value["bias"], fmt)
    return {"weights": tuple(tuple(v for v in row) for row in value["weights"]),
            "bias": tuple(value["bias"])}


def validate_network(graph, banks, fmt):
    _format(fmt)
    require(type(graph) in (tuple, list) and 1 <= len(graph) <= 32, "Reference graph must contain 1..32 calls")
    require(type(banks) is dict and banks and all(type(k) is str and k for k in banks), "Named physical-bank dict required")
    normalized_banks = {key: _bank(value, fmt) for key, value in banks.items()}
    labels, referenced, calls = set(), set(), []
    previous_width = None
    first_input = None
    for call in graph:
        require(type(call) is dict and set(call) == {"call_id", "bank_id", "activation"}, "Call schema mismatch")
        call_id, bank_id, activation = call["call_id"], call["bank_id"], call["activation"]
        require(type(call_id) is str and call_id and call_id not in labels, "Call IDs must be nonempty and unique")
        require(type(bank_id) is str and bank_id in normalized_banks, "Missing physical bank at a call")
        require(type(activation) is str and activation in ("identity", "relu"), "Unsupported nonlinearity")
        A = cb.decode_matrix(normalized_banks[bank_id]["weights"], fmt)
        require(previous_width is None or previous_width == A.ncols, "Adjacent layer shape mismatch")
        if first_input is None:
            first_input = A.ncols
        previous_width = A.nrows
        labels.add(call_id); referenced.add(bank_id)
        calls.append({"call_id": call_id, "bank_id": bank_id, "activation": activation})
    require(referenced == set(normalized_banks), "Unreferenced or omitted physical banks are not admitted")
    return {"graph": tuple(calls), "banks": normalized_banks, "input_dimension": first_input,
            "output_dimension": previous_width, "physical_bank_ids": tuple(sorted(referenced)),
            "numerical_policy": POLICY, "schedule": SCHEDULE, "norm": "linf"}


def _act(values, activation):
    return tuple(max(Fraction(0), x) for x in values) if activation == "relu" else tuple(values)


def _linear(A, h, b):
    return tuple(bi+sum((w*x for w, x in zip(row, h)), Fraction(0)) for row, bi in zip(A.rows, b))


def trace_network(graph, banks, input_words, fmt):
    descriptor = validate_network(graph, banks, fmt)
    decoded = cb.decode_vector(input_words, fmt)
    require(len(decoded) == descriptor["input_dimension"], "Network input shape mismatch")
    words, exact = tuple(input_words), decoded
    calls = []
    try:
        for call in descriptor["graph"]:
            bank = descriptor["banks"][call["bank_id"]]
            trace = cb.trace_affine(bank["weights"], words, fmt, bank["bias"])
            affine_words = trace["output_words"]
            if call["activation"] == "relu":
                output = tuple(w if v > 0 else 0 for w, v in zip(affine_words, trace["decoded_output"]))
            else:
                output = affine_words
            A, b = cb.decode_matrix(bank["weights"], fmt), cb.decode_vector(bank["bias"], fmt)
            exact_affine = _linear(A, exact, b)
            exact_output = _act(exact_affine, call["activation"])
            calls.append({**call, "input_words": words, "affine_trace": trace, "output_words": output,
                          "exact_input": exact, "exact_affine": exact_affine, "exact_output": exact_output,
                          "nonlinearity_additional_rounding_error": Fraction(0)})
            words, exact = output, exact_output
    except (ValueError, OverflowError) as exc:
        raise PropagationRefused("Actual graph execution could not be verified: " + str(exc)) from None
    return {"input_words": tuple(input_words), "output_words": tuple(words), "decoded_output": cb.decode_vector(words, fmt),
            "exact_output": exact, "calls": calls, "numerical_policy": POLICY,
            "scope": "one actual input only; no sampled-domain extrapolation"}


def propagate_recurrence(Ls, betas, initial_error=0):
    require(type(Ls) in (tuple, list) and type(betas) in (tuple, list) and len(Ls) == len(betas), "Recurrence sequence mismatch")
    gains, forcing = tuple(_q(x) for x in Ls), tuple(_q(x) for x in betas)
    require(all(x >= 0 for x in gains+forcing), "Recurrence coefficients must be nonnegative")
    e0 = _initial_error(initial_error)
    series = [e0]
    for L, beta in zip(gains, forcing):
        series.append(L*series[-1]+beta)
    products = []
    for stop in range(len(gains)+1):
        multiplier = Fraction(1)
        for gain in gains[:stop]: multiplier *= gain
        value = multiplier*e0
        for j in range(stop):
            tail = Fraction(1)
            for gain in gains[j+1:stop]: tail *= gain
            value += forcing[j]*tail
        products.append(value)
    require(tuple(products) == tuple(series), "Direct product-sum and recurrence disagree")
    return {"Ls": gains, "betas": forcing, "initial_error": e0, "error_bounds": tuple(series),
            "final_error_bound": series[-1], "product_sum_final": products[-1],
            "product_sum_prefixes": tuple(products), "scope": "algebra only; coefficient/domain provenance required"}


def constant_recurrence(L, beta, horizon, initial_error=0):
    L, beta, e0 = _q(L), _q(beta), _initial_error(initial_error)
    require(L >= 0 and beta >= 0, "Negative recurrence coefficient")
    require(type(horizon) is int and 0 <= horizon <= MAX_HORIZON, "Unsupported bounded reference horizon")
    proof = propagate_recurrence((L,)*horizon, (beta,)*horizon, e0)
    power = L**horizon
    forcing_sum = Fraction(horizon) if L == 1 else (1-power)/(1-L)
    closed = power*e0+beta*forcing_sum
    require(closed == proof["final_error_bound"], "Constant geometric formula failed")
    return {**proof, "L": L, "beta": beta, "horizon": horizon, "forcing_sum": forcing_sum,
            "closed_form": closed, "regime": "contractive" if L < 1 else ("neutral" if L == 1 else "amplifying"),
            "uniform_in_time_claim": False}


def _output_enclosure(bank, bounds, fmt, activation):
    proof = cb.box_bound(bank["weights"], bank["weights"], bounds, fmt,
                         old_bias=bank["bias"], new_bias=bank["bias"])["old_range_proof"]
    A, b = cb.decode_matrix(bank["weights"], fmt), cb.decode_vector(bank["bias"], fmt)
    intervals, output_bounds = [], []
    for row, bias, rp in zip(A.rows, b, proof["rows"]):
        radius = sum((abs(w)*h for w, h in zip(row, bounds)), Fraction(0))
        rho, magnitude = rp["row_error_bound"], rp["output_magnitude_bound"]
        lower = max(-magnitude, bias-radius-rho)
        upper = min(magnitude, bias+radius+rho)
        require(lower <= upper, "Certified endpoint range intersection is empty")
        activated = (max(Fraction(0), lower), max(Fraction(0), upper)) if activation == "relu" else (lower, upper)
        out = max(abs(activated[0]), abs(activated[1]))
        intervals.append({"affine_lower": lower, "affine_upper": upper,
                          "output_lower": activated[0], "output_upper": activated[1],
                          "output_magnitude_bound": out})
        output_bounds.append(out)
    return {"input_bounds": tuple(bounds), "output_bounds": tuple(output_bounds),
            "signed_ranges": intervals, "operation_range_proof": proof}


def network_bound(graph, old_banks, new_banks, old_input_bounds, new_input_bounds, fmt,
                  initial_error=0, first_difference_columns=None):
    old_desc = validate_network(graph, old_banks, fmt)
    new_desc = validate_network(graph, new_banks, fmt)
    require(old_desc["physical_bank_ids"] == new_desc["physical_bank_ids"], "Endpoint physical bank IDs differ")
    for key in old_desc["physical_bank_ids"]:
        require(cb.decode_matrix(old_desc["banks"][key]["weights"], fmt).shape ==
                cb.decode_matrix(new_desc["banks"][key]["weights"], fmt).shape, "Endpoint bank shapes differ")
    dimension = old_desc["input_dimension"]
    old_h, new_h = _bounds(old_input_bounds, dimension), _bounds(new_input_bounds, dimension)
    initial_old, initial_new = old_h, new_h
    if first_difference_columns is None:
        first_columns = tuple(range(dimension))
    else:
        require(type(first_difference_columns) in (tuple, list), "Difference-column relation must be explicit")
        first_columns = tuple(first_difference_columns)
        require(all(type(j) is int and 0 <= j < dimension for j in first_columns)
                and len(set(first_columns)) == len(first_columns), "Invalid differing-coordinate relation")
    e0 = _initial_error(initial_error)
    error = e0
    product, forcing = Fraction(1), Fraction(0)
    calls, Ls, betas = [], [], []
    try:
        for index, call in enumerate(old_desc["graph"]):
            key = call["bank_id"]
            old, new = old_desc["banks"][key], new_desc["banks"][key]
            joint = tuple(max(a, b) for a, b in zip(old_h, new_h))
            joint_proof = cb.box_bound(old["weights"], new["weights"], joint, fmt,
                                       old_bias=old["bias"], new_bias=new["bias"])
            old_range = _output_enclosure(old, old_h, fmt, call["activation"])
            new_range = _output_enclosure(new, new_h, fmt, call["activation"])
            Wnew = cb.decode_matrix(new["weights"], fmt)
            columns = first_columns if index == 0 else tuple(range(Wnew.ncols))
            L = max((sum((abs(row[j]) for j in columns), Fraction(0)) for row in Wnew.rows), default=Fraction(0))
            drift = max(joint_proof["algebraic_coordinate_bounds"], default=Fraction(0))
            rho_old = joint_proof["old_range_proof"]["rho_linf"]
            rho_new = joint_proof["new_range_proof"]["rho_linf"]
            beta = drift+rho_old+rho_new
            next_error = L*error+beta
            calls.append({**call, "old_input_bounds": old_h, "new_input_bounds": new_h,
                          "joint_input_bounds": joint, "old_output_bounds": old_range["output_bounds"],
                          "new_output_bounds": new_range["output_bounds"], "L": L,
                          "lipschitz_map": "exact new affine/nonlinear map; not its rounded staircase",
                          "differing_columns": columns, "same_input_exact_drift": drift,
                          "rho_old": rho_old, "rho_new": rho_new, "beta": beta,
                          "previous_error": error, "next_error": next_error,
                          "old_range": old_range, "new_range": new_range,
                          "joint_operation_range_proof": joint_proof})
            old_h, new_h = old_range["output_bounds"], new_range["output_bounds"]
            product, forcing = L*product, L*forcing+beta
            error = next_error
            Ls.append(L); betas.append(beta)
    except (ValueError, OverflowError) as exc:
        raise PropagationRefused("Joint domain/range propagation refused: " + str(exc)) from None
    recurrence = propagate_recurrence(Ls, betas, e0)
    require(error == product*e0+forcing == recurrence["final_error_bound"], "Network recurrence mismatch")
    return {"norm": "linf", "graph": old_desc["graph"], "physical_bank_ids": old_desc["physical_bank_ids"],
            "old_input_bounds": initial_old, "new_input_bounds": initial_new,
            "old_output_bounds": old_h, "new_output_bounds": new_h,
            "error_bounds": recurrence["error_bounds"], "final_error_bound": error,
            "lipschitz_product": product, "forcing_bound": forcing, "recurrence": recurrence,
            "calls": calls, "domain_containment_proved": True, "totality_proved": True,
            "first_difference_columns": first_columns,
            "relation_premise": "initial differences bounded by E0, and omitted coordinates exactly equal",
            "numerical_policy": POLICY, "schedule": SCHEDULE, "authorizes_commit": False}


def model_descriptor(model_id, fmt):
    _format(fmt)
    require(type(model_id) is str and model_id in MODELS, "Unknown or unproved B3 model/domain")
    feedforward = model_id in ("two_layer_relu_v1", "shared_relu_v1")
    if model_id == "two_layer_relu_v1":
        graph = ({"call_id": "hidden", "bank_id": "first", "activation": "relu"},
                 {"call_id": "output", "bank_id": "second", "activation": "identity"})
    elif model_id == "shared_relu_v1":
        graph = ({"call_id": "shared_hidden", "bank_id": "shared", "activation": "relu"},
                 {"call_id": "shared_output", "bank_id": "shared", "activation": "identity"})
    else:
        graph = ({"call_id": "state_update", "bank_id": "update", "activation": "identity"},)
    return {"registry": "dmwk-p2-b3-fixed-domain-v1", "model_id": model_id, "format": fmt,
            "kind": "feedforward" if feedforward else "recurrent", "graph": graph,
            "physical_bank_ids": tuple(sorted(set(c["bank_id"] for c in graph))),
            "state_dimension": 0 if feedforward else 1, "input_dimension": 2 if feedforward else 1,
            "network_input_dimension": 2, "output_dimension": 2 if feedforward else 1,
            "input_bounds": (Fraction(1), Fraction(1)) if feedforward else (Fraction(1),),
            "initial_state_bounds": () if feedforward else (Fraction(1),),
            "domain_id": model_id+":complete-canonical-word-box-v1",
            "source_domain": "all canonical finite raw words within the stated exact coordinate bounds",
            "initial_relation": "identical network input" if feedforward else
                "all admitted initial state pairs within their boxes with linf difference <= declared E0",
            "input_relation": "identical input" if feedforward else "same legal input at every finite time",
            "state_update": "none" if feedforward else "all next-state coordinates from the same old snapshot",
            "observation": "all final output coordinates" if feedforward else "all state coordinates at every time 0..T",
            "numerical_policy": POLICY, "schedule": SCHEDULE, "norm": "linf",
            "fixed_endpoints_throughout": True, "maximum_reference_horizon": MAX_HORIZON}


def initial_banks(model_id, fmt):
    model_descriptor(model_id, fmt)
    enc = lambda v: get_fp().encode_constant(v, fmt)
    bank = lambda rows: {"weights": tuple(tuple(enc(v) for v in row) for row in rows),
                         "bias": (0,)*len(rows)}
    if model_id == "two_layer_relu_v1":
        return {"first": bank(((1, 0), (0, 1))), "second": bank(((Fraction(1, 2), 0), (0, Fraction(1, 2))))}
    if model_id == "shared_relu_v1":
        return {"shared": bank(((Fraction(1, 2), 0), (0, Fraction(1, 2))))}
    if model_id == "contractive_scalar_v1":
        row = (Fraction(1, 2), Fraction(1, 8))
    elif model_id == "neutral_scalar_v1":
        row = (Fraction(1), Fraction(0))
    else:
        row = (Fraction(2), Fraction(0))
    return {"update": bank((row,))}


def _registered_endpoints(descriptor, old_banks, new_banks, fmt):
    expected = validate_network(descriptor["graph"], initial_banks(descriptor["model_id"], fmt), fmt)
    old = validate_network(descriptor["graph"], old_banks, fmt)
    new = validate_network(descriptor["graph"], new_banks, fmt)
    for endpoint in (old, new):
        require(endpoint["physical_bank_ids"] == expected["physical_bank_ids"], "Registered bank set mismatch")
        for key in expected["physical_bank_ids"]:
            require(cb.decode_matrix(endpoint["banks"][key]["weights"], fmt).shape ==
                    cb.decode_matrix(expected["banks"][key]["weights"], fmt).shape,
                    "Registered physical bank shape mismatch")
    return old["banks"], new["banks"]


def _state_box(value, default=None):
    if value is None:
        return default
    return _bounds((value,), 1) if type(value) in (int, Fraction) else _bounds(value, 1)


def _with_initial_error(proof, initial_error):
    """Reuse fixed-domain coefficient proofs with a different scalar relation."""
    error = _initial_error(initial_error)
    calls, Ls, betas = [], [], []
    for call in proof["calls"]:
        next_error = call["L"]*error+call["beta"]
        calls.append({**call, "previous_error": error, "next_error": next_error})
        Ls.append(call["L"]); betas.append(call["beta"]); error = next_error
    recurrence = propagate_recurrence(Ls, betas, initial_error)
    return {**proof, "calls": calls, "error_bounds": recurrence["error_bounds"],
            "final_error_bound": error, "recurrence": recurrence}


def analyze_model(model_id, fmt, old_banks, new_banks, horizon=1, initial_error=0,
                  method="tube", state_box=None):
    descriptor = model_descriptor(model_id, fmt)
    old_banks, new_banks = _registered_endpoints(descriptor, old_banks, new_banks, fmt)
    require(type(horizon) is int and 0 <= horizon <= MAX_HORIZON, "Unsupported reference horizon")
    require(type(method) is str and method in ("tube", "invariant"), "Unknown propagation proof method")
    e0 = _initial_error(initial_error)
    common = {"descriptor": descriptor, "norm": "linf", "horizon": horizon,
              "initial_error": e0, "method": method, "old_banks": old_banks, "new_banks": new_banks,
              "domain_containment_proved": True, "totality_proved": True,
              "fixed_endpoint_premise": True, "authorizes_commit": False,
              "claims_BIT": False, "claims_program_noninterference": False}
    if descriptor["kind"] == "feedforward":
        require(horizon == 1 and e0 == 0 and method == "tube" and state_box is None,
                "Feedforward registry requires one identical input and tube method")
        proof = network_bound(descriptor["graph"], old_banks, new_banks,
                              descriptor["input_bounds"], descriptor["input_bounds"], fmt)
        return {**common, "network_proof": proof, "error_bounds": proof["error_bounds"],
                "final_error_bound": proof["final_error_bound"], "observed_bound": proof["final_error_bound"],
                "observation": descriptor["observation"], "uniform_in_time_bound": None}
    init = descriptor["initial_state_bounds"]
    inputs = descriptor["input_bounds"]
    cap = _state_box(state_box, (Fraction(2),) if method == "invariant" else None)
    require(cap is None or all(x <= y for x, y in zip(init, cap)), "Declared state box excludes admitted initial states")
    relation = {"old_initial_bounds": init, "new_initial_bounds": init, "linf_difference_at_most": e0,
                "same_initial_state": e0 == 0, "source": "all pairs satisfying these explicit premises"}
    if method == "invariant":
        proof = network_bound(descriptor["graph"], old_banks, new_banks, cap+inputs, cap+inputs, fmt,
                              initial_error=0, first_difference_columns=(0,))
        require(all(v <= c for v, c in zip(proof["old_output_bounds"], cap)) and
                all(v <= c for v, c in zip(proof["new_output_bounds"], cap)),
                "Common invariant not certified: an endpoint image enclosure exits the proposed box")
        L, beta = proof["lipschitz_product"], proof["forcing_bound"]
        recurrence = constant_recurrence(L, beta, horizon, e0)
        uniform = max(e0, beta/(1-L)) if L < 1 else (e0 if L == 1 and beta == 0 else None)
        tube = (init,)+(cap,)*horizon
        steps = []
        current_error = e0
        for time in range(horizon):
            step = _with_initial_error(proof, current_error)
            steps.append({"time": time, **step})
            current_error = step["final_error_bound"]
        require(current_error == recurrence["final_error_bound"], "Invariant-step recurrence mismatch")
        return {**common, "state_box": cap, "initial_relation": relation,
                "error_bounds": recurrence["error_bounds"], "final_error_bound": recurrence["final_error_bound"],
                "observed_bound": max(recurrence["error_bounds"]), "old_state_tube": tube, "new_state_tube": tube,
                "steps": steps, "recurrence": recurrence,
                "common_invariant_proof": proof, "common_invariant_verified": True,
                "uniform_in_time_bound": uniform,
                "uniform_scope": "all finite times under the same fixed endpoints/domain and proven common invariant" if uniform is not None else None,
                "observation": descriptor["observation"]}
    old_state, new_state = init, init
    old_tube, new_tube, series, steps, Ls, betas = [init], [init], [e0], [], [], []
    for time in range(horizon):
        proof = network_bound(descriptor["graph"], old_banks, new_banks,
                              old_state+inputs, new_state+inputs, fmt,
                              initial_error=series[-1], first_difference_columns=(0,))
        old_state, new_state = proof["old_output_bounds"], proof["new_output_bounds"]
        require(cap is None or (all(v <= c for v, c in zip(old_state, cap)) and
                                all(v <= c for v, c in zip(new_state, cap))),
                "Finite tube exits supplied cap; no clamping or original-domain reuse is allowed")
        old_tube.append(old_state); new_tube.append(new_state); series.append(proof["final_error_bound"])
        steps.append({"time": time, **proof}); Ls.append(proof["lipschitz_product"]); betas.append(proof["forcing_bound"])
    recurrence = propagate_recurrence(Ls, betas, e0)
    require(tuple(series) == recurrence["error_bounds"], "State recurrence mismatch")
    return {**common, "state_box": cap, "initial_relation": relation, "error_bounds": tuple(series),
            "final_error_bound": series[-1], "observed_bound": max(series),
            "old_state_tube": tuple(old_tube), "new_state_tube": tuple(new_tube), "steps": steps,
            "recurrence": recurrence, "common_invariant_verified": False,
            "uniform_in_time_bound": None, "observation": descriptor["observation"]}


def trace_model(model_id, fmt, banks, initial_state_words=(), input_sequence=()):
    descriptor = model_descriptor(model_id, fmt)
    banks, _ = _registered_endpoints(descriptor, banks, banks, fmt)
    require(type(input_sequence) in (tuple, list), "Input history must be a finite sequence")
    if descriptor["kind"] == "feedforward":
        require(type(initial_state_words) in (tuple, list) and len(initial_state_words) == 0
                and len(input_sequence) == 1, "Feedforward point trace takes exactly one input and no state")
        require(type(input_sequence[0]) in (tuple, list), "Feedforward input must be a raw word vector")
        inp = tuple(input_sequence[0])
        values = cb.decode_vector(inp, fmt)
        require(len(values) == 2 and all(abs(v) <= b for v, b in zip(values, descriptor["input_bounds"])),
                "Point input outside declared source domain")
        proof = trace_network(descriptor["graph"], banks, inp, fmt)
        return {"descriptor": descriptor, "outputs": (proof["output_words"],), "output_words": proof["output_words"],
                "states": (), "calls": [proof], "input_sequence": tuple(tuple(v) for v in input_sequence),
                "scope": "one declared point input only"}
    require(len(input_sequence) <= MAX_HORIZON, "Point history exceeds reference horizon")
    require(type(initial_state_words) in (tuple, list) and len(initial_state_words) == 1, "Scalar initial state word required")
    state = tuple(initial_state_words)
    decoded = cb.decode_vector(state, fmt)
    require(abs(decoded[0]) <= descriptor["initial_state_bounds"][0], "Initial state outside declared source domain")
    states, calls, outputs = [state], [], []
    for inp in input_sequence:
        require(type(inp) in (tuple, list) and len(inp) == 1, "Scalar external input word required")
        values = cb.decode_vector(inp, fmt)
        require(abs(values[0]) <= descriptor["input_bounds"][0], "External input outside declared domain")
        proof = trace_network(descriptor["graph"], banks, state+tuple(inp), fmt)
        state = proof["output_words"]
        states.append(state); outputs.append(state); calls.append(proof)
    return {"descriptor": descriptor, "states": tuple(states), "outputs": tuple(outputs),
            "output_words": state, "calls": calls, "input_sequence": tuple(tuple(v) for v in input_sequence),
            "scope": "one finite history; not a proof that a sampled envelope is invariant"}
