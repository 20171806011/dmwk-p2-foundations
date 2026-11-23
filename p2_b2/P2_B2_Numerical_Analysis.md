# P2-B2 — Certified arithmetic and error accounting

This document specifies the numerical claims implemented in [certified_bounds.py](certified_bounds.py). The mathematical results are proved in [P2_B2_Theorems.md](P2_B2_Theorems.md); [B2_Interface.md](B2_Interface.md) gives the public signatures. The implementation is a read-only diagnostic and does not publish weights, optimizer state or protected state.

## 1. Exact data and outward norm certificates

Stored BF16/FP32 words are decoded into exact rational values. Endpoints, biases and inputs reject NaN, infinity and the negative-zero input encoding; arithmetic zeros use the inherited canonical +0 policy. The effective update is exact decoded `W' - W`. It need not itself be representable as a target-format tensor.

Algebraic matrices and vectors use Q, with their usual embedding in R for Euclidean norms. The reference does not use an SVD estimate as a certificate. For every rational matrix A, it first computes

\[
q_A=\min\{\|A\|_F^2,\ \|A\|_1\|A\|_\infty\}
\]

exactly. Both entries bound the square of the spectral norm, so an outward upper enclosure of sqrt(q_A) is a certified spectral upper bound. Zero-row/zero-column matrices have zero norm. For a rational vector, its squared Euclidean norm is an exact sum of rational squares.

`sqrt_bounds(q,bits)` uses only exact rational arithmetic, integer bit lengths and integer square roots. A rational square is detected by checking whether both the reduced numerator and denominator are integer squares; its two endpoints then coincide. Otherwise, let k=floor(log2(q)), computed by exact comparisons, and let s=2^floor(k/2). The normalized value q/s^2 lies in [1,4). With t=2^bits, compute

\[
z=\left\lfloor\sqrt{\left\lfloor(q/s^2)t^2\right\rfloor}\right\rfloor.
\]

Then `s*z/t` and `s*(z+1)/t` enclose sqrt(q). The width is s/t, so `bits=80` means fractional precision on the normalized root. It is not a fixed absolute width 2^-80, which would conceal FP32-subnormal-scale effects. No host square-root or power implementation is trusted for these certificates.

An outward upper estimate of an observed norm can marginally exceed a separately constructed valid upper bound. Therefore implementation checks compare the **exact squared observed norm** with the square of the nonnegative claimed bound, not two independently rounded norm estimates.

## 2. Protected action and activation residual are different terms

Let H generate a declared reference space V and let Pi_V be its exact orthogonal projector. For the exact decoded update Delta and point h, compute

\[
x=\Pi_Vh,\qquad e=(I-\Pi_V)h.
\]

The projector route bounds the response by

\[
\|\Delta h\|_2
\le \|\Delta\Pi_V\|_2\,\|x\|_2
+\|\Delta\|_2\,\|e\|_2.
\]

The projector is computed from an exact independent column basis of H using a Gram inverse. For an explicitly supplied orthonormal U spanning V, the implementation verifies both `U.T U=I` and exact equality of projectors, and substitutes the certified norm of `Delta U`. Here ||x|| equals the orthonormal coefficient norm ||U.T h||. The returned `bound` retains this split. A separate `uniform_bound` records the valid alternative `||Delta|| ||h||`; it is not silently substituted for the named core bound.

If V is already proved to contain every actual legal activation under consideration, e is exactly zero. A nonzero e is meaningful only for an explicitly stated reference space or enlarged/perturbed input envelope. The geometry helper does not infer global coverage from a numeric matrix H or from samples.

For example, Delta=(3,4), V=span(e1) and h=(1,1) give the core upper bound 3*1+5*1=8, while the actual scalar response is 7. Replacing the protected-component norm by ||h|| would introduce an unnecessary relaxation. The absence of simultaneous equality in every triangle/operator inequality is not an implementation failure.

## 3. Approximate bases: conditioning and alignment

An approximately orthonormal matrix U has two independent issues:

1. Its columns may be poorly conditioned even when they span the intended space.
2. Its column space may differ from V even when its Gram matrix is exactly identity.

The implementation certifies

\[
\delta_G\ge\|U^TU-I\|_2,\qquad
\sigma\ge\|\Pi_V-\Pi_U\|_2.
\]

It requires delta_G<1 for this particular route. That inequality proves U has full column rank, so the exact rational projector `Pi_U=U(U.T U)^-1 U.T` is valid. The inverse-conditioning multiplier is an outward square-root upper bound of `1/(1-delta_G)`. This avoids division by a rounded-to-zero lower endpoint near a conditioning boundary.

With x=Pi_V h, the implemented protected-action coefficient is

\[
\varepsilon_U/\sqrt{1-\delta_G}+M\sigma,
\quad
\varepsilon_U\ge\|\Delta U\|_2,
\quad M\ge\|\Delta\|_2,
\]

which is multiplied by ||x|| and then augmented by M||e||. A scaled basis can have sigma=0 but nonzero Gram error; a rotated orthonormal basis can have delta_G=0 but nonzero sigma. Neither quantity substitutes for the other.

Failure of the computed delta_G<1 test means this conservative conditioning proof is unavailable. It does not prove that U is rank deficient or that the endpoint is unsafe. The caller may separately request the exact-projector route; the implementation does not silently relabel the failed basis as orthonormal or claim an unproved pseudoinverse alternative.

## 4. A disjoint upstream error ledger

Two valid accounting routes are kept separate:

- **Direct endpoint route:** decode the actual stored endpoints and bound Delta_eff directly. Candidate generation, factor arithmetic, optimizer rounding and endpoint storage effects are already included in this difference.
- **Telescoping route:** supply a named exact chain of increments D0,...,Dm, ending at the actual effective increment, and use `Dm=D0+sum_i(Di-D(i-1))`. Bound the baseline and each adjacent signed error once.

`error_ledger` checks matrix shapes and unique stage labels and records every exact adjacent difference. With a specified h, it applies each term to h before taking its norm; without h, it uses spectral upper bounds. The net increment is the **last chain matrix**, not the difference between last and first. The signed telescope is exact, while the sum of norm bounds can be loose because errors may cancel.

The chain proves an accounting identity. It does not prove that a label such as “ideal Adam,” “approximate projector” or “storage” accurately describes a generation procedure unless that procedure has its own evidence. In particular no ideal correctly rounded host power or square-root model is fabricated for B1's optimizer. A direct actual-endpoint bound must not be enlarged again by the same upstream errors as though they were missing terms.

## 5. Fixed affine graph and exact trace residuals

The protected graph starts each output accumulator at its stored bias, then visits columns in ascending order. Each column performs one separate target-format multiplication followed by one separate target-format addition. There is no FMA, reassociation or implicit omission of zero terms.

For one row, let exact product p_j=w_j h_j, rounded product p_hat_j=p_j+mu_j, and rounded accumulation

\[
s_j=\operatorname{RN}(s_{j-1}+\widehat p_j)
=s_{j-1}+\widehat p_j+\alpha_j,
\qquad s_0=b.
\]

By exact rational subtraction of decoded operands/results,

\[
s_d-(b+\textstyle\sum_j p_j)=\sum_j(\mu_j+\alpha_j).
\]

This identity needs actual finite execution under the specified graph. It does not need normal intermediates, a condition number, a relative-error-only model or a statistical independence assumption. Each event records its exact operation argument, rounded word, signed local error and absolute local error. The row bound is the sum of absolute local errors; rho_2 is the outward Euclidean norm of those row bounds, and rho_infinity is their maximum. Bias loading is exact and has no additional rounding term.

The old and new endpoints are traced separately. Let their row-error vectors be bounded by rho_old and rho_new, and let db=b'-b be the exact explicit bias difference. Then

\[
\|\widehat y'-\widehat y\|_2
\le \|\Delta_{\rm eff}h+db\|_2
+\rho_{\rm old,2}+\rho_{\rm new,2}.
\]

The point implementation computes the exact algebraic vector, an outward norm bound and both independent execution contributions. It also returns coordinate bounds and their infinity norm. It does not replace the difference of two rounded executions by a rounded execution of Delta_eff. The rounded-thirds example is precisely a case where the exact algebraic term is zero while the execution difference is nonzero.

An actual overflowing operation, nonfinite word or invalid encoding causes refusal. The exact residual path can still certify a finite trace whose unrounded argument lies slightly above Fmax but rounds to a finite word; such an event does not receive the stricter local mixed-range annotation described next.

## 6. Underflow-aware analytic box bounds

For the sufficient local range |z|<=Fmax under the declared rounding policy, the scalar mixed bound is

\[
|\operatorname{RN}(z)-z|\le u|z|+\eta/2,
\]

where u=2^-p and eta is the smallest positive subnormal. The additive term covers the subnormal region; canonicalizing a zero does not change its real value. The point trace annotates this bound only when its exact operation argument satisfies the stated range condition.

For a complete coordinate envelope |h_j|<=H_j, the box helper proves range and error recursively for **each endpoint separately**. Start with A0=|b|. At column j:

\[
L_j=|w_j|H_j,\quad R^p_j=uL_j+\eta/2,
\quad T_j=\min(F_{\max},L_j+R^p_j),
\]

\[
S_j=A_{j-1}+T_j,\quad R^s_j=uS_j+\eta/2,
\quad A_j=\min(F_{\max},S_j+R^s_j).
\]

It requires both L_j<=Fmax and S_j<=Fmax before proceeding. The row error bound is the sum of all R^p_j+R^s_j. The algebraic coordinate response bound is `abs(db_i)+sum_j abs(Delta_eff_ij)*H_j`. Adding old/new row errors gives the coordinate bounds; the L2 bound instead sums the Euclidean bound of the algebraic vector and the separate old/new rho_2 bounds, matching the point theorem.

Every accepted recurrence establishes totality and the error estimate for all admitted raw inputs inside that box, not just its corners or samples. The envelope's inclusion of every legal shared-call activation is a separate obligation of the bounded-certificate registry. `global_domain_inclusion_verified` is false in the generic helper until that external proof is supplied.

The recurrence intentionally preserves conservative zero-operation padding and loses correlations/cancellation. It can refuse even when every actual input of interest executes finitely, including cases near Fmax. Such refusal means “this box proof did not establish totality,” not “the implementation observed overflow.” It can also return a positive bound when old and new endpoints coincide; the separately traced point method may be much tighter. Neither outcome is disguised as a measured execution error.

No gamma_n formula is used by the delivered bound or acceptance APIs. A gamma specialization would require its own verified operation count, `n*u<1`, normal-range/relative-error premises and no-overflow proof. Merely observing a normal rounded output is not a replacement for those premises near the normal/subnormal boundary.

## 7. Relative, mixed and bitwise conclusions

At a point, the reference output is the actual decoded old output. Its maximum coordinate magnitude is a certified lower bound L on its L2 norm. If L>0, `l2_bound/L` is a safe relative upper bound. If L=0, the old vector is zero and the relative bound is explicitly undefined; absolute and mixed statements remain meaningful.

`mixed_budget(B,L,a,b)` uses nonnegative quantities and checks `B<=a+b*L`. Given certified B and L, this is sufficient for `||difference||<=a+b||old_output||`; it is conservative because L is a lower bound. The generic routine cannot infer the provenance of a caller-supplied L. The analytic box helper provides no invented positive uniform lower reference bound: its relative result is `None` unless a separate argument is made outside that helper.

A finite canonical-output separation argument may turn a **strict** uniform bound below eta into bitwise equality on the fully covered domain. Equality at eta is not enough. A point bound cannot make that conclusion for untested inputs, and a numeric receipt remains distinct from B1's live BIT/ALG_AND_BIT certificate. Program-level lifting still needs the fixed-D, legal-input, state-invariant, full-call-site and scheduling premises from A3.

## 8. Cost and unverified execution environments

Norm certificates require exact sums and integer-square-root operations whose cost depends on rational bit lengths and requested precision. They are not floating SVD calls. The explicit projectors use rational elimination and Gram inverses and may require quadratic matrix storage and cubic dense algebra in the relevant dimensions; large-instance efficiency is not established. A point trace records 2nd arithmetic events per n-by-d endpoint, or 4nd events for an old/new pair, in addition to exact-reference bookkeeping. Box recurrence work is linear in the number of coefficients, with exact-rational growth left visible.

The implementation verifies software BF16 and the available audited local CPU FP32 path. GPU, native BF16, arbitrary optimization/fusion, general concurrency and hardware faults remain outside certification. The exact analysis extends to stated real/rational algebra, but does not declare arbitrary floating networks, undocumented kernels or other execution graphs safe. Actual experimental counts and timings belong to the result JSON and evidence map, not to the mathematical cost discussion.
