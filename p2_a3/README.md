# DMWK P2-A3: exact linear noninterference and executable certificates

This stage separates three questions: whether exact linear outputs agree on a globally justified activation space, how much a specified floating execution changes at one input, and whether every protected raw output agrees on a complete legal execution domain. It also supplies a conditional local-to-program trace theorem and a finite-domain certificate checker.

Read [the report](P2_A3_Report.md), [definitions](P2_A3_Definitions.md), [proofs](P2_A3_Theorems.md), and [claim-to-evidence map](P2_A3_Evidence_Map.md). [Counterexamples](P2_A3_Counterexamples.md) show why exact algebraic and finite-domain floating equality are distinct, non-nested contracts.

## Reproduce in this workspace

The environment used is Python 3.12.14 with NumPy 2.3.5 on Linux x86-64. [requirements.txt](requirements.txt) pins NumPy. Existing read-only dependencies must remain at the sibling `p2_a1`, `p2_a2`, and `dmwk-p1-foundations` paths. This continuation package is not a standalone export of those earlier stages.

```bash
python -B /workspace/p2_a3/verify_noninterference.py
python -B /workspace/p2_a3/verify_review_checks.py
```

The first command writes `verification_results.json`; the second writes `review_results.json`. Neither launches a prior-stage verification suite. The main driver rejects Python `-O` and `-OO`; do not disable verification assertions.

A fresh output can be written from another directory:

```bash
cd /tmp
python -B /workspace/p2_a3/verify_noninterference.py --output /workspace/p2_a3/reproduction_results.json
```

The recorded primary and foreign-directory results are compared in [driver_checks.json](driver_checks.json). Only timestamps and timing fields are excluded from that comparison. A source change requires affected-check reruns and refreshed evidence binding.

## Implemented contracts

| Contract | Entry point | Meaning |
|---|---|---|
| ALG | [linear_contracts.py](linear_contracts.py): `exact_linear_report`, `exact_affine_report` | Exact endpoint difference annihilates the supplied generator span. The helper does not establish global provenance or authorize a bitwise commit. |
| BOUND | [bounded_contracts.py](bounded_contracts.py): `pointwise_report` | Exact-rational a posteriori absolute bounds for the specified stored endpoints, bias and input under bias-first separate RNE. No live authorization. |
| BIT | [certificate_kernel.py](certificate_kernel.py): `make_certificate`, `check_certificate`, `CertificateKernel` | Recompute complete registered finite call/state obligations, bind the execution contract, then publish a validated endpoint bank. |

The executable checker has five fixed registries, including two stateful Boolean-feedback models and three stateless boundary fixtures. It does not accept arbitrary external invariant claims. The stateful route protects both full two-coordinate matrix outputs at every site, as well as the state transition. It can accept edits to coefficients actively used by D, provided the full registered execution remains identical.

For example, replace `I_2` with `((0,1),(2,-1))` under `duplicate_feedback_v1`. On all protected inputs `(q,q)` and `(u,u)`, q,u Boolean, the full outputs agree; the fixed next-state recurrence is XOR. At legal A input `(1,0)`, output changes from `(1,0)` to `(0,2)`. The changed output is an existence witness, not a learning-performance claim.

See [Execution specification](P2_A3_Execution_Spec.md) for canonical certificate fields, versioning, refusal and publication semantics. A checksum identifies data; the checker recomputes the evidence and does not trust the checksum as proof.

## Artifact index

| Purpose | Artifacts |
|---|---|
| Pre-execution plan and derivation | [Plan](P2_A3_Plan.md), [Mathematical checkpoint](P2_A3_Mathematical_Checkpoint.md) |
| Mathematical scope | [Definitions](P2_A3_Definitions.md), [Theorems](P2_A3_Theorems.md), [Errata/clarifications](P2_A3_Errata.md) |
| Runtime specification | [Execution specification](P2_A3_Execution_Spec.md), [a3_runtime.py](a3_runtime.py) |
| Component verification | [Exact](verify_linear_cases.py), [Bounds](verify_bounded_cases.py), [Counterexamples](verify_counterexample_cases.py), [Certificates](verify_certificate_cases.py) |
| Component results | [algebra_results.json](algebra_results.json), [bounded_results.json](bounded_results.json), [counterexample_results.json](counterexample_results.json), [certificate_results.json](certificate_results.json) |
| Aggregate evidence | [Main verifier](verify_noninterference.py), [verification_results.json](verification_results.json), [reproduction_results.json](reproduction_results.json) |
| Independent review | [Review](P2_A3_Review.md), [Independent verifier](verify_review_checks.py), [review_results.json](review_results.json) |
| Synthesis | [Report](P2_A3_Report.md), [Evidence map](P2_A3_Evidence_Map.md), [Counterexamples](P2_A3_Counterexamples.md) |
| Identity and continuation | [dependency_baseline.json](dependency_baseline.json), [final_integrity.json](final_integrity.json), [completion_status.json](completion_status.json), [A4 handoff](P2_A4_Handoff.md) |

## Proof and execution boundaries

T1–T5 are handwritten proofs with explicit hypotheses. Finite exhaustive checks and independent oracles provide implementation evidence; no SMT or Lean/Coq run is claimed. BF16 uses software RNE. FP32 scalar CPU operations are checked against exact rational rounding. GPU, native BF16, general concurrent or hostile host-runtime execution, arbitrary compiler transformations, and general P2-C composition are not certified.

P1/A1/A2 artifacts and the published repository remain unchanged. This delivery stops at A3 and saves an A4 research starting point without performing that next stage.
