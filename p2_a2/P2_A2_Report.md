# DMWK P2-A2 research report

## Result and scope

The requested A2 work is complete under four explicit conditional contracts. Exact rational projection and the complete linear annihilator space have been constructed and proved. Numerical implementations quantify the errors of the projector, candidate generation, committed weights, and execution separately. A fixed shared-matrix system admits a nonzero stored update that changes an A-track output while leaving every protected D trace unchanged for any finite horizon. Arbitrary projected BF16/FP32 patches do not receive this last guarantee.

The main unresolved issue is the size and usefulness of the executable safe family for less restricted architectures. A positive algebraic complement dimension is necessary for a nonzero globally annihilating linear update, but it does not by itself provide a storable, useful, bitwise-safe edit. A2 gives exact statements and counterexamples delineating this gap, rather than treating numerical orthogonality as its solution.

All research text in this delivery is English; the user's complete original Chinese plan is preserved unchanged. This invocation does not start P2-A3, publish files, change any existing repository, or rerun previous-stage suites.

## Inherited premises and objects

For one physical shared weight matrix, fix D, all protected call sites, their common input-coordinate frame, permitted initial states and external input histories, encoding, numerical policy, and deterministic schedule. From P2-A1, obtain a rational generator matrix H whose real column space contains **all** protected activations over all permitted finite prefixes, or a proved conservative superspace. A sample matrix without an upper-inclusion proof does not satisfy this premise.

Let H be d-by-m, V=col_R(H), and r=rank_Q(H)=rank_R(H). Exact computation uses `Fraction`; accepted finite floating words decode to exact dyadic rationals. The span and Euclidean orthogonality are over the reals. The finite floating activation set is not asserted to be a real vector space. Local call-site generators must be merged before protecting shared storage. Fixed biases are separate; jointly editable affine blocks require augmented activations (h,1), with the declared bias reduction order still respected.

The existing activation-space certificate concerns the original fixed program. An arbitrary update can change later activations or control flow. Thus a one-call annihilation identity is not automatically a whole-program proof. The structural construction below establishes its own closed Boolean invariant and excludes that circularity.

[Definitions](P2_A2_Definitions.md) specifies all interfaces. The baseline covers all 17 existing P2-A1 top-level files and three referenced P1 source files. All **20 dependency hashes** remained unchanged through the main and reproduction runs. No P1/P2-A1 suite was launched.

## Four proved results

These are mathematical handwritten proofs in [P2_A2_Theorems.md](P2_A2_Theorems.md), separately reviewed. Finite implementation evidence is listed later.

### T1: exact orthogonal projection

For a full-column-rank basis B of V,

\[
P_\perp=I-B(B^TB)^{-1}B^T.
\]

The Gram matrix is positive definite on its coefficient space. The resulting rational matrix is symmetric and idempotent, annihilates V, has image V-perp and rank d-r, and is the unique Euclidean orthogonal projector onto that complement. A full basis N of ker(H^T) gives the same operator N(N^TN)^(-1)N^T. Zero rank gives I; full rank gives 0. Duplicate, zero and dependent generators do not invalidate either basis construction.

### T2: all algebraic updates and useful response

\[
\mathcal U_V=\{\Delta:\Delta V=0\}
 =\{GP_\perp:G\in\mathbb R^{d\times d}\},
\quad \dim\mathcal U_V=d(d-r).
\]

Every such update obeys rank(Delta)<=min(rank(G),d-r). The dimension of this matrix space differs from the rank of one update. For h_A outside V, set z=P_perp h_A. For any desired nonzero response y,

\[
\Delta=\frac{y z^T}{z^T h_A}
\]

annihilates V and maps h_A to y, since z^T h_A=||z||^2>0. If h_A is in V, no such protected linear update can change that input. A particular nonzero update can also miss a particular h_A outside V.

This establishes a nontrivial **algebraic** capacity theorem. It does not say those coefficients fit a target format or preserve a floating instruction trace. A conservative superspace can reduce this capacity; merging local spaces can eliminate it completely.

### T3: actual update and execution perturbation

Distinguish the exact projector P, decoded approximate projector Q, actually generated candidate D_hat, and stored endpoint W'. Define

\[
E=Q-P,\quad A_{\rm gen}=\widehat D-GQ,\quad
S=W'-(W+\widehat D),\quad \Delta_{\rm eff}=W'-W.
\]

These are exact differences of decoded values. For h in V,

\[
\Delta_{\rm eff}h=GEh+A_{\rm gen}h+Sh.
\]

If e and e' are the old and new execution errors relative to their exact products (including the same fixed bias), the measured output change is this sum plus e'-e. A certified upper bound is therefore

\[
\|\widehat y'-\widehat y\|_2\le
\bigl(\|G\|_2\|E\|_2+\|A_{\rm gen}\|_2+\|S\|_2\bigr)\|h\|_2
+\epsilon_{\rm old}+\epsilon_{\rm new}.
\]

The implementation uses exact rational squared Frobenius norms and upward dyadic square-root enclosures, giving conservative upper bounds without assuming that an SVD estimate is certified. Local rounding errors of each performed product and sum telescope exactly; their absolute-value sums also apply to admitted subnormal results. A gamma_(2d) relative-error bound is offered only when each operation satisfies that model and 2du<1. Nonfinite results are refused rather than assigned finite error bounds.

The 40 seeded numerical certificates are **pointwise**. They are not uniform bounds over all reachable inputs or a long-horizon stability theorem. A zero residual on H does not itself certify floating execution on every real linear combination, even when that combination is a legal stored input. A nonzero real norm bound says nothing about signed-zero equality or arbitrary finite-horizon bit preservation.

### T4: one nonzero structurally safe update mechanism

Both tracks use stored

\[
W=\begin{pmatrix}-1&0\\0&\theta\end{pmatrix},\qquad b=(1,0)^T.
\]

Only theta is editable. The protected fixed sparse graph computes a Boolean toggle/hold recurrence from the same old snapshot:

\[
n=1+(-1)q,\quad \bar u=1+(-1)u,\quad
q'=\bar u q+un,
\qquad q,u\in\{0,1\}.
\]

The protected graph never reads the editable cell: this is dependency exclusion, not cancellation involving theta times a numerical zero. All performed protected intermediates are exactly representable. A input (0,a), with a in {0,1}, reads theta through the declared sparse route. Replacing theta=1 by theta=2 is a nonzero stored edit and changes the legal A response at a=1 from 1 to 2 in both formats.

The update interface validates the complete replacement word bank before immutable publication. Protected writes, unsupported routes or arithmetic policies, malformed/nonfinite words, negative zero, stale versions, and invalid audit objects are refused with no state change. A validated audit cannot invoke user callbacks through counter or list subclasses. Snapshots and synchronous state commits preserve bits. Rejected updates are not counted as accepted safety examples.

An induction on the common trusted instruction schedule and subsequent ticks proves equality of protected raw-word states and outputs for **every finite number of steps**, with the same admitted initial state and protected input sequence. This conclusion follows from the proof, not extrapolation of finite traces. A-to-D feedback, changed scheduling, shared mutable scratch, concurrent API calls, arbitrary private runtime mutation, and compiler-introduced dependencies are excluded.

Here d=2,r=1: the full algebraic update space has dimension two; the implemented structural mask retains one coordinate. This is a deliberately smaller sufficient safe family, not an optimality claim or a general dense matrix-kernel solution. The shared storage and fixed sparse read selection are explicit in [the structural contract](P2_A2_Structural_Contract.md).

## What the numerical and adversarial evidence changed

[The counterexample catalog](P2_A2_Counterexamples.md) covers every requested class. Three distinctions are particularly consequential.

1. **Nonrepresentable projection does not imply kernel leakage.** For V=span(1,1,1), P=I-J/3 cannot be stored exactly. Its rounded BF16 and FP32 coefficients nevertheless retain exact zero row sums, and the specified execution gives zero at (1,1,1). Idempotence is lost. The separate six-coordinate construction I-J/6 has genuine exact decoded residual -3/1024 per row in BF16 and -3/67108864 in FP32.
2. **A successful basis probe does not establish execution on the span.** For the rounded thirds projector, both (1,1,1) and (eta,eta,eta) are explicitly legal in the counterexample, where eta is the format's smallest positive subnormal. The exact decoded product is zero for both. Actual separate-RNE execution on the second input gives raw word `0x1` in every row. The small products round individually; linearity of real matrix multiplication does not transfer to this rounded instruction sequence.
3. **The actual patch is W'-W.** With precision p=8 or 24, take one old row (2^p,0), ideal update (1,-1), and protected input (1,1). Ideal annihilation is exact. Final commit rounding produces (2^p,-1), so the effective update is (0,-1). The protected exact residual and the observed output difference are -1. Checking only the proposed increment would miss this failure.

Other recorded cases include full rank, locally low-rank calls whose union has full rank, exact zero dots executing to -1, numerical effective-rank truncation, updates that have no useful target response, and changes caused by reduction reordering or modeled one-round FMA. The latter FMA calculation is software reference evidence, not native hardware FMA testing. These general finite-value examples need not belong to the P1 Boolean compiler's restricted activation language; they invalidate universal claims beyond that language, not its stated small-integer closure theorem.

A further exact capacity example distinguishes standalone increments from stored endpoint differences. For a=2^p-1, H columns (1,a,0) and (0,1,a) have a one-dimensional complement generated by (a^2,-a,1). No nonzero vector on this line has three individually storable p-bit components, by the odd-significand proof. Yet representable endpoints (-1,0,0) and (a^2-1,-a,1) have exactly that difference. This is not a bitwise-execution guarantee for those endpoints.

## SVD, precision and review corrections

Exact rational rank is the reference. SVD diagnostics separately record input conversion, exact rank of original and converted matrices, precision, singular values, cutoff, selected rank, conditioning estimate, residuals and time. They include FP64, explicitly dispatched FP32, and subsequent BF16 quantization. Sign changes or orthogonal changes within the same ideal singular subspace preserve its exact projector; cutoff decisions and floating evaluation can still differ.

Review found that NumPy 2.3.5's public SVD path promoted float32 inputs internally and cast outputs back. A float32 output dtype therefore did not establish single-precision computation. The final reference selects the compiled `f->fff` gufunc explicitly, validates its availability and output dtypes, and pins NumPy 2.3.5. This is a version-specific experimental dispatch, not a certification of compiled LAPACK internals.

Review also corrected a cutoff-comparison trap from weak scalar conversion, an overly restrictive optional increment-storage probe, and callback-capable audit contents. Nonfinite solver outputs and thresholds are refused; an unavailable condition diagnostic carries a reason rather than JSON Infinity. The independent report records the findings, fixes and regression evidence. No blocking contradiction remains within the final four stated contracts; that is an audit conclusion with limited evidence, not formal certification of the host stack.

## Actual validation and reproducibility

Primary evidence is [verification_results.json](verification_results.json). All three planned sections completed, with no unexecuted section or unexpected failure. Seed: **20261114**. Environment: Python **3.12.14**, NumPy **2.3.5**, Linux x86-64. The main recorded wall time was approximately **1.070 s**; it is an observation of this small run, not a benchmark or scalability claim.

| Route | Actual finite coverage | Result |
|---|---|---|
| Exact algebra | 3,377 explicit checks; all 81 ternary 2-by-2 and 64 binary 2-by-3 matrices; 60 seeded rational instances and 60 seeded covariance cases; all six S3 coordinate permutations; seven refusal cases | Passed |
| Numerical | 256 checks; 20 SVD cases; 40 seeded pointwise perturbation certificates; BF16/FP32 quantization, rank, commit, execution and subnormal cases; 15 expected refusals | Passed |
| Structural | 135,773 outer checks; all 65,536 BF16 words (65,279 admitted, 257 refused); 526 FP32 boundary/seeded words (520 admitted, six refused); 74 explicit transaction refusals | Passed |
| Stateful production traces | Per format: both initial bits and all 32 length-five inputs, giving 64 traces, 320 ticks and 320 commits; an additional 256 seeded feedback ticks with 86 commits | Passed |
| Independent review | Independent cofactor/minor oracle on 512 binary 3-by-3 matrices and six edge/rational fixtures; independent word-search RNE; 128 paired traces, 640 tick pairs and 640 commits across formats; 28 rollback refusals; independent numerical and threshold cases | Passed |

These counts have different units and overlap in subject matter; they are not added into a universal confidence score. The structural CPU FP32 run performed 9,316 audited scalar operations (5,254 multiplies and 4,062 adds); the BF16 operations use software RNE. The reviewer used different finite oracles, not the main verifier's assertions. [review_results.json](review_results.json) records its own costs and source hashes.

A second main run from `/tmp` completed in approximately **1.114 s**. Every non-timing field matched, including results, residuals, counts, formats, source hashes and backend metadata. `-O`, `-OO`, and a nonexistent P1 root were each refused before any verification section; the primary result stayed unchanged. See [driver_checks.json](driver_checks.json). Driver refusals are separately recorded as intentional failed invocations.

No SMT query or proof-assistant run occurred. The exact-rational assertions, exhaustive finite domains, random samples, native FP32 probes, and handwritten proofs are explicitly different evidence classes. Sources and results are indexed by SHA-256; hashes establish file identity, not truth. [The evidence map](P2_A2_Evidence_Map.md) links each claim to its supporting proof, implementation and finite output.

## Cost, capacity and coordinate behavior

For an explicit d-by-m rational H and basis rank r, dense elimination uses O(dm min(d,m)) rational field operations. Forming and inverting B^TB adds O(dr^2+r^3); forming the dense projector adds O(d^2r). These are algebraic operation counts, not unit-cost bit complexity or exact instrumented totals. Intermediate numerator/denominator sizes and rational reduction costs matter. The recorded exact tests observed at most 54-bit numerators and 53-bit denominators in their audited construction operations; this is not a universal growth bound or process-memory measurement.

| Representation or route | Storage and work | Capacity/limit |
|---|---|---|
| Explicit exact projector | d^2 rational entries; dense construction terms above | Exact complement rank d-r, possible coefficient growth |
| Basis/Gram action | O(dr+r^2) entries, O(dr+r^2) field operations per vector after setup | Same ideal operator; null-basis alternative uses d-r instead of r |
| Dense projected patch | O(d^2) endpoints regardless of projector storage; GP costs O(d^3) naively, or O(d^2r+dr^2) with a cached Gram representation | Algebraic space dimension d(d-r); storage and execution impose further restrictions |
| Numerical SVD | Thin/core decomposition typically O(dm min(d,m)) arithmetic; forming the d-by-d projector adds O(d^2r), with implementation-dependent factor/workspace costs | Effective rank depends on precision and threshold; no safety authorization |
| Structural mechanism | Constant-size 2-by-2 matrix fixture; complete small-bank validation and snapshot publication | One writable coordinate, strictly smaller than the two-dimensional algebraic family |

The SVD estimate does not include the cost of completing full orthogonal factors; the implemented full-factor diagnostic and explicit projector have those additional output/workspace costs. The structural row describes the delivered fixture, not a measured asymptotic algorithm for arbitrary masks. Explicit weights can dominate memory even when the projector is matrix-free. No large-scale performance advantage or hardware optimum is claimed.

For an input-coordinate permutation Pi, the exact projector transforms as P'=Pi P Pi^T. Input-only relabeling requires W'=W Pi^T and the corresponding patch transformation; simultaneous input/output relabeling requires conjugation of W and the patch. The exact proof and tests cover this covariance. They do not equate reordered floating reductions or implement historical patch migration.

## Remaining boundaries and next handoff

The all-time protection theorem applies to the specified sparse trusted API, fixed D, same admitted initial state/inputs/schedule, bit-preserving storage and canonical-zero RNE policy. GPU, native BF16, dense GEMM substitution, alternative fusion/reduction policies, concurrent transactions, hostile private-memory mutation and complete compiler refinement are not certified. CPU FP32 results concern the operations actually performed in this environment.

The general numerical bound still needs a proved legal-input family and uniform error control to become a global quantitative guarantee. Approximate SVD rank is not an activation-space certificate. Extending the safe family while preserving useful A behavior, realistic sharing and all-time state invariants remains open. No novelty or performance claim is made. Original references were checked where identifiable; incomplete source labels were not used as evidence. See [References](P2_A2_References.md).

The next stage should begin with three explicit inputs: a globally justified protected activation contract, the actual committed endpoints/effective difference, and an execution-level acceptance certificate tied to a fixed graph and numerical policy. It must retain a nonzero A-response witness and treat failure to certify as refusal. [The saved handoff](P2_A3_Handoff.md) gives a proposed next-stage plan; it does not constitute P2-A3 implementation or completion. This round stops at the A2 delivery point.
