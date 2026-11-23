# P2-B2 — Strict single-layer perturbation theorems

These handwritten proofs use [Definitions](P2_B2_Definitions.md). They are not inferred from the test counts. Delta is always the exact decoded endpoint difference W'-W. V means the declared reference space V_ref; it is identified with the full legal span only when that separate fact has been proved. All square roots/norms in proofs are real; executable rational upper bounds must enclose them.

## T1 — Restricted update residual and activation leakage

Let Q_D have orthonormal columns spanning V. For h=Q_D a+e with a=Q_D^T h and e=(I-Q_DQ_D^T)h, let epsilon and M be nonnegative upper bounds on ||Delta Q_D||_2 and ||Delta||_2. Then

\[
\|\Delta h\|_2
\le \epsilon\|a\|_2+M\|e\|_2,
\qquad
\|\Delta h\|_2\le M\|h\|_2.
\tag{1}
\]

Both bounds hold, so their minimum is valid. For an affine layer add ||delta_b||_2 to either bound.

**Proof.** Linearity gives Delta h=(Delta Q_D)a+Delta e. Apply the triangle inequality and the defining induced-norm inequalities. Applying the global operator norm directly to h gives the second bound. The affine difference is Delta h+delta_b, so one more triangle inequality gives its stated bound. Orthonormality also gives ||h||_2^2=||a||_2^2+||e||_2^2. ∎

An exact-projector implementation need not construct an irrational Q_D: ||Delta Pi_V||_2=||Delta Q_D||_2. Indeed Delta Pi_V=Delta Q_D Q_D^T gives one inequality and Delta Q_D=Delta Pi_V Q_D gives the reverse, since Q_D and Q_D^T have norm one when r>0. For r=0 both operators are zero. Also ||Pi_Vh||_2=||a||_2. Therefore a certified bound using exact Pi_V is an equivalent route, though its chosen numerical norm upper bound may be more conservative than a differently shaped computation.

**Degenerate cases.** If V={0}, a is empty and e=h, so the leakage bound is the global bound. If V=R^d, e=0 and ||Delta Q_D||_2=||Delta||_2, so the restricted bound is global. If h=0 and bias is fixed, the exact difference is zero. If Delta=0 both exact bounds vanish. If V contains the complete legal activation domain, legal e is exactly zero; a nonzero e requires a separately declared reference/perturbation envelope. Consequences for rounded execution require its graph/policy premises. In particular identical canonical endpoints and fixed bias under the same deterministic graph do give identical execution; the specified finite bias-first graph at the zero input also returns the fixed bias exactly for either endpoint. A nonzero exact annihilator does not generally give this conclusion.

**Separate sharpness.** For V=span(e_1) in R^2, a row Delta=(c,0) and h=e_1 attain the restricted term c, while Delta=(0,c) and h=e_2 attain the leakage term c, for c>=0. The sum in (1) is generally conservative when both components are nonzero, because the two blocks share the same global operator-norm budget. For example Delta=(3,4), h=(1,1), Q_D=e_1 give epsilon=3, M=5, actual |Delta h|=7 and basic bound 8. A claim that both terms are always simultaneously sharp for fixed epsilon,M would be false.

### T1(a): optional sharp joint envelope

Assume V and V-perp are both nonzero and the output dimension is at least one. Fix h with A=||a||_2 and E=||e||_2, and consider every real matrix Delta satisfying ||Delta||_2<=M and ||Delta Q_D||_2<=epsilon. Set c=min(epsilon,M). If M=0 or h=0 the supremum is zero. Otherwise its exact value is

\[
\Phi(A,E)=
\begin{cases}
M\sqrt{A^2+E^2},&MA\le c\sqrt{A^2+E^2},\\
cA+\sqrt{M^2-c^2}\,E,&MA>c\sqrt{A^2+E^2}.
\end{cases}
\tag{2}
\]

This is an algebraic class optimum; it does not assert that a maximizing matrix is an available stored endpoint difference for a fixed old W.

**Proof.** For a unit output direction z put w=Delta^T z. Then ||w||_2<=M and ||Pi_V w||_2=||Q_D^T Delta^Tz||_2<=c. Cauchy-Schwarz on the two orthogonal blocks gives

\[
z^T\Delta h\le xA+yE,
\quad x,y\ge0,\quad x\le c,\quad x^2+y^2\le M^2.
\]

Taking the supremum over unit z bounds the output norm by this scalar optimization. Without the x constraint its maximizer is (x,y)=M(A,E)/sqrt(A^2+E^2). This is feasible exactly in the first case of (2). Otherwise the maximizing x is c and y=sqrt(M^2-c^2): on the circular boundary, the derivative A-E x/sqrt(M^2-x^2) is positive up to the unconstrained maximizing x. The same conclusion follows directly when E=0. Thus (2) is an upper bound.

To attain it, choose unit vectors in the directions of the nonzero v and e components, and arbitrary unit vectors in the appropriate nonzero subspaces for zero components. Form w with those components of lengths x,y at the scalar optimum. Choose any unit output z and set Delta=z w^T. This rank-one map has global norm ||w||_2<=M and restricted norm ||Pi_V w||_2<=c. It maps h to z(xA+yE), attaining (2). This also covers A=0 or E=0 by the choices just described. ∎

The reference need not implement (2) to use the proved simpler bounds in (1). Reporting a conservative bound rather than this optimum is not a numerical failure.

## T2 — Approximate basis conditioning and subspace deviation

Let U have l columns, and suppose ||U^TU-I_l||_2<=delta<1. For l>0, U has full column rank and its exact orthogonal projector is Pi_U=U(U^TU)^(-1)U^T. Suppose alpha>=1/sqrt(1-delta), epsilon_U>=||Delta U||_2, M>=||Delta||_2 and sigma>=||Pi_U-Pi_V||_2. Then every v in V satisfies

\[
\|\Delta v\|_2
\le (\epsilon_U\alpha+M\sigma)\|v\|_2.
\tag{3}
\]

For general h=v+e with v=Pi_Vh this implies

\[
\|\Delta h\|_2
\le (\epsilon_U\alpha+M\sigma)\|v\|_2+M\|e\|_2.
\tag{4}
\]

**Proof.** For any x in R^l,

\[
\|Ux\|_2^2=x^TU^TUx\ge(1-\delta)\|x\|_2^2.
\]

Thus U is injective. The formula for Pi_U is symmetric and idempotent, fixes range(U) and kills its orthogonal complement, so it is its orthogonal projector. Let U^+=(U^TU)^(-1)U^T. For z, put x=U^+z; then Ux=Pi_Uz. The displayed inequality gives ||x||_2<=alpha||Pi_Uz||_2<=alpha||z||_2, hence ||U^+||_2<=alpha. Since v=Pi_Vv,

\[
\Delta v=\Delta U U^+v+\Delta(\Pi_V-\Pi_U)v.
\]

The triangle and operator-norm inequalities give (3). Adding Delta e gives (4). With l=0 the first term is zero and Pi_U=0; the conclusion follows directly from the second term, without a Gram inverse. ∎

**Scope and counterexamples.** Gram control is conditioning, not alignment. For V=span(e_1), U=e_2 and Delta=(1,0), the Gram error and Delta U are zero, but Delta e_1=1; the projector gap is one and cannot be omitted. Conversely U=2e_1 spans the correct V but has Gram deviation three, so this sufficient delta<1 route is unavailable even though its exact projector is perfectly well defined. For U=(3/5,4/5)^T and V=span(e_1), the Gram deviation is zero and the projector difference has norm 4/5: its symmetric 2-by-2 difference has trace zero and square (16/25)I. Rank mismatch forces ||Pi_U-Pi_V||_2>=1, because the larger subspace contains a unit vector orthogonal to the smaller one. Thus a certified gap below one implicitly requires equal ranks.

### T2(a): checkable rational upper bounds

For any real matrix A, ||A||_2<=||A||_F and ||A||_2<=sqrt(||A||_1||A||_infinity). The Frobenius inequality follows by rowwise Cauchy-Schwarz and summation. For the second, apply |(Ax)_i|^2<=(sum_j|a_ij|)(sum_j|a_ij||x_j|^2), sum over i, and use the maximum row/column sums. For rational A all squared quantities used here are rational; a nonnegative rational t with t^2 greater than or equal to the relevant bound is a certified norm upper bound.

Alternatively t>=||A||_2 is exactly equivalent to t^2I-A^TA being positive semidefinite for t>=0, since its quadratic form is t^2||x||^2-||Ax||^2. Exact positive-semidefinite verification, for example checking all principal minors, is a complete finite algebraic option. It may be exponential in the dimension and is not claimed as a scalable optimal method. For approximate U, rational delta<1 and alpha>=0 with alpha^2(1-delta)>=1 certify the conditioning factor. Rational full-rank H gives an exact rational Pi_V, so the projector-gap matrix can be bounded by these same methods. None proves that H covers all legal activations; that provenance is a separate premise. ∎

## T3 — Disjoint representation, optimizer, generation and storage ledger

With the objects defined in Definitions §4,

\[
\Delta=C_*+E_{repr}+E_{opt}+E_{gen}+E_{store}.
\tag{5}
\]

**Proof.** Substitute the definitions. The first two terms sum to G_*P_tilde, adding E_opt gives G_hat P_tilde, adding E_gen gives D_hat, and adding E_store gives Delta. Each intermediate cancels exactly once. ∎

Consequently, for every h,

\[
\|\Delta h\|_2
\le\|C_*h\|_2+
\sum_{j\in\{repr,opt,gen,store\}}\|E_jh\|_2.
\tag{6}
\]

Each error term may be bounded by ||E_j||_2||h||_2, or by a separately proved restricted/domain bound. On V, C_*h=0. The triangle inequality can be loose because error terms may cancel. A bound directly calculated from actual Delta already contains those errors; adding (6)'s error terms to it counts the same effects twice and is not the disjoint analysis claimed here. Such a larger number may remain an upper bound, but it is not a justified decomposition into additional independent sources.

**Factor alternative.** Suppose an ideal safe generator C_* uses exact factors, for example A_*B_*^TN_*^T with range(N_*)=V-perp. Define one represented-factor expression F_rep from the stored/represented ideal factors, and F_opt from the chosen computed optimizer factors. Set E_factor=F_rep-C_*, E_opt=F_opt-F_rep, E_gen=D_hat-F_opt and E_store=Delta-D_hat. Their sum with C_* again telescopes to Delta. This combined factor-representation term replaces the projector-representation term. Products of factor perturbations must either be retained inside E_factor or decomposed by a fully specified telescoping identity; discarding cross terms is not an exact bound.

The identity alone does not certify the magnitude of a hypothetical ideal optimizer discrepancy. An error budget for G_hat-G_* requires a defined ideal path and a validated calculation of its deviation. B1's observed host AdamW path is not silently relabelled as exact arithmetic.

## T4 — Local rounding, trace telescoping and two-execution difference

### T4(a): mixed local RNE model

Let |x|<=Fmax. For correctly rounded binary arithmetic with precision p, gradual underflow, RNE and canonical zero,

\[
|RN_F(x)-x|\le u|x|+\eta/2,
\qquad u=2^{-p}.
\tag{7}
\]

The sufficient range condition ensures a finite result. Canonicalizing zero does not change its decoded value.

**Proof.** In the subnormal region the representable values form an eta-spaced lattice, so nearest rounding has absolute error at most eta/2. For a normal binade beginning at 2^e the spacing is 2^(e-p+1), so the half-spacing bound is 2^(e-p)<=u|x|. At binade transitions the smaller adjacent gap can only improve this bound. At the finite upper endpoint, |x|<=Fmax ensures that a nearest finite representative exists within the same half-spacing bound. These cases imply (7); its added eta/2 allows one formula for both normal and subnormal cases. ∎

The relative-only inequality |RN(x)-x|<=u|x| is false in general under underflow: x=eta/2 rounds to zero by ties-to-even and has error eta/2>u eta/2. Thus additive underflow terms cannot be silently dropped. A finite actual trace can instead use exact local residuals, even when a sufficient analytic range test is inconclusive.

### T4(b): exact trace identity

For each finite bias-first row trace define rho_j=p_j-w_jh_j and tau_j=s_j-(s_(j-1)+p_j). Then

\[
s_d-(b+\textstyle\sum_jw_jh_j)=\sum_j(\rho_j+\tau_j).
\tag{8}
\]

**Proof.** The row recurrence is s_j=s_(j-1)+w_jh_j+rho_j+tau_j. Summing from j=1 through d and using s_0=b cancels each internal accumulator exactly. ∎

Thus beta=sum_j(|rho_j|+|tau_j|) bounds that row's error. All residuals are exact rational numbers when the finite trace is decoded. This identity uses actual operation results and does not require that a generic upper bound like (7) be tight.

### T4(c): old/new executions are separate

Let zhat and zhat' be the full decoded finite outputs of old and new executions at the same h, and let beta_old,i and beta_new,i bound their row errors relative to Wh+b and W'h+b'. Then

\[
|\widehat z'_i-\widehat z_i|
\le |(\Delta h+\delta_b)_i|+\beta_{old,i}+\beta_{new,i}.
\tag{9}
\]

**Proof.** Write each floating output as its exact algebraic output plus its trace error, subtract, and apply the scalar triangle inequality. The signs of old and new errors are generally unrelated. ∎

For the infinity norm, maximize (9) over rows. For the Euclidean norm, one may bound the exact residual by T1/T2 and add ||beta_old+beta_new||_2, or use the possibly looser sum ||beta_old||_2+||beta_new||_2 used by the reference. The triangle inequality proves both. Fixed bias removes delta_b but not either rounding term. Exact Delta h=0 can coexist with a nonzero rounded difference, as in the inherited thirds/subnormal construction; a direct floating zero test at one basis input does not eliminate this possibility.

## T5 — A universal analytic box bound and guarded relative specialization

Assume every admitted input in the covered domain satisfies |h_j|<=B_j, with B_j nonnegative rationals. For one fixed row define A_0=|b|. At each j form

\[
L_j=|w_j|B_j,\quad
R^p_j=uL_j+\eta/2,\quad
T_j=\min(Fmax,L_j+R^p_j),\quad
S_j=A_{j-1}+T_j.
\]

Require L_j<=Fmax and S_j<=Fmax. Then set

\[
R^s_j=uS_j+\eta/2,\qquad
A_j=\min(Fmax,S_j+R^s_j),\qquad
\overline\beta=\sum_j(R^p_j+R^s_j).
\tag{10}
\]

If a range test fails, this certificate refuses; it does not conclude that every actual input overflows.

**Statement.** If all these tests succeed, every admitted raw input in the envelope executes finitely, its j-th accumulator has magnitude at most A_j, and its row execution error is at most overline_beta. Apply the construction independently to every row of both endpoints. Then a global full-output infinity bound is

\[
\max_i\left(
\sum_j|\Delta_{ij}|B_j+|\delta_{b,i}|+
\overline\beta_{old,i}+\overline\beta_{new,i}
\right).
\tag{11}
\]

**Proof.** At j=0 the loaded finite bias has exactly magnitude A_0. Suppose the previous accumulator bound holds. The exact product has magnitude at most L_j<=Fmax, so (7) bounds its error by R^p_j. Its rounded finite magnitude is at most T_j because both L_j+R^p_j and Fmax are upper bounds. The exact add input therefore has magnitude at most S_j<=Fmax, so it is finite after rounding, has error at most R^s_j and resulting magnitude at most A_j. Induction proves every range and local residual bound. Summing the local bounds and using (8) proves the row error estimate. The exact affine residual obeys |(Delta h+delta_b)_i|<=sum_j|Delta_ij|B_j+|delta_b,i|. Inserting this into (9) proves (11) uniformly. ∎

For multiple shared sites with different envelopes or biases, apply this theorem to each declared site and take the maximum; omitting a site invalidates a global shared-matrix claim. The proof ranges over every admitted input in the envelope, not only its corners or sampled traces. Loose absolute ranges can fail on large cancelling expressions that execute safely; refusal of this conservative method is not a proof of impossibility.

For the Euclidean version, let k_i=sum_j|Delta_ij|B_j+|delta_b,i| and collect the nonnegative row-error envelopes into beta_old and beta_new. Componentwise (9) implies the global bound ||k+beta_old+beta_new||_2. The reference uses the valid possibly looser bound ||k||_2+||beta_old||_2+||beta_new||_2, with outward rational square-root enclosures; its validity follows from one further triangle inequality. This proves the box method for either explicitly selected norm.

### T5(a): optional gamma bound with extra premises

Suppose, additionally, every product and addition in the entire claimed domain is finite and satisfies a relative local model RN(x)=x(1+theta), |theta|<=u (with exact zero handled as zero). This must be separately established; gradual underflow alone does not imply it. If (d+1)u<1, define gamma_(d+1)=(d+1)u/(1-(d+1)u). Then

\[
|\widehat z-(b+\textstyle\sum_jw_jh_j)|
\le\gamma_{d+1}\left(|b|+\sum_j|w_jh_j|\right).
\tag{12}
\]

**Proof.** Expand the recurrence symbolically. The bias is multiplied by at most d addition-error factors. The j-th exact product is multiplied by its one product-error factor and at most d-j+1 addition-error factors, at most d+1 factors total. For m<=d+1 factors with |theta|<=u and mu<1, their product differs from one in magnitude by at most gamma_m<=gamma_(d+1): the upper deviation follows from (1+u)^m<=1/(1-mu), using binomial coefficients bounded by m^k; the lower deviation is at most 1-(1-u)^m<=mu. Subtract the exact row sum and bound each coefficient deviation by gamma_(d+1). ∎

When d=0 no arithmetic is performed and the bias is exact; error is zero. A pointwise check of the relative local property supports only that trace. If the analytic or relative hypotheses cannot be proved globally, the interface must use its qualified mixed/absolute route or refuse the unsupported specialization.

Equation (12) is a conditional mathematical specialization. The delivered analytic-box method uses (10)'s mixed local bounds and does not silently turn this theorem into an unverified gamma-based acceptance path.

## T6 — Relative, mixed and strict finite-output separation

### T6(a): reference norms and cancellation

If an actual two-execution norm difference is bounded by B and the chosen reference output norm is at least L>0, then its relative difference is at most B/L. This follows by division by the positive norm. If only an exact old output lower bound ||Wh+b||>=L_exact and old execution-error upper bound beta_old are known, the reverse triangle inequality supplies L=L_exact-beta_old when this is positive. A zero/nonpositive result provides no positive denominator certificate.

Cancellation demonstrates the need: an old row (1,-1) at h=(1,1), bias zero, has exact and rounded output zero. Changing its second coefficient to zero gives output one. No finite relative-only constant times the zero reference norm bounds that difference. This is an admissible finite-output example, not an overflow artifact.

If an exact algebraic mixed relation ||Delta h+delta_b||<=rho||Wh+b||+tau_0 holds, rho>=0, and the two execution errors have norm bounds beta_old,beta_new, then

\[
\|\widehat z'-\widehat z\|
\le\rho\|\widehat z\|+
\tau_0+(\rho+1)\beta_{old}+\beta_{new}.
\tag{13}
\]

**Proof.** T4 bounds the difference by the exact residual plus the two execution errors. Substitute the mixed relation and use ||Wh+b||<=||zhat||+beta_old. ∎

This mixed bound is meaningful at zero. It does not imply that the absolute term is small, or propagate itself through recurrent/control-flow computations.

### T6(b): a strict lattice gap can prove output words equal

In one fixed admitted canonical finite BF16/FP32 format, every decoded value is an integer multiple of eta. If both full output vectors are finite and

\[
\|\widehat z'-\widehat z\|_\infty\le B<\eta,
\tag{14}
\]

then their raw output words agree.

**Proof.** Every nonzero coordinate difference is an integer multiple of eta of magnitude at least eta. Equation (14) excludes it. Canonical finite decoding is injective because the duplicate negative-zero representation is rejected/canonicalized, so coordinate equality gives word equality. ∎

The strict inequality is essential: old scalar weight zero, new weight eta and h=1 give outputs zero and eta, with difference exactly eta and different words. If both zero signs were admitted without canonicalization, equal decoded numbers would not imply equal bits. A full-domain bound proves only output equality on that domain; unobserved flags/effects, missing sites or updated feedback closure do not follow. To lift equality to a protected program trajectory requires the separate A3 initial-state/input/schedule/interface/invariant and covered-effect premises. The B2 receipt does not implement a new BIT authorization even when (14) happens to hold.

## T7 — Scope of the read-only numerical receipt

Assume a trusted fixed domain descriptor proves coverage of its original input envelope and all required shared sites. A pure verifier reconstructs the exact endpoints, bias, observed ports, graph, arithmetic policy, selected norm and method. For `complete_point_trace` it enumerates every declared input and checks both actual finite traces with T4; for `analytic_box` it validates the domain-to-box inclusion and T5's totality/range proof. It accepts only when the recomputed bound in the explicitly selected Euclidean or infinity norm is at most the declared nonnegative budget.

**Conclusion.** An accepted receipt proves the claimed single-call difference bound, in its selected norm, on exactly that domain under those premises. It changes no protected bank, state or optimizer state and conveys no B1 publication authority.

**Proof.** In the finite case every domain element has the point theorem and the maximum covers their union. In the box case inclusion places every domain element under the universally proved range and error induction. In either case comparison with the budget proves the stated inequality. Purity of the receipt path means its execution has no state publication transition. B1's accepted-record schema and BIT/ALG_AND_BIT checks remain independent obligations. ∎

This conclusion does not authenticate a caller's historical intent, prove an untrusted coverage assertion, or show that a candidate program stays in the original envelope. A snapshot/hash binds identity only under the declared trusted runtime and recomputation contract. Reassociation, FMA, format/zero-policy changes, omitted calls or nonfinite results require rejection or a different explicitly proved descriptor. Numerical budget acceptance is neither exact algebraic annihilation nor automatic bitwise equality, and is not a result for all subsequent P2 stages.
