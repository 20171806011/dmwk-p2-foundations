# P2-B4 exact-D sequences and separate read-only switching budgets

## Two independent contracts

`update_sequence.py` is a new trusted serialized owner around the **unchanged B1 exact gate**. It publishes accepted weights, optimizer state and history together. `sequence_certificate.py` is a different, read-only numerical evidence type for explicit changing endpoint histories. A numerical receipt is not an exact-D transaction and cannot be used to waive BIT or ALG_AND_BIT requirements.

The exact-D fixture is B1's `structural_duplicate_v1`: a 2-by-3 shared bank with first columns I2, editable third column theta, fixed zero bias and two protected call sites `(q,q,0)` and `(u,u,0)`. D's admitted sparse arithmetic reads columns zero then one, protects both full two-component outputs and applies the inherited same-snapshot XOR transition. Both q and u are canonical bits. A uses the legal e3 input and exposes theta. There is no A-to-D feedback, dynamic task admission or changing protected input domain in this live reference.

The selected gate is always **ALG_AND_BIT**. An accepted step must satisfy the unchanged complete registered B1 contract, not merely an ideal gradient or numerical perturbation budget. For the globally protected line through `(1,1,0)`, the unrestricted exact annihilator has dimension four. The structural reserved-column family has dimension two and every actual stored increment has rank at most one. Its A-e3 response space has dimension two. Those numbers describe exact algebra/structure, not a same-dimensional finite storage or BIT set.

## Exact-D public interface and ownership

```python
SequenceKernel(fmt, optimizer_config, max_updates=128)
owner.snapshot()
owner.evaluate_a()
owner.full_D()
owner.toy_gradient()
owner.preview(request)
owner.prepare(request)  # canonical JSON
owner.commit(prepared_text)
owner.tick(canonical_input_word)
```

Requests retain the unchanged B1 AI/optimizer schema. AI directions and optimizer gradients are trusted caller proposals; the wrapper does not authenticate a model's intent or prove that every supplied gradient is a derivative of its measured objective. The specific experiment uses `toy_gradient`. An arbitrary accepted safe AI edit may increase loss. Only the exact-D gate is a safety condition.

The owner stores one private `CombinedState` containing a B1 kernel, a tuple of canonical accepted-update event strings and a tuple of canonical tick event strings. No public method returns the owned kernel. Snapshots and previews are detached primitive copies; the exported weight value is an immutable tuple of tuples. Configuration, optimizer-state and history exports do not provide mutable aliases into the owner.

To prepare an update:

1. Snapshot the complete current owner and deep-copy its B1 kernel privately.
2. Prepare and commit the unchanged B1 candidate **on that copy**. Its endpoint/config/optimizer/domain/graph/policy checks remain mandatory.
3. Check the administrative history limit and complete before/after D observations; verify that a weight update preserved q/ticks.
4. Construct the new accepted event, immutable ledger, replacement combined value and canonical receipt data.
5. During commit, repeat this staging against the current complete owner and require exact canonical agreement with the supplied prepared record.
6. Publish exactly one new outer `CombinedState` reference after all refusing work and return-value construction succeed.

A tick follows the same ownership rule: execute on a private copy, build its immutable tick event and result, then publish one replacement. There is no publicly applied B1 update followed by a separately failing ledger update. In particular, the accepted-ledger limit is deliberately checked after the copy-local B1 commit; tests verify that this late refusal leaves the real owner unchanged.

This is a trusted serialized Python memory model. Private-member/module mutation, malicious interpreters, general concurrent callers, process failure, crash durability, arbitrary host allocation failure and hardware faults are outside its proof. It is not a production persistent transaction manager.

## Snapshot and candidate binding

The complete snapshot binds B4 schema/schedule; fixed toy task and D descriptor; nested B1 endpoint, q/ticks, weight version, optimizer step/m/v, config, claim and B1 schedule; accepted-update and tick ledgers; ledger limit and tail digest; fixed origin identity; and the explicitly scoped capacity record. Candidates additionally bind the exact request, full inner B1 prepared evidence, staged endpoint and optimizer snapshot, new ledger event and source identities. A later tick invalidates a prepared update even when weights are unchanged. A later accepted update or replay also invalidates it.

Every accepted event records adjacent old/new words and exact effective difference/rank, prefix difference/rank against the fixed original bank, ideal increment, actual A output/loss, all four complete D state/input observations, old/new optimizer states, acceptance index, current execution tick and B1 receipt. The sum of adjacent matrix-infinity increment norms is a **descriptive path length**, not an additional execution-error term to add to an already direct endpoint bound.

The fixed task is squared loss on A-e3 toward theta `(1,-1)`, initially `(1,0)`. Loss is calculated with exact rationals after decoding the actual BF16/FP32 A output. The gradient used in the experiment belongs to the continuous linear squared-loss extension at that endpoint; it is not a derivative of target-format rounding.

Candidate hashes establish semantic identity under recomputation, not historical intent. A coherently prepared new trusted request with complete valid evidence is a new request. Arbitrary rehashed changes to task, domain, schedule, endpoints, optimizer state or ledger do not bypass the checks.

## Separate counters and limits

Diagnostic attempts are counted by the test driver. Refused attempts do not modify the owned accepted ledger. The accepted index k includes every accepted transaction, including zero stored changes. The nonzero stored-update count is separate. A B1 weight version increments on each accepted transaction; optimizer time advances on accepted optimizer requests, while accepted AI requests retain optimizer state. Protected time t advances only on a legal tick.

`max_updates` defaults to 128 and is an administrative ledger-length limit. It is not algebraic dimension exhaustion, a numerical error budget or a claim that the safe endpoint family has become empty. B1's bounded tick/version counters and canonical parsing size limit also remain explicit reference limitations. The closure theorem concerns admitted prefixes; the implementation does not promise unlimited accepted updates despite finite resource counters.

## Actual repeated-learning evidence

Both formats ran 32 SGD attempts at learning rate `1/4`, all accepted, with the same seed **20261114** and same legal 32-bit external-input sequence. Every accepted endpoint passed the complete D domain and every tick matched an unchanged B1 peer. The actual results are:

| Format | Accepted | Nonzero stored changes | Accepted no-ops | Final theta | Exact final loss |
|---|---:|---:|---:|---|---|
| BF16 software model | 32 | 16 | 16 | `(1,-127/128)` | `1/32768` |
| Audited CPU FP32 | 32 | 32 | 0 | `(1,-16775531/16777216)` | `2839225/562949953421312` |

Initial loss was `1/2` in both cases. FP32 final loss is about `5.043476747e-9`. BF16's first stored no-op is attempt 17. At the stalled second coordinate `-127/128`, the exact gradient step toward -1 is a half-ULP tie and RNE retains the existing even endpoint. Subsequent identical proposals remain zero stored changes. This is a property of this proposal/quantizer/current endpoint, not a deduction that the full fixed safe family or its algebraic dimension shrank.

A separate tiny AI proposal in both formats rounds to a zero effective change and is accepted as such; a subsequent larger reserved-column AI edit is nonzero and accepted. Thus the test directly distinguishes local representability stalls from inability to make any safe A-response change. The live global span, unrestricted algebraic dimension four, reserve dimension two and response dimension two remain unchanged throughout. The accompanying pure capacity history helper explicitly does not invent global provenance from its supplied generator; the fixed complete B1 registry and structural proof supply that separate premise.

The toy improvement establishes this finite objective's response and loss changes under exact D protection. It is not evidence of universal convergence, general task benefit, generalization or a performance advantage. The reference copies and serializes growing ledgers; its measured runtime is not a throughput benchmark.

## Read-only changing-history certificate

```python
make_sequence_certificate(
    model_id, fmt, old_history, new_history, old_schedule, new_schedule, budget,
    initial_error=0, comparison="two_histories", method="tube",
    state_box=None, common_family=None, version=0,
    initial_pair=None, external_context=None)

check_sequence_certificate(text, ...same externally expected arguments...)
```

The trusted switching registry supplies scalar identity/ReLU, two-coordinate nilpotent and shared-ReLU graphs with fixed source domains. Each complete endpoint history contains actual stored weights and biases for every physical bank, including versions that receive no executed tick and unused tail versions. Nondecreasing schedules independently select old and new version indices for each execution time. Revisiting a mode uses a new stored history entry; a decreasing version index is refused. Patch count, accepted-update count and execution time are not interchangeable.

The comparison is explicitly `original_reference`, `adjacent_endpoints`, or `two_histories`, with the switching core enforcing the corresponding endpoint/schedule identities. The certificate binds the complete histories and all shared sites, not just the selected endpoints at the final time. An unused version can change the identified history or a declared invariant mode family even when it does not change the current finite trajectory.

The initial relation consists of every registered canonical pair in the old/new initial boxes with distance at most E0. Zero E0 means equal initial states, not overlapping boxes. Inputs are the same legal raw history in both runs. Optional `initial_pair` is checked against this relation using a zero-tick initial check; this does not replace analytic future containment with a sample trace.

The core recomputes each selected pair's actual endpoint drift, exact-map state gain, both execution-rounding contributions, joint domains and full-prefix recurrence. `tube` proves the stated finite envelope. `common_invariant` proves all declared modes preserve a common box, covers every full-history version and every mode pair in one infinity norm, and reports a conditional uniform envelope only when its additional contraction premises hold. A scalar cap is normalized to a one-coordinate vector; other state dimensions require a correctly shaped vector. No unproved cap truncates the propagated domain.

The budget ledger includes time zero and every prefix, retains the running maximum and remaining budget, and refuses when any certified prefix bound exceeds the budget. A conservative bound exceeding a budget does not, by itself, prove that the actual output exceeded it. A later cancellation or small final bound does not erase earlier certified consumption. Direct endpoint drift already includes generation/optimizer/storage effects; the live descriptive update path length is not added to it again.

The producer/checker binds registry/domain provenance, numerical policy, schedule policy, all histories, indices, biases, reference choice, E0 and optional initial pair, full-state prefix observation, horizon, method, cap/common family, version, budget and computed ledger. The checker receives all expected inputs independently of the serialized record and recomputes them. Expected versions/contexts are identity bindings, not discovered live state or authenticated history.

Optional external context is a complete B4 exact-D snapshot with both outer and nested schedules, task, domain and ledger fields. It is identity metadata only. The numerical scalar/two-coordinate graph is not asserted to be the 2-by-3 exact-D bank or its Boolean state. The receipt always declares `authorizes_commit=False`, `claims_BIT=False`, `claims_exact_ALG=False` and `claims_program_noninterference=False`. Both unchanged B1 and new B4 exact commit interfaces reject it, preserving their complete owned snapshots, including nonzero optimizer moments.

## Verification, correction and remaining limits

The actual transaction verifier passes **1,120 checks**, with **98 expected refusals** and zero unexpected failures. It records 64 accepted training updates, 48 nonzero stored changes and 64 paired D ticks; 58 rehashed exact/numerical tampering cases; 12 valid numerical comparison cases; 14 budget-exhaustion records, including final cancellation with an earlier violation; and four late-refusal/numeric-authority rollback records. Main and independent evidence have separate logic and scope.

An initial integration run exposed a cap-type mismatch: the B4 switching core requires coordinate vectors, while a fixture initially passed B3's scalar convenience form. The new fixture was corrected to `(2,)`, and the new receipt normalizes scalar caps to one-element vectors. The affected complete B4 verifier was rerun successfully. This changed no predecessor evidence and was not presented as a failed mathematical theorem.

Frozen B1 evidence is read only: all 21 original refused endpoints remain BIT-equal under their recorded domain but ALG-failing; dense FP32 AdamW retains zero accepted steps, eight refusals and initial/final loss `5/2`. No old optimizer trajectory is regenerated. Numerical receipts do not retroactively authorize those candidates.

The implementation uses software BF16 and locally audited scalar CPU FP32 with canonical zeros and the declared separate-operation graph. GPU, native BF16, arbitrary compiler/FMA/reassociation changes, arbitrary branches, concurrent mutation, durable crash transactions and whole-host machine correctness remain uncertified. Handwritten closure/induction theorems, complete small-domain checks, fixed-seed histories and independent arithmetic replays are distinct. This stage does not implement C1 or a production learning kernel.

```sh
python /workspace/p2_b4/verify_transactions.py
```

Run without `-O` or `-OO`. The actual output is `transaction_results.json` beside the script. The root aggregate performs foreign-directory reproduction and verifies that prior evidence is unchanged.
