# P2-A1 — Deterministic activation spaces

This round defines the activation space seen by each fixed deterministic matrix over every legal initialization, input history, call site, and finite execution time. It establishes exact finite-state construction and conditional invariant-space certificates, with full-rank and deficient-rank examples. It does not implement P2-A2 or modify a protected weight program.

- [Saved research plan](P2_A1_Plan.md)
- [Definitions and execution assumptions](P2_A1_Definitions.md)
- [Theorems and complete handwritten proofs](P2_A1_Theorems.md)
- [Research report](P2_A1_Report.md)
- [Claim-to-evidence map](P2_A1_Evidence_Map.md)
- [Main executed results](verification_results.json)
- [Independent review](P2_A1_Review.md) and [finite rank checks](review_checks.json)

## Reproduce

Use Python 3.12 and NumPy 2.3.5. The default read-only P1 reference is the sibling `../dmwk-p1-foundations` directory. This is the existing published P1 checkout; no P1 suite or publication workflow is run.

```bash
python -B /workspace/p2_a1/verify_activation_spaces.py
python -B /workspace/p2_a1/verify_review_checks.py
```

For another local layout:

```bash
python -B /path/to/p2_a1/verify_activation_spaces.py \
  --p1-root /path/to/dmwk-p1-foundations \
  --output /path/to/p2_a1/verification_results.json
python -B /path/to/p2_a1/verify_review_checks.py
```

Install the declared NumPy dependency into your chosen environment if needed. No solver dependency is required for this round. Output files are actual run records and are overwritten by a rerun; timestamps and wall times may differ. A failed assertion or exhausted exploration budget is an error, not a completed global-space result. Do not use Python optimization flags to disable checks.

## Interpretation

The exact-rational span library does not use floating SVD or numerical rank tolerances. The main verifier combines explicitly bounded exhaustive models with 80 fixed-seed rational-matrix implementation checks. The independent verifier exhausts 512 binary 3-by-3 matrices and checks additional exact cases. These are not proofs for every possible program or matrix.

BF16 execution is software modeled. The compiler's BF16 path has its P1 small-integer certificate; the separate general floating reduction counterexample uses P1 C3's software rounding model. FP32 checks execute local NumPy scalar operations with type and bit checks. No GPU, native BF16, Lean/Coq, concurrency, or P2-A2 result is claimed. No SMT queries are executed in P2-A1.

Full-rank legal witnesses can establish a full global span. A deficient sampled rank cannot establish a global complement. A certified deficient superspace can establish an algebraic complement; a full superspace alone is inconclusive. Real or rational orthogonality is not a guarantee of bitwise floating execution invariance.
