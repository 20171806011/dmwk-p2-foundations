# P2-A3 — Linear noninterference and executable acceptance contracts

This stage asks when an actual stored endpoint replacement preserves protected linear outputs, and what additional premises lift a local executable guarantee to a protected program trace. P1 and P2-A1/A2 remain read-only dependencies. The pre-implementation derivation is preserved in [Mathematical checkpoint](P2_A3_Mathematical_Checkpoint.md). Universal arguments are in [Theorems](P2_A3_Theorems.md); experiments and independent review are separate evidence.

## 1. Stored endpoints, fields and outputs

Fix a format F and its declared accepted finite raw words. The reference uses BF16 or FP32, nearest rounding with ties to even, gradual underflow, canonical positive arithmetic zero, and explicit rejection of nonfinite or invalid operands/results. The decoding map nu_F takes every admitted finite word to its exact dyadic rational value. Raw-word equality is stronger than equality of decoded values if a different interface admits both zero signs; this stage's numerical bounds alone never certify zero signs.

Let K be either Q or R. One physical shared matrix has k output rows and d input columns, with k,d>=1. Stored old/new endpoints decode to W,W' in Q^(k by d), regarded as matrices over K. Define

\[
\Delta_{\mathrm{eff}}=W'-W.
\]

This subtraction is exact algebra on decoded endpoints. It is not an additional BF16/FP32 subtraction instruction and is not replaced by a proposed ideal increment. Its entries need not themselves be individually representable in F. If an update generator computes a proposal D_hat and commit rounds W+D_hat, those are distinct objects; A3 checks the resulting endpoint W'.

For fixed bias b in Q^k, the exact linear-affine output is f_W(h)=Wh+b. If the bias may change, write b', delta_b=b'-b, and compare W'h+b' with Wh+b. The phrase **full linear output** means all k coordinates before a later activation, observation projection or state selection. For a fixed output projection R, the relevant equality is R(W'h+b')=R(Wh+b), and its annihilation condition involves R Delta_eff rather than Delta_eff. This distinction matters when a program reads only part of a matrix call.

The concrete reference protects the complete two-coordinate output at each declared protected matrix call. Its bias is fixed zero. Its subsequent state transition uses only specified output coordinates, but the certificate checks the stronger complete-output relation.

## 2. Global protected activation domain

Fix the source/control program D, graph identity, physical parameter sharing, matrix orientation and column layout, input preparation, arithmetic and storage policy, legal initial configurations, admitted external histories and trusted logical scheduler. A1 supplies the meaning of a legal finite prefix. An input record is legal only under the declared state/monitor rule, not merely because its words are finite.

For each protected call site c of the shared matrix M, let A_c^raw contain every admitted raw input vector arising at c in any permitted finite prefix and from any allowed initial configuration. All operands are represented after gathers, permutations and padding in the same physical input-column coordinates. Equal coefficients in distinct storage objects do not imply sharing. A transposed use or differently oriented parameter action needs its own joint analysis and is not silently folded into this model.

Define

\[
\mathcal A_c=\nu_F^d(\mathcal A_c^{\mathrm{raw}}),\qquad
\mathcal A=\bigcup_{c\in\mathrm{Sites}(M)}\mathcal A_c,
\qquad V_K=\operatorname{span}_K\mathcal A.
\]

The actual finite activation set is generally not closed under real addition or scaling. The abstract span is. When the words, widths and layout are fixed, the set of possible raw activation vectors is finite even if the number of time steps is unbounded; a small enumerated sample need not cover it. A global reachability computation additionally needs the A1 finite-monitor and terminating-step premises. A3 does not invent an effective global reachability algorithm for arbitrary history constraints.

A rational matrix H in Q^(d by m), m>=0, is supplied with one of three different provenance meanings:

1. **Exact global generators:** col_K(H)=V_K, supported by a global proof or complete declared finite model.
2. **Proved containing generators:** V_K is contained in U_K=col_K(H), with a specified containment proof.
3. **Samples only:** the columns were observed, but the required global upper inclusion is not proved.

Only the first two can support their corresponding global algebraic protection claims. Calling a sample list a domain, hashing it, or naming it an invariant does not prove its completeness. Every site must be included in the union; a certificate for one site is not automatically a certificate for shared storage.

The empty activation set has span {0}; it remains empty in the affine construction below. Duplicate and zero columns are permitted. An arbitrary generator H need not be a basis; an exact full-column-rank B spanning the same space gives equivalent algebraic checks. For rational matrices, rational and real ranks agree, although their spans contain different scalars.

## 3. Bias and affine activation spaces

If a shared bias can change jointly with W, define

\[
\bar W=[W\ b],\quad \bar W'=[W'\ b'],\quad
\bar\Delta=[\Delta_{\mathrm{eff}}\ \delta_b],\quad
\bar{\mathcal A}=\{(h,1):h\in\mathcal A\}.
\]

The correct protected space for that joint parameter block is span_K(bar A), a subspace of K^(d+1). It is **not** generally V_K times K. For A empty, bar A is empty and the output condition is vacuous; no fabricated constant column is inserted. For a singleton A={h_0}, the augmented space is the single line through (h_0,1), permitting cancellation of weight and bias changes at that one input.

If sites have independent editable biases b_c, either retain separate equations Delta_eff h+delta_b_c=0 for every site c and h in A_c, or use one-hot site coordinates in a joint parameter block: [W b_1 ... b_s] applied to (h,e_c). A single appended scalar would incorrectly identify independent biases. Fixed site biases cancel separately in the fixed-bias comparison.

These are exact algebraic identities. Homogenization does not authorize changing bias placement, dot-product order, FMA policy or storage layout in an executable graph.

## 4. Three distinct claims

### 4.1 ALG: exact algebraic noninterference

An ALG result proves or checks the exact decoded identity Delta_eff H=0, or the corresponding augmented identity, with explicitly stated provenance for H. With exact global generators this is equivalent to full exact output equality on every actual activation. With containing generators it is a sufficient condition. With samples alone it is only a statement about their span.

ALG is not a live bitwise-update authorization. Rounded multiplication and addition are not a K-linear map of input activations, and the actual committed endpoints may differ from the proposed update.

### 4.2 BOUND: finite-arithmetic perturbation

Let E_g(W,b,a) be execution of the fixed graph g on raw activation a under numerical policy pi; h=nu_F^d(a). For accepted finite executions define e_g(W,b,a)=nu_F(E_g(W,b,a))-(Wh+b). Then the decoded executed difference is

\[
\nu_F(E_g(W',b',a))-\nu_F(E_g(W,b,a))
=\Delta_{\mathrm{eff}}h+\delta_b+e_g(W',b',a)-e_g(W,b,a).
\]

Certified local roundoff sums or justified uniform error estimates give quantitative bounds. The reference can report exact rational per-input residuals and conservative norm bounds. A bound computed for one stored input is pointwise; it is not automatically uniform on a span, every legal trajectory or an arbitrary time horizon. A positive norm bound is not automatically a raw-word equality certificate: deriving that conclusion needs a separate output-separation and encoding argument. Arithmetic rejection is recorded as rejection, not as a finite residual.

### 4.3 BIT: fixed-graph raw-output noninterference

For every protected site and every activation context covered by the trusted complete domain, both old and new graph executions must be accepted under the same policy and return identical protected raw outputs and protected effects. If the model includes observable failures, rejection outcomes must instead be matched explicitly. The delivered model uses total accepted execution on its legal domain.

A structurally proved read-exclusion argument or complete enumeration of a trusted finite domain can establish a local BIT obligation. The A3 reference takes the finite-domain route and recomputes obligations; it does not trust a caller's claim that a few basis probes are complete. Exact algebraic equality may be an additional conservative acceptance restriction, but it is not generally necessary for observational equality of a rounded program on a finite domain.

The implemented BIT route treats the exact endpoint residual as a separate diagnostic, not as a necessary acceptance condition. The contracts are not nested: ALG can pass while BIT fails through rounding, and BIT can pass while ALG fails because a small nonzero exact change rounds away on every actually legal protected input. In particular the full-rank split-site domain {0,(1,1),(1,0)} can admit a changed stored coefficient that is invisible there but visible at an A input outside that finite set. Its real span is all of R^2; this does not contradict the zero exact-annihilator theorem.

## 5. Program-level relation and induction premises

Let z be the **complete protected configuration**: every state, monitor, control and scheduler component that can influence subsequent protected calls, admissibility or outputs must be represented. AI-only storage and version counters may be excluded only if D does not read them or depend on their timing. Protecting just one visible register is insufficient if a hidden mutable component affects the next input or branch.

Let I be a common inductive set of configurations, I_0 subset I the allowed initial set, and Legal(z,u) the unchanged admitted external input relation. The same protected initial configuration, external input sequence and trusted logical schedule are used in both compared executions. Every declared tick is a terminating fixed graph that reads one old snapshot and commits a complete successor once. Calls and inter-call input preparation are deterministic functions of the protected snapshot, the common external input and prior equal protected local results. There is no unmodeled A-to-D channel, changed side effect, hidden exception flag or mutable scratch dependency.

Every read of editable parameter storage that can influence D must occur through a covered call or an explicitly covered effect. A separate branch on the raw weight words, a direct parameter read, or a transpose use outside the certified call model defeats this interface assumption even if every listed matrix output agrees.

The old reference transition is total for every z in I and Legal(z,u), and maps back to I. A local BIT proof/check must cover every corresponding call context that can arise from this common domain. Equal local results and equal protected side effects then imply that the new transition is also total, follows the same control path, has the same complete protected successor and remains in I. This is a relational proof obligation; a patch is not allowed to declare newly failing inputs illegal after it has been tested.

For multiple committed versions W_0,W_1,..., each accepted pair must be certified on the same invariant envelope, all shared sites, fixed graph and policy. Equality of those local functions is transitive across a finite version prefix. Updates themselves preserve protected z; stale endpoints cannot replace the checked pair; rejected transactions publish nothing. This permits comparison against the original reference even when a checker validates each patch against the current bank. A certificate valid only at the current z or a sampled history lacks this premise.

An implementation may bound its version counter and refuse further updates at exhaustion. The theorem quantifies finite sequences of actually accepted transactions, not an unlimited supply of successful patches. Its arbitrary finite transition horizon is a semantic statement under sustained execution premises, not a claim of an infinite hardware clock or unlimited physical resources. A host tick counter used only for instrumentation is not an implicit finite-width D-state register.

## 6. Concrete dense shared-matrix witness

The reference starts at W_0=I_2 with fixed zero bias. Both initial state bits q in {0,1} are admitted. Every next input u is a canonical Boolean word. The same physical matrix has two protected call sites:

\[
a_{\rm state}=(q,q),\qquad a_{\rm input}=(u,u).
\]

Both complete two-coordinate call outputs are protected. The next state is the fixed P1-style Boolean XOR of the first state-site output and first input-site output, computed from the same old q. For W_0 this is q'=q XOR u and preserves the canonical-bit invariant. The common complete finite domain contains all four (q,u) pairs and both sites, not just the pairs in the current trace.

The candidate

\[
W_1=\begin{pmatrix}0&1\\2&-1\end{pmatrix}
\]

returns (t,t) on every protected (t,t), t in {0,1}, using the fixed separate-RNE dense row order. Mutable coefficients are actually read and multiplied; safety is not obtained by omitting them from the D graph. A legal A observation at e_1=(1,0) changes from (1,0) to (0,2). No A output feeds the protected inputs or scheduler. Existence of this changed output is not a claim about optimization quality, learned tasks or useful performance.

A second declared model may prepare the input site as (u,0). Its protected global span includes (1,1) and (1,0) and is full rank. The previous patch then fails the second site's full-output equality. Such a graph/domain change requires its own model identity and cannot reuse the first certificate.

## 7. Certificate identity, semantics and trust

An executable acceptance request must bind old/new raw endpoint words, fixed bias, physical matrix and site identities, actual derived Delta_eff, complete-domain/invariant evidence, graph and numerical policy, version, and scheduler/snapshot assumptions. A digest is an identity aid, not a proof of a caller-supplied domain or authority to alter state. The trusted checker must match an admitted registry/specification and recompute the required algebraic, call and transition obligations before publication.

Malformed, stale, incomplete, mismatched or unsupported requests are refused. In particular a sample-only claim, omitted call site, changed prepared-input domain, different reduction tree/FMA/fusion policy or unverifiable invariant cannot authorize a commit. Exact API shape and field names are specified in `P2_A3_Execution_Spec.md` and the implementation; the mathematical meaning here is independent of a serialization choice.

The runtime boundary is trusted serialized local execution with fixed implementation and no arbitrary mutation of private Python memory or modules. One bank is read for checking; the same expected version/endpoints must still hold at commit; a validated complete new bank is published once. Failure leaves protected state and the existing bank unchanged. This is not a general concurrent atomicity theorem, an OS isolation boundary or a proof against an adversarial interpreter.

## 8. Evidence limits

Theorems are handwritten conditional proofs. Finite exhaustive checks, fixed-seed property tests, observed native FP32 operations, software BF16 execution and independent implementations are reported separately. No finite basis test proves a universal floating statement. P1 arithmetic premises are inherited only where their admitted operands and operations apply. Native BF16, GPU, arbitrary dense-library kernels, concurrent commits, arbitrary compiler optimizations, hardware faults and complete host-stack formal verification are not certified by this stage. No P2-C or P2-A4 completion is claimed.
