# P2-B2 read-only numerical-budget certificate

## Scope and fixed object

This API produces detached evidence about one fixed shared linear matrix evaluated on a declared input envelope. It does **not** publish parameters, grant a live update authority, weaken B1's BIT or ALG_AND_BIT claims, or prove the safety of a perturbed feedback program.

The fixed read-only A3 registry supplies one of five named domains: `duplicate_feedback_v1`, `split_feedback_v1`, `thirds_two_inputs_v1`, `commit_rounding_v1`, or `shared_axis_v1`. Every listed input at every shared call site is included. These inputs are a complete *declared* finite single-layer domain, not discovered samples. The stateful descriptors also identify the original Boolean program envelope; the numerical certificate does not establish that a modified program remains in that envelope. A nonzero linear-output perturbation may invalidate Boolean state closure immediately. No bound on subsequent states is asserted.

All output ports are observed, and bias is fixed at the registry's canonical positive zero. The scalar endpoints are finite canonical BF16 or FP32 words; decode maps them to exact dyadic rationals. Negative zero, infinity and NaN are refused. The old and new words are separately supplied, and bounds use their actual decoded difference. No ideal optimizer step is substituted. The graph is fixed bias-first, ascending-column, separate multiply/add without skipped zero terms, with RNE, gradual underflow and canonical arithmetic zero. No reassociation, FMA or unverified graph change is admitted.

The mathematical scalar field for bound construction is Q with real Euclidean norms enclosed by outward rational intervals. The primary budget is an absolute full-output L2 bound. A separately named `linf` budget is also supported. A rational budget is nonnegative and finite; a host float is not accepted as an exact budget.

## Two supported methods

`complete_point_trace` evaluates both endpoints independently at every listed call input. Each point bound includes the exact decoded algebraic change and both executions' certified rounding contributions. The certificate takes the maximum of the selected L2 or infinity bound over all calls. Actual decoded differences are separately recorded: their complete finite-domain infinity maximum and squared L2 maximum are exact rational enumeration facts. Those observed maxima are not mislabeled as a universal analytic bound, nor substituted for the selected trace-bound algorithm.

`analytic_box` computes each input-coordinate bound as the maximum absolute decoded coordinate across the complete registry. Inclusion is proved directly for every listed call. The algorithm in `certified_bounds.py` proves intermediate operation ranges and a mixed relative/additive rounding bound over **every canonical finite raw input within that box**. Failure to establish a sufficient no-overflow range condition causes refusal, even if the smaller listed domain might execute safely. The analytic box can include inputs outside the original protected subspace; a larger bound therefore reflects both a larger quantified set and conservative arithmetic estimates.

The caller cannot supply a smaller box, omit a shared call, replace complete coverage with samples, change observation ports or relabel the graph. An unregistered domain is refused. Pointwise and box bounds remain conditional on the fixed numerical policy and totality assumptions proved by the corresponding method.

## API and externally expected semantics

```python
analyze_registered_domain(model_id, fmt, old_words, new_words,
                          method="complete_point_trace", norm="l2")

make_budget_certificate(model_id, fmt, old_words, new_words, budget,
                        method="complete_point_trace", norm="l2",
                        version=0, snapshot_context=None)

check_budget_certificate(text, model_id, fmt, old_words, new_words, budget,
                         method="complete_point_trace", norm="l2",
                         version=0, snapshot_context=None)
```

`analyze_registered_domain` is pure diagnostics. The producer checks that the recomputed bound is at most the requested rational budget before producing canonical JSON. The checker requires the expected old **and new** endpoints, norm, method, budget, version and optional context independently of the serialized text, then recomputes all semantic evidence and requires exact canonical equality. Rehashing an edited record does not bypass this check. The digest identifies data; it does not authenticate a caller, intent, global provenance or a live state.

The payload binds:

- schema, named read-only claim, norm, rational budget and method;
- both complete raw endpoints, shape, shared physical matrix and all registry sites;
- domain/invariant identifiers and registry source descriptor;
- zero biases and all output-port labels;
- fixed graph, numerical policy and source scheduling description;
- complete bound, call traces or box/range proof;
- expected version and optional full B1 context;
- source identities for the certificate code, numerical bound implementation, runtime, fixed registry and audited primitive execution.

The optional context is an exact primitive copy with the complete B1 snapshot schema, including weights, q, ticks, weight version, optimizer step/m/v, model, format, claim, config **and schedule**. Its old endpoint, model, format and version must agree with the numerical object. The remainder is bound as identity context. This is not a full B1 state-invariant validator and does not authenticate a snapshot, verify that it came from a live kernel, or establish optimizer consistency. Checking against the later snapshot after a tick fails even if the endpoint stayed unchanged. The A3 descriptor's call schedule and B1 context's publication schedule are distinct bound fields; neither turns this numerical receipt into a program-level authorization.

The receipt always sets:

```text
authorizes_commit = false
claims_BIT = false
claims_program_noninterference = false
candidate_state_invariant_verified = false  # in the bound payload
```

Even a zero numeric bound is not relabeled as a B1 commit certificate. A separate mathematical strict-output-separation corollary may imply local raw equality under its own canonical-domain premises. Program lifting still needs full input/invariant containment, fixed D, same initial state and inputs, trusted schedule and all A3 interface obligations.

## Refusal and side-effect behavior

Unknown domains/methods/norms, invalid words, negative or inexact budgets, unsupported totality, insufficient budgets, stale versions or snapshot identity, malformed or duplicate-key JSON, and any mismatch against complete semantic recomputation are refused. No state exists inside this producer/checker to commit or roll back. A caller can coherently request different complete evidence for a different explicitly supplied budget; that is a new read-only request, not a bypass of an externally expected existing budget.

The separate integration test submits this new JSON directly to the **unchanged** B1 `commit`. B1 rejects the schema/staged-transaction mismatch. It must preserve its complete composite bank, including nonzero first and second moments, optimizer time, endpoint, q/ticks and version. The fixture first makes one new B2 integration update using B1's legitimate joint checker; this is not a rerun of a frozen optimization experiment. The fixed accepted setup uses AdamW learning rate one, beta1=beta2=0, epsilon one, no decay, and gradient `((1,0),(0,0))`. Final exact projection produces the storable first-row increment `(-1/4,1/4)`, so both moment arrays become nonzero while the complete protected domain remains unchanged.

These statements concern a trusted serialized Python interface. They do not protect against arbitrary interpreter/module mutation, malicious process memory, concurrent writers, process failure or hardware faults.

## Frozen B1 analysis

`verify_certificates.py` reads the frozen B1 training JSON and analyzes every one of its 21 refused proposed endpoints. It does not regenerate gradients, optimizer moments, proposals or the old training trajectory. For each pair it freshly evaluates complete single-layer point bounds, an enclosing analytic box bound, exact decoded residuals and actual output differences. The original refusal remains a refusal: B2 evidence is never passed into a replacement B1 policy.

The analysis preserves the distinction that all 21 original candidates passed the registered BIT diagnostic but failed the chosen exact ALG condition. In particular, the frozen dense FP32 AdamW run had zero accepted commits, eight refusals and loss `5/2` before and after. A positive trace or analytic bound for an actually zero difference is conservative evidence, not a claim that the frozen outputs changed. Bound-to-observed-change ratios are undefined when the observed change is zero; the records do not divide by zero or report a finite relative tightness ratio in that case.

## Evidence and reproduction

`certificate_results.json` contains actual acceptance, refusal, tampering, snapshot rollback, seeded endpoint and frozen-analysis records, exact rational values, raw words, source identity, environment and measured costs. Main checks reuse the declared numerical producer and are not independent machine proofs. The separate independent verifier reconstructs numerical execution and envelope obligations through its own logic; its report states the scope. Universal algebra/rounding theorems, complete finite-domain enumeration and fixed-seed properties are separate evidence classes.

The actual main run passed **421 checks**, including **108 expected refusals**, with zero unexpected failures. It issued and checked **40 registered cases** (five models, two formats, two methods and two named norms), checked 16 seeded endpoint pairs and two new B1 integration rollback fixtures, and analyzed all 21 frozen refused endpoint pairs. Each named finite domain has 1, 2 or 4 listed calls, and each receipt includes all of them; duplicated physical inputs at different sites remain separate bound observations.

| Frozen B1 group | Endpoint pairs | Fresh actual L2 change | Point-trace L2 bound |
|---|---:|---:|---:|
| BF16 momentum | 6 | 0 | `1/256` |
| BF16 AdamW | 7 | 0 | about `0.005524271728` (exact outward rational in JSON) |
| FP32 AdamW | 8 | 0 | `1/16777216` |

Every exact effective change in this table fails ALG, and every fresh complete-domain actual output difference is zero. Every point bound is positive and smaller than its analytic-box counterpart. This demonstrates conservatism and the difference in quantified input sets, not an observed nonzero output error. The original frozen loss and refusal outcomes are unchanged.

```sh
python /workspace/p2_b2/verify_certificates.py
```

Run without `-O` or `-OO`. The script writes beside itself and supports execution from another current directory. It imports only declared read-only prior runtime modules; no previous verification suite is invoked. GPU, native BF16, arbitrary compiler optimization, general concurrency and full program state-error propagation remain uncertified.
