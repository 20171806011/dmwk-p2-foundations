"""B4 exact capacity histories and complete named finite endpoint families.

Stored differences are decoded exactly. Generic supplied spans are not global
domain proofs. Raw-domain BIT and A3 certificate acceptance are separate sets.
Nothing in this module authorizes live endpoint or optimizer publication.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import product
import hashlib
import json

from b4_runtime import get_fp, load_a2, load_a3, load_a4

xp = load_a2("exact_projection")
ca = load_a4("capacity_algebra")
cd = load_a4("capacity_discrete")
ck = load_a3("certificate_kernel")


class CapacityRefused(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise CapacityRefused(message)


def _matrix(value):
    require(type(value) is xp.Matrix, "Exact immutable rational Matrix required")
    return value


def record(value):
    if type(value) is Fraction:
        return [value.numerator, value.denominator]
    if type(value) is xp.Matrix:
        return {"shape": [value.nrows, value.ncols], "rows": record(value.rows)}
    if type(value) in (tuple, list):
        return [record(v) for v in value]
    if type(value) is dict:
        require(all(type(k) is str for k in value), "Record keys must be strings")
        return {k: record(v) for k, v in value.items()}
    require(value is None or type(value) in (int, str, bool), "Unsupported record value")
    return value


def _zero(matrix):
    return all(v == 0 for row in matrix.rows for v in row)


def _words(words, fmt):
    require(type(words) in (tuple, list) and len(words) >= 1, "Nonempty endpoint rows required")
    require(all(type(row) in (tuple, list) for row in words), "Endpoint rows must be sequences")
    width = len(words[0])
    require(width >= 1 and all(len(row) == width for row in words), "Positive rectangular endpoint required")
    return tuple(tuple(ck._word(v, fmt) for v in row) for row in words)


def decode_matrix(words, fmt):
    return cd.decode_matrix(_words(words, fmt), fmt)


def algebra_budget(H, output_rows, targets=None, rank_cap=None):
    _matrix(H)
    if targets is not None:
        _matrix(targets)
    report = ca.budget_report(H, output_rows, rank_cap=rank_cap, x=targets)
    return {**report, "global_provenance_verified": False,
            "coverage": "supplied algebraic span only; no samples-to-global inference",
            "authorizes_live_update": False,
            "target_scope": "declared exact target matrix; legal executable A interface not inferred"}


def registered_budget(model_id, fmt, output_rows=None, targets=None, rank_cap=None):
    descriptor = ck.model_descriptor(model_id, fmt)
    n, _ = descriptor["shape"]
    require(output_rows is None or (type(output_rows) is int and output_rows == n), "Registered output shape differs")
    H = cd.global_generators(model_id, fmt)
    report = algebra_budget(H, n, targets, rank_cap)
    return {**report, "global_provenance_verified": True, "registered_generators": H,
            "descriptor": descriptor, "coverage": "all calls in the fixed registered original envelope",
            "coverage_limit": "conditional registry/domain proof; not arbitrary application or modified-feedback reachability",
            "authorizes_live_update": False}


def response_feasibility(H, X, R, rank_cap=None):
    _matrix(H); _matrix(X); _matrix(R)
    solution, detail = ca.solve_response(H, X, R, rank_cap=rank_cap)
    return {"feasible": solution is not None, "solution": solution, "detail": detail,
            "scope": "exact response feasibility only; endpoint storage/BIT not established",
            "authorizes_live_update": False}


def joint_task_feasibility(tasks):
    require(type(tasks) in (tuple, list) and len(tasks) >= 1, "Nonempty task list required")
    hs, ys = [], []
    for item in tasks:
        require(type(item) in (tuple, list) and len(item) == 2, "Task must be (generators, desired outputs)")
        h, y = _matrix(item[0]), _matrix(item[1])
        require(h.ncols == y.ncols, "Task anchor column count mismatch")
        if hs:
            require(h.nrows == hs[0].nrows and y.nrows == ys[0].nrows, "Task dimensions differ")
        hs.append(h); ys.append(y)
    d, n = hs[0].nrows, ys[0].nrows
    require(d > 0 and n > 0, "Positive task dimensions required")
    H, Y = ca.concatenate(*hs), ca.concatenate(*ys)
    relations = xp.nullspace(H)
    residual = xp.matmul(Y, relations)
    compatible = _zero(residual)
    solution, detail = ca.solve_response(xp.zeros(d, 0), H, Y)
    require(compatible == (solution is not None), "Task relation and constructive feasibility disagree")
    witness = None
    if not compatible:
        bad = next(j for j in range(relations.ncols) if any(residual.rows[i][j] != 0 for i in range(n)))
        alpha = xp.Matrix(tuple((row[bad],) for row in relations.rows), 1)
        witness = {"alpha": alpha, "H_alpha": xp.matmul(H, alpha), "Y_alpha": xp.matmul(Y, alpha)}
    else:
        require(xp.matmul(solution, H) == Y, "Constructed joint anchor fails direct equations")
    r = xp.rank(H)
    return {"compatible": compatible, "combined_generators": H, "combined_anchors": Y,
            "combined_rank": r, "relation_basis": relations, "relation_residual": residual,
            "impossibility_witness": witness, "particular_solution": solution,
            "solution_affine_dimension": n*(d-r) if compatible else None,
            "construction_detail": detail, "pairwise_intersections_suffice": False,
            "storage_and_BIT_verified": False, "authorizes_live_update": False}


def task_anchor_check(words, fmt, H, Y):
    W = decode_matrix(words, fmt)
    _matrix(H); _matrix(Y)
    require(W.ncols == H.nrows and (W.nrows, H.ncols) == Y.shape, "Task anchor shape mismatch")
    actual = xp.matmul(W, H)
    residual = xp.sub(actual, Y)
    return {"anchor_satisfied": _zero(residual), "actual_outputs": actual,
            "desired_outputs": Y, "residual": residual,
            "future_annihilating_updates_can_repair_mismatch": False,
            "meaning": "freezing the new directions preserves their current anchor; it is not retroactive task satisfaction"}


def analyze_history(word_history, fmt, spaces, mode="fixed", targets=None, rank_cap=None):
    require(type(word_history) in (tuple, list) and len(word_history) >= 1, "Stored endpoint history required")
    words = tuple(_words(w, fmt) for w in word_history)
    decoded = tuple(decode_matrix(w, fmt) for w in words)
    n, d = decoded[0].shape
    require(all(w.shape == (n, d) for w in decoded), "History endpoint shapes differ")
    require(type(spaces) in (tuple, list) and all(type(h) is xp.Matrix and h.nrows == d for h in spaces), "Space generators mismatch")
    require(type(mode) is str and mode in ("fixed", "cumulative", "moving"), "Unknown protection evolution")
    count = len(decoded)-1
    require(len(spaces) == (1 if mode == "fixed" else count), "Protection schedule length mismatch")
    if targets is not None:
        _matrix(targets)
    # Reuse explicit A4 validation for the cap even when there are no updates.
    initial_space = spaces[0] if spaces else xp.zeros(d, 0)
    algebra_budget(initial_space, n, targets, rank_cap)
    prefixes = tuple(xp.sub(w, decoded[0]) for w in decoded)
    steps, increments, used_spaces = [], [], []
    running = xp.zeros(n, d)
    for k in range(count):
        H = spaces[0] if mode == "fixed" else (ca.concatenate(*spaces[:k+1]) if mode == "cumulative" else spaces[k])
        seen = spaces[0] if mode == "fixed" else ca.concatenate(*spaces[:k+1])
        delta = xp.sub(decoded[k+1], decoded[k])
        residual = xp.matmul(delta, H)
        alg = _zero(residual)
        r = xp.rank(delta)
        running = xp.add(running, delta)
        require(running == prefixes[k+1], "Actual endpoint telescope failed")
        steps.append({"update_index": k, "generators": H, "budget": algebra_budget(H, n, targets, rank_cap),
                      "effective_delta": delta, "update_rank": r, "current_space_residual": residual,
                      "annihilates_current_space": alg, "actual_rank_cap_satisfied": rank_cap is None or r <= rank_cap,
                      "algebraic_rank_bound_applicable": alg, "prefix_delta": running,
                      "prefix_rank": xp.rank(running),
                      "prefix_preserves_initial_space": _zero(xp.matmul(running, initial_space)),
                      "prefix_preserves_seen_union_relative_W0": _zero(xp.matmul(running, seen))})
        increments.append(delta); used_spaces.append(H)
    anchors = []
    arrivals = ((0, spaces[0]),) if mode == "fixed" else tuple(enumerate(spaces))
    for start, H in arrivals:
        observations = []
        for t in range(start, len(decoded)):
            difference = xp.sub(decoded[t], decoded[start])
            residual = xp.matmul(difference, H)
            observations.append({"endpoint_index": t, "residual": residual, "preserved": _zero(residual)})
        anchors.append({"arrival_index": start, "anchor_endpoint_index": start, "generators": H,
                        "anchor_outputs": xp.matmul(decoded[start], H), "observations": observations,
                        "preserved_since_arrival": all(x["preserved"] for x in observations)})
    final = prefixes[-1]
    fixed_safe = mode == "fixed" and all(step["annihilates_current_space"] for step in steps)
    fixed_bound = min(n, d-xp.rank(initial_space), sum(xp.rank(x) for x in increments)) if fixed_safe else None
    return {"format": fmt, "mode": mode, "update_count": count, "endpoint_words": words,
            "decoded_endpoints": decoded, "steps": steps, "actual_increments": tuple(increments),
            "prefix_differences": prefixes, "telescope_sum": running, "final_difference": final,
            "final_rank": xp.rank(final), "sum_individual_ranks": sum(xp.rank(x) for x in increments),
            "final_preserves_initial_space": _zero(xp.matmul(final, initial_space)),
            "every_prefix_preserves_initial_space": all(_zero(xp.matmul(p, initial_space)) for p in prefixes),
            "all_current_space_checks_pass": all(x["annihilates_current_space"] for x in steps),
            "task_anchors": anchors, "all_arrival_anchors_preserved": all(a["preserved_since_arrival"] for a in anchors),
            "fixed_space_cumulative_rank_bound": fixed_bound,
            "fixed_space_cap_bound": min(n, d-xp.rank(initial_space), count*rank_cap) if fixed_safe and rank_cap is not None and all(s["actual_rank_cap_satisfied"] for s in steps) else None,
            "global_provenance_verified": False, "authorizes_live_update": False,
            "scope": "exact supplied-span history of actual stored endpoints; no application reachability inferred"}


def quantize_proposal(old_words, ideal_increment, fmt):
    old_words = _words(old_words, fmt)
    old, ideal = decode_matrix(old_words, fmt), _matrix(ideal_increment)
    require(old.shape == ideal.shape, "Proposal shape mismatch")
    exact_candidate = xp.add(old, ideal)
    try:
        new_words = _words(tuple(tuple(get_fp().round_fraction(v, fmt) for v in row) for row in exact_candidate.rows), fmt)
    except (ValueError, OverflowError) as exc:
        raise CapacityRefused("Stored endpoint cannot be admitted: " + str(exc)) from None
    new = decode_matrix(new_words, fmt)
    delta = xp.sub(new, old)
    return {"old_words": old_words, "new_words": new_words, "ideal_increment": ideal,
            "effective_delta": delta, "storage_error": xp.sub(delta, ideal),
            "nonzero_ideal_increment": not _zero(ideal), "stored_noop": _zero(delta),
            "quantization_stall": not _zero(ideal) and _zero(delta), "authorizes_live_update": False}


def _protected_signature(model_id, fmt, words):
    desc = ck.model_descriptor(model_id, fmt)
    return tuple((site["id"], tuple(h), cd.dense_words(words, tuple(h), fmt))
                 for site in desc["sites"] for h in site["activations"])


def _json_key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _summarize(records, predicate):
    selected = [r for r in records if predicate(r)]
    total = [r for r in selected if r["A_execution_total"]]
    signatures = {_json_key(r["A_new_output_words"]) for r in total}
    changed = {_json_key(r["A_new_output_words"]) for r in total if r["A_any_raw_response_changed"]}
    return {"endpoints": len(selected), "nonzero_updates": sum(r["nonzero_effective_difference"] for r in selected),
            "effective_rank_histogram": dict(sorted(Counter(str(r["rank_effective_difference"]) for r in selected).items())),
            "exact_A_response_image_count": len({_json_key(r["exact_A_response"]) for r in selected}),
            "raw_A_response_image_count": len(signatures), "changed_raw_A_signatures": len(changed),
            "A_total_endpoints": len(total), "A_execution_refusals": len(selected)-len(total),
            "nonzero_updates_with_no_A_change": sum(r["nonzero_effective_difference"] and not r["A_any_raw_response_changed"] for r in total)}


def enumerate_endpoint_family(model_id, fmt, old_words, palette_words, targets=None,
                              mutable_cells=None, max_candidates=4096):
    descriptor = ck.model_descriptor(model_id, fmt)
    old_words = _words(old_words, fmt)
    n, d = descriptor["shape"]
    require(decode_matrix(old_words, fmt).shape == (n, d), "Registered endpoint shape mismatch")
    require(type(palette_words) in (tuple, list) and len(palette_words) > 0, "Nonempty raw palette required")
    palette = tuple(ck._word(v, fmt) for v in palette_words)
    require(len(set(palette)) == len(palette), "Duplicate palette words are not distinct endpoints")
    cells = tuple((i, j) for i in range(n) for j in range(d)) if mutable_cells is None else mutable_cells
    require(type(cells) in (tuple, list), "Explicit mutable-cell sequence required")
    require(all(type(c) in (tuple, list) and len(c) == 2 and all(type(v) is int for v in c)
                and 0 <= c[0] < n and 0 <= c[1] < d for c in cells), "Invalid mutable cell")
    cells = tuple(tuple(c) for c in cells)
    require(len(set(cells)) == len(cells), "Duplicate mutable cell")
    size = len(palette)**len(cells)
    require(type(max_candidates) is int and max_candidates > 0 and size <= max_candidates, "Named finite family exceeds declared enumeration limit")
    if targets is None:
        one = get_fp().encode_constant(1, fmt)
        targets = tuple(tuple(one if j == k else 0 for j in range(d)) for k in range(d))+((0,)*d,)
    require(type(targets) in (tuple, list) and all(type(h) in (tuple, list) for h in targets), "Target list type mismatch")
    targets = tuple(tuple(ck._word(v, fmt) for v in h) for h in targets)
    require(all(len(h) == d for h in targets), "Target shape mismatch")
    if descriptor["stateful"]:
        require(all(list(h) in descriptor["A_domain"] for h in targets), "Target outside registered legal A interface")
    try:
        old_signature = _protected_signature(model_id, fmt, old_words)
    except (ValueError, OverflowError) as exc:
        raise CapacityRefused("Old endpoint is not total on the fixed protected domain: " + str(exc)) from None
    records = []
    for choice in product(palette, repeat=len(cells)):
        new = [list(row) for row in old_words]
        for (i, j), word in zip(cells, choice): new[i][j] = word
        new = tuple(tuple(row) for row in new)
        classified = cd.classify_endpoint(model_id, fmt, old_words, new, targets)
        certificate = classified["BIT"]
        certificate_reason = classified.pop("bit_refusal_reason")
        certificate_sha = classified.pop("certificate_sha256")
        classified.pop("E_cert", None)
        reason, signature = None, None
        try:
            signature = _protected_signature(model_id, fmt, new)
            total, bit = True, signature == old_signature
        except (ValueError, OverflowError) as exc:
            total, bit, reason = False, False, str(exc)
        classified.update({"E_CERT": certificate, "BIT": bit, "ALG_AND_BIT": classified["ALG"] and bit,
                           "ALG_and_BIT": classified["ALG"] and bit,
                           "protected_execution_total": total, "protected_execution_error": reason,
                           "protected_signature": signature,
                           "A3_certificate_sha256": certificate_sha, "certificate_refusal_reason": certificate_reason,
                           "bit_refusal_reason": reason if not total else (None if bit else "Fixed-domain full-output words differ"),
                           "BIT_field_meaning": "actual total full-output equality at every registered raw call",
                           "E_CERT_field_meaning": "A3 certificate acceptance, including its extra invariant/valid-bank obligations"})
        records.append(classified)
    predicates = {"storable": lambda r: True, "ALG": lambda r: r["ALG"], "BIT": lambda r: r["BIT"],
                  "ALG_AND_BIT": lambda r: r["ALG"] and r["BIT"],
                  "ALG_NOT_BIT": lambda r: r["ALG"] and not r["BIT"],
                  "BIT_NOT_ALG": lambda r: r["BIT"] and not r["ALG"], "E_CERT": lambda r: r["E_CERT"]}
    absolute_family = {"format": fmt, "shape": [n, d], "palette_words": list(palette),
                       "mutable_cells": [list(c) for c in cells],
                       "fixed_cells": [[i, j, old_words[i][j]] for i in range(n) for j in range(d) if (i, j) not in cells]}
    return {"model_id": model_id, "format": fmt, "descriptor": descriptor, "old_words": old_words,
            "absolute_family": absolute_family,
            "absolute_family_sha256": hashlib.sha256(_json_key(absolute_family).encode()).hexdigest(),
            "enumerated_candidates": size, "old_endpoint_is_member": all(old_words[i][j] in palette for i, j in cells),
            "targets": targets, "target_scope": "registered legal A inputs" if descriptor["stateful"] else "declared stateless diagnostic observer",
            "global_generators": cd.global_generators(model_id, fmt), "old_protected_signature": old_signature,
            "groups": {name: _summarize(records, predicate) for name, predicate in predicates.items()},
            "records": records, "raw_BIT_is_live_authority": False,
            "scope": "complete named finite Cartesian family, not the entire floating format or a vector space",
            "authorizes_live_update": False}
