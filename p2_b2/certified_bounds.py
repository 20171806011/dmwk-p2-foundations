"""B2 exact/outward single-affine-layer perturbation certificates.

Bounds are read-only diagnostics, never live commit authorization. All norm
certificates use rational/integer arithmetic; protected traces use the fixed
P1 BF16 software / locally audited FP32 word primitives.
"""
from __future__ import annotations

from fractions import Fraction
from math import isqrt

from b2_runtime import get_fp, load_a2, load_a3

xp = load_a2("exact_projection")
Matrix = xp.Matrix
ck = load_a3("certificate_kernel")
POLICY = "p2-b2-affine-bias-first-ascending-separate-rne-canonical-zero-v1"


class BoundRefused(ValueError):
    """The requested bound's premises or totality could not be certified."""


def require(ok, message):
    if not ok:
        raise BoundRefused(message)


def rational(value):
    require(type(value) in (int, Fraction), "Exact int/Fraction values required")
    return Fraction(value)


def _matrix(value):
    require(type(value) is Matrix, "Exact immutable A2 Matrix required")
    return value


def _vector(value, length=None):
    require(type(value) in (tuple, list), "Exact vector must be a list or tuple")
    require(length is None or len(value) == length, "Vector dimension mismatch")
    return tuple(rational(x) for x in value)


def record(value):
    """Canonical primitive form; no float approximations or hidden matrix shape."""
    if type(value) is Fraction:
        return [value.numerator, value.denominator]
    if type(value) is Matrix:
        return {"shape": [value.nrows, value.ncols], "rows": record(value.rows)}
    if type(value) in (tuple, list):
        return [record(v) for v in value]
    if type(value) is dict:
        require(all(type(k) is str for k in value), "Record keys must be strings")
        return {k: record(v) for k, v in value.items()}
    require(value is None or type(value) in (str, bool, int), "Unserializable bound record")
    return value


def sqrt_bounds(q, bits=80):
    q = rational(q)
    require(q >= 0, "Square root requires a nonnegative rational")
    require(type(bits) is int and 1 <= bits <= 4096, "Dyadic precision must lie in [1,4096]")
    sn, sd = isqrt(q.numerator), isqrt(q.denominator)
    if sn*sn == q.numerator and sd*sd == q.denominator:
        exact = Fraction(sn, sd)
        return exact, exact
    # Normalize the squared value to [1,4), avoiding an absolute 2^-bits
    # width that would be useless for subnormal-scale responses.
    exponent = q.numerator.bit_length()-q.denominator.bit_length()
    below = (q.numerator < (q.denominator << exponent)) if exponent >= 0 else ((q.numerator << -exponent) < q.denominator)
    if below:
        exponent -= 1
    root_exponent = exponent // 2
    magnitude = Fraction(1 << root_exponent) if root_exponent >= 0 else Fraction(1, 1 << -root_exponent)
    normalized = q/(magnitude*magnitude)
    require(1 <= normalized < 4, "Root normalization failed")
    scale = 1 << bits
    floor_scaled = isqrt((normalized.numerator * scale * scale) // normalized.denominator)
    lo, hi = magnitude*Fraction(floor_scaled, scale), magnitude*Fraction(floor_scaled+1, scale)
    require(lo*lo <= q <= hi*hi, "Integer square-root enclosure failed")
    return lo, hi


def norm2_bounds(values, bits=80):
    v = _vector(values)
    return sqrt_bounds(sum((x*x for x in v), Fraction(0)), bits)


def spectral_upper(A, bits=80):
    _matrix(A)
    frob2 = sum((x*x for row in A.rows for x in row), Fraction(0))
    one = max((sum((abs(A.rows[i][j]) for i in range(A.nrows)), Fraction(0))
               for j in range(A.ncols)), default=Fraction(0))
    infinity = max((sum((abs(v) for v in row), Fraction(0)) for row in A.rows), default=Fraction(0))
    return sqrt_bounds(min(frob2, one*infinity), bits)[1]


def _apply(A, h):
    _matrix(A)
    h = _vector(h, A.ncols)
    return tuple(sum((a*b for a, b in zip(row, h)), Fraction(0)) for row in A.rows)


def _vsub(a, b):
    require(len(a) == len(b), "Vector subtraction shape mismatch")
    return tuple(x-y for x, y in zip(a, b))


def geometry_bound(delta, H, h, U=None, basis_route="projector", bits=80):
    _matrix(delta); _matrix(H)
    require(delta.ncols == H.nrows, "Protected-space input dimension mismatch")
    require(type(basis_route) is str and basis_route in ("projector", "orthonormal", "approximate"), "Unknown geometry route")
    h = _vector(h, H.nrows)
    projector = xp.projection(H).P_D
    protected = _apply(projector, h)
    residual = _vsub(h, protected)
    dn = spectral_upper(delta, bits)
    hn, pn, en = (norm2_bounds(v, bits)[1] for v in (h, protected, residual))
    route = {}
    if basis_route == "projector":
        require(U is None, "Unused basis must be absent on projector route")
        action = spectral_upper(xp.matmul(delta, projector), bits)
    else:
        _matrix(U)
        require(U.nrows == H.nrows, "Basis ambient dimension mismatch")
        gram = xp.matmul(xp.transpose(U), U)
        gram_error = xp.sub(gram, xp.eye(U.ncols))
        delta_g = spectral_upper(gram_error, bits)
        if basis_route == "orthonormal":
            require(gram_error == xp.zeros(U.ncols, U.ncols), "Basis is not exactly orthonormal")
            p_u = xp.project_onto_columns(U)
            require(p_u == projector, "Orthonormal basis does not span declared V")
            action = spectral_upper(xp.matmul(delta, U), bits)
            route = {"gram_error_upper": Fraction(0), "projector_deviation_upper": Fraction(0),
                     "inverse_condition_upper": Fraction(1)}
        else:
            require(delta_g < 1, "Gram bound >=1: this conditioning route is not certified")
            # delta_g<1 proves full column rank, permitting an exact Gram inverse.
            p_u = xp.project_onto_columns(U)
            sigma = spectral_upper(xp.sub(projector, p_u), bits)
            condition = sqrt_bounds(1/(1-delta_g), bits)[1]
            observed = spectral_upper(xp.matmul(delta, U), bits)
            action = observed*condition + dn*sigma
            route = {"gram_error_upper": delta_g, "projector_deviation_upper": sigma,
                     "inverse_condition_upper": condition, "basis_residual_upper": observed,
                     "approximate_projector": p_u}
    bound = action*pn + dn*en
    actual = _apply(delta, h)
    actual_lo, actual_hi = norm2_bounds(actual, bits)
    require(sum((v*v for v in actual), Fraction(0)) <= bound*bound,
            "Constructed geometric bound does not cover exact squared response")
    result = {"bound": bound, "uniform_bound": dn*hn, "actual_change": actual,
              "actual_norm_lower": actual_lo, "actual_norm_upper": actual_hi,
              "h_norm_upper": hn, "protected_component": protected,
              "protected_component_norm_upper": pn, "residual": residual,
              "residual_norm_upper": en, "delta_norm_upper": dn,
              "protected_action_norm_upper": action, "basis_route": basis_route,
              "protected_projector": projector,
              "scope": "exact point geometry on the declared reference space; global provenance not inferred"}
    result.update(route)
    return result


def error_ledger(chain, h=None, bits=80):
    require(type(chain) in (tuple, list) and len(chain) >= 1, "Nonempty named ledger chain required")
    names, matrices = [], []
    for item in chain:
        require(type(item) in (tuple, list) and len(item) == 2 and type(item[0]) is str and item[0],
                "Ledger entry must be (nonempty name, exact matrix)")
        require(item[0] not in names, "Ledger names must be unique; duplicated errors are not allowed")
        names.append(item[0]); matrices.append(_matrix(item[1]))
    require(all(m.shape == matrices[0].shape for m in matrices), "Ledger matrix shape mismatch")
    hv = None if h is None else _vector(h, matrices[0].ncols)
    def measure(A):
        return spectral_upper(A, bits) if hv is None else norm2_bounds(_apply(A, hv), bits)[1]
    stages = []
    rebuilt = matrices[0]
    bound = measure(matrices[0])
    for i in range(1, len(matrices)):
        error = xp.sub(matrices[i], matrices[i-1])
        size = measure(error)
        stages.append({"name": names[i], "from": names[i-1], "error": error,
                       "bound": size, "point_error": None if hv is None else _apply(error, hv)})
        rebuilt = xp.add(rebuilt, error)
        bound += size
    require(rebuilt == matrices[-1], "Telescoping identity failed")
    return {"accounting": "telescoping_alternative_to_direct_endpoint", "baseline_name": names[0],
            "baseline_increment": matrices[0], "baseline_bound": measure(matrices[0]),
            "stages": stages, "net_increment": matrices[-1], "bound": bound,
            "point": hv, "direct_endpoint_bound": measure(matrices[-1]),
            "scope": "exact accounting identity; supplied ideal/host stage provenance not certified"}


def _format(fmt):
    require(type(fmt) is str and fmt in ("BF16", "FP32"), "Unsupported target format")
    return get_fp().get_format(fmt)


def _word(word, fmt):
    spec = _format(fmt)
    require(type(word) is int and 0 <= word < (1 << spec.total_bits), "Raw word must be an in-range built-in integer")
    require(((word >> spec.fraction_bits) & spec.exponent_mask) != spec.exponent_mask,
            "NaN/infinity is outside the finite input policy")
    require(word != spec.sign_mask, "Negative zero input encoding is not canonical")
    return word


def decode_vector(words, fmt):
    require(type(words) in (tuple, list), "Raw vector must be a tuple or list")
    return tuple(get_fp().decode_word(_word(w, fmt), fmt) for w in words)


def decode_matrix(words, fmt):
    require(type(words) in (tuple, list) and len(words) >= 1, "Nonempty raw matrix required")
    require(all(type(row) in (tuple, list) for row in words), "Raw matrix rows must be tuples or lists")
    width = len(words[0])
    require(all(len(row) == width for row in words), "Ragged raw matrix")
    return Matrix(tuple(decode_vector(row, fmt) for row in words), width)


def format_constants(fmt):
    spec = _format(fmt)
    maximum_word = ((spec.exponent_mask-1) << spec.fraction_bits) | ((1 << spec.fraction_bits)-1)
    return {"u": Fraction(1, 1 << spec.p), "eta": get_fp().decode_word(1, fmt),
            "maximum": get_fp().decode_word(maximum_word, fmt), "maximum_word": maximum_word,
            "precision": spec.p}


def _bias(bias, n, fmt):
    value = (0,)*n if bias is None else bias
    require(type(value) in (tuple, list) and len(value) == n, "Bias shape mismatch")
    return tuple(_word(x, fmt) for x in value)


def trace_affine(weights, h, fmt, bias=None, bits=80):
    A = decode_matrix(weights, fmt)
    hv = decode_vector(h, fmt)
    require(len(hv) == A.ncols, "Input activation shape mismatch")
    bwords = _bias(bias, A.nrows, fmt)
    b = decode_vector(bwords, fmt)
    fp, constants = get_fp(), format_constants(fmt)
    u, eta, maximum = constants["u"], constants["eta"], constants["maximum"]
    audit = fp.Audit()
    rows, output_words, exact_outputs, signed, rowbounds, mixed_rows = [], [], [], [], [], []
    try:
        for i, wrow in enumerate(weights):
            acc = bwords[i]
            events = []
            for j, (w, value) in enumerate(zip(wrow, h)):
                arg = A.rows[i][j]*hv[j]
                product = fp.mul_words(w, value, fmt, audit)
                decoded_product = fp.decode_word(_word(product, fmt), fmt)
                err = decoded_product-arg
                valid = abs(arg) <= maximum
                mixed = u*abs(arg)+eta/2 if valid else None
                require(mixed is None or abs(err) <= mixed, "Product mixed-error bound failed")
                events.append({"operation": "multiply", "column": j, "exact_argument": arg,
                               "output_word": product, "decoded_output": decoded_product,
                               "signed_error": err, "absolute_error": abs(err),
                               "mixed_range_proved": valid, "mixed_bound": mixed})
                arg = fp.decode_word(acc, fmt)+decoded_product
                acc = fp.add_words(acc, product, fmt, audit)
                decoded_acc = fp.decode_word(_word(acc, fmt), fmt)
                err = decoded_acc-arg
                valid = abs(arg) <= maximum
                mixed = u*abs(arg)+eta/2 if valid else None
                require(mixed is None or abs(err) <= mixed, "Addition mixed-error bound failed")
                events.append({"operation": "add", "column": j, "exact_argument": arg,
                               "output_word": acc, "decoded_output": decoded_acc,
                               "signed_error": err, "absolute_error": abs(err),
                               "mixed_range_proved": valid, "mixed_bound": mixed})
            exact = b[i]+sum((a*x for a, x in zip(A.rows[i], hv)), Fraction(0))
            error_sum = sum((event["signed_error"] for event in events), Fraction(0))
            abs_sum = sum((event["absolute_error"] for event in events), Fraction(0))
            mixed = (sum((event["mixed_bound"] for event in events), Fraction(0))
                     if all(event["mixed_range_proved"] for event in events) else None)
            require(fp.decode_word(acc, fmt)-exact == error_sum, "Signed local-error telescope failed")
            rows.append({"row": i, "events": events, "exact_output": exact,
                         "error_sum": error_sum, "abs_error_sum": abs_sum,
                         "mixed_error_bound": mixed})
            output_words.append(acc); exact_outputs.append(exact); signed.append(error_sum)
            rowbounds.append(abs_sum); mixed_rows.append(mixed)
    except (fp.ExecutionError, OverflowError) as exc:
        raise BoundRefused("Actual ordered execution is not total in the finite policy: " + str(exc)) from None
    return {"policy": POLICY, "format": fmt, "input_words": tuple(h), "bias_words": bwords,
            "output_words": tuple(output_words), "decoded_output": decode_vector(output_words, fmt),
            "exact_output": tuple(exact_outputs), "row_signed_errors": tuple(signed),
            "row_error_bounds": tuple(rowbounds), "row_mixed_error_bounds": tuple(mixed_rows),
            "rho_l2": norm2_bounds(rowbounds, bits)[1], "rho_linf": max(rowbounds, default=Fraction(0)),
            "rows": rows, "arithmetic_counts": ck._audit_record(audit),
            "totality": "actual_trace_checked", "scope": "one_declared_input_only"}


def point_bound(old_words, new_words, h_words, fmt, old_bias=None, new_bias=None, bits=80):
    old, new = decode_matrix(old_words, fmt), decode_matrix(new_words, fmt)
    require(old.shape == new.shape, "Endpoint matrix shapes differ")
    old_b = _bias(old_bias, old.nrows, fmt)
    new_b = old_b if new_bias is None else _bias(new_bias, old.nrows, fmt)
    old_trace = trace_affine(old_words, h_words, fmt, old_b, bits)
    new_trace = trace_affine(new_words, h_words, fmt, new_b, bits)
    delta = xp.sub(new, old)
    bias_delta = _vsub(decode_vector(new_b, fmt), decode_vector(old_b, fmt))
    exact = tuple(a+b for a, b in zip(_apply(delta, decode_vector(h_words, fmt)), bias_delta))
    actual = _vsub(new_trace["decoded_output"], old_trace["decoded_output"])
    exact_upper = norm2_bounds(exact, bits)[1]
    coordinate = tuple(abs(v)+ro+rn for v, ro, rn in zip(exact, old_trace["row_error_bounds"], new_trace["row_error_bounds"]))
    linf = max(coordinate, default=Fraction(0))
    l2 = exact_upper+old_trace["rho_l2"]+new_trace["rho_l2"]
    lower_reference = max((abs(v) for v in old_trace["decoded_output"]), default=Fraction(0))
    actual_lo, actual_hi = norm2_bounds(actual, bits)
    require(all(abs(a) <= b for a, b in zip(actual, coordinate)) and
            sum((v*v for v in actual), Fraction(0)) <= l2*l2, "Two-execution bound failed")
    return {"policy": POLICY, "format": fmt, "old_trace": old_trace, "new_trace": new_trace,
            "effective_delta": delta, "bias_delta": bias_delta, "exact_change": exact,
            "exact_change_norm_upper": exact_upper, "actual_change": actual,
            "actual_norm_lower": actual_lo, "actual_norm_upper": actual_hi,
            "coordinate_bounds": coordinate, "linf_bound": linf, "l2_bound": l2,
            "reference_output_norm_lower": lower_reference,
            "relative_bound": l2/lower_reference if lower_reference > 0 else None,
            "relative_norm": "l2 relative to actual decoded old output, lower bounded by its linf norm",
            "scope": "one_declared_input_only", "authorizes_live_commit": False}


def mixed_budget(bound, reference_lower, absolute_budget, relative_budget):
    b, ref, absolute, relative = map(rational, (bound, reference_lower, absolute_budget, relative_budget))
    require(min(b, ref, absolute, relative) >= 0, "Mixed bound and budgets must be nonnegative")
    threshold = absolute+relative*ref
    return {"accepted": b <= threshold, "bound": b, "reference_lower": ref,
            "absolute_budget": absolute, "relative_budget": relative,
            "certified_threshold": threshold,
            "scope": "sufficient numeric condition only; reference lower-bound provenance required"}


def _box_trace(words, bounds, fmt, bias, bits):
    A = decode_matrix(words, fmt)
    b = decode_vector(bias, fmt)
    constants = format_constants(fmt)
    u, eta, maximum = constants["u"], constants["eta"], constants["maximum"]
    rows, errors = [], []
    for i, row in enumerate(A.rows):
        accumulator = abs(b[i])
        error_sum = Fraction(0)
        steps = []
        for j, (weight, hbound) in enumerate(zip(row, bounds)):
            product_arg = abs(weight)*hbound
            require(product_arg <= maximum,
                    "Conservative box totality refused: product range exceeds Fmax at row %d column %d" % (i, j))
            product_error = u*product_arg+eta/2
            product = min(maximum, product_arg+product_error)
            addition_arg = accumulator+product
            require(addition_arg <= maximum,
                    "Conservative box totality refused: accumulator range exceeds Fmax at row %d column %d" % (i, j))
            addition_error = u*addition_arg+eta/2
            next_accumulator = min(maximum, addition_arg+addition_error)
            error_sum += product_error+addition_error
            steps.append({"column": j, "old_accumulator_bound": accumulator,
                          "product_argument_bound": product_arg, "product_error_bound": product_error,
                          "rounded_product_bound": product, "addition_argument_bound": addition_arg,
                          "addition_error_bound": addition_error, "new_accumulator_bound": next_accumulator,
                          "product_range_proved": True, "addition_range_proved": True})
            accumulator = next_accumulator
        rows.append({"row": i, "bias_bound": abs(b[i]), "steps": steps,
                     "row_error_bound": error_sum, "output_magnitude_bound": accumulator})
        errors.append(error_sum)
    return {"rows": rows, "row_error_bounds": tuple(errors),
            "rho_l2": norm2_bounds(errors, bits)[1], "rho_linf": max(errors, default=Fraction(0)),
            "constants": constants, "totality": "proved_for_stated_box"}


def box_bound(old_words, new_words, coordinate_bounds, fmt, old_bias=None, new_bias=None, bits=80):
    old, new = decode_matrix(old_words, fmt), decode_matrix(new_words, fmt)
    require(old.shape == new.shape, "Endpoint matrix shapes differ")
    bounds = _vector(coordinate_bounds, old.ncols)
    require(all(v >= 0 for v in bounds), "Input coordinate bounds must be nonnegative")
    old_b = _bias(old_bias, old.nrows, fmt)
    new_b = old_b if new_bias is None else _bias(new_bias, old.nrows, fmt)
    old_proof = _box_trace(old_words, bounds, fmt, old_b, bits)
    new_proof = _box_trace(new_words, bounds, fmt, new_b, bits)
    delta = xp.sub(new, old)
    bias_delta = _vsub(decode_vector(new_b, fmt), decode_vector(old_b, fmt))
    algebraic = tuple(abs(db)+sum((abs(v)*h for v, h in zip(row, bounds)), Fraction(0))
                      for row, db in zip(delta.rows, bias_delta))
    coordinate = tuple(v+ro+rn for v, ro, rn in zip(algebraic, old_proof["row_error_bounds"], new_proof["row_error_bounds"]))
    return {"policy": POLICY, "format": fmt, "input_coordinate_bounds": bounds,
            "old_range_proof": old_proof, "new_range_proof": new_proof,
            "effective_delta": delta, "bias_delta": bias_delta,
            "algebraic_coordinate_bounds": algebraic, "coordinate_bounds": coordinate,
            "linf_bound": max(coordinate, default=Fraction(0)),
            "l2_bound": norm2_bounds(algebraic, bits)[1]+old_proof["rho_l2"]+new_proof["rho_l2"],
            "constants": format_constants(fmt), "totality": "proved_for_stated_box",
            "relative_bound": None, "scope": "all_admitted_raw_inputs_in_stated_box",
            "global_domain_inclusion_verified": False, "authorizes_live_commit": False}
