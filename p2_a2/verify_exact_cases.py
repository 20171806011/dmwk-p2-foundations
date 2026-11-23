"""Finite exact-algebra validation for P2-A2; no FP execution is certified."""
from __future__ import annotations

from fractions import Fraction
import itertools
import random
import time

import exact_projection as q

SEED = 20261114


class Checks:
    def __init__(self):
        self.count = 0

    def __call__(self, condition, message):
        self.count += 1
        if not condition:
            raise AssertionError(message)

    def rejects(self, function, message):
        self.count += 1
        try:
            function()
        except (ValueError, TypeError):
            return
        raise AssertionError(message)


def _flatten(a):
    return tuple(x for row in a.rows for x in row)


def _column(values):
    return q.matrix(tuple((x,) for x in values))


def _permutation(order):
    return q.matrix(tuple(tuple(int(j == index) for j in range(len(order))) for index in order))


def _properties(h, checks, *, generator=None, audit=None):
    certificate = q.projection(h, audit=audit)
    p, d, r = certificate.P_perp, certificate.d, certificate.rank
    checks(q.transpose(p) == p, "Projection symmetry")
    checks(q.matmul(p, p) == p, "Projection idempotence")
    checks(q.matmul(p, h) == q.zeros(d, h.ncols), "Global H annihilation")
    checks(q.rank(p) == d-r, "Projection rank")
    checks(q.rank(certificate.N) == d-r, "Null-basis rank")
    checks(q.matmul(q.transpose(h), certificate.N) == q.zeros(h.ncols, d-r), "Null-basis equations")
    checks(q.project_via_nullspace(h) == p, "Column-space and null-space projector formulas agree")
    checks(q.add(certificate.P_D, p) == q.eye(d), "Complementary projectors sum to identity")
    checks(q.matmul(certificate.P_D, p) == q.zeros(d, d), "Orthogonal complementary images")
    checks(q.apply_perp_matrix_free(certificate.B, q.eye(d)) == p, "Matrix-free application agrees")
    g = q.eye(d) if generator is None else generator
    update = q.project_update(g, certificate)
    checks(q.matmul(update, h) == q.zeros(g.nrows, h.ncols), "Projected update annihilates H")
    checks(q.matmul(update, p) == update, "All produced updates factor through complement")
    checks(q.rank(update) <= min(q.rank(g), d-r), "Projected update rank bound")
    checks(q.apply_perp_matrix_free(certificate.B, q.transpose(g)) == q.transpose(update),
           "Right update projection equals transposed matrix-free application")
    if d <= 3:
        # Generate the image of every elementary candidate matrix under G -> GP.
        generators = []
        for i in range(d):
            for j in range(d):
                elementary = q.matrix(tuple(tuple(int(a == i and b == j) for b in range(d))
                                            for a in range(d)), ncols=d)
                generators.append(_flatten(q.matmul(elementary, p)))
        represented_dimension = q.rank(q.matrix(generators, ncols=d*d))
        checks(represented_dimension == d*(d-r), "Square update-space dimension differs from single-matrix rank")
    return certificate


def run_checks():
    start = time.perf_counter()
    checks = Checks()
    rng = random.Random(SEED)
    examples = []
    named = [
        ("no_activation_columns", q.zeros(3, 0)),
        ("zero_rank_with_zero_columns", q.zeros(3, 2)),
        ("zero_ambient_dimension", q.zeros(0, 3)),
        ("partial_repeated_and_zero_columns", q.matrix(((1, 1, 0), (1, 1, 0), (0, 0, 0)))),
        ("full_rank", q.eye(3)),
        ("thirds_projector", q.matrix(((1,), (1,), (1,)))),
        ("two_protected_coordinates", q.matrix(((1, 0), (0, 1), (0, 0)))),
    ]
    for name, h in named:
        audit = q.ArithmeticAudit()
        certificate = _properties(h, checks, audit=audit)
        examples.append({"name": name, **q.serialize_projection(certificate), "construction_cost": audit.summarize()})

    exhaustive = []
    # All 3^4 ternary 2x2 and all 2^6 binary 2x3 input matrices.
    for shape, alphabet in (((2, 2), (-1, 0, 1)), ((2, 3), (0, 1))):
        nrows, ncols = shape
        rank_histogram = {}
        count = 0
        for entries in itertools.product(alphabet, repeat=nrows*ncols):
            h = q.matrix(tuple(tuple(entries[i*ncols+j] for j in range(ncols)) for i in range(nrows)))
            certificate = _properties(h, checks)
            rank_histogram[str(certificate.rank)] = rank_histogram.get(str(certificate.rank), 0)+1
            count += 1
        exhaustive.append({"shape": list(shape), "alphabet": list(alphabet), "cases": count,
                           "rank_histogram": rank_histogram, "failures": 0})

    random_cases = []
    permutation_checks = 0
    for index in range(60):
        d, m = rng.randrange(1, 6), rng.randrange(0, 7)
        h = q.matrix(tuple(tuple(Fraction(rng.randrange(-3, 4), rng.randrange(1, 5)) for _ in range(m))
                           for _ in range(d)), ncols=m)
        g = q.matrix(tuple(tuple(Fraction(rng.randrange(-3, 4), rng.randrange(1, 4)) for _ in range(d))
                           for _ in range(d)))
        before = time.perf_counter(); audit = q.ArithmeticAudit()
        certificate = _properties(h, checks, generator=g, audit=audit)
        elapsed = time.perf_counter()-before
        order = tuple(rng.sample(range(d), d))
        s = _permutation(order); st = q.transpose(s)
        transformed = q.projection(q.matmul(s, h))
        checks(transformed.P_perp == q.matmul(q.matmul(s, certificate.P_perp), st), "Projector covariance")
        # Both input and output coordinates changed: G' = S G S^T.
        transformed_g = q.matmul(q.matmul(s, g), st)
        delta = q.project_update(g, certificate)
        transformed_delta = q.project_update(transformed_g, transformed)
        checks(transformed_delta == q.matmul(q.matmul(s, delta), st), "Update covariance")
        h_a = _column(tuple(Fraction(rng.randrange(-2, 3)) for _ in range(d)))
        checks(q.matmul(transformed_delta, q.matmul(s, h_a)) == q.matmul(s, q.matmul(delta, h_a)),
               "Input/output covariance")
        permutation_checks += 1
        random_cases.append({"case": index, "dimension": d, "columns": m, "protected_rank": certificate.rank,
                             "candidate_rank": q.rank(g), "update_rank": q.rank(delta),
                             "seconds": elapsed, "construction_cost": audit.summarize()})

    # A nontrivial fixed rank-two geometry under every coordinate permutation.
    cov_h = q.matrix(((1, 0), (2, 1), (0, 1)))
    cov_g = q.matrix(((1, 2, 0), (0, -1, 3), (2, 0, 1)))
    cov_a = _column((1, 0, 0)); cov_cert = q.projection(cov_h)
    cov_delta = q.project_update(cov_g, cov_cert)
    exhaustive_covariance = []
    for order in itertools.permutations(range(3)):
        s = _permutation(order); st = q.transpose(s)
        transformed_cert = q.projection(q.matmul(s, cov_h))
        transformed_delta = q.project_update(q.matmul(q.matmul(s, cov_g), st), transformed_cert)
        checks(transformed_cert.P_perp == q.matmul(q.matmul(s, cov_cert.P_perp), st),
               "Exhaustive 3-coordinate projector covariance")
        checks(transformed_delta == q.matmul(q.matmul(s, cov_delta), st),
               "Exhaustive 3-coordinate update covariance")
        checks(q.matmul(transformed_delta, q.matmul(s, cov_a)) == q.matmul(s, q.matmul(cov_delta, cov_a)),
               "Exhaustive 3-coordinate response covariance")
        exhaustive_covariance.append({"permutation": list(order), "projector": q.serialize(transformed_cert.P_perp)})

    # Construct a response to an input outside the protected span.
    protected = q.matrix(((1,), (1,), (1,)))
    certificate = q.projection(protected)
    a = _column((1, 0, 0)); z = q.matmul(certificate.P_perp, a)
    y = _column((1, 0, 0)); denominator = q.matmul(q.transpose(z), a).rows[0][0]
    useful = q.scale(q.matmul(y, q.transpose(z)), Fraction(1)/denominator)
    checks(denominator > 0, "Outside-space input yields positive complement energy")
    checks(q.matmul(useful, protected) == q.zeros(3, 1), "Useful update preserves protected algebra")
    checks(q.matmul(useful, a) == y, "Useful update attains nonzero target response")
    checks(q.rank(useful) == 1, "Constructed useful update is rank one")
    useless = certificate.P_perp
    checks(q.rank(useless) > 0 and q.matmul(useless, protected) == q.zeros(3, 1),
           "Nonzero safe algebra update can be useless for a protected AI input")
    h_e1 = _column((1, 0, 0)); p_e1 = q.projection(h_e1)
    narrow_update = q.matrix(((0, 0, 0), (0, 1, 0), (0, 0, 0)))
    outside_but_ignored = _column((0, 0, 1))
    checks(q.matmul(p_e1.P_perp, outside_but_ignored) != q.zeros(3, 1), "Ignored AI input lies outside V")
    checks(q.matmul(narrow_update, h_e1) == q.zeros(3, 1) and q.rank(narrow_update) == 1,
           "Narrow update is a nonzero annihilator")
    checks(q.matmul(narrow_update, outside_but_ignored) == q.zeros(3, 1),
           "A particular annihilator can miss an outside AI input")

    # Local spaces cannot stand in for a shared global matrix's space.
    left = q.projection(_column((1, 0))); right = q.projection(_column((0, 1)))
    merged = q.projection(q.eye(2))
    checks(q.rank(left.P_perp) == q.rank(right.P_perp) == 1, "Local rank deficiencies")
    checks(merged.P_perp == q.zeros(2, 2), "Merged shared space is full rank")
    checks(q.matmul(left.P_perp, _column((0, 1))) != q.zeros(2, 1), "Local projection interferes with another site")

    # Explicit conservative upper bound can deliberately remove actual freedom.
    actual = q.projection(_column((1, 0, 0)))
    conservative = q.projection(q.matrix(((1, 0), (0, 1), (0, 0))))
    checks(q.matmul(conservative.P_perp, actual.H) == q.zeros(3, 1), "Superspace protects actual activations")
    checks(q.rank(conservative.P_perp) < q.rank(actual.P_perp), "Superspace can reduce available capacity")

    # Low-rank candidate factorization enforces the sharper rank bound.
    low_rank_g = q.matmul(_column((1, 2, 3)), q.matrix(((1, 0, -1),)))
    low_rank_delta = q.project_update(low_rank_g, certificate)
    checks(q.rank(low_rank_g) == 1 and q.rank(low_rank_delta) <= min(1, 3-certificate.rank),
           "Low-rank candidate sharp bound")

    # Public exact-domain checks: implicit rounding is not accepted as exact input.
    negative = [lambda: q.matrix(((1.0,),)), lambda: q.matrix(((True,),)),
                lambda: q.matrix(((1, 2), (3,))), lambda: q.inverse(q.zeros(2, 2)),
                lambda: q.matmul(q.eye(2), q.eye(3)),
                lambda: q.project_onto_columns(q.matrix(((1, 1), (1, 1)))),
                lambda: q.apply_perp_matrix_free(q.eye(2), q.eye(3))]
    for operation in negative:
        checks.rejects(operation, "Invalid exact algebra input must be rejected")

    return {"status": "passed", "seed": SEED, "check_count": checks.count,
            "check_unit": "Explicit algebra/property/refusal assertions in this stage",
            "failures": 0, "seconds": time.perf_counter()-start,
            "named_examples": examples, "exhaustive_input_families": exhaustive,
            "random_matrix_cases": random_cases, "random_matrix_case_count": len(random_cases),
            "permutation_covariance_cases": permutation_checks,
            "exhaustive_three_coordinate_covariance": {"cases": len(exhaustive_covariance),
                "H": q.serialize(cov_h), "G": q.serialize(cov_g), "records": exhaustive_covariance},
            "negative_input_cases": len(negative),
            "learning_response": {"protected_H": q.serialize(protected), "AI_input": q.serialize(a),
                "complement_component": q.serialize(z), "delta": q.serialize(useful),
                "response": q.serialize(q.matmul(useful, a)),
                "safe_but_useless_AI_input": q.serialize(protected),
                "safe_but_useless_nonzero_delta": q.serialize(useless),
                "outside_but_ignored_input": q.serialize(outside_but_ignored),
                "outside_but_ignored_delta": q.serialize(narrow_update),
                "scope": "Exact rational algebra, not stored-word or bit-execution authorization"},
            "shared_call_counterexample": {"local_left": q.serialize(left.P_perp),
                "local_right": q.serialize(right.P_perp), "global": q.serialize(merged.P_perp),
                "local_patch_response_at_other_site": q.serialize(q.matmul(left.P_perp, _column((0, 1))))},
            "counterexamples": {
                "C1_full_rank_no_nonzero_update": {"H": q.serialize(q.eye(3)),
                    "P_perp": q.serialize(q.zeros(3, 3)), "square_update_space_dimension": 0,
                    "reason": "The exact annihilator of the full input space contains only zero."},
                "C2_merged_calls_full_rank_local_projection_unsound": {
                    "local_left_P_perp": q.serialize(left.P_perp),
                    "local_right_P_perp": q.serialize(right.P_perp),
                    "global_P_perp": q.serialize(merged.P_perp),
                    "other_site_response_to_left_update": q.serialize(q.matmul(left.P_perp, _column((0, 1))))},
                "C7_safe_but_no_learning_response": {
                    "nonzero_update_for_AI_input_in_V": q.serialize(useless),
                    "AI_input_in_V": q.serialize(protected),
                    "response_in_V": q.serialize(q.matmul(useless, protected)),
                    "nonzero_update_missing_an_outside_input": q.serialize(narrow_update),
                    "AI_input_outside_V": q.serialize(outside_but_ignored),
                    "response_outside_V": q.serialize(q.matmul(narrow_update, outside_but_ignored))}},
            "conservative_superspace": {"actual_rank": actual.rank, "upper_bound_rank": conservative.rank,
                "actual_complement_rank": q.rank(actual.P_perp),
                "conservative_complement_rank": q.rank(conservative.P_perp)},
            "matrix_free": {"formula": "X-B(B^T B)^(-1)B^T X", "dense_projector_built_by_application": False,
                "factor_storage_entries_excluding_X_and_output": "d*r+r*r if Gram inverse cached",
                "dense_projector_entries": "d*d", "scope": "Exact equality checked; no speed or memory benchmark claim"},
            "evidence_scope": "Finite exact-rational cases; T1/T2 universal proofs are separate handwritten arguments",
            "SMT_queries": 0}


if __name__ == "__main__":
    import json
    from pathlib import Path
    if not __debug__:
        raise SystemExit("Use ordinary Python, not -O/-OO")
    result = run_checks()
    path = Path(__file__).resolve().with_name("exact_results.json")
    path.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "check_count": result["check_count"],
                      "seconds": result["seconds"], "output": str(path)}))
