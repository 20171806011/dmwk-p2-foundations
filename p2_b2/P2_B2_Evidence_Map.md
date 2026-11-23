# P2-B2 — Claim-to-evidence map

This map distinguishes handwritten proofs, exact finite computations, target-format execution probes and read-only numerical receipts. It does not treat a finite bound check, a complete small domain, a sampled family or a future stage title as a universal machine proof. General assumptions are fixed in [Definitions](P2_B2_Definitions.md); [Theorems](P2_B2_Theorems.md) contains T1–T7 and [Numerical Analysis](P2_B2_Numerical_Analysis.md) fixes the implemented arithmetic.

## Theorem and implementation ledger

| Claim | General proof | Executed producer evidence | Limit |
|---|---|---|---|
| **T1: core protected-action/residual bound** | Orthogonal decomposition h=Qa+e and operator/triangle inequalities; exact-projector reformulation avoids irrational basis construction. Degeneracies and sharpness are stated separately. | `geometry_bound`: 64 seeded geometry cases, seven named geometry cases; exact squared responses are compared with the square of each certified bound. | H supplies a declared reference space, not automatic global provenance. If it already contains every legal input, the activation residual is zero. |
| **T2: certified norms and approximate basis** | Rational square-root enclosures and elementary spectral inequalities; Gram conditioning and projector deviation are bounded separately. | 69 square-root interval cases, three approximate-basis cases and four expected geometric refusals. The sqrt implementation normalizes scale before integer enclosure. | A conservative Gram bound >=1 refuses this route; it does not prove rank deficiency. No SVD estimate or host square root is accepted as a norm certificate. |
| **T3: disjoint telescoping ledger** | Adjacent exact matrix differences telescope to the actual final increment. Triangle bounds measure those differences once. | Two format-specific ledger records, eight checks. All adjacent terms are nonzero; their pointwise effects can cancel, giving direct response zero while the ledger triangle budget is 5/4. | The identity does not certify the semantic origin of stage labels or an invented ideal Adam computation. Direct endpoint and upstream-ledger bounds are alternatives. |
| **T4: local residuals and two rounded executions** | Each decoded multiplication/addition error is exact; signed errors telescope per row. Old and new trace errors enter separately. | The finite-execution section records 218 point records and 2,614 checks overall, using exact rational affine references; counterexamples include rounded thirds, cancellation, underflow and effective endpoint change. | A point trace is not a whole-domain proof. The difference of rounded executions is not generally a rounded execution of the exact update. |
| **T5: complete box totality and error bound** | An induction establishes every product and pre-round sum range, rounded accumulator magnitude and summed local error over the stated box. | 26 box records, plus explicit conservative refusal and overflow boundaries in the counterexample section. The numerical receipt suite binds boxes to registered-domain inclusion. | Refused range certification need not mean actual overflow. Zero-term padding and lost cancellation can make a valid bound loose. No gamma_n route is used by the delivered checker. |
| **T6: relative/mixed budgets and strict output separation** | A certified positive lower reference norm permits division; mixed budgets work at zero. A strict bound below the canonical finite lattice step can imply equality with full coverage. | Zero/cancellation and mixed-budget cases are exercised. The thirds/tiny observations exhibit unequal outputs at difference eta. The counterexample section has 24 format-specific point records and two additional exact/mixed records; its 22 numeric refusal events are separate. The general strict-gap implication is a handwritten proof. | Relative output error is undefined at zero. A non-strict eta bound or a point-only bound is insufficient for a global BIT claim. |
| **T7: bounded-receipt scope and non-authority** | Complete semantic recomputation binds endpoints, norm, domain/envelope, graph, policy, bias and budget. The returned receipt makes no live-publication claim. | 40 registered receipt cases; 36 field-tampering cases; 16 seeded endpoint cases; two B1 full-state rollback fixtures; 108 expected receipt/interface refusals. | This is a selected single-layer norm statement on the original registered envelope. It does not prove candidate feedback closure, authorize a B1 commit or replace the selected BIT/ALG_AND_BIT contract. |

The gamma specialization in the theorem text is conditional mathematics only. Its additional premises are not advertised as a delivered acceptance route. No SMT queries or Lean/Coq checking are recorded by the producer suites.

## Actual producer runs

| Record | Actual coverage and counts | Status |
|---|---|---|
| [bound_results.json](bound_results.json), [verify_bounds.py](verify_bounds.py) | 3,419 checks: geometry 504, ledger 8, finite execution 2,614, counterexamples 293. 26 expected refusals, 69 sqrt cases, 64 seeded geometry cases, 12 seeded endpoint pairs per the recorded family, complete nine-input domains, 218 point records and 26 box records. | Passed; zero unexpected failures; 2.465374464 seconds |
| [certificate_results.json](certificate_results.json), [verify_certificates.py](verify_certificates.py) | 421 checks; 40 registered receipt cases; 108 expected refusals; 36 tampered-field cases; 16 seeded endpoint cases; two integration rollback fixtures; all 21 frozen B1 refusals newly analyzed. | Passed; zero unexpected failures; 8.830940041 seconds |
| [independent_results.json](independent_results.json), [verify_independent.py](verify_independent.py) | Independent interval/PSD/projector checks, 1,458 exhaustive and 128 seeded affine point pairs, 24 box certificates, 40 receipts and all 21 frozen B1 endpoint pairs | Passed; 16.060792099 seconds |
| [verification_results.json](verification_results.json), [verify_b2.py](verify_b2.py) | Both planned sections completed, no unexecuted sections, all 447 prior artifacts checked unchanged | Passed; 11.860618054 seconds |
| [reproduction_results.json](reproduction_results.json), main runner from `/tmp` | Same two sections and unchanged prior inventory/content | Passed; 12.189905724 seconds |
| [independent_reproduction_results.json](independent_reproduction_results.json), independent runner from `/tmp` | Same independent scientific results and source bindings | Passed; 16.707115789 seconds |

Both producer records use seed **20261114** and distinguish seeded families from complete declared-domain enumeration. Their check counts are assertion/condition counts, not a claim of that many independent theorems. Repeated inputs across sites remain separate call-site observations; a count does not certify omitted sites. The scripts do not rerun old-stage suites.

The bound suite's 26 expected refusals consist of four geometry refusals and 22 numerical/counterexample refusals. They are not the same quantity as the counterexample section's 26 retained records (24 format-specific point records plus two additional exact/mixed records).

The 40 registered receipts span two formats, five declared models, two evidence methods (`complete_point_trace` and `analytic_box`) and two explicit norms (`l2` and `linf`). The bound and actual finite-domain supremum are different fields: the latter comes from complete enumeration of that small registered domain, while the analytic box bound covers the larger stated envelope by proof.

## Frozen B1 endpoint analysis

The source is the existing B1 training result, hash

`b417741ab974752d7858c978bc75197f3199312e9bdf118c232dcbd8cef7cfb1`.

The B2 receipt suite reads all 21 rejected endpoint records: six BF16 momentum attempts, seven BF16 AdamW attempts and eight FP32 AdamW attempts. It does not execute the old optimizer again. Every new finite-domain diagnostic retains BIT equality and ALG failure; the previous state, moments and refusal outcome are unchanged. Every record separately computes point-trace and analytic-box bounds, and the point bound is smaller than its box bound in these cases.

B1's dense FP32 AdamW result remains zero accepted and eight refused attempts, with loss 5/2 before and after. New numerical receipts are evidence of bounded single-layer output difference, not revised optimization history. Bounds can be positive even when complete finite-domain observation finds zero actual output difference; the triangle/error decomposition is conservative.

Two new integration fixtures first establish nonzero B1 moments and a protected state tick, then attempt to submit a B2 numerical receipt through the unchanged B1 commit interface. Both are refused with the **entire** weight/optimizer/protected snapshot preserved. Their later tick also makes the bound context stale and is refused by the receipt checker. These are new B2 integration tests, not a rerun of B1's optimization suite.

## Counterexample and failure scope

The producer catalog covers scaled and rotated bases, zero/full-rank geometric cases, protected-action versus activation-residual terms, nonzero ledger terms with cancellation, nonzero/zero reference outputs, subnormal rounding, signed-zero/nonfinite policy refusals, actual overflow, conservative box refusal, rounded-thirds basis-test failure, endpoint quantization, saturated storage and full-rank rounded equivalence. Target incompatibility, sample-only provenance, omitted shared sites and wrong graph/policy/schedule remain explicit failures or refusal cases.

No failure is relabeled as a zero bound. A conservative totality refusal is identified as such. Native word observations, exact decoded residuals and analytic bounds remain separate fields in the JSON. The main counterexample narrative is [P2_B2_Counterexamples.md](P2_B2_Counterexamples.md).

## Independent checker, aggregate and preservation evidence

The independent norm/geometry path verifies 32 square-root intervals and 72 spectral upper bounds by exact positive-semidefinite conditions using all principal minors, rather than reproducing the producer's elementary-norm inequality as its assertion. It checks 450 two-dimensional geometric cases, 48 seeded three-dimensional cases, eight zero/full-space cases and three explicit approximate-basis examples. Its projector reference uses exact adjugate calculations/direct products. The geometry seed is 20261114.

The independent point/box path reconstructs IEEE word values and nearest-even results, signed local residuals, coordinate bounds and both execution-error contributions. It checks 1,458 exhaustive point pairs on its named small sets and 128 seeded affine pairs with subseed **20261115**. It reconstructs 24 analytic box recurrences and checks 384 named box inputs, plus 81 mixed-budget cases. Enumeration checks those finite inputs; the universal box conclusion still rests on the separate range-induction proof.

The ledger review uses three modes with four nonzero adjacent errors and checks duplicate-label refusal. The receipt review validates 40 receipts and 26 distinct complete-call comparisons, including 38 expected refusal cases and two full nonzero-moment B1 rollback fixtures. It independently reads all 21 frozen endpoint pairs and checks 84 registered calls. Those counts do not represent new optimizer trajectories or old-suite reruns. Numerical point refusals and basis refusals are recorded in their own sections rather than silently discarded.

[driver_checks.json](driver_checks.json) records the completed main and independent foreign-working-directory runs, their commands, output hashes and comparison exclusions. Both scientific comparisons match after excluding only enumerated timestamp/seconds fields; source identities, environment metadata, refusal reasons and scientific values are compared. Both standalone producer records also match their aggregate sections under the same timing-only rule. The new comparisons are reproducibility checks, not additional universal proof coverage.

The driver also verifies all 447 prior content hashes and the nonexcluded inventory unchanged, verifies current source bindings, and records that `-O` and `-OO` both refuse during preflight with exit code one and zero attempted sections. Those guard tests do not replace or modify the primary passing evidence. The written [independent review](P2_B2_Review.md) and [research report](P2_B2_Report.md) interpret these records; final packaging manifests remain separate artifact-integrity records.

The numerical environment is software BF16 and locally audited CPU FP32 under canonical-zero, gradual-underflow, fixed-order separate operations. The exact norm and residual computations use rational/integer arithmetic. GPU, native BF16, FMA/reassociation changes, arbitrary compilation, general concurrency, crash recovery and malicious private-memory mutation remain uncertified. Neither a point result nor a numerical receipt establishes a general multilayer or deterministic-program perturbation theorem; B3 and later work remain outside this stage.
