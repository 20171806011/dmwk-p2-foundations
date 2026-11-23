# C1 compiler interface — fixed bounded reference

This interface fixes a closed trusted source and emitter, not a generic validator for arbitrary external programs. Implementation follows the saved mathematical checkpoint. All old modules are read-only dependencies.

## Source

`compile_program(source, budget, fmt, response_request=None, mode="structural")` takes a built-in JSON-compatible dictionary with exactly these fields:

```
schema: "dmwk-p2-c1-bool-fsm-v1"
state_ports: [distinct labelled names], length 1..2
input_ports: [distinct labelled names], length 0..2
output_ports: [distinct labelled names], length 1..2
initial_states: nonempty list of distinct canonical bit lists
next_state: one expression per state port
outputs: one expression per output port
```

Names are ASCII identifiers of at most 32 characters and distinct across all three namespaces. Expressions are built-in prefix lists: `["const",0/1]`, `["state",index]`, `["input",index]`, `["not",e]`, `["and",a,b]`, `["or",a,b]`, `["xor",a,b]`, `["mux",c,a,b]`. Bit constants and indices are exact built-in integers, never host floats or booleans. Each expression has depth at most 8; the complete source has at most 256 expression-node occurrences. Shared Python references do not imply common-subexpression elimination. Cycles and unknown fields/operators are refused.

All state/input values are Boolean. Initial states are the stated nonempty subset; the invariant and step domain are **all** Boolean states and inputs. Every output and next-state expression reads the same old snapshot. Outputs are pre-transition observations. Reset, hold and halt-like behavior require explicit Boolean expressions; there are no implicit reset/halt ports, effects, hard floating guards or source jumps.

## Lowering and numerical graph

All next-state expressions are lowered in state-port order, then all output expressions in output-port order. Children are evaluated eagerly left to right, once per syntax occurrence. Leaves become typed wires; no folding, CSE, reassociation or scheduling optimization occurs. The only generated gate operations are AND and NOT. Derived gates lower as:

- OR(a,b) = NOT(AND(NOT(a),NOT(b))) — four primitive calls.
- XOR(a,b) = AND(OR(a,b),NOT(AND(a,b))) — seven primitive calls after lowering its children once.
- MUX(c,a,b) = OR(AND(c,a),AND(NOT(c),b)) — seven primitive calls after lowering its children once.

The single physical bank has shape `(2+p,3+q)` with p=A rows and q=A columns. D block rows are `(1,1,-1)` and `(-1,0,1)`; cross blocks are fixed +0 and A block is editable. Fixed bias is +0 throughout. A D call prepares `(a,b,1,0,...,0)`; NOT uses b=0. It computes **both** D rows using columns 0,1,2 in ascending order, separate rounded multiply/add from a +0 accumulator, then coordinatewise ReLU. Selected row 0 is AND and row 1 is NOT. A rows are not evaluated in a D call. There are 12 floating binary operations per D primitive call.

A calls prepare `(0,0,0,z)` and evaluate only the A block, with identity activation, zero bias and ascending separate multiply/add. Legal A input vectors z are exactly zero and the q positive coordinate basis vectors. Every finite canonical A endpoint is total on this domain, including saturated finite values. These A inputs have fixed labelled shared-call identities in the artifact. No A value, output or optimizer state is read by the D graph.

Canonical finite BF16/FP32 words only; stored negative zero, nonfinite words and host floating inputs are refused. Arithmetic uses inherited RNE/gradual-underflow/+0 normalization, software BF16 or audited CPU FP32. FMA, altered precision or other graph policies are unsupported.

## Budget

The budget has exactly these built-in nonnegative integer fields:

```
d_row_budget, d_col_budget,
a_rows, a_cols,
parameter_budget, call_budget,
min_A_response_dimension, required_update_rank
```

A sizes p,q lie in 1..2. Required fixed D resources are two rows and three columns. The physical dense storage receipt counts `(2+p)*(3+q)` words; the D call budget covers emitted primitive calls per tick. Required A-response dimension cannot exceed p*q; required individual rank cannot exceed min(p,q). These are reservation/existence budgets, not a per-update rank-cap authorization. Call budget is capped at 2048 in this small implementation. `default_budget(a_rows=1,a_cols=1)` gives explicit permissive defaults for all fields. Dense word storage, structurally nonzero cells, sparse arithmetic per site and wire/state overhead are separately reported.

## Initial A anchors

Optional `response_request` has exactly `inputs` and `outputs`, lists of matching length 1..8. Inputs are q-coordinate exact Boolean zero/basis vectors. Outputs are p-coordinate exact rational values, represented canonically as `[numerator,positive_denominator]` in lowest terms (zero is `[0,1]`). Conflicting duplicate anchors or nonzero output on zero input are refused. Unspecified basis columns initialize to zero. The resulting exact A matrix must be exactly representable in the selected format; a rational such as 1/3 is refused as an exact initial anchor. The compiler also validates its actual fixed-graph outputs on these legal inputs.

These are **initial A assignments**, not protected tasks that future learning must preserve. General mixed-direction response analysis is a separate exact read-only diagnostic; it does not enlarge this compiler's legal input graph or authorize geometric BIT updates.

## Pure API and artifact

Module `c1_compiler.py` exports:

- `validate_source(source)`, `source_step(source,state_bits,input_bits)`; the latter returns `next_state_bits` and `output_bits` and is only a mathematical/test interpreter.
- `default_budget(...)`, `compile_program(...)` returning a detached canonical primitive dictionary.
- `check_artifact(artifact, expected_source, expected_budget, fmt, response_request=None, mode="structural")`, reconstructing the complete expected artifact and requiring exact equality.
- `initial_weights(artifact)`, `initial_state_words(artifact,index=0)`, `legal_states(artifact)`, `legal_inputs(artifact)`.
- `validate_endpoint(artifact,words)` returning immutable admitted words; it requires the fixed D/cross cells and every word policy, without changing the artifact.
- `execute_d(artifact,words,state_words,input_words)` returning `next_state_words`, `output_words`, `site_traces`, `arithmetic_counts`; each site trace records its ID, argument words, complete physical activation, two preactivations/ReLU outputs and selected row/result.
- `evaluate_a(artifact,words,a_input_words)` returning `output_words`, `arithmetic_counts` and its labelled A site. Inputs are q-coordinate vectors, not full mixed vectors.
- `canonical_json`, `digest`, `decode_matrix`, `quantize_endpoint` for callers that need exact stored differences.

Artifact keys include `schema`, `format`, `source`, `budget`, `response_request`, `source_sha256`, `graph_sha256`, `graph`, `layout`, `domain`, `capacity`, `proof`, `cost`, `initial_weight_words`, `numerical_policy`, `schedule`. `layout` exposes `a_rows`, `a_cols`, `full_shape`, `writable_cells` and `fixed_cells`. `graph` contains all ordered D calls and ports and all legal A call descriptors; identities are immutable within the compiled artifact. `domain` includes initial-state words, complete Boolean state/input sizes and A domain words.

The always-containing protection space is the first three physical coordinate axes, rank 3. A complete finite enumeration across **all** Boolean states/inputs and every emitted D call additionally reports the actual generated-call span and per-site activation sets. This finite complete state envelope may include unreachable states from the selected initial subset. A source with no gates has actual D-call span rank zero while the deliberately conservative reservation still uses rank three. The authorization is structural, not based on a sampled or unexpectedly small rank.

Runtime validation is strict but is not an external-program discovery oracle. The caller must first bind/reconstruct the artifact against the expected complete source and budgets. The serial publication owner will retain this bound artifact and enforce endpoint/version/state/optimizer/ledger contracts separately.

`c1_runtime.py` exposes `get_fp()`, `load_b1(name)`, `load_a4(name)`, `load_a3(name)`, `load_a2(name)` and `environment_metadata()`, with an explicit allowlist of pure old dependencies and no previous verifier imports.
