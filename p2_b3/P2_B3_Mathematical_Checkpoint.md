# P2-B3 mathematical checkpoint

Saved after reading the B3 plan and B2 handoff, before B3 implementation. The proof scope is fixed old/new endpoints, equal admitted external input and trusted schedule. Numerical evidence is read-only and does not replace BIT/ALG_AND_BIT.

1. **Exact maps plus two execution errors.** At layer/time k let F_k,F'_k be exact real maps, and let both finite executions satisfy xhat_k=F_k(xhat_(k-1),u_k)+r_k and xhat'_k=F'_k(xhat'_(k-1),u_k)+r'_k on jointly certified domains. If F'_k is L_k-Lipschitz in its state argument, ||F'_k(x,u)-F_k(x,u)||<=a_k on the old domain, and ||r_k||<=rho_k, ||r'_k||<=rho'_k, then E_k<=L_k E_(k-1)+b_k with b_k=a_k+rho_k+rho'_k. A rounded staircase is not presumed L_k-Lipschitz. Reversing the split gives an old-map Lipschitz alternative when its domains are proved.

2. **Nonhomogeneous propagation.** For E_0 bounding the actual initial difference and nonnegative L_k,b_k,
   E_t <= E_0 product_(k=1..t)L_k + sum_(j=1..t) b_j product_(k=j+1..t)L_k.
   Empty products are one. The same induction applies to finite layer composition or finite time; shared matrices still require every physical call site and intermediate envelope.

3. **Constant envelopes.** If L_k<=L and b_k<=b, then E_t<=L^t E_0+b sum_(j=0..t-1)L^j. For 0<=L<1 this is bounded by max(E_0,b/(1-L)); at L=1 the envelope is E_0+tb; for L>1 it is L^t E_0+b(L^t-1)/(L-1). These are upper envelopes, not automatic lower-growth or stability claims. Time-uniform conclusions require the same domain/totality/forcing premises for every time.

4. **Domain closure is a separate proof.** Build endpoint-specific finite-operation interval bounds and output boxes. A common box invariant requires both rounded maps to send all admitted states/inputs in the box back into it. A finite tube supplies boxes K_k,K'_k and radii E_k, with initial inclusion and transition inclusion at every step. Domain inclusion and recurrence are proved together by induction. Samples or a bound on the original trajectory alone do not supply modified-domain closure.

5. **Affine/ReLU and branches.** Coordinatewise ReLU is 1-Lipschitz in the implemented infinity norm (and each standard l_p norm). Its finite canonical execution is exact on a finite input word; affine rounding errors remain. Thus a layer has L<=||W'||_infinity and same-input perturbation <=||Delta W||_infinity B+||delta_b||_infinity on ||x||_infinity<=B, or sharper row/box bounds. For recurrent input (state,u), use the state block for L because u is shared. ReLU is not equivariant under arbitrary rotations. A hard branch requires a certified guard margin exceeding a bound on guard change; absent it, arbitrarily small numerical changes can change control flow and yield a discontinuous state jump.

6. **Finite output gap and receipt scope.** A strict full-domain finite canonical-output bound below eta implies those output words agree; <=eta does not. Program BIT lifting still requires the A3 covered-effect/input/snapshot/schedule assumptions. A B3 read-only receipt binds endpoints, all sites, graph/activation, policy, domains and joint closure method, initial relation, horizon, observation and budget. It authorizes no live change. Observed-port bounds alone are not full-state bounds, and a later observation does not erase earlier unprotected effects.
