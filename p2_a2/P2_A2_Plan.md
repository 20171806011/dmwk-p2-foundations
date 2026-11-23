# P2-A2 execution plan

Status: **completed for the stated P2-A2 contracts**. This plan was saved before derivation, implementation and experiments; the completion record below was added after actual verification. This invocation completes P2-A2 only, then hands off to the coordinator. The user's authorization to continue the wider research does not require executing P2-A3 in this invocation.

## Request and preserved dependencies

The complete supplied text is preserved byte-for-byte in `P2_A2_User_Plan_Original.txt`. Read-only prerequisites are the existing `../p2_a1` activation-space definitions, theorems, evidence/results and implementation interface, plus necessary floating execution helpers from `../dmwk-p1-foundations`. No P1 or P2-A1 stage suite is rerun and no existing artifact is edited. No publishing or repository creation is part of this task.

## Sequence and responsibilities

1. **Mathematical specification first.** Fix the global/superspace/sample status of H, physical shared column coordinates, rational and real domains, shapes, bias policy, target numerical contracts and admitted source of certificates. Derive T1 projector properties/uniqueness, T2 complete update parameterization/dimensions/nontrivial response, T3 separated residual/commit/execute bounds, and T4 one precise structural safe construction. Save English Definitions/Theorems and an early derivation checkpoint before experiments.
2. **Exact reference.** Implement exact Fraction elimination, basis/nullspace, inversion and both orthogonal-projector constructions, including zero/full rank, repeated/zero columns, merged calls, permutation covariance and matrix-free application. This is the truth reference, not FP64 SVD.
3. **Numerical route.** Implement FP64 and actual dtype-checked FP32 SVD, explicit absolute/relative rank cutoffs, quantization to BF16/FP32, projector/effective-update exact residuals, condition diagnostics, fixed-order separate multiply/add execution, and computable error certificates. Treat input conversion, candidate-product arithmetic, final storage quantization and execution as distinct objects.
4. **Executable structural route.** Implement a small fixed shared-matrix/reference system with a nonzero permitted update, an observable changed A output, and an unchanged protected D trace for all admitted inputs/initial states under a specified mask/layout and operation schedule. Reject protected writes, stale/version or malformed requests, nonfinite weights, changed execution contracts and uncertified claims. Validate completely before committing; retain bit-preserving synchronous snapshots. Do not claim a general OS/concurrency or arbitrary-network sandbox.
5. **Main finite verification and eight counterexample classes.** Use fixed seed 20261114, small exhaustive instances, exact-rational comparisons, random property tests and concrete adversarial cases. Cover all eight requested counterexample classes, all rank edges, learning response, sharing, representation/commit errors, SVD rank thresholds, coordinate covariance, finite arithmetic and refusals. Store true counts, timings, backend/dtype/policy metadata and hashes in verification_results.json.
6. **Independent review.** A separate reviewer uses independently implemented determinant/minor/linear-constraint or exact arithmetic references, checks the four proofs and numerical preconditions, searches for counterexamples to safety/API claims, and records findings and fixes. Main and independent checks rerun only as required by corrections. No finite test or SMT outcome is called a universal machine proof.
7. **Synthesis and handoff.** Write Counterexamples, Numerical_Analysis, Evidence_Map and Report; preserve all actual evidence, complete a foreign-working-directory reproduction and integrity/unchanged-dependency check, state exact limitations, and save the P2-A3 prerequisite/handoff without starting that stage.

## Required named deliverables

- P2_A2_Plan.md; P2_A2_Definitions.md; P2_A2_Theorems.md
- P2_A2_Numerical_Analysis.md; P2_A2_Counterexamples.md
- exact_projection.py; numerical_projection.py; safe_update.py
- verify_projection.py; verify_review_checks.py; verification_results.json
- P2_A2_Evidence_Map.md; P2_A2_Report.md

Additional README, dependency pins, original request, independent results and provenance/continuation records are permitted where useful. Only created files and actual outcomes are reported.

## Acceptance and scope

T1/T2 are exact algebra results, not FP safety. T3 must give explicit computable bounds with target RNE, overflow, subnormal, zero, product/add order and FMA assumptions; exact rational local-roundoff bounds may complement conservative gamma bounds. T4 must support at least one nonzero, stored update with a changed legal A response and protected all-time D semantics, or truthfully report failure. Approximate/sample-only evidence never authorizes a global bit-exact claim. The 1/3 projector example is measured even if a particular quantization preserves its row sum; a different genuine failure must then be provided. Truncated source citations are verified against original documentation or omitted as evidence. No novelty, throughput or universal safety claim is inferred.

## Completion record

All seven planned steps were carried out. The four conditional handwritten proofs, three implementations, eight counterexample classes, numerical analysis, independent review, claim-to-evidence map, and synthesis are delivered. The main run completed all three sections: 3,377 exact checks, 256 numerical checks, and 135,773 structural checks, with their differing units preserved. The independent verifier passed its own finite oracles. No SMT or proof-assistant claim is made.

Foreign-working-directory reproduction matched every non-timing field. Optimized Python modes and an absent P1 dependency were refused before any section. All 20 baseline dependency files and the copied original request retained their hashes. The original 1/3 fixture retained its exact kernel after rounding; separate sixths and subnormal cases demonstrate genuine failures. Independent review corrected precision-dispatch, rank-threshold, ideal-commit-domain, and audit-callback issues before the final main run.

See `P2_A2_Report.md`, `verification_results.json`, `review_results.json`, and `driver_checks.json` for actual evidence. `P2_A3_Handoff.md` saves the next research prerequisites only. No P2-A3 execution or publication was performed.
