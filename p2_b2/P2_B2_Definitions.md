# P2-B2 — Single-layer perturbation contracts

This stage analyzes a fixed single linear/affine call and its full output. It preserves the previous BIT and ALG_AND_BIT authorization contracts. The [checkpoint](P2_B2_Mathematical_Checkpoint.md) predates implementation. Earlier research and stored evidence are read-only dependencies.

## 1. Objects, fields and actual endpoints

Let W and W' be n-by-d matrices obtained by exact decoding of two admitted finite stored weight banks. Their actual difference is Delta=W'-W, computed mathematically over Q and embedded in R. This is not a target-format subtraction instruction and is not replaced by a proposed increment. A general affine comparison permits fixed decoded b,b' in Q^n and delta_b=b'-b. Registered executable examples fix zero bias; an extension with changed biases must bind both biases and their graph placement explicitly.

An exact call has output y(h)=Wh+b, with y'(h)-y(h)=Delta h+delta_b. Euclidean vector norm and its induced spectral matrix norm are denoted ||.||_2; infinity, one and Frobenius norms receive explicit subscripts. All geometric theorems are real-algebra statements. Rational certificates are checked exactly and interpreted through Q contained in R. Orthonormal bases may have irrational entries even when their exact subspace projector is rational. A finite raw activation set is not asserted to be a real vector space.

Affine algebra may be homogenized as `[W b](h,1)`, or with one-hot site coordinates for independent shared-site biases. That rewrite describes exact algebra only; it does not replace a bias-first floating graph by a bias-last matrix product.

## 2. Legal inputs, shared sites and reference subspace

Fix the original protected program D, legal input histories, initial-state/invariant contract, physical sharing, deterministic logical schedule and same-snapshot state updates. For each call site c of this physical matrix let A_c contain every activation at that site on every admitted original execution. The global domain is the labelled union of all A_c in the matrix's common physical input coordinates, and V_global is the real span of that union. A complete finite registry or an independently justified invariant/domain inclusion can discharge coverage. A sample, observed low rank or caller-provided coverage label cannot do so.

Let V_ref be a declared reference subspace of R^d; write V=V_ref below for brevity, with exact orthogonal projector Pi_V and orthonormal basis Q_D of d-by-r shape. This reference is not silently identified with V_global. For an activation h define

\[
a=Q_D^T h,\qquad v=Q_Da=\Pi_Vh,\qquad e=(I-\Pi_V)h.
\]

Thus h=v+e, Q_D^T e=0 and ||h||_2^2=||a||_2^2+||e||_2^2. If a proved containment A_c subset V holds at every site, e is identically zero. Otherwise any global bounds on ||a|| and ||e|| require their own complete-domain proof. A nonzero leakage allowance is a quantitative approximation contract, not the previous exact-containment premise. If V is a proved conservative containing space, the familiar overrestriction/capacity cost remains.

All numerical receipts in this stage refer to the declared original input envelope. A changed layer may change future states, activations or control flow. A bound on the original envelope alone does not prove closure of the modified program, a bound on every modified trajectory, or a time-uniform program error. Those are additional obligations rather than implied consequences of single-call analysis.

## 3. Approximate basis and certified norms

Let U be a decoded d-by-l matrix. It is not treated as orthonormal. A near-orthonormal certificate consists of rational nonnegative delta, alpha, epsilon_U, M and sigma satisfying

\[
\|U^TU-I_l\|_2\le\delta<1,\quad
\alpha^2(1-\delta)\ge1,\quad
\|\Delta U\|_2\le\epsilon_U,\quad
\|\Delta\|_2\le M,\quad
\|\Pi_U-\Pi_V\|_2\le\sigma,
\]

where Pi_U=U(U^TU)^(-1)U^T is computed in exact algebra. The empty-column case denotes Pi_U=0. For l>0 the Gram condition proves full column rank. Pi_V must come from a separately justified exact subspace, not from assuming that U fits sampled data. A rational independent generator H supplies Pi_V=H(H^TH)^(-1)H^T after redundant columns are removed exactly.

Norm upper bounds can use exact rational Frobenius sums with outward rational square roots, sqrt(||A||_1||A||_infinity), or independently checked positive-semidefinite inequalities. An ordinary floating SVD result without a certified error enclosure is not a norm certificate. A declared upper bound may be conservative; failure of delta<1 means this particular conditioning theorem is unavailable, not that a known full-rank U is necessarily unusable by another proved method.

## 4. Candidate error accounting

For one explicitly specified generator path define an ideal candidate G_*, ideal complementary projector P=I-Pi_V, represented projector P_tilde, computed optimizer candidate G_hat and generated pre-storage increment D_hat. Write

\[
C_*=G_*P,\quad
E_{repr}=G_*(\widetilde P-P),\quad
E_{opt}=(\widehat G-G_*)\widetilde P,\quad
E_{gen}=\widehat D-\widehat G\widetilde P,\quad
E_{store}=\Delta-\widehat D.
\]

These definitions fix an exact telescoping identity. They do not assert that a hypothetical ideal Adam path or its error has already been certified. Exact decoded host candidates can be used as observed G_hat; any claimed bound relative to G_* requires a specified ideal computation and proof/evidence for that difference.

Two accounting routes are separate: (i) directly bound actual Delta, which already includes all upstream errors; or (ii) bound C_* and the disjoint ledger terms. The ledger must not be added again to a bound on the same actual Delta. A factorized implementation uses a separately defined combined factor-representation term rather than adding an overlapping projector term.

## 5. Fixed floating graph and finite-word policy

The accepted target formats are canonical finite BF16 or FP32. Stored negative zero, NaN and infinity are rejected; arithmetic zero is canonicalized to +0. Rounding is nearest with ties to even, subnormals are retained, and individual products and sums are rounded separately in the target format. Let p=8 or 24, u=2^(-p), eta=2^(-133) or 2^(-149), and Fmax the largest finite magnitude in that format.

For row i, the graph is

\[
s_{i,0}=b_i,\qquad
p_{ij}=RN_F(w_{ij}h_j),\qquad
s_{i,j}=RN_F(s_{i,j-1}+p_{ij}),\quad j=1,\ldots,d.
\]

The returned output is s_{i,d}. Every operand/result must be finite; nonfinite results cause refusal and are not assigned a finite error. The bias load is exact word-preserving storage. The old and new executions have the same declared input, ordering, precision, zero policy and output ports, but are distinct executions with separate rounding residuals. FMA, reassociation, a different accumulator precision, flush-to-zero, sparse instruction changes or a compiler transformation require a new bound/certificate.

For a particular trace define exact rational local residuals

\[
\rho_{ij}=p_{ij}-w_{ij}h_j,\qquad
\tau_{ij}=s_{i,j}-(s_{i,j-1}+p_{ij}),
\]

and beta_i(h)=sum_j(|rho_ij|+|tau_ij|). This is pointwise evidence. A coordinate envelope |h_j|<=B_j may support an analytic global bound only with proven coverage and operation-range/totality induction. Both old and new range proofs are required.

## 6. Absolute, relative and mixed claims

An absolute claim bounds ||yhat'-yhat|| by B. A relative claim divides by an explicitly chosen nonzero reference norm, normally ||yhat||; a certified positive lower bound on that norm is required for a uniform numerical constant. Near cancellation and zero reference outputs invalidate an unqualified relative claim. A mixed claim has the form ||yhat'-yhat||<=rho||yhat||+tau and remains meaningful at zero because of its absolute term.

A point bound applies to that point. A maximum over a completely enumerated finite domain applies to exactly that declared domain. A box theorem applies to all admitted raw inputs in its proved envelope. Sampling has no such universal implication. Canonical finite output separation can mathematically turn a strict full-domain infinity bound below eta into output-word equality, but the B2 receipt does not automatically perform or authorize that conversion.

## 7. Read-only numerical evidence

The B2 numerical-budget receipt is a pure diagnostic for a fixed absolute budget in a declared Euclidean or infinity norm. It binds the selected norm, old/new raw endpoints, format, complete domain and coverage provenance, all shared call sites, bias, full output observation, graph, policy, and method. Methods distinguish complete point-trace enumeration from analytic box proof. Optional B1 snapshot data bind context identity, not authorization. The receipt covers the original declared call envelope and explicitly makes no candidate-feedback closure claim.

The receipt authorizes no live commit, changes no bank/state/optimizer memory, and cannot replace a B1 BIT or ALG_AND_BIT record. Inconsistent/stale bound data are refused by recomputation. A coherent new valid trusted-caller request is a new diagnostic, not evidence of original-intent authentication. Exact current endpoint decoding, trusted coverage/graph identity and complete specification validation are still premises; a digest cannot prove them.

## 8. Evidence and stage boundary

General theorems below are handwritten proofs. Exact finite enumeration, seeded properties, local CPU FP32 operations, software BF16, bounded SMT if actually run, and independent oracles have individually recorded finite scopes. None is relabelled as a full machine proof. GPU, native BF16, arbitrary optimizations, general concurrency, hardware faults, untrusted private mutation and complete host-stack proof remain outside the certified scope. B3 and later composition/long-term training work are not completed here.
