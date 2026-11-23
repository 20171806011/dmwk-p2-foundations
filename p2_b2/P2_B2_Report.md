# DMWK P2-B2: strict single-layer perturbation bounds

## Result

B2 supplies conditional mathematical bounds and an executable exact-rational reference for one fixed linear/affine layer. It distinguishes the effective update's action on a reference subspace, activation components outside that subspace, approximate-basis defects, endpoint-generation errors and the two separate floating execution errors. It also supplies read-only numerical-budget receipts. None of those receipts weakens B1's BIT or ALG_AND_BIT publication contract.

The central result is

\[
\|\Delta h\|_2\le\epsilon\|a\|_2+M\|e\|_2,
\quad h=Q_Da+e,\quad Q_D^Te=0,
\]

where `Delta=W'-W` is the exact decoded difference between stored endpoints, Q_D has orthonormal columns, epsilon bounds `||Delta Q_D||_2`, and M bounds `||Delta||_2`. The exact output bound is not the entire floating-execution bound. For two independently rounded evaluations the reference adds both old and new execution-error bounds.

The proofs are [T1-T7](P2_B2_Theorems.md), with [Definitions](P2_B2_Definitions.md) and [Numerical Analysis](P2_B2_Numerical_Analysis.md). They are handwritten conditional proofs, not conclusions obtained by extrapolating a finite test count. This delivery performs B2 only and leaves B3 and all multilayer/long-term work unexecuted.

## Objects and coverage

The layer has n output rows and d input columns, uses full output observation and a fixed bias-first ascending-column sequence of separate products and additions. BF16/FP32 inputs, stored weights and biases are finite canonical words; negative-zero inputs, NaN and infinity are refused. Arithmetic uses RNE, gradual underflow and explicit zero canonicalization. The global interpretation retains fixed D, all shared physical call sites, legal initial-state/input provenance, correct storage and the stated schedule. A single-layer numerical receipt does not independently prove those whole-program premises.

The exact calculations embed decoded words in Q and use real Euclidean/operator norms. The finite word set itself is not a vector space. Effective differences and rational bounds need not be representable in the target format. Registered receipt examples keep bias fixed at zero. General point/box helpers accept explicit old/new finite biases and add their exact difference without changing the bias-first execution order; algebraic homogenization is not permission to reorder that graph.

The reference subspace V_ref and the actual complete legal activation span V_global are separate objects. If proved containment gives every legal h in V_ref, then e is exactly zero for those legal calls. Nonzero e belongs to a separately declared enlarged/perturbed input envelope or a distinct analysis reference. It cannot be justified by merely observing that samples have low rank.

Three coverage levels are explicit:

| Evidence route | Quantifier |
|---|---|
| Point trace | One specified admitted input and two actual finite traces |
| Complete registered-domain maximum | Every listed input at every site in a fixed trusted small domain |
| Analytic box induction | Every admitted raw input satisfying the stated coordinate envelope, with certified operation ranges |

The five receipt registries reuse A3's declared duplicated-bit, split-bit, thirds/tiny-input, endpoint-rounding and shared-axis call sets. The domain union covers every named shared site. The box is built from all those decoded inputs, with explicit inclusion evidence. This is an envelope for single-layer calls; a modified feedback program may leave it unless separate invariant/coverage reasoning is supplied. A caller cannot replace it by a sample subset.

## Geometry and approximate bases

T1 follows by splitting `Delta h=(Delta Q_D)a+Delta e` and applying induced norms. A second independent bound is `M||h||_2`; their minimum is valid. The implementation exposes the separated bound and the uniform alternative explicitly. An exact rational projector Pi_V avoids constructing an irrational orthonormal basis because `||Delta Pi_V||_2=||Delta Q_D||_2` and `||Pi_V h||_2=||a||_2`.

Each term is separately sharp. With V=span(e1), `Delta=(3,0), h=e1` attains 3, and `Delta=(0,5), h=e2` attains 5. Both terms need not attain their extrema simultaneously under one global norm budget. For `Delta=(3,4), h=(1,1)`, epsilon=3 and M=5 give actual change 7, basic bound 8 and uniform bound `5 sqrt(2)`. T1 also proves the sharp joint class envelope, attained by a rank-one real map; its value is 7 for this example. That optional optimum is a mathematical result, not a search over available finite endpoints.

Zero/full protected rank, zero input and zero update are handled explicitly. Algebraic conclusions still require a numerical graph argument when used as execution claims. In particular, identical canonical endpoints/biases deterministically execute identically, and zero input with fixed bias is exact under this policy. A nonzero exact annihilator generally lacks that implication.

For a decoded approximate basis U, let

\[
\|U^TU-I\|_2\le\delta<1,\qquad
\sigma\ge\|\Pi_U-\Pi_V\|_2,
\qquad\alpha\ge(1-\delta)^{-1/2}.
\]

The implemented bound is

\[
\|\Delta h\|_2
\le(\epsilon_U\alpha+M\sigma)\|\Pi_Vh\|_2
+M\|(I-\Pi_V)h\|_2,
\quad\epsilon_U\ge\|\Delta U\|_2.
\]

Gram conditioning and subspace alignment cannot substitute for one another. U=e2 is perfectly orthonormal but wrong for V=span(e1): `Delta=(1,0)` annihilates U while changing e1 by one. U=e1/2 spans the right space but needs the conditioning factor two. U=2e1 has the correct span but fails this sufficient Gram-defect test; refusing that route does not prove rank deficiency or impossibility of another certificate.

No unverified SVD estimate is used as a norm certificate. The reference bounds spectral norm by the square root of the smaller of Frobenius norm squared and `||A||_1 ||A||_infinity`. Rational square-root intervals use integer arithmetic, a normalized dyadic grid and exact rescaling, with exact results for rational perfect squares. Normalization prevents an absolute precision floor from overwhelming subnormal-scale responses. Independent squared/positive-semidefinite checks supply a different finite verification mechanism.

## Error accounting without omitted or duplicated terms

For a specified generator path, the disjoint identity is

\[
\Delta=C_*+E_{repr}+E_{opt}+E_{gen}+E_{store},
\]

with ideal safe increment `C*=G*P`, represented projector P_tilde, computed candidate G_hat and generated pre-storage increment D_hat:

- `E_repr=G*(P_tilde-P)`;
- `E_opt=(G_hat-G*)P_tilde`;
- `E_gen=D_hat-G_hat*P_tilde`;
- `E_store=Delta-D_hat`.

The sum telescopes exactly. A factor route instead uses a named combined represented-factor error, retaining cross terms; it must not add a duplicate projector error for the same discrepancy. The chain helper verifies the identity, not the historical provenance of a supplied ideal optimizer. In particular, hypothetical exact AdamW power/square-root errors are not fabricated from B1's observed host computation.

There are two legitimate analyses: bound actual Delta directly, which already includes every upstream effect, or use a certified decomposition of the named stages. Adding the ledger again to a direct endpoint bound would count the same sources twice. It may produce a larger upper bound, but would misstate the error accounting.

A stored example has four nonzero representation/optimizer/generation/storage terms. On its protected e1 input their separate absolute sum is 5/4, while the actual effective update has zero action. Signed errors cancel. This illustrates both the exact identity and the possible looseness of an attribution bound.

## Two-execution rounding and strict range checks

For a finite row trace, write each product residual as `rho_j=RN(w_j h_j)-w_j h_j` and each addition residual as `tau_j=s_j-(s_(j-1)+p_j)`. Exact decoding gives

\[
\widehat y-(Wh+b)=\sum_j(\rho_j+\tau_j).
\]

The sum of absolute local residuals bounds each row error. For the old and new endpoints separately, these produce nonnegative row bounds beta_old and beta_new. Consequently,

\[
\|\widehat y'-\widehat y\|_2
\le\|\Delta h+\delta_b\|_2
+\|\beta_{old}\|_2+\|\beta_{new}\|_2.
\]

The point implementation records exact signed residuals, absolute local contributions, output words and arithmetic counts. It executes both traces independently. Old and new rounding errors can reinforce or cancel the exact change; neither may be silently omitted.

An independent executed witness makes both terms necessary. Let s be the rounded stored value of 1/3, use old scalar weight s, new weight 2s and input eta. The old output is zero and the new output is eta. The exact change is s eta, the old execution error is -s eta and the new execution error is (1-2s) eta. Including both errors gives the exact upper bound eta; dropping either produces an invalid smaller bound. This witness runs in both software BF16 and local scalar CPU FP32.

The analytic box route does not enumerate the whole floating alphabet. It proves operation ranges inductively for every raw input with `|h_j|<=B_j`. Its local sufficient model is

\[
|RN(x)-x|\le u|x|+\eta/2,\qquad |x|\le Fmax,
\]

where eta is the smallest positive subnormal and u=2^-p. At each product/add the method certifies the exact-argument magnitude, applies this mixed bound, and uses Fmax to cap the finite rounded magnitude. Separate recurrences for the two endpoints yield their global error bounds. A failed range check means this conservative method cannot certify totality; it is not necessarily an observed overflow. The actual point overflow `Fmax*2` is separately refused.

The additive eta/2 is essential: `(1/2)*eta` rounds to zero, whose error violates a relative-only local model. T5 proves an optional gamma_(d+1) specialization only when every local operation on the claimed domain separately satisfies the relative model, remains finite and `(d+1)u<1`. The delivered runtime does not use that specialization to bypass subnormal or overflow conditions.

## Absolute, relative and BIT conclusions

A point relative bound uses a certified positive lower bound on the **actual old output norm**. The maximum absolute old output coordinate is a valid Euclidean lower bound. If it is zero, the relative bound is undefined. A mixed numerical budget uses an explicit absolute term and remains meaningful at zero; it does not manufacture a nonzero denominator.

For a row `(1,-1)` at `(1,1)`, old output is zero. Changing the second coefficient to -1/2 gives actual change 1/2. A relative-only budget cannot cover it, while an absolute budget of 1/2 can. Cancellation and near-zero outputs therefore require visible absolute terms.

Finite canonical outputs lie on the eta lattice. A fully covered infinity-norm difference bound **strictly below eta** implies equal output words. The threshold cannot be weakened to `<=eta`; zero and eta differ by exactly eta. Equal decoded zeros also require the canonical-zero policy to imply equal words. This is a separate theorem, not the meaning of every positive numerical budget, and program-level use still requires A3's same initial state/input/schedule, invariant, interface and covered-effects premises.

The new claim is `read_only_single_layer_absolute_budget`, selecting L2 or infinity norm and a complete-point or analytic-box method. It binds expected endpoints, complete domain, fixed bias/output ports, graph/policy, version and optional snapshot identity. It declares `authorizes_commit=False`, `claims_BIT=False` and `claims_program_noninterference=False`. Canonical recomputation checks consistency against externally expected data; public hashes do not authenticate caller intent or prove a live snapshot is valid.

B1's existing transaction rejects this receipt. Its BIT and ALG_AND_BIT contracts, staged optimizer publication and full rollback remain unchanged. No live bounded-policy path was added.

## Executed counterexamples and bound quality

The [counterexample catalogue](P2_B2_Counterexamples.md) and JSON records separate mathematical constructions, declared finite enumeration and actual fixed-graph arithmetic.

| Case, both formats | Actual observation | What the bound establishes |
|---|---|---|
| Rounded-thirds matrix on all ones | Exact and executed difference zero | The basis point alone proves no full-span BIT claim |
| Same matrix on eta times all ones | Exact change zero, executed change eta per output | Execution rounding must be included; point infinity bound eta |
| Ideal `(1,-1)` update at row `(2^p,0)` | Effective update `(0,-1)`, output change -1 | Actual endpoints replace the ideal proposal; point absolute bound 1 |
| Ordered `2^p+1-2^p` from a zero baseline | Exact change 1, executed change zero | Point bound 2 is conservative because errors cancel |
| Full-rank finite domain with tiny off-diagonal edit | Exact residual nonzero, protected words unchanged | A positive point bound `2 eta` need not imply observed drift |
| Saturated row `(Fmax,Fmax)` at `(1/2,1/2)` | Finite old output Fmax; only the same exact-safe stored row | Storage impossibility remains separate from a numerical budget |

The 12 seeded endpoint pairs per format were evaluated over all nine ternary 2D inputs, with two additional bias cases overall and 26 analytic boxes. Across those selected pairs, the box infinity bound divided by the observed finite-domain maximum ranges approximately 1.00940249-1.01802679 in BF16 and 1.00000014305-1.00000027418 in FP32. Exact rational ratios/slack are saved. These are fixture-specific comparisons; the analytic box covers more inputs than the nine tested points and no optimality or performance claim follows. Ratios at zero observed perturbation are left undefined.

## New analysis of preserved B1 endpoints

B2 reads the frozen B1 training evidence and analyzes its 21 refused candidate pairs without regenerating optimizer steps. All actual protected output differences remain zero, and every exact ALG condition still fails. The following complete-domain L2 upper bounds are positive:

| Frozen B1 category | Pairs | B2 point upper bound | Observed protected difference |
|---|---:|---:|---:|
| BF16 momentum refusals | 6 | 1/256 | 0 |
| BF16 AdamW refusals | 7 | approximately 0.00552427 | 0 |
| FP32 AdamW refusals | 8 | 1/16777216 | 0 |

Each point bound is smaller than its separately proved broader box bound. Their positivity is looseness of a valid upper bound, not a claim that D changed. The original joint refusals and full rollback remain correct. Dense FP32 AdamW still has zero accepted updates in eight attempts and final loss 5/2; numerical-budget analysis does not retroactively turn those attempts into learning progress.

Two new B2 interface-boundary fixtures first establish nonzero B1 optimizer moments with a small accepted dyadic update, then verify that a B2 receipt is refused without changing the complete bank. These are new boundary checks, not reruns of the old optimizer experiment.

## Verification and remaining limitations

The bounds component actually passed **3,419 checks** with **26 expected refusals**. It includes 69 square-root interval cases, seven named plus 64 seeded geometry cases, three approximate-basis positives, two nonzero error ledgers, 218 finite-domain/bias point records and 24 adversarial point records. The receipt component passed **421 checks** with **108 expected refusals**, covering 40 registry/method/norm/format combinations, 16 seeded endpoint pairs, two optimizer-rollback fixtures and all 21 frozen B1 pairs. Root seed is 20261114. Actual costs, arithmetic counts and full scope are in the saved outputs.

The independent checker passed using different exact references: 32 rational square-root intervals, 72 spectral checks by all principal minors, 450 small geometric cases, 48 seeded three-dimensional cases, eight zero/full-space cases, 1,458 exhaustive affine endpoint/input pairs and 128 seeded affine pairs. It reconstructed 24 analytic boxes and tested 384 named box members, 81 mixed budgets, 40 receipts and all 21 frozen B1 pairs (84 registered call observations). The affine/box subseed is 20261115; geometry uses 20261114. Those counts are finite checks, not full-format enumeration or machine verification of the general theorems.

The aggregate runner passed both components in 11.860618054 seconds; its foreign-directory repeat from `/tmp` passed in 12.189905724 seconds. The independent runner passed in 16.060792099 seconds and repeated from `/tmp` in 16.707115789 seconds. All scientific values, refusal reasons, environment fields and source identities matched after excluding only the recorded timestamp/seconds fields. Both standalone component records also match their aggregate counterparts by this rule. These costs describe the actual small runs and are not a benchmark claim.

[driver_checks.json](driver_checks.json) records these comparisons, the expected preflight refusals for Python `-O` and `-OO`, and unchanged hashes and inventory for all 447 prior artifacts. Both optimized-mode probes attempted zero verification sections and preserved the primary evidence. No previous suite or publication workflow was rerun. The [Evidence Map](P2_B2_Evidence_Map.md) links the separate records and the [Review](P2_B2_Review.md) records independent disposition. No proof-assistant or SMT verification is claimed. Exact all-domain theorems, finite complete registries, sampled properties and observed native operations remain distinct evidence classes.

Rational projection and norm certificates can incur large integer costs; exact principal-minor checks used for small independent validation are not advertised as scalable. Analytic ranges may be loose or refuse safe cancelling cases. General global activation discovery, narrow envelopes for arbitrary programs and optimal finite-word bounds remain open. B2 does not train a model, provide general learning performance, or propagate a single-layer budget through time or multiple layers.

Software BF16, local audited scalar CPU FP32 and host AdamW proposal arithmetic remain separate. GPU, native BF16, arbitrary FMA/reassociation/compiler changes, general concurrent publication and whole-host formal correctness are not certified. [P2_B3_Handoff.md](P2_B3_Handoff.md) saves the strict next-stage obligations. B2 stops for coordinator review without executing B3.
