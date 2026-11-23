# P2-B1 — Candidate restriction, optimizer closure and safe publication

These proofs use [Definitions](P2_B1_Definitions.md). They are conditional mathematical arguments, not claims inferred from experimental success. Let V subset K^d be globally justified, K=Q or R, P its exact orthogonal complementary projector, and U(V) the n-by-d annihilator space.

## T1 — Exact algebraic projection in Frobenius geometry

**Statement.** Pi_alg(G)=GP is linear, idempotent and self-adjoint under the Frobenius inner product. Its range is U(V), and it is the unique nearest point to G in U(V) for the Frobenius norm. In particular,

\[
\|GP\|_F\le\|G\|_F.
\]

**Proof.** Linearity follows from matrix multiplication. Since P^2=P, (GP)P=GP. For any v in V, Pv=0, so GP annihilates V. Conversely if Delta annihilates V, decompose x=(I-P)x+Px with (I-P)x in V. Then Delta x=Delta Px for every x, hence Delta=Delta P. Therefore the range is exactly U(V).

Since P^T=P, the trace identity gives

\[
\langle GP,H\rangle_F
=\operatorname{tr}(P G^T H)
=\operatorname{tr}(G^T H P)
=\langle G,HP\rangle_F,
\]

so the map is self-adjoint. For every Delta in U(V), Delta=Delta P and Delta(I-P)=0; equivalently its row vectors lie in V-perp. The residual G(I-P) has rows in V and is orthogonal to every such Delta. Thus

\[
\|G-\Delta\|_F^2
=\|G(I-P)\|_F^2+\|GP-\Delta\|_F^2.
\]

The second term is nonnegative and vanishes exactly at Delta=GP, proving uniqueness of the nearest point. Applying the orthogonal decomposition G=GP+G(I-P) gives ||G||_F^2=||GP||_F^2+||G(I-P)||_F^2, proving nonexpansiveness at zero. The same identity applied to a difference gives ||G_1P-G_2P||_F<=||G_1-G_2||_F. ∎

For rational G,P, the unique real-space minimizer GP is rational. Thus it also minimizes over the corresponding rational annihilator, with the norm interpreted through Q subset R. At r=0, P=I and restriction does nothing; at r=d, P=0 and every exact projected proposal is zero. These are exact algebraic conclusions, not finite BIT capacity classifications.

**Optional local surrogate statement.** If a real-valued surrogate f is differentiable at W with true Frobenius gradient G, the feasible direction D=-GP has directional derivative <G,D>_F=-||GP||_F^2. Orthogonal decomposition supplies the equality. If GP is nonzero this derivative is negative; the statement alone does not establish a safe finite step, an endpoint certificate, discrete-loss improvement or convergence. The deployed finite-word function may have different differentiability properties.

## T2 — Nullspace coordinates and low-rank representation

Let N in K^(d by c) have full column rank and column space V-perp, where c=d-r.

**Statement.** Every safe exact update has a unique representation

\[
\Delta=Z N^T,\qquad Z\in K^{n\times c},
\]

and rank(Delta)=rank(Z). For c>0,

\[
Z=\Delta N(N^T N)^{-1},\qquad
P=N(N^T N)^{-1}N^T.
\]

If A is n-by-k and B is c-by-k, then Delta=A B^T N^T is safe and has rank at most min(k,n,c). Conversely every safe exact update of rank at most k admits such a representation, with zero padding if needed. The implemented factorization L R P, L n-by-k and R k-by-d, has the same upper bound and represents every safe rank-at-most-k update with suitable factors.

**Proof.** Each row of an annihilator belongs to V-perp, so it has a unique expansion in the independent columns of N. Collect those coefficient rows into Z; this proves existence and uniqueness. Multiplying Delta=Z N^T by N(N^TN)^(-1) gives the formula. The Gram matrix is invertible because N has independent columns. Since N^T maps K^d onto K^c, im(ZN^T)=im(Z), proving rank equality.

The rank of A B^T N^T is at most that of each factor, so the claimed bound follows. For a safe Delta of rank q<=k, its coefficient matrix Z has rank q. Choose a basis A_q for its column space and coefficient rows B_q^T such that Z=A_q B_q^T; append zero columns to obtain k-column factors. Then Delta=A B^T N^T. For the other representation, factor Delta=L R with q padded to k; safety gives Delta P=Delta, so L R P=Delta. The converse safety/rank bound follows by multiplication with P. When c=0, only the zero update exists and the zero-column construction denotes it without inverting an empty Gram matrix. ∎

Unless N is orthonormal, NN^T is not generally the orthogonal projector. Nullspace coordinates can parameterize safe algebra without an orthonormal basis; the Gram inverse is essential for the nearest-projection claim. These factors need not be target-storable and their rounded products/endpoints need not preserve the exact identities. A4's unrestricted dimension nc, low-rank nonlinearity, finite endpoint counts and target-response constraints are unchanged.

### T2(a): parameter coverage does not identify the optimization metric

Let a real differentiable surrogate f have gradient g at W=W_base+Z N^T. For a coordinate variation D_Z,

\[
df[D_Z]=\langle g,D_ZN^T\rangle_F
=\langle gN,D_Z\rangle_F.
\]

Thus the Euclidean coordinate gradient is grad_Z f=gN. Plain exact Z-SGD induces the weight step -eta gNN^T, which is safe but generally differs from -eta gP. To recover the Frobenius projected weight step, use the coordinate increment -eta gN(N^TN)^(-1), whose induced weight increment is exactly -eta gP. For example V=span(e_1), N=(0,2)^T and g=(0,1) give gNN^T=(0,4), while gP=(0,1). Both annihilate V, but their steps differ by a factor of four. This is a chain-rule calculation for a differentiable real surrogate, not a claim about the derivative of quantized execution or equivalent low-rank factor training. ∎

### T2(b): per-step and persistent-adapter rank caps differ

Suppose each exact increment Delta_t annihilates V and has rank at most k. Their sum still annihilates V, but after m steps its rank is only bounded in general by min(mk,n,c), not k. The rank inequality follows by repeated rank subadditivity and T1. For V=span(e_1) in K^3, the two updates diag(0,1,0) and diag(0,0,1) each have rank one, while their sum has rank two. This is an exact two-step counterexample, not an analysis of long-term training behavior.

Instead parameterize each ideal bank as W_t=W_base+A_t B_t^T N^T with baseline residual rank at most k. Then each W_t-W_base satisfies that cap, but a successive increment

\[
W_{t+1}-W_t=(A_{t+1}B_{t+1}^T-A_tB_t^T)N^T
\]

has rank at most min(2k,n,c), and can exceed k. The same diagonal rank-one residuals, now used as consecutive adapters relative to the base, have rank-two difference diag(0,-1,1). Both types of increment remain exact annihilators. Thus neither a rank-k step generator nor a rank-k persistent adapter justifies the other's rank claim. Rounding those ideal banks into stored endpoints introduces the separate effective-update and certificate obligations of T4. ∎

## T3 — Optimizer closure and precise failure conditions

### T3(a): scalar SGD and linear combinations

If D in U(V) and alpha in K, then alpha D is in U(V), by linearity. Consequently exact SGD applying a scalar step to an exact-safe gradient preserves that algebraic property. A finite sum of safe directions with scalar coefficients is safe. More generally, left multiplication by any output-coordinate matrix preserves annihilation, because (A D)v=A(Dv)=0.

These statements concern exact products and sums in K; host or target rounding is a separate perturbation. They also require the same fixed protected space. A moment safe under an old space need not be safe when the protected domain expands or changes.

### T3(b): momentum state

For the convention m_new=beta m+(1-beta)g_P with g_P in U(V),

\[
m_{\rm new}(I-P)=\beta m(I-P).
\]

This follows by right multiplication and g_P(I-P)=0. Therefore if beta is nonzero, m_new belongs to U(V) iff m does. If beta=0 the old component is discarded. If the old state starts safe and every gradient is restricted to the same U(V), induction keeps the first moment safe; a subsequent scalar step preserves it.

For unprojected gradients, the unsafe component instead equals beta m(I-P)+(1-beta)g(I-P). Cancellation can make this sum zero even if individual terms are not safe. Thus “every past term is safe” is a sufficient closure condition, not an unconditional necessary condition for every possible history. The iff above is restricted to the already-safe-gradient recurrence with nonzero beta.

A simple failure has V=span(1,1), safe g_P=(1,-1), old m=(1,0), and beta=1/2. Then m_new=(1,-1/2), whose action on (1,1) is 1/2. Projecting only the new gradient did not remove the old off-space state. Likewise m=(0,1) is safe for V_old=span(e_1) but not for V_new=span(e_2); changing the projector requires revalidation/reprojection rather than an inherited momentum claim.

### T3(c): clipping and coordinate preconditioning

An exact global-norm clip multiplies its entire argument by one scalar alpha (with the zero-input case defined). It preserves U(V). Rowwise scalar factors preserve it as a special case of left multiplication. The reference's host-estimated common scalar also preserves exact annihilation when that scalar is decoded and applied as one exact rational coefficient; this says nothing about exact satisfaction of its numerical norm threshold.

Elementwise clipping need not preserve U(V). On V=span(1,1,1), the row (2,-1,-1) is safe, but clipping each coordinate to [-1,1] produces (1,-1,-1), whose protected response is -1.

For a fixed diagonal coordinate scaling D_i in row i, universal preservation of safe rows is equivalent to D_i(V-perp) subset V-perp. Because D_i is symmetric, this is also equivalent to D_i V subset V: for v in V and z in V-perp, <D_i v,z>=<v,D_i z>, so invariance of either orthogonal subspace implies the other. Therefore nonuniform coordinate scaling can be safe for specially aligned spaces, but it has no general preservation guarantee. A particular scaled row can accidentally remain safe even when the operator fails universal preservation.

### T3(d): an exact Adam first-step counterexample

Consider ordinary bias-corrected Adam moments initialized to zero, coefficients beta_1,beta_2 in [0,1), nonzero gradient coordinates g=(2,-1,-1), and finite epsilon>=0. In exact real arithmetic the first bias-corrected moments are g and g squared, so the normalized direction is

\[
d=\left(\frac{2}{2+\epsilon},
-\frac{1}{1+\epsilon},-\frac{1}{1+\epsilon}\right).
\]

Every denominator is positive. Its response on (1,1,1) is

\[
\frac{2}{2+\epsilon}-\frac{2}{1+\epsilon}
=-\frac{2}{(2+\epsilon)(1+\epsilon)}\ne0.
\]

The original gradient has zero sum, so it is safe for V=span(1,1,1), whereas the adaptive direction is not. Multiplying by a nonzero learning rate does not remove this nonzero response. This proves lack of general closure even before floating rounding. It does not assert that every Adam update violates safety, or that every host implementation computes these ideal fractions exactly. The binary64 experiment records its actual operations separately.

The second-moment state is used to define scaling; it is not required to be an annihilator itself. A sound mechanism must constrain the final resulting update or prove the particular adaptive operator preserves the relevant space.

### T3(e): decay and operation order

A decoupled decay term D_decay=-eta lambda W annihilates V iff eta lambda Wv=0 for every v in V. If eta lambda is nonzero, this is equivalent to W in U(V). For a typical nonzero protected function Wv, decay changes it. Thus projecting only a gradient does not protect a later decay term.

If the complete final increment D includes momentum/adaptive scaling, decay and clipping, then DP always annihilates V in exact algebra by T1. Performing clipping, decay or other non-preserving transformations *after* that final projection loses the guarantee unless those transformations separately preserve U(V). Restricting the final increment changes the proposal algorithm; it is not a claim that the resulting sequence is standard unconstrained SGD/AdamW or has their convergence properties. ∎

## T4 — Final projection is not endpoint certification

Suppose D=Pi_alg(G) annihilates V and the stored endpoint is W'=RN_F(W+D) under a declared commit procedure. Define S=W'-(W+D) by exact decoding. Then

\[
\Delta_{\rm eff}=W'-W=D+S,
\qquad \Delta_{\rm eff}h=Sh\quad(h\in V).
\]

This is direct subtraction. There is no reason for S to annihilate V. For p=8 or 24, use old row W=(2^p,0), safe D=(1,-1), and h=(1,1). Endpoint rounding gives W'=(2^p,-1), effective difference (0,-1), and protected response -1. Thus even an exactly projected complete proposal can fail actual ALG and BIT checks.

For the following inherited counterexamples, eta is the format's smallest positive subnormal (2^-133 for BF16 or 2^-149 for FP32). Products and the specified sums are rounded separately with gradual underflow and canonical arithmetic zero. Conversely, a decoded effective difference can annihilate V yet change rounded execution: let s=RN_F(1/3), and let Q have diagonal 2s and off-diagonal -s. Relative to zero weights, Q is exact-null on both 1_3 and eta 1_3 because every decoded row sums to zero. Its fixed rounded execution on 1_3 returns zero. At eta 1_3 each positive product 2s eta rounds to eta, while each negative product -s eta rounds to zero; the output is eta in each row. A local basis probe therefore cannot establish complete BIT safety.

The reverse non-implication also remains: I_2 to ((1,eta),(0,1)) is BIT-equal on the full-rank finite protected domain {0,(1,1),e_1} while failing exact annihilation. I_2 to ((1,eta),(eta,1)) is BIT-equal on duplicated bits but its effective rank is two, above the algebraic complement dimension one. These are inherited conditional graph/rounding constructions, not reasons to treat all candidate updates as safe.

Therefore an ALG_AND_BIT request must check actual Delta_eff plus complete supported BIT evidence. A BIT-only request checks its distinct finite execution condition and must not report algebraic rank guarantees it has not established. Capacity or projection reports do not change the chosen claim after observing a refusal.

## T5 — Partial safe update and full optimizer rollback

**Hypotheses.** One trusted serialized owner holds a complete immutable bank B=(w,q,t,nu,O). Configuration, model/domain/invariant, graph, policy, schedule and acceptance claim are fixed and bound. A request is parsed into validated immutable data. Proposal construction and optimizer-state calculation are pure with respect to B; all host arithmetic failures, endpoint quantization, exact/executable checks and canonical record validation occur before publication. The prepared record commits to the full old snapshot, actual endpoint, staged optimizer state and trusted specification. Commit recomputes the record against the current snapshot and allocates both replacement bank and receipt before one publication. There is no unmodeled concurrent/private mutation, process failure or hardware fault in this semantic model.

**Statement.** Every protocol refusal leaves the complete bank unchanged, including weights, protected state, version, tick count, optimizer moments and optimizer step. Every accepted optimizer update publishes its endpoint and staged optimizer state together, with one version increment and unchanged q/ticks. An accepted AI update retains optimizer state. A prepared transaction cannot be replayed after a weight/version or protected snapshot change. Under a sound selected BIT certificate and the A3 invariant/interface premises, any finite accepted tick/update interleaving preserves the reference protected trace.

**Proof.** Until the final publication, every proposed value is temporary data derived from the old bank. No step assigns to B. Thus any validation, arithmetic or certificate failure before publication has no bank effect; optimizer step/moments were only staged, so they also remain unchanged. On success the replacement bank contains both the checked endpoint and exactly the staged optimizer state; assigning that one complete object publishes them jointly. Its construction explicitly copies old q/ticks and increments nu once. The AI branch copies O instead of advancing it.

If any bound snapshot component has changed, recomputation uses a different old record and cannot equal the canonical prepared record for the previous snapshot. Similarly, inconsistent alteration of a bound request, endpoint, optimizer state or execution descriptor fails canonical recomputation; caller changes cannot override the owner's trusted configuration or specification. Thus an old prepared record or an internally inconsistent alteration refuses rather than overwriting a later protected state or optimizer moment. A coherent replacement request with a newly recomputed, currently bound and semantically valid record may instead be accepted as a new proposal from the trusted caller. The protocol provides no secret key or original-intent registry and does not authenticate that a submitted request is historically identical to one previously prepared. A digest alone is not used to establish canonical equality, semantic safety or original-intent authenticity.

For protected trace equality, a successful update preserves q and all protected state and carries a valid local BIT relation on the same complete invariant envelope. A refused update preserves the old bank. At each tick, the current bank is compared to the reference by the same local equality, totality, covered-input/effect and same-snapshot premises as A3. Local relations compose transitively over any finite accepted version prefix. Induction over the finite event sequence therefore preserves protected observations and state. Optimizer state may differ from a reference run, but by hypothesis it influences D only through checked endpoint publication and is not an unmodeled D input. ∎

This is full semantic rollback, not an implementation of crash recovery or general concurrent atomicity. A certificate covering all D states does not alone permit overwriting a newer q/tick snapshot during combined publication; B1's stricter full-snapshot binding closes that separate transaction obligation. Version/step/resource limits, if imposed, cause refusal rather than an unlimited-success promise.

## T6 — Structural live family with nonzero response

Consider `structural_duplicate_v1` from the Definitions. The shared bank is W(theta)=((1,0,theta_0),(0,1,theta_1)), initially theta=(1,0). All admitted stored theta values are finite and canonical. The protected sites use (q,q,0) and (u,u,0), q,u Boolean. The fixed sparse D arithmetic reads only columns one and two and returns (q,q),(u,u). Their first coordinates feed the exact same-snapshot XOR graph.

**Statement.** Every admitted endpoint changing only theta satisfies both exact ALG and this structural BIT relation. Every protected transition is q_next=q XOR u and remains Boolean for all four state/input pairs. At legal A input e_3, the output is theta. Thus nonzero accepted endpoint edits can change A behavior while preserving D, and T5/A3 lift this local fact to any finite supported event sequence. The reserved update space has dimension two and individual rank at most one, a strict subset of the four-dimensional geometric annihilator for this rank-one protected span.

**Proof.** The protected third input coordinate is zero, so an exact update supported only in the third column annihilates every protected activation. More strongly, after total side-effect-free validation of the admitted bank, the protected sparse arithmetic never reads those mutable coefficients. Its operands remain the fixed identity columns and the same q/u words. It therefore returns identical full outputs, with exactly representable Boolean intermediates. The fixed XOR computation yields q XOR u and preserves the canonical-bit invariant. Both initial states and every legal next input are included; this establishes coverage and closure without trace sampling.

At e_3, each A output multiplies its finite theta by one and adds canonical zero; this preserves the stored value exactly and cannot overflow. Changing theta from (1,0) to (0,2) therefore changes the actual A output by (-1,2), with all words representable in both formats. The first two columns remain unchanged and D is unaffected. A third-column-only 2-by-3 update has two scalar entries and rank at most one. The protected span is generated by (1,1,0), so A4's unrestricted exact dimension is 2(3-1)=4. The mask retains two of those four abstract parameters. ∎

Any optimizer, including adaptive or coordinate-clipped proposals, can be used as a *candidate generator* for this reserved family when the entire final increment is masked to the third column and the actual endpoint passes the structural transaction. Its moments or host intermediates need not themselves have that support. This does not authorize changing immutable columns, a different graph, an unsupported descriptor or a nonfinite endpoint. Pure validation may inspect theta; whole-host instruction traces and timing are not protected by the arithmetic read-exclusion argument.

## Learning and completion boundary

These theorem families establish exact candidate geometry, identify optimizer non-closure mechanisms, and state executable acceptance/publication conditions. They do not prove universal improvement of an AI objective. A fixed small squared-loss run can demonstrate measured behavior for its actual accepted endpoints; rejection histories and unchanged optimizer state must be recorded rather than treated as successful learning steps.

All assumptions on global activation coverage, exact endpoint decoding, accepted A inputs, target-response relations, fixed numerical policy, state invariants and trusted schedule remain explicit. Native BF16, GPU, arbitrary compiler transformations, general concurrency, adversarial private runtime and full proof-assistant verification are outside this stage's evidence. B2 perturbation-bound research and later long-term training/composition stages are not completed here.
