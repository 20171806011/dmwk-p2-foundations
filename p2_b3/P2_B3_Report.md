# DMWK P2-B3: nonlinear and finite-time perturbation propagation

## Scope and mathematical result

B3 analyzes a fixed old/new pair of stored endpoint banks, a specified nonlinear network or synchronous state graph, common legal external inputs and a trusted schedule. It extends B2's single-layer analysis by proving intermediate-domain containment and propagation together. It does not analyze continual parameter changes, B4 capacity evolution or a live relaxed update policy.

Let the actual finite executions obey

\[
\widehat s_{t+1}=F_t(\widehat s_t,u_t)+r_t,\qquad
\widehat s'_{t+1}=F'_t(\widehat s'_t,u_t)+r'_t.
\]

Here F and F' are exact maps obtained from decoded stored endpoints, while r and r' are their separate execution residuals. If the exact new map has a certified cross-state Lipschitz bound L_t on the required joint domain, its same-input endpoint drift is at most a_t, and both execution errors are bounded, then

\[
E_{t+1}\le L_t E_t+\beta_t,\qquad
\beta_t=a_t+\rho_t+\rho'_t.
\]

The corresponding nonhomogeneous product-sum includes the initial difference:

\[
E_T\le E_0\prod_{t=0}^{T-1}L_t+
\sum_{j=0}^{T-1}\beta_j\prod_{t=j+1}^{T-1}L_t.
\]

The same recurrence applies across layers, with the correct intermediate dimensions and norms. Every shared-bank call remains in the composition; sharing parameters does not remove repeated arithmetic or repeated endpoint effects. For identical initial state and constant uniform L,beta this gives the requested beta times the finite geometric sum. The proofs cover arbitrary finite horizons under their stated premises; the executable registry limits requests to horizons 0 through 64.

For L<1, an all-time joint invariant, totality, fixed endpoints and uniform forcing are needed to obtain the bound max(E0,beta/(1-L)). At L=1 the envelope is E0+T beta. For L>1 the generic upper envelope can amplify; this is not a theorem that every actual error grows. Exact scalar examples attain the geometric recurrence, while cancellation, identical executions or conservative constants can make its numerical upper bound loose.

The [Definitions](P2_B3_Definitions.md) and [Theorems](P2_B3_Theorems.md) contain the complete conditional proofs. Their truth is not inferred from a finite trajectory count and is not claimed to have been machine checked.

## The missing link supplied by domain closure

Both old and new intermediate inputs must stay in domains on which the claimed constants and rounding bounds are valid. A low-rank sample, original-only activation collection or observed trajectory maximum cannot discharge this obligation. The old global legal activation span and a chosen reference space remain distinct. If a local geometric argument uses a reference space, new-state leakage needs its own proved envelope; approximate-basis conditioning and alignment still require separate certificates.

The concrete method uses rational symmetric boxes. Every affine product and sum is range-checked under the fixed numerical policy; its output radius and error are enclosed. ReLU cannot increase that radius and is 1-Lipschitz in the infinity norm. Propagating those separate endpoint boxes gives a finite tube. Checking both endpoint images against one fixed state box gives a common-invariant proof. A claimed cap is checked, never used to truncate an escaping bound. Failure can mean conservative lack of certification or genuine domain exit; the counterexamples distinguish them.

Same initial state is a paired relation, not a conclusion from overlapping initial boxes. The recurrent registry admits all initial pairs in magnitude-one boxes whose separation is at most the declared E0. With E0=0 the canonical initial words coincide. Both executions then use the same input history with input magnitudes at most one. A supplied actual initial context is checked against that relation. Recurrent observation covers the full state at every time from zero through the requested horizon; a final-only bound is not silently substituted.

## Numerical and nonlinear semantics

The reference uses exact rational arithmetic for certificates and the infinity norm's exact maximum absolute row sum. It does not accept an uncertified SVD result as a bound. Every endpoint matrix and bias is decoded from finite canonical BF16/FP32 words. The graph fixes bias-first ascending-column separate multiplication/addition, nearest-even rounding, gradual underflow and canonical zeros. Identity and coordinatewise ReLU have explicit implementations; no arbitrary activation kernel is inherited as exact.

The effective update is Delta=W'-W. It already includes generation, projection, optimizer and storage effects. Adding those effects a second time to a direct endpoint bound would misstate the accounting. The alternative B2 telescoping ledger remains available only with named, disjoint stages and their provenance.

Exact-map Lipschitz constants are not constants of the rounded staircase without another proof. At eta and 2 eta, rounding x/2 gives zero and eta: the finite-pair gain is one although the exact gain is one-half. Both old and new residuals repair this discrepancy. A separate stored x+1 witness makes both residuals necessary individually. Near zero and cancellation, relative bounds require a certified positive reference-output lower bound; absolute and explicitly mixed statements remain meaningful when such a bound is absent.

ReLU activation-pattern changes do not invalidate its continuous nonexpansiveness theorem. A hard guard is different: the concrete branch is g>0, with zero false. Its strict margin must exceed the whole executed-guard perturbation, including input change, endpoint drift and both execution errors. Smooth branch bodies do not make their switched map smooth. Coordinatewise ReLU also does not commute with arbitrary orthogonal rotations. These are distinct boundaries, documented in [Control Flow](P2_B3_Control_Flow.md).

## Authorization and deterministic protection

B3 numerical receipts are detached, read-only evidence. They bind actual physical endpoint banks and biases, every ordered shared call, graph/activation, format/policy, domain, initial relation, joint proof method, horizon, complete observation, budget, version and schedule. Optional B3 state context is checked against the declared initial relation. An attached B1 snapshot is separately labelled unrelated identity metadata; it is not evidence that the B3 network is the B1 protected program.

Neither a positive bound nor a small observed error authorizes a BIT/ALG_AND_BIT update. Strict sub-eta full-domain output bounds can imply finite canonical word equality, but this has separate separation and coverage premises. Program lifting still needs every A3 initial/input/invariant/interface/covered-effect/same-snapshot scheduling premise. Critical deterministic state retains exact protection; a continuous numerical budget cannot quietly weaken it.

B1's 21 saved refusals remain BIT-preserving but ALG-failing. Its dense FP32 AdamW experiment remains zero accepted updates in eight attempts with final loss 5/2. The new stage reads this evidence, without regenerating the old optimizer trajectory. New transaction-boundary fixtures test that a B3 receipt cannot bypass the existing B1 API and that refusal preserves the complete weight, optimizer and protected-state snapshot.

## Executed evidence

The propagation producer passed 2,103 checks with six expected refusals in 10.305082273 seconds. It includes 64 seeded nonhomogeneous recurrences, 32 constant scalar cases, 324 complete small-alphabet histories through T=3 and 96 seeded histories through T=6. The complete histories comprise 12 families, each exhausting all 27 length-three words over the named three-value alphabet; this is not enumeration of the entire BF16/FP32 input alphabet or every initial state. There are also 36 complete small-domain multilayer/shared-call point probes and 16 executed retained-boundary points, with the target-incompatibility algebra record separate.

For the same-initial-state families, the new scalar bias is 1/64. The measured final differences attain the exact scalar geometric recurrence in these short dyadic fixtures. The implemented global tube bounds are larger because they cover the broader declared raw-word boxes and use conservative arithmetic errors:

| Exact state gain | Observed maximum at T=3, both formats | BF16 certified bound (approximate display) | FP32 certified bound (approximate display) |
|---|---:|---:|---:|
| 1/2 | 7/256 | 0.04325458344 | 0.02734398982 |
| 1 | 3/64 | 0.13457725247 | 0.04687631875 |
| 2 | 7/64 | 0.72880320850 | 0.10938430764 |

Exact rational bounds, slack and ratios are in the result record; the decimal displays are not acceptance inputs. These examples distinguish recurrence sharpness from the conservative implementation. In the separate L=2 identical-endpoint controls, actual difference is zero while the generic computed bound is positive. The gain of an upper envelope is not a lower-growth claim.

Both formats also certify a common scalar invariant box of radius one for the contraction fixture. With initial difference at most 1/8, its uniform-in-time bound is 1/8. This conclusion comes from the invariant/range proof and the constant-coefficient theorem, not from the finite test horizon. In contrast, the identity-map box check conservatively refuses even though the displayed state remains one; the amplifying map at state one actually produces two and leaves the claimed radius-one box. The two refusal meanings remain distinct.

The two-layer ReLU fixture has observed finite-domain maximum 7/32, with approximate bounds 0.49880397125 (BF16) and 0.43750092760 (FP32). The repeated shared-bank fixture has observed maximum 1/8, with approximate bounds 0.23265724501 and 0.20312544703. Each exhausts its named nine-point input grid. Their universal analytic bounds apply to the larger specified raw input box by the separate proof; the grids are corroborating finite instances.

The control producer passed 1,578 checks with 28 expected refusals in 4.078897967 seconds. Each format executes 287 guard input pairs: 162 from complete small grids, 120 seeded pairs and five named boundary pairs, plus separate rotation traces. The receipt producer passed 498 checks with 128 expected refusals in 9.478728363 seconds, including 44 registered receipt cases, 46 rehashed semantic-tampering cases, eight seeded endpoint receipts and two B1 full-rollback fixtures with nonzero moments. The root seed is 20261114. These are actual local costs, not performance claims.

The independent checker passed in 39.415879754 seconds using its own word decoding/RNE oracle, exact product-sum computation and reconstructed range/forcing formulas. It checked 5,655 exhaustive named coefficient/initial-value combinations and 180 constant envelopes; 24 registered network endpoint pairs at 288 input pairs plus 24 seeded rectangular networks; and 36 recurrent analyses covering 1,944 named initial-pair/history combinations and 972 distinct word trajectories. It checked two common invariants, four guard certificates at 324 complete small pairs, 32 seeded guard certificates, 12 receipts, 38 receipt refusals, two nonzero-moment B1 rollback fixtures and 26 schema/range adversaries. Its new exact-reference evaluation of the frozen 21 B1 endpoint pairs preserves their classifications over 84 labelled calls without regenerating the optimizer. The control substream seed is 20261115; other declared seed streams are recorded explicitly.

The aggregate runner passed all three sections in 27.699216039 seconds. Its foreign-directory repeat from `/tmp` passed in 26.186360291 seconds. The independent repeat passed from `/tmp` in 38.071814596 seconds. [driver_checks.json](driver_checks.json) records five successful comparisons: aggregate versus repeat, independent versus repeat and each of the three standalone producers versus its aggregate section. Only enumerated timestamp/seconds fields were omitted; all scientific results, refusal reasons, environment fields, source identities and independent producer-evidence bindings matched. Python `-O` and `-OO` were each refused at preflight with zero sections attempted and without replacing the passing evidence.

Hash and nonexcluded-inventory checks retained all 699 predecessor artifacts unchanged. No old suite, old optimizer trajectory or publishing operation was repeated. The independent Review records one development import collision, which stopped before invoking any old verifier function, and a corrected wording distinction between generic graph consistency and registered complete-call coverage. No scientific implementation defect or predecessor correction remained after review. See [Evidence Map](P2_B3_Evidence_Map.md) for claim attribution and [Review](P2_B3_Review.md) for the independent disposition.

General proofs, complete named finite alphabets/horizons, seeded trials, local CPU operations and software BF16 retain distinct labels throughout. There were zero SMT queries and no Lean/Coq checking. Source hashes and packaging checks establish evidence identity, not mathematical truth or live authorization.

## Limitations and handoff

Box methods lose sign/correlation information and can reject safe systems. Uniform contraction conclusions depend on uniform invariant/domain/rounding conditions, not merely L<1 on samples. No arbitrary branch analyzer, complete reachability solver or universally tight finite-format perturbation estimator is delivered. Numeric hashes bind evidence identity under a trusted runtime; they do not authenticate historical intent or stop hostile private-memory mutation.

GPU, native BF16, general concurrent publication, arbitrary compiler/FMA/reassociation changes, hardware faults and whole-host formal correctness remain uncertified. Toy bounds and finite trajectories establish no universal learning benefit. The separate [B4 handoff](P2_B4_Handoff.md) records the next obligations; B4 is not executed here.
