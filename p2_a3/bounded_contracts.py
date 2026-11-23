"""Pointwise finite-arithmetic reports, never weight-commit permissions.

Stored endpoint subtraction and residual accounting use exact Fractions. The
performed multiply/add operations use the inherited, audited arithmetic policy.
Bias is the initial accumulator; it is not appended/reordered as another dot term.
"""
from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction

from a3_runtime import get_fp

POLICY = "a3-bias-first-separate-rne-canonical-zero-v1"


class BoundRejected(ValueError):
    pass


def _require(ok, message):
    if not ok:
        raise BoundRejected(message)


def _words(value, fmt):
    _require(type(value) is tuple, "An exact tuple of stored words is required")
    for word in value:
        _require(type(word) is int, "A raw word must be an exact int, not bool")
        _require(word != fmt.sign_mask, "Negative zero is outside this report policy")
        get_fp().decode_word(word, fmt)
    return value


def _matrix(value, fmt):
    _require(type(value) is tuple and len(value) > 0,
             "Nonempty immutable matrix rows required")
    for row in value:
        _words(row, fmt)
    d = len(value[0])
    _require(d > 0 and all(len(row) == d for row in value),
             "Positive consistent matrix width required")
    return value


def _eval(row, h, bias, fmt):
    fp = get_fp()
    audit = fp.Audit()
    acc = bias
    local_errors = []
    steps = []
    exact = fp.decode_word(bias, fmt)
    for index, (wi, hi) in enumerate(zip(row, h)):
        product_exact = fp.decode_word(wi, fmt) * fp.decode_word(hi, fmt)
        product_word = fp.mul_words(wi, hi, fmt, audit)
        product_value = fp.decode_word(product_word, fmt)
        rho = product_value - product_exact
        sum_exact = fp.decode_word(acc, fmt) + product_value
        acc = fp.add_words(acc, product_word, fmt, audit)
        sigma = fp.decode_word(acc, fmt) - sum_exact
        local_errors.extend((rho, sigma))
        exact += product_exact
        steps.append({"column": index, "product_word": product_word,
                      "accumulator_word": acc, "product_error": str(rho),
                      "addition_error": str(sigma)})
    decoded = fp.decode_word(acc, fmt)
    error = decoded - exact
    bound = sum(map(abs, local_errors), Fraction(0))
    _require(error == sum(local_errors, Fraction(0)), "Rounding identity failed")
    _require(abs(error) <= bound, "Local absolute bound failed")
    return {"word": acc, "value": decoded, "exact": exact,
            "error": error, "bound": bound, "steps": steps,
            "audit": asdict(audit)}


def pointwise_report(old_words, new_words, input_words, format_name,
                     *, old_bias_words=None, new_bias_words=None,
                     policy=POLICY):
    """Certify a posteriori absolute bounds for one declared stored input.

    Missing new bias means the same bias as old. Explicit replacement biases
    are included in the actual affine endpoint difference. Returned objects
    are diagnostic data, not trusted capabilities or global certificates.
    """
    _require(type(policy) is str and policy == POLICY, "Uncertified arithmetic policy")
    _require(type(format_name) is str, "Exact format name required")
    fp = get_fp()
    fmt = fp.get_format(format_name)
    old_words = _matrix(old_words, fmt)
    new_words = _matrix(new_words, fmt)
    _require(len(old_words) == len(new_words) and len(old_words[0]) == len(new_words[0]),
             "Endpoint shapes differ")
    input_words = _words(input_words, fmt)
    _require(len(input_words) == len(old_words[0]), "Input width differs")
    k = len(old_words)
    if old_bias_words is None:
        old_bias_words = (0,) * k
    if new_bias_words is None:
        new_bias_words = old_bias_words
    _words(old_bias_words, fmt)
    _words(new_bias_words, fmt)
    _require(len(old_bias_words) == len(new_bias_words) == k, "Bias shape differs")
    rows = []
    for old, new, b, bp in zip(old_words, new_words, old_bias_words, new_bias_words):
        a = _eval(old, input_words, b, fmt)
        z = _eval(new, input_words, bp, fmt)
        exact_effect = z["exact"] - a["exact"]
        output_difference = z["value"] - a["value"]
        _require(output_difference == exact_effect + z["error"] - a["error"],
                 "Endpoint/output decomposition failed")
        beta = abs(exact_effect) + a["bound"] + z["bound"]
        _require(abs(output_difference) <= beta, "Pointwise output bound failed")
        rows.append({
            "exact_effective_affine_response": str(exact_effect),
            "actual_output_difference": str(output_difference),
            "absolute_output_bound": str(beta),
            "old_output_word": a["word"], "new_output_word": z["word"],
            "raw_words_equal": a["word"] == z["word"],
            "old_error": str(a["error"]), "new_error": str(z["error"]),
            "old_local_error_bound": str(a["bound"]),
            "new_local_error_bound": str(z["bound"]),
            "old_steps": a["steps"], "new_steps": z["steps"],
            "old_audit": a["audit"], "new_audit": z["audit"],
        })
    return {
        "schema": "dmwk-p2-a3-pointwise-v1", "contract": "pointwise_bounded",
        "authorizes_commit": False,
        "scope": "This stored input and these endpoints only; no global or time-uniform claim",
        "format": format_name, "policy": policy,
        "old_words": old_words, "new_words": new_words,
        "old_bias_words": old_bias_words, "new_bias_words": new_bias_words,
        "input_words": input_words,
        "effective_weight_difference": [
            [str(fp.decode_word(vp, fmt)-fp.decode_word(v, fmt)) for v,vp in zip(r,rp)]
            for r,rp in zip(old_words,new_words)],
        "rows": rows,
        "infinity_norm_output_bound": str(max(Fraction(r["absolute_output_bound"]) for r in rows)),
        "all_output_words_equal_on_this_input": all(r["raw_words_equal"] for r in rows),
        "bound_type": "Exact rational a posteriori absolute local errors; subnormals included; overflow refused",
    }
