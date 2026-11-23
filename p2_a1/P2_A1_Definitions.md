# P2-A1 — Legal trajectories and deterministic activation spaces

This document defines the objects studied in this round. It does not implement weight modification, promise useful learning directions, or advance P2-A2. The statements called theorems are proved in [P2_A1_Theorems.md](P2_A1_Theorems.md). Executed finite-instance evidence is reported separately.

## 1. Fixed execution contract

Fix one deterministic program D, its compiled graph and topology, parameter words, matrix sharing, state and input layouts, and numerical policy. The P1 contract is assumed, rather than re-proved:

1. Every protected Boolean port uses the declared BF16/FP32 encodings of canonical +0 and +1. Fixed-width words and control states use the declared encoding; arbitrary finite FP words are not automatically legal Boolean inputs.
2. Each primitive has the declared format, rounding and operation order. Any zero normalization, overflow rejection, and acceptance domain are part of that policy. Separate multiplication/addition is not silently replaced by FMA or a different reduction.
3. Register loads, stores, copies and resets preserve the required bits. All next-state expressions read the same old snapshot; a complete candidate is committed synchronously.
4. D and the scheduling rule are fixed. The state description includes every variable that can affect the next transition or a recorded call. Hidden mutable state, an unmodeled time counter, concurrent writes or a changing D are outside this model.
5. Legal initial states and external inputs are specified before collecting data. Environment constraints, reset permissions, and the treatment of HALT are part of the specification. The theorem ranges over every admitted choice, not just a supplied test trace.
6. Every considered execution step satisfies the P1 arithmetic/storage/scheduling contract. These are conditional semantic claims, not certification of all CPU/GPU implementations or immunity to hardware failure.

A1/A2/A4's exact discrete logic results apply to their admitted generated programs. They do not make every arbitrary real-weight neural network exact. General finite-FP calls below use their actual specified arithmetic semantics, and their numeric activations need not equal an unrounded real-network evaluation.

## 2. Raw words, scalar fields, and vector spaces

Let F be the fixed format. Let Word_F be its finite set of bit patterns, and Fin_F the accepted finite numeric patterns (excluding NaN and infinity). The numeric decoding map is

$$
\nu_F:\operatorname{Fin}_F\longrightarrow\mathbb Q\subset\mathbb R.
$$

Every finite binary floating-point number is dyadic, hence rational. If both signed zeros are admitted at a non-Boolean port, both decode to rational zero. Raw-word equality, numeric equality, and equality of decoded vectors remain distinct. At protected Boolean ports, the P1 canonical +0 restriction removes that particular ambiguity.

For a matrix with m input columns, the ambient scalar field K is explicitly either Q or R, and its numeric input space is K^m. The decoded finite activation set is **a subset** of that vector space. In general it is not closed under addition or scalar multiplication: {0,1} is not a vector space over Q or R. No floating arithmetic is used to define exact linear combinations, rank or orthogonality in this round.

For a finite rational set A, define

$$
\operatorname{span}_{\mathbb Q}A
 =\left\{\sum_{i=1}^{k}\alpha_i a_i:k\ge0,\ \alpha_i\in\mathbb Q,\ a_i\in A\right\}.
$$

The empty sum is zero; in particular span(empty set)={0}. Define span_R identically with real coefficients. Their dimensions agree for rational A, but the resulting sets differ: a nonzero rational line contains only rational vectors over Q and also irrational multiples over R.

## 3. Legal inputs, initialization and histories

### 3.1 General history semantics

Let S_D be the finite set of declared raw D-state encodings when storage widths and topology are fixed. Let I_D be a specified subset of legal states. Let U be the finite alphabet of input records whose raw words satisfy the input type/encoding contract. A history specification L assigns a set of admitted finite input histories to each allowed initial state. It can enforce correlations, reset rules or restrictions beyond per-record type validity.

Assume its admitted executable histories are prefix-closed, include the empty history for every initial state, and use a fixed deterministic execution policy. This defines the set of all admitted finite execution prefixes. The time index t is the number of completed logical transitions, not necessarily a hardware cycle or high-level loop iteration. Call events may occur inside a transition; all their positions and read snapshots are determined by the execution policy.

If L contains arbitrary history dependence, finite storage of D alone does **not** make L finite-state or provide an effective exact reachability algorithm. Existence of the sets defined below is distinct from computing them. A policy that uses an unbounded external clock or undecidable predicate needs separate assumptions; it cannot be hidden in a claim that the whole system is finite-state.

### 3.2 Finite monitor form for executable enumeration

For the constructive finite-state theorem, supply a finite monitor H and a fixed finite logical scheduler state K_s. The augmented configuration space is

$$
Q\subseteq S_D\times H\times K_s,
$$

with a finite, explicitly enumerable initial set Q_0. Q contains the legal combinations, including any cross-field invariant. Let input_ok(q,u) be the declared input/monitor permission predicate. A terminating deterministic step evaluator either accepts with a successor/log or returns its declared arithmetic rejection. Define the effective admission predicate en(q,u) to mean input_ok(q,u) **and successful numerical acceptance of that step**. It is required to be decidable; this acceptance policy is fixed before any collection. In the total generated P1 discrete case, input_ok already implies numerical acceptance. Deterministic evaluation then defines an admitted transition

$$
\delta(q,u)=(q',\operatorname{log}(q,u))
\quad\text{whenever}\quad \operatorname{en}(q,u),
$$

where q' belongs to Q and log(q,u) is a finite ordered list of matrix-call events. Termination of this single-step evaluator is an explicit assumption. For a P1 finite DAG tick, the bounded node schedule provides it. A generated P1 discrete tick has no arithmetic rejection on admitted legal states and inputs under its execution contract; the partial-function discussion below is for a more general declared finite-FP policy. There is no implicit assumption that an arbitrary interpreter step containing an internal unbounded loop terminates.

The underlying step relation may be partial on raw type-valid inputs if the declared numerical policy rejects. The displayed delta is its restriction to en(q,u), so it is defined on every admitted pair; en does not mean type validity alone. Its admissibility/acceptance rule must be explicit and decidable. A rejected call must not be retrospectively treated as an accepted legal transition merely because its partial output is convenient. For the finite-monitor construction, log(q,u) covers an admitted, completed transition. Even calls that finish before a later failure/aborted commit are outside those successful-transition logs unless explicit abort transitions are added. Failed arithmetic attempts and aborted-prefix observations therefore require a separate event model if they are of interest. This distinction does not exclude any admitted generated P1 tick, because its legal-domain execution is total under the assumed contract.

An allowed finite trace has q_0 in Q_0 and, for each t, en(q_t,u_t) and delta(q_t,u_t)=(q_{t+1},log_t). Define

$$
R_0=Q_0,\qquad
R_{k+1}=R_k\cup\{q':q\in R_k,\ u\in U,\operatorname{en}(q,u),\delta(q,u)=(q',\ell)\},
$$

and Reach=union_{k>=0} R_k. The monitor/scheduler must make this representation Markov: all future admissibility and calls depend only on q and the next u. Two D states that look the same cannot be merged if their monitor states permit different futures.

HALT can be modeled as an absorbing state that still executes a declared tick circuit, or as no further transitions. These choices can yield different call sets and must be stated. Reset may be an input, an initialization rule or a separately modeled operation; it is not silently added to every trace.

## 4. Matrix identities, call sites and global activation sets

Let M denote one fixed physical/shared parameter matrix W_M of shape r_M by m_M. Its identity includes the parameter storage identity, orientation, column order and execution policy. Distinct matrices with equal numeric entries are not thereby the same shared object. A call site c is a static location in the fixed program; an event also records its occurrence within a tick. A finite bounded graph may invoke the same matrix at multiple sites, and repeated execution revisits sites at arbitrarily many t.

All calls of M must be represented in its **same physical input-column frame** K^{m_M}. If a site first permutes, pads, gathers or encodes values, the activation vector is the actual input after that preparation. Local coordinates cannot be compared or merged without the declared mapping into this common frame. A use of W_M transposed has a different input dimension/parameter action and is not silently folded into this definition; it needs its own oriented-call model and joint parameter analysis. Batched calls may be expanded into one event per input column/row according to the declared multiplication convention. Merely treating a dense row or a reconstructed graph as a hardware GEMM is not justified.

A call event is (M,c,a_raw), with a_raw an accepted vector of m_M raw finite words. Define A_raw_{M,c} as all such raw vectors appearing at site c in **any** admitted finite prefix, from **any** allowed initial state. Then

$$
A_{M,c}=\{\nu_F^{m_M}(a):a\in A^{\rm raw}_{M,c}\},\qquad
A_M=\bigcup_{c\in\operatorname{Sites}(M)}A_{M,c}.
$$

Equivalently in the finite-monitor model, collect the matching call events from log(q,u) for every q in Reach and every enabled u. Every reachable q has a legal history, and the Markov monitor makes every enabled extension legal.

The local and globally shared spaces are

$$
V_{M,c}^{K}=\operatorname{span}_{K} A_{M,c},\qquad
V_M^{K}=\operatorname{span}_{K} A_M
       =\sum_{c\in\operatorname{Sites}(M)}V_{M,c}^{K}.
$$

These are numeric geometry objects. They do not contain call order, correlations between two successive activations, raw signed-zero distinctions, or the entire program semantics. In particular, one cannot replace the legal activation set by every element of its span as if every linear combination were an executable input.

A sampled space V_sample uses only collected events. It is a lower bound on V_M when every sample is legal. If it already has the full ambient dimension, it does certify that V_M is full; a deficient sampled rank alone is not a certified upper bound. A certified superspace U_M is instead a subspace for which a proof establishes A_M subset U_M; then V_M subset U_M. The directions of these inclusions are opposite.

## 5. Bias and affine homogenization

If the matrix operation is y=W_M a+b_c, state which parameters are represented. For geometry of the shared W_M with biases fixed separately or different at different sites, the ambient space is K^{m_M}. One must not claim that [W_M b_c] is one globally shared block when the biases are not shared. Only when one declares a jointly shared affine parameter block [W_M b_M], define

$$
\widetilde a=(a,1)\in K^{m_M+1},\qquad
\widetilde V_M=\operatorname{span}_K\{(a,1):a\in A_M\}.
$$

The final coordinate is a genuine constant input to the mathematical affine representation; it is not an extra free runtime input. It may be an analytical homogenization rather than an additional operation in the implemented kernel. Separate FP bias-first execution must still be modeled with its original order.

For nonempty A, aff(A) is the set of affine combinations with coefficients summing to one. Theorem A1.4 proves dim(span{(a,1)})=dim(aff(A))+1. Thus appending a constant can reveal an affine relation even when the unaugmented linear span is full; it does not create a zero constant coordinate or automatically add one to the *linear* rank of A. For A empty, both activation spans are zero and the nonempty formula is not invoked.

## 6. Sound invariant-space certificates

An invariant is always relative to named operations. It is not enough to say that a space is "invariant" without specifying those operations.

One certified construction uses a rational state feature vector x in Q^n and its lift z=(x,1) in Q^{n+1}. A finite operation family J models every admitted step. A certificate supplies rational matrices B_j, error subspaces E_j, initial-vector generators Z_0 and call-observation maps H_c. It must prove:

- Every admitted initial lifted feature lies in span_Q Z_0.
- For every reachable admitted step in mode j, its actual decoded successor satisfies z' in B_j z+E_j.
- Every emitted physical activation at site c belongs to H_c z+F_c, or to one of a supplied finite family of such expressions. The call-error/input subspace F_c must be explicit. If the observation depends on the current external input, that input is included in the feature state, is incorporated into a finite mode, or is covered by a proved F_c; it cannot be omitted.

The B_j and H_c are **rational algebra maps**. They do not assert that actual FP arithmetic is distributive or linear. For exact affine state transitions x'=A_j x+b_j, the usual B_j is [[A_j,b_j],[0,1]], with E_j={0}. For rounded transitions, nonzero rounding discrepancies must be enclosed in E_j, unless exactness has already been proved on the domain. A full coordinate error space is valid but may destroy every useful rank bound.

Starting from U_0=span(Z_0 union all E_j), define

$$
U_{k+1}=U_k+\sum_{j\in J}B_jU_k.
$$

At stabilization U_*, it is invariant under every B_j and contains every E_j. The activation superspace is the sum of H_c U_*+F_c over all sites using M. U_* is the invariant **state-feature** space under the B_j family. Its derived activation superspace need not itself have an induced transition or any invariance property; it is a proved container, which is all that the activation-span bound requires. Ignoring mode guards is conservative: it allows extra operation sequences but does not remove legal ones. A tighter location-indexed certificate can use a separate space per program location with inclusions along every transition edge.

The real and rational activation ranks for a fixed format agree. Ranks across BF16 and FP32 need not agree for general floating networks: format-specific reachable activations can differ. Agreement across formats requires a separate P1 exact-simulation argument for the relevant recorded activations, or explicit exhaustive verification for the selected instance.

This is a *sufficient* construction, not an assertion that every Boolean/ReLU/rounded transition has a small affine description in the chosen features. Arbitrary finite transitions do admit a finite exact one-hot configuration lift, but its dimension can be the entire state-space size. That construction establishes existence of a finite algebraic model, not practical efficiency.

## 7. Evidence labels and round boundary

- **Proof:** a handwritten mathematical argument with explicitly stated assumptions.
- **Exhaustive model check:** every state/input/call in a stated finite model was enumerated with a specified oracle. This can establish an exact span for that model when enumeration completeness and step semantics are justified; it does not establish the implementation for all possible programs.
- **Finite SMT:** only the exact encoded bounded obligation and solver assumptions, if any such queries are executed. No SMT result is presumed in this definition document.
- **Sampling:** only the recorded finite draws/traces. Low sampled rank is not a global rank upper bound.
- **Native arithmetic check:** only the operations and backend actually executed; software BF16 is recorded separately from CPU FP32. No GPU, native BF16 or full proof-assistant result is implied.

Null spaces, annihilators and complements are discussed only as algebraic properties of these spaces. This round does not apply a weight patch, implement P2-A2, or infer FP bitwise preservation from an exact rational/real zero dot product.
