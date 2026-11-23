# P2-A4 — Counterexamples and constructive boundaries

The examples below delimit the theorems in [Theorems](P2_A4_Theorems.md). General mathematical arguments, finite enumerations and numerical observations are labeled separately. Set n to the output dimension, d to the input dimension, r=dim(V), and c=d-r. ALG means exact annihilation of the proved protected span by the actual decoded endpoint difference; BIT means equality on the complete declared raw protected domain under the fixed execution graph and policy. Neither property automatically implies the other.

## 1. Zero rank, full rank and shared-call exhaustion

**Exact construction.** If V={0}, all n-by-d exact maps are allowed: dimension nd and maximum update rank min(n,d). If V=K^d, only the zero exact annihilator is allowed. These statements concern exact algebra, not arbitrary finite-domain BIT edits.

For one shared 1-by-2 bank, let call site 1 produce e_1 and call site 2 produce e_2. Each local protected span has rank one and leaves one exact scalar degree of freedom. The global span is K^2 and leaves zero. The locally safe update (0,1) changes site 2. Counting the local complements independently would authorize an unsafe shared edit.

**Evidence.** `algebra_results.json/named_cases/zero_rank`, `full_rank` and `local_low_rank_global_full_rank`; finite shared-site endpoint families and omitted-site refusal checks in `discrete_results.json`. T1/T2 prove the general statements.

## 2. A conservative span can freeze too much; a sampled span can protect too little

**Exact counterexamples.** With true V=span(e_1) in K^2, the update (0,1) is safe. Replacing V by a proved containing space U=K^2 removes that freedom, so a valid conservative estimate may reject useful exact possibilities. Conversely, if the actual protected set contains e_1 and e_2 but the sample contains only e_1, the same update passes the sample constraint and changes the omitted input by one.

A proved superspace supplies a conservative lower bound on available exact freedom. A sample span supplies only an optimistic upper bound until an independent global containment proof is provided. Neither the number of observed examples nor a low observed rank resolves that distinction.

**Evidence.** `algebra_results.json/named_cases/conservative_overfreezing`, `sample_underprotection` and `protection_chain`; independent exact constraints and the A3 sample-domain refusals. This is not an empirical estimate of a real model's reachable span.

## 3. An algebraic direction need not produce a nonzero stored endpoint

**Full-format impossibility proof.** Let M be the maximum finite positive value of the admitted BF16 or FP32 format and use an old 2-by-2 bank with every entry M. Protect h=(1/2,1/2), so r=1, c=1 and the exact update space has dimension two. Exact preservation requires each new row (a,b) to satisfy a+b=2M. Since a<=M and b<=M, both must equal M. Thus the complete finite-format ALG endpoint set has cardinality one.

The old execution is finite: the products M/2 and M/2 and their sum M are exactly representable. This example does not rely on an overflowing old output. It proves singleton **ALG** capacity; it does not assert a singleton BIT class.

**Same rank, opposite endpoint count.** Keep the same protected span and use the zero old bank. Each exact-safe row is (a,-a), with exactly N canonical finite choices for a. The two rows are independent, giving N^2 ALG endpoints. Hence the same rank and exact dimension give **one** endpoint at the saturated old bank and **N^2** at zero:

| Format | N | N^2 |
|---|---:|---:|
| BF16 | 65,279 | 4,261,347,841 |
| FP32 | 4,278,190,079 | 18,302,910,352,054,026,241 |

**Evidence.** T5 is the whole-format proof. `boundary_results.json` records `same_rank_different_complete_format_ALG_counts` for both formats, including the exact residual of a neighboring candidate and displayed finite execution probes. `discrete_results.json` and the independent checker also retain the saturated fixture. These are proved counts, not whole-format bank enumeration.

An even simpler admitted-family restriction is an all-frozen mask: it gives one candidate regardless of the unrestricted exact dimension. The separate `A4-D1_mask_capacity_collapse` example demonstrates that case without confusing a chosen mask with an intrinsic limitation of the whole format.

## 4. The ideal proposal is not the submitted effective update

**Numerical counterexample.** Let p be the format's significand precision (8 for BF16, 24 for FP32). For an old row (2^p,0), propose the exact increment (1,-1), which annihilates (1,1). Under round-to-nearest ties-to-even, the first endpoint entry RN(2^p+1) is still 2^p; the second becomes -1. The actual endpoint difference is therefore (0,-1), which does not annihilate the protected direction.

The correct capacity object is decoded W'-W. Testing the proposal or its generating factors before storage does not establish the submitted endpoint's membership in ALG or BIT.

**Evidence.** `boundary_results.json/ideal_not_effective_rank_budget` and `discrete_results.json/A4-D5_commit_changes_effective_update` record this in both formats and record refusal. This is an adversarial finite execution case, supported by the explicit rounding argument.

## 5. An exact-safe stored endpoint can fail BIT, even after a floating basis test

**Counterexample under the fixed separate-operation policy.** Let eta be the smallest positive subnormal and s=RN(1/3). Use the old zero 3-by-3 matrix and the stored endpoint

\[
Q=\begin{pmatrix}2s&-s&-s\\-s&2s&-s\\-s&-s&2s\end{pmatrix}.
\]

Protect the complete two-input raw domain {1_3, eta 1_3}. Its exact span has rank one. Every decoded row sums to zero, so Q belongs to ALG. Ordered execution at 1_3 gives zero. At eta 1_3, each positive product 2s eta rounds to eta, while each negative product -s eta rounds to zero (then canonical +0); the output is eta in every row. Thus Q is not BIT, and checking the floating output only on the ordinary basis vector 1_3 would miss the violation on another legal activation in its span.

**Evidence.** `boundary_results.json/ALG_not_BIT_family` enumerates the two endpoints {0,Q} in both formats: ALG count two, BIT count one. The actual nonzero output words are `(1,1,1)`, where raw word 1 denotes eta. Independent word-search rounding checks confirm the boundary. This is not a claim about flush-to-zero hardware or a different reduction graph.

## 6. Full protected rank does not exclude nonzero BIT edits

**Counterexample.** Let old W=I_2, new W'=((1,eta),(0,1)), and protect the complete raw set {0,(1,1),e_1}. Its span is K^2. The endpoint difference is nonzero and not ALG. Yet all protected outputs are bitwise unchanged: eta is absorbed in RN(1+eta)=1 at (1,1), and the other inputs are exact. At legal A input e_2, the output changes from (0,1) to (eta,1).

This refutes the implication “full protected rank implies no executable observational capacity.” It does not refute the correct exact theorem that full protected rank forces the exact annihilator to be zero. Adding e_2 to the protected raw domain exposes the edit without increasing its already full numeric rank.

**Evidence.** `boundary_results.json/full_rank_BIT_not_ALG_family`: two candidates, ALG count one, BIT count two, in each format, plus eight paired feedback ticks. In the complete 81-endpoint `tiny_nonnegative` family for `split_feedback_v1`, the producer and independent checker both find one ALG and two BIT endpoints. The legal A output change is actually retained as the subnormal raw word.

## 7. A BIT update can have rank greater than the complement dimension

**Counterexample.** Keep old W=I_2 but protect only the duplicated-bit raw domain {0,(1,1)}. Here r=1 and c=1. Take

\[
W'=\begin{pmatrix}1&\eta\\\eta&1\end{pmatrix},\qquad
\Delta_{\mathrm{eff}}=\begin{pmatrix}0&\eta\\\eta&0\end{pmatrix}.
\]

Each protected nonzero output rounds 1+eta to one, and zero stays canonical zero. Thus the edit is BIT. Its exact determinant is -eta^2, which is nonzero in Q/R, so its exact rank is two, greater than d-r=1. At A inputs e_1 or e_2, the eta output change survives. Computing the determinant in the finite format would underflow and is not a valid exact rank test.

**Evidence.** The `tiny_nonnegative` / `duplicate_feedback_v1` family in `discrete_results.json` contains this endpoint in both formats. Its 81 candidates contain four ALG and sixteen BIT endpoints. Among BIT endpoints, the exact effective ranks are: one rank-zero, seven rank-one and eight rank-two. The independent checker confirms all candidate memberships. The algebraic rank bound applies to annihilators, not arbitrary finite-domain BIT edits.

## 8. A nonzero safe update may be silent on A

**Exact construction.** Let V=span(e_1) in K^3, with one output and target X=e_2. The nonzero update (0,0,1) is safe but produces zero target change; (0,2,0) is safe and produces target change two. Here c=2, target quotient rank s=1, response dimension one and silent-kernel dimension one. If every A target lies in V, then s=0 and all exact-safe updates are silent on A despite positive update capacity.

**Evidence.** `algebra_results.json/named_cases/silent_and_responding` and `all_targets_protected` validate these exact constructions. The structural finite family also records unchanged A output on e_1 for all checked reserved pairs, while e_3 distinguishes every pair. This separates nonzero parameters, nonzero outputs and independently controllable targets.

**A stored, accepted responding example.** In the A3 duplicate-feedback model, the nonzero stored endpoint change I_2 to ((0,1),(2,-1)) preserves the full protected domain and changes legal A output at e_1 from (1,0) to (0,2). The actual serial transaction records in both formats include 49 trace ticks, with 48 seeded accepted patch ticks. The structural example W_theta with theta=(1,2) similarly changes A output on e_3 from (0,0) to (1,2). These are examples of functional response, not evidence of general learning performance.

## 9. Target relations and rank caps impose distinct impossibilities

**Quotient-relation counterexample.** Let V=span(e_1) in K^2 and X=(e_2,e_1+e_2). Both target columns represent the same quotient class. With alpha=(-1,1), X alpha=e_1 lies in V, so every safe response must satisfy R alpha=0. The requested row R=(1,2) is impossible even though its rank is one. The row R=(1,1) is feasible via Delta=(0,1).

**Evidence.** `boundary_results.json/target_compatibility_not_rank_alone` records that exact witness and construction. The related producer named case uses X=(e_2,2e_2) and R=(1,1), with witness alpha=(-2,1). The complete small response sweep also includes inconsistent targets.

**Rank-cap impossibility.** With V={0}, X=I_2 and prescribed R=I_2, the unique response constraint forces Delta=I_2 and rank two. Cap k=1 is impossible although the unconstrained response is feasible. More generally, T3 proves the minimum implementation rank is rank R; rank R<=k is an additional condition, not a replacement for quotient compatibility. The mathematical 2-by-2 example is an immediate proof; the producer's actual cap tests cover 6,912 finite queries and seeded rectangular positive/negative constructions.

Even the family rank Delta<=1 is not a vector space: diag(1,0) and diag(0,1) each satisfy it but their sum has rank two. `rank_cap_not_linear_space` records this exact example. No nc vector-space dimension is assigned to the intermediate low-rank family.

## 10. Structural reserves can lose geometric freedom

**Exact boundary.** For V=span(1,1) in K^2, an update row (a,-a) is safe, so there is a nontrivial geometric complement. Neither input coordinate is identically zero on V. Consequently no single coefficient can be changed independently while the other is frozen. A geometric projection can coordinate both entries; a free-coordinate reserve cannot claim that same freedom.

For the implemented 2-by-3 layout, reserve only the last column. With D inputs (q,u,0), the global protected rank is two: algebraic dimension two, reserved-mask dimension two and cost zero. With D inputs (q,q,0), rank is one: algebraic dimension four, reserved-mask dimension two and cost two. Both layouts retain two stored response words at A input e_3. Structural simplicity has an explicit budget cost in the correlated case.

**Evidence.** `structural_results.json/layouts` records both budgets and `no_independent_coordinate_example` records a further zero-reserve boundary. The main mask suite checks 1,728 exhaustive cases and 60 rational rectangular cases; the independent checker uses direct constraints for 4,096 two-row reports. T7 proves the general mask formula. These are small fixed layouts, not a completed general compiler or a hardware-optimal allocation theorem.

## 11. Complete finite candidate counts do not describe the whole format

The following actual endpoint counts are identical in the BF16 and FP32 runs, but concern the stated finite alphabets only. The old bank is I_2 and all four cells are mutable.

| Alphabet and candidate count per model | Protected model | ALG | BIT | ALG intersect BIT |
|---|---|---:|---:|---:|
| {-1,0,1,2}, 256 | duplicate feedback | 16 | 16 | 16 |
| {-1,0,1,2}, 256 | split feedback | 1 | 1 | 1 |
| {-1,0,1,2}, 256 | shared axes | 1 | 1 | 1 |
| {0,eta,1}, 81 | duplicate feedback | 4 | 16 | 4 |
| {0,eta,1}, 81 | split feedback | 1 | 2 | 1 |
| {0,eta,1}, 81 | shared axes | 1 | 1 | 1 |

Across both formats this is 2,022 endpoints in twelve families, independently reevaluated. For the stated full-output basis observer, raw A-signature counts equal endpoint counts because e_1 and e_2 expose every column. In the shared-axis fixture this observer is a declared stateless diagnostic, not an additional certified program-level A interface.

The finite candidate sets, their ALG/BIT subsets and their raw response images are finite sets, not nonzero vector spaces over Q/R. For example, scalar multiplication can leave the chosen endpoint alphabet. Full-format counts require the separate T4/T5/T8 proofs; finite family enumeration cannot establish them.

## 12. Contract changes and unsafe authorization are rejected, not repaired by capacity

The implementation does not authorize a patch merely because its projected generator has low rank, its algebraic residual is zero, or a few tested outputs agree. Acceptance uses the inherited A3 endpoint/domain/graph/policy/version/schedule contract. The discrete suite records 38 expected transaction refusals and checks protected snapshots after refusal. Independent checks include stale replay, omitted call sites, sampled-domain claims, a changed numerical policy and a changed schedule. A certificate for one graph does not authorize reassociation, FMA, fusion or another graph, even when a displayed test output happens to match.

Structural read exclusion has a narrower meaning: the declared D arithmetic omits the reserved words after pure admitted-bank validation. It does not say that validation, memory access traces, runtime cost or all host branches are independent of those words. The structural module substitutes immutable endpoint banks in a small model; it is not a replacement for the live A3 certificate checker.

All numerical examples assume the recorded canonical-zero, finite-word, correctly rounded, gradual-underflow and fixed-order policies. BF16 execution here is software; FP32 checks are local native CPU operations with exact or independent rounding references. GPU, native BF16, arbitrary optimizations, untrusted runtime mutation and general concurrent commits remain uncertified. The counterexamples change or delimit claims; they are not evidence that useful learning has been achieved or that the remaining P2 stages are complete.
