# B4 switching interface: explicit histories, two indices and read-only budgets

Saved after the B4 mathematical checkpoint and before `switching_bounds.py`. Numerical analysis never authorizes a live deterministic update. Exact D authorization and its serial history wrapper remain separate.

## Physical histories and time schedules

Reuse B3's fixed ordered affine/ReLU/identity graph and physical bank schema. Every physical endpoint snapshot is a dict from a bank ID to `{"weights": tuple(tuple(raw_words)), "bias": tuple(raw_words)}`. Every version has all and only the banks used by the fixed graph, with unchanged shapes. Bias belongs to its shared physical bank. All call sites are present and bank reuse remains explicit.

A history is a nonempty tuple/list of endpoint snapshots, with indices k=0,...,K. A schedule is a tuple/list of nondecreasing built-in integer version indices, one for each executed transition t=0,...,T-1. The t-th tick snapshots bank version k(t), reads the old state and shared external input, and commits the complete next state. Repeated indices represent ticks without a patch. A skipped version is an ordered patch endpoint with no executed tick using it; multiple patches can occur between ticks. Unused tail versions are also bound even though this finite execution horizon never uses them. No numerical analysis proves that those patches passed B1 authorization.

An arbitrary switching sequence A,B,A can be represented by three successive versions whose stored values revisit A; a decreasing version index is refused. Replacements are assumed serialized and preserve the numerical state between ticks. Neither patch count nor version number is the elapsed execution time. The concrete reference supports T<=64, at most 128 stored versions per history, and at most 16 distinct modes in a common-family invariant proof; these are implementation bounds, not theorem limits.

Comparison labels are exact:

- `original_reference`: old history has one endpoint, all old indices are zero, and that endpoint equals new history version zero. The initial state relation is still explicit; this label fixes the weight reference, not initial-state equality by itself.
- `adjacent_endpoints`: both arguments are the same full stored history and every tick compares new index=old index+1. The trajectories may have different states; the analyzer retains their propagated state difference. The same-input drift term inside each bound is specifically between those adjacent endpoints.
- `two_histories`: two explicit endpoint histories and schedules, without an extra endpoint-reference identification.

## Core APIs

`analyze_switching(graph, old_history, new_history, old_schedule, new_schedule, fmt, *, state_dimension, old_initial_bounds, new_initial_bounds, input_bounds, initial_error=0, comparison="two_histories", method="tube", state_box=None, common_family=None, budget=None)`:

- Supports one or two state coordinates. The first `state_dimension` graph input columns are state; remaining columns are common external input. The complete graph output is the next state and must have exactly that state dimension.
- Old/new initial symmetric boxes are separately supplied. The initial relation covers every admitted pair in those boxes with infinity distance<=initial_error. Zero initial error means paired equality, not merely membership in one common box. Each external input satisfies its declared coordinate bounds and is identical in both runs.
- Every step recomputes B3 `network_bound` at the actual selected stored endpoint pair and current old/new state enclosures, concatenated with the common external input box. Only the first-layer state columns contribute to the input-difference gain. All endpoint drift and both execution errors are retained.
- `method="tube"` propagates both state enclosures without truncation. An optional common `state_box` is a cap checked against initial and every propagated enclosure; failure is a conservative refusal rather than clipping.
- `method="common_invariant"` requires a common `state_box`. A `common_family` may explicitly list additional allowed endpoint snapshots; otherwise the family is the distinct union of both full histories. Every declared history version must belong to the family. Each mode must map the common state/input box into the common state box under certified rounded execution. Every ordered mode pair is bounded in the same infinity norm. A uniform-in-time envelope is returned only if the maximum exact state gain L is strictly below one; it applies conditionally to every finite continuation using modes from that same family and the same domains/policy. It is not inferred from the finite history.
- The finite trajectory still recomputes per-step joint tubes even when a separate common-family proof is available. The returned `steps` bind actual version indices, endpoint drift, L, beta, both rounding accounts, and old/new input/output boxes at every time.
- Return fields include `error_bounds` for t=0..T, `final_error_bound`, `observed_bound=max(error_bounds)`, `old_state_tube`, `new_state_tube`, `Ls`, `betas`, independent `product_sum`, schedule/version metadata, optional `common_family_proof`, and `budget_ledger`.
- Finite scalar/row bounds use exact rational arithmetic. B3's endpoint bound already contains generation/quantization effects through the actual endpoints; an increment ledger is not added again.

`budget_ledger(error_bounds,budget=None)` includes time zero, the running maximum of all prefix bounds, remaining budget, and the first exhausted index. With a supplied nonnegative absolute infinity budget it passes only if every prefix bound is <=budget. With no budget it records that none was requested. A final smaller bound cannot erase an earlier violation. `analyze_switching` with a supplied failed budget raises `BudgetExceeded`, a `SwitchingRefused` subtype carrying the computed ledger; this is read-only refusal, not state rollback from a partially published update.

`trace_history(graph, history, schedule, initial_state_words, input_sequence, fmt, *, state_dimension, initial_state_bounds, input_bounds)` executes the explicitly supplied point trajectory, retaining all state words and per-step B3 call traces. It checks initial/input domain membership, all versions and schedule, and actual finite operations. It does not clip a future state to the initial box or use an observed trajectory as a proof of an invariant.

## Fixed model registry and wrappers

| Model ID | Fixed graph | Initial state boxes | Shared input domain |
|---|---|---|---|
| `scalar_switching_v1` | one 1x2 identity affine call, bank `dynamics` | both magnitude<=1 | one input with magnitude<=1 |
| `relu_scalar_switching_v1` | same shape, ReLU activation | both magnitude<=1 | one input with magnitude<=1 |
| `nilpotent_switching_v1` | one 2x2 identity affine call, bank `dynamics` | both coordinates magnitude<=1/8 | no external input |
| `shared_relu_switching_v1` | two 2x2 calls of bank `shared`: ReLU then identity | both coordinates magnitude<=1/4 | no external input |

The complete registered legal input-history set is every finite sequence satisfying those raw canonical-word boxes. Observation is the **full recurrent state at every time 0..T**. Generic user-supplied graphs/boxes have their explicitly conditional scope; the fixed registry supplies a repeatable model/domain identity for a read-only receipt, not arbitrary source-program provenance.

- `model_descriptor(model_id,fmt)` returns the fixed graph, state/input layout, complete source-domain descriptions, numerical policy, schedule policy and prefix observation.
- `initial_banks(model_id,fmt)` gives one illustrative stored endpoint: scalar row(1/2,1/8), zero bias; nilpotent A=((0,2),(0,0)); shared bank=(1/2)I. Supplied histories may contain other validated endpoints of the same shape.
- `analyze_model(model_id,fmt,old_history,new_history,old_schedule,new_schedule,initial_error=0,comparison="two_histories",method="tube",state_box=None,common_family=None,budget=None)` supplies the registered graph and domains to the generic analyzer.
- `trace_model(model_id,fmt,history,schedule,initial_state_words,input_sequence,side="old")` supplies the appropriate initial/input domains to the point tracer.
- `compare_model_traces(model_id,fmt,old_history,new_history,old_schedule,new_schedule,old_initial_state_words,new_initial_state_words,input_sequence,initial_error=0,comparison="two_histories")` checks the actual initial pair relation and common external sequence, executes both histories, and reports per-time decoded infinity differences and raw equality. It is finite evidence, not a replacement for the analytic envelope.

`record(value)` converts exact fractions to the established B2/B3 numerator/denominator primitive representation. `SwitchingRefused` denotes a missing/invalid premise; `BudgetExceeded` additionally exposes `.ledger`. No receipt here certifies GPU/native BF16, arbitrary branching, concurrent updates or modified reduction/FMA policies. The separate transaction/receipt module must bind the complete supplied histories, schedules, source descriptor, initial relation, horizon, version/context and budget and recompute analysis. Its source hashes identify data/implementations, not authority to publish.
