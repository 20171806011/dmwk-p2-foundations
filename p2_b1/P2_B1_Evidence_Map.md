# P2-B1 — Claim-to-evidence map

The universal claims below are conditional mathematical proofs in [P2_B1_Theorems.md](P2_B1_Theorems.md), using [P2_B1_Definitions.md](P2_B1_Definitions.md). Finite verification checks the reference implementation and selected hypotheses; it does not convert those proofs into a complete machine-checked theory. Seeds, cases, refusals, word-level outputs and costs are recorded in the linked JSON artifacts.

## Proof and implementation correspondence

| Claim | Proof mechanism | Producer evidence | Necessary boundary |
|---|---|---|---|
| **T1: exact orthogonal restriction** | Symmetry/idempotence of P and the orthogonal Frobenius decomposition prove range, nearest point and nonexpansiveness of `G P`. | `constrained_updates.project_direction`; the constraint suite covers 324 exhaustive small H/G pairs and seeded rational factor/projection cases. | The protected space must be globally justified. A sampled H does not authorize unknown call sites or inputs. The minimizer is an exact algebraic map, not a nearest finite BIT endpoint. |
| **T2: nullspace and low-rank representations** | A full-column-rank basis N gives the unique coordinates `Delta=Z N.T`, rank equality and factor coverage. | `nullspace_update` and `lowrank_update`; 64 seeded rectangular factor cases plus four named edge cases. Direct ranks and null products are recorded. | Per-proposal exact rank is distinct from rounded effective rank, cumulative rank and baseline-adapter rank. No live rank-cap certificate is supplied by these helpers. |
| **T2(a/b): optimization metric and rank semantics** | Chain rule supplies the coordinate gradient; a Gram inverse recovers Frobenius projection. Two explicit diagonal constructions distinguish step and persistent-adapter ranks. | Exact mathematical constructions in the theorem text; the producer records rank-boundary examples. | Equivalent parameter coverage does not imply identical optimizers or a metric independent of the chosen basis. The coordinate-metric argument is a handwritten exact statement, not a claim of target-format differentiation. |
| **T3: optimizer closure and failure conditions** | Linearity proves safe scalar combinations. Momentum's off-space component is explicit. Coordinate clipping/scaling, exact Adam normalization and decoupled decay give constructive failures. | `optimizer_proposal`, `stage_optimizer` and `clip_direction`; four named optimizer counterexamples plus the training routes record the actual staged order and moments. | SGD/momentum proposals are rational; AdamW is a declared finite host computation. No general rounding theorem for Python power or `math.sqrt`, optimizer convergence theorem or preserved exact norm threshold is asserted. |
| **T4: endpoint obligations remain** | Exact subtraction gives `Delta_eff=D+S`, so a safe ideal D need not give a safe endpoint. Rounded-thirds and tiny-edit constructions separate ALG and BIT. | The numerical/domain section records 15 cases, 38 checks and eight expected refusals across software BF16 and audited CPU FP32. Actual rounded endpoints, exact differences and complete local BIT checks are used. | A floating test on a basis cannot establish safety on every legal activation. Full protected rank only exhausts exact annihilators, not every finite-domain BIT class. |
| **T5: partial acceptance and combined rollback** | All computation and validation precede the sole immutable-bank assignment. Full-snapshot binding prevents overwriting a later D tick or optimizer state. Finite-event induction uses the same protected input/state/schedule premises. | `OptimizerKernel.prepare/commit/tick`; producer transactions give 46 checks and 32 expected refusals. Training adds 75 accepted safe optimizer commits and 21 safe-route refusals with full-state rollback comparisons. | Trusted single-threaded ownership; no process-failure atomicity, concurrent mutation or malicious-memory protection. Canonical evidence is not authentication of original intent. |
| **T6: structural responding family** | Immutable identity columns and sparse protected reads give identical operands; Boolean XOR closes the complete state invariant. Legal A input e3 returns the two reserved words. | Both formats execute all declared Boolean contexts while training. The structural SGD run changes A response from (1,0) to (0,2), preserves all D contexts and reaches zero loss on the one declared target. | A fixed 2-by-3 model with two reserved coefficients, not a general compiler or evidence of broad learning ability. Validation is pure, but its host instruction trace is not claimed independent of reserved values. |

The exact, stored-endpoint, BIT and A-response notions inherited from A4 remain separate. ALG and BIT are generally incomparable. The live default is **ALG_AND_BIT**; an explicitly selected BIT-only route is checked under its own contract and does not inherit an algebraic rank bound.

## Current producer records

| Record and generator | Actual scope | Status |
|---|---|---|
| [constraint_results.json](constraint_results.json), [verify_constraints.py](verify_constraints.py) | 2,400 checks: 2,316 exact/optimizer checks, 38 numerical/domain checks and 46 transaction checks. 324 exhaustive projection pairs, 64 seeded factor cases, four named factor cases, four optimizer counterexamples. Eight numerical/domain and 32 transaction refusals are expected. | Passed; zero unexpected failures |
| [training_results.json](training_results.json), [verify_training.py](verify_training.py) | 1,013 checks; 24 runs; 192 proposals: 75 safe accepted commits, 21 safe refusals and 96 applied offline baseline steps. Seed 20261114, eight shared feedback input bits. | Passed; zero unexpected failures |
| [independent_results.json](independent_results.json), [verify_independent.py](verify_independent.py) | 512 exact projection/nullspace/low-rank cases; 144 optimizer proposals; all 192 recorded training attempts and 1,536 complete-domain context comparisons; 58 full-snapshot refusals | Passed; 2.974865151 seconds |
| [verification_results.json](verification_results.json), [verify_b1.py](verify_b1.py) | Both planned sections completed, no unexecuted sections, 413 prior artifacts verified unchanged | Passed; 8.695691488 seconds |
| [reproduction_results.json](reproduction_results.json), same entry point from a different working directory | Both sections completed again, no unexecuted sections, 413 prior artifacts verified unchanged | Passed; 8.822424968 seconds |

The sums above distinguish implementation checks from distinct mathematical instances. Expected rejection is a tested protocol outcome, not an unexpected failure. Finite cases in different runs may overlap; repeated checks do not enlarge the proved domain automatically. Component costs are recorded by their JSON files and are not speed comparisons.

## Optimization evidence and its limits

Every run starts with A response (1,0), target (0,2) and exact decoded loss 5/2. The objective uses one legal A basis input, with the continuous linear squared-loss gradient at the decoded bank. This is an explicitly supplied surrogate for proposing a new stored endpoint; it is not the derivative of the rounded execution function.

| Format and optimizer | Dense final-projected route: accepted / refused | Final dense loss | Structural route: accepted / refused | Final structural loss |
|---|---:|---:|---:|---:|
| BF16 SGD | 8 / 0 | 5/131072 | 8 / 0 | 0 |
| BF16 momentum | 2 / 6 | 10125/8192 | 8 / 0 | 20353/2097152 |
| BF16 AdamW | 1 / 7 | 8593/4096 | 8 / 0 | 3128225/33554432 |
| FP32 SGD | 8 / 0 | 5/131072 | 8 / 0 | 0 |
| FP32 momentum | 8 / 0 | 3217343436125/562949953421312 | 8 / 0 | 81972005/8589934592 |
| FP32 AdamW | 0 / 8 | 5/2 | 8 / 0 | 839678799469385/9007199254740992 |

All actual endpoints in these live safe runs preserve the complete registered D domain. The independent replay finds that all **21** rejected proposed endpoints preserve the declared BIT observations but violate the separately selected exact ALG condition. They are correctly refused under the fixed joint claim; the run does not silently switch to BIT-only acceptance. Rejected attempts retain their old optimizer state, so repeated identical rejected proposals can remain stuck; the FP32 dense AdamW run records exactly that behavior. The experiment therefore does not promise accepted progress, even for a projected proposal. The structural and dense models have different parameterizations and protected graphs, so this table is not evidence of one optimizer or architecture's performance advantage.

The other twelve runs are **offline** unconstrained or gradient-only baselines. Their 96 endpoint applications are not authorized live commits. Full-domain D checks and feedback diagnostics are recorded separately; a baseline loss reduction does not certify protected behavior. A diagnostic stops the Boolean transition when its operands cease to be canonical bits rather than extending an invalid Boolean-state contract silently.

## Refusal coverage

The producer's B1 transaction cases check stale replay after commit, a D tick after preparation, an unsafe AI endpoint, unknown restriction, wrong gradient shape, noncanonical serialized text, and inconsistent graph, numerical policy, schedule, model, weight version, optimizer state, configuration, request or candidate-word fields. They also verify that a BIT-only tiny endpoint is accepted under its selected contract and refused under the joint claim. Every recorded refusal compares the complete combined snapshot, including optimizer step and moments.

These tests concern inconsistent records or unsupported semantics. They do not establish cryptographic origin or intent authenticity: a coherently recomputed valid candidate under the same fixed safety premises is a new authorized trusted-caller proposal. A checksum is not an authority to bypass the complete checker.

## Independent checker and reproduction

The independent algebra checker uses direct annihilation/residual-span equations and determinant/minor ranks. It visits 64 binary 3-by-2 generators and 512 seeded exact cases. Each of those 512 cases checks projection characterization, a nullspace construction and a low-rank construction; these are **512 cases with three checks**, not 1,536 distinct sampled cases. Its algebra seed is 20261114.

The optimizer reference uses independent IEEE decoding and word-search round-to-nearest, including midpoint-square reasoning for the selected square-root comparisons. It checks 144 proposals across three optimizer kinds, three clipping modes and four restriction modes using subseed **20261115**. The selected dyadic power cases are exactly representable; this does not certify arbitrary Python power or libm behavior.

The training replay reconstructs every recorded gradient, moments, raw and restricted increment, rounded endpoint, effective ALG residual, complete local BIT observation, feedback state and A loss. It checks all 192 attempts and 1,536 protected contexts and reproduces the 75/21/96 accepted/refused/offline counts. Its separate transaction suite records 58 refusal comparisons of complete snapshots and 22 direct complete-domain context checks, including detached-record/configuration ownership boundaries. Numerical boundary checks also cover three exact Adam epsilon cases and the inherited format-specific failures.

The producer training result's hash is bound in the independent output. Aggregate/reproduction source hashes and prior-file checks are recorded separately. Repeated finite work is reproduction evidence, not extra universal proof coverage. The programs record no old-stage suite rerun and no B2 execution.

The independent verifier was also repeated from `/tmp`, producing [independent_reproduction_results.json](independent_reproduction_results.json) in 2.820407227 seconds. [driver_checks.json](driver_checks.json) confirms that both primary/reproduction pairs agree after excluding only timing/timestamps, and that the two standalone components match the aggregate. Source hashes and every non-timing result remain in the comparison. The main entry point's two optimized-mode refusals occur before any scientific section; those expected refusals are not failed mathematical claims.

## Arithmetic and verification boundary

Exact projection, rank and residual checks use Q and extend mathematically to R under their stated assumptions. The BF16 execution tests use software round-to-nearest, ties-to-even; FP32 uses audited local CPU scalar operations. Protected operations preserve the declared canonical-zero, gradual-underflow, fixed-order and no-FMA contract. The optimizer's host arithmetic is a distinct proposal computation whose outputs still require endpoint acceptance.

No SMT queries or Lean/Coq proof checking are claimed. GPU, native BF16, arbitrary compiler transformations, general concurrency, crash recovery and arbitrary A-to-D feedback remain uncertified. The original D program, complete domain, invariant and trusted execution policy remain fixed. Prior-stage files are read-only dependencies, not modified or revalidated by rerunning their old suites.

The [written review](P2_B1_Review.md), [completion record](completion_status.json) and [final integrity manifest](final_integrity.json) remain distinct from scientific verification. They record review disposition, the scoped stopping point and artifact identity; none converts a finite check into a universal theorem. A filename or a completed stage label does not substitute for proof premises, independent scope or actual result content.
