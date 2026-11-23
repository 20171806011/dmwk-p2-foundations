# P2-B4 independent review

## Scope and checkpoint review

The B4 plan, mathematical checkpoint and B3 handoff were reviewed before independent implementation. The required earlier capacity, endpoint and execution contracts are read-only. No predecessor verifier or saved optimizer trajectory is rerun. This review concerns B4 only and does not implement C1.

No initial mathematical blocker was identified. The checkpoint distinguishes actual stored increments, prefix safety, final cancellation, task admission, moving protection spaces, finite endpoint classes and changing-history execution. The following obligations guide the independent checks.

1. Every prefix is safe for a fixed annihilator exactly when each adjacent actual increment is safe. A safe final sum alone proves neither intermediate endpoint safety nor unchanged executed history.
2. A newly protected task needs a compatible target anchor at its admission endpoint. Restricting future increments cannot retroactively satisfy or preserve a previously unprotected task. Joint feasibility must check all linear relations across tasks, not only pairwise intersections.
3. Algebraic freedom does not decrease simply because an update counter advances. Cumulative independent constraints may exhaust it; nonnested current constraints may recover dimensions while losing historical protection. Individual update-rank bounds do not constrain a cumulative residual to the same rank.
4. Exact annihilation, storable endpoints, complete finite-domain BIT equivalence, certificate acceptance and A-response signatures are different capacity objects. Their counting statements require a fixed endpoint family, graph, legal domain and anchor where used.
5. Execution time t and accepted update index k have separate schedules. Every changing-history bound must cover both actual intermediate domains, the fixed exact-map comparison, both arithmetic errors and the initial pair relation. Uniform switching requires one common norm and a proved common invariant, not merely separately stable modes.
6. The exact-D wrapper must stage B1 authorization and the new optimizer/history/ledger together, then publish one combined value. Any later ledger or budget refusal must leave the old owned snapshot intact. Numerical switching receipts remain read-only and cannot waive the exact gate.

## Final mathematical and interface audit

The full T1–T9 proofs, Definitions, capacity and switching interfaces, capacity analysis, numerical analysis and exact-D transaction specification were reviewed. No blocking mathematical or implementation-contract inconsistency was found in their stated scope.

- T1 requires every prefix, making the converse by adjacent subtraction valid. Final cancellation alone is correctly excluded.
- T2/T3 require a globally justified space and a satisfied task anchor at admission. All concatenated linear relations are checked; pairwise intersections do not suffice for three tasks. Cumulative preservation starts at each actual admission bank, not automatically at the original bank.
- T4 extends the induced quotient response map by zero, making its image exactly the requested response image and proving minimum rank. The cumulative rank construction uses distinct complementary directions and differs from a persistent adapter's rank constraint.
- T5 fixes the absolute endpoint universe and protected anchor/context. Translating a relative proposed-step set would not prove class invariance. Zero and saturated anchors are different classes. Raw local BIT and inherited certificate acceptance remain different; local equality does not supply a program invariant. The A-response statement includes the required A-totality/failure-output convention.
- T6/T7 use actual selected endpoints, the initial relation, both arithmetic errors, all shared calls and jointly propagated domains. Common input coordinates contribute to ranges/forcing but not the first state-difference gain. The family certificate checks every mode and ordered pair in one norm. No all-time inference comes from a finite tube or separate stable modes.
- T8 charges every prefix, including time zero. Conservative refusal is not measured drift. Unused history versions are bound and structurally validated; they receive no future transition-domain certificate unless covered by the common family.
- T9 protects the designated D observation trace; success intentionally changes weights, optimizer and history metadata. Rollback compares the entire owned snapshot. The copied B1 kernel is checked before one outer publication; a later copy-local ledger refusal cannot publish a partial real update.

An additional read-only integration audit by the switching-core contributor found no blocker in the receipt, owner and T8/T9 boundary. That reading added no scientific test and changed no source. An external exact-D snapshot attached to a numerical receipt is identity data only: it proves neither authenticity, independently discovered live freshness nor correspondence between the numerical state graph and Boolean D graph. Unkeyed digest consistency is not authentication.

## Actual independent verification

[verify_independent.py](verify_independent.py) passed and saved [independent_results.json](independent_results.json). The run used seed **20261114**, reported **33,901 checked assertions**, **56 expected refusals**, zero unexpected failures and **79.998951999 seconds**. Counts include reference-domain guards and repeated checks; they are not independent experiment counts. The verifier source SHA256 is:

    c7f6666325e9a48ae39d53ee4f734716279c604e126121809a9bddbff2f20f6f

The result binds current Python source hashes and the three producer JSON hashes. Current modules load by exact file path. The post-run verification-module inventory contains only this new verifier; no predecessor verification suite is imported or run. Pure older mathematical/execution interfaces remain dependencies.

| Section | Actual finite coverage | Distinct reference logic |
|---|---|---|
| Exact algebra | 486 budget cases, 512 response/cap queries, 27 joint assignments and 81 pairwise checks | Determinants of minors; augmented row equations; direct response and impossibility-witness verification |
| Stored histories | 486 history/mode cases plus higher-dimensional witnesses | Exact adjacent differences, sums, admission-anchor equations and minor ranks |
| Finite endpoints | 16 named families and 1,136 candidate examinations | Own call lists, exact matrix action, word outputs, group/rank/image counts and class comparisons |
| Exact-D sequence | 32 SGD steps, 32 paired feedback ticks, 128 full D observations and two additional accepted no-ops | Own endpoint RNE, decoded loss, actual difference/rank, path sum and XOR reference |
| Switching | 28 analyses, 1,142 trajectory pairs and 18 family ordered-pair references | Independent word arithmetic, signed intervals, state-column gains, both rounding errors and direct product sums |
| Read-only receipts | 12 accepted receipts and 24 refusal checks | Reconstructed numerical proof, rehashed mutations, initial-relation checks and full-owner nonzero-moment rollback |
| Frozen B1 | 21 saved refused endpoint pairs and 84 state/input pairs | Read-only decoding and direct outputs; no old optimizer trajectory regeneration |

The 1,142 switching pairs comprise 1,080 complete cases in the named scalar three-tick schedule/input/initial-pair family, 60 finite nonlinear/shared cases and two nilpotent witnesses. They do not enumerate every canonical input history. Conditional family coverage follows its separate enclosure proof.

The floating oracle decodes words to exact rationals and selects nearest-even results by ordered-word binary search, tie parity and explicit overflow/canonical-zero handling. It does not use the implementation's rounding assertions as its expected answer. Actual traces use inherited software BF16 or audited local CPU FP32; the independent expectations use exact rational/word computations. These are separate methods in the same Python host, not certification of that host.

The interval oracle rebuilds product/addition allowances, per-endpoint enclosures, joint-domain forcing, shared-call composition and the recurrence. It checks first-layer gain from state columns alone. Family checks include unused modes and all ordered pairs. The nilpotent history reaches (0,8) from (0,1/8) in six ticks; this is a finite witness, not an infinite-format growth guarantee.

The 56 refusals consist of 22 exact-D checks, 10 switching premise/budget checks and 24 receipt checks. They cover rehashed endpoint/event/moment/task/schedule/domain inconsistencies; stale ticks; late ledger refusal after copy-local B1 commit; illegal ticks and protected-column edits; omitted modes and decreasing versions; wrong adjacent reference and time-zero budget; changed receipt history, initial relation, bound or authority; and numerical-receipt rejection by the live exact-D owner. Full snapshots, including nonzero moments and both ledgers, remain unchanged on refusal. Caller configuration, snapshots and previews have no mutable alias into the owner. Hostile private mutation, concurrency and crashes are outside this check.

## Producer and synthesis evidence

Standalone records were inspected and bound without importing their verifier modules:

- capacity: 14,345 assertions, 10 expected refusals;
- switching: 4,028 assertions, 10 expected refusals;
- transactions: 1,120 assertions, 98 expected refusals.

The new primary aggregate also passed all three sections with 19,493 assertions and 118 expected refusals. Overlapping main and independent sets are not summed into independent theorem proofs.

The primary structural experiment records 32 accepted updates per format. BF16 makes 16 nonzero changes followed by 16 accepted no-ops, ending at loss 1/32768; FP32 makes 32 nonzero changes, ending at 2839225/562949953421312. The independent 16-step-per-format trajectory recomputes its endpoints and losses separately. These specific decreases preserve fixed D; they prove no universal learning benefit or indefinite distinct capacity.

Frozen B1 remains unchanged: all 21 refused candidates have nonzero protected exact residual and rank-two effective update while the registered Boolean calls agree bitwise. Dense FP32 AdamW stays **0 accepted / 8 refused**, final loss **5/2**. B4's structural success does not overturn that joint-contract failure.

## Corrections and failed draft fixtures

The first independent learning oracle wrongly assumed reserved initial coordinates (0,0). Read-only inspection established the inherited registered value (1,0). The oracle now decodes that baseline; affected checks and the final suite passed. No old result or implementation changed, and the failed draft is not counted as successful evidence.

The transaction contributor initially supplied a scalar where the core requires a state-cap vector. The new receipt now explicitly normalizes a scalar only to a one-coordinate vector; the corrected complete integration suite passed. This was an interface/fixture correction, not a mathematical counterexample. Both corrections are in [Errata](P2_B4_Errata.md).

The Report's vague reference to no experiment beyond 10,000 updates was replaced by the actual 32-update-per-format experiment and engine limits, avoiding an implication of an unperformed long run.

## Scope and packaging separation

General theorems were not machine checked by Lean/Coq or SMT. Exact finite enumerations, seeded sequences, analytic witnesses and local CPU/software operations have separate scope. GPU, native BF16, arbitrary reassociation/FMA/compiler transformations, arbitrary branches, concurrency, crash consistency, hardware faults, universal learning and C1 remain outside this review.

The Report, README, Evidence Map, Counterexamples, numerical/capacity analyses, Transaction Spec and C1 handoff were read for consistency. No blocking scope mismatch remains. Final preservation and packaging are separate root checks recorded in the completion status and final integrity receipt; they add no scientific test or general proof.

Independent reproduction without overwriting saved evidence:

    python -B /workspace/p2_b4/verify_independent.py --output /tmp/p2_b4_independent_review.json

## Final reproduction audit

The actual [reproduction driver](reproduction_driver_results.json) reports success. Its five comparisons passed: primary versus foreign-directory aggregate, primary versus foreign-directory independent evidence, and each of three standalone producers versus its aggregate section. Only named timing fields were excluded. Main execution took 70.286952879 seconds and foreign execution 74.400552056 seconds; independent execution took 79.998951999 seconds and foreign execution 85.498845732 seconds. The independent foreign run retained 33,901 checks and all scientific results.

Both optimized interpreter modes, -O and -OO, were refused before any main test section. The driver preserved five primary evidence files and 13 source/dependency bindings and verified 739 previous artifacts and their nonexcluded inventory. A final separate read-only review recomputed those 13 source and five evidence hashes, both complete non-timing reproduction comparisons and all 739 prior content hashes. All matched. No new scientific experiment was run during this audit.

No blocker remains in this scoped B4 review. General proof, complete named finite cases, numerical reference evidence, backend limits and future C1 work remain separately stated. Final status/integrity records may now be sealed without further scientific source changes.
