# P2-B4 capacity across actual stored update histories

This document describes the capacity component of B4. Its general results are handwritten proofs in [Theorems T1–T5](P2_B4_Theorems.md), its public contract is [B4_Capacity_Interface.md](B4_Capacity_Interface.md), and its executed finite evidence is [capacity_results.json](capacity_results.json). The component is a diagnostic, not a live update authorization mechanism.

## 1. Objects that must remain distinct

Let a stored matrix decode to W in Q^(n×d), embedded in R^(n×d), and let V be a globally justified protected input span of rank r. The exact annihilator U(V)={Delta:Delta v=0 for every v in V} has dimension n(d-r). Its maximum individual update rank is min(n,d-r). If each update must have rank at most q, its maximum rank is min(q,n,d-r). The set with an intermediate rank cap is not generally a vector space, so n(d-r) is not its vector-space dimension.

The capacity code preserves separate objects:

1. The exact annihilator and its quotient-response map.
2. The actual finite stored endpoints, with effective increment W'-W decoded exactly.
3. Endpoints whose actual fixed raw-call outputs equal those of the anchor (BIT).
4. Distinct exact or raw responses on a declared set of A observation inputs.
5. Acceptance by the inherited A3 authorization checker (E_CERT), which can impose additional state/invariant requirements.

ALG and BIT are different constraints. In particular, a full-rank protected span eliminates nonzero ALG updates but need not eliminate nonzero BIT-equivalent endpoints on a finite raw domain. Conversely, cancellation in exact algebra does not guarantee cancellation in the actual ordered floating-point execution. E_CERT is not silently used as the definition of BIT.

All generic matrix APIs report `global_provenance_verified=False`. A rank calculation on supplied H proves a fact about span(H), not that H covers every legal activation of a program. `registered_budget` instead derives H from every call and input of a named unchanged A3 descriptor. That establishes its declared envelope only under the descriptor's inherited assumptions; it is not a reachability proof for an arbitrary changed graph.

## 2. Fixed, cumulative and moving spaces

All update histories use actual stored endpoints W_0,...,W_K and exact differences Delta_k=W_(k+1)-W_k. Consequently sum_(k<K) Delta_k=W_K-W_0 without an additional optimizer or storage-error term. Any such upstream effects are already in the endpoints.

For a fixed V, every increment annihilates V if and only if every prefix endpoint agrees with W_0 on V. Agreement only at W_K is weaker. The saved row history (0,0) -> (1,0) -> (0,0), with V=span(e1), returns to the protected anchor after violating it at the intermediate endpoint. The verifier records both final and prefix checks rather than letting final cancellation mask that violation.

Repeated fixed-space updates do not consume one algebraic dimension per step. The row history (0,0) -> (0,1) -> (0,2) -> (0,-1), protected on e1, has a one-dimensional exact update space at every step. It also demonstrates several nonzero stored changes without establishing any general learning benefit.

For cumulative arrivals, C_k=V_0+...+V_k and U(C_k) is a nested decreasing family. Its dimension n(d-rank(C_k)) and its achievable response-image spaces cannot increase. Task i is anchored at its admission endpoint W_i. In the recorded e1/e2 example, W_0=(0,0), W_1=(0,1), W_2=(0,1): the dimensions fall from 1 to 0, and both admitted anchors are preserved. The new e2 anchor is 1, not its old value 0 at W_0. Requesting the latter anchor at W_1 fails the admission check; merely freezing e2 cannot repair the mismatch.

For moving, nonnested spaces, neither monotonicity nor historical protection follows. The history (0,0) -> (0,1) -> (1,1) first protects e1 and then e2. Each current-space check succeeds while the old e1 anchor is damaged. Another saved schedule e1, span(e1,e2), e2 has dimensions 1,0,1: current algebraic capacity can recover by dropping old constraints, at the cost of losing their historical guarantee. These examples are exact in both tested formats.

## 3. Task compatibility and response capacity

Task generators H_i and desired images Y_i must define a single consistent linear map. Concatenate H=[H_1 ... H_m] and Y=[Y_1 ... Y_m]. Compatibility is equivalent to ker(H) being contained in ker(Y). The implementation computes an exact rational nullspace N of H and checks YN=0. If compatible, it returns a particular map plus affine-family dimension n(d-rank H); otherwise it returns a nonzero relation witness alpha with H alpha=0 but Y alpha!=0.

Pairwise intersection agreement is insufficient. For the three lines e1, e2 and e1+e2, desired scalar values y1,y2,y3 are jointly compatible exactly when y3=y1+y2. All pairwise line intersections are zero. Among all 27 assignments in {-1,0,1}^3, only 7 are jointly compatible although all 81 pairwise checks succeed. This is an admission/feasibility distinction, not evidence of a defect in the annihilator formula.

For A observations X, let s=rank([H X])-rank(H). The unrestricted exact response-image dimension is ns and the target-silent kernel has dimension n(d-r-s). A prescribed response R is feasible exactly when X alpha in V implies R alpha=0. When feasible, the smallest implementing update rank is rank R, so a per-update cap q admits that response exactly when rank R<=q. The executable reference reuses the exact A4 construction, while the new small verifier checks consistency using direct two-variable equations and determinants and checks the returned images, not just the reported dimensions.

Individual low rank is not a cumulative rank cap. With V=span(e1) in three input and output dimensions, the two stored increments diag(0,1,0) and diag(0,0,1) each have rank 1 but sum to rank 2. The general bound is min(n,d-r,Kq), and Theorem T4(a) gives a construction attaining it when enough complement directions are available. This statement concerns increments, not a persistent adapter whose baseline rank is separately constrained.

## 4. Fixed endpoint classes versus local reachability

Fix an absolute finite endpoint universe E, the protected space V and the protected exact anchor. If W_k agrees with W_0 on V, then

E_ALG(W_k,V) = {Z in E : Z|V=W_k|V} = E_ALG(W_0,V).

Fix instead a raw domain, complete graph/call order and numerical policy, and restrict to endpoints total on that domain. BIT output equality is an equivalence relation, so its entire class is unchanged along a BIT-equivalent chain. With fixed A observations, the absolute A-response image of either unchanged endpoint class is unchanged as well. A relative delta-response label can translate with the anchor; this does not change the absolute class or its cardinality.

The finite experiment fixes all four mutable cells of a 2×2 matrix to palette {-1,0,1,2}. Starting once at I and once at [[0,1],[2,-1]], it enumerates the same 256 endpoints. The descriptor protects duplicate inputs. Both runs have exactly the same 16 ALG endpoints, the same 16 BIT endpoints, and the same absolute raw A-response images. The absolute-family digest excludes values of mutable cells, so changing the anchor does not accidentally redefine E.

Global class invariance does not imply that a particular optimizer or small proposal can reach every member. Quantization, step-size restrictions, per-increment rank caps and optimizer state define different local neighborhoods. For example, at stored scalar W=1 with V={0}, a proposed increment equal to the smallest positive subnormal is nonzero in exact arithmetic but stores back to 1. A larger increment 1 reaches 2. This is a local proposal stall with an available alternative endpoint, not global capacity exhaustion.

An infinite sequence in a finite endpoint class must repeat an endpoint, but arbitrary external choices or additional optimizer state need not yield a periodic endpoint sequence. Finite stored capacity does not establish endlessly many distinct useful learned functions.

## 5. Finite palettes and whole-format extremal examples

The following counts hold separately for BF16 and FP32 under the explicitly declared software/CPU policy. They are complete only for the displayed finite families. Eta is the smallest positive subnormal of the respective format.

| Descriptor/anchor and palette | Stored candidates | ALG | BIT | E_CERT |
|---|---:|---:|---:|---:|
| Duplicate inputs, I, {-1,0,1,2} | 256 | 16 | 16 | 16 |
| Duplicate inputs, [[0,1],[2,-1]], same palette | 256 | 16 | 16 | 16 |
| Duplicate inputs, I, {0,eta,1} | 81 | 4 | 16 | 16 |
| Split inputs, I, {0,eta,1} | 81 | 1 | 2 | 2 |
| Duplicate inputs, zero matrix, {0,1} | 16 | 1 | 1 | 0 |
| All shared axis inputs, I, {-1,0,1,2} | 256 | 1 | 1 | 1 |

In the tiny duplicate family, 8 BIT updates have actual rank 2 although the exact protected complement has dimension 1. This is consistent: those updates need not belong to the exact annihilator. In the tiny split family, the protected span is full rank, yet one nonzero stored BIT-equivalent endpoint remains. The zero-matrix row distinguishes raw total output equality from the stricter A3 checker: it is BIT-equivalent to itself on the stated calls but violates additional original-state obligations of that checker. The capacity diagnostic does not use this raw BIT observation to authorize a live change.

Whole-format storage collapse is a separate proved extremal example. Let M be the maximum finite magnitude and let W be the 2×2 matrix with every entry M. Protect V=span((1,1)). Any finite endpoint Z with Z(1,1)^T=W(1,1)^T must have each row sum 2M in exact algebra. Since each entry is at most M, every entry must equal M. Thus the stored ALG endpoint count is 1 despite exact dimension 2. The old actual call at h=(1/2,1/2) remains finite and returns (M,M); using h=(1,1) would instead overflow and is not the executed probe.

At the different anchor W=0 with the same V, each safe row can be (a,-a). With N canonical finite values, the complete stored ALG count is N^2: N=65,279 for BF16 and N=4,278,190,079 for FP32, giving 4,261,347,841 and 18,302,910,352,054,026,241 endpoints respectively. These counts follow from the proof and sign symmetry, not from enumerating all words. The zero and saturated anchors cannot be connected by a fixed-ALG-safe chain; they illustrate anchor dependence rather than within-class depletion.

The executed boundaries also retain two numerical separations. At old row (2^p,0), an ideal increment (1,-1) is orthogonal to (1,1), but storage produces effective increment (0,-1). In the thirds example, the submitted matrix itself has exact zero row sums yet the specified ordered floating-point outputs differ on a protected input. Ideal proposal safety, effective exact safety and raw BIT safety therefore remain separate checks.

## 6. Reproduction, costs and actual evidence

Run only this new component from any working directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B /workspace/p2_b4/verify_capacity.py \
  --output /tmp/p2_b4_capacity_results.json
```

The saved first component run used Python 3.12.14, NumPy 2.3.5 and Linux x86-64; its measured elapsed time was 14.841555603001325 seconds. Root seed is 20261114. BF16 multiply/add is a Fraction-based software RNE model. FP32 uses separate CPU NumPy float32 multiply/add with each result audited against rational RNE. The numerical contract specifies nearest-even, gradual underflow, canonical +0 and no FMA. Environment details and exact raw outputs are in the JSON; no GPU or native BF16 execution is claimed.

| New component evidence | Actual scope |
|---|---|
| Exhaustive stored histories | 1,458 cases: all triples of row endpoints in {-1,0,1}^2, both formats |
| Seeded fixed-space histories | 72 rectangular rational cases, 4 constructed increments each |
| Quotient budgets | 64 binary H/X cases |
| Prescribed response/rank-cap queries | 1,728 queries; 468 feasible and checked constructions |
| Joint task assignments | 27; 7 compatible; 81 pairwise compatibility checks |
| Finite endpoint families | 12 families, 1,892 enumerated candidates |
| Explicit invalid inputs | 10 expected refusals |
| Recorded assertion checks | 14,345; no unexpected failure in the saved run |

The assertion count includes distinct checks on shared cases; it is not a count of independent experiments. Named boundary records and whole-format proofs must not be added to the enumeration count as if all words had been tested. This component runs no old-stage test suite, no new optimizer trajectory, no SMT query and no proof assistant. Independent B4 validation has its own script/results and must be cited with its own actual scope.

Exact elimination on a d×m generator matrix uses polynomially many rational field operations (ordinary elimination O(d m min(d,m))), with integer bit costs depending on intermediate numerator/denominator growth. The reference repeats some elimination and constructs explicit witnesses for clarity; it is not an optimized rank-maintenance algorithm. Histories retain every prefix and task-anchor check; with K arrivals, checking every admitted anchor at every later endpoint has O(K^2) pairs before matrix-operation costs. Enumeration with p palette words and c mutable cells visits p^c endpoints and performs exact and actual-call checks on each. The explicit `max_candidates` limit refuses excessive finite families; this does not classify the unvisited family. No performance advantage is inferred from the measured runtime.

## 7. What this component does not establish

Generic H data does not establish whole-program activation coverage. Exact output anchors do not alone describe nonlinear task success. Raw-call BIT requires a separate invariant/local-to-program argument before it preserves an evolving protected trace. Changes to graph, domain, reduction order, FMA, state sharing or scheduling require renewed contracts. A supplied unsafe history is analyzed and marked unsafe; this diagnostic never publishes it.

The results do not certify GPU, native BF16, arbitrary compiler optimization, general concurrency or hostile direct memory mutation. They do not show that all algebraic updates are storable, that all stored updates satisfy BIT, that all BIT endpoints satisfy A3 authorization, or that a nonzero A response improves a real learning task. B4's separate serial transaction experiment supplies its own accepted toy training evidence; no such training is fabricated in this component.
