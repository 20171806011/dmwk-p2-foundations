"""Read-only B3 hard-guard diagnostics and strict margin certificates.

Exact decoded endpoint changes, both input domains and both rounding errors
are explicit. These reports have no live update or program-proof authority.
"""
from __future__ import annotations

from fractions import Fraction
import math

from b3_runtime import get_fp, load_b2

cb = load_b2("certified_bounds")
POLICY = cb.POLICY
GUARD = "decoded_finite_guard_strictly_greater_than_zero"


class MarginRefused(ValueError):
    """The requested sufficient control-flow condition was not established."""


def require(ok, message):
    if not ok:
        raise MarginRefused(message)


def rational(value):
    require(type(value) in (int, Fraction), "Exact int/Fraction bound required")
    return Fraction(value)


def record(value):
    """Stable JSON primitives; exact rationals are strings, never approximations."""
    if type(value) is Fraction:
        return str(value)
    if type(value) in (tuple, list):
        return [record(x) for x in value]
    if type(value) is dict:
        require(all(type(k) is str for k in value), "Record keys must be strings")
        return {k: record(v) for k, v in value.items()}
    if type(value) is float:
        require(math.isfinite(value), "Nonfinite JSON number")
        return value
    require(value is None or type(value) in (int, str, bool), "Unsupported record type")
    return value


def _endpoints(old_row, new_row, old_bias, new_bias, fmt, policy):
    require(type(policy) is str and policy == POLICY, "Uncertified guard arithmetic policy")
    require(type(old_row) is tuple and type(new_row) is tuple and len(old_row) >= 1,
            "Nonempty immutable raw guard rows required")
    require(len(old_row) == len(new_row), "Guard endpoint dimension mismatch")
    try:
        a = cb.decode_matrix((old_row,), fmt).rows[0]
        ap = cb.decode_matrix((new_row,), fmt).rows[0]
        b, bp = cb.decode_vector((old_bias, new_bias), fmt)
    except cb.BoundRefused as exc:
        raise MarginRefused(str(exc)) from None
    return a, ap, b, bp


def _box(values, d, name):
    require(type(values) in (tuple, list) and len(values) == d,
            name + " box dimension/type mismatch")
    answer = tuple(rational(x) for x in values)
    require(all(x >= 0 for x in answer), name + " box bounds must be nonnegative")
    return answer


def strict_margin(margin, change_bound):
    """Check only the scalar obligation; supplied quantities need proof provenance."""
    margin, change_bound = rational(margin), rational(change_bound)
    require(change_bound >= 0, "Guard change bound must be nonnegative")
    require(margin > change_bound,
            "Strict margin not established: equality or insufficient margin refused")
    return {"margin": margin, "change_bound": change_bound,
            "strict_slack": margin-change_bound, "strict_condition_holds": True,
            "scope": "scalar inequality only; no domain or bound provenance inferred",
            "authorizes_live_commit": False}


def certify_guard_margin(old_row, new_row, old_bias, new_bias, fmt,
                         old_box, new_box, input_radius, *, policy=POLICY):
    """Sufficient uniform branch equality on the stated two-box/radius relation.

    Domain inclusion for a surrounding trajectory must be proved elsewhere.
    Analytic endpoint-specific box proofs certify rounding and no overflow.
    """
    a, ap, b, bp = _endpoints(old_row, new_row, old_bias, new_bias, fmt, policy)
    B, Bp = _box(old_box, len(a), "Old"), _box(new_box, len(a), "New")
    radius = rational(input_radius)
    require(radius >= 0, "Input radius must be nonnegative")
    try:
        old_proof = cb.box_bound((old_row,), (old_row,), B, fmt,
                                 (old_bias,), (old_bias,))["old_range_proof"]
        new_proof = cb.box_bound((new_row,), (new_row,), Bp, fmt,
                                 (new_bias,), (new_bias,))["old_range_proof"]
    except cb.BoundRefused as exc:
        raise MarginRefused("Guard totality/range proof refused: " + str(exc)) from None
    rho, rhop = old_proof["rho_linf"], new_proof["rho_linf"]
    delta = tuple(y-x for x, y in zip(a, ap))
    delta_b = bp-b
    endpoint_change = abs(delta_b)+sum((abs(x)*bound for x, bound in zip(delta, B)), Fraction(0))
    new_lipschitz = sum(map(abs, ap), Fraction(0))
    input_change = new_lipschitz*radius
    kappa = endpoint_change+input_change+rho+rhop
    old_variation = sum((abs(x)*bound for x, bound in zip(a, B)), Fraction(0))
    low, high = b-old_variation-rho, b+old_variation+rho
    if low > 0:
        branch, margin = True, low
    elif high < 0:
        branch, margin = False, -high
    else:
        raise MarginRefused("Old executed guard interval does not have a strict sign")
    checked = strict_margin(margin, kappa)
    return {"method": "two_endpoint_boxes_strict_guard_margin_v1",
            "format": fmt, "guard": GUARD, "numerical_policy": policy,
            "old_weight_words": old_row, "new_weight_words": new_row,
            "old_bias_word": old_bias, "new_bias_word": new_bias,
            "effective_coefficient_delta": delta, "effective_bias_delta": delta_b,
            "old_box": B, "new_box": Bp, "input_radius": radius,
            "old_exact_guard_interval": (b-old_variation, b+old_variation),
            "old_executed_guard_enclosure": (low, high),
            "rho_old": rho, "rho_new": rhop,
            "old_range_proof": old_proof, "new_range_proof": new_proof,
            "endpoint_change_bound": endpoint_change,
            "new_exact_guard_lipschitz_linf": new_lipschitz,
            "input_change_bound": input_change, "guard_change_bound": kappa,
            "margin": margin, "strict_slack": checked["strict_slack"],
            "same_branch": branch, "branch_equality_certified": True,
            "scope": "all accepted stored pairs in stated boxes with distance <= input_radius",
            "global_trajectory_containment_verified": False,
            "authorizes_live_commit": False}


def trace_guard(row, bias, input_words, fmt, *, policy=POLICY):
    _endpoints(row, row, bias, bias, fmt, policy)
    require(type(input_words) is tuple and len(input_words) == len(row),
            "Immutable guard input with matching dimension required")
    try:
        return cb.trace_affine((row,), input_words, fmt, (bias,))
    except cb.BoundRefused as exc:
        raise MarginRefused("Actual guard execution refused: " + str(exc)) from None


def diagnose_finite_pairs(old_row, new_row, old_bias, new_bias, pairs, fmt,
                          *, old_box=None, new_box=None, input_radius=None,
                          policy=POLICY):
    """Execute exactly the listed pairs; no global coverage is inferred.

    Optional domain/radius arguments are all-or-none and checked on both
    decoded inputs, preventing original-domain-only use of a certificate.
    """
    a, ap, b, bp = _endpoints(old_row, new_row, old_bias, new_bias, fmt, policy)
    require(type(pairs) in (tuple, list) and len(pairs) >= 1,
            "Nonempty explicit finite input-pair family required")
    supplied = (old_box is not None, new_box is not None, input_radius is not None)
    require(all(supplied) or not any(supplied), "Both domains and radius must be supplied together")
    if all(supplied):
        B, Bp = _box(old_box, len(a), "Old"), _box(new_box, len(a), "New")
        radius = rational(input_radius)
        require(radius >= 0, "Input radius must be nonnegative")
    else:
        B = Bp = radius = None
    data, audit = [], {}
    delta = tuple(y-x for x, y in zip(a, ap))
    for pair in pairs:
        require(type(pair) in (tuple, list) and len(pair) == 2, "Each pair needs old and new raw input")
        left, right = pair
        require(type(left) is tuple and type(right) is tuple and
                len(left) == len(right) == len(a), "Pair input dimensions/types differ")
        try:
            x, xp = cb.decode_vector(left, fmt), cb.decode_vector(right, fmt)
        except cb.BoundRefused as exc:
            raise MarginRefused(str(exc)) from None
        distance = max(abs(v-u) for u, v in zip(x, xp))
        if B is not None:
            require(all(abs(v) <= bound for v, bound in zip(x, B)), "Old actual input outside declared old domain")
            require(all(abs(v) <= bound for v, bound in zip(xp, Bp)), "New actual input outside declared new domain")
            require(distance <= radius, "Actual input-pair radius exceeds declared radius")
        old = trace_guard(old_row, old_bias, left, fmt, policy=policy)
        new = trace_guard(new_row, new_bias, right, fmt, policy=policy)
        old_g, new_g = old["decoded_output"][0], new["decoded_output"][0]
        endpoint_term = sum((v*u for v, u in zip(delta, x)), Fraction(0))+(bp-b)
        input_term = sum((v*(y-z) for v, z, y in zip(ap, x, xp)), Fraction(0))
        signed_old, signed_new = old["row_signed_errors"][0], new["row_signed_errors"][0]
        require(new_g-old_g == endpoint_term+input_term+signed_new-signed_old,
                "Exact guard error decomposition failed")
        for trace in (old, new):
            for key, value in trace["arithmetic_counts"].items():
                audit[key] = audit.get(key, 0)+value
        data.append({"old_input_words": left, "new_input_words": right,
                     "old_input": x, "new_input": xp, "input_distance_linf": distance,
                     "old_output_word": old["output_words"][0], "new_output_word": new["output_words"][0],
                     "old_exact_guard": old["exact_output"][0], "new_exact_guard": new["exact_output"][0],
                     "old_executed_guard": old_g, "new_executed_guard": new_g,
                     "old_signed_error": signed_old, "new_signed_error": signed_new,
                     "rho_old": old["rho_linf"], "rho_new": new["rho_linf"],
                     "endpoint_change_term": endpoint_term, "input_change_term": input_term,
                     "actual_guard_change": new_g-old_g,
                     "point_guard_change_bound": abs(endpoint_term)+abs(input_term)+old["rho_linf"]+new["rho_linf"],
                     "old_branch": old_g > 0, "new_branch": new_g > 0,
                     "branches_equal": (old_g > 0) == (new_g > 0),
                     "old_branch_output": int(old_g > 0), "new_branch_output": int(new_g > 0)})
    return {"format": fmt, "guard": GUARD, "numerical_policy": policy,
            "pair_count": len(data), "pairs": data,
            "branch_changes": sum(not row["branches_equal"] for row in data),
            "all_declared_branches_equal": all(row["branches_equal"] for row in data),
            "both_domains_and_radius_checked": all(supplied),
            "arithmetic_counts": audit, "scope": "the supplied finite family only",
            "global_trajectory_containment_verified": False, "authorizes_live_commit": False}


def relu_words(words, fmt):
    """Coordinatewise exact ReLU on canonical finite words; no rotation rule."""
    require(type(words) is tuple, "Immutable finite ReLU input required")
    try:
        decoded = cb.decode_vector(words, fmt)
    except cb.BoundRefused as exc:
        raise MarginRefused(str(exc)) from None
    return tuple(0 if value < 0 else word for word, value in zip(words, decoded))
