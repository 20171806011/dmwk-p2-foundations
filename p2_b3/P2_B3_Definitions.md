# P2-B3 — Nonlinear and finite-time propagation contracts

This stage extends single-call bounds to fixed finite compositions and synchronous state maps. The [mathematical checkpoint](P2_B3_Mathematical_Checkpoint.md) was saved before implementation. P1 and P2 predecessor files remain read-only. A numerical propagation receipt supplies no live BIT/ALG_AND_BIT authority.

## 1. Fixed endpoints and exact versus rounded maps

Every physical bank has fixed old and new admitted finite word matrices throughout the analyzed composition/time interval. Exact decoding gives W,W' and Delta=W'-W in Q, embedded in R. Candidate, optimizer, representation and storage effects are already included in Delta; an upstream ledger is an alternative explanation, not an extra term to add again. All sites sharing a bank refer to these same endpoint tensors; a site cannot silently use an independently patched copy.

At step k, F_k and F'_k denote the exact real maps determined by the old/new endpoint tensors, fixed biases or explicitly changed endpoint biases, activations and input preparation. The actual finite maps are denoted Fhat_k,Fhat'_k. Their difference from the exact maps is an explicitly bounded execution residual, not a presumption that floating operations evaluate the real map exactly.

For common external input u_k and decoded finite states/intermediates xhat_(k-1),xhat'_(k-1), write

\[
\widehat x_k=F_k(\widehat x_{k-1},u_k)+r_k,\qquad
\widehat x'_k=F'_k(\widehat x'_{k-1},u_k)+r'_k.
\]

Finite feedforward composition uses the same notation for successive layers. Recurrent use repeats a specified step graph on one complete old-state snapshot and publishes the complete successor synchronously with bit-preserving storage. Partial in-place updates or a changed schedule are different maps. Endpoints do not evolve during this stage; continual patch evolution belongs to later work.

## 2. Norm, initial relation and joint domains

The generic proofs use a chosen norm on each state/intermediate space and its induced Lipschitz/operator bounds. The implementation uses the vector infinity norm and induced maximum absolute row-sum matrix norm. State and external input are concatenated in a declared order; under the infinity norm the concatenated difference is max(state difference,input difference). Common inputs make the second term zero. An external input is not silently incorporated into a changing state coordinate.

An admissible initial relation R_0 contains exactly the permitted old/new initial pairs. A number E_0 bounds their decoded norm differences. Same initial raw state is the important E_0=0 case, but theorems retain arbitrary certified E_0>=0. Independent initial boxes imply only their maximum possible separation unless a stronger relation, such as equality or a paired enumeration, is proved.

Let K_(k-1),K'_(k-1) be certified old/new state domains and U_k the common legal input domain. Alternatively an explicit relation may restrict allowed pairs and inputs. For the standard split used below, F'_k must be defined on every old comparison point (x,u), and its Lipschitz inequality must hold for each relevant cross pair x in K_(k-1), x' in K'_(k-1) with the common input. A containing joint set on which F'_k is Lipschitz suffices. It is not enough that F'_k is Lipschitz only along its own observed trajectory.

The same-input exact endpoint drift bound a_k applies on the old domain:

\[
\|F'_k(x,u)-F_k(x,u)\|\le a_k.
\]

Execution-error bounds rho_k,rho'_k cover the actual old and new input domains separately. The new execution need not actually run at the old comparison point, but its exact map must be defined there. No floating staircase is assumed to have the exact real map's Lipschitz constant.

Domain coverage must include all admitted initial pairs, all common legal input histories, every shared call and all intermediate layers. A proof on original activations alone supplies no modified-trajectory closure. In particular the old global activation span and a reference subspace used by a geometric estimate are distinct: if a new intermediate lies outside the proved old containing space, any leakage bound needs its own certified envelope.

## 3. Two forms of domain proof

A finite tube consists of old/new domains K_0,...,K_T and K'_0,...,K'_T, together with nonnegative error radii E_0,...,E_T. It supplies initial inclusion and, at every k<=T, totality and output inclusion for both rounded maps plus a recurrence valid on the required cross pairs. Its paired relation is

\[
\mathcal R_k=\{(x,x'):x\in K_k,\ x'\in K'_k,\ \|x'-x\|\le E_k\}.
\]

Inductive transition inclusion proves membership in R_k through the stated finite horizon only. Symmetric coordinate boxes |x_i|<=B_(k,i) are one executable sufficient representation. Rounded arithmetic ranges, not exact-map outputs alone, must remain in the next box.

A common invariant uses time-independent domains K,K' and an admitted input policy whose conditions hold for all times. It requires both rounded transition maps to be total and preserve their respective domains for every admitted state/input, together with the cross-pair bounds. A common symmetric box K=K' is a sufficient special case. A successful finite trajectory is not an invariant proof. Conservative interval failure means the method did not establish closure, not necessarily that the actual transition escapes.

## 4. Executable layers and arithmetic policy

An affine layer starts each accumulator at its stored bias and visits input columns in ascending order, with separate target-format multiplication and addition. Identity and coordinatewise ReLU are the supported nonlinearities. ReLU on a finite word returns that word when positive and canonical zero otherwise; it introduces no extra arithmetic rounding in this specified graph.

BF16/FP32 operands/results use finite canonical encodings, RNE, gradual underflow and canonical +0. Negative-zero inputs, NaNs and infinities are rejected. The constants are p=8 or24, u=2^(-p), eta=2^(-133) or2^(-149), and finite maximum Fmax. Product/add ranges and residuals inherit the B2 graph-specific analysis. FMA, reassociation, an altered accumulator precision, skipped operations or flush-to-zero require a new specification and proof.

For a recurrent affine-ReLU map on concatenated (s,u), write the exact new matrix as [A' B']. A Lipschitz bound in state at fixed input uses A', not automatically the whole matrix. The same-input endpoint drift uses all changed state/input weights and bias on their declared coordinate envelopes. If a more complex fixed step contains several layers, compose their certified local state/input dependencies; do not silently treat each hidden layer as an independent recurrent state update.

## 5. ReLU and hard control decisions

Coordinatewise ReLU is a continuous 1-Lipschitz map in the implemented infinity norm and standard l_p norms. Its activation pattern can change without invalidating that bound. It is not equivariant under arbitrary orthogonal rotations, and its Lipschitz property does not apply to an arbitrary discontinuous branch.

For a hard decision, fix the convention branch(g)=1 when g>0 and 0 otherwise; a zero guard takes the false branch. A branch certificate must bound the actual guard change, including state perturbation, endpoint drift and both relevant execution errors, and prove a strict margin from the threshold. A zero/borderline guard or absent margin is reported as unproved; preserving a continuous ReLU output bound does not by itself preserve a hard program counter or branch-dependent side effect.

This hard-guard analysis is a separately scoped control-flow diagnostic/theorem. The registered propagation graphs themselves support affine identity/ReLU calls; they do not implement arbitrary branched programs or a general cross-branch output budget.

## 6. Observations and quantitative claims

The primary recurrence bounds the complete analyzed numerical state/intermediate vector. A specified exact observation O with Lipschitz constant C converts a state bound E to an observation bound CE. Exact coordinate selection has C<=1 in the infinity norm. A separately rounded or changed observation graph contributes its own execution/endpoint terms; it is not a free readout. Observed-port equality alone does not imply hidden-state equality or protect later observations influenced by hidden state.

Finite-horizon statements quantify k<=T. A uniform-in-time bound additionally requires time-uniform constants and an invariant valid for every time under fixed endpoints, inputs, graph, policy and schedule. A constant greater than one in an upper recurrence permits an exponentially growing bound but does not prove that the actual error grows. Relative observations require a positive certified reference norm; absolute/mixed bounds remain meaningful at zero.

Strict sub-eta separation of full finite canonical outputs can imply their raw-word equality on the covered domain. It is a separate theorem with strictness, output-format and coverage assumptions. To infer a protected program trace still requires the A3 initial-state/input/interface/covered-effect/synchronous-schedule premises; a local numerical tube does not certify unmodeled effects.

## 7. Read-only receipts and evidence scope

A B3 receipt binds endpoint identities, all physical shared call sites, graph and activations, numerical policy, legal input/state domains and provenance, initial relation, joint tube/invariant method, horizon, selected observation, budget, version and trusted schedule. Complete snapshot context, if supplied, binds the current context. The delivered analytic methods are `tube` and `invariant`; complete finite trajectory enumeration is separate experimental evidence, not an additional implemented receipt method. Labels and sample statistics cannot substitute for their different quantifiers.

The receipt publishes no weights, state or optimizer state. It cannot be submitted as a weakened replacement for a B1 BIT/ALG_AND_BIT transaction. Existing full-snapshot binding, rejection and rollback obligations remain unchanged. Hashes identify data under the trusted runtime; they do not establish domain truth or authenticate historical intent. General concurrency, arbitrary private-memory mutation, process/hardware faults and arbitrary compiler changes remain excluded.

General results are handwritten conditional proofs. Complete finite enumeration, seeded trials, exact rational references, software BF16 and audited local CPU FP32 results have separate recorded scopes. No full proof-assistant or arbitrary-backend certification is inferred from them. This stage does not establish general learning benefit, B4 continual-training capacity or the later composition series.

## 8. Concrete reference scope

The registered feedforward graphs have two affine/ReLU-or-identity calls, including a graph that invokes the same physical bank twice. They admit all identical canonical raw two-coordinate inputs with coordinate magnitudes at most one and observe all final output coordinates. The scalar recurrent graphs prepare `(state,input)` and admit all initial old/new raw state pairs of magnitude at most one whose distance is at most the declared E_0, together with every common raw input history having magnitude at most one. Their observation is the full state at every time from0 through the declared horizon; its bound is max_k E_k, not only the final E_T.

The reference accepts recurrent horizons0 through64. The mathematical finite-horizon theorem has no fixed universal upper limit, but the implementation limit is not silently removed. A `tube` cap is checked against the complete computed enclosures and is never used to truncate them. An `invariant` state box must include the initial domains and both endpoints' complete rounded images. Only a proved common invariant plus uniform contraction constants yields the optional all-time bound.

At each layer the implementation uses a joint input box containing both endpoint-specific boxes for drift and both rounding estimates, then propagates old/new output boxes separately. Its first-layer gain may use only declared differing input coordinates; all other coordinates must be equal under the trusted relation. Subsequent gains use every coordinate. Every physical call contributes its own range and error obligations even when its bank is shared.
