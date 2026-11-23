# P2-A1 adversarial review

Status: completed for the stated P2-A1 scope. No remaining blocking inconsistency was found after the corrections below. This is a source/proof review plus finite checks, not a proof-assistant certification or a guarantee that every defect has been excluded.

## Review scope

The review covers the English definitions and handwritten proofs, exact-rational rank implementation, finite reachability, activation collection, conservative affine invariants, compiler observation adapter, counterexamples, and evidence interpretation. It does not reopen P1 verification or implement weight updates, P2-A2, a GPU backend, or a proof-assistant formalization. Only the necessary existing A4 execution interface was read; no P1 suite was rerun or modified.

## Concrete findings and resolutions

| Finding | Resolution | Evidence |
|---|---|---|
| Inferring matrix identities only from observed events omitted a declared but never-called matrix, rather than reporting its zero span. | The reachability model accepts an explicit matrix-dimension and call-site registry. Uncalled entries are retained at rank zero; undeclared observed entries and inconsistent dimensions are refused. Without a registry, the output explicitly says it covers observed matrices only. | `Reachability.spaces`, `enumerate_reachable`; main verifier's uncalled-matrix/site case; independent review check. |
| A guard-relaxation example had two translation generators but described a guarded hold transition, which was not in that family. | The identity generator was added. The guarded model is explicitly exhausted: two states and two edges, translation at the first state and identity at the second. Its exact homogeneous span has rank 2, while the three-generator relaxation has rank 3. | `invariant_examples`; recorded `guard_relaxation` result. |
| A rational-size statistic measured stored coefficients, not every transient multiplication intermediate. | Its result key now says `peak_stored_numerator_or_denominator_bits`; no total bit-operation count or peak transient allocation is claimed. | `Basis.summary` and result records. |
| The general partial-FP definition initially risked interpreting input enablement as sufficient for a successful transition. | `input_ok` denotes input/monitor permission; effective `en` additionally requires successful numerical acceptance by a terminating evaluator. Delta is restricted to `en`. Failed/aborted transitions are outside successful-transition call logs unless explicitly modeled. | Definitions section 3.2; A1.5 assumptions and proof. |
| An empty call-site family makes an unqualified maximum-dimension expression undefined. | The nonnegative dimension bound explicitly uses empty maximum zero and empty sum space `{0}`. | Theorem A1.2. |

The following were checked as necessary scope obligations, not all defects in an earlier implementation:

- Finite D storage does not make an arbitrary history-dependent input policy finite-state. Exact BFS requires a complete finite Markov configuration, finite effective transition/input enumeration, and decidable admission. The separate unbounded-history halting reduction does not apply to a supplied finite monitor.
- A sampled rank plateau is not a stopping certificate. Full ambient rank witnessed by legal samples is sufficient for full rank; deficient samples remain only lower bounds.
- Images of a basis establish closure only for a genuinely linear algebra map. ReLU and rounding do not inherit this argument. The affine-family theorem names every generator and requires a refinement or error-space enclosure of actual operations.
- Numeric spans over Q/R do not make finite FP words closed under arbitrary linear combinations, and numeric decoding can lose signed-zero distinctions.
- Physically shared matrices use one input-coordinate frame. Equal row values do not establish storage sharing. Actual A4 rows are reported independently; the separate interned-row adapter explicitly declares its new sharing presentation.
- A4 executes every node on each admitted tick, including source-inactive alternatives. The trace adapter follows that schedule and is compared bitwise against the unchanged original tick on every explored edge.
- Operand-only and homogeneous affine coordinates are reported separately. A bias-first floating execution is not silently reordered by writing a mathematical final coordinate of one.
- A nontrivial algebraic complement does not establish an admissible sparse/bounded/finite-format change or bitwise safety. The four-term zero-dot counterexample is explicitly not a protected-D patch.
- The fixed direct-matrix-use reference does not automatically cover transposed parameter tying, dynamic shapes, or changing matrix identity; those require an expanded declared interface.

## Independent finite checks actually executed

Run:

```bash
python -B /workspace/p2_a1/verify_review_checks.py
```

The actual output is [review_checks.json](review_checks.json). Its source hashes bind it to the reviewed rank library and the independent review script. The checks passed:

- All 512 binary 3-by-3 matrices: exact RREF rank versus a separately implemented determinant/minor rank oracle, input-generator containment, and reversed row-order invariance.
- Four additional empty, zero, fractional, and tiny-nonzero rational cases. The tiny rational direction is still exact rank, with no SVD tolerance.
- Four negative argument/universe-closure cases.
- One ReLU basis-only closure counterexample: both basis vectors are fixed, but another vector in their span leaves the space after ReLU.
- One explicit uncalled matrix/site check, both recorded with rank zero.

These are finite algorithm checks. They do not machine-prove rank correctness for all rational matrices, model faithfulness for arbitrary callbacks, or any floating backend.

## Main recorded verification inspected

The final main record reviewed here is `verification_results.json`, status `passed`, with 2,533 verifier checks. That number is an assertion count, not a count of distinct programs or mathematical theorems. The final verifier includes the three added checks for the stronger ReLU basis-only closure counterexample; their source and result hashes were inspected after the earlier review. The main script records 80 seeded rational-matrix samples, finite declared activation domains and finite state models, and no SMT query.

The two actual compiler fixtures are each checked under software BF16 and local scalar CPU FP32: the two-bit counter-to-two has six reachable states, six edges, and 45 executed nodes per edge; the input-driven two-register fixture has four reachable states, eight edges, and 13 nodes per edge. Their source state spaces, allowed initial states, input alphabets, row identities, common-coordinate sharing adapter, and bit-level comparisons are explicit in the results. Exhausting each declared reachable graph supports that instance's all-time span through the separately stated finite-state argument; it does not verify every possible compiled program.

The finite affine FP bridge additionally exhausts the two reachable Boolean states and six hold/toggle/reset edges per format. Each actual decoded edge agrees with one declared affine generator, the raw input span has rank 1 in dimension 2, and the homogeneous reachable span equals the computed invariant hull at rank 2 in dimension 3. The unbounded translation example is separately labeled rational algebra only.

The arithmetic counterexample uses unit activations and coefficients `(2^p, 1, -2^p, -1)`: its exact dot product is zero and the specified ordered RNE result is `-1`, for software BF16 (`p=8`) and actual scalar CPU FP32 (`p=24`). This disproves the algebra-to-bitwise inference; it does not authorize those coefficients in the protected compiler.

## Remaining boundaries

The handwritten results and the source implementation are not fully checked in Lean or Coq. No P2-A1 SMT query, GPU execution, native BF16 execution, BLAS reduction proof, concurrency proof, or general nonlinear abstract interpreter is supplied. A custom legal-input monitor or call observer still needs its own semantic justification. Exact enumeration can be exponential, and a conservative invariant can become full-dimensional. The recorded rank and counterexamples do not establish a safe weight-update method or implement any subsequent P2 stage.
