# P2-A1 — Activation-space theorems, proofs and counterexamples

All results use the definitions in [P2_A1_Definitions.md](P2_A1_Definitions.md). Every universal result below is a **handwritten proof**, not a Lean/Coq check or a theorem obtained merely from a finite experiment. Exact finite-instance enumeration can support the implementation and characterize its declared instance; its outcome and cost belong to the separate verification record.

## A1.1 — Existence, finite dimension and rational/real agreement

**Theorem.** Fix an input width d and a finite FP format with only finite accepted activation words. The set A of decoded activations over any set of admitted trajectories and all finite times is finite, even if there are infinitely many trajectories or time indices. The spaces V_Q=span_Q A and V_R=span_R A exist, have the same rank r between 0 and d, and admit a basis consisting of r actual activation vectors. There is a finite time horizon containing such a basis, unless r=0 in which case the empty basis suffices.

**Proof.** Each raw vector belongs to Fin_F^d, a finite set with at most |Fin_F|^d elements. A is its image under numeric decoding, so is finite; duplicated words or signed zeros can only reduce its cardinality. The definition of span supplies a subspace of K^d: zero is the empty combination, the sum of two finite combinations is another, and multiplying coefficients by any scalar stays within K. A greedy independent-subset construction selects at most d vectors from A and spans every rejected vector, giving a basis and finite dimension.

Place the selected rational vectors into a matrix. Its rank is the largest order of a nonzero minor. Every minor is a rational determinant; a rational number is zero in Q if and only if its image is zero in R. Therefore the ranks over Q and R coincide, and the same rational basis generates the corresponding spaces over the respective fields. This is not equality of V_Q and V_R as sets.

For each basis activation, its membership in A has a witness at some call event of a finite admitted execution prefix. There are finitely many basis vectors, so the maximum of their finite witness times is finite. That horizon need not be known or computable from samples. If A is empty or consists only of zero vectors, the rank is zero. ∎

**Consequence.** Finiteness of a numerical format establishes finite dimension and a finite witness set; it does not establish a small rank, an efficient enumeration, or closure of A itself under real linear combinations.

## A1.2 — Shared matrices, monotonicity, and samples

**Theorem.** In a common physical column frame of dimension d,

$$
V_M=\sum_c V_{M,c},\qquad
\max_c\dim V_{M,c}\le\dim V_M
\le\min\left(d,\sum_c\dim V_{M,c}\right).
$$

For this nonnegative-dimension bound, define max over an empty call-site family to be zero; the empty sum of spaces is {0}.

If admitted initial states, legal input histories or admitted call sites are enlarged while the fixed transition/call semantics is retained, each old activation set is a subset of the new one and its rank cannot decrease. For a legal sample set B subset A, rank(B) <= rank(A); if rank(B)=d, then rank(A)=d. If rank(B)<d, the samples alone provide no nontrivial upper bound on rank(A).

**Proof.** A vector in span(union_c A_c) is a finite linear combination whose terms can be grouped by c; each group belongs to V_c, so the vector lies in the sum. Conversely, expand each member of a finite sum of V_c as a linear combination of its activation generators; the result belongs to span(union_c A_c). Each summand embeds into the sum, proving the lower bound. Concatenating bases of the summands gives a generating set of size sum_c dim V_c, proving that upper bound; the ambient bound is d.

Every previously admitted trace remains admitted under a genuine enlargement of the allowed traces without semantic changes. Every old call event therefore remains, so set inclusion and span inclusion follow. Apply this to a sample set for the rank inequality. Full ambient rank leaves no possible larger subspace. For deficient samples, both an activation set equal to their span's sampled generators and an extension by missing basis directions are compatible with the same recorded samples; a concrete deterministic realization appears in Counterexample A1.9. ∎

The rank monotonicity statement does not compare two different programs or numeric policies. Changing a rounding policy, call order, compiler layout or shared identity can change the actual trace family, not simply enlarge it.

## A1.3 — Complements, annihilators and their limitations

**Theorem.** Let V subset K^d have dimension r. An algebraic direct complement of dimension d-r exists. Over R with the standard Euclidean inner product, V-perp has dimension d-r. For rational generators, the rational annihilator

$$
V^\circ=\{\lambda\in\mathbb Q^d:\lambda^T v=0\text{ for every }v\in V\}
$$

has dimension d-r over Q and extends to the real orthogonal complement. For a shared matrix,

$$
\left(\sum_c V_c\right)^\circ=\bigcap_c V_c^\circ.
$$

A nonzero complement/annihilator exists exactly when r<d, including the r=0 empty-call case.

**Proof.** Extend a basis of V to a basis of K^d; the span of the added basis vectors is a direct complement of dimension d-r. For the annihilator, put a basis of V in the columns of a d by r matrix B. The equations B^T lambda=0 have coefficient rank r, so rank-nullity gives kernel dimension d-r. These are rational equations, and A1.1's minor argument gives the same rank over R. A linear functional vanishes on a sum exactly when it vanishes on each summand, proving the intersection identity. ∎

These are algebraic statements only. A nonzero real or rational direction need not be representable by one FP word per coefficient, respect a compiler's coefficient bounds/sparsity, preserve its Boolean-output certificate, or retain any FP execution bits. For example, the annihilator of (1,3) in R^2 is the line generated by (-3,1), but its intersection with integer coefficient changes restricted to [-2,2]^2 is only zero. This example is about an algebraic coefficient restriction; (1,3) is not presented as a legal two-Boolean D input. No patch is applied in this round.

## A1.4 — Affine augmentation

**Theorem.** For nonempty A subset K^d and a_0 in A, let D_A=span_K{a-a_0:a in A}. Then

$$
\operatorname{aff}(A)=a_0+D_A,
$$

and

$$
\operatorname{span}_K\{(a,1):a\in A\}
=\operatorname{span}_K\{(a_0,1)\}\ \oplus\ (D_A\times\{0\}).
$$

Consequently the augmented rank is dim(aff(A))+1 and lies between rank(A) and rank(A)+1. If A is empty, its augmented span is {0}; the nonempty formula is not used.

**Proof.** An affine combination sum_i alpha_i a_i with sum_i alpha_i=1 equals a_0+sum_i alpha_i(a_i-a_0), so belongs to a_0+D_A. Conversely, a_0+sum_i beta_i(a_i-a_0) equals (1-sum_i beta_i)a_0+sum_i beta_i a_i, an affine combination. Each lifted generator is (a_0,1)+(a-a_0,0), and each difference (a-a_0,0) is the difference of two lifted generators. This proves equality of the lifted span and the stated sum. Their intersection is zero because a multiple of (a_0,1) has final coordinate equal to its multiplier, whereas D_A times {0} has final coordinate zero. The dimension is therefore 1+dim D_A. Projection onto the first d coordinates maps the lifted span onto span(A), so its dimension is at least rank(A); appending one row to a generator matrix increases rank by at most one, proving the other bound. ∎

The lift is an analysis of a joint affine block or of state dynamics. It does not imply that call-specific biases are one physically shared parameter, nor that the FP execution can move its bias into an arbitrary reduction position.

## A1.5 — Exact finite-state reachability and span construction

**Theorem.** Suppose the finite-monitor model has a finite enumerable configuration set Q, finite input alphabet U, finite enumerable Q_0, decidable enable/acceptance predicates, and a terminating exact one-step evaluator producing finite call logs. Worklist reachability initialized by Q_0, processing every enabled input at every newly discovered configuration, terminates and returns exactly Reach. Collecting every matching event at every processed enabled transition returns exactly A_raw_{M,c} and hence the exact numeric local/global spans of the specified model, for all finite times.

**Proof.** Each queued configuration is placed into a set and queued only on first discovery. At most |Q| configurations can be added, and each has only |U| input candidates, each checked/evaluated in finite time with finite output, so the procedure terminates.

Soundness follows by induction over additions. Each initial configuration has an admitted empty prefix. If q has an admitted witness prefix and en(q,u), the Markov contract makes its extension by u admitted, so its successor is reachable and every event emitted by that transition is a legal event. Completeness follows by induction on the length of any admitted prefix: q_0 is queued; after the predecessor is eventually processed, its enabled actual next input is considered, so the successor is included. Thus all reachable configurations and all admitted next-step call events occur in the returned collection. Definition 4 identifies these with the activation sets, and exact rational linear algebra returns their spans. ∎

**Shortest-witness bound.** Let R=|Reach|>0. Every reachable configuration has a simple path from some q_0 of length at most R-1: remove a repeated-configuration segment from a shortest path, retaining the same enabled suffix because configurations include the full monitor/scheduler state. Every emitted activation has a witness in one further transition, of prefix length at most R. This is a model-dependent bound derived from complete reachability, not a justification for stopping after an arbitrary number of stable ranks.

**Cost.** Write K for the total number of emitted input vectors, C_step for a bound on one enabled-step evaluation including its log, and d_M for each matrix's input dimension. There are at most R|U| tested state/input pairs. State hashing/encoding and enable evaluation also have costs and are not assumed free. With one incremental exact basis per local site and per matrix, each vector costs O(d_M^2) field operations, so an explicit bound is the traversal cost plus O(sum_events d_M^2) rational operations (up to the separately declared local/global bookkeeping). Storing every event costs its full output size; streaming a basis can reduce activation storage but cannot remove the need to retain the visited-state set or complete transition coverage.

These are not unit-cost bit-complexity claims. Numerators and denominators must be stored and arithmetic/gcd performed exactly. For rational input entries of bit length at most B, clearing denominators in a d-dimensional row gives integer bit length O(dB); determinant/minor bounds for a reduced echelon basis give polynomial bit lengths O(d^2 B+d log d). A fraction-free or reduced-rational rank implementation therefore has polynomial bit cost in the explicit activation-matrix size and these bit lengths. The verification script may report its measured counts rather than asserting a sharp symbolic arithmetic constant. With b independent binary state slots, the legal state space can have 2^b states; with k unrestricted input bits, |U|=2^k. More specifically, the P1 A4 source layout with b register bits and an m-way one-hot PC has m times 2^b type-legal states, not 2^(b+m); a finite monitor/scheduler multiplies that bound by its own number of configurations. Reachability from the specified initialization can be much smaller. A finite algorithm is consequently exponential in a compact bit-width description even before graph evaluation and rank work.

For an abstract interpreter or compiler, a resource budget may cause early refusal. Such refusal is not a completion certificate and cannot justify reporting a partial basis as the exact global space.

## A1.6 — Sound affine invariant-space construction

**Theorem.** Let z in Q^n be a chosen lifted feature representation. Supply finite rational generator sets for initial space U_init and error spaces E_j, finitely many rational n by n matrices B_j, and prove that every initial feature is in U_init and every admitted actual successor in mode j satisfies z' in B_j z+E_j. Define

$$
U_0=U_{\rm init}+\sum_j E_j,\qquad
U_{k+1}=U_k+\sum_j B_jU_k.
$$

The sequence stabilizes after at most n-dim(U_0) strict increases. Its fixed point U_* is the least linear subspace containing U_init and every E_j and invariant under every B_j. Every reachable actual feature is in U_*. If each emitted physical input at site c is proved to lie in H_c z+F_c for a rational linear H_c and a declared error/input space F_c, then

$$
V_M\subseteq\sum_{c\in\operatorname{Sites}(M)}(H_cU_*+F_c).
$$

**Proof.** Every U_k is a subspace and U_k subset U_{k+1}. A proper inclusion raises its integer dimension by at least one; all dimensions are at most n, proving termination of an equality-tested iteration. At equality, B_j U_* subset U_* for every j, and initial/error inclusion is inherited from U_0. If V is any other subspace with those properties, U_0 subset V; induction gives U_{k+1} subset V from U_k subset V and B_jV subset V. Hence U_* subset V, proving minimality relative to the declared operation/error family.

For actual executions, initialization gives z_0 in U_*. If z_t lies in U_*, then z_{t+1}=B_j z_t+e for some e in E_j, and both terms belong to U_*, so z_{t+1} is in U_*. Induction covers every finite admitted prefix. The observation assumption therefore puts every emitted activation in the corresponding H_cU_*+F_c; their sum is a subspace containing their union, so contains its span. ∎

A basis test suffices for B_j-invariance because B_j is a genuinely linear algebra map: B_j(sum alpha_i b_i)=sum alpha_i B_j b_i. It does **not** suffice for an arbitrary nonlinear or rounded implementation merely because that implementation was evaluated on the same basis. Exact affine FP agreement on the admitted domain, or a proved enclosure of all rounding errors in E_j, is part of the certificate's soundness assumptions.

**Cost.** An n-dimensional basis has at most n columns. In one round, at most |J|n images B_j b are needed, with O(|J|n^3) elementary rational operations for dense matrix-vector multiplication plus incremental basis reduction. At most n+1 rounds suffice with the simple synchronous construction, yielding a coarse O((|J|+1)n^4) rational-operation bound, separate from initial input parsing, error-generator reduction and observation maps. Rational bit lengths and their arithmetic costs are additional. This polynomial bound is in the explicit feature dimension and explicit family description; those can already be exponential in a compact finite-state program.

Guard removal is sound only as an overapproximation: closing under every mode in every feature state permits all actual mode sequences and possibly many impossible ones. It can produce a full ambient space even when the exact reachable activation span is deficient. The fixed point is the least invariant subspace for the *relaxed algebraic family*, not necessarily the least exact reachable span.

**Location-indexed variant.** Let locations l have spaces U_l and allowed edges e:l->l' with z' in B_e z+E_e. Require initial inclusion at each starting location and B_e U_l+E_e subset U_l' for every edge. Reachable features at each location lie in its U_l by the same path induction. A worklist adds missing basis vectors along edges; the sum of dimensions can rise at most n times the number of locations. Closure is over these edges, not over unmodeled transitions. Call-site superspaces are mapped from their respective locations before merging by physical matrix identity.

### Concrete exact Boolean invariant

Let the state be (x,y) in {0,1}^2, initialize it at (0,0), and admit only hold, simultaneous toggle (x,y)->(1-x,1-y), and reset to (0,0). On the homogeneous feature z=(x,y,1), use

$$
B_{\rm hold}=I_3,\quad
B_{\rm toggle}=\begin{pmatrix}-1&0&1\\0&-1&1\\0&0&1\end{pmatrix},\quad
B_{\rm reset}=\begin{pmatrix}0&0&0\\0&0&0\\0&0&1\end{pmatrix}.
$$

Set every error space to zero. Starting from span{(0,0,1)}, toggle adds (1,1,1), so the closure is U_*=span{(0,0,1),(1,1,0)}, of dimension 2 in ambient dimension 3. Every displayed map preserves the relation x=y, proving closure directly; each generator is obtained from initialization and one image, proving minimality. Projecting to the operand pair gives span{(1,1)}, of dimension 1 in ambient dimension 2. The exact reachable Boolean states are (0,0),(1,1), so this bound is attained.

This example satisfies an actual discrete P1 implementation premise: hold and reset are bit-preserving copies/constants, and toggle uses two exact NOT operations reading one old snapshot. All outputs remain canonical Boolean encodings. There is no unproved appeal to affine FP linearity on arbitrary real inputs. Adding a reset to (1,0) breaks x=y and makes the operand span full; the allowed reset operation family is essential.

## A1.7 — Exact one-hot lift exists but need not be useful

**Proposition.** Any explicit finite total deterministic transition table on N configurations, with a finite input alphabet, admits an exact N-dimensional one-hot linear lift. For each input u define B_u e_q=e_{delta(q,u)}. If an input is disabled at q, assign that column any fixed value, such as zero, for a conservative operation-family closure. A deterministic call-vector table a_c(q,u) has a linear observation map H_{c,u} with H_{c,u}e_q=a_c(q,u); set the column to zero when no call occurs. For multiple events per tick, index the bounded event slots separately.

**Proof.** A linear map is uniquely determined by its values on a basis. Define the stated columns. Every legal actual transition/call on a one-hot configuration then agrees with the corresponding column by construction. Initial one-hot vectors and the linear-family closure satisfy A1.6's assumptions. Disabled combinations or absent calls introduced by relaxed closure can add conservative results, including zero, but cannot remove any legal event. ∎

The one-hot feature dimension N is the complete configuration count, not the number of original register bits. Building this table already incurs explicit state-space cost. The proposition proves representability, not a small or efficiently discoverable invariant, and does not imply that an unconstrained real linear combination of one-hot states is itself executable.

## A1.8 — Full rank is neither necessary nor forbidden

All Boolean examples below use canonical +0/+1 inputs and can be implemented by exact P1 Boolean gates, fixed-width registers and synchronous snapshot updates. They are semantic examples; the separately recorded script determines which concrete instances were executed.

**Full Boolean input cube.** Let a call receive every a in {0,1}^d through unrestricted legal input, with d>=1. Each standard basis vector e_i occurs, hence V=K^d, rank d and complement dimension zero. The affine lift includes (0,1) and (e_i,1); their differences yield (e_i,0), so its rank is d+1. Thus finite precision and discrete exactness do not force low rank.

**Correlated nonzero bits.** Restrict a=(b,b) with b in {0,1}, by the input contract or a proved synchronous duplicate-register invariant. A={0,(1,1)} and V=span{(1,1)} has rank 1 in dimension 2. Its affine lift has generators (0,0,1),(1,1,1), of rank 2 in dimension 3. It has a nontrivial algebraic complement despite exact execution. If the initial-state contract instead allows (1,0), or a legal input/reset can independently write one component, the old correlation need not hold and full rank can result. The invariant requires the allowed initial states as well as preservation by each transition.

**Zero and unreachable calls.** A called zero vector produces rank 0; a site never reached has an empty activation set and also rank 0. Their event semantics differ even though their numeric spans coincide. If A={(1,1)} rather than {0,(1,1)}, its ordinary rank remains 1 but its lifted rank is only 1, illustrating why an affine conclusion cannot be inferred from ordinary rank alone.

**Sharing destroys separate slack.** Suppose one site of the same two-column matrix receives {0,e_1} and another receives {0,e_2}. Each local span has rank 1, but their global sum has rank 2 and no common annihilator. They cannot be analyzed as two independently modifiable matrices. If instead they are distinct parameter objects with equal coefficient words, each retains its own rank-1 space. A local coordinate permutation must be applied before this union, not after a convenient independent relabeling at each site.

**One-hot vectors are not a homogeneous rank constraint.** Let A={e_1,...,e_m}. Although sum_i a_i=1 for every activation, the ordinary rank is m: the vectors themselves are a basis. This equation is affine, not a homogeneous relation among the m coordinate functions. The lifted vectors (e_i,1) still have rank m in dimension m+1, with the homogeneous relation sum_i a_i-last=0.

**Fixed counter/PC example.** If a b-bit counter starts at zero, increments modulo 2^b and its bits are observed before each update forever, it reaches every Boolean word and its bit-vector span has rank b. If a fixed HALT stops it before some states, its exact span can shrink. Repeatedly observing a fixed halted state yields no new direction; a P1 graph that continues executing its entire HALT tick may nevertheless have more internal call events than a host interpreter that makes no call after HALT. The actual specified executor decides which set is relevant.

## A1.9 — Why sample rank stabilization does not certify all time

**Counterexample.** For any prescribed finite H>=1, construct a fixed finite counter with states 0,...,H and absorbing H, initialized to zero. At each tick emit e_1=(1,0) when the old counter is below H, otherwise emit e_1+e_2=(1,1); advance counter by one with saturation at H. The first H calls all equal e_1 and have rank 1. Call H+1 emits e_1+e_2, an independent vector, so the all-time global rank is 2. The counter requires a finite width sufficient for H, and all comparison/MUX/update operations have exact Boolean realizations. This is a family of different fixed finite machines, one for each H; it does not contradict A1.5's bound for any one explicit complete configuration graph.

The example also defeats stopping on several consecutive rounds of unchanged rank. The correct finite-state stopping condition is that every reachable configuration has been processed under every legal enabled input, or another valid invariant/containment certificate—not that new samples happened to lie in the existing span.

A finite full-rank sample *is* a certificate of full rank, as A1.2 explains. Also A1.1 proves that every deficient global span has some finite basis-witness horizon. The missing information is a certified **upper** bound excluding unseen directions, not the existence of finite generating witnesses.

## A1.10 — Arbitrary computable history policies can defeat exact computability

**Proposition (precise scope).** There is no algorithm that returns the exact global activation rank for every finitely described pair consisting of (i) a fixed one-state exact Boolean input-recording D program and (ii) an arbitrary total computable finite-history admission predicate, even though the input alphabet and D storage are finite.

**Proof by reduction.** Given a Turing machine T and its fixed input, let the call's allowed numeric input vectors be e_1=(1,0) and e_2=(0,1). D has one state, leaves it unchanged, and presents its input vector to the observed call. The history policy always allows e_1. At a history of length t, it allows e_2 if and only if simulating T for t steps has observed termination. Each single predicate evaluation terminates, because it performs only t simulation steps. Admitted finite histories are defined by requiring this predicate at every position, so are prefix-closed and include the empty history.

If T never halts, only e_1 ever appears and the rank is 1. If T halts after h steps, the legal prefix of h copies of e_1 can be followed by e_2, so both basis directions occur and the rank is 2. An algorithm always returning the rank for this specification class would therefore decide T's halting, contradicting undecidability of that problem. ∎

The unbounded history length and simulation state are in the external policy, not hidden in a finite Markov monitor. This proposition does not contradict exact finite BFS when a finite complete monitor is actually supplied. It explains why “all data words are finite precision” is insufficient by itself for a universal termination or effective exact-space claim. The trivial superspace K^d remains computable and sound in this class; the obstruction is to returning the exact rank, not to returning any conservative container.

## A1.11 — Representation, control and nonlinear lifting change rank

**Encoding proposition.** A variable with 2^w possible values has all of the following valid but different input geometries, depending on which actual representation a matrix receives:

- Its full binary encoding has ambient width w and rank w for w>=1, because all standard basis bit patterns occur.
- A one-hot encoding has width 2^w and rank 2^w, because its legal words are all basis vectors.
- A single exact packed scalar has width 1 and rank 1 if at least one represented value is nonzero. This scalar realization is asserted only when the chosen encoding admits all those exact scalar words. A floating format cannot encode arbitrarily many distinct values in one word.

**Proof.** The first two claims follow from the displayed basis witnesses. Every nonzero subset of a one-dimensional space spans that space. No comparison of ranks is meaningful without recording the different ambient representations. ∎

The packed scalar's rank does not bound the rank after exact nonlinear extraction into bits. Conversely, a duplicated wire can create a homogeneous relation at one row's input even when the complete register state has full span. Padding, repeated taps, unused coordinates and call-site gather maps are therefore part of the dimension specification.

**Control/input proposition.** Suppose every combination of r Boolean register bits, k Boolean input bits and an m-way one-hot PC is admitted at a call, with m>=1. Its ordinary input dimension and rank are r+k+m. Its homogeneous affine lift has ambient dimension r+k+m+1 but rank r+k+m.

**Proof.** Activations with all register/input bits zero and PC e_j provide the m independent PC basis vectors. The difference between an activation with one chosen register/input bit set and the otherwise identical activation gives that coordinate's basis vector, so all r+k+m ambient directions lie in the ordinary span. For the lift, the equation sum_j PC_j-last=0 gives an upper bound r+k+m. The lifted PC vectors with all other bits zero are m independent vectors, and the r+k coordinate differences are independent of their span, giving the matching lower bound. ∎

This is an all-combinations hypothesis. A chosen reset PC, reachability restrictions or input correlations can reduce the rank. A legal type-level state space and the reachable state set from one specified initialization must not be conflated.

**Nonlinear feature proposition.** On all Boolean pairs (a,b), the augmented input (a,b,1) has rank 3, whereas (a,b,ab,1) has rank 4.

**Proof.** The four lifted feature vectors at (0,0),(1,0),(0,1),(1,1) are (0,0,0,1),(1,0,0,1),(0,1,0,1),(1,1,1,1). Subtract the first vector from the second and third to obtain the first two basis directions; subtract those plus the first from the fourth to obtain the third direction. The first vector provides the fourth direction. The input rank follows from A1.4 or the three obvious independent vectors. Boolean multiplication/AND is an exact P1 gate on these inputs; increasing feature rank does not require numerical error. ∎

**Nonlinear closure counterexample.** The line V=span{(1,-1)} is not invariant under coordinatewise ReLU, because ReLU(1,-1)=(1,0) is not a multiple of (1,-1). Even checking only a chosen basis against ReLU is unsound: let V=span{(1,1,0),(0,1,1)}. Both basis vectors are nonnegative and remain fixed by ReLU. Their difference (1,0,-1) is in V, but its ReLU image (1,0,0) is not, because every vector in V satisfies its middle coordinate = first coordinate + third coordinate. A ReLU-specific implementation must prove its own reachable-domain containment or use sound activation bounds/finite enumeration; it cannot borrow linear-basis closure without such a proof.

**Compiler boundary.** The existing P1 A4 reference evaluates every generated graph node on every tick, including circuits belonging to inactive source-PC alternatives. A source branch's inactive assignment does not imply absence of its compiled call. A HALT source state also does not imply no calls when the reference tick is still invoked. A valid activation analysis instruments the actual fixed graph schedule or proves a precise relation to a pruned schedule; it cannot silently prune by source control flow. Equal coefficient tuples on two independently stored rows also do not establish physical sharing. A sharing adapter must declare which rows are tied, keep common operand/bias ordering, and be validated as the chosen presentation; it is not inferred solely from a matching numeric value.

## A1.12 — Exact annihilation is not a bitwise FP guarantee

**Counterexample.** Let p=8 for BF16 or p=24 for FP32, and let A=2^p. Use the numeric activation a=(1,1,1,1) and row v=(A,1,-A,-1), with zero bias and separate multiplication followed by sequential nearest-even addition in that listed order. All constants and individual products are exactly representable. In rational/real algebra,

$$
v^Ta=A+1-A-1=0.
$$

Under the stated floating reduction, the first sum is A; adding 1 is a midpoint at that binade and rounds back to the even value A. Adding -A gives canonical zero, and adding -1 gives -1. The all-zero row yields zero on the same activation. Thus exact annihilation by v does not imply bitwise equality of these two ordered FP evaluations.

This comparison is a numerical counterexample, not an admissible update of the protected D graph. Its coefficients exceed A4's small gate-coefficient contract. The point is precisely that an algebraic null-space argument cannot substitute for the arithmetic/encoding/compiler certificates needed to justify any later modification. Software BF16 and actual scalar CPU FP32 execution of this example, if run, remain separate finite arithmetic evidence.

## Scope at the stopping point

The mathematical answer is conditional but definite: every specified fixed-width call family has a finite-dimensional activation span; exact finite-state enumeration and proved invariant superspaces can establish global constraints; rank need not be full, but neither exactness nor finite precision ensures a nontrivial complement. Sharing, broader legal inputs, initialization, encoding and compiled intermediate features can eliminate a complement. A deficient sample rank does not certify one. No weight update, learning rule, or P2-A2 safety theorem is constructed here.
