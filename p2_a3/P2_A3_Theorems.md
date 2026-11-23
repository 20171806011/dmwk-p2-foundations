# P2-A3 — Exact linear noninterference and conditional program lifting

All statements below use [Definitions](P2_A3_Definitions.md). They are handwritten mathematical proofs, not conclusions inferred from finite tests. The A3 reference instantiates a restricted executable model; the general hypotheses remain explicit obligations.

## T1 — Exact endpoint, generator and span equivalence

**Hypotheses.** Let K be Q or R. Let W,W' in K^(k by d), with k,d>=1, be exact decoded stored endpoints, and Delta=W'-W. Fix b in K^k. Let A subset K^d be the actual global set of protected activations over all relevant shared call sites and legal executions in common physical input coordinates. Let V=span_K(A), and let H in K^(d by m) have column space V, including m=0 when appropriate.

**Statement.** The following are equivalent:

1. W'h+b=Wh+b for every h in A.
2. Delta h=0 for every h in A.
3. Delta v=0 for every v in V.
4. Delta H=0.
5. Delta B=0 for any chosen full-column-rank basis matrix B of V, including an empty basis when V={0}.

**Proof.** For each h, subtracting the same bias gives W'h+b-(Wh+b)=(W'-W)h=Delta h. Thus (1) and (2) are equivalent. If (2) holds and v in V, the definition of span gives a finite expression v=sum_i alpha_i h_i with h_i in A. Linearity of the exact matrix map gives Delta v=sum_i alpha_i Delta h_i=0, proving (3). Conversely A is contained in V, so (3) implies (2). If (3) holds, each column of H is in V and is annihilated, which is (4). If (4) holds, write any v in V as Hc; then Delta v=(Delta H)c=0, proving (3). The same argument with B in place of H proves equivalence with (5). No linear independence of H was needed. For A empty, V={0}; all five conditions are vacuous or the identity Delta 0=0, so the argument includes the degenerate case. ∎

**Rational/real agreement.** If endpoints and H are rational, Delta H=0 is the same exact rational identity whether the matrices are viewed over Q or R. Therefore the corresponding annihilation conditions hold on both spans, although span_Q(A) and span_R(A) are different sets. Rational and real rank agree because the presence of a nonzero maximal minor is the same rational determinant test. This is not a claim that arbitrary real combinations of activations are legal finite words.

**Full-output scope.** T1 concerns equality of all k linear output coordinates. If only a fixed linear observation R is protected, apply T1 to RDelta: the correct condition is RDelta H=0. Equality after a nonlinear observation or floating graph requires its own relation and need not imply Delta H=0. If call sites use different observation maps, each site has its own R_c Delta H_c obligation. The delivered dense reference protects full outputs at both sites.

**Failure range.** T1 does not compare executions with different inputs h and h'. It does not justify replacing Delta by a proposed increment, treating finite-precision execution as a linear map, or treating a sample matrix as an exact global generator. Correctness of the input/global-domain premise is logically separate from the linear algebra.

## T2 — Sharing, conservative spaces, rank edges and affine edits

### T2(a): all shared calls

**Statement.** If V_c=span_K(A_c) for all protected sites of one physical matrix, then V=sum_c V_c. For generator matrices H_c in the same physical input frame, a concatenated matrix H=[H_1 ... H_s] generates V, and Delta H=0 iff every Delta H_c=0.

**Proof.** Every finite linear combination of activations from the union can be grouped by site, so span(union_c A_c) is contained in sum_c V_c. Conversely every finite sum of vectors from the V_c is a finite linear combination of vectors from the union. Concatenated columns generate that same sum, and matrix multiplication annihilates the concatenation exactly when it annihilates each block. Empty/unreachable sites contribute no columns. ∎

**Counterexample to a local substitution.** In K^2, A_1={e_1} and A_2={e_2} each generate rank one, but the shared global space is K^2. Delta=diag(0,1) annihilates the first site and changes the second. This failure is exact algebra, not a rounding artifact.

### T2(b): conservative and sample spaces

**Statement.** Suppose V subset U=col_K(H). Then Delta H=0 implies exact noninterference on every actual activation. It need not be necessary. If U strictly contains V and k>=1, there is an update that annihilates V but not U.

**Proof.** The T1 generator argument shows that Delta H=0 annihilates U, hence V and A. For strict containment, extend a basis v_1,...,v_r of V by a vector u in U outside V and then to a basis of K^d. Define a linear functional ell taking value zero on the V basis, value one on u, and zero on the remaining extension basis. Taking one nonzero output vector y, set Delta x=y ell(x). It annihilates V but maps u to y, proving that the conservative condition can reject a genuinely V-annihilating update. ∎

The existence statement is in the abstract space of K-linear maps. This construction is not guaranteed to equal the difference of two admitted stored endpoint matrices, obey a coefficient/mask constraint, or constitute a valid executable edit. For a particular supplied stored pair, the sufficient implication remains exact, but finite-format realizability is a separate question.

If H contains samples from A, then col(H) subset V. Annihilating col(H) alone protects only that smaller span. The local-site counterexample above also shows the possible failure on an omitted actual activation. Conversely a sample set that happens to generate V can be sufficient, but the needed equality/containment must be independently established; the word “sample” is not such a proof.

### T2(c): rank boundaries

**Statement.** Let r=dim V. The vector space of k-by-d exact linear annihilators of V has dimension k(d-r). Every member has rank at most min(k,d-r). If r=d it contains only zero. If r=0 it contains all k-by-d matrices.

**Proof.** Choose a basis of K^d whose first r vectors span V. A linear map annihilating V must send those r basis vectors to zero, and can independently send each of the remaining d-r vectors to any vector in K^k. There are k(d-r) independent scalar coordinates. Its image is generated by at most d-r such images and lies in a k-dimensional output space, proving the rank bound. The two rank-edge claims follow immediately. ∎

This restates the rectangular algebra needed to interpret exact acceptance, not an A4 exploration of maximal executable capacity. It counts a space over K, not the number of target-format endpoint pairs, allowed API edits, bitwise-safe patches or useful learning directions. A nonzero finite-domain observational equivalence may exist even when an exact linear annihilator condition fails; full algebraic rank is not a classification of every rounded program equivalence.

In particular, positive abstract dimension does not by itself guarantee that a nonzero member is realizable as W'-W for an admitted stored W' at a fixed stored W. The endpoint and executable restrictions must still be checked; the concrete witness later supplies such a pair only for its declared instance.

### T2(d): jointly edited affine parameters

**Statement.** For possibly changed b,b', define bar Delta=[Delta delta_b], bar A={(h,1):h in A}, and bar V=span_K(bar A). Exact affine equality on A is equivalent to bar Delta vanishing on bar V, and to bar Delta bar H=0 for any generators bar H of bar V.

**Proof.** For every actual h,

\[
(W'h+b')-(Wh+b)=\Delta h+\delta_b
 =[\Delta\ \delta_b]\binom{h}{1}.
\]

Apply T1's span/generator argument to the augmented linear map. If A is empty, bar A is empty and no constraint is introduced. If biases are site-specific, replace the appended one by e_c and use the block [Delta delta_b_1 ... delta_b_s]; its action at (h,e_c) is exactly Delta h+delta_b_c, so the same argument applies to the union of these augmented site inputs. ∎

**A useful distinction.** For A={h_0}, affine equality permits delta_b=-Delta h_0; requiring Delta to annihilate span(A) and independently requiring delta_b=0 is stronger than necessary. For A={0}, weight changes are unconstrained but a jointly changed bias must be zero, because the augmented activation is (0,1). For A empty, even the bias constraint is vacuous. Algebraic augmentation does not change executable bias order.

## T3 — Finite-arithmetic difference and bounded evidence

**Hypotheses.** Fix identical raw input a, decoded h, graph g and numerical policy pi. Both endpoint executions are accepted and finite, use the declared bias/order and return vectors of k raw outputs. Let e=nu_F(E_g(W,b,a))-(Wh+b) and e'=nu_F(E_g(W',b',a))-(W'h+b').

**Statement.** The exact decoded output change is

\[
\nu_F(E_g(W',b',a))-\nu_F(E_g(W,b,a))
 =\Delta_{\rm eff}h+\delta_b+e'-e.
\]

For any induced norm and certified nonnegative bounds ||e||<=epsilon and ||e'||<=epsilon',

\[
\|\nu_F(E_g(W',b',a))-\nu_F(E_g(W,b,a))\|
\le \|\Delta_{\rm eff}h+\delta_b\|+\epsilon+\epsilon'.
\]

If exact algebraic noninterference holds for h, only the first term is zero; the rounding-error difference need not be.

**Proof.** Substitute the two definitions of e,e', subtract, and use W'-W=Delta_eff and b'-b=delta_b. The triangle inequality gives the bound. ∎

**Computability for a fixed separate-RNE row.** Let s_0=b, p_j=RN(w_j h_j), s_j=RN(s_(j-1)+p_j). Define rho_j=p_j-w_jh_j and sigma_j=s_j-(s_(j-1)+p_j) using exact decoded values. Substituting and telescoping gives

\[
s_d-(b+\sum_j w_jh_j)=\sum_j(\rho_j+\sigma_j).
\]

Therefore sum_j(|rho_j|+|sigma_j|) bounds that row's execution error. The reference can calculate these rationals, including underflow cases, because all accepted finite endpoints/operands/results decode exactly. Row bounds can be combined into a conservative vector norm bound, with rational upward enclosures when a square root is needed. Nonfinite rejection is outside this finite-output identity. A relative gamma bound needs its separate rounding, dimension and underflow hypotheses; those are not silently assumed here.

**Uniformity condition.** If one proves a common legal family A_* and uniform bounds for the exact residual and both execution errors on that family, taking the supremum yields a uniform bound. Without that proof, the displayed measured certificate is only pointwise. A small uniform positive bound is not automatically an all-time raw-word guarantee. Signed zeros also require an explicit bit policy, not a real norm argument.

**Corollary (optional certified output separation).** In one fixed accepted finite output format with canonical zero, let eta be the smallest positive subnormal. If both output vectors are finite and a certified bound satisfies

\[
\|\nu_F(y')-\nu_F(y)\|_\infty\le\beta<\eta,
\]

then their raw output words agree. **Proof:** every finite decoded value in that format is an integer multiple of eta, so every nonzero coordinate difference has magnitude at least eta. The strict bound rules out such a difference. Canonical finite encoding is injective, hence equal decoded coordinates have equal raw words. ∎

This corrects an overly absolute interpretation of “positive bounds cannot certify bits.” The accepted output format, strict gap, canonical encoding and proven domain coverage are explicit premises. A pointwise bound proves only the local result at that point; a program-level consequence additionally needs uniform coverage of all relevant contexts and T4's invariant/interface premises. The delivered BOUND interface does not use this additional acceptance route; its live BIT checker directly verifies complete registered raw outputs.

### Proposition: floating basis checks do not extend by linearity

Let Q be the target-rounded matrix I-J/3 in dimension three, with diagonal RN(2/3) and off-diagonal -RN(1/3), under BF16 or FP32 nearest-even rounding. The decoded row sums are exactly zero because RN(2/3)=2RN(1/3). Thus Q annihilates span_R(1,1,1). Separate-RNE execution at (1,1,1) returns zero.

For the last claim, put s=RN(1/3). Each row contains one 2s and two -s values. In every left-to-right row order, the partial sums are among 0, s, -s, 2s and -2s, all exactly representable; multiplication by one is exact. Hence this zero result follows from the instruction graph, rather than merely from the exact row sum.

Now explicitly admit both (1,1,1) and eta(1,1,1), where eta is the format's smallest positive subnormal. Each positive diagonal product is strictly between eta/2 and 3eta/2 and rounds to eta. Each negative off-diagonal product has magnitude strictly below eta/2 and rounds to zero, with the declared canonical-zero normalization. The output is consequently (eta,eta,eta), not zero. Exact products of the decoded matrix still vanish. The second input is an explicitly legal stored vector; no closure of a finite legal set under arbitrary real scaling was assumed.

This supplies a rigorous counterexample to promoting floating equality at generators to floating equality over the protected activation set. It also supplies endpoint noninterference failure by comparing old zero weights with new Q under the same legal input set. The result is conditional on the stated format and separate-RNE graph, not a statement that every arithmetic graph behaves this way. ∎

### Proposition: an ideal null proposal can fail after commit

Take p=8 or 24, h=(1,1), W=(2^p,0), and ideal increment v=(1,-1). Exactly, vh=0. A single-final-rounding target commit gives W'=(2^p,-1), since 2^p+1 is a nearest-even tie rounded to 2^p. The actual endpoint difference is (0,-1), whose action at h is -1. Ordered execution at h gives old output 2^p and new output 2^p-1, both representable. The ideal proposal passed a null test that the actual endpoint fails. ∎

### Proposition: finite bitwise protection need not imply exact linear protection

Let eta be the smallest positive subnormal of BF16 or FP32, and use zero bias and the same separate-RNE ordered dense graph. Let

\[
W=I_2,\qquad W'=\begin{pmatrix}1&\eta\\0&1\end{pmatrix},\qquad
\mathcal A=\{(0,0),(1,1),(1,0)\}.
\]

All displayed endpoints and activations are legal finite words. At zero both outputs are canonical zero. At (1,0), both return (1,0). At (1,1), the first row for W' performs the exact products 1 and eta, then RN(1+eta)=1 because eta is strictly less than half the spacing above 1 in either format; the second output remains 1. Thus every protected raw output agrees on the **complete declared finite set** A.

However Delta_eff=((0,eta),(0,0)), and Delta_eff(1,1)^T=(eta,0)^T is nonzero. The protected span is full rank because (1,0) and (1,1) are linearly independent. At the permitted A observation e_2=(0,1), the full output changes from (0,1) to (eta,1), with eta retained by gradual underflow. This is a nonzero stored edit with finite-domain BIT equality and failed ALG equality, even for full-rank protected span. It is compatible with T2(c): that theorem forbids a nonzero exact annihilator, not a rounded observational equivalence on a finite set. ∎

Together with the previous propositions this proves that ALG and BIT are distinct, non-nested predicates in general. It does not characterize maximal finite-format capacity or complete A4.

## T4 — From local bitwise equality to protected program traces

### T4(a): one endpoint pair

**Hypotheses.** Fix a complete protected configuration space, common invariant I, legal initial set I_0 subset I, and common Legal(z,u). Fix the physical sharing, graphs, input preparations, control flow, arithmetic policy, state storage and trusted logical schedule. Assume:

1. The original program has terminating accepted transitions on every z in I and Legal(z,u), and its complete protected successor remains in I.
2. Corresponding non-patched operations and input preparations are deterministic functions of equal protected snapshot data, common input and earlier corresponding protected local results. They have identical protected effects. Any control tests, faults and state-affecting flags are covered; no A-only value or update metadata affects them outside the declared interfaces. Every D-influencing read of editable parameters is through a covered call/effect: a separate raw-weight test, direct read or uncovered transpose operation is not permitted by this premise.
3. At every patched call context reached in those corresponding legal transitions, the old and new local executions are both accepted and have identical raw protected outputs and protected effects. The coverage proof covers every site and every context reachable from I, not merely a current execution sample. It can be established by structural proof, trusted finite complete enumeration, or another separately proved method.
4. All next-state calculations read the same old snapshot and publish the complete successor with bit-preserving storage. No partial overwrite, concurrent update or changed instruction schedule invalidates the comparison.

**Statement.** Starting from the same z_0 in I_0 and following any common legal external input history and trusted schedule, old and new protected observations and configurations are raw-word equal after every finite number of completed transitions. The new execution is accepted on the same histories and remains in I.

**Proof of one transition.** Start from equal old snapshots z in I and the same admitted input u. Induct through the original transition's terminating instruction order, including input preparation and branch decisions. At a non-patched instruction, its protected operands and relevant state are equal by the induction hypothesis; premise 2 gives the same effects/results. At a patched call, earlier equality gives identical prepared raw operands and the same call context. Premise 3 supplies accepted execution and equal outputs/effects. At a control decision, the tested protected values are equal, so the same branch and subsequent instruction occur. Therefore the new execution reaches every corresponding step without a new failure and terminates on the same path. Premise 4 makes the final protected successor and observation equal to the old ones. The original successor belongs to I by premise 1, so the equal new successor does also.

**Proof over time.** At zero transitions, initialization agrees and is in I. Suppose protected configurations and observations agree through t transitions. Apply the one-transition result to the common legal next input to obtain equality and invariant membership at t+1. Mathematical induction proves the statement for every finite t. The theorem does not assert termination of an unbounded source program, eternal fault-free hardware operation, liveness or unmodeled scheduling fairness. ∎

**Why the input-domain premise is not circular.** The coverage can be established on a common syntactic/semantic envelope I before accepting the patch. Alternatively, a lockstep proof can use original execution contexts, because corresponding operands are equal before every patched call and totality/effect equality is supplied there. It is invalid merely to observe that a patch annihilates original sample activations and then assume future operands remain unchanged. The one-transition relation, legal-domain preservation and coverage argument provide the missing steps.

### T4(b): serialized sequences of accepted patches

**Additional hypotheses.** Let W_0 be the original bank. Each accepted transaction from current W_j to W_(j+1) establishes premise 3 on the same fixed common context envelope, graph/policy/site collection and invariant I. All admissibility and side-effect premises above are unchanged. The transaction itself preserves the complete protected configuration and only publishes the validated endpoint bank. The checker is tied to the current endpoint/version, and a stale or refused request publishes nothing. Serialized operations ensure the bank used by checking is the bank replaced; every tick snapshots one complete version.

**Statement.** Every finite execution with any finite interleaving of these accepted patches and ticks has the same protected trace as the original W_0 program under the same admitted initial state, inputs and logical tick schedule.

**Proof.** Local raw-output/effect equality is an equivalence relation on total local functions over the fixed common context envelope. For any finite j, transitivity of the accepted pair relations yields equality of W_j with W_0 on that envelope. Consider a finite interleaving prefix. At an update event, the protected configuration does not change; after a successful publication, the new bank remains locally equivalent to W_0 by transitivity. A refusal retains the prior bank and configuration. At a tick, use T4(a)'s one-transition proof for the currently snapshotted bank and W_0. It gives equal protected successors/observations and preserves I. Induction over the finite event prefix proves the result. Update versions may differ from the reference, but they are outside the protected configuration only under the explicit no-D-dependency premise. ∎

**Limits.** The theorem is a sufficient relational lifting rule, not a completed general P2-C composition system. It requires unchanged input/admissibility/scheduling interfaces and every relevant protected effect. If AI outputs influence D inputs or scheduling, if an omitted monitor affects later calls, if an accepted endpoint fails on another legal state, or if the graph changes under fusion, the hypotheses have not been established. Pure algebraic annihilation cannot replace premise 3, as the preceding propositions show.

If the implementation has a bounded version counter, further update attempts at exhaustion must be refused without publication. The theorem concerns any finite interleaving of **accepted** updates and admitted ticks, not arbitrarily many successful version increments. Abstract arbitrary finite tick horizons also retain all numerical/storage/scheduling and resource premises; they do not supply infinite hardware resources or certify a host instrumentation counter as a protected finite register.

## T5 — Sound finite-domain acceptance and refusal

**Hypotheses.** A trusted immutable model specification determines I, Legal, all protected sites/preparations, graph/policy and serialized transition/update semantics. A terminating checker enumerates every admitted pair in its declared finite complete domain and each corresponding protected call. It verifies both endpoint executions are accepted, every protected raw local output/effect agrees, next configurations/observations agree, and successors lie in I. It recomputes derived endpoint differences and matches the request's model/endpoints/version/schedule commitments against the live bank and trusted specification. The accepted request cannot mutate or redirect the checked data during evaluation. A separately required exact algebraic check may conservatively reject more candidates.

**Statement.** A successful check establishes the finite model's local relation and common-invariant transition obligations, so the serialized mechanism satisfies T4 under its remaining runtime premises. A failed check followed by no publication leaves the old protected configuration and bank unchanged.

**Proof.** Every member of the trusted admitted finite domain is visited by hypothesis; passing all comparisons therefore yields the universally quantified local and transition predicates on that domain. The domain's completeness/invariance proof connects it to all legal executions, rather than to just an observed sample. Binding/recomputation ensures the predicate applies to the actual old and replacement endpoints with the same graph, policy and schedule. The successful publication and serialized execution premises make those the endpoints subsequently used; T4 applies. For a failure, all computation occurs before publication, and the checker has no protected side effect, so the previous bank and protected configuration remain unchanged. ∎

This is a soundness theorem **conditional on correct complete enumeration and trusted checker semantics**, not a formal verification of Python or cryptographic authorization from a digest. Certificate field equality is necessary for binding but cannot make an arbitrary user-supplied invariant true. Unsupported domains, missing sites, sample-only provenance and changed arithmetic graphs must be refused because the stated proof method cannot establish the obligation. Runtime reentrancy, private-memory mutation and general concurrency require additional mechanisms/proofs and are not covered by a single-threaded model alone.

## Corollary — Dense nonzero executable witness

Take W_0=I_2, W_1=((0,1),(2,-1)), fixed zero bias, canonical q,u in {0,1}, and the two protected inputs (q,q),(u,u). For t in {0,1}, both matrices return (t,t) under the fixed ordered separate-RNE graph in either format. For W_1, the first row computes 0*t+1*t=t; the second computes 2*t+(-1)*t=t. Every intermediate is exactly representable in the admitted small-integer set. Arithmetic zero is canonicalized by the fixed policy.

The endpoint difference is

\[
\Delta_{\rm eff}=\begin{pmatrix}-1&1\\2&-2\end{pmatrix},
\quad \Delta_{\rm eff}(1,1)^T=0.
\]

Thus full local outputs agree for every protected call and bit. The fixed XOR graph applied to their first coordinates returns q XOR u exactly and remains Boolean; it reads the old q snapshot. Both possible initial states and all four (q,u) pairs are in the trusted finite invariant/domain. Updates preserve q and every other protected effect, so T4/T5 yield equal protected traces for every finite horizon under the specified serialized protocol.

At the legal A input e_1, W_0 e_1=(1,0) while W_1 e_1=(0,2), with exact target-format execution. The stored patch is nonzero and genuinely changes a legal A observation. The mutable matrix terms are evaluated in the protected dense calls; this extends beyond A2's read-exclusion fixture while remaining a tiny explicitly enumerated model. The observation proves existence of a functional response, not useful learning performance, convergence or capacity optimality.

If the input-site preparation is instead (u,0), then at u=1 the protected output changes from (1,0) to (0,2). This second site makes the merged input span full rank and the same patch must be refused. Its certificate cannot be transferred by renaming a domain or omitting that site. ∎

## Proof and backend boundary

The algebraic and induction arguments are independent of finite test counts. Their executable instantiation assumes the declared rounding, word preservation, graph identity and trusted runtime. Software BF16 and audited local CPU FP32 probes provide finite evidence for the performed operations only. GPU, native BF16, arbitrary BLAS/GEMM replacement, concurrent publication, arbitrary compiler optimization, hardware faults and complete proof-assistant checking are outside the demonstrated scope. A4 rank/capacity research can use these conditions as premises, but no further stage is completed here.
