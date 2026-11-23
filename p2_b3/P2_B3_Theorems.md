# P2-B3 — Nonlinear composition and finite-time perturbation theorems

These are handwritten conditional proofs using [Definitions](P2_B3_Definitions.md), not conclusions inferred from a finite experiment. Endpoints, graphs, numerical policies and input/schedule contracts remain fixed. The exact maps and their rounded executions are different objects throughout.

## T1 — One-step relational recurrence

Fix a common input u and an admissible old/new state pair x in K, x' in K'. Assume:

1. The exact maps F,F' are defined at all comparison points used below. For every relevant cross pair and common input,
   ||F'(x',u)-F'(x,u)||<=L||x'-x|| with L>=0. A Lipschitz bound on a containing joint domain is sufficient.
2. The same-input endpoint drift satisfies ||F'(x,u)-F(x,u)||<=a on the old domain, with a>=0.
3. Both rounded executions are total on their respective domains, and ||Fhat(x,u)-F(x,u)||<=rho, ||Fhat'(x',u)-F'(x',u)||<=rho', with rho,rho'>=0.

Then

\[
\|\widehat F'(x',u)-\widehat F(x,u)\|
\le L\|x'-x\|+b,
\qquad b=a+\rho+\rho'.
\tag{1}
\]

**Proof.** Add and subtract F'(x',u), F'(x,u) and F(x,u). The four resulting differences are the new execution residual, the new exact map's cross-state difference, the same-input exact endpoint drift, and the negative old execution residual. Bound each by its stated premise and apply the triangle inequality. ∎

The new exact map at the old point need not be an actual new execution, but it must be defined and covered by the algebraic cross-pair bound. The same-input drift need only cover the old domain for this particular split. Reversing the split gives an alternative with the old-map Lipschitz constant and a same-input drift bound on the new domain; one may use the smaller certified result only if both sets of hypotheses hold.

No statistical independence of rounding errors is assumed. The argument does not claim that Fhat' is L-Lipschitz. Identical canonical endpoints and an identical deterministic graph do give equal executions at equal inputs; the possibly positive generic rho+rho' bound need not exploit that special cancellation.

## T2 — Nonhomogeneous layer/time propagation

Suppose initial pairs satisfy ||xhat'_0-xhat_0||<=E_0. For k=1,...,T, suppose the joint domain/totality premises of T1 hold at the reached pairs, with constants L_k,b_k>=0. Define

\[
E_k=L_kE_{k-1}+b_k.
\tag{2}
\]

Then every admitted execution pair satisfies ||xhat'_k-xhat_k||<=E_k and

\[
E_t=
E_0\prod_{k=1}^{t}L_k+
\sum_{j=1}^{t} b_j\prod_{k=j+1}^{t}L_k.
\tag{3}
\]

Empty products are one and an empty sum is zero, so t=0 returns E_0. Zero L_k require no division and are allowed.

**Proof.** At k=0 use the initial relation. If the state difference is bounded by E_(k-1), T1 and nonnegativity of L_k give the next difference at most L_kE_(k-1)+b_k=E_k. This proves the first claim by induction. For the formula, t=0 is immediate. Multiply the product-sum expression at t-1 by L_t and add b_t; all earlier terms gain their final L_t factor and the new term has an empty product. This is exactly (3). ∎

This result applies to successive network layers, where dimensions and their chosen norms may differ, or to successive synchronous time steps. A fixed multilayer state transition can first be analyzed by its layer recurrence and then used as a single step, provided every internal domain and repeated shared-bank call is covered. It is invalid to add only local same-input differences while omitting the propagation of earlier input changes.

Same initial boxes are not the same initial relation: two independently chosen points in one box can differ. E_0=0 requires exact paired equality or an equivalent trusted relation. An observation at the end of T layers does not prove equality of intermediate branch decisions or side effects.

If the observation is the full recurrent state at every time0,...,T, the valid bound is max_(0<=k<=T)E_k. Each observed time has its own inequality, so taking their maximum proves this prefix claim. A bound only on E_T is insufficient when earlier errors are larger, including a contracting sequence with a nonzero initial difference.

## T3 — Constant envelopes, their regimes and tightness

Assume L_k<=L and b_k<=b for nonnegative constants. Then

\[
\|\widehat x'_t-\widehat x_t\|
\le L^tE_0+b\sum_{j=0}^{t-1}L^j.
\tag{4}
\]

For L!=1 this is L^tE_0+b(L^t-1)/(L-1). For L=1 it is E_0+tb. For L=0 and t>=1 it is b.

**Proof.** The recurrence E_k<=LE_(k-1)+b follows from T2 and nonnegative bounds. Apply its constant-coefficient product-sum formula. The finite geometric-sum identity follows by multiplying the sum by L and subtracting; no division is used when L=1. ∎

If 0<=L<1 and the premises hold for every time, then

\[
\|\widehat x'_t-\widehat x_t\|
\le L^tE_0+(1-L^t)\frac{b}{1-L}
\le\max\{E_0,b/(1-L)\}.
\tag{5}
\]

The right side is a convex combination, proving the final inequality. A uniform invariant domain, all-time totality, uniform input/rounding bounds and unchanged endpoints/policy are required for this time-uniform conclusion. A finite tube supports only its stated horizon.

At L=1 the bound can grow linearly; at L>1 it can grow exponentially. These are upper envelopes, not lower bounds on actual drift. For example the exact zero map admits the valid loose Lipschitz bound L=2 but erases every initial difference after one step. The exact real scalar comparison F(x)=Lx and F'(x)=Lx+b, with nonnegative initial difference E_0 and common zero external input, attains (4) when no additional forcing/error is inserted. This proves sharpness for that algebraic class. It is not a claim that an arbitrary finite-format execution remains exact or finite at arbitrarily large t.

In the exact scalar contraction example, a symmetric box of radius R with LR+b<=R is invariant for both endpoints. For a neutral or amplifying example that fails this inclusion, one may still prove a finite tube; a desired regime label does not establish an invariant.

## T4 — Joint box invariance and finite tube closure

### T4(a): finite paired tube

Let K_0,...,K_T and K'_0,...,K'_T be declared domains. Assume every admissible initial pair belongs to K_0 by K'_0 with difference at most E_0. For every k<=T and every pair in

\[
\mathcal R_{k-1}=
\{(x,x'):x\in K_{k-1},\ x'\in K'_{k-1},\ \|x'-x\|\le E_{k-1}\},
\]

and every permitted common input, assume:

- both actual rounded steps are finite and return points in K_k and K'_k;
- T1's cross-pair, endpoint-drift and two-execution-error bounds hold;
- E_k>=L_kE_(k-1)+b_k.

Then every admitted pair stays in R_k through k=T.

**Proof.** Initial inclusion supplies the base case. Membership in R_(k-1) permits application of both endpoint range inclusions and T1. The two successors are in their next domains and have difference at most E_k, hence belong to R_k. Induction proves the claim without assuming that the new trajectory stays near the old one before establishing it. ∎

The range conditions may be checked on the larger independent product K_(k-1) by K'_(k-1), a conservative sufficient method. Correlations can tighten them but cannot be assumed from samples. The theorem does not assert membership after T.

### T4(b): invariant relation

If time-independent K,K' and common input policy satisfy the same totality and individual range inclusions at every step, they are simultaneous invariant domains. If additionally E_0<=R and LR+b<=R, the paired relation with radius R is invariant.

**Proof.** Use T4(a)'s one-step argument repeatedly with the same domains and radius. Since no time-dependent premise expires, induction applies to every finite t. ∎

For L<1, R>=max(E_0,b/(1-L)) suffices. For L=1 with b>0 this scalar inequality cannot certify a finite R, although a different invariant/error analysis might. For L>1 a positive R may likewise be unsupported by this particular inequality. Failure of this proof method is not an impossibility theorem for the actual system.

### T4(c): executable symmetric-box range witness

For a stored affine row with inputs satisfying |h_j|<=B_j, use the B2 mixed local bound |RN(z)-z|<=u|z|+eta/2 on the sufficient range |z|<=Fmax. Start A_0=|bias| and define

\[
L_j=|w_j|B_j,\quad
R^p_j=uL_j+\eta/2,\quad
P_j=\min(Fmax,L_j+R^p_j),
\]

\[
S_j=A_{j-1}+P_j,\quad
R^s_j=uS_j+\eta/2,\quad
A_j=\min(Fmax,S_j+R^s_j).
\tag{6}
\]

Require L_j<=Fmax and S_j<=Fmax. Then every input in the declared raw box executes finitely, the output magnitude is at most A_d, and its affine execution error is at most sum_j(R^p_j+R^s_j). A finite ReLU output is nonnegative and has magnitude no larger than A_d. Identity has the same magnitude bound.

**Proof.** The exact product magnitude is bounded by L_j, so the local mixed inequality bounds its error and its finite magnitude by P_j. The exact addition argument is bounded by S_j, so its error and rounded magnitude obey R^s_j and A_j. Induct from the exact loaded bias. Summing signed local residuals telescopes the row error; summing their absolute upper bounds proves the estimate. ReLU cannot increase a scalar magnitude. ∎

Run this calculation separately for every row, endpoint and internal layer. A symmetric next box with coordinate radii at least these output bounds provides an explicit inclusion witness for T4(a); comparison to the same declared state radii provides an invariant witness for T4(b). Arithmetic/storage/call identities remain part of the witness. A failed conservative range test can occur despite actual cancellation or bounded trajectories, and must be reported as lack of certification rather than an observed escape.

The implementation may tighten this witness by intersecting two proved row intervals. Let R=sum_j|w_j|B_j and let r bound the row's affine execution error. The exact affine value is in [bias-R,bias+R], so the rounded affine value is in [bias-R-r,bias+R+r]. It also lies in [-A_d,A_d] by (6). Their intersection therefore still contains every rounded value. Identity preserves this interval, while monotonic ReLU sends its endpoints to their nonnegative parts; the maximum magnitude of those activated endpoints is a valid next symmetric radius. This intersection uses two proved enclosures, not a desired state cap or sample-based truncation.

## T5 — Affine/ReLU layer bounds and repeated calls

For coordinatewise ReLU phi, ||phi(z')-phi(z)||_p<=||z'-z||_p for every standard p in [1,infinity].

**Proof.** For scalars the nonnegative-part map satisfies |max(0,a)-max(0,b)|<=|a-b| by considering whether each is nonnegative. Apply this coordinatewise; sum p-th powers and take roots, or take the coordinate maximum for p=infinity. ∎

In the following layer inequalities, the norm is one of these stated standard l_p norms, including the implemented infinity norm. A different norm requires its own activation Lipschitz constant and the corresponding extra factor. Thus for exact layers F(x)=phi(Wx+b), F'(x)=phi(W'x+b'),

\[
\|F'(x')-F'(x)\|\le\|W'\|\,\|x'-x\|,
\quad
\|F'(x)-F(x)\|\le\|\Delta x+\delta_b\|.
\tag{7}
\]

These inequalities also hold for identity activation. In the infinity norm, if |x_j|<=B_j then a valid same-input drift constant is

\[
a=\max_i\left(\sum_j|\Delta_{ij}|B_j+|\delta_{b,i}|\right),
\quad
L=\|W'\|_\infty=\max_i\sum_j|w'_{ij}|.
\tag{8}
\]

**Proof.** Apply ReLU's Lipschitz inequality to the corresponding affine differences, then the induced-norm or coordinatewise absolute-value bounds. ∎

The specified finite ReLU chooses a finite input word or canonical zero exactly. If its affine input has error bounded by rho, its post-ReLU error relative to the exact layer is also at most rho. There is no missing activation rounding term for this specific implementation; a different activation kernel needs its own bound. A change in ReLU activation pattern does not invalidate (7), so a hard-branch margin is not required merely to analyze continuous ReLU.

For a recurrent layer F(s,u)=phi(As+Bu+b), with the same u on both executions, use L=||A'||_infinity. Its drift bound includes both Delta A times the old state envelope and Delta B times the common input envelope, plus delta_b. This follows by expanding F'(s',u)-F'(s,u): the B'u terms cancel. If inputs differed, that cancellation would fail and an additional certified input-difference term would be needed.

More generally, if the trusted input relation guarantees that only columns J may differ, the first-layer infinity gain is `||W'[:,J]||_infinity`: `W'(x'-x)=W'[:,J](x'-x)_J`. All equal coordinates still participate in range and same-input endpoint-drift calculations. Subsequent layers generally differ in every coordinate and use their full gain. For a fixed multi-layer state step with local gains L_1,...,L_m and forcing beta_1,...,beta_m, T2 yields the step bound

\[
E_{next}\le\left(\prod_{j=1}^m L_j\right)E_{state}
+\sum_{j=1}^m\beta_j\prod_{k=j+1}^m L_k.
\]

Every internal old/new domain must be included in this construction. A larger joint box for both rounding/drift calculations is valid, while separate endpoint output boxes can reduce later enclosures. The interface's claim that non-J coordinates are equal requires provenance; it cannot be justified merely by requesting a smaller gain.

If a physical matrix is called more than once, (7) holds at each call, but (3) includes every call's forcing and propagation factor. Weight sharing does not remove repeated arithmetic or repeated perturbation effects. As an exact scalar example, applying old W=1 twice and new W'=1+c twice at x=1 gives difference 2c+c^2, not the single-call c. Its inputs at the second call also differ. A certificate omitting that second site is incomplete even though the endpoint bank is shared.

ReLU is not equivariant under arbitrary orthogonal rotations. For R=((0,-1),(1,0)) and x=(0,1), phi(Rx)=(0,0) but R phi(x)=(-1,0). Orthogonal coordinate changes therefore do not automatically preserve a ReLU program or its coordinatewise box/activation semantics.

### T5(a): exact-map Lipschitz constants do not transfer to rounding

For the exact scalar map F(x)=x/2 the Lipschitz constant is 1/2. In either stated format, let x=eta and x'=2eta. With separate RNE multiplication by stored 1/2 and addition of zero, Fhat(x)=0 by ties-to-even and Fhat(x')=eta. Hence

\[
|\widehat F(x')-\widehat F(x)|=\eta>	frac12|x'-x|.
\]

Both inputs are legal finite words. The exact-map constant fails for the rounded map on this finite domain; the two-residual recurrence remains valid. On real input domains, rounding also has jumps at quantization boundaries and need not have any finite global Lipschitz constant across such a boundary. This latter real-domain statement is distinct from a fixed finite raw domain, on which a finite maximum pairwise ratio exists whenever the domain has more than one point.

## T6 — Hard branches require guard margins

Use branch(g)=1 for g>0 and0 otherwise, including branch(0)=0. Suppose actual old/new finite guards satisfy |ghat'-ghat|<=zeta and a uniform old actual-guard margin |ghat|>=m>zeta. Then the two branches agree.

**Proof.** If ghat>=m, then ghat'>=ghat-zeta>=m-zeta>0. If ghat<=-m, then ghat'<=ghat+zeta<=-m+zeta<0. The old guard is nonzero in either case and both signs agree. ∎

A valid zeta can be derived from T1 for the guard computation: state amplification plus same-input endpoint drift plus both guard execution residuals. Thus the margin must cover arithmetic as well as an ideal parameter perturbation.

Alternatively let an exact old guard have |g(x,u)|>=m and fixed sign throughout the covered domain. Suppose its old execution error is at most rho_g and its new actual guard differs from that exact old value by at most L_gE+a_g+rho'_g. If

\[
m>\max\{\rho_g,L_gE+a_g+\rho'_g\},
\tag{9}
\]

both actual guards have that same exact sign. This follows by the same one-sided estimates; it is an alternative accounting route, not a reason to add already included residuals twice.

Strictness matters. Old actual guard eta and new actual guard zero have margin m=eta and change zeta=eta but different >0 decisions. More generally the real branch map 1_{x>0} sends epsilon and -epsilon to outputs differing by one although their inputs differ by 2epsilon, for every real epsilon>0. Thus there is no finite Lipschitz bound across zero. In one fixed BF16/FP32 format the smallest raw gap is finite; using eta and -eta is a concrete small finite counterexample, not an assertion of arbitrarily small distinct representable values within that fixed format.

A margin can justify applying branch-local maps along a common path only if the remaining path's state domains, totality and effects are also covered. A failed margin test does not prove that branches must differ; it means the proposed same-branch certificate is unavailable. ReLU's continuous bound in T5 does not require this same-branch assertion.

This theorem does not provide an arbitrary cross-branch output bound or claim that the registered affine/ReLU propagation engine implements general control-flow graphs. If branches can differ, a separate proof must cover their paired successor maps and effects; no such general integration is completed here.

## T7 — Observation and finite-output separation

If a fixed exact observation O is C-Lipschitz on the reached cross pairs, a state bound E_t implies

\[
\|O(\widehat x'_t)-O(\widehat x_t)\|\le CE_t.
\]

This is the definition of Lipschitz continuity. Exact coordinate selection has C<=1 in the infinity norm. If observation execution is rounded or its endpoints change, applying T1 to the observation adds its appropriate same-input drift and two execution residuals. A bound on selected output ports alone does not constrain other state coordinates; those may affect later selected outputs.

For finite canonical full observed outputs in one fixed format, a certified infinity difference bound B<eta implies equality of their raw words. Every finite decoded value is an integer multiple of eta, so a nonzero coordinate difference has magnitude at least eta; canonical zero makes decoding injective. Equality B=eta is insufficient, witnessed by output zero versus eta. Signed-zero admission without canonicalization also invalidates the inference from equal real values to equal words.

This conclusion has the quantifiers of its domain proof. A final-time gap does not prove equality at earlier times. Full trajectory equality requires the corresponding gaps/local BIT facts at every protected point together with the A3 initial-state, common legal input, complete covered-effect/interface, invariant and same-snapshot scheduling premises. If those are supplied, A3's lockstep induction gives the protected trace result. A numeric B3 receipt itself does not publish a new BIT authorization.

For relative observed-error claims, let B_t bound the actual observation difference and let m_t>0 be a proved lower bound on the norm of the actual old observation for every admitted initial pair/input history at time t. Then the relative error is at most B_t/m_t by division by a positive denominator. A full-horizon relative bound may take max_t(B_t/m_t), or use one positive uniform lower bound m and max_t B_t/m. A sampled positive minimum does not supply this universal lower bound.

For nonnegative atol,rtol, the sufficient mixed-budget test B_t<=atol+rtol*m_t implies difference<=atol+rtol*||old observation|| whenever m_t is a certified nonnegative lower bound. This mixed test remains meaningful at m_t=0; a relative-only quotient does not. The condition must hold at every observed time for a full-prefix claim. Contraction of a state norm does not by itself give a positive lower bound on the reference observation.

## T8 — Read-only receipt soundness and stage boundary

Assume a trusted verifier reconstructs the fixed endpoint banks and every shared site, graph/activation, format/policy, initial relation, legal input domain, complete observation, schedule, horizon and domain-proof method. It accepts a numerical budget only after validating the relevant initial inclusion, joint range/totality and recurrence obligations and comparing the resulting bound to the requested budget.

If the method is a finite analytic tube, T4/T2 give the bound only through its declared horizon. If it is a uniform invariant with the hypotheses of T3/T4(b), it can justify the explicitly stated all-time envelope. For the implemented recurrent full-prefix observation the budget must cover max_(0<=k<=T)E_k; the feedforward final-output observation uses the final layer bound. Separate complete finite enumeration covers exactly its enumerated initial pairs/input histories/horizon and does not, by itself, supply an unbounded-time theorem or add an implemented enumeration receipt path. A seeded sample remains sample evidence.

**Proof of the receipt's claim.** The verified initial relation supplies the induction base. The verified joint-domain and numerical obligations supply each induction step. The resulting recurrence bounds the full analyzed state; the declared observation rule and budget comparison give the accepted observation claim. No verifier transition writes an endpoint/state/optimizer bank, so this proof produces evidence without publication authority. ∎

Any missing shared site, unsupported domain provenance, changed policy, stale/inconsistent snapshot, unproved initial relation or failed range/margin obligation must cause refusal or a separately named restricted claim. A coherent new trusted-caller request with a valid recomputed record is a new diagnostic, not a violation of historical-intent authentication. Unkeyed digests establish neither provenance nor authority by themselves.

Fixed endpoints exclude continual update/capacity analysis. General concurrency, arbitrary compiler/FMA/reassociation changes, GPU/native-BF16 certification, hardware faults, full host formal correctness, universal learning improvement and later P2 stages remain outside these proofs. Finite experiments and independently checked references support their stated instances without being promoted to complete machine proofs.
