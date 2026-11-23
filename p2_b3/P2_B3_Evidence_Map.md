# P2-B3 claim-to-evidence map

This map separates handwritten general proofs, universally quantified analytic witnesses under explicit premises, complete finite families, seeded evidence, backend probes and independent review. A passed finite assertion is not a machine proof of a universal theorem. Every numerical update is the actual decoded endpoint difference; upstream generation/storage errors are not added to it a second time.

## General claims and implemented witnesses

| Claim | Mathematical evidence | Implementation / actual finite evidence | Scope and remaining premise |
|---|---|---|---|
| One-step difference includes state amplification, same-input endpoint drift and both execution errors | [Theorems T1](P2_B3_Theorems.md#t1--one-step-relational-recurrence) | `network_bound` in [propagation_bounds.py](propagation_bounds.py); propagation and control records | Exact maps use certified cross-pair domains. Neither rounded map inherits the exact map's Lipschitz constant automatically. |
| Nonhomogeneous depth/time product-sum includes initial difference | T2 | `propagate_recurrence`; `propagation_results.json/sections/recurrences`: 64 seeded nonhomogeneous cases and 32 constant cases, 160 assertions | Finite checks validate these cases. The arbitrary-finite statement is the handwritten induction. |
| Contraction/neutral/amplifying envelopes have different upper bounds | T3 | `constant_recurrence`; three scalar model families, both formats, initial differences 0 and 1/8 | An L>1 envelope is not a lower-growth theorem. All-time contraction requires a common invariant and uniform forcing/rounding. |
| Old and new trajectories stay inside jointly certified domains | T4 | Per-endpoint output boxes and joint local error boxes; `analyze_model` tube/invariant methods | Every initial pair and legal input must satisfy the declared domain. An original-only sample or a clamped output box does not establish this. |
| ReLU layers and repeated shared calls obey the recurrence | T5 | `two_layer_relu_v1`, `shared_relu_v1`; 36 complete two-dimensional points across 4 format/model cases | Full endpoint shapes, all call labels and sharing are fixed. Every shared call contributes separately. |
| Hard branch preservation needs a strict executed-guard margin | T6; [Control Flow](P2_B3_Control_Flow.md) | [control_flow.py](control_flow.py), [control_results.json](control_results.json) | Convention is `g>0`, zero false. Margin includes state/endpoint drift and arithmetic residuals. Arbitrary cross-branch programs remain unimplemented. |
| Full-prefix state observation differs from final-only observation | T2/T7 | Recurrent `observed_bound=max(error_bounds)` includes time 0 | E0=0 is a paired same-state relation, not a conclusion from overlapping initial boxes. |
| Strict sub-eta output bounds can imply canonical word equality | T7, inherited B2 separation proof | Named zero/eta and guard-boundary probes; no automatic B3 BIT route | Requires strict inequality, finite canonical outputs, complete coverage and separate program-lifting hypotheses. |
| A numerical receipt is read-only, bound to complete semantics and not B1 authority | T8 | [propagation_certificate.py](propagation_certificate.py), [certificate_results.json](certificate_results.json) | Trusted serialized recomputation; neither an unkeyed digest nor an unrelated external snapshot proves domain truth or historical intent. |

The generic proofs permit a specified norm with the required map constants. Concrete receipts and propagation use the infinity norm. ReLU's stated nonexpansiveness is for standard l_p norms; an arbitrary norm requires its own activation constant. Relative/mixed observation statements have separately quantified reference-output lower bounds and are not inferred from nonzero sample observations.

## Producer evidence actually saved

All three saved producer records report status `passed`, seed 20261114 and zero unexpected failures. Expected refusals are intentional negative checks, not suppressed failures. Counts below are assertion/dataset counts with different units; they should not be interpreted as independent universal guarantees.

| Output | Assertions | Expected refusals | Actual saved cost |
|---|---:|---:|---:|
| [propagation_results.json](propagation_results.json) | 2,103 | 6 | 10.305082273 s |
| [control_results.json](control_results.json) | 1,578 | 28 | 4.078897967 s |
| [certificate_results.json](certificate_results.json) | 498 | 128 | 9.478728363 s |

The propagation sections are independently labelled in their JSON:

| Section | Recorded finite scope | What it does not enumerate |
|---|---|---|
| `recurrences` |64 seeded nonhomogeneous cases plus 32 constant scalar cases | Every possible coefficient sequence or real initial difference |
| `recurrent_execution` | 12 complete families × 27 histories of length 3 over `{-1,0,1}` = 324 histories;12 seeded families × 8 histories of length 6 = 96 histories; 420 total recorded histories | All canonical raw input values, all initial pairs in the analytic box, or unbounded time |
| `multilayer` | 4 cases × 9 complete small two-dimensional inputs = 36 points | Every raw point in the registered magnitude-one box |
| `retained_boundaries` |16 actual two-call floating probes across BF16/FP32 plus 1 exact target-relation record; 2 expected refusals | A new audit or rerun of all predecessor stages |

The recurrent complete families vary format, three scalar regimes and initial relation. The complete alphabet is exactly `{-1,0,1}`; initial examples and endpoints are recorded, not generalized from their observed maxima. The universal containing-box result instead uses T4's exact range induction and the complete registry-domain premise.

Control output records two complete margin families per format, with 162 pair executions per format (324 total). Its 24 seeded guard cases per format use five pairs per case, giving 120 seeded pair executions per format and 48 cases / 240 pair executions overall. It records exact ReLU rotation and rounded-half-map counterexamples, strict/equality margin boundaries, underflow/overflow/nonfinite policy cases, and a two-error witness where dropping either endpoint residual invalidates the claimed bound. These probes are not a full branch analyzer or a complete program-reachability proof.

Receipt output records 44 registered cases, 46 rehashed inconsistent-record cases, 8 seeded endpoint receipts, and 2 new B1 boundary fixtures. The latter begin with nonzero optimizer moments and a nonzero tick count, attempt to submit a B3 numerical receipt through the unchanged B1 interface, and preserve complete endpoint/state/version/tick/optimizer snapshots on refusal. This is a new interface test, not a rerun of a prior optimizer trajectory.

## Counterexamples and failure boundaries

The [Counterexamples](P2_B3_Counterexamples.md) catalog gives the concrete constructions and their recorded scope; [Numerical Analysis](P2_B3_Numerical_Analysis.md) specifies the implementation's range and rounding accounting.

| Boundary | Evidence location | Consequence |
|---|---|---|
| Exact contraction does not give the same Lipschitz constant for rounded execution | `control_results.json/formats/*/rounded_half_map` | At eta and 2 eta, rounded x/2 has pairwise gain 1 despite exact gain 1/2. |
| Omitting either execution residual can break a bound | `control_results.json/formats/*/both_rounding_errors` | The stored x+1 witnesses retain both old and new residuals; they are not statistical noise terms. |
| Small guard perturbation can change a branch | `branch_jumps` and margin refusals in control output | Strict margin is required; fixed-format examples do not imply arbitrarily small distinct raw values. |
| New trajectory can leave an original cap | Recurrent refusal and trajectory records | Refusal is supported by an actual domain-exit witness when supplied. |
| A safe identity can fail a conservative invariant enclosure | Recurrent refusal records | A failed interval certificate is not an impossibility theorem or necessarily an observed overflow. |
| Basis-zero test misses subnormal nonzero execution | `retained_boundaries`: `thirds_multilayer_basis`, `thirds_multilayer_subnormal` | Algebraic annihilation and same-basis floating checks do not replace full execution/domain analysis. |
| Commit quantization changes the effective update | `quantized_endpoint_downstream` | Use actual stored endpoints, not the ideal increment. |
| Full-rank protected spans can still admit finite-domain BIT changes | `full_rank_BIT_nonALG_shared_depth_two` | The exact algebraic rank restriction does not classify rounded observational equivalence. |
| BIT update rank can exceed algebraic complement dimension | `BIT_rank_exceeds_complement_shared_depth_two` | Individual exact-annihilator rank bounds do not apply to every BIT endpoint set. |
| Target relations remain constraints despite downstream composition | `target_relation_with_fixed_identity_downstream` | A requested response cannot violate an exact protected-span relation. |
| Omitted site, changed graph/policy/input relation or stale context | Receipt refusal records | Changed or incomplete semantics are not certified by recomputing an unkeyed hash alone. |

## Independent review, reproduction and preserved dependencies

Mathematical review has checked T1–T8, including cross-pair domains, initial relations, recurrence regimes, joint closure, state-block gains, repeated sharing, strict guards and observation scope; see [Review](P2_B3_Review.md). [independent_results.json](independent_results.json) reports `passed` in 39.415879754 s, with the following finite scope:

| Independent category | Actual coverage |
|---|---|
| Recurrences | 5,655 complete sequence/initial-value cases: lengths 0–3, gains `{0,1/2,1,2}`, forcing `{0,1/8,1}`, E0 in `{0,1/4,1}`; 180 constant envelopes at horizons `{0,1,2,5,9}` |
| Networks | 24 registered endpoint pairs, 288 registered points and 24 seeded rectangular networks |
| Recurrent comparisons | 36 analyses, 1,944 named initial-pair/history cases, 972 separate word trajectories and 2 common invariants |
| Guards | 4 uniform-margin certificates, 324 complete guard-pair cases and 32 seeded margin fixtures |
| Receipts and rollback | 12 registered receipts, 38 expected receipt refusals and 2 nonzero-moment B1 rollback fixtures |
| Frozen B1 evidence | 21 stored endpoint pairs, 84 protected call checks; all remain BIT-equal and exact-ALG-failing; no optimizer generation |
| Adversaries | 26 schema/domain/range refusals and 2 shared-call witnesses |

The independent verifier uses separate exact binary-word decoding and RNE word search, direct product-sums and independently reconstructed interval/trajectory calculations. It does not use producer test assertions as its oracle. The successful recorded run imported zero old verifier modules; a development-only module-name collision is separately disclosed in [Review](P2_B3_Review.md) and [Errata](P2_B3_Errata.md), with no old verification function executed. The result binds five current implementation/reviewer source hashes and all three saved producer JSON hashes. Its main seed is 20261114; its guard substream is explicitly 20261115. These independent finite scopes are not pooled into a universal proof count.

[verification_results.json](verification_results.json) reports aggregate status `passed`: all 3 planned sections completed, section assertion/refusal counts match the producer records, and all 699 predecessor artifacts passed before/after content and inventory checks. [driver_checks.json](driver_checks.json) records all four successful executions:

| Run | Working directory | Actual elapsed time |
|---|---|---:|
| Main aggregate | `/workspace/p2_b3` | 27.699216039 s |
| Main reproduction | `/tmp` | 26.186360291 s |
| Independent | `/workspace/p2_b3` | 39.415879754 s |
| Independent reproduction | `/tmp` | 38.071814596 s |

Main versus foreign main, independent versus foreign independent, and each of the three standalone producer records versus its aggregate section all match after excluding only enumerated timing fields. Source/producer identities, environment metadata, exact values and refusal reasons were compared. The driver also records successful expected `-O` and `-OO` refusals at preflight, exit code 1, with no scientific section attempted; the primary evidence files were unchanged by those negative checks. No prior suite or optimizer trajectory was rerun.

[dependency_inspection.json](dependency_inspection.json) records the passed read-only B2 manifest inspection and the expanded 699-file predecessor baseline. [dependency_baseline.json](dependency_baseline.json) includes original loose P1 directories, the publication worktree, P2 A1–A4/B1–B2 and root P1 summary/state files. `.git`, virtual environments and caches are explicitly excluded. Initial inspection is not a fresh exhaustive audit of every old proof. The completed driver verifies all 699 hashes and the full nonexcluded inventory unchanged, together with current-source and producer-evidence bindings.

The frozen B1 evidence remains 21 BIT-equal but exact-ALG-failing refusals, with dense FP32 AdamW 0 accepted / 8 refused and final loss 5/2. Certificate tests verify those saved records without regenerating the optimizer. No old stage suite or publication task was run.

## Evidence limits

Software BF16 and the available audited CPU FP32 path are different backend claims. GPU/native BF16, arbitrary FMA/reassociation or compiler substitutions, general concurrency, adversarial private runtime mutation and hardware faults remain uncertified. No SMT query or proof-assistant check is claimed by the producer records. Costs are actual local elapsed times, not performance advantages or scalability guarantees. Exact rational bit lengths and box conservatism can grow with depth/time.

B3 ends at fixed-endpoint, scoped delivery. The [B4 handoff](P2_B4_Handoff.md) identifies next obligations without implementing continual patch evolution or capacity decay.
