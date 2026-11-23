# P2-A3 independent adversarial review

## Disposition and scope

The review found no remaining blocking inconsistency in the final conditional mathematical statements or the inspected reference interfaces. This is an independent source/proof review and finite implementation evidence, not machine verification of Python, NumPy, the compiler, or hardware.

The reviewer read the necessary A1/A2 definitions, mathematical scope, independent-review limits and A3 handoff without editing those files or running their stage suites. The A3 plan and mathematical checkpoint preceded implementation. The review examined the final A3 Definitions, Theorems, exact diagnostic, pointwise diagnostic and registered-domain certificate mechanism. No P2-A4 work or publication action was performed.

Actual independent checks are in [verify_review_checks.py](verify_review_checks.py), with output [review_results.json](review_results.json). The verifier does **not** import the production test modules or reuse their assertions. Its results bind the reviewed production modules and its own source by SHA-256. Hashes identify those files; they do not prove their correctness.

## Mathematical obligations

| Result | Review assessment | Boundary |
|---|---|---|
| T1: endpoint/basis/span equivalence | Exact subtraction of decoded endpoints and linear extension prove all equivalences. Empty domains, dependent generators, rational/real extension and full-output meaning are explicit. | A complete global generator is a separate premise; a numerical basis probe does not satisfy the theorem. Equality after a projection requires the projected condition. |
| T2: sharing, conservative generators, rank and affine cases | Shared calls require the union in common physical coordinates. A containing space gives a sufficient condition, not a necessary one. Joint bias changes use actual lifted activations. Rank/dimension statements concern exact linear maps. | The real annihilator dimension does not count storable or executable updates. A fixed bias may cancel from the difference, but editable bias cannot simply be ignored. |
| T3: pointwise finite arithmetic | Exact endpoint response plus the difference of execution errors equals the decoded output change. The local absolute rounding errors telescope and cover accepted subnormal results. | A posteriori bounds are per input; they do not authorize commits or establish uniform/all-time raw equality. |
| T4: program lifting | Instruction-level equality, totality, effects and identical operand preparation yield equal transitions; a common invariant and induction yield all-finite-prefix equality. Successive patch pairs compose transitively on the same fixed context envelope. | Same initial protected configuration, admitted inputs, graph, effects and trusted schedule are required. A direct weight read, hidden control dependency, or A-to-D input channel invalidates the premise. This is not complete general P2-C composition. |
| T5: finite certificate soundness | Complete enumeration of a trusted declared model establishes its local relation. Recomputed endpoint/domain/graph/version binding and serialized publication connect evidence to the actual bank. Failed validation has no publication. | Soundness is conditional on correct checker/model semantics. A digest or a caller-supplied invariant is not proof, authorization or arbitrary-code isolation. |

The concrete dense witness satisfies both exact algebraic and finite bitwise equality on duplicated Boolean activations, while all mutable matrix coefficients are actually evaluated. The A output changes from `(1,0)` to `(0,2)` at the declared input `e1`. This establishes an observable nonzero edit; it does not prove learning performance.

## Review-driven clarifications and adversarial findings

1. **Complete output versus selected observation.** The exact theorem now distinguishes full-vector equality from equality after a linear observation map. The implemented checker protects both output words of each site, although the state recurrence uses only the first coordinate.

2. **Affine lifting must precede basis compression.** Ordinary input-span generators can lose the affine relation. On actual scalar activations `{1,2}`, the edit `delta_weight=1, delta_bias=-1` does not preserve both outputs, although it preserves the selected ordinary basis activation `{1}`. The independent verifier checks this directly, along with empty and singleton domains.

3. **Exact and bitwise contracts are not nested.** The rounded-thirds case shows ALG can pass while BIT fails. The commit-rounding case instead has a null ideal proposal but a non-null actual endpoint difference: correctly defined ALG fails there, as does BIT. The reverse implication also fails: replacing the first row of `I2` by `(1,eta)`, where eta is the minimum positive subnormal, preserves all rounded outputs on `{0,(1,1),(1,0)}` while giving a nonzero exact endpoint residual. This legal set has full real rank. The independent checker accepted the registered duplicate and split models and refused the same edit in the axis model, where `e2` exposes the change. Full algebraic rank removes exact annihilators, not every finite-domain floating observational equivalence.

4. **Global coverage comes from the trusted model.** The certificate's descriptor cannot change its legal states, activations or site list. The checker regenerates the expected record from the registered model and tests every required call and state/input pair. Removing a site or activation, marking samples global, changing the invariant, or recomputing the packet and descriptor checksums does not bypass that logic.

5. **Equality of arbitrary endpoints is not sufficient for the state invariant.** For stateful models, the checker additionally requires each endpoint's full outputs to match the registered Boolean preparation. Equal all-zero endpoints therefore fail, even though they agree with each other. The live kernel starts at the verified identity bank and preserves this invariant through accepted updates.

6. **Version limits and host counters remain explicit.** The theorem quantifies accepted transactions. Version exhaustion is a refusal, not an unlimited successful-update promise. The Python tick counter is reference instrumentation rather than a certified fixed-width perpetual clock. A global-domain certificate may remain valid after a legal state tick if the weight version and endpoints are unchanged; that case was tested.

7. **Trusted serialized API, not an adversarial interpreter.** Public certificate inputs are exact built-in strings, parsed into fresh JSON primitives. Candidate matrices and words are validated before use. Caller-supplied string/tuple subclass callbacks were refused without invocation. The checker uses its own instrumentation; private memory/module mutation and concurrency remain excluded. Recomputed checksums are publicly forgeable, so semantic rechecking is essential.

8. **A positive bound can imply bit equality under an explicit separation premise.** The final T3 corollary is valid: finite decoded values in a fixed binary format lie on integer multiples of its minimum positive subnormal eta. A certified infinity-norm output-difference bound strictly less than eta excludes every nonzero decoded difference. With canonical finite encoding, decoding is injective and the raw words therefore agree. This is a mathematical sufficient condition, not an implemented automatic BOUND-to-BIT authorization path. A program-level result still requires complete context coverage and T4's invariant/interface premises. Without these additional conditions, a positive pointwise bound alone is not a global bitwise certificate.

These are clarifications, constructive limitations and successful adversarial rejection checks. The review did not discover an unresolved production defect or a prior-stage error requiring modification of old evidence. No defect-free universal implementation claim follows from that outcome.

## Independent methods and actual coverage

The reference oracles are different from the production checking approach:

- **Algebra:** determinant/minor rank tests and a greedy independent basis, followed by direct rational matrix-vector products. Production uses the A2 exact elimination/basis implementation. The verifier checks all **1,296** combinations of binary 2-by-2 generator matrices and ternary 2-by-2 endpoint differences, plus **576** combinations of binary 2-by-3 generators and ternary 1-by-2 differences. The 16 binary 2-by-2 generators have ranks 0/1/2 in counts 1/9/6. An additional **72** affine cases cover every subset of `{0,1,2}` and all ternary scalar weight/bias changes. These are finite domains, not arbitrary-rational machine proofs.
- **Rounding and quantitative reports:** an independent monotone-word binary search implements nearest-even choice using separately decoded IEEE fields. Per format it checks **17 rational values**, **2 overflow refusals**, and **3 pointwise old/new output-bound fixtures**: bias-first affine arithmetic, effective commit leakage, and minimum-subnormal thirds arithmetic. It also independently reconstructs the ordered zero-dot result `-1`. Production words, exact endpoint responses and output bounds agree with these oracles.
- **Certificate candidates:** for each format, every **625** 2-by-2 matrix with coefficients in `{-2,-1,0,1,2}` is compared against an independent dense rounded evaluator on the complete duplicated-bit domain. **16** are accepted and **609** refused, matching the independent predicate. The certificate covers four site/activation cases and four state/input transitions. This is a complete search of that small candidate alphabet, not the floating weight space.
- **State feedback:** per format, both initial bits and all 32 length-five Boolean input sequences give **64 paired traces**, **320 tick pairs**, and **320 interleaved commits**. The independent recurrence is `q_next=q XOR u`, and both full protected site outputs are checked. Across the two formats this is 128 paired traces, 640 tick pairs and 640 commits. The general finite-horizon conclusion still comes from T4's separate induction.
- **Adversarial transactions:** per format, **34 named re-signed packet or public-API refusals** preserve the complete live snapshot. They include claim downgrade, changed old/new endpoints, forged effective difference, stale version metadata, omitted states/sites/activations, fake domain/invariant/physical sharing, reduction/FMA/fusion changes, policy/schedule changes, forged proof/code digests, duplicate JSON keys, nonfinite JSON, noncanonical serialization, oversized input, invalid input bits, reinitialization and callback-bearing objects. Separate regressions cover stale replay, effective commit leakage, the tiny-input domain omission, a second shared call, invalid old invariant, and valid global evidence surviving a legal state advance.

This independent suite uses deterministic exhaustive sets and fixed adversarial values; it has no random sampling component of its own. Production seeded property tests are recorded separately. Counts have distinct units and must not be pooled as a theorem count or universal confidence score. Runtime and environment are recorded in the actual JSON; no throughput advantage is claimed.

## Remaining limitations

The complete-domain claim is about the small fixed trusted registry, not inferred reachability for arbitrary user programs. General input monitors, parameter orientations, hidden state, side effects, altered initialization and scheduling need their own containment and refinement arguments. Pointwise reports cannot authorize a global transaction. Arbitrary ordinary-basis probes cannot certify a rounded function on its span.

The actual BF16 arithmetic is a software RNE model; FP32 scalar CPU results are checked against exact rounding in this environment. Native BF16, GPU, arbitrary dense-library reductions, general concurrent publication, malicious private-runtime mutation, arbitrary compiler optimization and full host-stack formal verification are not certified. There was no SMT query or Lean/Coq run. The exact statements and all-time induction remain handwritten conditional proofs.

## Reproduction

```bash
python -B /workspace/p2_a3/verify_review_checks.py
```

This writes `review_results.json`. `--output PATH` preserves an earlier result when running a separate reproduction. The script uses the existing A3 source and declared read-only arithmetic dependencies; it does not run P1, P2-A1 or P2-A2 verification suites.
