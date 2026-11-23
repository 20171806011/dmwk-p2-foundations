# P2-B3 — Control-flow margins and rounded-map boundaries

This specification and the proofs below are saved before the control-flow implementation. They refine the B3 mathematical checkpoint for a fixed hard guard and do not introduce a new state compiler, live update policy or global reachability method. All APIs described here are read-only diagnostics.

## 1. Fixed guard and two actual domains

Use the strict guard **g>0**: a zero or negative guard takes the false branch. Fix stored finite old/new affine coefficients and biases, decoded exactly into rationals,

\[
g(x)=a^Tx+b,\qquad g'(x')={a'}^Tx'+b'.
\]

The actual old and new input words decode to x and x'. They may be different intermediate activations or states even when the program receives the same external input. State the two containing boxes independently:

\[
K=\{x:|x_j|\le B_j\},\quad
K'=\{x':|x'_j|\le B'_j\},\quad
\|x'-x\|_\infty\le E.
\]

Their role is conditional containment. A declared box is not a proof that all program trajectories remain in it. A caller must supply that global inclusion/invariant separately, or limit the claim to the explicitly declared finite input-pair family. The reference does not turn observed extrema into global bounds.

Both guard executions use fixed bias-first, ascending-column, separate nearest-even multiply/add, canonical zero and gradual underflow. Let their errors relative to the exact maps be r and r', with proved bounds rho and rho' on K and K' respectively. The reference obtains each endpoint's analytic range/error proof independently from the read-only B2 box machinery. Its finite diagnostic can instead measure exact local errors on each actually executed input pair. Unsupported rounding/reduction/fusion policies and uncertified ranges are refused.

## 2. Strict margin theorem

Let Delta_a=a'-a and delta_b=b'-b be exact differences of decoded stored endpoints. Define

\[
D=\sum_j|\Delta_{a,j}|B_j+|\delta_b|,\quad
L'=\sum_j|a'_j|,\quad
\kappa=L'E+D+\rho+\rho'.
\]

Then the two executed guards satisfy

\[
|\widehat g'-\widehat g|\le\kappa.
\]

**Proof.** Subtract the exact expressions and add the two execution errors:

\[
\widehat g'-\widehat g
={a'}^T(x'-x)+\Delta_a^Tx+\delta_b+r'-r.
\]

The triangle inequality and the two box/radius assumptions give the displayed bound. The old range K controls the same-input endpoint change, while K' is needed to certify the new execution's rounding and totality. Omitting either endpoint's rounding term is not generally valid. ∎

The old exact interval is [ell,u], where

\[
\ell=b-\sum_j|a_j|B_j,\qquad
u=b+\sum_j|a_j|B_j.
\]

The old executed interval is contained in [ell-rho,u+rho]. If either

- positive branch: m=ell-rho>kappa, or
- negative branch: m=-u-rho>kappa,

then every admitted pair in the stated two-box/radius relation takes the same branch. **Proof:** in the positive case, old guard>=m and new guard>=old guard-kappa>0. In the negative case, old guard<=-m and new guard<=old guard+kappa<0. Thus both strict-guard decisions agree. ∎

This is deliberately sufficient and conservative; the old error appears in the interval margin and again in the change bound. A sharper argument may reduce that conservatism but must retain valid error accounting. A zero old guard, an interval crossing zero, or m<=kappa is refused by this proof route. Failure to certify does not establish that the branches actually differ. At equality a general claim is unsafe: old guard +eta and new guard zero change the strict decision from true to false when m=|change|=eta.

The low-level scalar margin predicate validates the strict inequality only. It does not authenticate supplied bounds or establish domains. The full guard routine constructs its own endpoint/domain/error quantities. Neither routine authorizes a weight commit.

## 3. Finite pair diagnostics and branch jumps

For an explicitly supplied finite family of stored pairs, execute both affine guards, record their exact and rounded values, local absolute error sums, raw output words, and branch decisions. Optional box/radius assumptions must be checked against **both** decoded inputs. These observations are complete for the listed family only. They are not global trajectory evidence unless a separate coverage argument identifies that list with the whole legal domain.

For the branch output H(z)=1 when z>0 and H(z)=0 otherwise, changing an old guard zero to a new guard eta changes output from 0 to 1. This can be achieved by changing the input of g(x)=x from zero to eta, or changing a zero bias to eta at zero input. Eta is the format's smallest positive subnormal: 2^-133 in BF16 and 2^-149 in FP32. These are actual finite-format jumps. The continuum statement “arbitrarily small perturbations” refers to real epsilon>0 at the threshold; fixed formats have a minimum nonzero magnitude and must not be described as supporting smaller stored values.

Both branch functions 0 and 1 are smooth, with Lipschitz constant zero. Their switched map is discontinuous. Smoothness or a branchwise Lipschitz bound alone therefore does not establish a joint map bound or preserve branch-dependent side effects. If a margin cannot be proved, one needs an independently proved global/combined Lipschitz property or a branch-change budget. For example, if branch c' has state Lipschitz constant L_c' on the two-domain envelope and

\[
\sup_{x\in K}\|F'_{c'}(x)-F_c(x)\|\le J_{c',c},
\]

then that branch pairing has exact bound L_c' E+J_c',c, with both execution errors added. Every possible branch pairing and its domains must be covered. This formula is a proof obligation, not an implemented automatic branch analyzer. Even a numeric output bound does not cover unmodeled control-flow side effects.

## 4. ReLU does not commute with arbitrary rotations

Let R=((0,-1),(1,0)), a 90-degree rotation, and x=(1,-1). Then

\[
\operatorname{ReLU}(Rx)=(1,1),\qquad
R\operatorname{ReLU}(x)=(0,1).
\]

The difference is (1,0). This is exact arithmetic on small representable values and is also checked under both declared floating policies. Coordinatewise ReLU is 1-Lipschitz in the usual l_p norms, but it is not equivariant under arbitrary rotations. Orthogonal coordinates cannot therefore be moved across ReLU without changing the function. A 90-degree rotation is also an infinity-norm isometry in this example; no norm-distortion explanation removes the failure.

## 5. An exact-map Lipschitz constant need not hold for its rounded map

For F(x)=x/2, the exact map has L=1/2. At x=eta and x'=2eta, the stored separate-RNE results are respectively zero (a nearest-even half-subnormal tie) and eta. The input difference is eta and output difference is eta, so the rounded finite-pair ratio is 1>1/2. B3's exact-map recurrence must therefore retain execution errors; it must not simply assign the exact L to the rounded staircase.

A second example demonstrates why **both** execution errors matter. With precision p=8 or 24, take F(x)=1+x,

\[
x=2^{-p},\qquad x'=x+2^{1-2p}.
\]

Both inputs are stored exactly. Old output rounds to 1 by ties-to-even; new output rounds to 1+2^(1-p). The input difference is e_0=2^(1-2p), the old signed error is -2^-p, and the new signed error is 2^-p-e_0. Consequently

\[
e_0+|r|+|r'|=2^{1-p}
\]

equals the actual output jump. Removing either nonzero error term makes the bound too small. The rounded output/input ratio is 2^p although the exact map has L=1. These are one-step boundary examples, not empirical claims about long-time instability or a global optimal rounded Lipschitz constant.

## 6. Implementation and evidence boundary

`control_flow.py` implements strict margin construction, the standalone strict predicate, finite-pair diagnostics and exact finite-word ReLU using rational accounting and read-only B2 traces. `verify_control.py` constructs the named counterexamples and uses fixed seed 20261114. The actual `control_results.json` run passed **1,578 explicit checks** with **28 expected refusals** and no unexpected failure. Its recorded runtime was approximately **4.079 seconds**, an observation of this small run rather than a performance benchmark.

Per format, two complete small grid/offset families contribute 81 pairs each; 24 seeded affine guard fixtures contribute five pairs each; the three hard-branch boundary pairs and two rounded-map counterexamples contribute five further pairs. That is **287 guard-pair executions per format**, plus the two matrix traces for the ReLU/rotation example. The two complete families exhaust only their declared grid/offset alphabets, not all floating inputs in the analytic boxes. The boxes' universal conditional guarantee comes from the preceding range/margin proof.

Across these recorded diagnostics, each format performs 1,136 multiplies and 1,136 additions. BF16 uses software RNE. The local FP32 path executes 2,272 native scalar operations and checks their words against exact rounding. No native BF16 or GPU operation is inferred. The finite cases retain endpoint words, both actual inputs, signed guard errors, absolute error terms, branch outcomes, domain/radius checks and arithmetic counts. Seeded cases are finite samples, not global-invariant proofs.

These diagnostics neither publish weights nor alter B1 authorization. No new program compiler, GPU/native-BF16/concurrency certification, generic branch-verification algorithm or full machine proof is claimed. Independent verification is assigned separately by the coordinator and must use a distinct rounding/algebra oracle.
