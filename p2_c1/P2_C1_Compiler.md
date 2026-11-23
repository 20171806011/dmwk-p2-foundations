# P2-C1 compiler and execution specification

The implementation is a bounded, capacity-aware reference compiler for the closed Boolean FSM language in [Definitions](P2_C1_Definitions.md) and [Compiler Interface](C1_Compiler_Interface.md). It is justified by the handwritten [Theorems](P2_C1_Theorems.md), not by a claim that an arbitrary input graph can be certified through superficial structure checks. The mathematical checkpoint and theorem version were saved before compiler implementation.

## Accepted source and meaning

The source dictionary fixes named state/input/output ports, a nonempty initial-state subset, one next-state expression per state coordinate and one expression per output coordinate. State and input values are Boolean. There are one or two state coordinates, zero to two input coordinates and one or two output coordinates. All possible Boolean input tuples are legal; every Boolean state is included in the invariant/step domain. An initial state must additionally belong to the explicit allowed subset when an owner is constructed.

Constants, state references and input references are leaves. NOT, AND, OR, XOR and MUX are the only operators. All syntax is typed through exact built-in lists, strings and integers. Unknown fields, extra effects, host floating values, unrecognized operators, cyclic/deep expressions, mismatched declarations and duplicate port labels are rejected. A complete source has at most 256 expression occurrences and maximum depth eight. The exact concrete schema is in the interface file and is part of the compiler contract.

Every output and next-state expression reads one old snapshot. Outputs report the old-snapshot expression values; the full next state is committed simultaneously by the owner. There is no implicit reset, halt, threshold or control-flow side effect. A user can express reset/hold/conditional Boolean transitions explicitly with MUX and references. Eager MUX lowering evaluates both Boolean arms safely; it is not an uncertified hard floating branch.

## Complete graph construction

The emitter traverses next-state expressions in declared port order, then outputs in declared port order. Within a syntax occurrence it visits children left to right, creates their wires once, and emits the fixed macro. It performs no CSE, folding, fusion, reassociation, dead-site elimination, hidden state update or graph reordering. Two equal syntax occurrences remain distinct unless the source represents the shared result by an existing allowed source reference; the language has no generic temporary declaration.

Primitive AND and NOT calls receive fresh stable ordered identifiers. OR requires four primitive calls; XOR and MUX each require seven after their child expressions have been lowered once. The graph stores every primitive call, argument wire, selected row, source path, physical bank identity, active row/column view and activation/bias convention. Its final wire lists identify all state and output ports. The graph also records every legal A input as a labelled call (`a_zero`, `a_basis_j`), and the interface allows repeated invocations only through those declared inputs.

`check_artifact` regenerates the entire expected artifact from the externally expected source, budget, format and initial A-anchor request, then compares canonical serialized values. A missing call, extra call, modified wire, mixed source port, changed activation/bias or rehashed metadata inconsistency therefore fails reconstruction. A coherent different source is another program, not the expected one. Standalone execution helpers additionally reconstruct the embedded source/artifact for consistency, but the live owner must still bind its externally expected source and retain a detached verified artifact.

## Physical layout and arithmetic

With p A-output rows and q A-input columns, p,q in {1,2}, the single physical bank has shape `(2+p,3+q)`:

```
              D input coordinates       A input coordinates
 D rows       [ 1  1 -1 ]                fixed zeros
              [-1  0  1 ]
 A rows       fixed zeros                editable p-by-q A block
```

Fixed bias is an explicit zero vector. The third D input is the constant coordinate for the D affine lift; an A call instead prepares the first three coordinates as zero. These preparations are typed call contracts, not an assertion that all calls use one universal homogeneous coordinate value.

A D primitive prepares `(a,b,1,0_q)`. NOT sets b=0. Both D rows execute columns 0,1,2 in ascending order, with separate correctly rounded multiply/add from canonical zero; then coordinate ReLU runs and the operation selects its declared row. A rows are never evaluated at a D call. This matters for isolation and totality: zero cross blocks alone would not establish that unmodeled A arithmetic, state or effects cannot influence D.

An A call prepares `(0,0,0,z)` and executes only the A rows/columns, with identity activation. The legal z are zero and each positive coordinate basis vector. Each output is therefore zero or one stored coefficient exactly: finite products are only coefficient-times-zero/one, and at most one nonzero term enters a row. This provides totality on the complete declared A domain even for maximal finite or subnormal coefficients. Arbitrary dense A inputs, arbitrary activations and nonlinear A-to-D feedback are not included.

Stored words are canonical finite BF16/FP32 only. Negative zero, infinity, NaN, wrong-width integers, Python booleans and host floats are rejected as words. Arithmetic uses nearest-even rounding, gradual underflow and canonicalized zero. BF16 operations are software; FP32 operations use the inherited NumPy CPU scalar route with explicit dtype and an exact-RNE word audit on every multiply/add. D ReLU is an exact word selection using the decoded sign. No GPU, fused GEMM/FMA, BLAS reduction, altered accumulator precision or arbitrary compiler optimization is certified.

## Global coverage and initial states

The proof first establishes that every source/compiled selected wire is Boolean, then applies tick induction under synchronized old-state reads and bit-preserving state storage. Thus every D activation at every legal time lies in `{(a,b,1,0_q): a,b are bits}`. The fixed containing space is the first three physical coordinate axes and has rank three.

The compiler additionally enumerates every Boolean state/input pair and every generated primitive site in its closed graph. It records each site's complete activation set, their union and the exact rational span rank. This is a complete finite step-envelope analysis, not a sampled rank estimate. It may include unreachable states when the initial subset is smaller. Accordingly the artifact sets `exact_reachable_span_claimed=false`.

A source with no primitive gates has generated-call span rank zero. Its deliberately conservative physical reservation still uses the three D coordinates and rank-three containing space; the artifact keeps those two quantities separate. Authorization never depends on an unexpectedly low diagnostic rank. A new source, layout, port convention or graph receives a new compiler artifact and its own coverage evidence.

## Budgets, capacity and initial A anchors

The compiler accepts a budget only if its fixed D two-row/three-column primitive design fits, the complete emitted call count fits the requested per-tick call budget, physical matrix storage fits the word budget, and the requested A-response dimension and attainable single-update rank fit the reserved block. `required_update_rank` is a requested minimum achievable capacity, not a live rank cap. Failure is refusal by this construction; it does not prove that every possible compiler must fail.

The capacity receipt distinguishes:

| Object | Formula under the declared layout |
|---|---|
| Structural exact update-space dimension | p*q |
| Maximum rank of one unrestricted structural update | min(p,q) |
| Full-output annihilator of the rank-three containing space | (2+p)*q |
| External linear condition preserving only the first two preactivation rows | (2+p)*(3+q)-6 |
| Full-basis exact A-response dimension | p*q |
| Canonical structural stored endpoints and full-basis response signatures | N_F raised to p*q |

The fourth line is an external algebraic family, not the structural authorization family, a post-ReLU equivalence dimension or the complete BIT class. A rank-capped family is not assigned the unrestricted vector-space dimension. Canonical word counts are N_BF16=65279 and N_FP32=4278190079; the large powers are mathematical cardinalities, not exhaustively tested counts. All canonical structural endpoints are D-bitwise equivalent under this layout, but the entire observational BIT equivalence class could contain other endpoints excluded by the conservative mask.

Optional initial A anchors are allowed only at zero/basis inputs and use canonical exact rational output pairs. Zero input must map to zero; repeated input anchors must agree. These are the target-relation consistency conditions on this restricted input family. Missing basis columns initialize to zero. The resulting exact A matrix must be exactly storable, and its actual fixed-graph outputs are checked. Exact 1/3 anchors are refused, rather than silently relabeling a rounded value as the requested exact target.

These anchors specify initial A values only. Future learning is allowed to change them; they are not newly protected historical tasks. General mixed-input response feasibility and geometric projections remain separate read-only algebraic analysis. No rotation or general geometric mode is accepted by `compile_program` as BIT authorization. The structural mask itself is an exact coordinate projection onto the permitted block.

## Cost and what is encoded

For N source expression occurrences and G generated primitive sites, lowering is O(N+G), with G at most 7N as a loose bound. Complete finite step-envelope enumeration costs O(2^(s+u) G), where s and u are source state/input bit counts. This reference bounds s,u by two; it does not promise efficient exhaustive analysis for unrestricted state machines. Each site has at most four legal bit-pair activations, so the diagnostic union contains at most four physical vectors. Exact rank computation uses rational arithmetic and separately incurs its bit-operation costs.

The physical matrix stores `(2+p)*(3+q)` words, including fixed zeros; the bias metadata stores `2+p` zero words. Exactly five D coefficients are nonzero; the A block can contribute at most p*q nonzeros. The D view uses 12 floating binary operations and two ReLU word operations per primitive call. The A view uses 2pq binary operations per invocation. No claim that a dense matrix kernel executes only these sparse operations is made: the reference graph specifies these views explicitly.

The source and graph are not compressed into that constant-size gate bank. Graph instructions/wires/site identities grow with G. The receipt reports source and graph JSON bytes, G selected-result wire slots, G diagnostic trace records, source input/output slots and separate current/next state buffers. The detailed Python trace records, source artifacts, optimizer state and version/history ledgers incur additional host memory; the simple matrix-word budget is not a total-runtime-memory budget. No compiler/hardware performance advantage follows from these accounting formulas.

## Verification and publication interface

The pure implementation is [c1_compiler.py](c1_compiler.py) with explicit read-only dependencies in [c1_runtime.py](c1_runtime.py). Sources and artifact reconstruction are cached only by canonical immutable strings plus current implementation fingerprints; returned artifacts are detached JSON values. The cache does not turn a mutable caller object into trusted state.

`quantize_endpoint` forms an actual stored endpoint from an exact proposed increment and can reject overflow. It deliberately does not silently mask forbidden changes. Subsequent `validate_endpoint` must check every canonical word and every fixed D/cross cell. The live owner additionally binds the full source/artifact, initial-state relation, graph/policy, endpoints/version, D state, optimizer, counters, schedule and ledger, and stages changes before one serial publication. A numerical or geometric diagnostic has no update authority.

Scientific test counts and timings belong to actual main/independent result JSON and the Evidence Map. The compiler's small smoke checks are not substituted for those independent suites. General handwritten proofs, complete named finite programs, seeded tests and native/software execution observations remain separate evidence kinds. C2, coordinate migration, general finite-precision kernels, general concurrency, crash consistency, hostile memory and full-host machine proof remain outside C1.
