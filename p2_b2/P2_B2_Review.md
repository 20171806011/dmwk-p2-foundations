# P2-B2 — Independent mathematical and executable review

## Disposition and scope

No blocking mathematical or implementation inconsistency remains in the reviewed B2 contracts and finite reference checks. The results establish conditional single-layer bounds and read-only evidence. They do not establish a modified feedback program's future reachable domain, automatically authorize a B1 update, or certify arbitrary backends.

The review began with the saved plan and mathematical checkpoint before implementation, then examined the interface, exact-bound implementation, bounded-receipt implementation and final definitions/theorems. Earlier artifacts were read-only dependencies. No old verification suite was imported or run, and no frozen optimizer trajectory was regenerated.

[independent_results.json](independent_results.json) records the successful independent run beginning at `2026-11-14T08:34:43.954971+00:00`, with elapsed time `16.060792099000537` seconds. Four implementation/verifier source hashes are bound and checked for changes during the run. The frozen B1 training file is separately bound by its SHA-256. Timings are observations of this environment, not speed or scaling claims.

## Mathematical review

| Claim family | Independent review and qualification |
| --- | --- |
| T1: protected action and leakage | The orthogonal decomposition gives the two-term bound directly. The coefficient norm is `||Pi_V h||`, not an unexplained substitute based on a sampled space. If V contains all legal inputs, leakage is exactly zero there. The global alternative `M ||h||` is independently valid; either bound or their minimum may be used with its stated meaning. |
| T1(a): sharp joint class bound | The adjoint maps a unit output vector to an input vector with total norm at most M and protected-component norm at most `min(epsilon,M)`. The resulting two-variable disk problem gives the displayed formula. A rank-one outer product attains it. The nonzero subspace/output assumptions and zero-component cases are correctly handled. This is a real matrix-class optimum, not guaranteed finite-endpoint attainability. |
| T2: approximate bases | Gram control supplies injectivity and a pseudoinverse norm bound. The separate projector-gap term controls alignment with the declared reference space. The proof `Delta v=Delta U U^+v+Delta(Pi_V-Pi_U)v` establishes the coefficient. Gram error alone cannot establish true-space alignment or legal-input provenance. Failing the sufficient Gram-bound test does not prove rank deficiency. |
| T2(a): rational norm certificates | Frobenius and one/infinity norm products are valid spectral majorants. Outward rational roots certify their use. Exact positivity of `B^2 I-A^T A` is an independent certificate for a particular claimed upper bound; checking all principal minors is valid but can be expensive. No unverified SVD is used. |
| T3: disjoint ledger | Consecutive exact differences telescope once to the effective endpoint increment. Representation, optimizer, generation and storage terms are distinct only when their stage definitions are distinct. The factor alternative must retain cross terms. The identity does not validate an asserted ideal optimizer's history, and the same errors must not be presented again as new terms on top of a direct endpoint bound. |
| T4: two executions | Local signed product/addition residuals telescope exactly for the specified bias-first graph. Absolute residual sums bound row errors. Subtracting old and new executions needs both error contributions. The additive underflow term is necessary for the general local model. Actual finite traces and sufficient analytic range checks are separate forms of evidence. |
| T5: complete boxes and optional gamma bound | The range recurrence checks every product and sum argument before deriving finite rounded magnitudes, then propagates the resulting bound. It applies separately to both endpoints. It is an inductive proof over the entire stated box, not an extrapolation from corners. A refused conservative range proof need not identify an actually overflowing displayed input. The gamma specialization correctly requires the relative local model throughout its claimed domain and is not used by the delivered bound APIs. |
| T6: relative/mixed bounds and finite separation | A positive certified reference lower bound is necessary for division; zero-output cases remain absolute or mixed. Canonical finite decoded values lie on the eta lattice. A strict full-domain infinity bound below eta forces full output-word equality; equality at eta does not. This output statement does not cover missing effects, sites or modified-program reachability. |
| T7: numerical receipts | Complete point maxima and proved containing boxes support the selected L2 or infinity budget on the original registered single-layer domain. Recomputed endpoints, observations, domain, policy and method bind that diagnostic. The result has no live publication transition and no B1 BIT/ALG_AND_BIT authority. |

The final definitions explicitly distinguish `V_ref` from the complete original legal span `V_global`. A nonzero residual relative to `V_ref` is not called leakage from a space that already contains every legal activation. They also distinguish coverage of original registered call inputs from closure of an altered stateful program.

## Independent verification method

[verify_independent.py](verify_independent.py) imports the bound and receipt APIs but no producer verifier or old-stage test module. Its references use different reasoning from the producer assertions:

- Exact square-root intervals are checked by squaring their rational endpoints and checking the normalized relative width.
- Spectral certificates are checked using every principal minor of `B^2 I-A^T A` for the small tested matrices. Independent determinant/adjugate calculations construct reference projectors and validate protected/residual components.
- Floating words are decoded independently. RNE results are selected by a binary search over ordered positive finite words, exact rational distances and nearest-even ties, with explicit overflow and canonical-zero handling.
- The independent affine evaluator reconstructs every product/addition argument, rounded word and signed local residual. It verifies the old and new traces separately, then checks their coordinate, L2 and relative bounds against the exact decoded output difference.
- The analytic box recurrence is reconstructed directly from coefficient magnitudes, envelope bounds and exact format constants. Both endpoint recurrences and every reported intermediate range/error contribution are compared. Complete small raw-input sets then test that certificate on declared members; the universal conclusion still comes from the separate induction proof.
- Receipt checks use explicitly listed complete call sets for the five fixed registries. Candidate endpoints, selected norms, domain maxima and box inclusion are checked against independently evaluated point traces or range bounds. Inconsistent records are rehashed before submission to distinguish semantic recomputation from a mere checksum test.

The geometry base seed is `20261114`. Point/box property fixtures use the explicitly recorded deterministic substream seed `20261115`. No random seed or sampled family is presented as global coverage.

## Actual independent evidence

| Evidence | Actual finite scope |
| --- | ---: |
| Outward square-root enclosures, including very small and large rational scales | 32 |
| Spectral bounds checked by exact principal-minor PSD certificates | 72 |
| Two-dimensional geometry instances across projector/orthonormal routes | 450 |
| Seeded three-dimensional geometry instances | 48 |
| Zero/full-space cases | 8 |
| Scaled/rotated approximate-basis cases | 3 |
| Wrong-span or uncertified-basis refusals | 3 |
| Complete small old/new/input point combinations, both formats | 1,458 |
| Seeded two-output affine point pairs, including changed biases | 128 |
| Analytic two-endpoint box certificates | 24 |
| Members exhausted in the named small box-input sets | 384 |
| Nonnegative mixed-budget combinations | 81 |
| Telescoping modes with all four errors nonzero | 3 |
| Registry/method/norm/format receipt combinations | 40 |
| Distinct declared call cases checked for those endpoint pairs | 26 |
| Expected receipt/context/authorization refusals | 38 |
| New B1 integration fixtures with both first and second moments nonzero | 2 |
| Frozen B1 refused endpoint pairs newly analyzed | 21, covering 84 labelled call cases |

There are also six explicitly recorded numeric-policy/range refusals, duplicate-ledger-label refusal and format-specific boundary witnesses. These categories are not pooled into a universal proof count or a confidence score. The script records their separate scopes.

The direct joint-envelope witness `Delta=(3,4)`, `h=(1,1)` has response 7, two-term bound 8 and uniform-bound square 50. It corroborates the stated coupling caveat without claiming every norm term can simultaneously be attained.

The approximate-basis checks separately validate the Gram condition, inverse-conditioning inequality and exact projector-gap certificate for a scaled correct-space basis, an orthogonal wrong-space basis and a rationally rotated basis. The reference projector is derived independently by adjugate algebra; the tests do not infer that a supplied reference matrix covers an unknown program.

## Rounding and refusal findings

The independent boundary tests cover more than a zero residual at a convenient input:

1. With old scalar weight zero, new weight eta and input one, the actual gap and point infinity bound are exactly eta, while the words differ. This explicitly rules out replacing the strict separation condition by `<=eta`.
2. Identical zero endpoints produce a bound zero strictly below eta and identical canonical words. A negative-zero stored input is refused, rather than silently treating numerical equality as bit equality under two zero encodings.
3. Multiplying eta by one-half rounds to zero; its error eta/2 violates the relative-only local model. The mixed local bound covers it.
4. Let `s=RN(1/3)`, compare old scalar weight s with new weight 2s, and use input eta. The actual output gap is eta. The exact algebraic change plus only the old error is too small, and the exact change plus only the new error is also too small. Adding both recorded errors gives exactly eta. This demonstrates why neither endpoint's rounding contribution can be omitted.
5. Cancellation can make the reference output zero while a finite endpoint change yields output one; the relative field is `None`. A zero-column, bias-only graph has zero arithmetic residual and the correct explicit bias difference.
6. The displayed half-maximum saturated input executes finitely, while the conservative box route refuses its generic range proof. This is reported as inability to certify that envelope by the chosen recurrence, not observed overflow at the displayed input. Actual overflowing execution is a separate refused case.

The receipt tests preserve all shared sites and full output ports. They refuse omitted sites/activations, sampled coverage substitutions, changed FMA/policy/schedule fields, false BIT/live-authority/invariant claims, altered endpoints, lowered proof bounds, insufficient budgets, wrong external versions, unknown sample registries and shrunk boxes.

For the B1 integration boundary, each format uses a new exact first-step fixture with zero Adam coefficients and epsilon three. The accepted projected increment is `(-1/8,+1/8)` in the first row, and both moment arrays contain a nonzero entry. A numerical receipt for a subsequent bounded candidate is rejected by the unchanged B1 commit API with the entire current snapshot preserved. A later tick's state is also retained when stale context evidence is rejected. These are new interface tests, not reruns of the saved optimizer experiment.

## Frozen B1 evidence remains unchanged

The reviewer reads each saved refused endpoint pair and calculates fresh B2 traces and bounds; it does not regenerate the gradient, moments or optimizer trajectory. All 21 pairs still have zero actual protected difference over every registered call, while an exact ALG residual remains nonzero. Each positive point bound is smaller than its broader analytic box bound. A positive upper bound is not evidence of nonzero drift, and the strict lattice criterion is sufficient rather than necessary for the already observed bitwise equality.

The frozen FP32 dense AdamW joint-policy result remains zero accepted updates, eight refusals and final loss `5/2`. B2 does not relabel those attempts as accepted learning or override their selected ALG_AND_BIT claim. The original training file's bytes and digest are checked unchanged during the independent analysis.

## Corrections and remaining boundaries

Pre-code review requested the distinction between the reference space and actual legal span, the sharper protected-component norm in the implemented split, and explicit separation of original-domain coverage from candidate feedback closure. Those distinctions are present in the final implementation and mathematical contracts.

A concrete new B2 adapter issue was found before the successful independent run: the optional complete B1 snapshot-context schema initially omitted B1's `schedule` field. The schema was corrected in B2. The independent suite now accepts the complete snapshot and rejects one with the schedule removed. No predecessor evidence was changed. The theorem's receipt statement was also aligned with the two supported named norms. The final report's Gram-defect notation was requested in the unambiguous form `||U^T U-I|| <= delta < 1`, matching the implemented condition on the certified upper bound.

The tests are finite exact/rational and software-reference checks. Production BF16 is a software RNE model; production FP32 evidence concerns the available audited local scalar path. No GPU, native BF16, arbitrary FMA/reassociation/compiler transformation, general concurrency, hardware faults, unsupported modified-program invariant or whole-host formal correctness is certified. There were zero SMT queries and no Lean/Coq proof checking. The universal results remain handwritten proofs with explicit premises.

B2 introduces no live bounded-error update policy and no automatic program-level noninterference or time-uniform error theorem. B3 and later stages remain unexecuted.

## Reproduction

```sh
python -B /workspace/p2_b2/verify_independent.py
```

To preserve the saved result while reproducing:

```sh
python -B /workspace/p2_b2/verify_independent.py --output /tmp/p2_b2_independent_results.json
```

The default output is `independent_results.json`. These commands execute only the new B2 verifier and its declared read-only dependency interfaces. Hash bindings support evidence identity; they are not cryptographic authorization or original-intent authentication.

## Final synthesis and reproduction audit

The final README, Report, Evidence Map, Certificate Spec and B3 handoff were read against the recorded proof and experiment scopes. No blocking inconsistency remains. The Report now states the Gram condition as `||U^T U-I|| <= delta < 1` and includes the executed witness requiring both endpoint rounding terms. The documents preserve the read-only nature of numerical receipts, the original-domain versus modified-feedback distinction, the 21 BIT-preserving/ALG-failing B1 refusals, and all unverified backend and program-level limits. The handoff records obligations without implementing B3.

The completed `driver_checks.json` records successful main and foreign-directory main runs of 11.860618054 and 12.189905724 seconds, and independent runs of 16.060792099 and 16.707115789 seconds. Their scientific results, source bindings, environment data and refusal reasons agree after excluding only the enumerated timestamp/seconds paths. The two standalone component records likewise agree with their aggregate sections. Both `-O` and `-OO` probes refused in preflight with zero attempted sections and preserved the primary evidence. The driver reports all 447 predecessor content hashes and the nonexcluded inventory unchanged. These are reproducibility and preservation checks, not additional scientific coverage or universal machine proofs. This synthesis audit introduced no new scientific run and changed no source code or saved experimental output; the final packaging manifest is a separate subsequent integrity record.
