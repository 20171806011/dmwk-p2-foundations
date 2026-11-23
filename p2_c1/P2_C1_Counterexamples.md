# P2-C1 counterexamples and refusal boundaries

The compiled source language admits Boolean D inputs and zero or coordinate-vector A inputs. The examples below identify which restrictions an extension would have to reestablish. The final section records the measured outputs and refusal counts.

## 1. A zero cross block alone does not isolate a program

Let the physical bank be diag(1,a). If a nominal D observation reads the second output, or its prepared first input depends on that output, changing a can change D despite both cross blocks remaining zero. The same issue arises if the activation mixes coordinates, the bias contains an A-dependent value, or the state update aliases a learnable register. Thus the complete source-to-graph/input/state/effect correspondence is part of the structural theorem. The compiler must reconstruct every site and state/observation map; checking only displayed zero entries cannot establish isolation.

The concrete C1 layout instead fixes the D gate block, both cross blocks, zero biases, sparse D input columns, coordinatewise ReLU, and D-owned state. A calls use a separate identity-activation interface. A missing or mixed site is rejected by comparison with the complete reconstruction from the expected source.

## 2. A proved smaller activation span still does not make ALG imply BIT

Consider a source whose only primitive is `AND(1,1)`. Its complete D-call activation set is the singleton h=(1,1,1), embedded with zero A coordinates; its exact span has rank one. The original AND row is (1,1,-1), whose exact and prescribed rounded outputs are 1.

Let p be the format precision (8 for BF16, 24 for FP32), and F=2^p. Replace this row by (F,1,-F). Both rows and all entries are storable. Their exact actions on h are equal:

    F + 1 - F = 1,      ((F,1,-F)-(1,1,-1)) h = 0.

Under ascending-column, separate nearest-even addition, however, F+1 is exactly halfway between F and F+2 and rounds to F. Subtracting F then gives zero. ReLU preserves zero. Thus even this genuinely complete, non-sampled, rank-one activation proof does not upgrade exact annihilation to bitwise execution equality.

The structural endpoint rule rejects the changed fixed row. The conservative V_* also rejects it algebraically; the counterexample concerns an attempted geometric relaxation using the valid tighter span. It is not an accepted C1 patch.

## 3. BIT can hold while ALG and the selected contract reject

Let eta be the smallest positive subnormal. Change the D NOT row from (-1,0,1) to (-1,eta,1). On every Boolean pair (a,b), prescribed separate arithmetic still returns 1-a: eta is swallowed when added to -1 or +1, and arithmetic zero is canonicalized. But the exact difference is eta times the second coordinate and is nonzero on the rank-three containing space V_*. Hence full Boolean gate-table equality does not imply exact annihilation.

This candidate is rejected because it changes a fixed D cell under the selected structural ALG_AND_BIT policy. Such a rejection is not observed D drift. It is consistent with the earlier B1 evidence of BIT-equal but ALG-failing candidates.

## 4. Ideal projection can be invalidated by endpoint storage

Take a row W=(2^p,0), protected vector v=(1,1), and ideal increment G=(1,-1). Exact Gv=0. Nearest-even endpoint storage rounds 2^p+1 back to 2^p, leaving actual difference (0,-1), whose action on v is -1. An ideal projected candidate is not the actual increment. This is a read-only geometric diagnostic; the C1 structural path verifies stored endpoints and does not accept this generic two-coordinate projection as authorization.

## 5. A floating test on basis vectors is not a full-space certificate

Let s be the stored rounded value of one third, and use row (2s,-s,-s). The row annihilates span(1,1,1) in exact rational decoding. Its prescribed finite execution at (1,1,1) is zero. At (eta,eta,eta), the leading product rounds to eta while the two negative products underflow to canonical zero, so the result is eta. Testing only a spanning vector in floating arithmetic does not establish execution invariance on its real span.

These subnormal activations are outside the compiled Boolean D domain and outside the declared A domain {0,e_j}. The example explains why unsupported geometric extensions and input-domain changes require a new proof rather than inherited labels.

## 6. Orthogonal rotations do not commute with coordinate ReLU

Let R=[[0,-1],[1,0]] and x=(1,-1). R is orthogonal, yet ReLU(Rx)=(1,1), whereas R ReLU(x)=(0,1). Thus a geometric coordinate change cannot be inserted around a coordinatewise nonlinearity merely because it preserves Euclidean norms. C1 admits no such compiler rewrite. Permutation-specific or other restricted symmetries require their own graph and numerical proof.

## 7. Arbitrarily small branch changes and illegal selectors

A hard guard `x>0` differs at x=0 and x=eta. No absolute perturbation statement alone preserves a threshold at its boundary. The source MUX is a Boolean constructor lowered eagerly to exact gates; it does not admit a continuous selector, an arbitrary threshold node or an unmodeled effectful branch. Invalid input words and unsupported branch opcodes are refused rather than treated as approximate Boolean values.

## 8. Source completeness, synchronization and certificate identity

Omitting a generated gate can leave every listed local gate well formed while changing the program. Likewise sequentially publishing one next-state component can cause a later expression to read the new value rather than the specified old snapshot. The compiler only certifies the canonical graph reconstructed from every source next-state and output expression; the runtime snapshots all old state before evaluating and commits all next state together.

Changing expected source, port labels, allowed initial states, parameter IDs, shared sites, weights, policy, activation, graph order or layout changes the proposition being certified. Merely recomputing an unkeyed digest cannot restore equality with the current expected artifact or live snapshot. Digests establish consistency in the trusted API, not historical intent authentication.

## 9. Capacity failures are not one phenomenon

- An insufficient row/column/cell/call budget rejects this construction; it is not a proof that no other compiler could work.
- A full-output annihilator has dimension n(d-r), whereas the chosen editable A mask has its own smaller dimension. Counting the former as writable structural capacity is wrong.
- A requested response whose target columns obey an incompatible linear relation cannot be implemented even with nonzero free parameters.
- An exactly feasible response may require non-storable coefficients and therefore fail endpoint realization.
- Storage saturation may reject an overflowing proposal while other representable updates remain available.
- An accepted quantized no-op can advance version/optimizer counters without changing A's function; it does not consume one algebraic degree.
- Per-step rank one does not imply cumulative rank one; extra fixed protected directions must be analyzed separately from update count.

## Observed compiler results

The compiler suite ran the two formats separately with seed `20261114`. Its recorder counted 1,400 accepted compilation requests and 69 rejected compilation requests. The 176 intentional refusals across all APIs include those 69 compile-time refusals. For each format the checker refused 23 rehashed artifact mutations, including omitted D/A sites, mixed rows, changed bias/activation, undeclared feedback, altered state wiring, invented capacity and an invalid domain. The endpoint validator also refused mutations to each of 16 fixed cells in the tested 4-by-5 layout. [Compiler results](compiler_results.json)

| Diagnostic | Software BF16 | Local CPU FP32 audited against RNE |
|---|---:|---:|
| Constant AND protected row before/after the exact-span-preserving edit, raw words | 16256 → 0 | 1065353216 → 0 |
| NOT-row subnormal edit on the complete four-entry Boolean table | 4/4 outputs equal | 4/4 outputs equal |
| Ideal null-action proposal `(1,-1)` at `(2^p,0)`, actual increment | `(0,-1)` | `(0,-1)` |
| Rounded-thirds row output at `(1,1,1)` and the triple of smallest subnormals, raw words | 0 and 1 | 0 and 1 |
| Separate multiply/add and exact one-round reference, raw words | 0 and 47232 | 0 and 2826960896 |
| Strict guard at canonical zero and its positive successor | false, true | false, true |

Raw word `1` in the thirds example encodes the smallest positive subnormal. The one-round reference was obtained by exact rational evaluation followed by rounding. The source compiler supports separate multiply/add. The rotation example computes `R R^T`, `ReLU(Rx)` and `R ReLU(x)` in integer arithmetic. Their values are the identity matrix, `(1,1)` and `(0,1)` respectively. The synchronous two-register witness produced next bits `(1,1)` and old-snapshot observations `(0,1)`. A sequential overwrite would yield `(1,0)` as the next state. [Verifier](verify_compiler.py)

The complete named grammar families comprised 576 ordered pairs of next/output expressions over 24 atomic, NOT and AND terms, plus 96 OR/XOR/MUX programs. Across both formats the verifier examined 5,376 state/input contexts and executed 10,752 D transitions at two endpoints per context. Saturating each writable A cell preserved all D traces in these tests. The separate seeded cases used 12 two-state/two-input programs in both formats, with 384 additional complete state/input contexts and 384 feedback ticks. Across the four supported block shapes the verifier enumerated 204 endpoints over the palette `{−1,0,1}` and checked 588 A responses and 816 D contexts. The proofs quantify over the declared legal domains under their graph and execution contracts. [Verification record](compiler_results.json) [Theorems](P2_C1_Theorems.md)
