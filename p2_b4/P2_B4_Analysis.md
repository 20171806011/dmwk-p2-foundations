# P2-B4 — Changing-history numerical analysis

This document explains the executable numerical route after the mathematical checkpoint. It complements the exact capacity results and the general proofs in `P2_B4_Theorems.md`. It does not certify a live approximate update, replace B1's exact gate or claim general C-series composition.

## 1. Update count is not elapsed execution time

A stored history records banks W_0,...,W_K after ordered replacements. A schedule k(t) selects one complete bank for logical transition t. Several replacements can occur between two transitions, and many transitions can use one bank. The reference therefore accepts repeated or skipped **nondecreasing** version indices; an A,B,A mode sequence is represented by three successive versions whose values revisit A, rather than by rolling back the version index.

Every supplied endpoint, including an unused middle or tail version, is validated for canonical finite words, physical matrix identity, shapes and the fixed graph. The analysis binds all of them. However, a version used by no tick contributes no tick observation or per-tick range certificate. Only the separately requested common-family proof covers every family mode as a possible future transition. Calling an unused version “bound” does not assert that an optimizer forward pass or a branch side effect at that version was analyzed.

Numerical replacements are assumed serialized at tick boundaries and preserve the numerical state. Any optimizer computation, activation-dependent edit, logging effect read by D, branch or state mutation outside the modeled tick must be added explicitly to the graph/event model. It is not protected by silence. The numerical history is a declared analysis input, not evidence that B1 accepted its entries.

The comparison label fixes which weight reference is meant:

- `original_reference` compares a single fixed W_0 with selected versions of a history whose version zero equals W_0.
- `adjacent_endpoints` selects consecutive versions from one common history at each tick. Its two trajectories may still have different states, so the propagated state error is retained.
- `two_histories` compares two explicitly named schedules and endpoint lists.

No label changes the initial relation: initial boxes and the bound on the actual paired difference remain separate premises. Membership of both states in the same box does not imply E_0=0.

## 2. Recomputed endpoint and domain accounting at every time

The fixed graph is a finite composition of affine calls and identity/ReLU activations. It uses the same physical banks at every named shared call, without omitting repeated uses. One or two state coordinates precede any shared external input coordinates. Every transition reads one old state snapshot and commits the full graph output as its successor.

At time t, let F_t and F'_t be the exact real maps defined by the two **selected stored endpoint banks**. Let s_t and s'_t denote decoded actual states, and let the common external input be u_t. The two rounded executions obey

\[
\widehat s_{t+1}=F_t(\widehat s_t,u_t)+r_t,\qquad
\widehat s'_{t+1}=F'_t(\widehat s'_t,u_t)+r'_t.
\]

The core invokes the pure B3 `network_bound` at this actual endpoint pair and the independently propagated old/new state boxes, concatenated with the common input box. It obtains

\[
E_{t+1}\le L_t E_t+\beta_t.
\]

L_t is an exact-new-map infinity-norm state Lipschitz upper bound. At the first layer only state columns contribute to amplification, because the external input coordinates are identical. The common external input still contributes to operation ranges and same-input parameter drift. Subsequent layers use all their differing intermediate coordinates.

For one affine call, beta is the same-input drift from the decoded endpoint differences, plus independently certified old and new arithmetic-error terms. For a multi-call composition, these local terms are propagated through subsequent gains. The returned `network_proof` preserves every call's L, exact same-input drift, rho_old, rho_new, beta, physical bank ID and range proof. Coordinatewise ReLU adds no word-rounding error in this implementation and is 1-Lipschitz; it does not make arbitrary hard branches safe or commute with arbitrary rotations.

Both old and new output boxes are propagated using their own endpoint ranges. The next tick starts from those new boxes. An optional state cap is checked against each enclosure and never used to truncate it. A failed conservative range/inclusion check means this method could not prove the requested statement; it does not necessarily mean an actual trajectory overflows or leaves the cap.

The linear recurrence and the direct product-sum agree exactly:

\[
E_T=E_0\prod_{t=0}^{T-1}L_t+
\sum_{j=0}^{T-1}\beta_j\prod_{t=j+1}^{T-1}L_t.
\]

Here E_T denotes the computed upper envelope, not necessarily the actual error. The reused B3 exact-rational routine independently reconstructs every prefix product-sum. No numerical SVD rank or observed sample maximum supplies a domain guarantee.

## 3. Drift to the original endpoint and alternative ledgers

For a physical matrix, the actual stored increments satisfy

\[
W_{k(t)}-W_0=\sum_{j<k(t)}(W_{j+1}-W_j).
\]

This is exact subtraction of decoded endpoint values, not a target-format subtraction instruction or an ideal optimizer proposal. Bias differences obey the same identity. For an affine map on a current containing box K_t, a direct net-endpoint drift bound can be used, or a sum of valid adjacent-increment bounds evaluated on that same current domain. They are **alternative** upper bounds. Adding both would count the same drift twice.

Past adjacent bounds computed on smaller past domains do not automatically apply at the current domain. A proved common invariant can supply one common domain for all of them; otherwise the needed bounds must be recomputed. At the level of exact nonlinear maps, a same-input map difference can also telescope, but each intermediate-map bound must hold at that same input/domain. It is not a statement that different historical trajectory states can be substituted into one telescope.

The implemented switching core uses the direct selected endpoint pair. It records the physical endpoint difference and lets B3 account for the complete graph. Generation, projection, optimizer and commit-rounding effects already present in those stored endpoints are not appended as new error terms. Only the two actually compared executions contribute the per-step execution errors. In particular a final cancellation of weight increments does not cancel previous state perturbations or earlier budget violations.

## 4. A common family invariant and uniform switching envelope

The optional `common_invariant` method receives a symmetric state box and either an explicit mode family or the distinct union of both full histories. Every supplied history version, even a zero-runtime version, must belong to that family. The fixed shape/call-site/layout checks apply to extra declared future modes as well.

The checker proves two different obligations:

1. For **every** family mode, the rounded graph maps the common state box and complete external input box back into the common state box, with all intermediate totality/range conditions established.
2. For **every ordered pair** of family modes, the two-execution bound is established on that common domain. The maximum state gain L and forcing beta are measured in the same infinity norm.

If L<1, the conditional envelope

\[
\sup_{t\ge0}E_t\le\max\left(E_0,\frac{\beta}{1-L}\right)
\]

follows by the scalar contraction recurrence and induction on domain inclusion. It covers every finite continuation choosing only those family modes, with the same input domain, graph, numerical policy and state-preserving update semantics. It is a theorem under these continuing hypotheses, not an inference from the finite execution history or a promise of infinite physical runtime.

Even after proving the common family, the finite history analyzer rebuilds its per-step endpoint-specific tubes. Those tighter finite coefficients are checked against the separate family-wide coefficient envelope. A family proof is not silently inferred from small finite error or from a spectral radius below one for individual modes. Without strict common contraction the implementation returns no uniform contraction bound, even if a particular finite run is small.

## 5. Individually stable modes can amplify under switching

Let

\[
A=\begin{pmatrix}0&2\\0&0\end{pmatrix},\qquad
B=A^T=\begin{pmatrix}0&0\\2&0\end{pmatrix}.
\]

Both A^2 and B^2 are zero, so each fixed exact autonomous mode reaches zero after two steps. But

\[
BA=\operatorname{diag}(0,4),
\]

so alternating A then B multiplies the second coordinate by four every two exact steps. From (0,1/8), the switched sequence A,B,A,B produces (1/4,0), (0,1/2), (1,0), (0,2). Repeating only A produces zero from the second step onward. These displayed small values and operations are exactly representable in both formats; the actual finite checks must still execute the declared graph.

Separate norms can conceal the problem. In norm_A(x)=max(|x_1|/4,|x_2|), A has induced gain 1/2. In norm_B(x)=max(|x_1|,|x_2|/4), B has induced gain 1/2. Switching the norm without tracking its conversion factors does not give a common contraction. In fact no single induced norm can make both gains strictly below one, because then ||BA||<1 would contradict its eigenvalue four. In the implemented common infinity norm both mode gains are two, so the unjustified contraction claim is refused immediately; nonzero common-box invariance also fails for this family.

This is an exact real switching counterexample and a finite-format boundary experiment. An indefinitely growing exact sequence eventually exceeds a fixed format's range; it is not a certified infinite floating execution.

## 6. Prefix budgets and initial error

The read-only ledger observes the full state at all times 0,...,T. For each time it records E_t, the running maximum P_t=max_(j<=t) E_j, remaining budget and the first exhausted index. A supplied absolute infinity budget passes only if every prefix bound is at most that budget. Equality is allowed for this numerical budget; it is unrelated to the strict inequality required by a hard-guard margin.

E_0 is charged even for T=0. A history with errors 0,1,0,0 can violate a budget 1/2 at the first transition despite a zero final error. An analogous computed envelope may have a tiny positive final rounding allowance; the prefix decision is unchanged. `BudgetExceeded` exposes the computed ledger without publishing any state. Exceeding a conservative bound budget is not automatically evidence that a particular actual trajectory exceeds it.

This ledger is separate from the exact-D transaction history. The numerical analyzer performs no commits, and a B4 budget receipt cannot be presented as B1 BIT/ALG_AND_BIT authority. The transaction/receipt layer must bind both complete histories, both schedules, all graph sites, domains, initial relation, numerical policy, horizon, prefix observation, budget, version and expected context. Replacing a fixed B3 endpoint after its certificate was issued requires new analysis rather than reusing that certificate under a changed version.

## 7. Cost and reference limits

The executable reference limits an execution schedule to 64 ticks, each history to 128 stored versions, state dimension to one or two, and a common-invariant family to 16 distinct modes. These bounds keep the explicit reference manageable; the mathematical finite-horizon statements do not assume those particular numbers.

Let P count physical bank coefficients/biases, and let Q count coefficients with their call multiplicity in the fixed graph. Validating K stored versions takes O(KP) scalar checks, plus graph/layout checks. The finite tube uses O(TQ) rational field-operation range/error work up to norm-enclosure and graph constants. Retained detailed proofs consume O(KP+TQ) rational/word records rather than just one final scalar. Shared banks save physical endpoint storage but each call still incurs its own propagation obligation.

A family of M modes adds M self-inclusion proofs and M^2 ordered-pair bounds, with O((M+M^2)Q) such field-operation work and retained diagnostic records. The recurrence itself is linear in T. The reused independent reconstruction of every prefix product-sum uses nested suffix-product loops and costs O(T^3) rational multiplications in the present small reference; no optimized asymptotic claim is made for that cross-check.

Rational arithmetic is not unit-cost real arithmetic. Numerator/denominator lengths can grow through repeated gain/range products and exact error sums. Integer division, gcd reduction and outward norm enclosures contribute additional bit complexity. Recorded runtime/size observations from the new verifier describe only its actual fixtures and do not establish a large-model speed or memory advantage.

## 8. Evidence and remaining boundary

The implementation is in `switching_bounds.py`, the precise public shapes in `B4_Interface.md`, and dependency provenance in `b4_runtime.py`. The main changing-history verifier and independent reviewer own separate actual result files; their counts and costs must be read from those files after execution rather than inferred from this derivation. No previous suite is imported or rerun.

BF16 remains software RNE. FP32 point traces use the inherited local scalar execution and exact word audit. The analytic box/recurrence conclusions are conditional handwritten proofs implemented with rational arithmetic; finite tests are not a full machine proof. GPU, native BF16, general concurrency, arbitrary FMA/reassociation, state-changing optimizer side effects, arbitrary branch analyzers and the C-series whole-kernel result remain outside this route.
