# DMWK P2-B1: constrained optimizer updates and certified endpoint publication

## Result and scope

B1 establishes a conditional update protocol with a concrete nonzero optimization witness. An AI-proposed direction and an optimizer-generated increment enter the same endpoint pipeline: form the complete proposal, apply its declared restriction, round a replacement bank, check the actual endpoint against the selected claim, then publish weights and optimizer state together. Refusal preserves the entire old bank. This is stronger than projecting only the gradient, but it is not a guarantee that every useful proposal has an acceptable stored endpoint.

The exact restriction is a Frobenius orthogonal projection onto a globally justified linear annihilator. The executable safe operator is instead a **partial certificate-gated transaction**. It is neither a linear projection onto a finite floating safety set nor a nearest-safe-endpoint solver. This distinction is essential to the recorded optimizer failures and refusals.

This invocation completes B1 only. It does not perform B2, establish general learning benefit, finish B4 long-term training, or certify the complete C-series system. Earlier research and the published repository are read-only dependencies.

## Inherited premises and chosen small models

Fix the protected D program, all legal initial states and input histories, physical sharing and all call sites, bias policy, graph, canonical storage, correct rounding, same-snapshot synchronous state updates and trusted serialized schedule. A1 supplies the activation-domain vocabulary, A2 the projection/endpoint distinction, A3 complete-domain local certificates and conditional trace lifting, and A4 rank and target-response budgets. The B1 dependency inspection checked the A4 handoff artifacts and their hashes without rerunning old suites.

For exact algebra use Q or R. All executable finite endpoints decode to dyadic rationals. A working space V is either the exact global protected span or a proved containing space; a conservative space may overfreeze capacity. A sample span alone does not authorize protection. Bias is fixed in the executable fixtures; any joint affine edit requires its own augmented-domain construction.

The dense optimizer fixture reuses the unchanged `duplicate_feedback_v1` registry. Its shared 2-by-2 bank starts at I2. The two D sites consume `(q,q)` and `(u,u)` for every canonical Boolean q/u, and the next state is the fixed XOR of their first outputs. Both complete site outputs are protected. Legal A input e1 initially returns `(1,0)`.

The new `structural_duplicate_v1` has a 2-by-3 bank `((1,0,theta0),(0,1,theta1))`, initially theta=(1,0). Its sites consume `(q,q,0)` and `(u,u,0)`. The fixed sparse D arithmetic reads only the first two columns; A at e3 uses the full ordered graph and returns theta. The new descriptor, all four state/input cases, fixed identity columns, Boolean closure and one-publication protocol are explicitly checked. A4's earlier pure layout did not itself grant this new live authority.

Pure structural validation can read every parameter. Read exclusion protects the D arithmetic after admitted-bank validation, not the complete Python memory trace, branches or timing. Neither fixture has an A-to-D feedback channel through the API.

## What has been proved

The full statements and proofs are [T1-T6](P2_B1_Theorems.md); the following is a scope summary, not a substitute for their hypotheses.

1. **Exact candidate projection.** For the symmetric complementary projector P, `Pi_alg(G)=GP` is linear, idempotent, self-adjoint and nonexpansive in Frobenius norm. It uniquely minimizes the distance to G among exact annihilators of V. This proves the ideal geometric restriction, not finite execution safety.
2. **Nullspace and low-rank coverage.** If N is a full-column-rank basis of V-perp, every annihilator has a unique form `Z N^T`, with equal ranks. Factorizations `A B^T N^T` and the implemented `L R P` represent every safe exact update of rank at most k, subject to the shape bound `min(k,n,d-r)`. A nonorthonormal N changes the coordinate optimization metric: ordinary Z-SGD induces `-eta*g*N*N^T`, not generally the orthogonal projected gradient.
3. **Optimizer closure.** Scalar exact SGD, exact linear combinations of safe directions and common-scalar clipping preserve the annihilator. With an already projected gradient and a nonzero old-state coefficient, the old momentum must also be safe for the same space. Generic coordinate preconditioning, element clipping and decay do not preserve it. The final restriction must follow all potentially direction-changing transformations.
4. **Endpoint distinction.** Even after exact final projection, rounding `W+D` introduces S, so `Delta_eff=D+S`. A safe D does not make S safe. ALG and BIT remain different conditions on the actual stored endpoint; neither generally implies the other.
5. **Combined transaction.** Under the trusted serial contract, all potentially rejecting work precedes one immutable publication. A failed request leaves weights, q, ticks, version, moments and optimizer step unchanged. A successful optimizer update publishes its endpoint and staged optimizer state together. Complete local BIT evidence and the inherited A3 premises lift protection to every finite supported event sequence.
6. **Structural response.** The reserved-column family is exact-safe and BIT-safe under its stated graph. It has two independent editable coefficients and individual update rank at most one. The global geometric annihilator has dimension four, so this structural restriction sacrifices two algebraic degrees of freedom. The accepted change theta=(1,0) to (0,2) changes legal A output while preserving D.

A rank-k increment generator does not keep the sum of many increments rank k. A persistent rank-k adapter relative to a fixed base can have a successive difference of rank up to 2k. These are separate exact constraints, and neither automatically bounds the rank of quantized endpoint differences. The API reports ideal and effective ranks separately; it does not silently enforce a requested finite-endpoint rank cap.

A4's target condition is retained: a prescribed exact response R on target columns X must satisfy `X alpha in V => R alpha=0`. Only after compatibility is established is the minimum implementing rank `rank(R)`. Projection, parameter rank, stored endpoint feasibility and actual target response remain distinct capacities.

## Executed update order and refusal semantics

The frozen [interface](B1_Interface.md) specifies this order:

`request -> optional gradient-only diagnostic projection -> moments -> parameter step -> decoupled decay -> increment clipping -> final projection/mask -> exact endpoint sum -> target rounding -> endpoint certification -> combined publication`.

The gradient-only and unconstrained optimizer routes are isolated offline comparisons. They are not accepted live optimizer modes. The live projected route uses the complete final increment. AI requests can propose arbitrary exact directions, including an unrestricted direction under an explicit BIT-only claim, but still require a valid endpoint certificate before publication.

SGD and EMA momentum use exact rational proposal arithmetic. AdamW uses a stated finite Python binary64 sequence for moments, bias correction, power, square root, division and step construction; its resulting floats are then decoded exactly. Its decay, projection and endpoint sum are separately specified rational operations. Host `pow`/`math.sqrt` are not certified as universally correctly rounded or cross-platform reproducible. The optimizer is a proposal generator, so this limitation does not replace or weaken the final protected-execution check.

The default claim is `ALG_AND_BIT`; explicit `BIT` is a different supported choice. The former checks actual `W'-W` on the complete global generating matrix as well as the fixed raw-domain execution. The latter must not inherit algebraic rank guarantees it has not established. No rejected joint claim is silently retried under a weaker claim.

A prepared candidate binds the full old combined snapshot, optimizer configuration/state, request, actual endpoints, model/domain/invariant, graph/policy, schedule and implementation identities. Commit reconstructs the expected candidate and evidence. A D tick after preparation makes the B1 record stale, even when an underlying A3 local certificate alone would still cover the new state. This prevents an optimizer publication from overwriting later D state.

On rejection, optimizer time and moments do not advance. Repeated deterministic attempts can therefore repeat a refusal; the API gives safety, not guaranteed progress. A later legal D tick is a separate event and may advance q/ticks normally. Accepted no-op weight updates can advance the optimizer and version, so accepted commits are not counted as nonzero learning steps indiscriminately.

Canonical records and hashes establish semantic consistency and identity, not cryptographic authentication of original intent. An inconsistent or stale record is refused. A coherent newly issued safe request from a trusted caller may be accepted as a different request. Arbitrary private-memory mutation, concurrent races and process failure are outside the one-publication theorem.

## Concrete failure mechanisms retained

The [counterexample catalogue](P2_B1_Counterexamples.md) records proofs and executed probes separately.

- On the protected line through `(1,1,1)`, projecting raw gradient `(3,0,0)` gives `(2,-1,-1)`. With zero moments and epsilon one, ideal Adam normalization produces `(2/3,-1/2,-1/2)`, whose sum is -1/3. Actual finite host proposal words are recorded rather than assumed equal to those fractions. This is a failure before endpoint rounding.
- Off-space momentum contributes an unsafe component even when the new gradient is projected. Decay changes a nonzero protected W response; element clipping can change the zero-sum relation. Exact common-scalar clipping preserves that relation, without certifying a host-estimated norm threshold.
- Quantizing the exact projector for `V=span(1,3)` yields nonzero decoded residuals in both formats. Its BF16 residual is `(-1/256,-1/2048)`; its FP32 residual is `(-1/16777216,-1/134217728)`. An approximate projector is not an authority.
- The `(2^p,0)` endpoint-rounding example, rounded-thirds/subnormal failure, full-rank BIT/non-ALG edit and rank-two BIT edit with complement dimension one remain regression cases. So do saturated storage, incompatible targets, target-silent edits, merged shared-site exhaustion and sample-only underprotection.
- Stale versions/snapshots, omitted coverage, altered graph/policy/schedule, inconsistent certificate fields and malformed requests are refused with full-bank equality checks. A successful projection or A4 enumeration does not bypass these checks.

## Actual small optimization results

The complete 24-run comparison is in [Optimization Experiment](P2_B1_Optimization_Experiment.md) and [training_results.json](training_results.json). Both formats start with actual A output `(1,0)` and target `(0,2)`. Loss is the exact rational squared loss of the **decoded executed A output**, initially 5/2. The gradient is from the continuous linear extension; it is not asserted to be a derivative of the quantizer.

Each optimizer runs eight attempts. SGD uses rate one. Momentum uses rate 1/2 and EMA coefficient 1/2. AdamW uses rate 1/4, beta1=1/2, beta2=3/4, epsilon=1/1024 and decoupled decay 1/8. Both safe routes select ALG_AND_BIT.

| Format | Optimizer | Dense final projection: accepts/refusals | Dense final loss, approximately | Structural accepts/refusals | Structural final loss, approximately |
|---|---|---:|---:|---:|---:|
| BF16 | SGD | 8 / 0 | 0.0000381469727 | 8 / 0 | 0 |
| FP32 | SGD | 8 / 0 | 0.0000381469727 | 8 / 0 | 0 |
| BF16 | Momentum | 2 / 6 | 1.23596191 | 8 / 0 | 0.00970506668 |
| FP32 | Momentum | 8 / 0 | 0.00571515002 | 8 / 0 | 0.00954279734 |
| BF16 | AdamW | 1 / 7 | 2.09790039 | 8 / 0 | 0.09322837 |
| FP32 | AdamW | 0 / 8 | 2.5 | 8 / 0 | 0.0932230736 |

Dense SGD's exact final output is `(1/256,255/128)` and loss `5/131072`. The eight-step dyadic construction is storable in both formats and accepted each time. Structural SGD reaches `(0,2)` at the first step; later accepted zero-gradient updates are not new nonzero responses. Different parameterizations and D graphs make this a feasibility comparison, not a speed or optimization-performance ranking.

The offline unconstrained SGD achieves zero A loss but loses D equality. Gradient-only SGD preserves D in this exact fixture; a counterexample does not imply that every such step must fail. Gradient-only AdamW loses D equality in both tested formats. Gradient-only momentum loses D equality in this BF16 trajectory but preserves it over the eight tested FP32 steps. Unsafe offline D feedback stops once its outputs leave the declared Boolean domain; A optimization can continue as a diagnostic without reclassifying that illegal D state as reachable.

There are **75 accepted safe commits**, including **61 nonzero stored changes**, **21 refused safe attempts**, and **96 offline applications** across 192 attempts. All 96 paired safe feedback ticks match the unchanged reference peer. Crucially, **all 21 rejected candidates pass the registered-domain BIT diagnostic** but violate the additionally selected exact ALG requirement after endpoint rounding; their effective ranks are two. These are correct refusals under the chosen stronger contract, not observed D corruption. Dense FP32 AdamW's frozen result therefore does not establish impossibility of BIT-safe AdamW learning. No weaker fallback was substituted.

## Verification, costs and evidence classes

The component [constraint_results.json](constraint_results.json) records **2,400 checks** with seed 20261114: 324 exhaustive small projection pairs, 64 seeded factor cases and four named cases, optimizer closure probes, both-format numerical boundaries and transaction attacks. It records **40 expected refusals**: eight numerical/domain cases and 32 transaction cases. The initial verifier development corrected an assumed prior API return shape; it did not discover or overwrite a predecessor defect.

The optimization component records **1,013 checks**, 24 runs and 192 attempts, with 1,536 complete local state/input-pair diagnostics over proposed and actual endpoints. These local enumerations are distinct from the sampled feedback sequence and from the arbitrary-finite-time proof. Expected refusals and zero optimizer progress are recorded as outcomes, not suppressed failures.

The independent verifier passed **512 exact instances**, each checked for projection characterization, nullspace rank and low-rank restriction; these are not 1,536 different instances. It independently checked **144 ordered optimizer proposals**, replayed all **192** recorded attempts and **1,536** D contexts, and performed **58** separate full-snapshot refusal probes plus 22 additional complete-domain context checks. It confirms all 21 BIT-preserving but ALG-failing training refusals. Its root/algebra seed is 20261114; its optimizer substream is explicitly 20261115. Direct constraints, determinant/minor ranks and separate exact-word RNE/square-root references replace the main assertion logic. Selected dyadic powers have exact values; no arbitrary host-library power certification is inferred.

| Recorded execution | Status | Observed elapsed seconds |
|---|---|---:|
| Aggregate two-section main run | Passed | 8.695691488 |
| Independent verification | Passed | 2.974865151 |
| Aggregate repetition from `/tmp` | Passed | 8.822424968 |
| Independent repetition from `/tmp` | Passed | 2.820407227 |

The primary/reproduction pairs match in all scientific results, counts, metadata and source hashes after excluding only timestamps and timing fields. Both standalone component records also match the aggregate sections under that rule. The main entry point refuses `-O` and `-OO` before attempting a section; the expected refusal checks preserve the primary evidence. [driver_checks.json](driver_checks.json) records these facts and the exact comparison omissions. This is reproduction from another working directory in the same environment, not a clean-room installation or cross-hardware validation. Python is 3.12.14 and NumPy is 2.3.5 on the recorded Linux x86-64 environment. These timings are cost observations, not benchmark claims.

Universal T1-T6 remain handwritten proofs. No SMT or Lean/Coq checking is claimed. The independent verifier and producer records retain their different finite scopes; counts are not pooled into a universal proof score. [final_integrity.json](final_integrity.json) binds the delivered files and verifies the **413** prior-file contents and nonexcluded inventory against the initial read-only baseline.

This reference pays for exact rational projection and explicit complete-domain rechecking. Projection costs depend on matrix dimensions and rational coefficient bit growth; exhaustive domain costs scale with the number of declared local contexts and graph operations. Candidate records, repeated recomputation and arbitrary-precision optimizer state also cost time and memory. Counter exhaustion and numerical refusal can stop progress. No large-model scalability or performance advantage follows from these small runs.

## Remaining limits and next stage

The established mechanism is conditional on a trusted serial API and supported complete domains. It is not a general invariant prover, closest-safe-endpoint optimizer, authenticated distributed update protocol or general concurrent runtime. Exact clipping/decay conventions and host proposal arithmetic are explicitly chosen reference semantics, not a claim of identity with every framework's SGD/AdamW implementation.

BF16 execution is software RNE. FP32 evidence concerns the actually audited local scalar CPU path. GPU, native BF16, arbitrary fusion/reassociation/compiler optimization, process-failure atomicity, full host-stack machine proof, arbitrary A-to-D feedback and useful long-term learning remain uncertified. Stronger guarantees would require separate proofs and evidence rather than inherited labels.

[P2_B2_Handoff.md](P2_B2_Handoff.md) saves the next-stage single-layer perturbation-bound obligations: actual endpoints, explicit error decomposition and norm/domain choices, underflow/overflow and graph policies, and a clear distinction between bounded difference and bitwise equality. B1 stops for coordinator review; no B2 work was performed.
