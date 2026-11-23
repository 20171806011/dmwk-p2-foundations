# P2-B3 — Numerical propagation and domain certificates

This document describes [propagation_bounds.py](propagation_bounds.py), its read-only runtime dependencies and the exact scope of its numerical evidence. [B3_Interface.md](B3_Interface.md) fixes the schema; [P2_B3_Theorems.md](P2_B3_Theorems.md) gives the conditional mathematical proofs. The implementation does not publish an endpoint, change an optimizer or authorize a numerical replacement for a deterministic safety claim.

## Exact maps, rounded maps and the chosen norm

The concrete implementation uses the infinity norm throughout. For a fixed physical affine bank and a fixed activation,

\[
f(z)=\phi(Wz+b),\qquad \phi\in\{\mathrm{identity},\mathrm{ReLU}\},
\]

is an exact rational/real map. The executed map first computes every affine row with stored bias, ascending-column separate products/additions, then applies the declared activation to the rounded word. Finite canonical BF16/FP32 words decode exactly into Q. Nonfinite words and negative-zero input encodings are refused; arithmetic zeros remain canonical +0. The nonlinear word operation is exact: identity preserves the word and ReLU either preserves a positive finite word or returns canonical zero.

Both activations are coordinatewise 1-Lipschitz in the infinity norm. Thus an exact-map Lipschitz upper bound is the maximum absolute row sum of W. For the first layer of a recurrent state update, the input is `(s,u)` and u is identical in the two runs. Only the **state columns** contribute to the initial difference gain. Subsequent layers use all columns, because their intermediate coordinates may differ. Input columns remain present in every operation-range, domain and endpoint-drift calculation.

This is not a Lipschitz claim for the rounded staircase map. A tiny input change can cross a rounding threshold even when the exact affine gain is small. The local bound explicitly includes rounding contributions from both executions. ReLU's Lipschitz property also does not imply equivariance under arbitrary rotations or justify an untracked neuron-coordinate change.

## Shared banks and complete call order

Each bank ID identifies one physical W and bias b. Every call records a unique call ID, its bank ID and its fixed activation. Repeated bank IDs reuse exactly the same endpoint words at all sites. In this reference, bias is part of the shared affine bank as well. The generic graph validator checks adjacent shapes, required banks, unique call labels and that there are no unreferenced banks. It cannot infer whether a structurally consistent supplied graph omits a call from some larger application. The registered analysis and receipt instead bind the entire expected graph, so a subset cannot replace that registered complete call order.

The fixed registry supplies two feedforward graphs and three scalar recurrent interfaces. Their source domains are complete declared canonical-word boxes, not estimated samples. Generic custom-graph helpers prove statements conditional on the supplied graph, domains and input relation; that does not confer provenance for an unrelated application. Read-only receipts separately bind the expected registered graph, domain, endpoints and schedule.

## Local forcing on the joint input box

At one call, let old/new input magnitude boxes be H_old and H_new. Form their coordinatewise maximum H_joint, which contains both. Let the exact decoded endpoint differences be Delta W and Delta b. The same-input affine drift is bounded by

\[
a=\max_i\left(|\Delta b_i|+\sum_j|\Delta W_{ij}|H_{\rm joint,j}\right).
\]

The implementation invokes B2's analytic box proof on **both affine endpoints over H_joint**. That proof certifies every operation range and gives row rounding-error bounds. Let rho_old and rho_new be their separate infinity bounds. ReLU or identity does not enlarge the corresponding exact-versus-rounded discrepancy. Hence

\[
\beta=a+\rho_{\rm old}+\rho_{\rm new},
\qquad E_{\rm next}=L_{\rm new}E+\beta
\]

is a valid local recurrence. Its proof inserts the exact new map at the old input, applies its Lipschitz bound to the input difference, and bounds the endpoint change at that same input. Every inserted evaluation lies in the proved joint domain. One may derive tighter coordinatewise or endpoint-specific estimates, but this implementation retains the displayed sum of three nonnegative scalar contributions for explicit attribution.

Delta W and Delta b come from the actual stored endpoints. They already include optimizer, factor-generation, projection and storage effects. No upstream error ledger is added a second time. Endpoint words remain fixed at every call and time in this stage; continual updates belong to later work.

## Two endpoint-specific output enclosures

Joint-domain certification alone is not an invariant argument. The implementation also propagates the old and new output domains separately from their own input boxes.

For each endpoint/row, B2 supplies a finite rounded-output magnitude bound A_i and a row error bound r_i. With input box H, compute the exact affine radius

\[
R_i=\sum_j|w_{ij}|H_j.
\]

Two valid enclosures of the rounded preactivation are `[-A_i,A_i]` and `[b_i-R_i-r_i,b_i+R_i+r_i]`. Their intersection is

\[
\ell_i=\max(-A_i,b_i-R_i-r_i),\qquad
u_i=\min(A_i,b_i+R_i+r_i).
\]

This intersection tightens two proved enclosures; it is not an arbitrary state cap. Identity preserves the interval. ReLU maps it monotonically to `[max(0,ell_i),max(0,u_i)]`. The next symmetric coordinate radius is the maximum magnitude of the two activated endpoints. The next layer's joint box is recomputed from these separately proved old/new radii.

This can retain useful sign information, for example proving a sufficiently negative ReLU output is zero. It still discards correlations and the nonnegative shape of intermediate boxes when replacing them by symmetric radii, so it may be loose. The generic B2 error recurrence includes additive underflow terms even for many exactly executed zero operations; these can produce small enclosure inflation. No interval is reduced merely because a requested budget or external state cap would otherwise fail.

## Operation ranges and refusal

B2's sufficient local model is `|RN(x)-x| <= u|x|+eta/2` with the exact operation argument certified inside `[-Fmax,Fmax]`. Its recurrence separately bounds each product, rounded product, pre-round sum and rounded accumulator. The additive term covers subnormal rounding. B3 reuses these pure proofs; it does not rerun B2's old verifier or substitute an unguarded gamma model.

A failed joint or endpoint-specific range proof causes refusal. This can be conservative: a finite actual trajectory may exploit cancellation, exact zeros or exact identity operations that the box proof does not capture. Conversely, an actually overflowing point execution is separately refused by the word-level trace. Neither case is reported as a zero error or silently repaired by clipping a state.

## Layer and time product-sums

For certified nonnegative coefficients,

\[
E_{k+1}=L_kE_k+\beta_k
\]

has the exact rational product-sum

\[
E_T=\left(\prod_{k=0}^{T-1}L_k\right)E_0
+\sum_{j=0}^{T-1}\beta_j\prod_{k=j+1}^{T-1}L_k.
\]

Empty products are one and an empty time interval retains E0. `propagate_recurrence` computes the streamed recurrence and an explicit product-sum for every prefix and checks exact agreement. This algebra helper does not establish that its coefficients or initial bound apply to an actual program.

For constant L and beta the reference also checks the geometric expression. If L=1, it is `E0+T*beta`. Otherwise it is `L^T E0+beta*(1-L^T)/(1-L)`, including L=0 and T=0. “Contractive,” “neutral” and “amplifying” classify this upper envelope. They do not assert that an observed trajectory contracts, changes or grows at that rate; nonlinear saturation and rounding can make actual differences much smaller or zero.

The reference supports at most 32 calls per graph and horizons 0..64. General finite-T formulas are mathematical statements; the implementation does not claim unlimited resources. Streaming the recurrence alone takes O(T) rational operations. The deliberately direct all-prefix product-sum check has nested prefix, forcing-index and tail-product loops, giving **O(T^3)** rational operations. This cost is retained rather than describing the full checker as linear time. Rational operand lengths and the size of stored operation proofs also affect cost.

## Finite tubes, common invariants and initial relations

The recurrent registry admits old/new initial states in magnitude-one boxes and explicitly restricts their pair to infinity distance at most E0. For E0=0 this means the same initial state, not merely overlapping boxes. At every time, both executions receive the same admitted external input. The complete input-history domain is every finite sequence of canonical words with the declared magnitude bound.

The finite-tube method begins with both initial boxes. At each time it proves the network ranges and local recurrence on the current joint state/input box, derives both next-state boxes, and continues. An optional external state box is checked for inclusion of the initial and every propagated enclosure. If it is exceeded, the proof refuses. The state is never truncated to that cap and the original domain is never reused without a new inclusion argument.

The common-invariant method starts from a proposed common box containing every admitted initial state. It proves both endpoint image enclosures are contained in that same box for every legal input. Only after that closure check does it reuse the fixed-domain map/forcing certificate through time. Each saved step instantiates the coefficient proof at the current scalar E, while the input range proof can conservatively use the larger common invariant even at time zero.

With a proven common invariant, fixed endpoints and uniform L<1 and beta, the implementation returns

\[
E_t\le\max\{E_0,\beta/(1-L)\}\quad\text{for every finite }t.
\]

It also recognizes the conditional neutral case L=1, beta=0. Other neutral/amplifying finite bounds are not relabeled as time-uniform stability. A finite successful tube alone yields no infinite-horizon statement. Conservative identity-map invariant refusal is possible even when its actual state stays fixed; an amplifying map may instead genuinely leave a proposed box. Those distinct failures are tested separately.

## Observation and actual traces

Feedforward receipts observe every final output coordinate. Recurrent receipts observe the full state at every time from zero through T, so their budget is `max(error_bounds)`, including E0. Using only the final bound would be unsound for an all-time observation when earlier differences are larger.

`trace_network` records actual word inputs, affine operations and activated outputs at each call. It also computes the exact real network at the original decoded input. That ideal network path is distinct from a local exact affine value evaluated at an already rounded intermediate input; the record keeps both instead of conflating them.

`trace_model` checks the declared initial/input domains and executes one finite history. Recurrent next-state words are computed from the same old snapshot, then committed together in the pure reference trace. The trace does not clamp a state back to the initial domain or infer an invariant from samples. Bounds are established independently by the analytic domain proof, while finite traces check the implementation on their stated instances.

## Branches, receipts and unresolved environments

ReLU remains covered by its global Lipschitz and monotone-range facts even when a coordinate crosses zero. A general hard branch requires a separately certified guard margin and branch-domain argument; small numerical perturbation alone does not preserve its choice. [P2_B3_Control_Flow.md](P2_B3_Control_Flow.md) states the separate helper's guard semantics and counterexamples. It does not turn arbitrary control flow into a Lipschitz network.

The read-only receipt binds the selected complete source domain, graph and every shared call, both fixed physical bank sets, initial relation, horizon, proof method, observation, policy, schedule and expected version/context. It proves only that specified numerical statement. B1's exact BIT/ALG_AND_BIT transaction remains unchanged and rejects a B3 receipt as a live publication certificate. Critical deterministic state must still satisfy its selected exact contract; a positive soft-state budget is not a replacement.

Finite canonical output separation can imply word equality only under its separate strict-gap and complete-coverage premises, plus the earlier program-lifting conditions. Relative claims still need a certified nonzero reference bound. No new relative-uniform or multilayer program-authority API is inferred from a finite propagation run.

The actual backend is software BF16 and locally audited CPU FP32. GPU, native BF16, FMA/reassociation or arbitrary compiler changes, general concurrency, crash consistency, malicious private-memory mutation and evolving-endpoint B4 training remain uncertified. General theorems remain handwritten; experimental counts, exact bounds and costs are recorded separately in the actual result JSON.
