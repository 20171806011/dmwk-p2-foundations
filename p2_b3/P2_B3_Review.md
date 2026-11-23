# P2-B3 independent review

## Scope and initial disposition

This review concerns the new B3 propagation proofs, reference implementation and read-only numerical receipts. Previous evidence, source files and publication repositories are read-only. No previous verifier or optimizer trajectory is rerun. General conditional proofs, complete finite examples, seeded examples and observed floating operations are separate evidence classes.

The mathematical checkpoint was read before B3 implementation. Its recurrence has the correct structure: an exact-map Lipschitz contribution, a same-input stored-endpoint difference, and the separate errors of both rounded executions. The initial-state difference appears explicitly in the product-sum solution. No pre-code mathematical blocker was identified. Full T1–T8, the core and receipt implementations, and the executed independent checks below have now been reviewed. No remaining blocking issue was found within the stated conditional scope.

## Obligations checked before implementation

1. For the split through the new exact map evaluated at the old input, that exact cross evaluation must be defined. The new exact map's Lipschitz estimate must cover old/new input pairs; containment in a common certified domain suffices. The same-input endpoint drift bound can be restricted to the old domain for this split. Separate arithmetic error bounds use each execution's own actual domain.
2. A rounded staircase need not have the exact map's Lipschitz constant. It is analyzed as the exact map plus bounded execution residuals. Coordinatewise ReLU remains 1-Lipschitz even when its active set changes; a discontinuous hard branch requires a different margin argument.
3. A finite paired tube establishes containment through its declared horizon only. A time-uniform conclusion needs an unchanged input policy and a genuine common invariant with uniform forcing, totality and contraction assumptions. A finite list of passing trajectories does not provide that premise.
4. Shared physical banks require coherent endpoint replacement and all labelled uses. The initial relation, same external history, schedule and full-state versus selected observation must be fixed explicitly. A bound on one observed port cannot silently protect hidden state or earlier effects.
5. Hard-branch stability uses a declared tie convention and a strict guard margin larger than the certified guard difference, including relevant arithmetic errors. A guard at zero is not protected by an arbitrarily small positive budget.
6. Numerical receipts remain read-only. Checksums bind content identity, not historical intent or trusted global provenance. Neither a positive error budget nor a small sampled error authorizes a BIT/ALG_AND_BIT transaction.

## Independent evidence

The actual absolute-path run of [verify_independent.py](verify_independent.py) passed and wrote [independent_results.json](independent_results.json). It began at `2026-11-14T09:46:55.868083+00:00` and took **39.415879754 seconds** in the recorded local environment. These costs are not a benchmark or scalability claim. The successful process loaded no predecessor verifier module, invoked no predecessor suite and regenerated no saved optimizer trajectory.

The independent arithmetic reference decodes sign/exponent/significand into exact rationals and implements nearest-even rounding by binary search over ordered finite positive words, with explicit overflow and canonical zero. It computes each multiply/add independently, then applies exact finite-word ReLU. It does not use the producer test modules or their assertions as its oracle.

The range review uses two calculations: an independent symbolic reconstruction of the stated mixed-error recurrence, and a distinct monotone nearest-even interval extension. It checks that the latter remains inside the delivered endpoint enclosure. Signed affine-range and magnitude enclosures are intersected only because both were separately justified; no requested external cap truncates a range. Gain, endpoint drift and rounding terms are reconstructed from decoded words, including the state-only gain and the complete state/input forcing columns for recurrence.

| Independent category | Actual finite scope |
|---|---|
| Nonhomogeneous recurrence | 5,655 named coefficient-sequence/initial-value cases, exhausting lengths 0–3 over four gains and three forcing values with three initial radii |
| Constant envelopes | 180 combinations of named gains, forcing values, initial radii and horizons |
| Registered nonlinear/shared networks | 24 endpoint pairs and 288 paired point evaluations: all nine ternary two-dimensional inputs plus named thirds/subnormal probes per pair |
| Custom rectangular networks | 24 seeded two-layer shape-changing graphs, with explicit old/new radii and initial difference |
| Recurrent analyses | 36 tube analyses at horizons 0, 1 and 3; 2 independently reconstructed common-invariant certificates |
| Recurrent finite trajectories | 1,944 initial-pair/history cases on the specified three-value state/input alphabets; 972 distinct single-endpoint word trajectories, each checked against the independent RNE stepper |
| Hard-guard certificates | 4 analytic strict-margin fixtures, 324 complete named finite input-pair cases, and 32 seeded margin fixtures |
| Read-only receipts | 12 registered tube/invariant receipts; 38 expected receipt/context/authority refusals; 2 complete B1 rollback fixtures with nonzero first/second moments |
| Frozen B1 evidence | 21 refused stored endpoint pairs and 84 labelled protected call checks, read and recalculated without optimizer replay |
| Other adversaries | 26 expected graph/schema/domain/range refusals; repeated shared-bank response witnesses |

The recurrent section also records four domain-proof refusals; the control section separately records six strict-margin/domain/zero-policy refusals. These are not pooled into a theorem count. The base seed is **20261114**; the independent guard substream is **20261115**. Complete enumeration refers only to these named finite alphabets, initial pairs and horizons. Universal analytic box coverage still depends on T4's range-induction proof and the declared registry, not extrapolation of the finite observations.

## Mathematical and implementation audit

| Claim | Review finding |
|---|---|
| T1: one-step recurrence | The split includes the new exact map at the old comparison point. Both execution residuals remain separate; no rounded-map Lipschitz assumption or statistical independence is inserted. |
| T2: depth/time propagation | The product-sum includes the nonzero initial term and empty-product case. Recurrent observation uses the maximum over the full prefix, including time zero. |
| T3: regimes | Constant-L formulas handle zero and one separately. An amplifying upper envelope is not a lower bound on actual drift; all-time contraction requires the common invariant and uniform hypotheses. |
| T4: joint domains | Both endpoints' ranges and totality are established. Finite tubes do not imply all-time invariance; failed sufficient intervals are distinguished from actual state escape. |
| T5: nonlinear/shared composition | Coordinatewise ReLU has the stated standard-norm Lipschitz property. The state-only first gain relies on equal external inputs, while every input column remains in drift/range calculations. Shared calls contribute repeatedly. |
| T6: hard guards | Strict `g>0`, zero false, is explicit. The guard-margin proof accounts for both arithmetic residuals and the old/new input relation. It does not imply arbitrary branch-side-effect safety. |
| T7: observation/separation | Observed-port versus full-state scope is explicit. Strict canonical output separation can imply words equal only with the corresponding complete coverage; relative bounds still require a positive reference lower bound. |
| T8: receipts | The checker recomputes a fixed trusted registered graph/domain and binds all endpoints, biases, calls, relation, horizon, policy and schedule. It gives no BIT, ALG or publication authority. |

The implemented layer return is a conservative sum of drift plus two infinity-norm rounding terms. Both endpoints use the common containing box for these terms; their output boxes are propagated separately. Generic custom graph helpers remain conditional on their supplied graph and relation. A caller cannot obtain application provenance merely by supplying fewer calls or a narrower radius; the registered analyzer and receipt fix the complete expected graph/domain.

For common invariants, the fixed-domain coefficient proof is reused with the current initial-error scalar in each saved step, and the all-time bound follows from a checked common image inclusion. That does not remove the finite reference horizon limit of 64 for concrete requests or permit endpoint changes during the analyzed execution.

## Independent boundary findings

- The two-use scalar-diagonal bank witness uses old gain one and new gain five-fourths. At the first basis input, the final exact and executed change is `9/16`, larger than the single-call `1/4`. Each call must be included even when the physical bank is shared.
- For the exact map `x/2`, inputs eta and twice eta produce rounded outputs zero and eta. The actual pairwise gain exceeds the exact gain one-half. For `x+1` at the two specified nearby dyadic inputs, adding the input difference and **both** absolute execution errors exactly gives the observed output jump; removing either execution error fails.
- A zero guard and an eta guard take different strict branches. Equality of claimed margin and guard-change radius is refused. The independent two-box examples also reject an omitted new-input domain and negative-zero encoded input.
- The new recurrent endpoint `(3/2,1/8)` at state/input one exits a radius-one cap while the old contractive endpoint remains inside it. This is an actual new-domain escape. By contrast, a stored identity map returns one exactly while the conservative generic radius-one invariant proof refuses. Neither event is concealed by clamping.
- A saturated `(Fmax,Fmax)` row at `(1/2,1/2)` returns finite Fmax, yet the sufficient analytic range proof refuses. Actual overflow at a different point is a separate refused case.
- The receipt tests reject rehashed omitted calls, sampled domain substitutions, altered initial relations, policies/schedules, observation ports, endpoints, horizon, proof bounds and authority flags. An E0=0 context with two different initial words is refused even though both words lie in the same magnitude-one box.

These are finite explicit witnesses and interface checks, not an exhaustive characterization of every safe program or every floating backend.

## B1 boundary and preserved failures

The independent B1 fixture is distinct from the main receipt fixture. AdamW with zero moment coefficients, epsilon seven and the specified first-coordinate unit gradient gives an exact host direction `-1/8`; final projection produces `(-1/16,+1/16)` in the first row. The committed endpoint is `(15/16,1/16)` in that row, both moment arrays have a nonzero entry, and a protected tick has occurred. Submitting a B3 numerical receipt through the unchanged B1 commit API is refused with the entire bank unchanged. A later snapshot identity also invalidates the earlier external context without mutating the later bank. This is a new B3 integration fixture, not replay of the saved training experiment.

All 21 frozen B1 rejected proposals still have nonzero exact action on the duplicated-bit protected generator and identical actual words at all four labelled calls. The saved dense FP32 AdamW joint route remains zero accepted commits, eight refusals and final loss `5/2`. Positive conservative bounds are not evidence that these protected outputs changed. The original JSON hash remains `b417741ab974752d7858c978bc75197f3199312e9bdf118c232dcbd8cef7cfb1`.

## Development issue, corrections and limits

A development-only import diagnostic exposed a module-name collision. Loading the new arithmetic dependency first prepended predecessor search paths, after which an unqualified import of `verify_independent` resolved B2's same-name module. The diagnostic immediately failed because that module lacked the new B3 function; no old verifier function or suite executed and no predecessor file changed. The process stopped. Subsequent development checks used explicit-file imports, and the final successful entry runs by absolute path with current-module provenance checks and a check that no old verifier module is loaded. This incident is recorded as a tooling issue rather than suppressed or described as a successful scientific run.

Pre-code review clarified the cross-pair domain obligation and the difference between finite tubes and uniform invariants. Final document review requested that generic graph validation be described as structural validation, with complete registered-call provenance supplied by the analyzer/receipt. No predecessor correction or numerical implementation repair was required by the independent checks.

The proofs are conditional handwritten arguments. There were no SMT queries or Lean/Coq proof checks. BF16 execution is software; FP32 evidence concerns the available audited scalar CPU path. GPU, native BF16, arbitrary FMA/reassociation/compiler changes, general concurrency, hardware faults, crash consistency, malicious private-memory mutation and whole-host formal correctness remain uncertified. The delivery does not implement general branched-program verification, evolving endpoint histories, B4, or a universal learning-performance guarantee.

## Reproduction and synthesis audit status

```sh
python -B /workspace/p2_b3/verify_independent.py --output /tmp/p2_b3_independent_results.json
```

The final definitions, proofs, control-flow specification, numerical analysis, counterexample catalogue, receipt specification and B4 handoff were read for consistency. The Report/README/Evidence Map distinguish proof, finite experiment and unverified environments. The generic-validator wording has been corrected: only the registered analyzer/receipt supplies the declared complete-graph binding. No later-stage result is inherited from a completion label.

The completed [driver_checks.json](driver_checks.json) records a successful main run of **27.699216039 seconds**, its foreign-directory repeat of **26.186360291 seconds**, the independent run of **39.415879754 seconds**, and its foreign-directory repeat of **38.071814596 seconds**. The two main/independent reproduction comparisons and the three standalone-to-aggregate section comparisons all match after excluding only the enumerated timestamps/seconds. Scientific values, rejection reasons, source/evidence identities and environment metadata remain in the comparisons. Both `-O` and `-OO` probes refused in preflight with zero attempted scientific sections, preserving the primary results. The driver also records all **699** predecessor content hashes and the nonexcluded inventory unchanged.

The reproduction results support repeatability in this available environment; they do not add universal theorem coverage or certify another backend. This final synthesis audit did not edit Python, change scientific output or rerun a scientific suite. The subsequent completion/manifest records concern artifact integrity and remain separate from the proof and execution claims. No blocking issue remains for the stated B3 scope.

