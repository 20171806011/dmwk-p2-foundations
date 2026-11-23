# DMWK P2-A2: exact projection, finite arithmetic and executable safety

P2-A2 is complete within the explicit contracts below. It constructs exact orthogonal projectors and the full algebraic update space, accounts for actual stored-weight and execution errors, and implements one nonzero update mechanism with a conditional all-finite-time protected-trace proof. It does **not** authorize arbitrary projected floating-point updates.

Start with [the research report](P2_A2_Report.md), [the four proofs](P2_A2_Theorems.md), and [the claim-to-evidence map](P2_A2_Evidence_Map.md). [Counterexamples](P2_A2_Counterexamples.md) explain why the three levels of guarantee cannot be merged.

## Reproduce in the existing workspace

The actual environment was Python 3.12.14, NumPy 2.3.5, Linux x86-64. Dependencies are pinned in [requirements.txt](requirements.txt). No new installation is needed in this workspace.

```bash
python -B /workspace/p2_a2/verify_projection.py
python -B /workspace/p2_a2/verify_review_checks.py
```

The first command writes `verification_results.json`; the second writes `review_results.json`. They run P2-A2 checks and import existing P1 arithmetic interfaces. They do not rerun the P1/P2-A1 suites. Do not use Python `-O` or `-OO`: assertions are part of the verification. The main driver refuses those modes before executing any section.

The main command is independent of the current working directory. A separate recorded reproduction was run as:

```bash
cd /tmp
python -B /workspace/p2_a2/verify_projection.py --output /workspace/p2_a2/reproduction_results.json
```

All non-timing fields matched the primary run. Three deliberately invalid invocations were also refused; [driver_checks.json](driver_checks.json) records their exact commands, results, and preservation of the primary output. Their separate `*_refusal.json` files are expected failures, not failed scientific cases.

This is a workspace continuation, not a standalone export of P1. The read-only default dependency is `../dmwk-p1-foundations`; the main driver supports `--p1-root PATH`. The preserved P2-A1 files are expected at `../p2_a1`. Their exact required hashes, and the original request hash, are in [dependency_baseline.json](dependency_baseline.json). Moving the whole workspace can preserve this layout; an unrelated P1 installation is not an interchangeable dependency. The independent verifier uses the default sibling layout.

## Deliverables

| Purpose | Files |
|---|---|
| Scope and definitions | [Plan](P2_A2_Plan.md), [Definitions](P2_A2_Definitions.md), [original request](P2_A2_User_Plan_Original.txt) |
| Mathematical results | [Theorems](P2_A2_Theorems.md) |
| Numerical and structural contracts | [Numerical analysis](P2_A2_Numerical_Analysis.md), [Structural contract](P2_A2_Structural_Contract.md) |
| Exact implementation | [exact_projection.py](exact_projection.py), [verify_exact_cases.py](verify_exact_cases.py) |
| Numerical implementation | [numerical_projection.py](numerical_projection.py), [verify_numerical_cases.py](verify_numerical_cases.py) |
| Executable update mechanism | [safe_update.py](safe_update.py), [verify_safe_cases.py](verify_safe_cases.py), [p1_runtime.py](p1_runtime.py) |
| Main execution evidence | [verify_projection.py](verify_projection.py), [verification_results.json](verification_results.json), [reproduction_results.json](reproduction_results.json) |
| Independent review | [Review](P2_A2_Review.md), [verify_review_checks.py](verify_review_checks.py), [review_results.json](review_results.json) |
| Interpretation and provenance | [Report](P2_A2_Report.md), [Counterexamples](P2_A2_Counterexamples.md), [Evidence map](P2_A2_Evidence_Map.md), [References](P2_A2_References.md), [reference_verification.json](reference_verification.json) |
| Completion and continuation | [completion_status.json](completion_status.json), [final_integrity.json](final_integrity.json), [handoff](P2_A3_Handoff.md) |

The separate `exact_results.json`, `numerical_verification_results.json`, and `safe_verification_results.json` preserve the actual component runs. The aggregate result contains a fresh execution of all three routes with a common source-hash record. Check counts describe different units and are not pooled into one proof or confidence score.

## Boundaries

T1–T4 are handwritten conditional proofs, not Lean/Coq proofs. No SMT was executed. BF16 is a software RNE model. FP32 scalar CPU operations were audited against exact rational rounding. The tested FP32 SVD selects a version-specific single-precision NumPy gufunc; the numerical library/toolchain is not certified. GPU, native BF16, dense GEMM substitution, concurrent commits, arbitrary private runtime mutation, and general adaptive whole-program safety are outside this delivery.

P1 and P2-A1 remain prior work; no publication or repository operation was performed. P2-A3 has not started.
