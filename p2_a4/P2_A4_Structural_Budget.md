# P2-A4 structural reserve budget and fixed-layout example

This document compares exact geometric freedom with row-mask restrictions, then instantiates a small reserved-column layout. [structural_budget.py](structural_budget.py) implements pure exact-budget reports and immutable-bank evaluations. It does **not** add a new live certificate/commit protocol. A3's unchanged transactional checker is exercised separately by A4's discrete-capacity route.

## Row-mask dimension

Let H be a d-by-m exact generator matrix for a protected space V over Q or R. There are n output rows. Row i of an update may have nonzero entries only in a specified index set J_i. Writing H[J_i,:] for the restricted generator rows, the allowed coefficient vector a_i must satisfy

\[
a_i H[J_i,:]=0.
\]

Rank-nullity gives row freedom |J_i|-rank(H[J_i,:]). Rows are independent constraints, hence the masked exact update space has dimension

\[
\boxed{\sum_{i=1}^{n}\bigl(|J_i|-\operatorname{rank}H[J_i,:]\bigr).}
\]

This is at most n(d-r), where r=rank(H), because the masked space is a subspace of the full exact annihilator. It is not necessarily the number of allocated cells. All allowed cells can vary independently exactly when every H[J_i,:] is zero. Necessity follows by choosing a unit edit in any allowed cell; sufficiency follows because every such edited row then multiplies H to zero.

For a target matrix X, the masked response dimension for row i is

\[
\operatorname{rank}[H[J_i,:]\;X[J_i,:]]-
\operatorname{rank}H[J_i,:].
\]

The sum over output rows is the dimension of the complete response image. This follows from the quotient response theorem restricted to each row's coordinate domain. A larger cell mask may therefore still have no response on the chosen target. These are exact algebra statements; the budget helper does not establish global-domain provenance or authorize a floating commit.

## Common reserved columns and geometric cost

For a common coordinate set J in every output row, arbitrary edits in those n|J| entries are exact algebraic annihilators iff h_j=0 for every protected h and j in J. With c=d-r, necessarily |J|<=c. The reservation retains n|J| exact coordinate directions and excludes n(c-|J|) directions available in the unrestricted geometric annihilator.

The restriction can be strict. If V=span(1,1,1), there are two complementary geometric directions, but no individual input coordinate vanishes on V. A policy permitting only independently editable zero-input columns reserves none, even though the geometric update dimension for two output rows is four. Coupled edits such as `(1,-1,0)` are possible algebraically; they are not independently free coordinate cells.

The term “geometric” here means the full exact annihilator, not an automatically safe rounded projection. A coupled cancellation may fail under the executed numerical graph, as the A2/A3 subnormal and commit examples show.

## A small layout budget

Use one shared immutable two-by-three stored bank, fixed zero bias and two reserved words:

\[
W(\theta_0,\theta_1)=
\begin{pmatrix}1&0&\theta_0\\0&1&\theta_1\end{pmatrix}.
\]

The protected block remains I_2. The D arithmetic graph reads only columns 0 and 1, in that order, using separate nearest-even multiply/add. A separately declared A observation reads one selected column through a multiply-by-one and add-positive-zero graph. This is an explicit graph/layout specification, not a compiler optimization inferred from a dense formula.

| Declared D preparation | Complete legal activation set | Rank r | Full exact update dimension | Reserved-column dimension | Lost exact directions |
|---|---|---:|---:|---:|---:|
| `axis_reserve_v1`: `(q,u,0)` | All q,u in `{0,1}` | 2 | 2 | 2 | 0 |
| `correlated_reserve_v1`: `(q,q,0)` | q in `{0,1}`, with every legal external u still admitted | 1 | 4 | 2 | 2 |

Both initial state bits are allowed. Each tick evaluates the D output from the same old q, then computes `q_next=q XOR u` using the first D output and the old external input. The fixed Boolean graph has exactly representable intermediates and preserves the canonical-bit invariant. All legal histories remain covered; the rank is not estimated from a finite observed trace.

This models a simple construction in which one zero-filled input slot and two stored coefficients are reserved. If a compiler layout instead appends f reserved columns to d_D existing input columns, their independent coordinate allocation contributes nf entries. If the protected span has rank r<=d_D, geometric freedom is n(d_D+f-r), so the coordinate-only allocation omits n(d_D-r) additional exact directions. This is a budget identity under the stated layout assumptions. It does not implement a general C1 compiler or certify any arbitrary C4 backend.

For the axis fixture specifically, a two-by-two protected identity block has four stored words and full input rank, hence no nonzero exact annihilator. Appending the declared zero-filled third input column gives six stored words and two independent reserved coefficients. The additional coefficient storage is two words: 32 bits in BF16 or 64 bits in FP32, excluding alignment, metadata and input-port bookkeeping. The protected arithmetic graph is deliberately kept as the original two-column read graph; no automatic compiler rewrite or performance advantage is asserted.

The cost also depends on the A targets. In the correlated fixture, geometric updates can respond independently on the quotient directions represented by e1 and e3, giving response-space dimension four for the two-output target matrix `[e1 e3]`. The reserved third column responds only to e3, so its response dimension is two; its response on e1 is always zero. The same reserve can therefore preserve all response freedom on a selected e3 target while discarding all useful response freedom on a selected e1 target. A raw reserve-cell count alone does not characterize target-specific learning opportunity.

## Read-exclusion and its precise boundary

After a bank has passed validation, every D **arithmetic operand** and instruction is independent of theta. Therefore old and replacement banks produce the same protected arithmetic outputs for the same q,u. The fixed XOR recurrence and same-snapshot next-state calculation preserve paired states by induction for every finite legal history under the inherited execution premises.

The Python entry points first validate the complete bank, including reading and decoding the reserved words. Thus the entire host instruction trace and validation time are **not** claimed to exclude theta. Validation is total and side-effect-free for all admitted finite canonical reserved words, and those validation differences do not influence protected outputs, admissibility, state or the trusted logical schedule in this model. Host timing and side channels are outside this guarantee.

The reference performs pure immutable endpoint substitutions and returns a next-state value; it does not publish a live bank or implement concurrent atomicity. The separate A3 transactional tests retain endpoint, complete-domain, graph, policy, version and synchronous-publication obligations. A caller cannot use `validate_reserved_pair` as an A3 certificate: it explicitly records `authorizes_live_commit: false`.

Dense GEMM, skipped-term changes, reassociation, FMA, fusion, different zero policies and arbitrary caller-supplied model names are refused by the layout interface. Such a refusal means that this supported contract is unavailable, not that every alternative implementation is mathematically impossible.

## Full-format endpoint and response counts

Let F use p significand bits and eight exponent bits. With NaN/infinity patterns and negative zero rejected, the number of admitted finite canonical raw words is

\[
N_F=2^{p+8}-2\,2^{p-1}-1=2\cdot255\cdot2^{p-1}-1.
\]

There are exactly N_F^2 independently storable reserved endpoint pairs at a fixed protected I_2 block. All are algebraically safe for these zero-filled protected activations. All are bitwise safe for the fixed D arithmetic graph because its operands are unchanged after valid-bank checking.

At legal A input e3, the declared operation is theta_i*1+0 for each row. Every admitted theta_i has an exactly representable finite result equal to itself; gradual underflow preserves nonzero subnormals, and zero is canonical. Thus the full A output is `(theta_0,theta_1)`, an injective response signature. The number of distinct responses equals N_F^2. From the zero reserved pair, N_F^2-1 endpoints and response signatures are nonzero changes. At A input e1, the output remains `(1,0)` for every reserve choice, so the response image has cardinality one despite the large endpoint family.

| Format | Canonical finite words N_F | Reserved endpoint / A-e3 response signatures |
|---|---:|---:|
| BF16 | 65,279 | 4,261,347,841 |
| FP32 | 4,278,190,079 | 18,302,910,352,054,026,241 |

These are **proved counts**, not a claim that every endpoint pair was executed. The sets are finite and have no asserted real vector-space dimension. The ability to distinguish all these selected outputs does not establish training benefit, robust task performance or information-theoretic communication capacity under noise.

The concrete nonzero witness is reserved pair `(0,0)` replaced by `(1,2)`. The protected outputs and states remain identical; A-e3 changes from `(0,0)` to `(1,2)`. A-e1 remains unchanged, demonstrating that a nonzero safe edit need not affect a chosen target.

## Actual finite verification

The actual run of [verify_structural_cases.py](verify_structural_cases.py) is recorded in [structural_results.json](structural_results.json): **74,911 checks passed**, with **29 explicit refusals** and no unexpected failure. Seed: **20261114**. No previous-stage suite was run.

- **Mask geometry:** all 27 ternary three-coordinate generator vectors crossed with all 64 two-row masks, giving **1,728** cases. A separately assembled flattened coefficient-constraint matrix checks the dimension; the induced response map on its nullspace checks response dimension. There are **60** additional seeded rectangular rational cases, including empty generator/target families.
- **Small endpoint pairs:** per format, all **25** pairs from the five-value alphabet `{-2,-1,0,1,2}` are evaluated, with 25 distinct A-e3 signatures and one A-e1 signature. Across the two declared models and all bit inputs, this gives **200** protected input cases per format.
- **All BF16 scalar words:** all **65,536** bit patterns are tested by the scalar reserved read. **65,279** are accepted and return the same raw word; **257** are refused. Accepted probes execute **65,279 software multiplies and 65,279 software additions**. This is complete scalar-word coverage, not complete pair-space enumeration.
- **FP32 scalar words:** **524** deduplicated boundary/seeded raw patterns are tested; **521** are admitted, **3** refused. Their **1,042** native scalar operations are audited against exact rational RNE. This is a finite sample of FP32, not all 2^32 patterns.
- **State feedback:** per format, both models, both initial bits and all length-five input sequences give **128 paired traces** and **640 paired ticks**, with an independently coded Boolean recurrence. The general finite-horizon claim remains the separate induction, not extrapolation from five ticks.
- **Refusals:** protected coordinate changes, noncanonical/nonfinite words, bool masquerading as a word, mutable bank shape, invalid bits/models/targets, changed arithmetic policy and malformed masks are rejected. These pure functions have no live protected bank to modify; rollback evidence belongs to A3's reused transactional interface.

The final component elapsed time was approximately **22.520 s**, including approximately **16.152 s** for the complete BF16 scalar scan. These are observed costs of a small reference run, not throughput or scaling advantages. Main aggregate/reproduction timings may differ and are preserved separately.

The independent reviewer uses a separate exact constraint-rank and rounding/state oracle. Its counts and disposition belong to the independent result/report, not to this component's assertions.

## Limits

The geometric formulas concern a correctly justified protected span; samples cannot establish the needed upper inclusion. The discrete pair count fixes the old protected block, allowed coordinate mask, accepted word policy, D graph and restricted A observations. A different input domain, mutable bias, shared transpose use, direct weight-dependent branch, A-to-D channel or graph transformation requires new obligations.

BF16 execution here is software RNE; FP32 evidence is local audited scalar CPU arithmetic. GPU, native BF16, general concurrency, arbitrary compiler optimization and full proof-assistant verification are not certified. The fixture illustrates a verifiable capacity budget and a nonzero response, without completing later compiler, hardware or learning-performance stages.
