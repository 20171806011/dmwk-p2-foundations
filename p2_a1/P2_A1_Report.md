# P2-A1 — Research report

## Result

For each fixed deterministic matrix, a global activation space is well-defined once the program, physical sharing, input/history contract, initial states, execution schedule, and numerical policy are fixed. It is the exact rational or real linear span of all decoded activations at every admitted call and finite execution time. Finite floating-point words make the activation set finite; they do not make that set itself a vector space and do not force a deficient rank.

This round establishes conditional constructions and counterexamples. It does not implement a weight update, P2-A2, or a safety theorem for modified deterministic weights. It adds no GitHub publication task and does not modify or rerun completed P1 suites.

## Mathematical conclusions

The complete arguments are in [Theorems](P2_A1_Theorems.md), with the contract in [Definitions](P2_A1_Definitions.md).

1. **Existence and field agreement (A1.1).** With input width d, every finite-word activation decodes to a rational vector. Its rational and real spans have the same dimension r between zero and d. A basis can be selected from at most d actual activations, each occurring at a finite time. This does not supply a known stopping horizon when the legal history model has not been specified effectively.
2. **Sharing and evidence direction (A1.2–A1.4).** In a common physical column frame, a shared matrix's space is the sum of its call-site spaces. Its common annihilator is the intersection of the local annihilators. A nontrivial algebraic complement exists exactly when r<d. A legal sample gives a lower bound; a proved superspace gives an upper bound. Reaching rank d with legal witnesses proves full rank, while a full conservative superspace alone proves no such thing. For nonempty A, the rank of {(a,1):a in A} is affine-dimension(A)+1, not automatically rank(A)+1.
3. **Exact construction (A1.5).** A finite augmented machine, including a finite complete input monitor and scheduler, can be explored to a reachable-state fixed point. Processing every legal input at every reached configuration gives the complete call sets and exact spans for all finite times. Rank stabilization is not the stopping criterion. If R configurations are reachable, each reachable call has a witness using at most R transitions from an allowed start.
4. **Sound superspaces (A1.6–A1.7).** Given a proved affine/error enclosure of actual state updates, homogeneous state-space closure under the specified rational generators yields a finite, checkable invariant. Applying the declared call maps gives a sound activation superspace. The state-feature space is invariant under the generators; its image is not automatically an invariant of some unspecified activation dynamics. A finite one-hot lift always exists for an explicit finite transition table, but its dimension can already be the number of configurations.
5. **No universal low-rank promise (A1.8–A1.11).** Full rank, deficient rank, and loss of deficiency under sharing, reset, broader initialization or broader input contracts all occur. Encoding and intermediate Boolean features can change rank. For arbitrary computable history policies with unbounded external memory, exact global rank is undecidable by the stated halting reduction; this does not apply to a supplied finite complete monitor.
6. **Numerical limit (A1.12).** A row orthogonal to all admitted activations in exact algebra need not yield a zero ordered floating reduction. That gap must be resolved before any later patch-safety argument; it is not resolved by this geometry stage.

These are handwritten proofs of stated models, not a Lean/Coq proof of the Python implementation or the P1 toolchain.

## Key dimensions

Here `rank / ambient` denotes ordinary operand-space rank unless explicitly marked as augmented. All entries below are checked finite instances; their general families have separate proofs.

| Case | Ordinary rank / ambient | Augmented rank / ambient | Consequence |
|---|---:|---:|---|
| Every three-bit Boolean input | 3 / 3 | 4 / 4 | Exact discrete inputs can leave no algebraic complement. |
| Correlated inputs (0,0), (1,1) | 1 / 2 | 2 / 3 | A proved correlation leaves one algebraic direction. |
| Two sites receiving only the first or only the second coordinate direction | Each 1 / 2; shared 2 / 2 | Analyzed separately where bias is included | Two local deficiencies can disappear under physical sharing. |
| Three one-hot input vectors | 3 / 3 | 3 / 4 | Sum=1 is affine; ordinary one-hot span is full. |
| Two free register bits, three one-hot PC bits, one free input bit | 6 / 6 | 6 / 7 | The PC relation appears only with the constant coordinate. |
| Same eight values represented as binary / one-hot / one exact packed scalar | 3 / 3; 8 / 8; 1 / 1 | Representation-dependent | The packed scalar does not bound downstream unpacked rank. |
| Boolean features (a,b,ab) | 3 / 3 | 4 / 4 | Exact nonlinear feature construction can increase the augmented rank. |
| Declared but never-called three-column matrix | 0 / 3 | Empty-call span is zero | Absence of events is recorded explicitly, not omitted. |

For a finite hold/toggle/reset machine initialized to (0,0), the only reachable states are (0,0) and (1,1). Its homogeneous invariant is

$$
U_* = \operatorname{span}\{(0,0,1),(1,1,0)\},\qquad \dim U_*=2.
$$

All three declared homogeneous state generators preserve this space. The projected operand space has rank one. Adding reset to (1,0) removes the correlation and can make the ordinary operand space full. The verifier checks every one of the six reachable state/mode edges per format and matches the rational affine model to the actual exact Boolean reference operations. An additional unbounded-translation example tests the algebra library only; it is not claimed to execute exactly forever in finite precision.

## Actual compiler instances

The reference consumes the unchanged P1 A4 compiler and executor. A4 stores distinct graph nodes. An additional, explicit adapter interns ordered coefficient-plus-bias tuples and uses one tuple at its declared call sites; it does not infer physical sharing from numerical equality in the original graph. It preserves input wire gathers, term order, bias-first arithmetic and each site's post-row activation. On every explored edge, the adapter's final state bits are compared with an actual original `Executor.tick` call and with the source transition. Operand-only and augmented input spaces are reported separately.

| Fixed source model | Type-legal state universe | Reachable states | Legal edges | Graph nodes | Calls per format |
|---|---:|---:|---:|---:|---:|
| Two-bit counter stopping at value two | 12 | 6 | 6 | 45 | 270 |
| Two-register feedback with one unrestricted Boolean input | 4 | 4 | 8 | 13 | 104 |

Both models are exhaustively explored under each of software BF16 and local scalar CPU FP32. The schedule continues to invoke the whole graph at the absorbing HALT PC. The counter's six explored edges include one HALT self-loop; a policy that stops the clock at HALT is a different call-set specification. Every node is evaluated even when its corresponding source block is inactive. Across the two models, the original executor performs 1,500 audited multiply/add operations per format; the separately instrumented adapter performs another 1,500 per format. These counts are separate from the outer verifier's assertion count and from the additional examples.

The counter produces a concrete sharing effect:

- `row_003`, coefficients (1,1,-2) and bias zero, is used at nodes 3,7,18,20,26,28. Every local operand space has rank at most two in dimension three; their shared space has rank **three**. Every local augmented space has rank at most three in dimension four; the shared augmented space has rank **four**. Sharing removes all local algebraic freedom in this fixture.
- `row_005`, coefficients (1,1,-1) and bias zero, has shared operand rank **two** in dimension three. Its third operand is always zero on every reached edge at every declared site. The augmented rank is **three** in dimension four. This is a globally deficient space for this exact program, initialization, input contract and sharing adapter, not a guarantee for a changed program or a wider contract.

The JSON contains every declared row, its call-site ranks, merged ranks, distinct activation vectors and exact rational basis. BF16 and FP32 agree on these instance spaces. The compiler and the adapter have not been machine-verified for all source programs.

## Counterexamples and failed approaches

- **Low sampled rank:** the first eight calls of a nine-state saturating-clock fixture have activation (1,0), rank one. The next call has (1,1), producing global rank two. The handwritten family extends this obstruction to any prescribed finite sampling horizon.
- **Ignoring sharing:** combining two rank-one sites can produce rank two. All physical coordinate preparations must be applied before the merge.
- **Ignoring reset/initialization/input policy:** permitting a new reset or start can introduce an independent direction. A training sample or observed input distribution is not a legal-input contract.
- **Basis-only nonlinear closure:** two nonnegative basis vectors are fixed by ReLU, yet a linear combination can leave their plane after ReLU. Images of a basis certify closure only for a proved linear operation family.
- **Unsound branch relaxation example, corrected during review:** an initial demonstration included a guarded hold edge without an identity map in its relaxed generator family. The family now contains identity and the two-state guarded graph is explicitly enumerated. A conservative model must actually include every legal operation.
- **Omitting uncalled matrices, corrected during review:** the API now accepts declared matrix dimensions and sites, reports zero spans for uncalled objects, and rejects undeclared events when a registry is supplied. Without a registry it explicitly reports only observed objects.
- **Exact zero is not FP zero:** with p=8 or 24, a=(1,1,1,1) and v=(2^p,1,-2^p,-1), the exact dot is zero but the specified separate-RNE, ordered floating dot is -1. The BF16 and FP32 tests record the accumulator words and operations. This row is a numerical counterexample, not an admitted modification of the small-coefficient D graph.

## Executed evidence and cost

The final main run reports **passed**, **2,533 explicit outer checks**, eight recorded sections, and **0.156565 seconds** on its recorded environment. It includes 80 seeded rational-matrix cases, the explicitly enumerated finite models and four compiler/format combinations (two programs times two formats). The independent review reports **512 exhaustively checked binary 3-by-3 matrices**, four additional exact cases, and four negative argument checks; its recorded duration is **0.046422 seconds**. These totals have different units and are not added. No SMT queries and no proof-assistant proofs were executed in this round.

A second invocation from `/tmp`, saved as [reproduction_results.json](reproduction_results.json), passed the same 2,533 checks. The entire stage records and source-hash maps match the primary run exactly; timings differ. This is a working-directory reproduction check on the same environment, not an independent host or backend certification.

The main result file records Python/NumPy versions, the fixed seed 20261113, source hashes, backend metadata, explicit initial states and legal inputs, every instance's coverage, bases, rank sequences and observed operation counts. Measured numerator/denominator size is labelled **stored coefficient size**; it is not a measurement of all transient allocation or arithmetic bit costs. Observed times are not performance claims.

For R reachable configurations, a finite input alphabet U and K emitted vectors, enumeration costs at least the state/input coverage and graph evaluation, with incremental rank work O(sum over events of d_M squared) rational operations. A b-bit register machine can have 2^b states; an m-PC A4 source machine has at most m times 2^b type-legal states before monitor/scheduler augmentation. The simple common-invariant-hull procedure takes at most n strict rank increases in an n-dimensional feature space, plus a final closure check; a coarse dense bound is O((number of modes + 1) times n^4) rational operations. Input parsing, rational bit growth/gcd cost, call maps and explicit output storage are additional. The reference stores edges and events, so it is not a memory-optimized analyzer.

A resource limit raises an error rather than returning a partial search as a global certificate. Superspace construction can be cheaper than reachability but may return the full ambient space and therefore fail to resolve whether an exact nontrivial complement exists.

## Reproduction, provenance and limits

See [README](README.md) for commands. The existing P1 reference is read-only. [Dependency baseline](p1_dependency_baseline.json) and the actual result hashes bind the three imported P1 files. No P1 publication status is reset and no repository is created or pushed in this round.

The general reference interface handles fixed-orientation direct matrix calls in one physical column frame. A shared transposed use W and W-transpose requires separately typed input spaces and joint parameter constraints; this implementation does not silently combine them into one space. The compiler adapter handles ordered sparse scalar rows, not a certified dense GEMM backend.

Open work includes scalable nontrivial certificates for large nonlinear programs, proof of arbitrary callback/monitor fidelity, efficient symbolic reachability, rigorous refinement to optimized kernels, and any later connection from algebraic complementary directions to admissible bitwise-preserving weight changes. Native BF16, GPU, concurrent execution and complete Lean/Coq verification are not certified. All original P1 execution assumptions remain: legal encodings, correct rounding, bit-preserving storage, fixed D/policy, deterministic scheduling and same-snapshot commits.

The intended P2-A1 mathematical questions are answered within these explicit models and boundaries. General efficient global-space discovery is not claimed. This round stops here; P2-A2 and other later stages remain unstarted.
