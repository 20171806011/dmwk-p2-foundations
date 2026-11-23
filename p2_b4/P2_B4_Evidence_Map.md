# P2-B4 claim-to-evidence map

This document distinguishes handwritten general proofs, conditionally universal analytic witnesses, complete named finite sets, seeded stress tests, exact-reference checks and local backend operations. Finite evidence does not become a theorem about every legal update history merely because a verifier passes.

## Mathematical claims and executable scope

| Claim | Proof | Reference interface / required evidence | Boundary |
|---|---|---|---|
| Fixed-space step safety iff every prefix preserves the anchor | T1 | `analyze_history` fixed mode in [capacity_history.py](capacity_history.py) | Final cancellation alone is insufficient; actual stored deltas and global coverage are required. |
| Cumulative spaces intersect their annihilators and reduce dimension by independent directions | T2 | `algebra_budget`, `registered_budget`, cumulative histories | A supplied sample H does not certify global activations. Nonnested current spaces can regain dimensions or lose historical protection. |
| Linear task anchors must respect every cross-task linear relation | T3 | `joint_task_feasibility`, `task_anchor_check` | Pairwise overlap checks can miss a three-task contradiction. Exact feasibility does not imply representable/BIT feasibility or retroactive history protection. |
| Quotient-target response capacity and cumulative update rank | T4 | Exact response construction, per-step/prefix rank records | Rank cap per step differs from cumulative rank and persistent-adapter rank. Nonzero response is not general task benefit. |
| Fixed absolute ALG/BIT classes do not shrink with update count | T5 | Finite endpoint-class comparisons at different class members | Local optimizer, radius, step, factor and quantization reachability can still stall. Saturated and zero-bank examples have different anchors. |
| Changing-history error needs new per-step endpoint/domain certificates | T6 | `analyze_switching` in [switching_bounds.py](switching_bounds.py) | Original-reference, adjacent-endpoint and two-history comparisons have explicitly different schedules/identifications. Both execution errors remain. |
| Uniform switching needs one common norm, domain and forcing bound | T7 | Common-family mode/image/pair checks | Separately nilpotent modes can amplify; a finite successful run is not an invariant proof. |
| Full-prefix budget cannot be recovered by final cancellation | T8 | `budget_ledger`, read-only `sequence_certificate.py` | Bound violations may be conservative. A positive bound is not measured D drift or live authorization. |
| Combined exact-D serial publication and full rejection rollback | T9 | [update_sequence.py](update_sequence.py), unchanged B1 gate | Accepted metadata/weights may differ from the original; D observations remain equal. Refusal preserves the entire owned snapshot. |

All T1–T9 statements refer to [Definitions](P2_B4_Definitions.md) and [Theorems](P2_B4_Theorems.md). The mathematical scalar field 𝕂 is distinct from the finite prefix index K. Update index k is distinct from execution time t. A raw history may contain skipped, unused or repeated numerical versions; its chronology does not prove live authorization.

## Actual producer evidence available so far

[capacity_results.json](capacity_results.json) reports `passed`, seed 20261114, 14,345 assertions, 10 expected refusals, zero unexpected failures and 14.841555603 s. Its finite scope is explicit:

| Capacity section | Actual coverage |
|---|---|
| Stored histories | 1,458 complete histories: every triple of one-row, two-coordinate endpoints over `{-1,0,1}`, in both formats; 72 seeded fixed-space cases |
| Responses and anchors | 64 response-budget cases, 1,728 prescribed-response/rank-cap queries with 468 feasible, 27 three-task anchor assignments with 7 jointly compatible, and 81 pairwise checks |
| Named evolution | Fixed reuse, unsafe final cancellation, cumulative exhaustion, admission mismatch, moving-space damage/recovery, rank-one sum growth and sample-versus-registered provenance |
| Finite endpoints | 12 explicitly specified Cartesian families and 1,892 candidate examinations; these are not 1,892 globally distinct format endpoints or a whole-format enumeration |
| Refusals | 10 schema/domain/algebra input refusals |

In the fixed-class finite fixture, the same absolute 256-endpoint universe has 16 ALG/BIT members before and after an accepted move within the class, with the same absolute A-response image. Tiny-palette examples separately yield ALG 4 versus raw BIT 16 on the duplicated domain, and ALG 1 versus raw BIT 2 on the full-rank split domain, in both formats. A named inadmissible old-state fixture has one raw-BIT no-op but zero `E_CERT` endpoints; complete call equality does not waive the stronger actual checker premises. All these counts belong to their named finite families and observations.

[switching_results.json](switching_results.json) reports `passed`, seed 20261114, 4,028 assertions, 10 expected refusals, zero unexpected failures and 22.620926238 s. Its declared subdivisions are:

| Section | Assertions | Actual finite scope |
|---|---:|---|
| `complete_and_seeded` | 3,944 | 64 complete mode-pair families; 1,152 named trajectory pairs; 12 seeded trajectory pairs of length 12; two additional common-family witnesses |
| `switching_and_budget` | 36 | Six named records across both formats; six expected refusals, including unsupported common-domain/budget premises |
| `numeric_boundaries` | 48 | Ten named records and four expected refusals; new changing-endpoint probes using pure earlier numerical helpers |

The 64 complete families divide as follows: for each format, 8 original-reference length 3 mode sequences, 8 adjacent-endpoint length 3 sequences, and 16 two-history length 2 mode pairs. Every chosen history exhausts the common input alphabet `{-1,0,1}` at its declared horizon and specified initial pair, giving 1,152 complete trajectory pairs overall. Twelve length 12 history pairs are seeded separately. Four further trajectory records cover skipped/repeated version indices and identical changing histories, yielding 1,168 trajectory records in that section; they are not additional complete history families.

The two common-family witnesses each prove closure for four declared modes and certify 16 ordered mode pairs in one infinity norm. Their uniform conclusion applies only to continuations within that family and unchanged state/input/policy conditions. The finite sampled histories do not supply those premises.

[transaction_results.json](transaction_results.json) reports `passed`, seed 20261114, 1,120 assertions, 98 expected refusals, zero unexpected failures and 30.747024295 s. Its finite evidence includes 64 accepted training attempts, 48 nonzero stored changes, 64 paired D ticks, 58 rehashed inconsistent-record cases, 12 numerical receipt cases, 14 budget-exhaustion cases, two storage-stall/alternative-A-edit cases and four rollback/no-authority boundary cases.

The two 32-step SGD runs use learning rate 1/4 and the fixed legal A target `(1,-1)`. BF16 performs 16 nonzero changes followed by 16 accepted no-ops; its exact decoded half-squared loss changes from 1/2 to 1/32768. FP32 performs 32 nonzero changes and reaches 2839225/562949953421312 from 1/2. Every accepted endpoint passes the original joint gate and every paired D tick agrees with the unchanged reference. Algebraic dimension 4, reserved dimension 2 and target-response dimension 2 stay fixed. These results show a specific A-loss decrease with exact D preservation, not a universal learning or endless-progress theorem.

Two late administrative-limit fixtures stage a successful B1 update on an unexposed copy and then refuse ledger publication while existing moments are nonzero; the full visible snapshot remains unchanged. Two separate numeric-no-authority fixtures show that a read-only switching receipt cannot be submitted as an exact live transaction. Rejected attempts are external diagnostics, not additions to the accepted ledger. The accepted-history cap is administrative, not exhausted rank.

## Independent evidence

[independent_results.json](independent_results.json) reports `passed`, seed 20261114, 33,901 assertions, 56 expected refusals, zero unexpected failures and 79.998951999 s. Its independent oracles use exact minors/direct equations, ordered-word nearest-even search, independently reconstructed interval recurrences, explicit word trajectories and direct weighted product sums. It imports no predecessor verifier suite; the pure inherited P1 arithmetic module is a disclosed dependency. Actual finite scope is:

| Independent section | Recorded coverage |
|---|---|
| Exact algebra | 486 minor-rank budget cases, 512 response/relation/rank cases, 27 three-task assignments and 81 pairwise subchecks |
| Stored histories | 486 named stored-history/mode cases, with separate prefix-cancellation, arrival-anchor, moving-space and cumulative-rank witnesses |
| Finite endpoints | 16 named families and 1,136 endpoint examinations; raw BIT remains separate from E_CERT |
| Exact-D transactions | 34 accepted repeated/no-op updates, including 32 toy learning steps, 32 paired feedback ticks and 128 complete D-call observations; two late-rollback fixtures retain nonzero moments |
| Switching | 28 analyses, 1,142 named trajectory pairs including nonlinear and nilpotent witnesses, and 18 common-family ordered-pair oracle checks; completeness applies only to the explicitly enumerated subfamilies |
| Read-only receipts | 12 accepted receipts; distinct stale/inconsistent, budget, initial-relation and no-live-authority refusals; two nonzero-moment rollback fixtures |
| Frozen B1 evidence | 21 refused endpoint pairs decoded afresh on 84 complete state/input pairs; the old optimizer is not executed and its old results are not replaced |

These are new B4 finite checks of named cases, not a second universal proof or a total over disjoint independent experiments. General theorems remain handwritten; zero SMT queries and no proof-assistant check are recorded. The successful run lists only the B4 independent verifier as an executed verification module, with its explicit pure P1 arithmetic dependency.

## Aggregate and preservation

[verification_results.json](verification_results.json) reports `passed`, three of three B4 sections completed, no unexecuted sections, and 70.286952879 s. Its sections are the same finite producer suites above; they are not additional distinct coverage to sum with the standalone counts. The aggregate checks 13 current source/configuration bindings and confirms the 739 predecessor artifact hashes and inventory unchanged. It records no old-suite replay, no old optimizer regeneration, zero SMT queries, no proof-assistant check and no C1 execution.

[reproduction_driver_results.json](reproduction_driver_results.json) reports `passed`. Its `/tmp` main run produces [reproduction_results.json](reproduction_results.json) in 74.400552056 s; its independent run produces [independent_reproduction_results.json](independent_reproduction_results.json) in 85.498845732 s. Five scientific comparisons pass after excluding recorded timing fields only: main versus foreign main, independent versus foreign independent, and each of the three standalone producer records versus its aggregate section. The driver also confirms all primary producer/source bindings unchanged and the 739 predecessor hashes/inventory preserved. Its total orchestration time is 88.588344645 s; the two foreign runs execute concurrently, so this is not their summed runtime.

The actual [optimized_O_results.json](optimized_O_results.json) and [optimized_OO_results.json](optimized_OO_results.json) record preflight rejection with zero sections attempted. They demonstrate that disabling Python assertions does not produce a misleading passed aggregate. They are deliberate negative driver checks, not extra numerical experiments or proof coverage.

## Counterexamples and non-implications

| Boundary | Exact argument or current recorded location | What it rules out |
|---|---|---|
| Final cancellation hides unsafe prefixes | T1: scalar endpoints 0,1,0 | A safe final telescope is not evidence that every published endpoint was safe. |
| Current-space safety forgets old tasks | T2: protect e1, then e2 with corresponding complementary edits | Moving nonnested protection does not preserve the task union. |
| Pairwise task compatibility misses a global relation | T3: e1,e2,e1+e2 with targets 0,0,1 | Pairwise intersections alone do not prove a joint solution. |
| Rank-one increments accumulate higher rank | T4: complementary diagonal updates | Per-step generator rank is not a lifetime cumulative-rank cap. |
| A local quantized step stalls inside a fixed feasible class | T5 | No-op storage does not prove that the global safe class has lost dimension/members. |
| Different anchors have different finite capacities | T5: zero versus saturated `(Fmax,Fmax)` bank | This is not capacity loss along one fixed-ALG chain. |
| Individually nilpotent modes amplify when alternated | T7; switching record `individually_nilpotent_switched_amplification` | Separate mode stability/norms cannot be multiplied into a common switching guarantee. |
| A patched mode invalidates old fixed-bank coefficients | `fixed_B3_coefficients_expire_after_patch` | A B3 certificate cannot be reused without new endpoint/domain obligations. |
| Prefix budget fails despite a smaller final error | `prefix_budget_not_final_only` | A final-only comparison does not cover all earlier observations. |
| Exact zero action misses subnormal execution | `thirds_then_identity_basis`, `thirds_then_identity_subnormal` | Algebraic annihilation and ordinary basis probes do not remove two-execution rounding. |
| Commit quantization is path-dependent | `repeated_commit_quantization_path_dependence` | Ideal increments cannot replace actual stored endpoint differences. |
| Identical histories have positive conservative bounds | `identical_changing_histories_zero_actual_positive_bound` | A certified upper bound is not an observed error or deterministic drift. |

Saturated storage, full-rank BIT/non-ALG, incompatible targets, omitted sites, policy changes, hard-branch margins and actual-versus-conservative domain failures retain their scoped predecessor meanings. New capacity, switching and transaction records exercise those stated B4 obligations; no old suite was rerun. Finite raw BIT and the stronger state/interface certificate group remain separately labelled.

## Authorization, state and evidence boundaries

The live experiment's exact-D model is B1's fixed `structural_duplicate_v1`: immutable identity columns, an editable reserved column, both Boolean shared call sites and synchronous XOR feedback. Its owner stages on a private copy, including the unchanged B1 gate and the new accepted ledger, before publishing one combined owner value. A late ledger failure must leave the visible endpoint, protected q/ticks, optimizer state and both ledgers unchanged. Administrative history length is not a mathematical capacity limit; accepted no-op and nonzero progress are separately counted.

The numerical receipt instead binds complete supplied histories, schedules, initial relation, joint domains, observation, policy and budget, then recomputes read-only evidence. An attached exact-D snapshot is labelled identity context, not proof that the numerical graph is the D program. Unkeyed hashes supply no original-intent authentication. The protected D observation projection is narrower than the full owned bank; acceptance changes metadata but must not change protected behavior. Rejection requires equality of the full owned before/after snapshot.

The predecessor inspection in [dependency_inspection.json](dependency_inspection.json) verified 39 B3 manifest entries and its 699 predecessor entries and established the expanded 739-file baseline in [dependency_baseline.json](dependency_baseline.json). That scope includes original P1 directories, the publication worktree, root P1 summaries and all prior P2 stages; `.git`, virtual environments and caches are excluded. This read-only inspection is not a new exhaustive audit of every old proof.

Frozen B1 facts remain 21 BIT-equal but exact-ALG-failing refused endpoints; its dense FP32 AdamW run remains 0 accepted / 8 refused with loss 5/2. Saved evidence is read and its refused endpoint words checked independently without regenerating optimizer trajectories. The completed B4 aggregate and foreign reproduction driver confirm predecessor preservation. Final packaging is a separate integrity record, not additional mathematical or numerical evidence.

## Reproduction and unresolved guarantees

Use the [README reproduction commands](README.md#reproduce-in-the-existing-workspace) to run only new B4 aggregate/independent scripts from a fresh `/tmp` directory. Recorded dependency: Python 3.12.14, NumPy 2.3.5. Producer/independent science, source identities and environments must match across directories, excluding only named timing fields.

Generic algebra uses exact rational matrices; numerical bounds use exact rational infinity norms and finite-range proofs. Actual BF16 is software, while FP32 is the available audited CPU scalar path. No GPU/native-BF16, arbitrary compiler/FMA/reassociation, general concurrency, hardware-fault or complete machine-proof claim is made. Finite cost and toy-loss evidence do not establish scalability, optimality or universal learning benefit. C1 remains the saved next-stage handoff.
## Final delivery binding

[completion_status.json](completion_status.json) records scoped B4 completion, source/result digests, actual verification counts and explicit unproved boundaries. [final_integrity.json](final_integrity.json) seals the complete delivered file inventory, excluding its own digest, and checks predecessor preservation and all source/producer bindings. These packaging checks add no scientific cases and do not turn the handwritten theorems into machine-checked proofs.
