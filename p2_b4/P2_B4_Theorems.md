# P2-B4 — Capacity and stability under repeated updates

These handwritten proofs use [Definitions](P2_B4_Definitions.md). Let 𝕂 be Q or R, n,d>=1, and let every increment Delta_k=W_(k+1)-W_k use exact decoded stored endpoints. Linear algebra, finite endpoint classes, numerical histories and exact deterministic transactions have separate hypotheses.

## T1 — Fixed-space closure is equivalent to safety of every prefix

Fix a globally justified subspace V and an endpoint sequence W_0,...,W_K. The following are equivalent:

1. Delta_i belongs to U(V) for every i=0,...,K-1.
2. W_j-W_0 belongs to U(V) for every prefix j=0,...,K.
3. W_j v=W_0 v for every v in V and every prefix j.

**Proof.** U(V) is a linear subspace: scalar multiples and sums of maps vanishing on V still vanish on V. The exact telescope is W_j-W_0=sum_(i<j)Delta_i. Thus 1 implies 2, including the zero prefix. Conversely Delta_i=(W_(i+1)-W_0)-(W_i-W_0), so 2 implies 1 by linearity. Subtracting the two restrictions to V proves equivalence of 2 and 3. ∎

The argument holds for every finite prefix of an unbounded mathematical sequence if all its step premises hold. It does not assume an ideal projected proposal equals the actual endpoint difference. No new independent linear constraint is consumed merely by applying another update in the same U(V).

**Final cancellation is weaker.** For scalar banks and V=𝕂, take W_0=0,W_1=1,W_2=0. The final total difference vanishes, but the first prefix changes every nonzero protected input. Thus a single final annihilation test is not sufficient for prefix protection. This example is storable in both formats; it does not authorize either live update.

This theorem is exact linear equality. It does not replace finite-graph BIT authorization, and it does not infer global activation coverage from any sample.

## T2 — Cumulative task spaces and monotone algebraic budgets

For task spaces V_0,...,V_K define C_K=sum_(i<=K)V_i with rank r_K. Then

\[
\mathcal U(C_K)=\bigcap_{i=0}^K\mathcal U(V_i),\qquad
\dim\mathcal U(C_K)=n(d-r_K),\qquad
\operatorname{rank}\Delta\le\min(n,d-r_K).
\tag{1}
\]

Under a per-update factor/generator rank cap q, the last upper bound becomes min(q,n,d-r_K). The abstract unrestricted rank bound is attainable; under freely chosen 𝕂-valued factors the capped bound is attainable as well.

**Proof.** A linear map vanishes on every V_i iff it vanishes on every finite sum of their vectors, proving the intersection identity. Extend a basis of C_K by d-r_K complementary vectors. An annihilator must map the first basis vectors to zero and may map each complement vector arbitrarily into 𝕂^n. There are n(d-r_K) independent coefficients, and at most d-r_K independent image generators, proving dimension/rank. Send any permitted number of complement vectors to independent output vectors and the rest to zero to attain the rank. A product with a rank-q factor has rank at most q; taking the constructed rank-at-most-q annihilator as its own projected generator attains that bound. ∎

Since C_K is nested, the update spaces are nested in the opposite direction. Adding delta_r independent protected directions removes exactly n delta_r unrestricted scalar degrees of freedom. New task names or repeated directions cost no additional dimension. The unrestricted exact space is zero iff r_K=d; extra rank, storage or API restrictions can exhaust a constrained family earlier.

For fixed target matrix X, the response-image spaces {Delta X:Delta in U(C_K)} are also nested, because their domain spaces are nested. A sample span S contained in the true global space gives an optimistic capacity count n(d-dim S), not a guarantee for its omitted activations. A proved conservative containing space gives a conservative update space. These statements must be re-justified if the true legal activation domain changes with the history.

**Moving spaces are different.** In 𝕂^2 with n=1, choose current spaces span(e_1), 𝕂^2, span(e_2). Their available dimensions are 1,0,1: no monotone decrease follows without nesting. For historical failure, start at W_0=(0,0), admit V_0=span(e_1), and use Delta_0=(0,1). Then switch protection to V_1=span(e_2) and use Delta_1=(1,0). Each increment annihilates its current space, but the second changes the original e_1 response from 0 to 1. Retaining only the current task is not cumulative protection.

## T3 — Compatible task anchors and nonretroactive admission

Suppose each task specifies a linear map L_i:V_i->𝕂^n. A matrix W_* satisfying W_*|V_i=L_i for every task exists iff

\[
\sum_i v_i=0,\ v_i\in V_i
\quad\Longrightarrow\quad
\sum_i L_i(v_i)=0
\tag{2}
\]

for every finite relation across the task spaces. When a solution exists, all solutions are exactly W_*+U(C_K), hence have affine dimension n(d-r_K).

**Proof.** Necessity follows by applying W_* to the zero sum. For sufficiency define L on C_K by L(sum_i v_i)=sum_i L_i(v_i). Two decompositions differ by a relation in (2), so this value is independent of the decomposition. Linearity follows from linearity of the task maps. Extend a basis of C_K to 𝕂^d and choose arbitrary images on the added basis vectors. The resulting linear map W_* has all required restrictions. The difference between any two solutions vanishes on C_K, and adding any annihilator preserves the restrictions. This proves the solution-set description and its dimension by T2. ∎

In finite generator form, concatenate task matrices H_i and target columns Y_i. Feasibility is equivalent to ker([H_0 ... H_K]) being contained in ker([Y_0 ... Y_K]); this also enforces each task's own internal linear relations. The preceding proof constructs an exact rational witness when the supplied data are rational.

Pairwise intersections alone are insufficient. Let V_1=span(e_1), V_2=span(e_2), V_3=span(e_1+e_2), with scalar anchors L_1(e_1)=0, L_2(e_2)=0 and L_3(e_1+e_2)=1. Pairwise intersections are zero, so pairwise overlap checks pass. The three-way relation e_1+e_2-(e_1+e_2)=0 violates (2), and no common bank exists.

### T3(a): admission and repair

Let W already satisfy old task anchors on C_old, and admit a new task L_new on V_new. An exact repair Delta with Delta C_old=0 and (W+Delta)|V_new=L_new exists iff

\[
L_{new}(v)=Wv\quad\text{for every }v\in C_{old}\cap V_{new}.
\tag{3}
\]

**Proof.** Necessity follows because Delta vanishes on the intersection. Conversely define Delta(v_old+v_new)=L_new(v_new)-Wv_new. If the same vector has two decompositions, their new components differ by a vector in the intersection, where the right side vanishes by (3). Hence the map is well defined and linear on C_old+V_new. Extend it to 𝕂^d. It has the required restrictions. ∎

This is exact-algebra feasibility only; rank caps, representability and fixed-graph safety can still prevent a permitted repair. If the new anchor is defined as current behavior W|V_new, (3) holds automatically, but that choice may differ from an externally requested task target.

If task i is satisfied at admission W_(a_i), and every later increment annihilates its space, T1 applied from that admission gives W_k|V_i=L_i for all k>=a_i. No such conclusion follows for k<a_i. Shrinking the future update space cannot retroactively change earlier outputs or repair an already unsatisfied anchor. Exact linear task anchors also do not by themselves specify a nonlinear network task or a protected program trace.

## T4 — Response feasibility and per-step versus cumulative rank

Fix V of rank r, c=d-r, and target inputs X in 𝕂^(d by m). Let pi:𝕂^d->𝕂^d/V be the quotient map, Y=pi X, and s=rank Y=rank([H X])-r. Then the response map Delta->Delta X on U(V) has image dimension ns and kernel dimension n(c-s). A prescribed R is feasible iff

\[
X\alpha\in V\Longrightarrow R\alpha=0,
\quad\text{equivalently }\ker Y\subseteq\ker R.
\tag{4}
\]

When feasible, the minimum rank of an implementing Delta is rank R. A rank-q per-update cap adds precisely rank R<=q to this algebraic feasibility condition.

**Proof.** Every annihilator factors uniquely as Delta=L pi. Its response is LY, determined by an arbitrary linear map on the s-dimensional image of Y, giving ns degrees of response freedom. Rank-nullity gives the kernel dimension. If R=LY, every relation Y alpha=0 forces R alpha=0. Conversely (4) makes L_0(Y alpha)=R alpha well defined on im Y. Extend L_0 by zero on a complement. Its image is exactly im R, so the resulting Delta has rank R. Every implementing Delta has rank at least rank(Delta X)=rank R. This proves the rank-minimal construction and the capped criterion. ∎

Thus nonzero response on some target exists iff s>0 (and q>=1 if capped). A nonzero safe but target-silent update exists iff c>s (and q>=1 if capped). Nonzero output response is not a theorem about learning-task benefit. Increasing cumulative V can reduce s or eliminate all target response even before every abstract update direction disappears.

### T4(a): accumulating rank-one or rank-q steps

For K increments in a fixed U(V), each of rank at most q,

\[
\operatorname{rank}(W_K-W_0)
\le\min(Kq,n,c).
\tag{5}
\]

Every value up to this upper bound, including the upper bound itself, is attainable in unconstrained exact algebra. It is not generally bounded by q.

**Proof.** Rank subadditivity bounds the sum by Kq; its image dimension is at most n and the sum still annihilates V, so T2 bounds it by c. To attain r_*=min(Kq,n,c), select r_* complement directions and independent output vectors. Partition those directions into at most K blocks of size at most q. Let each increment map its block to the corresponding output vectors and vanish elsewhere. Each rank is at most q and the cumulative rank is r_*. Empty blocks are zero; K=0 or q=0 gives zero. ∎

For example with V=span(e_1) in 𝕂^3, diag(0,1,0) followed by diag(0,0,1) gives two safe rank-one increments with rank-two sum. A persistent rank-q adapter W_k=W_base+R_k instead constrains each baseline residual R_k; successive differences R_(k+1)-R_k can have rank up to min(2q,n,c). Relative to an initial nonzero adapter R_0, the cumulative difference R_K-R_0 can also reach that 2q bound; if R_0=0 it is at most q. These contracts must not be conflated. Rounded endpoints remain separately checked.

## T5 — Fixed feasible classes do not shrink merely with update count

Fix an absolute finite endpoint universe E, a protection space V and canonical decoding. If W_k|V=W_0|V, then

\[
E_{ALG}(W_k,V)=E_{ALG}(W_0,V).
\tag{6}
\]

**Proof.** An endpoint Z is in the left set iff Z|V=W_k|V. Substitute the common anchor W_k|V=W_0|V to obtain exactly the right membership condition, with the same universe E. ∎

Fix also one complete raw context/effect domain Omega, physical graph, numerical policy and observation. Restrict to endpoints total on Omega. Equality of their full protected outputs/effects on Omega is an equivalence relation. Hence every accepted BIT chain remains in one unchanged absolute BIT class. An ALG_AND_BIT chain remains in the same intersection of its two classes. The absolute A-response image on any fixed target set and fixed A graph is consequently unchanged along such a chain, because its underlying feasible endpoint set is unchanged. For potentially failing A executions, restrict to the fixed A-total subset or explicitly include a failure symbol before defining that response function.

**Proof.** Reflexivity, symmetry and transitivity follow pointwise from equality of total outputs/effects under the same domain and graph. Equivalent endpoints have identical equivalence classes. Equation (6) gives the ALG part; intersecting unchanged classes gives the joint part. Applying a fixed response function to an unchanged set gives an unchanged image. ∎

The class cardinality and the unrestricted annihilator dimension therefore do not decrease just because another safe update is counted. A local transition family depending on the current endpoint, such as a bounded step, a rank cap, quantized proposal rule, optimizer state or selected factorization, can nevertheless have fewer next-step options or stall. The theorem fixes the absolute universe; it does not equate these changing local reachability graphs.

**Quantization stall.** At a free coordinate currently storing 1, an ideal positive increment 2^(-(p+1)) is below half the spacing above 1 for precision p=8 or 24. Nearest rounding stores 1 again. Its actual increment is zero despite a nonzero ideal proposal. This does not show that the global feasible class has lost a member.

**Saturation compares different anchors.** For an n-by-2 bank with every row (Fmax,Fmax) and V=span(1,1), exact preservation requires z_1+z_2=2Fmax. Since finite entries are each at most Fmax, only the original row is possible. The legal input (1/2,1/2) spans V and executes to finite Fmax through two exact half-products and their exact sum, so the example does not require an overflowing protected evaluation. At the zero bank with the same V, every finite pair (a,-a) is feasible. These are different protected anchors, not two positions connected by a fixed-ALG chain. The positive-dimensional abstract nullspace and singleton saturated class are compatible.

For canonical alphabet size N, an exact affine feasible family of dimension q has at most N^q stored members. Indeed a basis matrix for its translation space has q independent rows; projection onto those q coordinates is injective on the affine family. Each selected stored coordinate has at most N choices. In the unrestricted annihilator family q=n(d-r). This is a finite count bound, not the dimension of the stored set. Along a fixed class its actual cardinality stays the same; adding compatible task constraints can shrink the absolute feasible set by intersection. For BIT the raw domain/effect constraints themselves must grow: numeric span inclusion alone does not prove this finite-set monotonicity.

ALG and BIT remain nonnested in general. The rounded-thirds matrix annihilates its declared span but changes a subnormal input's execution; a tiny off-diagonal edit of I_2 can be BIT-equal on a full-rank finite domain while failing exact annihilation. The inherited graph/rounding premises remain necessary. No entire finite-format class was enumerated merely by giving these constructions.

An infinite sequence drawn from a finite endpoint class must repeat endpoints, by the pigeonhole principle. It need not become periodic: arbitrary input/update choices or additional optimizer/history state can choose a nonperiodic order of repeated endpoint values. Neither repetition nor the availability of repeated nonzero edits proves indefinitely many distinct useful learned functions.

## T6 — Two scheduled histories and accumulated original-reference drift

Let histories A and B have bound schedules k_A(t),k_B(t). Assume their actual initial states satisfy a certified difference E_0. At time t let exact maps F^A_t,F^B_t and actual executions use those scheduled stored endpoints and the same admitted input. Suppose on jointly certified old/new domains:

- F^B_t has a cross-state Lipschitz bound L_t in one fixed norm;
- ||F^B_t(x,u)-F^A_t(x,u)||<=a_t on the A comparison domain;
- the two actual execution errors are bounded by rho^A_t and rho^B_t;
- both next-state domains and every intermediate shared call are certified total and contained in the next tube.

Then, with beta_t=a_t+rho^A_t+rho^B_t,

\[
E_{t+1}=L_tE_t+\beta_t,
\qquad
\|\widehat s^B_T-\widehat s^A_T\|
\le E_0\prod_{t=0}^{T-1}L_t+
\sum_{j=0}^{T-1}\beta_j\prod_{t=j+1}^{T-1}L_t.
\tag{7}
\]

**Proof.** At one step insert F^B_t at the A state. The cross-state, same-input endpoint and two execution residual terms give the one-step recurrence by triangle inequality. The joint range premises place both successors in their next domains. Starting from the initial relation, induct simultaneously on domain membership and the error bound. Expanding the nonhomogeneous recurrence gives the displayed product-sum, with empty products one. ∎

This is a new per-step/history instantiation, not automatic reuse of a fixed-bank B3 result. A supplied history must bind every version selection and graph/policy. Fixed finite histories cover their stated horizon; a family theorem requires uniform premises across every allowed history. Full-prefix observation uses max_(0<=t<=T)E_t, including E_0.

### T6(a): original-reference forcing from actual increments

At a common activation h, W_k-W_0=sum_(i<k)Delta_i. For an affine row and a coordinate envelope |h_j|<=H_j,

\[
|( (W_k-W_0)h+b_k-b_0)_\ell|
\le \sum_j\left|\sum_{i<k}\Delta_{i,\ell j}\right|H_j
+\left|\sum_{i<k}\delta b_{i,\ell}\right|
\le\sum_{i<k}\left(\sum_j|\Delta_{i,\ell j}|H_j+|\delta b_{i,\ell}|\right).
\tag{8}
\]

**Proof.** The endpoint and bias differences telescope exactly. Apply triangle inequalities first to h's coordinate expansion and then to the increment sums. ∎

Taking the maximum row gives an infinity drift bound, and coordinatewise ReLU does not enlarge it. The direct net bound can be smaller through cancellation. It already contains all increment/storage effects, so the rightmost increment budget is an alternative bound, not a term to add to the direct net bound.

For a nonlinear multi-bank exact map at one common state/input z, the function values also telescope:

\[
F_{W_k}(z)-F_{W_0}(z)=\sum_{i<k}\bigl(F_{W_{i+1}}(z)-F_{W_i}(z)\bigr).
\]

Adjacent exact-map bounds can therefore be summed only if each is valid at that same comparison domain, including its required internal evaluations. An adjacent certificate on an obsolete state envelope cannot justify (8) or its nonlinear analogue at a later new state. A sum of small adjacent patches can give a large original-reference forcing, and a contracting state gain alone does not bound that forcing uniformly.

For two histories, the exact bank difference is

\[
W^B_{k_B(t)}-W^A_{k_A(t)}
=(W^B_0-W^A_0)+\sum_{i<k_B(t)}\Delta^B_i-\sum_{i<k_A(t)}\Delta^A_i.
\]

Any bound must include the initial bank difference when it is nonzero. Actual state difference, same-input bank difference and per-update generation error are not interchangeable. Even an exact zero same-input bank action does not remove the two rounding terms in (7).

## T7 — Uniform switching needs a common certificate

Assume a family of allowed modes/histories has a common simultaneous invariant domain for both compared executions, a fixed common norm and input policy, uniform finite-operation/coverage proofs, L_t<=L<1, and beta_t<=b for every allowed step. Then

\[
\|\widehat s^B_t-\widehat s^A_t\|
\le L^tE_0+b\frac{1-L^t}{1-L}
\le\max\{E_0,b/(1-L)\}
\tag{9}
\]

for every finite t and every admitted history in that family.

**Proof.** The common invariant makes T6 applicable inductively at every time. Replace each coefficient by its uniform nonnegative upper bound, expand the constant recurrence, and evaluate the geometric sum. The final expression is a convex combination of E_0 and b/(1-L). ∎

The condition is sufficient, not necessary for every stable switching system. A finite tube, a mode's spectral radius below one, or separate mode-specific norms does not establish it. If L=1 with zero forcing, E_t<=E_0 follows under the same invariant premises; positive forcing gives the finite bound E_0+tb. L>1 gives a possibly amplifying upper envelope, not an automatic lower-growth theorem.

### T7(a): individually stable modes can amplify under switching

Let

\[
A=\begin{pmatrix}0&2\\0&0\end{pmatrix},\qquad
B=\begin{pmatrix}0&0\\2&0\end{pmatrix}.
\]

Then A^2=B^2=0, so repeatedly using either exact mode alone sends every state to zero in two steps. Nevertheless BA=diag(0,4). Starting from e_2 and applying A then B repeatedly gives state 4^m e_2 after 2m steps.

**Proof.** Direct matrix multiplication proves the identities. Since BA e_2=4e_2, induction yields (BA)^m e_2=4^m e_2. ∎

Each mode even contracts in its own norm: define ||(x,y)||_A=max(|x|,4|y|) and ||(x,y)||_B=max(4|x|,|y|). Then ||Az||_A<=||z||_A/2 and ||Bz||_B<=||z||_B/2. But no single norm can make both modes contract by a common L<1, because it would imply ||BA e_2||<=L^2||e_2||, contradicting the exact factor 4. Switching changes the norm comparison; separate contractions cannot be multiplied as if they used one norm.

This history can be expressed with monotonically increasing version indices by publishing numerically repeated banks A,B,A,B,... and selecting k(t)=t. The exact real growth theorem is not an infinite finite-format execution claim: finite formats eventually require range checks/refusal, and finite probes establish only their recorded horizons. If both compared histories have identical states and identical modes, their error is zero; mode growth alone does not imply a difference between identical executions.

## T8 — Prefix numerical budgets are read-only evidence

Suppose a history verifier establishes T6's joint-domain premises and records certified E_0,...,E_T. For a full-state prefix observation define B_T=max_(0<=t<=T)E_t. Then B_T bounds the maximum observed difference through T. Alternatively, separately prescribed per-time budgets q_t are sufficient when E_t<=q_t for every t.

**Proof.** Each state difference is at most its E_t by T6. Taking a maximum proves the prefix result; comparing each term proves the per-time variant. ∎

B_T is nondecreasing with T even if the current E_T contracts. A final exact cancellation or a small final bound cannot erase a prior observed or certified budget excess. For example scalar states 0 versus 1 at time 1 and equal states at time 2 have final error zero but prefix error one. If the specification deliberately observes only the final time, that is a different claim and must be named as such.

A verifier may refuse because a conservative E_t exceeds budget even when the actual finite traces remain below it. Conversely a finite sample below budget does not prove its entire declared input/history family. A positive analytic bound is not reported as measured deterministic drift; identical executions can have zero actual difference and a positive conservative bound.

An accepted numerical receipt binds both histories and schedules, endpoint/bias versions, initial relation, joint coverage/invariant method, graph/activation/branch policy, every shared site, arithmetic policy, observation and budget. Pure recomputation establishes the bound under those premises and changes no endpoint/state/optimizer/history bank. It is neither BIT nor ALG_AND_BIT authorization. Strict full-domain canonical separation below eta can mathematically imply output-word equality, but the separate A3 program/effect and scheduling hypotheses remain, and the numerical receipt does not gain a live publication path.

## T9 — Exact-D serial history with atomic rejection and publication

Assume one trusted serialized owner maintains a complete owned snapshot consisting of weight banks/version, protected computational state, tick counter, optimizer state and B4 history/ledger metadata. The fixed D observation projection includes its protected state, covered outputs and effects; weights/version/optimizer/ledger are not assumed equal to an unpatched reference. Assume:

1. Every proposed endpoint is formed before checking, decoded exactly, and checked by the unchanged selected B1/A3 BIT or ALG_AND_BIT contract on one fixed complete context/invariant domain, graph, policy and sharing map.
2. A prepared transaction is bound to the current full snapshot, request/configuration, proposed endpoint/optimizer state, graph/domain/policy/schedule and intended history/ledger change. Recomputing against a changed protected tick, version, optimizer state or ledger refuses stale/inconsistent records.
3. All potentially refusing work, including record/receipt allocation and ledger validation, occurs without mutating the visible owned snapshot. Success exposes one validated complete replacement snapshot. Refusal publishes nothing. Updates preserve the D computational state; ticks use one old-state/bank snapshot and synchronized commit.
4. Metadata and A-side outputs influence D only through the covered checked interface. The initial D state, admitted external input sequence and trusted logical tick schedule match the original reference. The A3 invariant, totality and covered-effect hypotheses hold throughout.

Then every protocol refusal preserves the entire owned before/after snapshot. Every accepted update publishes its intended endpoint, optimizer and ledger/history changes atomically under this serial model. Every finite admitted event prefix has the same D observation trace as the original reference.

**Proof of rollback/publication.** All prepublication values are temporary data computed from the bound old snapshot. By premise 3 no rejecting computation assigns to the visible owner, so rejection changes none of its components. On success the one replacement contains all checked intended components; publishing that complete object exposes no partial endpoint/ledger or endpoint/optimizer state. The snapshot comparison prevents a stale transaction from restoring an older protected state or metadata.

**Proof of D trace preservation.** At an accepted update, its complete-domain BIT relation preserves the D state and local covered behavior. Transitivity of total local equality on the fixed context domain makes every accepted endpoint locally equivalent to the original one; ALG, when selected, is an additional obligation and not a substitute. At a rejected update the whole bank is unchanged. At a tick, the common input and same protected snapshot, complete covered local equalities and synchronized commit give the same protected successor and effects as the original reference by A3's one-step argument. Induction over the finite sequence of update/refusal/tick events proves equality of the D projection. ∎

This theorem does not assert full owned-bank equality to the unpatched reference: accepted weight words, versions, optimizer state and ledger entries intentionally differ. A ledger entry is not a D read unless covered by the interface premise. Same historical behavior cannot be recovered by adding a task after its violation; newly admitted tasks need their satisfaction/coverage proof before later preservation is claimed.

Unkeyed digests provide no original-intent authentication. A coherent new trusted-caller request may be accepted if fully checked against the current owner; inconsistent alterations and stale records refuse. General concurrency, crashes during publication, malicious private mutation and hardware faults are outside this serial proof. Existing finite version/resource limits cause refusal and do not create a promise of infinitely many successful updates.

Nonzero accepted A changes, repeated safe edits and measured improvement on a declared toy objective can demonstrate those particular executions. They do not prove universal learning benefit, endless distinct capacity or the later C-series compiler/kernel contracts.
