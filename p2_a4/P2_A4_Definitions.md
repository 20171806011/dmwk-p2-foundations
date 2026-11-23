# P2-A4 — Four notions of capacity for protected weight editing

This document fixes the mathematical objects and executable premises for A4. It inherits the qualified A1 activation-space definitions, A2 endpoint/rounding distinctions, and A3 complete-domain acceptance and trace-lifting conditions. The [pre-implementation checkpoint](P2_A4_Mathematical_Checkpoint.md) preceded this stage's implementation. Proofs and experiments remain separate.

## 1. Scalar fields, shapes and actual endpoints

Let K be Q or R. One physical shared matrix has n output rows and d input columns, with n,d>=1. The requested square case sets n=d. The symbol k denotes a nonnegative rank budget on an update generator; it is never the output dimension.

An admitted BF16/FP32 raw word decodes by nu_F to a dyadic rational. Canonical positive zero is required; NaN, infinities and negative-zero stored proposals are excluded by this stage's policy. Finite normal and subnormal words are admitted, with gradual underflow. The abstract parameter space is K^(n by d), but the admitted finite word set is not a K-vector space.

Fix an old stored raw bank w and a replacement w'. Their decoded matrices are W and W'. The effective update is

\[
\Delta_{\rm eff}=\nu_F(w')-\nu_F(w)=W'-W.
\]

This is exact decoded subtraction, not a target-format subtraction instruction. Its entries need not themselves be representable as standalone target-format words. An ideal proposed increment, its separately stored version, and the actual replacement bank are distinct objects.

Bias is fixed unless explicitly included in a jointly edited affine block. For joint bias edits use [W b] and the span of actual augmented activations (h,1), or site-tagged activations (h,e_c) for independently shared site biases. Augmentation occurs before selecting a basis. An arbitrary ordinary input-span basis cannot replace the actual augmented span. Algebraic homogenization does not reorder the implemented bias-first reduction.

## 2. Protected domain, sharing and provenance

Fix D, its graph and parameter orientation, every protected call site of the same physical matrix, legal initial states, all legal external input histories, input preparation, storage policy and deterministic logical schedule. All call operands are expressed in common physical input-column coordinates after any declared gather or permutation. A differently oriented/transposed use needs additional joint constraints; equality of coefficient values in distinct storage does not create sharing.

Let A_D,c be the decoded activation set at site c over every legal finite prefix, and define

\[
\mathcal A_D=\bigcup_c\mathcal A_{D,c},\quad
V=\operatorname{span}_K\mathcal A_D,\quad r=\dim_K V,\quad c=d-r.
\]

Here c in the final expression is the complement dimension; site indices are written with subscripts elsewhere. Although each fixed-format raw activation set is finite, it is not in general closed under real addition or scaling. The span is an abstract algebraic object. Rational and real ranks agree for rational generators, but the two scalar spans are different sets.

A supplied rational generator matrix H is labeled as one of:

- **Exact global:** col_K(H)=V, with a proved complete domain or reachability argument.
- **Proved containing:** V is contained in col_K(H), so protection is conservative.
- **Samples only:** only a lower inclusion col_K(H) subset V is established. Deficient sampled rank is not a protection certificate.

Every matrix-wide constraint uses the global union of shared sites. Adding a protected site or task changes capacity monotonically only when it actually enlarges the protected space/domain while old bank, graph, policy, masks, endpoint alphabet and other admissibility conditions stay fixed. Changing a task name while also changing its preparation or old bank is not the same monotonicity experiment.

## 3. Capacity I: abstract exact algebraic freedom

Define the annihilator space

\[
\mathcal U(V)=\{\Delta\in K^{n\times d}:\Delta v=0\ \forall v\in V\}.
\]

Its vector-space dimension is the number of independent scalar parameters in exact linear maps annihilating V. It is distinct from the rank of one update matrix. The low-rank family

\[
\mathcal U_{\le k}(V)=\{\Delta\in\mathcal U(V):\operatorname{rank}\Delta\le k\}
\]

is generally not a vector space: sums can have larger rank. The unrestricted dimension formula must not be assigned to this constrained set as a linear dimension.

Over R with Euclidean inner product, or for the corresponding rational projector, A2 gives P_perp, the exact projection onto V-perp. Updates of the form G P_perp belong to U(V). A rank cap rank(G)<=k induces a rank cap on the effective algebraic update. For a *fixed* candidate G, its orientation relative to V-perp matters: its rank alone need not predict the rank of G P_perp.

All abstract attainability results in U(V) concern K-linear maps. They do not by themselves produce a replacement bank that is finite-format representable at a specified old W, satisfies masks, or preserves a rounded execution.

## 4. Capacity II: stored endpoint feasibility

Let F_F be the finite set of admitted canonical raw words and N_F its cardinality. For BF16/FP32 with exponent width eight and significand precision p=8/24,

\[
N_F=2\cdot255\cdot2^{p-1}-1.
\]

This counts both signs of finite values and removes the duplicate negative-zero word. It is 65,279 for BF16 and 4,278,190,079 for FP32.

Fix a declared endpoint family E(w). It may be all admitted n-by-d banks, a product of per-coordinate alphabets, a mask keeping some entries equal to w, or another explicitly stated finite subset. Membership must be decidable for any executed finite enumeration. Unless stated otherwise, w belongs to E(w). Choosing a tiny alphabet defines a restricted experiment, not the entire format's endpoint space.

Define

\[
\mathcal E_{\rm ALG}(w,V)=\{w'\in\mathcal E(w):
(\nu_F(w')-W)V=0\}.
\]

An optional exact-rank bound or mask yields a further subset. Cardinality, the number of non-no-op endpoints, exact effective-update rank histograms, and log2 cardinality are valid discrete capacity descriptors. Log2 cardinality is a count-derived quantity, not mutual information, trainability, or a proof of learning performance. An empty feasible set has zero count and no logarithmic capacity value; the no-op makes the set nonempty only when it is admitted.

The map w' -> nu_F(w')-W is injective under canonical finite encoding at fixed w, so endpoint and effective-difference counts coincide. It does not follow that the difference entries are target-storable or that the finite set is closed under addition/scaling.

## 5. Capacity III: fixed-graph bitwise observational edits

Fix the complete protected raw context/domain Omega, including every relevant site, state/input pair, preparation and side effect, and fix graph g and numerical policy pi. Let E_D^total be the members of E(w) whose protected execution is accepted on every context in Omega. The reference old bank must also be total there.

Define

\[
\mathcal E_{\rm BIT}(w,\Omega,g,\pi)=
\{w'\in\mathcal E_D^{\rm total}:\operatorname{Obs}_{g,\pi}(w',\omega)
=\operatorname{Obs}_{g,\pi}(w,\omega)\text{ as raw words/effects for all }\omega\in\Omega\}.
\]

For stateful certificates, the invariant/closure and admitted-input obligations of A3 remain part of this definition's executable interpretation. A basis of the numeric span is not a substitute for Omega. To require both properties use E_joint=E_ALG intersection E_BIT. ALG and BIT are not generally nested: actual rounded cancellation can fail despite exact annihilation, while a small exact change can be rounded away on every legal protected input.

The A3 checker offers sound accepted subsets only for its supported finite registries and trusted runtime assumptions. Let E_cert be the endpoints for which an applicable checked certificate is issued. Within that supported contract, E_cert is contained in E_BIT; it need not represent every semantically safe endpoint of an arbitrary program. Certificate counts must identify the model/route and not masquerade as unrestricted safety counts.

All accepted edits still bind actual endpoints, complete domain/invariant, graph, policy, current version and serialized same-snapshot publication. Enumeration or an algebraic capacity report does not grant commit authority. Rejected transactions publish nothing. Same protected initial state, inputs and trusted schedule, plus coverage of all D-influencing channels, are required for the A3 all-finite-time lifting result.

## 6. Capacity IV: responses on specified A targets

For exact analysis, fix finite target columns X=[x_1 ... x_m] in K^(d by m), m>=0. These are the declared A input vectors, not assumed independent or outside V. In a finite-format executable instance each target must decode an admitted raw A input; vectors not representable by that interface belong only to an abstract algebraic extension, not to an executed learning claim. Let pi_V:K^d->K^d/V be the quotient map. In any quotient basis let Y=pi_V X, and set

\[
s=\operatorname{rank}Y=\dim((V+\operatorname{col}X)/V)
=\operatorname{rank}[H\ X]-r.
\]

Define the exact response map rho_X:U(V)->K^(n by m) by rho_X(Delta)=Delta X. Its image describes all simultaneously attainable exact response matrices on those targets. Its kernel consists of updates that are noninterfering on D and silent on every selected A target. Prescribed response matrices R must respect every target relation modulo V; arbitrary labels on dependent target columns need not be feasible.

For finite endpoints define an exact response image

\[
\rho_X(S)=\{(\nu_F(w')-W)X:w'\in S\}
\]

for any specified endpoint subset S. For executable target response, first restrict to S_A^total, the endpoints whose A executions on the declared raw target list are all accepted and finite. Then define the raw response signature

\[
\Sigma_A(w')=(\operatorname{Exec}_A(w',a_1),\ldots,
\operatorname{Exec}_A(w',a_m)),\qquad
\mathcal R_A(S)=\{\Sigma_A(w'):w'\in S_A^{\rm total}\}.
\]

The signature retains target order, output coordinates and raw encoding. Its cardinality counts distinct target behaviors, not distinct endpoints. Many endpoints can be target-silent or produce the same response. If rejection outcomes are to count as observations, that must instead be stated with an explicit failure alphabet; the finite-output bound used here does not silently include such outcomes.

If baseline w is included and A-total, a changed A behavior exists iff |R_A(S)|>=2; the number of changed signatures is |R_A(S)|-1. This does not claim that all non-no-op endpoints change a target or that the change improves a task. Fixed targets/masks/output ports are essential to interpreting any response count.

## 7. Structural reservations and layout budgets

A reserved-column set J allows changes only in those input columns. All arbitrary K-valued changes in those n|J| entries annihilate V precisely when every protected activation has zero J-coordinates. More general masks can permit correlated coordinate changes; their exact constrained dimension is a separate rank computation, not just the number of writable entries.

A fixed sparse D arithmetic graph may go further and never read reserved cells. Under identical protected inputs and state, changing those finite cells then leaves every protected arithmetic instruction operand unchanged. This is a sufficient BIT mechanism. A pure endpoint validator may still inspect every cell before execution; on admitted banks it must terminate, accept and have no protected side effects. The claim does not equate the validator's or host interpreter's full memory-access trace or timing. A dense graph evaluating zero products needs its own totality, zero-sign and arithmetic argument; absence of a numeric contribution is not identical to absence of a read dependency.

The A4 layout example uses a 2-by-3 shared bank with fixed first two columns equal to I_2 and a reserved third column. It is an explicit graph/layout budget fixture. It is not an implementation or certification of a general compiler, a complete P2-C1 compilation stage or arbitrary P2-C4 hardware.

## 8. Evidence boundary

Universal statements below are handwritten proofs with explicit hypotheses. Exact finite enumeration, seeded properties, local native FP32 observations, software BF16 execution and independent oracles are distinct evidence. Counts over a declared alphabet do not become full-format counts except where a separate counting theorem proves the result. No machine proof, GPU/native-BF16 validation, general concurrency guarantee, arbitrary compiler optimization guarantee, novelty or performance advantage is presumed.
