# P2-B4 — Repeated updates, remaining learning capacity and stability

## Research conclusion

Repeated safe updates do not inherently consume one degree of freedom per update. With one proved global protection space, the same exact annihilator remains available. More strongly, with a fixed absolute stored-endpoint universe and fixed protected anchor, an algebraically safe history stays in the same feasible endpoint class. Under a fixed complete execution context and graph, a BIT-safe history likewise stays in one unchanged BIT equivalence class. Quantization, step limits, low-rank generators and optimizer state can still cause local stagnation without shrinking that absolute class.

Cumulative independently added protection directions do reduce capacity. A changing current protection space need not do so monotonically and can lose previously protected behavior. Stability under changed weights needs a new changing-history certificate: a fixed-endpoint B3 bound does not authorize later endpoints. A common invariant, a common norm, a uniform gain below one and bounded forcing give a conditional all-finite-time bound; separate stable modes alone do not.

This is a conditional mathematical and finite-reference implementation result. It neither proves indefinite useful learning nor completes any C-series compiler/kernel obligation.

## Scope and dependency handling

The saved [Plan](P2_B4_Plan.md) and [mathematical checkpoint](P2_B4_Mathematical_Checkpoint.md) preceded implementation. The stage only reads prior P1/P2 files and the existing publication directory. The baseline covers 739 nonexcluded old artifacts. B3 handoff, definitions, proofs, numerical analysis, counterexamples, evidence/review, primary and independent results, reproduction, completion and integrity were inspected as dependencies; no previous suite or optimizer trajectory was rerun. The [dependency inspection](dependency_inspection.json) records the actual integrity checks. Scoped errata are recorded separately in [Errata](P2_B4_Errata.md).

Inherited facts remain unchanged: B1's 21 refusals passed its current finite-domain BIT test and failed ALG under the joint contract; they were not 21 observed D drifts. Dense FP32 AdamW had zero accepted updates, eight refusals and unchanged loss 5/2. B4's different structural toy does not replace or erase that negative result.

## Mathematical results

Full assumptions and proofs are in [Definitions](P2_B4_Definitions.md) and [Theorems](P2_B4_Theorems.md).

| Result | Established statement | Necessary boundary |
|---|---|---|
| T1 | Every actual increment annihilates fixed V iff every prefix difference from the original endpoint does | A safe final cancellation alone is insufficient; exact algebra is not BIT |
| T2 | Cumulative space rank r leaves n(d-r) scalar degrees and per-update rank at most min(n,d-r,q) under cap q | Full legal activation coverage across all shared sites; sampled rank is insufficient |
| T3 | Joint task anchors exist iff all inter-task linear relations are respected; feasible solutions form an affine annihilator coset | Pairwise overlap consistency alone can miss a three-task incompatibility; admission is not retroactive |
| T4 | Target-response dimension is n(rank[H X]-rank H); compatible requested response R has minimum implementing rank rank R | Nonzero safe directions can be silent on all target inputs; no general learning-benefit implication |
| T4(a) | K rank-q increments may accumulate rank min(Kq,n,d-r) | A persistent adapter rank constraint is a different family |
| T5 | Fixed-anchor absolute ALG and fixed-context BIT classes remain unchanged along their respective safe chains | Endpoint-dependent local reachability and optimizer progress may stall; changed task constraints change the class |
| T6 | Two scheduled histories obey a nonhomogeneous finite-time product-sum bound with initial error and both executions' rounding | Both trajectories and all intermediate calls need proved tubes/totality; freshly selected stored endpoints determine each coefficient |
| T7 | A common invariant/norm, uniform L<1 and forcing b imply error at most max(E0,b/(1-L)) for every finite time | Individual-mode stability, a finite sample, or different mode norms do not establish arbitrary-switch stability |
| T8 | A full-prefix ledger bounds every observed time and detects budget exhaustion | A small final error cannot erase earlier excess; numerical evidence is read-only |
| T9 | A complete-domain exact-D gate with atomic serial publication preserves the D observation trace across finite update/reject/tick histories | Successful updates intentionally change weights/optimizer/ledger; rejection preserves the entire owned snapshot |

All these general proofs are handwritten. No proof assistant or SMT solver has checked their general statements.

## Capacity examples and counterexamples

With a 2-by-3 bank and one protected direction, unrestricted exact freedom is four scalar degrees. Reserving only one editable column leaves two structural degrees and per-update rank at most one; the declared e3 target has two response degrees. Repeating an allowed update does not subtract from these numbers.

With three input coordinates, two rank-one safe increments on different complement directions can sum to rank two. With a two-coordinate scalar-output bank, protecting e1, then both coordinates, then only e2 gives current freedoms 1,0,1. Protecting only the current direction permits a locally safe second update to change the original e1 response. A cumulative union prevents that particular algebraic history loss, provided the anchors were satisfied on admission.

The zero bank on span(1,1) admits finite stored pairs (a,-a). A row (Fmax,Fmax) with that same space admits only its original finite endpoint under exact anchor preservation. These examples have different protected anchors: they are not evidence that one fixed-anchor safe chain has consumed its entire global class. Rounding a small proposal back to its current endpoint is local stagnation, not a loss of abstract dimension.

ALG and BIT remain different. Exact annihilation can fail to preserve a rounded execution; a full-rank finite legal domain can admit a nonzero BIT-equivalent stored edit that is not an algebraic annihilator. Neither finite alphabet enumeration nor a capacity formula supplies live update authorization.

## Changing-history stability and numerical accounting

For the selected stored versions at time t, the implemented comparison uses

`E[t+1] = L[t] E[t] + beta[t]`,

where beta includes same-input endpoint-map drift and both execution residuals. Actual endpoint differences already include projection, optimizer and storage effects. Their path-length sum is an alternative conservative accounting route, not another error term to add to the net endpoint difference.

Update index k and execution time t are independent counters. The bound explicitly binds both histories and nondecreasing version schedules, including skipped/repeated versions and unused declared endpoints. All versions must match the physical layout. Finite tubes are recomputed from both histories. The common-family route checks every mode's rounded image and every ordered mode pair under one infinity norm; it covers only that named family and declared input domain.

The nilpotent modes A=[[0,2],[0,0]] and B=A-transpose each send every exact state to zero after two repetitions. Their alternating product BA=diag(0,4) instead amplifies e2 by four every pair. Thus one cannot reuse each mode's separate stability claim as a common switching certificate. The exact real example is not an unbounded finite-format execution promise: range checks eventually matter.

Stored negative zero and nonfinite values are rejected, arithmetic zero is canonicalized, and finite subnormals use gradual underflow. The fixed graph uses separate multiply/add, explicit order and declared nonlinearities. Hard-guard margins, changed calls/layout/policy, overflow and domain exits require renewed evidence or refusal. A positive conservative bound is never labelled observed D drift.

## Implementation and transaction boundary

`capacity_history.py` computes exact algebraic history/anchor/response quantities and enumerates explicitly bounded stored families. `switching_bounds.py` creates rational changing-history bounds, common-family certificates and prefix ledgers. `sequence_certificate.py` checks complete canonical numerical evidence and has no publication authority.

An optional external exact-D snapshot in a numerical receipt is an identity binding supplied by the trusted caller. It does not authenticate that snapshot, establish its live freshness, or prove a correspondence between its state and the numerical history. The checker compares the complete caller-expected context; only the separate live exact-D owner checks its own current state and can publish an update.

`update_sequence.py` retains the unchanged B1/A3 exact-D gate. It prepares and checks a proposed endpoint, optimizer state and history ledger on an unexposed copy, then publishes one complete owner value. The trusted serial API rejects stale snapshots, inconsistent metadata and unauthorized protected edits. Refusal leaves weights, D state, optimizer, versions and ledgers unchanged. An administrative accepted-history limit is explicitly distinct from algebraic capacity and numerical error budgets.

The structural demonstration uses the registered two-call feedback model with legal Boolean state/input and an editable third column. Its toy A target is (1,-1), evaluated on e3 with loss equal to half the squared exact difference of decoded actual outputs. The surrogate optimization rule is not claimed to differentiate finite-word rounding. Returned snapshots are detached from owned state.

## Actual validation

The three standalone main producers have passed with seed `20261114`:

| Producer | Assertion checks | Expected refusals | Scientific scope |
|---|---:|---:|---|
| Capacity/history | 14,345 | 10 | 1,458 complete stored histories, 72 seeded rectangular histories, 1,728 response/rank-cap queries, 27 three-task anchor assignments, 1,892 endpoints in 12 explicitly finite families |
| Switching/budgets | 4,028 | 10 | 1,152 complete trajectory pairs in named finite mode/input alphabets, 12 seeded length-12 pairs, common-family certificates and numerical counterexamples |
| Transactions/learning | 1,120 | 98 | 64 learning updates and paired feedback ticks, full registered Boolean D checks, 58 rehashed tamper cases, 14 budget-exhaustion cases and rollback boundaries |

These are assertion and case counts with different units; they are not a count of proved universal propositions. All three records have zero unexpected failures. Finite endpoint families are not the full BF16/FP32 universe, and sampled histories do not establish arbitrary-history safety.

Both toy runs use 32 SGD attempts at learning rate 1/4, starting from the actual registered reserved coordinates `(1,0)`. Their actual results are:

| Format | Accepted / refused | Nonzero stored updates / accepted no-ops | Initial loss | Final decoded loss |
|---|---:|---:|---:|---:|
| Software BF16 | 32 / 0 | 16 / 16 | 1/2 | 1/32768 |
| Local CPU FP32 | 32 / 0 | 32 / 0 | 1/2 | 2839225/562949953421312 (about 5.04348e-9) |

BF16 first rounds the update to a no-op on attempt 17, ending at `(1,-127/128)`. This is a concrete storage-induced plateau despite unchanged unrestricted dimension four, reserved-coordinate dimension two and target-response dimension two. FP32 ends at `(1,-16775531/16777216)`. Every paired D tick and every complete registered D-state/input table agrees bitwise under the fixed policy. The counts of accepted updates, nonzero stored changes and optimizer steps remain distinct. No universal or sustained learning advantage is inferred.

The independent verifier passed 33,901 checks with 56 expected refusals and zero unexpected failures in its recorded 79.999-second primary run. It uses its own exact minors/direct linear equations, raw-word decoding and nearest-even reference, interval recurrences and product-sum reconstruction instead of the main verifier's assertion logic. Its scope includes 486 budget cases, 512 response queries, 27 joint and 81 pairwise anchor checks, 486 stored history/mode cases, 1,136 endpoints in 16 finite families, 34 accepted repeated/no-op updates with 32 learning/feedback ticks, and 12 read-only receipt cases.

Its 1,142 numerical trajectory pairs comprise 1,080 complete cases from named scalar schedule/input/initial alphabets, 60 nonlinear/shared-call cases and two nilpotent witnesses. They are not exhaustive over every canonical input word. Eighteen common-family ordered-pair checks have their own exact oracle. The independent run also redecodes the frozen B1 refusal evidence without rerunning its optimizer. Its 11 Python-source and three producer-result bindings match the current files.

The aggregate primary run passed all three sections: 19,493 assertion checks and 118 expected refusals, with zero unexpected failures, in 70.287 seconds. It verified all 739 prior-file hashes and the exact nonexcluded inventory before and after execution and bound 13 current source/dependency inputs. Costs are reference-fixture wall times, not a speed claim or a performance comparison.

The [foreign-directory driver](reproduction_driver_results.json) passed from `/tmp`. The repeated main and independent runs took 74.401 and 85.499 seconds respectively. Five comparisons matched after removing only wall-clock fields: primary/repeated main, primary/repeated independent, and each of the three standalone producers against its aggregate section. Seeds, scientific values, raw words, counts, source hashes and logical time indices remained in those comparisons. Both `-O` and `-OO` executions were refused before any test section ran. The driver verified unchanged primary evidence, current sources and the 739-file predecessor inventory. This is reproducibility in the same host from a different working directory, not an independent hardware certification.

Two development corrections are disclosed in [Errata](P2_B4_Errata.md): the independent oracle now decodes the actual initial reserved weights instead of assuming zeros, and the new numerical receipt adapter normalizes a scalar cap to a one-coordinate vector before the core checks dimensions. Affected checks and the final primary/independent/reproduction runs passed after these corrections. No previous-stage evidence was replaced.

## Limits and next-stage obligations

The mathematical spaces may be large even when the finite stored transition graph or selected optimizer cannot make progress. A finite endpoint class permits repeated states but does not imply eventual periodicity under arbitrary external update choices, or infinitely many useful functions. Adding tasks can fail because anchors conflict, not only because rank is exhausted. Changed reachability needs a fresh full-domain argument; no sample statistic is promoted to a global certificate.

The reference numerical engine supports one or two state coordinates, horizons up to 64, at most 128 versions per history and at most 16 distinct common modes. These are implementation limits, not bounds on the conditional theorems. The main toy learning experiment uses 32 accepted updates per format; finite numerical histories have their explicitly recorded lengths. No infinite-run inference is drawn from these experiments.

GPU, native BF16, FMA, arbitrary compiler transformations, general concurrent publication, process-crash atomicity and hardware fault tolerance remain uncertified. The serial owner relies on a trusted Python API and private storage. Generic nonlinear control flow, automatic all-program activation coverage, unbounded optimizer-state reasoning, general learning performance and an overall machine proof remain open.

The [C1 handoff](P2_C1_Handoff.md) identifies the proof-producing compiler/domain/graph correspondence obligations to address next, subject to the original C1 specification. No C1 implementation or authorization is included. B4 ends at this delivery point.
