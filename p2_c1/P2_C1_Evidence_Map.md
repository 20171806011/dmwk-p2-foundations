# P2-C1 claim-to-evidence map

## Evidence levels

General theorems are conditional handwritten proofs, not a Lean/Coq or full-host machine proof. Complete named finite source/domain families establish their recorded cases. Seeded larger/deeper examples are samples. Actual software BF16/local CPU FP32 execution and independent exact-word/source oracles are separate methods; neither implies an uncertified GPU or transformed kernel is correct. Source completeness is proved for the trusted closed compiler constructor, not inferred from observing a finite external program.

## Proof obligations and implementation boundary

| Claim | Handwritten source | Implementation/evidence obligation | What it does not establish |
|---|---|---|---|
| T1: source macros and complete sites | [Theorems](P2_C1_Theorems.md), fixed macro identities and structural induction | Canonical whole-source lowering/reconstruction, every site/operand/output wire | Completeness of an externally supplied arbitrary graph |
| T2: exact primitive and finite-tick semantics | Small-integer intermediate proof and state induction | Fixed AND/NOT block, full old snapshot, word-level traces | Arbitrary-weight floating exactness or fault-free infinite hardware operation |
| T3: global activation coverage | Boolean invariant and all-site input preparation | All Boolean state/input envelope and all emitted sites; rank diagnostics | Sample rank as a global certificate; exact reachability from a proper initial subset |
| T4: structural/algebraic capacity | Block basis/rank proof; Frobenius projector proof | Mask, shape, resource and rank/response receipts | Minimal architecture, all observationally safe updates or universal useful learning |
| T4(a): stored endpoint cardinality | Finite alphabet count and one-hot A-totality | Canonical finite words, fixed cross blocks, zero/basis A calls | Exhaustive experimental enumeration of N_F^(mc) words or the unrestricted BIT class |
| T5: response and initial-anchor compatibility | Kernel relation and exact column assignment proof | Duplicate/zero-input consistency and exact representability | Future protection of initial A targets, or success of a particular optimizer |
| T6: actual structural endpoint safety | All execution inputs/cells/effects fixed on D | Complete layout/domain/graph binding, immutable cells | General geometric ALG implies BIT; arbitrary ReLU rotations |
| T7: compiler certificate completeness | Equality to trusted full reconstruction | Expected source/budget/policy and canonical artifact comparison | Intent authentication from unkeyed digests or automatic external-code discovery |
| T8: exact serial publication and rollback | Induction over update/refusal/tick events | Full current endpoint/state/optimizer/version/schedule/ledger, one publication | General concurrency, crashes, hostile private mutation or metadata equality after success |
| T9: repeated capacity distinction | Linear closure, telescope and fixed endpoint universe | Actual increment/no-op/rank/response accounting | Endless distinct capacity or inevitable learning progress |

Every structural capacity statement specifies m-by-c editable cells, ambient n=2+m,d=3+c and V* rank three. The exact all-Boolean generated-call span may be smaller and is recorded separately. Fixed source-state bits, working wires, graph metadata, sparse arithmetic and dense storage are separate costs. The graph plus bank represents the program; the shared B block alone does not.

## Predecessor identity evidence

[dependency_inspection.json](dependency_inspection.json) reports a passing read-only inspection. It records B4 manifest SHA256 `2289d62fa6223193bceee706779a5c92d52fcdcbd95d9b2cdab5159309e2ee31`, 42 manifested entries, 43 actual B4 files, 739 predecessor hashes and a new baseline of 782 prior artifacts. Its selected B4 primary, independent, reproduction, driver and completion records all report `passed` and have recorded content hashes. The scope is identity/status/source binding plus necessary text/interface review, not new old-stage science.

The frozen B1 facts remain separate historical evidence: 21 refused candidates passed the current finite-domain BIT check but failed ALG under the joint contract; dense FP32 AdamW accepted zero of eight attempts and stayed at loss 5/2. C1's new structural layout and learning experiment do not erase those facts and do not inherit B1's model-specific authorization for a different graph.

## Finite implementation evidence

Each assertion counter includes repeated comparisons within a case. The main and independent suites overlap in scope. The seed for the recorded suites was 20261114.

| Evidence | Recorded scope | Connection to claims |
|---|---|---|
| [Compiler tests](verify_compiler.py) and [results](compiler_results.json) | 319,910 checks, 176 expected refusals. The compiler accepted 1,400 requests, refused 69 requests and completed 1,368 accepted artifact reconstructions. Compile requests are one subset of the tests. | T1–T7 cover the supported source, graph, budgets, activations, layouts, initial anchors and numerical policy. |
| Complete small programs | All 576 ordered next-state/output pairs from 24 leaf/AND/NOT expressions, plus 96 derived-macro programs. Both formats and four contexts give 5,376 state/input comparisons and 10,752 executions across the two endpoint choices. | Every call and D output in these families can be compared against the Boolean source. |
| Seeded sources | 12 deeper programs, both formats, all 16 contexts for each selected program, then 384 feedback ticks in total. | The sample covers temporal execution and a broader set of structures. Its size does not establish correctness for the entire source grammar. |
| Finite capacity enumeration | 204 candidate endpoints across four A shapes and two formats with entries in {-1,0,1}. The verifier made 588 A response checks and 816 complete D context checks. | Supports T4–T5 on these finite families. The complete format cardinality is proved separately from enumeration. |
| [Layout selector](compile_ir.py) and [results](layout_results.json) | 104 grid and anchor cases, 28 feasible and 76 expected infeasible. | Selects a minimum-storage feasible shape among the four supported shapes. The concrete budget in the resulting artifact remains bound to the caller’s expected source. |
| [Geometric comparator](verify_geometry.py) and [results](geometric_results.json) | 28 checks, four refused live submissions, with separately enumerated full Boolean context comparisons for both formats. A coupled integer edit and a rounded-cancellation edit both annihilate the exact call span, but only the first preserves all covered word observations. | A read-only test of specified endpoint pairs, bound to the reconstructed source and arithmetic policy. A nonmask endpoint remains outside the exact structural authorization gate. |
| [Transaction tests](verify_transactions.py) and [results](transaction_results.json) | 1,156 checks, 54 expected refusals, 64 accepted SGD updates and 64 paired D feedback ticks. The tests compared 256 full D state/input contexts and 1,792 site traces across these learning updates. | T8–T9 require a bound source, fixed D effects and serial publication. Stale, tampered or unsupported operations are checked against full owned snapshots. |
| [Independent verifier](verify_independent.py) and [results](independent_results.json) | 212,851 checks, 95 expected refusals. 120 one-operator programs per format gave 960 complete state/input cases and 5,152 site observations. Another 30 named or seeded program/format pairs supplied 412 additional cases. The owner check used ten momentum updates per format. | A distinct Boolean interpreter, minor-based rank checks, exact word decoding/rounding and independent owner expectations exercise the implementation separately. |
| [Example request](example_request.json) and [emitted artifact](example_artifact.json) | Parity state machine, one input, initial state zero, seven gate calls, one 4-by-4 matrix, 16 matrix words and two editable cells. Four legal state/input contexts, global containing rank three and all-state call-span rank three. | Readers can rebuild and inspect individual site operands, selected rows, physical activations, fixed words and the parameter mask via the CLI documented in the [README](README.md). |

All five stored verification records above have zero unexpected failures. The learning experiment begins with zero A outputs. The BF16 run made 16 nonzero changes and 16 accepted no-ops, yielding final output (127/128,-127/128) and loss 1/16384. All 32 FP32 updates changed stored weights, yielding (16775531/16777216,-16775531/16777216) and loss 2839225/281474976710656. The target was (1,-1) and the starting loss was 1 in each format. The source-state/learning-index distinction is visible in the tick and publication ledgers. [Training and rollback records](transaction_results.json)

## Counterexamples and read-only geometry

T6 gives a cancellation example where every legal deterministic input of the compiled constant AND gate is (1,1,1) on the D coordinates. Replacing (1,1,-1) with (2^p,1,-2^p) leaves the exact real dot product one on the entire protected span. Fixed-order finite arithmetic returns zero. The opposite subnormal NOT-row edit preserves the relevant Boolean outputs but violates the structural algebraic condition. The geometry comparison evaluates specified stored endpoint pairs on all contexts under its declared graph. Its results carry no commit authority. The live structural owner continues to enforce its own fixed-cell policy. [Geometric comparison proof and scope](P2_C1_Geometric_Comparison.md) · [Boundary cases](P2_C1_Counterexamples.md)

Additional cases exercise omission of a source operation, cross-region connections, modified bias/activation/state or operator order, inadequate budgets, inconsistent initial anchors, unrepresentable one-third coefficients, saturation, branch boundaries, illegal rotation, stale identity and rollback. The compiler's externally expected complete source is essential to detecting a missing site. [Compiler evidence](compiler_results.json) · [Transaction evidence](transaction_results.json)

## Literature and novelty boundary

[Related Work](P2_C1_Related_Work.md) and [literature_sources.json](literature_sources.json) record original-source checks for GPM/OGD. Projection away from protected gradients/representations is prior work; this stage's tested object is a bounded compiler-owned source/domain/graph/layout and exact publication contract. The evidence is not a claim that this is the first such general idea, a performance advantage over prior methods, or a universal solution to continual learning.

## Reproduction and packaging

The primary aggregate passed all 4 sections with 321,198 assertions, 310 expected refusals and zero unexpected failures in 85.188 seconds. It verified the 782 prior artifacts and bound 14 source and dependency inputs. The independent verifier separately passed 212,851 assertions with 95 expected refusals. [Primary results](verification_results.json) · [Independent results](independent_results.json)

The main driver binds the current research sources, recorded dependency inventory and emitted test sections. The independent entry point binds its own oracle and three implementation files. The archived records include wall time separately from scientific values. The foreign-directory driver evaluates both entry points under the same host environment and uses a recursive comparison that removes wall-clock fields while retaining all logical times, word outputs, counts and provenance. [Main entry point](verify_c1.py) · [Independent entry point](verify_independent.py) · [Reproduction driver](verify_reproduction.py)

Both verification entry points passed from `/tmp`. The foreign main run took 84.928 seconds and the foreign independent run took 17.813 seconds. All 6 comparisons matched after excluding wall-clock fields. These compare the two foreign runs with their primary records and each of the four standalone suites with its aggregate section. Both optimized interpreter modes refused before any test section. [Reproduction results](reproduction_driver_results.json) · [Foreign main record](reproduction_results.json) · [Foreign independent record](independent_reproduction_results.json)

The completion record identifies the scoped claims and source and result hashes. The final manifest records byte sizes and checksums of the other deliverables. [Completion status](completion_status.json) · [Final integrity](final_integrity.json)
