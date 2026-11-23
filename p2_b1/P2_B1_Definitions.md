# P2-B1 — Constrained proposals and complete update transactions

This stage separates exact candidate restriction, host optimizer arithmetic, target-format endpoint formation, and executable acceptance/publication. The [mathematical checkpoint](P2_B1_Mathematical_Checkpoint.md) was saved before implementation. A1–A4 definitions, proofs and evidence remain read-only dependencies.

## 1. Protected space and shapes

Let K be Q or R. A physical shared weight matrix has n output rows and d input columns. A globally justified protected activation set contains every relevant call input, over all admitted initial states, external histories, states and times, in common physical coordinates. Let V_exact be its K-linear span. Choose a working protected subspace V with a proof that V_exact is contained in V; V may equal V_exact or be an explicitly conservative containing space. Write r=dim V and c=d-r, and let H be a generator matrix for this V. All projection, nullspace and rank statements below use this same working space. A conservative choice can reject updates that are safe on V_exact. A sample-only H without global containment proof cannot support a global protection claim.

The current protected program, graph, physical sharing, parameter orientation, input preparation, legal-domain/invariant specification, arithmetic policy and trusted logical schedule are fixed during a supported transaction. If they change, previous optimizer-space or execution certificates do not silently transfer. Every editable-parameter read that can influence D must be covered by the declared calls/effects.

Let P=P_perp be the exact orthogonal projector onto V-perp. For rational H it is rational and acts on Q^d as well as its real extension. Orthogonal/Frobenius statements over Q use the usual Euclidean norm through Q subset R; the rational minimizer remains admissible when the inputs are rational. Let N be a full-column-rank d-by-c basis of ker(H^T)=V-perp. It need not be orthonormal. For c=0, N has zero columns and P=0.

Bias is fixed in the executable examples. Joint bias edits require a declared augmented block and the span of actual lifted activations, with independent site biases represented separately. This does not change bias placement in the floating graph.

## 2. Mathematical candidate restriction

The exact annihilator space is

\[
\mathcal U(V)=\{\Delta\in K^{n\times d}:\Delta V=0\}.
\]

Define the algebraic projection on an n-by-d candidate G by

\[
\Pi_{\rm alg}(G)=GP.
\]

This is an orthogonal projection in matrix Frobenius geometry. It is not a projection onto a finite set of stored endpoints or onto a rounded observational-equivalence class.

Nullspace coordinates use Z in K^(n by c) and Delta=Z N^T. Low-rank coordinates may use A in K^(n by k), B in K^(c by k), giving Delta=A B^T N^T. Another implemented representation is L R P with L of shape n-by-k and R of shape k-by-d. Both are exact-safe low-rank constructions with their stated rank bounds; finite rounding of their products/endpoints is a separate issue.

A per-step rank cap, a rank cap on the accumulated change from an initial bank, and a persistent low-rank adapter relative to a fixed base are distinct contracts. Repeated rank-k increments can accumulate higher rank. A persistent rank-k adapter constrains each baseline residual, but replacing one such adapter by another can produce an increment of rank up to 2k. Parameter coverage also differs from optimizer geometry: Euclidean gradient descent in a nonorthonormal nullspace coordinate Z does not generally equal Frobenius projected gradient descent in W.

A structural coordinate mask keeps only a declared reserved input-column set J. Such arbitrary column-supported updates annihilate V only when the protected activations have zero coordinates there. A read-exclusion graph is an additional executable sufficient condition. A4's dimension, finite-count and target-response distinctions continue to apply.

## 3. Optimizer state and proposal order

An optimizer configuration fixes its kind, scalar parameters, clipping policy, proposal arithmetic and restriction mode. The reference supports SGD, momentum and an explicitly ordered AdamW-style proposal. Its state records a step count, first-moment array m and second-moment array v. Not every optimizer-state array is itself a proposed weight update: in particular v need not annihilate V. The acceptance condition concerns the actual endpoint, while optimizer state must be bound and published consistently.

For exact closure theorems, scalar coefficients belong to K. A true Euclidean norm clip may require the real extension; the reference instead computes one common scalar from an explicitly specified binary64 norm calculation, decodes that scalar exactly to a rational, and applies it as an exact common multiplier. Its measured threshold is numerical, not a theorem about exact irrational norm clipping.

The reference operation order is:

1. Optionally project only the gradient in the diagnostic `gradient_only` mode.
2. Compute the optimizer's moments/state and parameter-step proposal.
3. Add the decoupled decay term `-learning_rate * weight_decay * W`.
4. Apply the declared increment clipping.
5. Apply the final entire-increment projection or structural mask when that route is selected.
6. Form and round the actual replacement endpoint.
7. Verify the selected endpoint claim and transaction binding before publishing anything.

The exact momentum convention is m_new=beta m+(1-beta)g, followed by the configured scalar step. SGD, this momentum recurrence, decay and coordinate clipping use rational operations in the reference. AdamW proposal calculations use separately specified finite host binary64 products/sums, bias correction, square root, denominator/division and step arithmetic; resulting floats are decoded exactly before subsequent rational operations. No host optimizer operation is labeled as BF16/FP32 protected execution or an exact Q-valued Adam recurrence.

The distinction between `gradient_only` and `projected` is semantic. The former restricts the gradient before optimizer state, adaptive preconditioning, decay and clipping. The latter restricts the complete final increment after those operations. Unconstrained and gradient-only optimizer comparisons are isolated diagnostic simulations, not automatically authorized live updates.

## 4. Storage and the selected executable claim

Fix admitted canonical finite BF16 or FP32 words, nearest rounding with ties to even, gradual underflow, explicit nonfinite rejection and canonical positive arithmetic zero. Let the old raw bank be w and the proposed stored endpoint be w'. Decode them to W and W'. The actual update is

\[
\Delta_{\rm eff}=W'-W.
\]

It is not replaced by the ideal restricted increment D. Even when D annihilates V, endpoint rounding W'=RN_F(W+D) can make Delta_eff fail that constraint. Individual entries of Delta_eff need not be target-representable as standalone words.

The two supported executable claims are distinct:

- **BIT:** complete fixed-domain protected raw outputs/effects agree under the same graph and policy, together with the supported state invariant and totality obligations.
- **ALG_AND_BIT:** BIT holds and the exact decoded Delta_eff annihilates the globally justified generator matrix.

A request cannot change its claim after an unsafe result. A BIT claim need not satisfy ALG, even at full protected rank, and an effective BIT update need not obey the algebraic rank bound. Conversely ALG alone is not a live authorization. Default selection and exact field names are fixed by the implementation/interface specification.

The dense live models reuse A3's unchanged complete-domain certificate functions for `duplicate_feedback_v1` and `split_feedback_v1`. They use pure verification, not a separate A3 live commit. The B1 owner publishes one combined bank only after that pure check and any requested exact ALG check succeed.

## 5. Pi_safe is a partial transaction

Let a complete owned snapshot be

\[
B=(w,q,t,\nu,O),
\]

where w is the raw weight bank, q the protected state, t the diagnostic tick count, nu the weight version, and O the optimizer state including step/m/v. The model/graph/policy/schedule, optimizer configuration and chosen acceptance claim are also fixed and bound. They are not caller-supplied assertions of global coverage.

An AI request supplies a candidate direction and an explicit restriction. An optimizer request supplies a gradient and a permitted restriction. Preparing a request stages the whole optimizer calculation, endpoint quantization and evidence without mutating B. A preview is explicitly uncertified.

Define Pi_safe(B,request) as a partial operation: it either produces a fully checked candidate for a specific current snapshot or refuses. It is not claimed to be linear, total, idempotent as a stateful transaction, a nearest projection, differentiable, or an optimizer convergence mechanism. Its output is an accepted stored endpoint with staged optimizer state, not an abstract nullspace vector.

The prepared record binds the complete old snapshot, including q and ticks; old/new endpoints; exact request; optimizer state/configuration; selected claim; complete domain/invariant; physical matrix/sites; graph; numerical policy; schedule; version; and trusted implementation identities. A digest identifies those data but does not prove a caller's domain or grant authority. Verification recomputes the expected staged proposal and evidence from the trusted snapshot/specification. This checks internal consistency and current-snapshot binding, not the historical origin or intent of a request. There is no secret key or original-intent registry: a trusted caller may replace a proposal with another coherent, fully valid request and recomputed record. Such a replacement is subject to the same complete safety checks and is not rejected merely because it differs from an earlier proposal.

Commit validates against the current full snapshot and prepares the receipt and replacement bank before one publication. On acceptance, weights and optimizer state are published together, version increments, and q/ticks are preserved. An AI update leaves optimizer state unchanged. On refusal at proposal, quantization, binding or certification, the entire bank stays unchanged, including moments and optimizer step. A tick after preparation invalidates a B1 prepared transaction because q/ticks changed, even though an A3 local certificate alone can cover all legal states. This stronger binding prevents a combined publication from restoring an older state snapshot.

This is a serialized trusted API contract. It excludes arbitrary private-memory/module mutation, malicious interpreters, asynchronous races, process failure and hardware faults during publication. It is not crash consistency or general concurrent atomicity. There is no publication followed by a protocol-level rejection in the proved path; all potentially refusing semantic work precedes publication.

## 6. Structural live model

The new `structural_duplicate_v1` bank is

\[
W(\theta)=\begin{pmatrix}1&0&\theta_0\\0&1&\theta_1\end{pmatrix},
\]

with theta initially (1,0), fixed zero bias and fixed first two columns. Both initial q bits are admitted and every external u is a canonical bit. Two protected sites of the same physical matrix prepare

\[
h_{\rm state}=(q,q,0),\qquad h_{\rm input}=(u,u,0).
\]

The fixed sparse D arithmetic evaluates the first two columns only and protects both complete two-coordinate outputs. Their first coordinates feed the fixed exact XOR graph, giving q_next=q XOR u from the same old snapshot. Thus every one of the four (q,u) pairs stays in the Boolean invariant. The complete protected global span is the line through (1,1,0), of rank one in width three.

Only the third column may change. The geometric annihilator dimension is 2(3-1)=4; the reserved-column update subspace has dimension two and individual rank at most one. A legal A interface includes e_3, e_1 and zero. At e_3, the A graph reads the reserved column and returns theta. There is no A-to-D state/input/scheduling channel through this API.

Pure endpoint validation may read theta. On admitted finite canonical banks it terminates, accepts and has no protected side effect. The read-exclusion claim concerns the protected D arithmetic after validation, not whole-host memory access or timing. The structural checker independently binds its new descriptor, validates immutable columns, complete state/input cases, graph/policy and publication obligations; it does not merely inherit authorization from the old A4 pure layout.

## 7. Response and learning scope

A4's target relation condition remains necessary for prescribed exact responses by updates in U(V): for target matrix X and response R, X alpha in V must imply R alpha=0. Rank budgets alone cannot remove target dependencies. If V strictly contains V_exact, these response restrictions can be stronger than the original protected-domain requirement. Storage and BIT acceptance can further change what is executable, and BIT can differ from exact linear response geometry.

The experimental objective is a fixed two-output squared loss at a declared legal A basis input. A lower observed loss is evidence for that finite objective/run only. The exact projected-gradient directional-derivative statement, where invoked, concerns a differentiable real surrogate with its true gradient; it does not equate surrogate gradients with derivatives of a finite-word execution. No universal learning benefit, convergence, long-term B4 training result or performance advantage is claimed.

## 8. Evidence boundary

Universal theorems are handwritten with explicit premises. Exact finite checks, host binary64 experiments, software BF16 execution, audited local CPU FP32 operations and independent oracles are separate evidence. GPU, native BF16, arbitrary compiler transformation, general concurrent execution and complete host-stack proof are not certified. This invocation completes only B1 and saves a B2 starting point without carrying out that stage.
