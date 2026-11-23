# P2-B3 read-only propagation-budget certificate

## Claim and scope

The concrete certificate bounds a fixed old/new pair of stored affine/ReLU networks or state maps in the **infinity norm**. It binds the finite horizon, complete input quantifier, initial relation, full observation, graph and shared physical banks, and recomputes the joint domain-containment and arithmetic-totality proof. It publishes no endpoint, state or optimizer value and authorizes no BIT/ALG_AND_BIT update.

Generic norm theorems elsewhere do not imply an L2 implementation here. The certificate's numerical budget is a nonnegative exact rational absolute infinity bound. Host floats are refused as exact budgets. The endpoints include actual stored weight **and bias** words at each physical bank; ideal proposed updates are not substituted. Each physical bank is fixed throughout the analyzed interval. All appearances of a shared bank use the same old/new tensors and bias.

The concrete reference accepts finite canonical BF16 or FP32 words, RNE with gradual underflow, canonical positive zero, bias-first ascending-column separate multiply/add, and the exact finite-word identity or coordinatewise ReLU operation. Arbitrary activations, FMA, reassociation, flush-to-zero, skipped terms and changed accumulator precision have no inherited certificate.

## Trusted model registry and observation

| Model | Complete source domain and observation |
|---|---|
| `two_layer_relu_v1` | Every identical canonical two-component old/new input with each magnitude at most one; all final output coordinates after the two declared calls |
| `shared_relu_v1` | The same complete input box, with two distinct calls to one physical bank; all final output coordinates |
| `contractive_scalar_v1` | Every admitted initial pair defined below and every same legal input history; full scalar state at every time `0..T` |
| `neutral_scalar_v1` | The same initial/input relation and full-state observation; its name does not certify arbitrary replacement endpoints as neutral |
| `amplifying_scalar_v1` | The same initial/input relation and full-state observation; an amplifying upper envelope does not prove observed error growth |

Default feedforward banks are `I2` followed by `(1/2)I2`; the shared default is `(1/2)I2` used twice. Recurrent defaults act on `(s,u)` with rows `(1/2,1/8)`, `(1,0)`, or `(2,0)`. All defaults have zero bias. A submitted endpoint pair can change these stored values within the fixed shapes; containment, totality and bounds must then be proved anew. Names and default examples are not safety evidence for changed parameters.

Feedforward receipts require horizon one, initial error zero and the tube method. The recurrent implementation supports finite horizons `0..64`. It quantifies **every** shared legal raw input sequence of the given length, with `|u_t|<=1`, and the initial relation

`R0(E0) = {(s0,s0'): canonical finite scalar words, |s0|<=1, |s0'|<=1, |s0'-s0|<=E0}`.

Thus `E0=0` means the same initial canonical word; it is not inferred from overlapping initial boxes. Nonzero E0 is a bound restricting a paired domain, rather than a statement that arbitrary pairs in the two boxes are that close. Every claimed actual initial pair must satisfy this relation. The same input history is essential; independent histories would need a separate forcing term and contract.

For recurrence the checked budget is `max(E_0,...,E_T)`, so a small final bound cannot hide a larger initial or intermediate bound. Feedforward budgets concern all final output ports; intermediate boxes and errors are bound evidence, not a claim that intermediate effects are bitwise unchanged. No output-port subset can be substituted into the fixed registry.

## Joint containment and arithmetic proof

The producer calls `propagation_bounds.analyze_model`, whose accepted proof must explicitly report `domain_containment_proved=True`, `totality_proved=True`, and `norm="linf"`. The core propagates both old and new intermediate enclosures, all shared call sites and the two executions' rounding terms. The new exact map's state Lipschitz bound is not assigned to the rounded staircase map. Common external input coordinates remain in range/forcing calculations but are excluded from the first recurrent state-difference factor.

The `tube` method constructs a finite old/new tube through the requested horizon. An optional common scalar cap must contain both initial and computed endpoint enclosures at every required step; the algorithm refuses rather than truncating an enclosure. The `invariant` method proves a common rounded-map invariant and totality for both endpoints, including initial-domain containment, before deriving constant-envelope results. A finite receipt still checks its stated `0..T` observation budget. Any auxiliary uniform-in-time theorem in the proof has separate invariant and contraction hypotheses; it is not inferred from a finite test or silently used to broaden the budget's horizon.

The bound is analytic over its declared domain. A caller's sample set, unsupported subspace label or observed maximum cannot replace domain provenance or joint containment. A conservative interval failure may refuse an actually safe system; refusal is not automatically an actual trajectory-escape witness.

## API and binding

```python
make_propagation_certificate(
    model_id, fmt, old_banks, new_banks, budget,
    horizon=1, initial_error=0, method="tube", state_box=None,
    version=0, state_context=None, external_context=None)

check_propagation_certificate(
    text, model_id, fmt, old_banks, new_banks, budget,
    horizon=1, initial_error=0, method="tube", state_box=None,
    version=0, state_context=None, external_context=None)
```

Banks have the exact schema `physical_id -> {"weights": tuple_of_word_rows, "bias": tuple_of_words}`. All and only the registered graph's bank identifiers must be present, with the registered shapes. A layer occurrence has a distinct call identifier, physical bank reference and specified activation. Replacing only one occurrence of a shared bank is not a legal physical endpoint representation.

The checker receives all expected endpoints and semantic parameters independently of the serialized text. It recomputes the complete registered proof, requires the bound to fit the externally expected budget, and compares canonical serialized records exactly. This rejects a rehashed but inconsistent graph, site list, policy, schedule, bias, endpoint, domain, initial relation, observation, horizon, version, proof or budget. Hashes provide content/source identity, not authentication of caller intent or of domain assertions.

Bound fields include the full descriptor, both physical endpoint sets, full output ports, numerical policy, schedule, fixed registry provenance, same-input-history quantifier, initial relation and E0, both-execution containment claim, horizon/method/cap, expected version, full proof, optional contexts and implementation identities. The reference bounds serialized receipt size at 16,000,000 characters and horizon at 64; these are explicit reference-interface limits, not limits on the conditional mathematical recurrence theorem.

All successful receipts set `authorizes_commit=False`, `claims_BIT=False`, `claims_exact_ALG=False`, and `claims_program_noninterference=False`. A strict finite-output gap theorem is separate. Even a zero budget at horizon zero is not relabeled as a live deterministic-program authorization.

## Two different kinds of context

Optional `state_context` has schema `dmwk-p2-b3-initial-context-v1` and binds model, format, weight version, complete old/new banks, old/new initial raw words, ticks and the required schedule. The producer validates the initial words, dimensions, registered magnitude bounds and actual initial difference against E0; a different initial state cannot be slipped into an E0=0 receipt. Bank identity uses exact canonical primitive serialization, avoiding Python boolean/integer equality aliases. Version/ticks are bounded nonnegative built-in integers.

This is initial-domain and identity checking, not live-state authentication. It does not prove that the supplied state was historically reachable at the supplied tick count. The analysis applies to any initial pair in its stated relation, so no historical reachability claim is needed. A checker rejects stale context when supplied with the currently expected context; a stateless read-only checker does not independently discover the live current version.

Optional `external_context` has kind `B1_identity_only` and contains a complete B1 snapshot schema: model, format, claim, config, weights, q, ticks, version, optimizer step/m/v and schedule. It is **unrelated identity metadata**. In particular, a B1 2-by-2 bank is not equated to a B3 scalar recurrence, and this context establishes neither B3 initial-state provenance nor a mapping from the B3 numeric graph to the B1 protected program. It is not a full B1 invariant validator or an authenticated snapshot. Omitting its schedule or other snapshot fields is refused.

## New B1 boundary fixture and preserved old evidence

The verifier constructs one new B3 integration fixture per format using the unchanged B1 API. AdamW with learning rate one, beta1=beta2=0, epsilon one, no decay and gradient `((1,0),(0,0))`, followed by the existing final projection, makes the joint-safe dyadic first-row increment `(-1/4,1/4)`. This accepted setup creates nonzero first and second moments. A legal protected tick then advances state/ticks.

Submitting a B3 numeric receipt to the unchanged B1 `commit` is refused. The test compares the entire before/after snapshot, including weights, q, ticks, optimizer moments/time and weight version. A later legal tick changes only its legitimate state context; checking the old B3 receipt against the later externally expected snapshot also refuses. This exercises an interface boundary and does not rerun the frozen B1 optimizer trajectory.

The old B1 training JSON is read-only. Its 21 refused endpoints remain BIT-equal under the recorded fixed domain while failing exact ALG. Its dense FP32 AdamW joint route retains zero accepted commits, eight refusals and unchanged loss `5/2`. B3 neither replays those optimizer steps nor changes their acceptance policy.

## Actual verification and evidence levels

The actual `verify_certificates.py` run passes **498 checks** with **128 expected refusals** and zero unexpected failures. It covers **44 registered receipt cases**, **46 rehashed tampering cases**, eight seeded endpoint examples and two new B1 rollback fixtures with nonzero moments. The seed is **20261114**. Registered cases include both formats, both multilayer/shared graphs, recurrent horizons 0, 1 and 4, E0 values 0 and 1/4, and contractive invariant proofs. They do not enumerate every endpoint or every horizon through 64.

The rejection cases cover absent schedule/provenance, samples substituted for a domain, omitted shared calls, wrong bank sharing/activation, FMA or asynchronous policy, endpoint/bias changes, stale version/state context, changed input histories or observation ports, false old-only containment, insufficient budgets, invalid initial relations, malformed JSON and unproved invariant/tube caps. Exact raw points and rational proof fields are retained in `certificate_results.json` along with environment, source identities, counts and wall-clock costs.

Each analytic receipt's universal domain statement depends on the handwritten core proof and trusted implementation. Main checks recompute that implementation; they are not independent machine proofs. The independent verifier uses its own arithmetic/reference logic and separately reports its finite coverage and findings. GPU, native BF16, general concurrency, arbitrary compiler transformations, malicious host mutation, crash consistency, continual endpoint evolution and B4 training remain outside certification.

```sh
python /workspace/p2_b3/verify_certificates.py
```

Run without `-O` or `-OO`. Output is written beside the script, independent of the working directory. The root aggregate verifies foreign-directory reproduction and predecessor integrity. No prior verification suite is imported.
