# P2-C1 — Capacity-aware compilation for a protected and learnable weight program

## Main result and its scope

This stage constructs a bounded source-to-graph-and-shared-bank compiler with an explicit learnable reserve. The source is a finite synchronous Boolean state machine. Its complete deterministic graph uses a fixed shared AND/NOT block, while an independently addressed A block admits nonzero updates. Isolation is proved for the full interface: source reconstruction, every call, input preparation, activation, bias, state, observations and schedule. A matrix with zero cross blocks alone would not establish that result.

The general proofs are conditional handwritten proofs. The prototype accepts a closed source language and a fixed numerical policy; it does not discover every effect of arbitrary external code. It does not encode an arbitrary program solely into a constant-sized matrix: graph/wire metadata and repeated work carry the source program. No C2, C3 or C4 result is claimed.

## Dependency preservation and research order

The saved [Plan](P2_C1_Plan.md), [mathematical checkpoint](P2_C1_Mathematical_Checkpoint.md) and full theorem draft preceded compiler/owner implementation. The checkpoint and T1–T9 received independent mathematical review. The initial [dependency receipt](dependency_inspection.json) verified B4's manifest, actual results/completion and bindings without running its scientific suites. A new baseline protects 782 prior artifacts and the nonexcluded inventory, including the existing publication directory. Earlier P1 compiler and P2 activation, endpoint, capacity, optimizer and error contracts remain read-only dependencies.

The relevant preexisting failure evidence is preserved: B1's 21 rejected candidates passed its finite-domain BIT test but failed ALG under the joint policy; these are not 21 observed D drifts. Its dense FP32 AdamW run accepted zero of eight attempts and retained loss 5/2. A different successful structural C1 toy would not overturn those results.

## Compiled representation

The bounded front end permits Boolean constants, state/input references, NOT/AND/OR/XOR/MUX, one or two state bits, zero to two inputs, one or two outputs and an explicit nonempty initial-state set. Next-state and output expressions all read the same old snapshot; outputs are pre-transition observations. Reset, hold or halt-like behavior can be written explicitly with Boolean expressions. Hard floating guards, external effects, implicit control-flow transformations and arbitrary user graphs are unsupported.

Canonical eager lowering uses only AND/NOT, with fresh ordered sites and no folding or common-subexpression elimination. OR, XOR and MUX require four, seven and seven primitive calls after evaluating their child expressions once. The complete graph is reconstructed from the expected source when its certificate is checked.

For A dimensions m by c, the physical shared matrix is

```
W = [[B, 0], [0, A]],    B = [[1, 1, -1], [-1, 0, 1]].
```

Each D call prepares `(a,b,1,0_A)`, computes both B rows in the fixed separate multiply/add order and applies coordinate ReLU. The selected results are AND and NOT. Each A call prepares `(0,0,0,z)`, computes only A rows/columns and uses identity activation. Biases and cross connections are fixed zero, and A cannot feed D state or inputs through an undeclared interface.

The A domain is exactly zero and the positive coordinate basis. This deliberate restriction makes every canonical finite A endpoint total: each row has at most one nonzero product, so its response is zero or an exact stored column. It includes subnormals and the largest finite word. An arbitrary dense A input would need another range/overflow proof.

## Proved obligations and capacity

The [Theorems](P2_C1_Theorems.md) prove macro/source correspondence, exact Boolean gate closure, every-finite-tick simulation, global activation containment, capacity/cardinality, initial-anchor feasibility, structural endpoint safety, complete reconstruction and serial rejection/publication.

All deterministic calls lie in the globally proved containing space `V*=K^3 x {0_A}` over Q or R. A complete enumeration over all Boolean state/input pairs and all generated calls also computes a tighter envelope. For a no-gate source its actual generated-call rank is zero, while the compiler still deliberately reserves three coordinates. The envelope need not equal the reachable span from a restricted initial set, and neither is inferred from samples.

| Object | Established quantity or condition | What it does not mean |
|---|---|---|
| Structural algebraic update space | Dimension mc | Not unrestricted geometric capacity or useful learning performance |
| Individual structural update | Rank at most min(m,c); generator cap adds its own bound | Not a bound on a sum of many low-rank updates |
| Full-output annihilator of V* | Dimension (2+m)c | Includes extra cells deliberately frozen by the structural compiler |
| Supported projection | S(G)=R_A G P_A, the exact Frobenius projection onto the editable block | Arbitrary rotated/approximate projectors are not BIT-authorized |
| Finite structural endpoints | Exactly N_F^(mc), with N_BF16=65279 and N_FP32=4278190079 | A finite counting proof, not a real-vector-space dimension or full enumeration |
| Legal A basis responses | Injective endpoint signature; response dimension mc in exact algebra | An optimizer need not reach or improve all those responses |
| Target subset Z | Response dimension m rank Z; R feasible iff ker Z is contained in ker R | Nonzero safe changes can be silent on the selected targets |

The broader compatibility condition remains `X alpha in V => R alpha=0`; a structural mask can impose additional restrictions. Optional compile-time A anchors assign exact rational responses at legal zero/basis inputs. Conflicting duplicate anchors, nonzero response on zero, or nonrepresentable exact coefficients such as 1/3 are rejected. These are initial A assignments, not tasks protected against subsequent learning.

The construction needs two D rows, three D columns, `(2+m)(3+c)` dense matrix words and twelve floating binary operations per primitive D site. A calls require `2mc` such operations. There are five structurally nonzero D coefficients. State buffers, biases/constants, source/graph metadata, temporaries, traces and staged transaction copies add separate costs. Resource insufficiency for this layout is not an impossibility proof for all compilers or encodings.

## Numerical and geometric boundaries

Stored endpoints use canonical finite words; negative zero and nonfinite words are rejected. Arithmetic uses nearest-even rounding, gradual underflow, canonical zeros, fixed separate multiply/add and declared row activations. Only software BF16 and the audited local CPU FP32 route are exercised.

A constant `AND(1,1)` source has a globally one-dimensional generated-call span. Replacing row `(1,1,-1)` by `(2^p,1,-2^p)` preserves exact dot products on that entire span but changes its rounded result from one to zero. This shows that even a genuinely proved low-rank activation span does not make algebraic geometry a bitwise certificate. Conversely a smallest-subnormal edit to the NOT row's b coefficient preserves its finite Boolean outputs but violates the selected ALG condition and structural mask. Both are refused by this compiler's live route.

An arbitrary rotation also fails to commute with coordinate ReLU. General geometric or numerical comparisons remain read-only or unsupported; they do not waive the source-bound structural ALG_AND_BIT gate. Actual endpoint differences already include optimizer and quantization effects. Any numerical comparison of two executions must still account for both executions' rounding; this stage does not reuse old-layout B3/B4 coefficients as new certificates.

## Publication contract

The new owner binds the complete expected source, artifact/graph/layout, all calls, domain/initial relation, precision policy, endpoints and versions, D state/ticks, optimizer, counters, task and ledgers. Proposals are formed before checking. The final structural mask is applied after the supported optimizer operations, then the actual stored endpoint is checked. Direct proposed endpoints must independently satisfy the same restrictions.

All checking and ledger construction occurs on unexposed staged data. Only after recomputation succeeds does one serial publication expose the complete replacement. A refusal leaves the whole owner unchanged. A successful A update preserves the designated D trace while legitimately changing A weights, optimizer state and metadata. Numeric read-only receipts have no publication authority. This is trusted serial behavior, not concurrency, crash durability or hostile-memory protection.

## Actual validation

The primary compiler suite accepted 1,400 direct compile requests and refused 69. It also checked 1,368 successful artifact reconstructions. The two complete small program families have 576 and 96 sources. Compiling each in both formats gives 1,344 program/format cases and 5,376 Boolean state/input contexts. Executing the initial and a second stored A endpoint gives 10,752 D transitions. The seeded deeper cases and the finite A-block palette are recorded separately. [Compiler output](compiler_results.json)

For automatic sizing, the caller supplies matrix-word and call budgets together with minimum A response dimension and attainable rank. The driver tries all four supported A shapes in order of dense matrix cost and selects the first satisfying the compiler and exact anchor constraints. On the parity source with two response degrees and attainable rank one, an unanchored choice uses 15 matrix words (one A row, two A columns). Requiring a two-output response on one basis input uses 16 words (two A rows, one A column). The first 15-word choice cannot realize that observation signature. Across 104 budget and anchor cases, the independent cost table predicted all 28 feasible selections and all 76 refusals. The archived fixed-layout example returned previous parities 0,1,0,0 on input 1,1,0,1 and ended in state one. Its seven D sites use 84 multiply/add operations and 14 ReLUs per tick. [Layout search](P2_C1_Layout_Search.md) · [Layout results](layout_results.json) · [Executable example](example_run.json)

The geometric comparison evaluated two coupled edits on the same complete rank-one call span. On the sole activation (1,1,1), rows (2,0,-1) and (2^p,1,-2^p) both give one in exact algebra. The first edit preserved every observed D word. The second gave zero after rounding. Each comparison covered every state and input and both call sites. The live owner refused both proposals in both formats because each changes an immutable cell. This gives a concrete sufficient case for geometric preservation under the declared observations, alongside the counterexample to an unconditional BIT claim. [Geometric proof and scope](P2_C1_Geometric_Comparison.md) · [Measurements](geometric_results.json)

The compiled XOR feedback experiment learned a two-output A target (1,-1) from zero, using one legal coordinate input. Its results measure actual stored outputs under the fixed execution graph.

| Format | Accepted / nonzero stored updates | Final A response | Exact decoded loss (initial loss 1) |
|---|---:|---|---:|
| Software BF16 | 32 / 16 | ±127/128, positive first component | 1/16384 |
| Local CPU FP32 | 32 / 32 | ±16775531/16777216, positive first component | 2839225/281474976710656 |

Across these updates, the 64 paired feedback ticks, 256 full state/input comparisons and 1,792 shared-gate trace comparisons had zero D word differences. BF16 first stored a no-op on attempt 17. The structural space still had dimension two. The transaction verifier recorded 54 expected refusals, including altered histories and late rejection with nonzero momentum, and checked equality of the full owned snapshots. [Transaction results](transaction_results.json) · [Publication specification](P2_C1_Transaction_Spec.md)

The primary sections recorded 319,910 compiler checks, 104 layout checks, 28 geometric checks and 1,156 transaction checks. The independent verifier passed 212,851 assertions with 95 expected refusals. It checked 240 program/format pairs, 960 complete small-domain transitions, 5,152 site observations and 412 further transitions. Its own word-rounding, direct Boolean expression and optimizer oracles also checked 20 momentum updates. Timing, proof, enumeration, seeded and backend scopes are indexed in the evidence map. [Evidence map](P2_C1_Evidence_Map.md) · [Independent results](independent_results.json)

The aggregate passed 321,198 assertions with 310 expected refusals in 85.19 seconds. The 782 predecessor files and their inventory passed content checks before and after the run. A second run from `/tmp` on the same host took 84.93 seconds. The independent runs took 18.68 and 17.81 seconds. All six comparisons matched after wall-clock fields were removed: each primary verifier matched its own reproduction and each of four standalone producers matched its aggregate section. The compared data retained raw words, observations, budgets, counts, logical time and source identities. Optimized Python modes were refused before tests. [Reproduction records](reproduction_driver_results.json) · [Completion and limits](completion_status.json)

## Prior work and unresolved boundaries

The [original-source comparison](P2_C1_Related_Work.md) verifies OGD (*Orthogonal Gradient Descent for Continual Learning*, AISTATS 2020) and GPM (*Gradient Projection Memory for Continual Learning*, ICLR 2021). Their stored-gradient/locality or sampled/thresholded activation projection methods are not treated as proofs of this compiler's full legal-domain, stored-endpoint or serial publication obligations. Projection and orthogonality are not claimed as new, and no novelty or benchmark advantage is established by this two-paper check.

The general proofs are not machine-checked. Finite source-family tests, seeded cases and exact reference computations remain distinct from general source/compiler correctness. Unsupported cases include arbitrary external programs, dense arbitrary A domains, A-to-D feedback, arbitrary compiler optimization/FMA/reassociation, GPU/native BF16, general concurrency, crash consistency and universal learning benefit. General bidirectional composition, coordinate migration and general hardware certification remain future stages. The [C2 handoff](P2_C2_Handoff.md) supplies their starting constraints; C1 stops at this delivery.

The serial reference stores detailed tick/update ledgers and caps accepted candidate text at 16 MB. A long ledger can limit further commits even if the next endpoint is representable and the algebraic reserve is intact. This bounds practical availability of this implementation.
