# P2-B4 — Capacity and stability across repeated updates

This stage distinguishes algebraic histories, stored endpoints, exact deterministic authorization and read-only numerical comparisons of changing histories. The [checkpoint](P2_B4_Mathematical_Checkpoint.md) predates implementation. Earlier P1/P2 artifacts are read-only dependencies; no predecessor suite or optimizer trajectory is replayed.

## 1. Update index, execution time and schedules

Let k count accepted endpoint publications, including an accepted no-op if the interface permits one; the number of nonzero increments is a separate statistic. For one physical n-by-d weight bank, w_k is its stored raw tensor and W_k its exact decoded matrix. Every accepted increment is

\[
\Delta_k=W_{k+1}-W_k.
\]

This is exact subtraction over Q, embedded in R, not a floating subtraction instruction or ideal proposal. Its entries need not themselves be representable words. Each physical bank used by several sites has one endpoint identity per version. Bias is fixed or included as an explicit shared endpoint component; independent site biases require separate labelled components or one-hot affine lifting.

The inherited numerical policy admits canonical finite BF16/FP32 words, rejects stored negative zero/NaN/infinity, uses nearest-even rounding and gradual underflow, and canonicalizes arithmetic zero to +0. The fixed affine graph is bias-first, ascending-column separate multiply/add, followed by the declared identity/ReLU operation. Let eta denote the format's smallest positive subnormal and Fmax its largest finite magnitude. Every operation must satisfy the declared totality/range proof or actual finite-trace check. FMA, reassociation, changed accumulator precision and unmodeled kernels require a new certificate.

Let t count completed synchronous state transitions. A declared schedule k(t) selects the accepted version snapshotted for transition t. In a chronological publication history k(t) is nondecreasing, may repeat while no update occurs, and may skip versions when several publications occur between ticks. The graph, input policy and allowed serial publication boundaries are explicit. Each transition reads one complete version and one complete old-state snapshot, then commits its complete successor with bit-preserving storage.

A switched mode may revisit a previous numeric bank by a new publication with a later version. Nondecreasing version indices do not forbid repeated numerical endpoint values. No arbitrary within-transition replacement or unmodeled asynchronous update is included.

## 2. Three comparison references

1. **Original reference:** compare a current endpoint W_k to W_0 at the same activation, or compare the scheduled execution W_(k(t)) to a specified execution using W_0. The latter also has state/input-domain and execution-error obligations.
2. **Adjacent endpoint:** compare W_(k+1) to W_k. A local exact residual, finite-domain BIT certificate or numerical bound has its declared domain and graph. It is not automatically an original-reference trajectory bound.
3. **Two histories:** compare endpoint histories W^A and W^B with explicitly bound schedules k_A(t),k_B(t), admitted initial-state pair relation and common external input history. The reference may itself change. An adjacent-history comparison is meaningful only after both complete histories and schedules are stated.

Every numerical record names its reference. A final difference from W_0, a sequence of adjacent differences and a difference between two state trajectories are different quantities. Summing adjacent numerical tolerances need not give a useful all-time bound; state amplification and both executions' roundoff remain.

## 3. Global spaces and history provenance

Let 𝕂 be Q or R, with n,d positive integers; the separate plain symbol K denotes a finite task/update-prefix index when used below. A protection subspace V must contain all relevant legal activations in the same physical coordinates across all shared calls, allowed initial states, input histories and reached states in its claimed scope. A sampled span is not such a proof. If reachability changes with endpoints, either supply a common containing invariant for the whole admitted history or refresh the coverage proof before relying on a new space.

Define the exact annihilator

\[
\mathcal U(V)=\{\Delta\in \mathbb K^{n\times d}:\Delta v=0\text{ for every }v\in V\}.
\]

A fixed-space policy uses one V throughout. A cumulative-task policy has task spaces V_i and protects their sum V_cum,K=sum_(i<=K)V_i. A moving-space policy uses a current V_k without assuming inclusion of past spaces. The word “capacity” must identify which of these policies and which evidence establishes coverage.

For cumulative tasks, r_K=dim V_cum,K and c_K=d-r_K. A rational generator H_K represents the cumulative space exactly; redundant columns are permitted but ranks are computed in exact algebra. A proved conservative containing space gives conservative capacity. A merely sampled rank gives no globally safe free directions.

## 4. Task anchors and admission times

A task anchor is a specified 𝕂-linear map L_i:V_i->𝕂^n, not merely a space V_i. A bank satisfies the task when its restriction to V_i equals L_i. Task i has an admission publication index a_i. If its desired anchor is current behavior, L_i=W_(a_i)|V_i; if it has an externally specified target, satisfaction at admission must be checked or established by a permitted repair.

Joint compatibility requires every finite relation sum_i v_i=0, with v_i in V_i, to imply sum_i L_i(v_i)=0. Pairwise overlap consistency alone is not assumed sufficient for three or more subspaces. Compatibility is an exact algebraic condition; representable endpoint existence and actual program behavior require additional checks.

After admission, cumulative annihilating increments preserve that task's admission anchor in exact algebra. Admission does not retroactively change earlier outputs or make an old unprotected history safe. If a task was already required from time zero, preservation from admission onward cannot satisfy that earlier obligation by relabelling it.

## 5. Distinct capacity objects

For a fixed working space V, the unrestricted exact update space has dimension n(d-dim V). Individual update rank, a generator rank cap, cumulative rank, target-response image dimension and a persistent low-rank adapter are distinct constraints. A rank-capped family is generally nonlinear, not a vector space assigned the unrestricted dimension.

For a target-input matrix X, the exact response map is Delta->Delta X. Its quotient-target rank is rank([H X])-rank H. Feasibility of a prescribed response requires all protected linear relations among target columns to be respected; the presence of a nonzero update is not enough.

Stored endpoints form a finite set under the fixed format. At old bank w and declared finite family E, let E_ALG(w,V) consist of endpoints whose exact decoded difference annihilates V. Let E_BIT(w,Omega) consist of endpoints whose fixed-graph full declared outputs/effects equal the old bank's on every raw context in the completely specified domain Omega, with totality there. The observation/domain must state whether this is local call equality or a richer protected context. The finite enumerator's raw BIT classification is local complete-call equality; its separate E_CERT group records the actual A3 checker, which can additionally require original-state admissibility, invariant and interface obligations. Even a raw-equal no-op can lack that stronger authorization if the supplied old endpoint violates those premises.

ALG and raw BIT are not generally nested and are not vector spaces over Q or R. The selected live contract may require a complete authorized BIT gate or ALG_AND_BIT; neither is silently weakened after refusal. No finite raw BIT classification alone grants live authority.

Finite capacity may depend on the protected anchor, word alphabet, legal raw domain, graph/order and target observations. Cardinality or response-signature counts must hold these fixed. Within one fixed absolute endpoint universe, equal protected exact anchors give the same ALG endpoint class; along a fixed complete-domain BIT chain, the BIT equivalence class also stays the same. Local rank/step/proposal/optimizer constraints can nevertheless change which members are reachable next. Saturated and zero-bank examples with different anchors are not a loss of global class cardinality along one fixed-ALG history.

A finite number of distinct endpoints can be revisited indefinitely in an abstract serial model, but that is not a guarantee of infinitely many distinct learned functions or useful progress. Pigeonhole repetition does not imply eventual periodicity under arbitrary input/update choices or unbounded optimizer clocks.

## 6. Changing execution maps and joint domains

For a history H, let F^H_t be the exact real state map of its selected stored endpoints at time t, and Fhat^H_t its fixed numerical execution. At every step compare the two histories under the same admitted external input u_t:

\[
\widehat s^H_{t+1}=F^H_t(\widehat s^H_t,u_t)+r^H_t.
\]

The implemented norm is infinity; general proofs allow one fixed specified norm with justified constants. A bound on each map in a different norm is not a common contraction certificate. State/input concatenation and the coordinates that may differ are explicit; common input coordinates do not contribute to the state-difference gain but remain in parameter forcing and range bounds.

A finite two-history tube supplies separate state boxes at every time and joint internal domains covering both histories and every comparison point. A common family invariant must cover every mode allowed by the claimed schedule family and preserve its boxes for every admitted input. Constants and no-overflow proofs must be recomputed or proved uniform across changed banks. A fixed-endpoint B3 certificate is not silently valid after a patch.

Exact affine/ReLU maps can be continuous and Lipschitz while their rounded maps are staircases. Both execution residuals remain explicit. Hard guards use the previously fixed `g>0` convention and need strict executed-margin certificates or a separately proved paired-branch analysis. ReLU pattern changes alone do not invalidate its continuous Lipschitz bound.

## 7. Numerical budget ledger versus exact D ledger

A read-only numerical ledger binds both endpoint histories and schedules, domains/provenance, initial relation, all shared sites, graph/activations, formats/policies, horizon, observations and budgets. A full-prefix budget records a nondecreasing envelope such as max_(j<=t)E_j or checks each declared per-time budget. A final small error cannot erase an earlier violation. This ledger authorizes no weight/state publication.

An exact-D serial owner instead retains the unchanged trusted B1/A3 authorization gate, complete legal context domain and exact selected claim. Its owned snapshot includes the endpoint version, protected state/tick, optimizer state, graph/domain/policy/schedule identifiers and the B4 history/ledger data it promises to update atomically. Prepare/check work is pure with respect to the owned snapshot; a successful publication exposes one validated replacement state, and refusal preserves the entire old state. The mathematical theorem applies only when the implementation establishes this combined publication boundary.

The D observation projection contains the protected computational state, covered outputs and effects. Accepted updates may change weight words, version, optimizer and ledger metadata, so the full owned bank is not equal to an unpatched reference bank. Those metadata may influence D only through the declared checked interface. Rejection rollback, in contrast, requires equality of the entire owned before/after snapshot, not merely its D projection.

Digests and canonical recomputation bind consistency/current identity under the trusted API; they do not authenticate historical intent or prove caller-supplied domain assertions. Coherent new valid trusted-caller proposals remain possible. Hardware faults, private-runtime mutation, crashes and general concurrent publication are excluded from this serial contract.

## 8. Evidence and completion boundary

All general theorems are handwritten conditional proofs. Finite named endpoint families, complete finite histories, seeded stress tests, software BF16, audited local CPU FP32 and independent exact references have separate recorded scopes. No complete proof-assistant result or GPU/native-BF16/general-compiler certification is inherited. Nonzero A response or improvement on a stated toy loss is not universal learning performance. This stage saves a C1 handoff but does not implement or certify the C-series compiler/kernel.

## 9. Concrete reference instantiation

The numerical switching interface uses fixed affine/ReLU/identity graphs with one or two recurrent state coordinates, explicit external input boxes and all shared calls. It supports horizons at most 64, at most 128 stored versions per history and at most 16 distinct modes in a common-family proof. Those are implementation limits. `original_reference` requires a one-endpoint old history equal to the new history's initial bank; `adjacent_endpoints` compares indices differing by one in the same complete history; `two_histories` binds both explicitly. Initial-state equality remains a separate relation even under the original-reference label. Skipped and unused versions are bound but are not declared live-authorized by the numerical analyzer.

The common-family method checks every declared mode's rounded image against the common box and every ordered mode pair in the same infinity norm. Its optional all-time bound applies to continuations within that same certified family and input/policy domain, not to an unlisted future patch. The finite selected history still receives its own per-step tube proof.

The exact-D fixture uses B1's unchanged `structural_duplicate_v1` family `[[1,0,theta0],[0,1,theta1]]`, with fixed first two columns. Its two shared deterministic calls prepare `(q,q,0)` and `(u,u,0)`, and the protected state follows same-snapshot Boolean XOR. Legal A input e3 returns theta under the declared graph. The declared toy target is `(1,-1)` and the loss is half the exact squared difference of decoded actual A output. The surrogate gradient is not labelled as the derivative of finite-word rounding.

The B4 owner stages B1 preparation/commit and ledger construction on an unexposed private copy, then publishes one combined owner value. Its administrative accepted-history limit is not a rank budget or a D-error budget. Accepted no-op count, nonzero stored changes, optimizer steps and protected ticks are reported separately. A descriptive sum of adjacent increment norms is a path-length statistic; it is not added again to a direct endpoint or execution bound. Allocation failures, crashes and hostile mutation outside the modeled protocol are not covered by the serial publication theorem.
