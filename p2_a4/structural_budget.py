"""A4 exact row-mask budgets and a small reserved-column execution layout.

The layout functions are pure immutable-bank evaluations, not a new live
certificate/commit interface. A3's supported live transactions are tested
separately. No previous-stage verifier is imported or executed.
"""
from __future__ import annotations

from fractions import Fraction

from a4_runtime import get_fp, load_a2

xp = load_a2("exact_projection")
POLICY = "p2-a4-reserved-column-sparse-rne-v1"
MODELS = ("axis_reserve_v1", "correlated_reserve_v1")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def _exact_matrix(value):
    require(type(value) is xp.Matrix, "An exact rational Matrix value is required")
    return xp.matrix(value.rows, ncols=value.ncols)


def mask_budget(protected_generators, masks, targets=None):
    """Exact dimension with row-specific support restrictions.

    Global-domain provenance is a separate premise. A masked row can require
    correlated coefficients; its listed cells are not automatically free.
    """
    h = _exact_matrix(protected_generators)
    require(h.nrows >= 1, "Positive input dimension required")
    require(type(masks) is tuple and len(masks) >= 1, "Nonempty tuple of row masks required")
    d, n = h.nrows, len(masks)
    if targets is not None:
        targets = _exact_matrix(targets)
        require(targets.nrows == d, "Target and protected input dimensions differ")
    rows = []
    for index, allowed in enumerate(masks):
        require(type(allowed) is tuple, "A row mask must be an exact tuple")
        require(all(type(j) is int and 0 <= j < d for j in allowed),
                "Mask coordinates must be in-range built-in integers")
        require(allowed == tuple(sorted(set(allowed))), "Mask coordinates must be unique and sorted")
        restricted = xp.matrix(tuple(h.rows[j] for j in allowed), ncols=h.ncols)
        restricted_rank = xp.rank(restricted)
        free = len(allowed) - restricted_rank
        response_dimension = None
        if targets is not None:
            joined = xp.matrix(tuple(h.rows[j] + targets.rows[j] for j in allowed),
                               ncols=h.ncols + targets.ncols)
            response_dimension = xp.rank(joined) - restricted_rank
        rows.append({"row": index, "allowed_columns": list(allowed),
                     "allocated_cells": len(allowed), "restricted_protected_rank": restricted_rank,
                     "exact_free_dimension": free,
                     "every_allowed_cell_independently_safe": restricted_rank == 0,
                     "target_response_dimension": response_dimension})
    r = xp.rank(h)
    dimension = sum(x["exact_free_dimension"] for x in rows)
    full = n * (d-r)
    require(0 <= dimension <= full, "Mask subspace dimension cannot exceed geometric dimension")
    return {"schema": "dmwk-p2-a4-row-mask-budget-v1", "input_dimension": d,
            "output_dimension": n, "protected_rank": r,
            "geometric_update_space_dimension": full,
            "masked_update_space_dimension": dimension,
            "mask_dimension_loss": full-dimension,
            "allocated_cells": sum(x["allocated_cells"] for x in rows),
            "rows": rows,
            "masked_target_response_dimension": None if targets is None else sum(x["target_response_dimension"] for x in rows),
            "global_provenance_verified": False, "authorizes_live_commit": False,
            "scope": "Exact rational supplied-span algebra; not stored or executable capacity"}


def layout_budget(model_id):
    require(type(model_id) is str and model_id in MODELS, "Unknown layout model")
    activations = [(q, u if model_id == "axis_reserve_v1" else q, 0)
                   for q in (0, 1) for u in (0, 1)]
    h = xp.matrix(tuple(tuple(a[j] for a in activations) for j in range(3)))
    target = xp.matrix(((0,), (0,), (1,)))
    result = mask_budget(h, ((2,), (2,)), target)
    result.update({"model_id": model_id, "protected_generators": xp.serialize(h),
                   "complete_activation_domain": [list(a) for a in sorted(set(activations))],
                   "initial_states": [0, 1], "external_inputs": [0, 1],
                   "state_recurrence": "q_next = q XOR u, using first protected output and old input",
                   "fixed_bias": [0, 0], "D_read_columns": [0, 1], "A_target": "e3",
                   "layout_domain_provenance": "Declared complete Boolean domain and separate closure proof",
                   "provenance_scope": "The generic mask helper does not certify reachability; this fixed layout has a separately proved complete domain"})
    return result


def canonical_finite_word_count(format_name):
    fp = get_fp()
    require(type(format_name) is str, "Built-in format name required")
    fmt = fp.get_format(format_name)
    return (1 << fmt.total_bits) - 2 * (1 << fmt.fraction_bits) - 1


def finite_reserved_counts(format_name):
    count = canonical_finite_word_count(format_name)
    return {"format": format_name, "canonical_finite_words": count,
            "reserved_endpoint_count": count**2, "changed_endpoint_count": count**2-1,
            "A_e3_response_count": count**2, "A_e3_changed_response_count": count**2-1,
            "A_e1_response_count": 1,
            "scope": "Theorem count for the two independently reserved words; not an exhaustive pair-space experiment",
            "vector_space_dimension_claim": False}


def _format(format_name):
    require(type(format_name) is str and format_name in ("BF16", "FP32"), "Unsupported format")
    return get_fp().get_format(format_name)


def _word(raw, format_name):
    fmt = _format(format_name)
    require(type(raw) is int and 0 <= raw < (1 << fmt.total_bits), "In-range built-in raw word required")
    require(((raw >> fmt.fraction_bits) & fmt.exponent_mask) != fmt.exponent_mask,
            "Nonfinite word refused")
    require(raw != fmt.sign_mask, "Negative-zero storage refused")
    get_fp().decode_word(raw, fmt)
    return raw


def _bank(bank, format_name):
    require(type(bank) is tuple and len(bank) == 2 and
            all(type(row) is tuple and len(row) == 3 for row in bank),
            "An immutable two-by-three bank is required")
    for row in bank:
        for raw in row:
            _word(raw, format_name)
    one = get_fp().encode_constant(1, format_name)
    require(bank[0][:2] == (one, 0) and bank[1][:2] == (0, one),
            "Protected coordinate block differs from fixed identity")
    return bank


def reserved_bank(theta_words, format_name):
    require(type(theta_words) is tuple and len(theta_words) == 2, "Two reserved raw words required")
    theta = tuple(_word(x, format_name) for x in theta_words)
    one = get_fp().encode_constant(1, format_name)
    return ((one, 0, theta[0]), (0, one, theta[1]))


def initial_bank(format_name):
    return reserved_bank((0, 0), format_name)


def validate_reserved_pair(old_bank, new_bank, format_name):
    old = _bank(old_bank, format_name)
    new = _bank(new_bank, format_name)
    fp = get_fp()
    return {"contract": "pure_reserved_layout_endpoint_check",
            "old_words": old, "new_words": new,
            "effective_difference": [[str(fp.decode_word(b, format_name)-fp.decode_word(a, format_name))
                                       for a,b in zip(ro,rn)] for ro,rn in zip(old,new)],
            "protected_read_words_unchanged": True, "authorizes_live_commit": False,
            "scope": "Immutable endpoint/layout evidence; no new live transaction interface"}


def _policy(policy):
    require(type(policy) is str and policy == POLICY, "Unsupported execution policy")


def _bit(raw, format_name):
    one = get_fp().encode_constant(1, format_name)
    require(type(raw) is int and raw in (0, one), "Canonical Boolean raw word required")
    return raw


def _audit(audit):
    return {key: getattr(audit, key) for key in
            ("native_multiply", "native_add", "software_multiply", "software_add",
             "exact_sums", "native_oracle_checks")}


def _d(bank, q_word, u_word, format_name, model_id, audit):
    fp = get_fp()
    h = (q_word, u_word if model_id == "axis_reserve_v1" else q_word)
    out = []
    for row in bank:
        accumulator = 0
        for j in (0, 1):
            product = fp.mul_words(row[j], h[j], format_name, audit)
            accumulator = fp.add_words(accumulator, product, format_name, audit)
        out.append(accumulator)
    return tuple(out)


def d_call(bank, q_word, u_word, format_name, model_id="axis_reserve_v1", *, policy=POLICY):
    _policy(policy)
    require(type(model_id) is str and model_id in MODELS, "Unknown layout model")
    bank = _bank(bank, format_name)
    _bit(q_word, format_name); _bit(u_word, format_name)
    audit = get_fp().Audit()
    return _d(bank, q_word, u_word, format_name, model_id, audit), _audit(audit)


def tick_snapshot(bank, q_word, u_word, format_name, model_id="axis_reserve_v1", *, policy=POLICY):
    """Pure next-state calculation from one immutable old bank/state snapshot."""
    _policy(policy)
    require(type(model_id) is str and model_id in MODELS, "Unknown layout model")
    bank = _bank(bank, format_name)
    _bit(q_word, format_name); _bit(u_word, format_name)
    fp = get_fp(); audit = fp.Audit()
    output = _d(bank, q_word, u_word, format_name, model_id, audit)
    product = fp.mul_words(output[0], u_word, format_name, audit)
    twice = fp.mul_words(fp.encode_constant(2, format_name), product, format_name, audit)
    negative = fp.mul_words(fp.encode_constant(-1, format_name), twice, format_name, audit)
    summed = fp.add_words(output[0], u_word, format_name, audit)
    successor = fp.add_words(summed, negative, format_name, audit)
    _bit(successor, format_name)
    return output, successor, _audit(audit)


def a_output(bank, format_name, *, target="e3", policy=POLICY):
    _policy(policy)
    bank = _bank(bank, format_name)
    require(type(target) is str and target in ("e3", "e1"), "Unsupported declared A target")
    column = 2 if target == "e3" else 0
    fp = get_fp(); audit = fp.Audit(); one = fp.encode_constant(1, format_name)
    outputs = tuple(fp.add_words(0, fp.mul_words(row[column], one, format_name, audit),
                                 format_name, audit) for row in bank)
    return outputs, _audit(audit)


def probe_reserved_scalar(raw, format_name):
    """Execute the declared one-coordinate A read for one accepted stored word."""
    raw = _word(raw, format_name)
    fp = get_fp(); audit = fp.Audit()
    product = fp.mul_words(raw, fp.encode_constant(1, format_name), format_name, audit)
    output = fp.add_words(0, product, format_name, audit)
    return output, _audit(audit)
