# DMWK P2-A3 research report

## Result

P2-A3 establishes an exact linear noninterference theorem for actual stored endpoints and a conditional rule for lifting complete local bitwise equality to protected program traces. A reference checker accepts or refuses endpoint replacements on a small trusted complete finite model, binds its evidence to the execution contract, and publishes a replacement only after successful verification. A nonzero dense patch changes an admitted A output while preserving every protected D call output and state transition.

The central algebraic result is

\[
\forall h\in\mathcal A_D,\quad W'h+b=Wh+b
\quad\Longleftrightarrow\quad
(W'-W)H=0,
\]

provided H generates the exact global protected activation span and the same fixed bias and input are compared. H must cover every protected site of the same physical matrix, every allowed initial state/input history and every time. If it generates a proved larger space, the right-hand condition is sufficient but need not be necessary. A sample-only H does not supply the global premise.

This equivalence is an exact rational/real statement. It is **not** an equivalence for a rounded execution graph. A3 demonstrates both directions of failure between exact algebraic equality and finite-domain floating bitwise equality, including a full-rank example. Consequently the three implemented contracts—ALG, BOUND and BIT—remain separate.

This delivery completes only the stated A3 work. It does not complete general P2-C composition, classify A4 capacity, or publish to a repository.

## Scope and inherited assumptions

The plan and a mathematical checkpoint were saved before implementation. Necessary A1/A2 definitions, proofs, execution contracts, independent reviews and the saved A3 starting point were examined read-only. No previous-stage verification suite was launched. A baseline of **341 prior files**, including earlier research and publication-tree content, remained unchanged through the main and reproduction runs. Listed Git/cache/virtual-environment internals are excluded from that baseline; no repository operations were performed.

Finite BF16/FP32 words decode to dyadic rationals. The algebraic field is explicitly Q or R, with equal rational/real ranks but different scalar sets. The finite legal activation set is not asserted to be closed under real combinations. All stored endpoint differences are exact decoded differences, not additional target-format subtraction instructions and not ideal proposed increments.

The general statement allows k-by-d weights, fixed or jointly edited bias, and multiple sites in common physical coordinates. The executable witness fixes zero bias, a 2-by-2 shared matrix, canonical Boolean state/input words, separate nearest-even multiply/add, gradual underflow, canonical positive zero, bit-preserving storage and a serialized synchronous schedule. Unsupported parameter orientations, transposed uses, new domains or graphs require their own analysis.

Details are in [Definitions](P2_A3_Definitions.md), [Theorems](P2_A3_Theorems.md) and [Execution specification](P2_A3_Execution_Spec.md).

## Proved statements

| Result | Established statement | Essential limitation |
|---|---|---|
| **T1: exact linear noninterference** | Actual endpoint difference annihilates the global activation set iff it annihilates its Q/R span iff it annihilates any generator or basis of that span. | Same inputs and fixed bias; global coverage is a premise. Full-vector equality differs from equality after a selected observation. |
| **T2: sharing, containment and affine cases** | Merge all shared-site spaces. A proved containing space is conservative. Exact k-by-d annihilators have dimension k(d-r), with zero/full-rank cases. Joint bias changes use the augmented actual activation span. | Abstract dimension is not representable endpoint or executable capacity. Augment actual activations before basis compression; independent site biases need separate coordinates/conditions. |
| **T3: finite-arithmetic difference** | Decoded executed change equals the exact effective affine response plus new-minus-old execution error. Exact local absolute errors give computable pointwise bounds, including accepted subnormals. | A measured input bound does not establish a uniform bound or authorize a transaction. Arithmetic failures are refusals, not finite residuals. |
| **T4: local-to-program lifting** | Complete local raw equality and invariant/totality/interface premises imply equal protected traces for every finite horizon. Successive current-bank patches preserve the original trace by transitivity on the same common domain. | Same protected initial configuration, input history and trusted schedule; all editable-parameter reads and relevant effects must be covered. No hidden A-to-D influence or unsynchronized publication. |
| **T5: finite checker soundness** | Correct complete finite-domain checking, endpoint/contract binding and validation-before-publication establish the supported model's obligations; refusal leaves the prior bank/state intact. | Conditional on trusted registry and checker semantics. This is not a formal verification of Python, arbitrary invariant proofs or concurrent atomicity. |

All five are handwritten proofs, independently reviewed. Neither the finite tests nor the source hashes are called machine proofs.

A small positive error bound is not automatically useless for bit equality. The added T3 separation corollary states that finite decoded values in a fixed format lie on eta Z, where eta is the minimum positive subnormal. A certified infinity-norm output difference strictly below eta forces numeric equality; canonical injective finite encoding then forces raw equality. This requires the explicit separation and encoding premises. A pointwise certificate still needs complete domain coverage and T4 before it can support a program-level claim. The implemented BOUND route does not automatically issue BIT permissions using this corollary.

## Three implemented contracts

**ALG** in [linear_contracts.py](linear_contracts.py) computes Delta_eff and exact generator/basis residuals with rational arithmetic. It records that provenance is unverified and bitwise commit authorization is false. The helper can merge supplied site generators and check containing spans, but cannot discover a site omitted by its caller. Affine tests lift actual columns before selecting a basis; the ordinary spans of `{0,1}` and `{1}` agree while their augmented spaces differ.

**BOUND** in [bounded_contracts.py](bounded_contracts.py) executes the specified stored endpoints at one stored input, with the bias as the initial accumulator. For each row, if rho_j and sigma_j are exact decoded local multiply/add rounding errors, the execution error is their sum and its absolute value is bounded by the sum of their absolute values. Therefore

\[
|\widehat y_i'-\widehat y_i|
\le |(\Delta_{\rm eff}h+\delta_b)_i|+
\beta_{i,\rm old}+\beta_{i,\rm new}.
\]

Every quantity is computed exactly as rational data for the performed execution; no unverified relative-error model is needed at underflow. Reports preserve words, intermediate errors, bias and endpoint differences, and explicitly set `authorizes_commit` to false. They are a posteriori reports, not a general prospective verifier over arbitrary domains.

**BIT** in [certificate_kernel.py](certificate_kernel.py) uses a trusted registry of five declared finite models. Two have Boolean feedback; three are stateless boundary fixtures. For a stateful model the checker enumerates every site/activation and every Boolean state/input pair, compares full output words, verifies closure and requires the old and new banks to match the registered invariant output map. Merely presenting two equally wrong banks cannot satisfy that stateful invariant.

The checker is deliberately incomplete: unknown domains, arbitrary proof languages and alternative graphs are refused. Its declared completeness follows from the small model and closure proof; it is not inferred from observed trajectories.

## Nonzero patch with active D reads

Use one shared dense matrix, initially W_0=I_2. The protected call sites prepare `(q,q)` and `(u,u)`, with q,u canonical bits. Both complete two-coordinate outputs are protected. The next state is the fixed floating Boolean XOR graph on their first coordinates, using the same old snapshot.

The replacement

\[
W_1=\begin{pmatrix}0&1\\2&-1\end{pmatrix},\qquad
\Delta_{\rm eff}=\begin{pmatrix}-1&1\\2&-2\end{pmatrix}
\]

produces `(t,t)` at every protected `(t,t)`, t=0 or 1, with exactly representable intermediates in both formats. All changed entries are actually evaluated when t=1. The two calls and their XOR transition therefore agree, the Boolean invariant is preserved, and T4 applies for every finite legal input history and accepted patch/tick interleaving.

At legal A input e1, the actual full output changes from `(1,0)` to `(0,2)`. Both stored endpoints and the output difference are nonzero. This goes beyond A2's sparse read-exclusion witness while remaining a small, completely specified finite model. It demonstrates functional editability, not training success, useful task performance, convergence or optimal capacity.

## Acceptance, refusal and binding

A certificate includes the schema/claim, model and physical matrix identity, format, old/new raw matrices, exact derived Delta_eff, fixed bias, full site/domain/invariant descriptor, graph, arithmetic policy, scheduler, expected weight version, complete call and state-transition evidence, and source/descriptor/payload identities.

At commit the checker reconstructs the trusted descriptor and recalculates the evidence against the current bank and version. It demands canonical byte agreement with the expected record. Recomputing a digest after deleting a legal input, falsifying a proof result or changing the graph does not bypass this process. Hashes establish identity, not semantic truth or unforgeable authority.

The implementation accepts only exact built-in primitive types and bounded canonical JSON. It refuses malformed shapes, invalid words, duplicate JSON keys, nonfinite JSON, changed endpoints/effective differences, missing sites or states, sample-only claims, unknown invariants, unsupported reduction/FMA/fusion policies, schedule changes, stale versions and forged implementation identities. The verifier creates its own audit containers rather than invoking caller callbacks.

All validation completes before one immutable-bank publication. Refusal preserves weights, protected q, version and tick count. Reinitialization is refused. A certificate may remain valid after a legal D tick if weights/version are unchanged, because its proof covers every legal state, not the current state alone. Successful commits, including no-op commits, increment the weight version and invalidate stale replays. Version exhaustion refuses new commits.

These are trusted serialized API semantics. General concurrency, arbitrary private-memory/module mutation, hostile interpreters and process failure during publication are outside the contract. The tick counter is host instrumentation and does not influence D. Equality of update metadata with the original unpatched execution is not part of protected-trace equality.

## Counterexamples and the corrected boundary

The catalog [P2_A3_Counterexamples.md](P2_A3_Counterexamples.md) contains eight classes in both formats, plus a full-rank observational example. The actual records include raw words, exact residuals and refused certificates where applicable.

**Commit rounding:** old row `(2^p,0)` and ideal increment `(1,-1)` have zero ideal response at `(1,1)`. Stored endpoint `(2^p,-1)` instead gives Delta_eff=`(0,-1)` and output change `-1`, p=8 or 24. The actual ALG condition fails, and BIT is refused. This is not an ALG-passes example once ALG is correctly defined using endpoints.

**A basis probe misses a legal activation:** the rounded thirds projector Q annihilates `(1,1,1)` and `eta*(1,1,1)` in exact algebra. Its executed output is zero on the first but raw word `0x1` in every row on the second. Both inputs are explicitly legal. ALG passes while BIT fails, and the complete registered checker refuses. It does not extend a finite legal set by assuming arbitrary real combinations are executable.

**Full-rank BIT can hold while ALG fails:** the split feedback model prepares `(q,q)` and `(u,0)`. Its legal protected vectors `{0,(1,1),e1}` span R^2. Change I_2 to `((1,eta),(0,1))`. The exact response at `(1,1)` changes by `(eta,0)`, so ALG fails. On every legal protected raw input the change rounds away, so the complete BIT checker accepts. At legal A input e2, the actual output changes from `(0,1)` to `(eta,1)`. The same edit is refused when a protected axis site includes e2.

This does not contradict the zero exact-annihilator theorem at full rank. It shows that finite observational equivalence is a different object, essential for the next rank/capacity study. The tiny A response does not establish robustness or learning utility.

Other cases expose an omitted shared site, an initially invisible edit that changes a later feedback state, unmodeled A-to-D input influence despite unchanged D weights, mutable bias omitted from the constraint, and changed reduction/FMA graphs. The fused result is a software one-round reference, not native FMA testing. General floating counterexamples are not silently admitted to the P1 Boolean compiler's restricted coefficient language.

## Actual verification

The primary [verification_results.json](verification_results.json) reports **four of four sections passed**, with no unexecuted section or unexpected failure. Seed: **20261114**. Environment: Python **3.12.14**, NumPy **2.3.5**, Linux x86-64. The observed main elapsed time was approximately **15.307 s**; it is a small-run observation, not a performance claim.

| Evidence | Actual scope and outcome |
|---|---|
| Exact algebra | **39,590 checks**; 6,561 exhaustive 2-by-2 generator/update pairs; 80 seeded rectangular/affine cases; 12 expected input refusals. Passed. |
| Pointwise bounds | **1,008 checks**; 160 seeded cases, four deterministic cases and 16 expected refusals. Passed. |
| Counterexamples | **126 checks**; eight classes in two formats, 12 expected refusals and two additional full-rank observational cases. Passed. |
| Certificate mechanism | **4,676 checks**, including **108 explicit refusal checks**. Per format: every 625 small integer endpoint matrix in each of two models; duplicate model accepts 16/refuses 609, split model accepts one/refuses 624. Passed. |
| Production state feedback | Per format: 64 length-five traces, 320 ticks and 320 interleaved commits, plus 48 seeded feedback cases. Full call outputs and state checked. Passed. |
| Independent algebra | 1,296 binary-generator/ternary-square-update pairs, 576 rectangular pairs and 72 affine cases, using determinant/minor and direct-output oracles. Passed. |
| Independent arithmetic and transactions | Per format: 17 rounding values, two overflow refusals, three pointwise fixtures, 625 endpoint candidates, 64 paired traces/320 paired ticks/320 commits, and 34 named tampering/API refusals plus separate boundary regressions. Passed. |

Counts have different units and overlapping subject matter; they are not summed into a universal confidence score. Exhaustive endpoint searches cover only the named small coefficient alphabets, not all target-format matrices. Each supported certificate nevertheless checks its complete declared legal input/state domain. The arbitrary finite-time consequence comes from the invariant/induction proof, not from five-tick traces.

One strong-witness certificate issuance performs 120 multiplies and 112 additions. In FP32 all 232 native scalar results are checked against rational RNE; BF16 uses software RNE. This is the cost of one issuance, not the total suite operation count. Complete checking cost scales with the explicitly enumerated domain and graph, and does not solve arbitrary-program reachability or large-model verification.

For explicit inputs, testing Delta_eff H costs O(kdm) rational field operations for k-by-d weights and m generators, apart from endpoint decoding and basis/rank work. A pointwise dense report performs O(kd) target operations and exact residual accounting. A finite checker with N local activation cases spends O(Nkd) target operations on those calls, plus complete state/input transition enumeration and serialization/source-identity work; verification repeats the evidence construction. These are operation-count descriptions, not unit-cost bit-complexity bounds: rational numerator/denominator growth and word/JSON processing matter. The delivered small fixed registries terminate by finite bounded loops. This does not supply an efficient general algorithm for proving arbitrary global domains.

The independent verifier uses different assertion logic and oracles rather than importing the production test modules. Review found no unresolved blocker within the final contracts. It clarified full versus selected outputs, affine lifting, non-nested contracts, invariant validation, metadata/callback trust and version semantics. [Errata](P2_A3_Errata.md) preserves A3 clarifications without changing prior evidence. No prior-stage error requiring an overwritten or replaced dependency was identified.

The second main run from `/tmp` also passed, in approximately **15.598 s**. All non-timing fields are compared separately in [driver_checks.json](driver_checks.json); source hashes and residuals are not excluded. Main/independent results, component records and the final integrity inventory identify the actual evidence. The source-bound counterexample component was rerun after the shared certificate source was finalized; earlier evidence was not silently attributed to the changed file.

## Remaining limitations and A4 starting point

No SMT query, Lean/Coq proof, native BF16 run or GPU validation was performed. Local CPU FP32 execution is evidence for the operations actually run, not certification of all processors or library reductions. General concurrency, arbitrary compiler optimization, hidden runtime effects, arbitrary user-supplied invariant proofs and general P2-C combination remain open.

For a larger program, the main unresolved premise is a correct complete context/domain certificate that remains valid across edits and covers every D-influencing interface. Exhaustive finite checking may be intractable; richer structural or symbolic proof methods would need their own soundness and refinement arguments. Numerical tolerance alone is not a replacement for such coverage.

A4 should begin by defining which capacity it measures: abstract annihilator dimension, individual update rank, representable endpoint differences, complete-domain bitwise-equivalence classes, or observable A responses. The full-rank counterexample prevents conflating those quantities. It must retain globally justified sharing/domain information, actual committed endpoints, and a fixed execution certificate, and distinguish changed output from useful learning performance.

[P2_A4_Handoff.md](P2_A4_Handoff.md) saves these prerequisites and a proposed research sequence. No A4 implementation or capacity classification was started. A3 stops here for coordinator review.
