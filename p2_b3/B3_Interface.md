# B3 interface: fixed endpoints, joint domains and finite propagation

Saved after the B3 mathematical checkpoint and before implementation. All numeric bounds use exact `Fraction` values and the infinity norm. Raw execution retains the P1 bias-first, ascending-column, separate multiply/add, canonical-zero BF16/FP32 policy. Every receipt remains read-only.

## Physical banks and graphs

`banks` is a dict from a physical bank ID to `{"weights": tuple(tuple(raw_words)), "bias": tuple(raw_words)}`. Old and new bank sets have identical IDs and shapes. Bias is part of the physical affine bank and is shared whenever that bank is reused. A graph is an ordered tuple/list of exact-key dictionaries `{"call_id": str, "bank_id": str, "activation": "identity"|"relu"}`. Call labels are unique; repeated bank IDs intentionally mean shared parameters. All and only referenced physical banks must be present; adjacent dimensions must match. No caller-supplied sample list replaces a declared domain.

## `propagation_bounds.py` generic pure helpers

- `validate_network(graph,banks,fmt) -> descriptor`: validates the complete graph/bank schema and shapes.
- `initial_banks(model_id,fmt) -> banks`, `model_descriptor(model_id,fmt) -> dict`: fixed trusted registry, below.
- `trace_network(graph,banks,input_words,fmt) -> dict`: actual fixed-order affine traces plus exact word ReLU/identity. Returns `output_words`, per-call `calls`, exact-real network output at the same decoded input, and per-call exact/rounded activations. No proof of arbitrary input history is inferred from this point trace.
- `network_bound(graph,old_banks,new_banks,old_input_bounds,new_input_bounds,fmt,initial_error=0,first_difference_columns=None) -> dict`: constructs endpoint-specific propagated symmetric input/output boxes. Each call uses a joint input box containing both endpoints, B2's analytic totality/rounding proof for both affine endpoints on that joint box, the exact new-map Lipschitz constant and a uniform same-input forcing term. At the first layer only, `first_difference_columns` may restrict the differing input coordinates (the other coordinates must be equal by the caller's relation). It defaults to all coordinates. Subsequent calls use all coordinates.
- Per-call forcing is the exact same-input affine endpoint-difference infinity bound on the joint box plus the two separately certified rounding errors. ReLU/identity are 1-Lipschitz, so the same bound remains valid after activation. The layer recurrence is `E_next=L_new*E+beta`. Output radii are proved from the separate old/new affine range enclosures and the selected activation; no externally supplied cap is used to truncate a computed radius.
- Network return keys: `error_bounds` (including E0), `final_error_bound`, `lipschitz_product`, `forcing_bound` (composition from zero initial difference), `old_input_bounds`, `new_input_bounds`, `old_output_bounds`, `new_output_bounds`, `calls`, `norm="linf"`, `domain_containment_proved=True`, `totality_proved=True`.
- Every call record contains `call_id`, `bank_id`, activation, old/new/joint input bounds, old/new output bounds, exact-new-map `L`, same-input exact drift, both rounding terms, `beta`, previous/next E, and the B2 joint operation-range proof. `L` is not claimed to be a Lipschitz constant of the rounded staircase map.
- `propagate_recurrence(Ls,betas,initial_error=0) -> dict`: exact rational nonhomogeneous recurrence and a separately computed product-sum. Returns the full series and final value. Empty lists give E0.
- `constant_recurrence(L,beta,horizon,initial_error=0) -> dict`: exact constant-L geometric formula, including L=0 and L=1. It classifies the upper envelope; no invariant-domain proof is implied by this algebra helper.
- `record(value)` recursively converts Fractions, matrices and tuples to canonical primitive records, reusing the B2 serialization convention.

## Fixed registry and `analyze_model`

The trusted models are:

| ID | Graph | Declared source domain |
|---|---|---|
| `two_layer_relu_v1` | bank `first` 2x2 ReLU, bank `second` 2x2 identity | Every canonical raw input with coordinate magnitudes <=1; old/new input identical |
| `shared_relu_v1` | bank `shared` 2x2 ReLU then the same bank identity, at two distinct call IDs | Same complete two-dimensional input box |
| `contractive_scalar_v1` | state/input concatenation `(s,u)` into one 1x2 identity bank; default row `(1/2,1/8)` | All old/new initial scalar states of magnitude <=1 satisfying the stated initial difference bound; every shared finite raw input history with |u|<=1 |
| `neutral_scalar_v1` | Same graph, default row `(1,0)` | Same declared initial/input relation |
| `amplifying_scalar_v1` | Same graph, default row `(2,0)` | Same declared initial/input relation |

All defaults have zero bias. Feedforward defaults are first=I2 and second=(1/2)I2; the shared default is (1/2)I2. Endpoints supplied for analysis may differ, but shapes, graph, domain and output/state interfaces are fixed.

`analyze_model(model_id,fmt,old_banks,new_banks,horizon=1,initial_error=0,method="tube",state_box=None) -> dict`:

- Feedforward models require horizon=1, initial_error=0, method=`tube` and no state_box. They quantify all identical declared raw inputs and observe all final output coordinates.
- Recurrent models support horizons 0..64 in this reference. Their declared initial relation is **all admitted old/new state pairs** inside their respective magnitude-one initial boxes with infinity distance <=initial_error; initial_error=0 means the same initial state. At each time both runs use the same legal u. The first affine Lipschitz calculation uses only the state column; the input column is excluded from the distance term but remains in all range/forcing calculations.
- Method `tube` builds both state enclosures and the error bound jointly for every time. An optional state_box is a claimed common cap that is checked against each initial and propagated enclosure; exceeding it refuses, rather than truncating the tube.
- Method `invariant` uses a caller-declared nonnegative rational common state box (default radius two), proves it includes the initial domains and proves both endpoint state images stay inside it for every legal input. It then propagates the constant certified map/error pair. A contraction uniform-in-time bound is returned only with this common-invariant proof; neutral/amplifying finite bounds are not relabeled as convergence.
- Recurrent observation is the full state at **all times 0..T**. Return keys include `error_bounds`, `final_error_bound`, `observed_bound=max(error_bounds)`, `old_state_tube`, `new_state_tube`, `steps`, initial relation, complete input-history domain, and (when proved) the common-invariant and uniform-in-time certificates. These are conditional quantified envelopes, not empirical reachability estimates.

`trace_model(model_id,fmt,banks,initial_state_words=(),input_sequence=())` is a point reference. For feedforward it takes a one-element sequence of complete raw input vectors; for recurrence each sequence member is a one-word external input vector and the initial state is one raw word. It checks the registered source/input domain, executes the fixed graph, and returns all state/output words and call traces. It does not truncate a propagated state to an initial box, silently halt at a domain exit, or manufacture an invariant from sampled traces.

## Trusted boundary

The initial relation and input domain are explicit preconditions of the universal analysis; an arbitrary actual initial pair must satisfy them before using its conclusion. Both old and new intermediate domains are propagated/proved. The matrix endpoints include every upstream generation/storage effect exactly once. The generic helper's custom graph/domain arguments require external provenance; registered `analyze_model` supplies the fixed domain/graph descriptors for the bounded receipt owner.

Version, optional identity context and numerical budget are bound by the separate receipt module. No receipt publishes state or authorizes a weakened deterministic contract. General concurrent changes, endpoint evolution during a trajectory, arbitrary nonlinearities/optimizations and B4 training are outside this fixed-endpoint B3 interface.
