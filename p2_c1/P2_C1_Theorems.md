# P2-C1 theorems — Compiling a reserved deterministic/learnable bank

These are conditional handwritten proofs using [Definitions](P2_C1_Definitions.md) and the fixed [compiler interface](C1_Compiler_Interface.md). K denotes Q or R. Stored words use the declared canonical finite BF16/FP32 policy; actual differences are differences of exact decoded endpoints. No theorem certifies arbitrary external code, an unspecified optimization or a general host/hardware execution.

## T1 — Boolean lowering, complete sites and source correspondence

Define the derived Boolean macros, after each child expression has been evaluated once in source order, by

    OR(a,b)  = NOT(AND(NOT(a),NOT(b))),
    XOR(a,b) = AND(OR(a,b),NOT(AND(a,b))),
    MUX(c,a,b) = OR(AND(c,a),AND(NOT(c),b)).

These use respectively 4, 7 and 7 AND/NOT primitive calls, excluding the calls evaluating their child expressions. NOT and AND each use one primitive. A leaf uses no primitive. Lower all next-state expressions in state-port order, then all output expressions in output-port order, recursively left to right. Every primitive gets a fresh deterministic site identity and an output wire referring only to previously available wires.

**Claim.** For every accepted source p, Boolean q,u, and each source expression e, the lowered expression's result is [[e]](q,u). Every source operation has precisely its specified lowering calls in the canonical graph; every such call is reachable in the eager graph evaluation. The graph returns Next_p(q,u) and Output_p(q,u) without dependence on any partial next-state write.

**Proof.** A constant or reference leaf has the same Boolean value by the input/state/wire definition. NOT and AND preserve the meanings by their primitive definitions. If child meanings agree, De Morgan's law gives the displayed OR identity. For XOR, when both arguments are zero its OR factor is zero; when exactly one is one the OR factor is one and the AND factor is zero; when both are one the negated AND factor is zero. Thus the result is exactly XOR. For MUX, c=1 leaves the term a and makes the other term zero; c=0 leaves b and makes the first term zero. The four identities prove the structural induction step for every constructor. Eager evaluation is legitimate because all children are pure and Boolean-total, and its fixed traversal does not depend on the values.

For site completeness, perform the same structural induction on the emitted list. A leaf emits no site; each nonleaf concatenates every child's complete list in order and then its fixed macro list, with fresh identities. Thus no source occurrence is omitted and no additional external occurrence is accepted by this construction. Each local macro references only its already constructed child results and earlier local sites. Concatenating top-level expression lists preserves this property. The graph takes all state/input leaves from the same old snapshot and publishes state only after every result is computed, so every result equals its source old-state semantics. ∎

This statement is about the particular constructor and complete-source reconstruction. An arbitrary external graph can delete an entire expression and still pass checks on its remaining local sites. Local structural validity alone therefore does not imply this theorem.

## T2 — Exact shared gate execution and Boolean closure

Let B have rows (1,1,-1) and (-1,0,1). On a,b in {0,1}, evaluate each row against (a,b,1) with fixed zero bias, ascending separate multiply/add, and then coordinate ReLU. The two canonical word outputs are respectively a AND b and NOT a in BF16 and FP32. NOT sites use b=0.

**Proof.** For the first row the products are a,b,-1. Starting at +0, the partial sums are a, a+b and a+b-1. Their values belong to {-1,0,1,2}; all products, coefficients and sums are exactly representable in both formats. Correct nearest-even rounding therefore changes none of their real values. ReLU sends the final values -1,0,1 to 0,0,1, which agrees with AND. The second row products are -a,0,1; its partial sums are -a,-a,1-a. They are exactly representable and ReLU leaves the Boolean final value unchanged. The explicit zero policy normalizes any arithmetic signed zero to canonical +0; 1 is canonical +1. No overflow or subnormal operation is required. ∎

Each primitive computes both rows: six products and six additions, plus two coordinate ReLUs and its declared wire selection. The zero coefficient in the NOT row does not authorize a different instruction graph. Sparse D row/column selection is itself part of the fixed contract.

**Corollary T2(a): finite-tick compilation correctness.** Under exact T2 operations, bit-preserving reads/writes and same-snapshot evaluation/publication, the compiled D machine agrees word for word with the encoding of the source state/output trace for every allowed initial state and every finite legal input sequence.

**Proof.** At a tick, T1's site induction with T2 replaces ideal gates by their actual exact words and keeps every intermediate result Boolean. Thus decoded next state/output equal their source values and their stored encodings are canonical. At time zero the admitted source and runtime initial states are encoded identically. Induct over ticks: equal old state and common legal input give equal output and next-state words; Boolean closure supplies the premise for the next tick. The induction has no fixed finite upper time bound. It assumes every tick continues to satisfy the contract and proves neither physical fault immunity nor source termination. ∎

## T3 — Global activation containment across every shared call

For every emitted D site at every legal tick,

    h=(a,b,1,0_c) in H_*={(a,b,1,0_c):a,b in {0,1}}.

Consequently all deterministic activation sets lie in V_*=K^3 x {0_c}, of rank three. The union over every Boolean state/input pair and every emitted call is a computable conservative envelope for all reachable activations. Exact enumeration of that finite envelope does not become a claim that every enumerated state is reachable from the declared initial subset.

**Proof.** Initial source states are Boolean and inputs are Boolean by admission. T1/T2 show every child wire feeding a gate is Boolean. Input preparation places its two declared operands (or zero for a NOT's second operand), the exact affine one, and fixed A-coordinate zeros in the declared positions. This proves membership in H_* for each site. T2(a)'s state induction makes the claim hold at every finite tick and for all legal input histories. All physical aliases are the compiler-generated sites of the same bank, so the union includes every deterministic use admitted by the source-to-graph theorem.

The vectors (0,0,1,0_c), (1,0,1,0_c) and (0,1,1,0_c) belong to H_*; taking their differences yields the first two coordinate vectors and the first vector is the third. They span K^3 x {0_c}; all vectors have zero A coordinates, so its dimension is exactly three. The all-Boolean-state envelope contains every reachable state by Boolean invariance, and enumerating its finite Cartesian product with all legal inputs and all generated sites gives the envelope exactly. A proper allowed-initial-state subset need not reach every envelope state. ∎

A zero-site program has actual generated-call span rank zero even though the compiler deliberately reserves V_* of rank three. NOT-only programs may have rank at most two. A diagnostic smaller rank does not silently grant extra writable cells; a different geometric authorization would require its own actual-endpoint/graph proof.

## T4 — Structural capacity, construction budgets and representable cardinality

Let n=2+m, d=3+c, with m,c>=1. Define

    M={Delta: Delta is zero outside the lower-right m-by-c block}.

Then M is a K-vector space of dimension mc. Every Delta in M annihilates V_*, and rank Delta<=min(m,c). With a freely chosen rank-q generator in the editable block the maximum rank is min(q,m,c), attained in unconstrained exact algebra. The full-output annihilator of V_* has dimension (2+m)c, generally larger than mc.

**Proof.** The mc independent editable coordinate matrices form a basis of M. Multiplication by a vector in V_* reads only the first three columns, all zero in Delta, so Delta V_*=0. Its image is contained in the last m output coordinates and its nonzero domain has dimension c, giving the rank bound. Put ones in any min(q,m,c) independent editable diagonal positions to attain the cap. The unrestricted full-output annihilator may arbitrarily fill all n rows of the last c columns and must have zero first-three columns; hence dimension nc=(2+m)c. The structural compiler freezes the additional 2c upper-right cells by design. ∎

These are stronger full-output algebraic constraints than merely preserving selected final source outputs. For example, if only the top two linear outputs were protected and arbitrary matrices allowed, the condition on V_* alone would fix six coefficients and leave nd-6 exact degrees. That different observational family is not the compiler's allowed endpoint set and is not classified as a BIT-safe program family here.

### T4(g): the structural mask is a certified geometric projector

Let R_A be the diagonal output-coordinate selector with zeros on the first two rows and ones on the remaining m, and P_A the diagonal input-coordinate selector with zeros on the first three columns and ones on the remaining c. Define S(G)=R_A G P_A. In exact algebra this is the Frobenius-orthogonal projection onto M: it is linear, idempotent, self-adjoint, and is the unique minimizer of ||G-U||_F over U in M. It satisfies rank S(G)<=min(rank G,m,c) and S(G)V_*=0.

**Proof.** The formula keeps exactly editable cells and zeros every other cell. Linearity is entrywise. Applying the same mask twice has no further effect, and the Frobenius inner products <S(G),H> and <G,S(H)> both sum G_ij H_ij only over editable cells. For any U in M, squared distance decomposes into the fixed sum of squared G entries outside the mask plus the sum of squared differences G_ij-U_ij inside; the latter is uniquely minimized by U_ij=G_ij. Multiplication on the left/right cannot increase rank and the selector ranks are m,c; annihilation follows because P_A V_*=0. ∎

This gives a geometric interpretation of the supported axis-aligned route, not support for arbitrary rotations or general approximate projectors. Its final ideal candidate still must become an admitted stored endpoint and pass the immutable-cell/current-context checks. Projecting only an earlier raw gradient does not authorize later optimizer, decay or storage steps.

### T4(a): finite storage, A-totality and exact structural cardinality

Let E_struct be all physical banks with the fixed B/cross-block words and arbitrary canonical finite A-block words. On the legal A input set {0,e_1,...,e_c}, every bank in E_struct is total and returns exactly zero or the selected stored A column. E_struct has exactly N_F^(mc) members. Every member is D-BIT equivalent under the compiled graph/domain, and the complete A-basis output signature is injective on E_struct.

**Proof.** At A input zero every product is a finite coefficient times zero, normalized to +0. At e_j every product except the j-th is zero and the remaining product is the j-th stored coefficient times one, which is exactly representable. Every partial sum is either zero or that one coefficient; hence none overflows, including at Fmax. The identity activation does not change the result. D evaluates only immutable B words, as T2/T3 prescribe, so A word choices do not alter any D gate result. Each of the mc independent cells has exactly N_F choices; the fixed rest contributes no choice, giving the cardinality. Querying each basis input returns each column's words exactly and therefore uniquely reconstructs the editable block. ∎

For an IEEE-like format with eight exponent bits and t fraction bits, finite words number 2*255*2^t. Removing stored negative zero leaves N_F=2*255*2^t-1. Thus t=7 gives 65279 for BF16 and t=23 gives 4278190079 for FP32. This is a counting proof for the structural universe, not enumeration of every format endpoint and not the cardinality of the unrestricted all-matrix BIT class. Its finite set has no real-vector-space dimension. Learning through a particular optimizer can still revisit endpoints or stall.

Moreover, from any endpoint in E_struct, an actual stored structural increment of any integer rank h with 0<=h<=min(m,c) exists. Choose h distinct editable diagonal positions; at each chosen position replace a nonzero old word by zero, or a zero old word by one, and leave every other word unchanged. Each selected exact difference is nonzero, so the diagonal difference has rank h. Every new word is admitted, and T4(a) preserves totality/D behavior. This shows attainable stored rank for the unrestricted structural transition universe; it does not assert that a fixed small-step optimizer can reach that endpoint or improve its objective. An outward proposal at Fmax may still fail even though a downward safe endpoint exists.

### T4(b): concrete resource sufficiency and limited necessity

For a lowered source with g primitive sites, this construction requires two D rows, three D columns, dense stored shape (2+m)(3+c), and g D calls per tick. It makes 12g floating binary D operations per tick, plus 2g ReLUs and Boolean wire/state/output handling; each A call makes 2mc binary operations. At most 5+mc coefficients are structurally nonzero (five in B); fixed zero words and dense storage are separately counted. Source/D state size s is not reduced by the constant gate-bank dimensions: the graph, wire storage and repeated calls carry the program.

Under this construction, resource limits below any of those declared requirements are insufficient, and requested unrestricted structural response dimension above mc or individual update rank above min(m,c) is impossible. Conversely if all limits cover the emitted graph/layout and the response minima do not exceed these structural maxima, zero initialization or compatible representable initial anchors give a construction satisfying the corresponding reservation budget.

**Proof.** Count the fixed row/column partition and the g emitted primitive invocations. T2 counts each D call; the A graph has m rows and c products/additions per row. B has five nonzero entries. T4 gives the algebraic maxima, and T4(a) supplies a finite total endpoint such as A=0. For representable compatible anchors, fill the specified A columns and the remainder with zero, as proved in T5. These observations prove the stated construction-level necessary and sufficient resource checks. ∎

A resource refusal is not an impossibility result for every compiler or encoding. Nor does a shared constant-size gate bank show that an arbitrary program is embedded into a low-dimensional activation space at no other cost. Eager graph size and state/wire storage remain. The bounded front end has one or two state ports, zero to two input ports, one or two outputs, expression depth at most eight and at most 256 source node occurrences. A dimensions lie in 1..2 and the emitted-call implementation cap is 2048. These finite limits bound exhaustive envelope work; they are not universal minimality claims.

In particular the compiler output's program representation is graph plus wires plus bank, not B alone. A straightforward eager interpreter retains g Boolean result words and old/new state buffers of s words each, in addition to input/output and constant/row scratch. Graph metadata is O(g+s+i+o) records before identifier/string bit costs. Storing dense words, storing fixed zero biases, retaining source/certificate metadata and staging a transaction have additional distinct costs. No minimal memory layout or hardware-optimal gate schedule is proved.

## T5 — Response compatibility and initial-anchor acceptance

For structural updates U in K^(m by c) and target columns Z in K^(c by p), the response image {UZ} has dimension m rank Z. A prescribed response R is feasible iff

    Z alpha=0 implies R alpha=0.

When feasible, the minimum rank of an implementing U is rank R; a freely chosen rank-q update can implement it iff rank R<=q. A nonzero update can have zero response on all those targets when rank Z<c.

**Proof.** Each row of U acts as a linear functional on the rank-Z-dimensional span of target columns, giving rank Z independent response coordinates per row. Necessity follows by applying U to a zero relation. Conversely define L(Z alpha)=R alpha; the relation condition makes this well-defined. Extend L by zero on a complement of im Z. Its image is exactly im R, hence its rank is rank R. Any U realizing R has rank at least rank(UZ)=rank R. A nonzero map supported on a complementary input direction exists when rank Z<c and is target-silent. ∎

For general protected V and homogeneous X, any Delta V=0 necessarily satisfies X alpha in V implies Delta X alpha=0. Factoring through K^d/V gives the inherited sufficient relation criterion for the unrestricted annihilator. The structural mask may be more restrictive, so this broad condition alone is not its endpoint certificate.

### T5(a): supported initial A assignments

The compiler's optional response request assigns rational output vectors to a finite list of legal A inputs zero or basis vectors. It has an exact structural solution iff every requested zero input has zero output and duplicate basis inputs request identical outputs. The selected solution fills each requested basis column accordingly and every unrequested column with zero. The selected solution is a stored exact endpoint iff every requested coefficient has an admitted exactly representable word; this is checked rather than silently rounded. Its actual A graph then returns those requested words exactly.

**Proof.** A linear map sends zero to zero and has one fixed image for each basis vector, proving necessity. Independent basis columns may be assigned arbitrarily, so the stated fill gives a solution when requests are consistent. A required exact coefficient can be a stored word iff it belongs to the format's decoded alphabet. T4(a) then proves actual graph equality on the requested inputs. ∎

For example an exact request for coefficient 1/3 is rejected in either binary format; rounding it to a nearby word would implement a different initial anchor. Saturated finite coefficients are representable and total on the one-hot A domain, but an outward proposed value beyond the finite range has no stored endpoint. These initial A assignments are not automatically protected immutable tasks during later learning. New protected task admission would require its own compatible-anchor and domain contract, beyond C1's current source protection.

## T6 — Structural endpoint safety and limits of geometric equality

For any two admitted endpoints W(A),W(A'), their exact difference lies in M and annihilates V_*. Every compiled D call, complete D output vector and next-state vector is bitwise equal at the same old state and input under the declared fixed graph. A outputs may differ.

**Proof.** Both endpoints have the same fixed B and cross blocks, so their difference has only the A block A'-A. Apply T4 for annihilation. A D call reads only the same B entries, same prepared D operand words, same bias and ordered arithmetic, same ReLU and result selector. Thus its complete intermediate and output words agree. Induction over the common generated graph and same-snapshot result publication gives the equality of source observations, including every shared call. T4(a) shows a changed A coefficient can produce a different legal basis response. ∎

This proof requires the whole interface, not merely displayed zero blocks. If preparation reads an A value as a D operand, activation mixing reads A rows, a bias changes, a state update reads an A result, a source site is omitted or within-tick publication changes the snapshotted bank, its premises fail. Such changes are rejected by full reconstruction/identity binding rather than deemed harmless because some matrix entries are zero.

### T6(a): exact annihilation is not a floating certificate

On a particular AND(1,1) call, the prepared D input is h=(1,1,1). The old first row (1,1,-1) has exact dot product one. In format precision p=8 or 24, let F=2^p and replace that row by (F,1,-F). Its exact dot product is still one, so the row difference annihilates span(h). But the fixed floating sum computes fl(F+1)=F by a nearest-even tie and then subtracts F, giving zero instead of one. Thus exact equality on the entire one-dimensional call span does not establish BIT equality.

**Proof.** At F=2^p the upward representable spacing is two; F+1 is the midpoint between F and F+2. F has even trailing significand parity, so nearest-even chooses F. All other displayed terms are exact and finite. ReLU keeps the resulting zero rather than the original one. ∎

Conversely, a zero coefficient in the NOT row's b-column can be changed to the smallest positive subnormal eta without changing any legal gate output under the fixed graph. For a=0,b=1, eta+1 rounds to one; for a=1,b=1, -1+eta rounds to -1 and adding one gives zero; b=0 is unchanged. The added row action eta*b is not identically zero on V_*, so this finite-domain BIT-equal example fails the universal ALG condition. It is outside the structural mask and is not authorized by C1 even though this isolated gate observation is BIT equal.

### T6(b): rotations and ReLU

Let R=[[0,-1],[1,0]] and x=(1,-1). Then ReLU(Rx)=(1,1), whereas R ReLU(x)=(0,1). Therefore an arbitrary orthogonal change of coordinates cannot be moved through coordinate ReLU as if it were a permutation symmetry. Exact geometric diagnostics, if exposed, are read-only and do not change the structural BIT gate. Changed graph/rounding policy similarly needs a new proof; a real zero product alone cannot authorize it.

## T7 — Bound compilation evidence is complete only through reconstruction

Assume the trusted parser/compiler deterministically reconstructs the canonical artifact from expected complete source, budget, format, supported initial response request and the fixed structural mode. Its checker accepts an artifact iff its canonical complete value equals that reconstructed artifact. Then any accepted artifact has the same source port/domain identities, every emitted D and legal A site, wire selections, bank layout, fixed words, mask, graph, numerical policy and budget/proof receipts as the compiler output.

**Proof.** Equality of the canonical complete structured value implies equality of every field and nested list item. T1 supplies source correspondence and site completeness for the reconstructed compiler output. Substituting the equal accepted artifact gives exactly those properties. ∎

The compiler itself and its canonicalization/parser belong to the trusted base of this theorem; tests can check that implementation without turning this implication into a full host proof. Hashes alone do not authenticate the expected source or discover omitted external behavior. A caller that supplies a different complete program has requested a different contract; the checker is not an intent-reading oracle.

## T8 — Finite serial update/tick preservation and rejection rollback

Assume one trusted serial owner retains a T7-bound artifact and complete owned snapshot, and the following publication protocol:

1. An initial state is chosen from the compiled admitted set and stored canonically. D inputs are validated against the entire Boolean input domain.
2. A candidate actual stored endpoint is formed before authorization. Its immutable cells, word policy, complete compiler identity and chosen exact contract are checked; valid structural endpoints satisfy T6. Its optimizer/counter/ledger transition is defined and bound.
3. Prepare/commit checking and all possibly refusing work use an unexposed copy. A commit reconstructs the candidate against the current full snapshot, including graph/source/domain/initial relation, endpoint/version, D state/tick, optimizer, schedule and ledgers. A successful operation publishes one fully prepared replacement snapshot. Refusal publishes nothing.
4. A tick reads one old endpoint/state snapshot, executes the complete source graph, and synchronously publishes the resulting state/output effects. A computations and mutable metadata do not affect D through an undeclared path. Numeric read-only receipts are never publication authority.

Then every refused operation leaves the entire owned snapshot unchanged. Every finite event history of accepted updates, refusals and legal ticks has the same D observation trace as the source/original compiled execution under the same admitted initial state, input sequence and trusted tick schedule. Accepted updates may change A outputs, weight words, optimizer and version/ledger metadata.

**Proof.** Before publication, all changed objects are private staged values. Therefore a refusal cannot alter any component of the visible owner. On success the one replacement contains the jointly checked endpoint, optimizer and metadata, so no partial kernel/ledger or endpoint/optimizer state is exposed under the stipulated serial semantics. A stale prepared record fails complete current-snapshot reconstruction rather than restoring old state.

For trace preservation, induct over the event history. At initialization use T2(a). An accepted update changes only an admitted structural endpoint and permitted metadata, leaving D state fixed; T6 supplies the same complete D behavior for any next legal tick. A refusal leaves the entire owner fixed. At a tick, equal source state and input plus T2/T6 and the one old snapshot give equal output and next-state encodings. Boolean invariance reestablishes the next event's premise. Thus the designated D trace is preserved for every finite event prefix. ∎

It would be incorrect to require the full successful-update snapshot to equal an unpatched reference, because its A endpoint/optimizer/version/ledger are intended to change. Conversely checking only D state on refusal would be too weak: the whole owner must roll back. This theorem assumes trusted serial copy-and-publish, not concurrency, crash consistency, arbitrary memory mutation, malicious host subclasses, hardware failures or complete machine verification.

## T9 — Repeated updates and remaining capacity in this construction

For any finite admitted structural endpoint history W_0,...,W_K, every actual increment lies in M and every prefix sum W_j-W_0 lies in M. Neither M's dimension mc nor the absolute structural endpoint cardinality N_F^(mc) decreases merely because K increases. The full-basis A signature class likewise remains fixed. A restricted optimizer proposal can nonetheless round to the same endpoint, fail representability or become unable to improve its chosen target.

**Proof.** M is a linear space, and endpoint differences telescope, so every finite prefix remains in M. All endpoints have the same immutable B/cross words and no historical exclusion is added to E_struct. Hence its definition and T4(a)'s cardinality stay unchanged. The full-basis response function is fixed and injective on that same set. Local proposal/optimizer restrictions concern reachable next edges, not the absolute set. ∎

If every increment additionally has rank at most q, its cumulative rank can reach min(Kq,m,c) in exact algebra by assigning disjoint editable diagonal directions across increments; it is not in general bounded by q. New independently protected A directions would shrink the permitted block-nullspace, but preserving a new task also requires a compatible satisfied anchor at its admission endpoint. These are inherited B4 distinctions, not a C1 implementation of changing protection policies or later coordinate migration.

An executed toy objective decrease shows only that target, optimizer, domain and finite run. BF16 no-op plateaus do not establish algebraic exhaustion. No theorem here promises useful learning for every target, infinitely many distinct learned functions, arbitrary long-host reliability, general bidirectional composition, C3 coordinate migration or C4 hardware correctness.
