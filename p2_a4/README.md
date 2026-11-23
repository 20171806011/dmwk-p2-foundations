# DMWK P2-A4: rank budgets and four capacity notions

This stage establishes exact rank and target-response budgets, then separates them from finite stored-endpoint counts and fixed-graph bitwise equivalence. It supplies constructive feasibility/impossibility results, small complete endpoint searches, a structural reserve example, and independent verification. It does not equate a changed A output with useful learning performance.

Start with [the report](P2_A4_Report.md), [definitions](P2_A4_Definitions.md), [theorems](P2_A4_Theorems.md), and [evidence map](P2_A4_Evidence_Map.md). [Counterexamples](P2_A4_Counterexamples.md) show why a single rank number cannot describe every capacity.

## Reproduction in the current workspace

The recorded environment is Python 3.12.14, NumPy 2.3.5 and Linux x86-64. [requirements.txt](requirements.txt) pins NumPy. Existing sibling directories `p2_a1`, `p2_a2`, `p2_a3` and `dmwk-p1-foundations` are read-only dependencies; this package does not copy or independently republish those earlier stages.

```bash
python -B /workspace/p2_a4/verify_capacity.py
python -B /workspace/p2_a4/verify_review_checks.py
```

These write `verification_results.json` and `review_results.json`. They run A4 checks, not old stage suites. Do not use `-O` or `-OO`, which disable verification assertions; the main driver refuses those modes.

To preserve the primary result while reproducing from another directory:

```bash
cd /tmp
python -B /workspace/p2_a4/verify_capacity.py --output /workspace/p2_a4/reproduction_results.json
```

[driver_checks.json](driver_checks.json) records the actual foreign-directory comparison and preflight refusals. Only timing/timestamp metadata is omitted from the primary-versus-reproduction comparison. Source hashes and scientific results remain part of that comparison.

## Interfaces and meaning

| Interface | Meaning |
|---|---|
| [capacity_algebra.py](capacity_algebra.py): `budget_report`, `attaining_update`, `solve_response` | Exact rational dimension/rank/response calculations. Constructs a minimum-rank feasible response or returns an incompatibility witness. It does not establish global provenance, storage feasibility or commit authority. |
| [capacity_discrete.py](capacity_discrete.py): `enumerate_family`, `classify_endpoint` | Counts an explicit finite endpoint family, separates ALG, certificate-checked BIT and their intersection, and records ranks and A response images. No full-format enumeration is inferred. |
| [structural_budget.py](structural_budget.py) | Exact row-mask budgets and a pure validated 2-by-3 reserve-layout evaluator. It adds no new live-update route to A3. |
| Existing A3 certificate API | Remains the live transaction mechanism for supported registered models. Counts or algebraic reports do not replace endpoint/domain/graph/policy/version checking. |

The stateful nonzero witness remains an actual accepted A3 dense update: `I_2 -> ((0,1),(2,-1))` preserves the complete duplicated-bit D domain and changes a legal A output. The structural fixture separately demonstrates two reserved coefficients with exact output/state protection under its stated read graph. Its parameter validator reads every cell; read exclusion concerns the protected arithmetic after validation, not the host's entire memory trace or timing.

## Artifact index

| Purpose | Files |
|---|---|
| Plan and pre-code derivation | [Plan](P2_A4_Plan.md), [Checkpoint](P2_A4_Mathematical_Checkpoint.md) |
| Mathematical contracts | [Definitions](P2_A4_Definitions.md), [Theorems](P2_A4_Theorems.md), [Errata](P2_A4_Errata.md) |
| Structural layout | [Structural budget](P2_A4_Structural_Budget.md), [structural_budget.py](structural_budget.py) |
| Main component checks | [Algebra](verify_algebra_cases.py), [Discrete endpoints](verify_discrete_cases.py), [Structural](verify_structural_cases.py), [Boundaries](verify_boundary_cases.py) |
| Component results | [algebra_results.json](algebra_results.json), [discrete_results.json](discrete_results.json), [structural_results.json](structural_results.json), [boundary_results.json](boundary_results.json) |
| Main run | [verify_capacity.py](verify_capacity.py), [verification_results.json](verification_results.json), [reproduction_results.json](reproduction_results.json) |
| Independent review | [Review](P2_A4_Review.md), [verify_review_checks.py](verify_review_checks.py), [review_results.json](review_results.json) |
| Synthesis | [Report](P2_A4_Report.md), [Evidence map](P2_A4_Evidence_Map.md), [Counterexamples](P2_A4_Counterexamples.md) |
| Dependency/continuation records | [a4_runtime.py](a4_runtime.py), [dependency_baseline.json](dependency_baseline.json), [final_integrity.json](final_integrity.json), [completion_status.json](completion_status.json), [B1 handoff](P2_B1_Handoff.md) |

## Evidence limits

T1–T8 are handwritten conditional proofs. Finite exhaustive checks, fixed-seed properties and actual arithmetic observations are different evidence classes. BF16 uses software RNE; CPU FP32 results are audited against exact rational rounding. No native BF16, GPU, general concurrency, arbitrary compiler optimization, whole host-stack machine proof, universal learning-performance result, completed C1 compiler or C4 hardware certification is claimed.

Earlier research and publication content are preserved. This stage stops at A4; B1 and long-term B4 training are not performed here.
