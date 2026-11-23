"""Independent finite exact-rank checks; no P1 suite or backend is executed."""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path
from fractions import Fraction
import time
import activation_spaces as algebra


def determinant(matrix):
    n = len(matrix)
    if n == 0:
        return Fraction(1)
    if n == 1:
        return matrix[0][0]
    return sum(((-1)**j * matrix[0][j] * determinant(
        tuple(tuple(row[k] for k in range(n) if k != j)
              for row in matrix[1:])) for j in range(n)), Fraction(0))


def rank_from_minors(rows, dimension):
    for size in range(min(len(rows), dimension), 0, -1):
        for row_ids in itertools.combinations(range(len(rows)), size):
            for column_ids in itertools.combinations(range(dimension), size):
                if determinant(tuple(tuple(Fraction(rows[i][j]) for j in column_ids)
                                     for i in row_ids)):
                    return size
    return 0


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    started = time.perf_counter()
    cases = 0
    for flat in itertools.product((0, 1), repeat=9):
        rows = tuple(tuple(flat[3*i+j] for j in range(3)) for i in range(3))
        basis = algebra.span(rows, 3)
        check(basis.rank == rank_from_minors(rows, 3), "Rank/minor disagreement")
        check(all(basis.contains(row) for row in rows), "Generator containment failed")
        reversed_basis = algebra.span(tuple(reversed(rows)), 3)
        check(basis.rows == reversed_basis.rows, "RREF row-order invariance failed")
        cases += 1
    special = [((), 0), (((0, 0), (0, 0)), 2),
               (((1, 0), (1, Fraction(1, 2**149))), 2),
               (((Fraction(1, 3), Fraction(2, 7)),
                 (Fraction(2, 3), Fraction(4, 7))), 2)]
    for rows, dimension in special:
        check(algebra.span(rows, dimension).rank == rank_from_minors(rows, dimension),
              "Additional rational rank case failed")
    relu_basis = ((1, 1, 0), (0, 1, 1))
    relu_space = algebra.span(relu_basis, 3)
    relu = lambda v: tuple(max(0, x) for x in v)
    check(all(relu(v) == v for v in relu_basis), "ReLU fixes the declared basis")
    check(relu_space.contains((1, 0, -1)), "ReLU witness belongs to the span")
    check(not relu_space.contains(relu((1, 0, -1))),
          "ReLU basis-only closure counterexample failed")
    dormant = algebra.enumerate_reachable(
        (0,), lambda state: (), lambda state, incoming: (state, ()),
        universe=frozenset({0}), matrix_dimensions={"dormant": 3},
        declared_sites=(("dormant", "never"),)).spaces()
    check(dormant["per_matrix"]["dormant"]["rank_Q_equals_rank_R"] == 0,
          "Uncalled matrix must be reported with rank zero")
    check(dormant["per_call_site"][0]["rank_Q_equals_rank_R"] == 0,
          "Unreachable call site must be reported with rank zero")
    negative = 0
    for action in [lambda: algebra.span(((1.0, 0),), 2),
                   lambda: algebra.span(((True, 0),), 2),
                   lambda: algebra.span(((1, 2, 3),), 2),
                   lambda: algebra.enumerate_reachable(
                       (0,), lambda state: (0,), lambda state, incoming: (1, ()),
                       universe=frozenset({0}))]:
        try:
            action()
        except (ValueError, TypeError):
            negative += 1
        else:
            raise AssertionError("Expected argument/closure rejection")
    report = {
        "schema": "p2-a1-independent-review-checks-v1", "status": "passed",
        "scope": "Exact rank library only; independent determinant/minor reference and argument rejection; no P1 suites or P2-A2 actions",
        "exhaustive_binary_3x3_matrices": cases,
        "row_order_invariance_cases": cases,
        "additional_exact_rational_cases": len(special),
        "relu_basis_only_closure_counterexamples": 1,
        "declared_uncalled_matrix_and_site_checks": 1,
        "negative_argument_cases": negative,
        "elapsed_seconds": time.perf_counter()-started,
        "implementation_sha256": hashlib.sha256(Path(algebra.__file__).read_bytes()).hexdigest(),
        "review_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "not_tested": ["All arbitrary rational matrices", "Floating-point backend certification",
                       "BFS monitor faithfulness for arbitrary user-supplied callbacks",
                       "Whole proof-assistant verification"]}
    path = Path(__file__).resolve().with_name("review_checks.json")
    path.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": report["status"], "matrix_cases": cases,
                      "additional_cases": len(special), "negative_cases": negative}))


if __name__ == "__main__":
    main()
