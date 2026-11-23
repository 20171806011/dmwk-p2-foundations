# DMWK P2-A4 research report: rank budgets, feasibility and impossibility

## Main result

A4 gives a precise algebraic answer to how much rank must remain for a specified response, and proves why that answer is not a universal finite-precision learning criterion.

For square d-by-d weights and a globally justified protected span V of rank r, the unrestricted exact update space has dimension d(d-r). Every member has rank at most d-r. With a generator rank cap k, the maximal attainable update rank is min(k,d-r), provided arbitrary exact complement maps are allowed. These bounds are attainable by explicit constructions; storage and execution impose separate constraints.

The relevant quantity for A targets is more specific. For target columns X, define

\[
c=d-r,\qquad s=\operatorname{rank}[H\ X]-r.
\]

Here s counts independent target directions **modulo the protected space**, not the number of targets or the ordinary rank of X. A nonzero exact A-target response preserving D exists precisely when s>0 and the rank cap permits at least rank one. A desired response matrix R must additionally respect every relation `X alpha in V => R alpha=0`. Once compatible, its minimum required update rank is rank(R).

Finite stored endpoints and rounded execution change the question. At the same protected rank, stored exact-safe capacity can range from many endpoints to only the old bank. Conversely, a finite-domain bitwise-equivalent edit can exist at full protected rank, and its effective rank can exceed d-r. Thus no single retained-rank number answers all four capacity questions.

This is an A4 delivery only. It does not establish universal learning benefit, complete B4 long-term training, implement B1, finish a C1 compiler or certify arbitrary C4 hardware.

## Four capacities and their premises

Fix one physical shared matrix with n output rows and d input columns; set n=d for the requested square case. Fields are Q or R, with exact rational computation for decoded finite endpoints. Bias is fixed unless an explicitly augmented joint affine block is analyzed. All protected sites, legal initial states, input histories, state preparations and time are included in the global protected domain. Site-local spaces are merged in common physical coordinates.

| Capacity | Mathematical object | Valid descriptor |
|---|---|---|
| Exact algebraic freedom | U(V)={Delta:Delta V=0} | Vector-space dimension n(d-r), individual rank, attainable response subspace |
| Stored endpoint feasibility | E_ALG={w' in E:(decode(w')-W)V=0}, for fixed old bank and endpoint family E | Cardinality, non-no-op count, exact rank histogram; not a real vector-space dimension |
| Fixed-graph bitwise equivalence | E_BIT on every declared protected raw context under a fixed graph/policy; E_cert for a supported certificate route | Finite cardinality and executable observations; not inferred from real-span rank alone |
| A response capacity | Exact response image Delta X, or finite accepted raw A-output signatures of a specified endpoint subset | Exact image dimension or finite signature count, with target/domain identity fixed |

The actual update is always the exact decoded difference Delta_eff=W'-W. An ideal delta or its separately quantized representation cannot substitute for it. Canonical finite encoding makes endpoint-to-effective-difference mapping injective at a fixed W; the differences themselves need not be standalone representable floats.

ALG and BIT sets are not generally nested. The joint requirement uses their intersection. Rank-capped algebraic families are generally non-linear sets, so their unrestricted dimension is not reused as a linear dimension. Finite response counting excludes rejected/nonfinite A executions unless a separate failure alphabet is explicitly introduced.

[Definitions](P2_A4_Definitions.md) fixes the complete domains and notation. All general results in [Theorems](P2_A4_Theorems.md) are handwritten conditional proofs, not machine proofs.

## Rank, response and impossibility theorems

### Exact rank budget and equality constructions

Choose a basis of V and extend it by c complement directions. An annihilating map can independently assign n output coordinates to each complement basis vector, giving dimension nc. Its image is spanned by at most c vectors, so rank(Delta)<=min(n,c).

For Delta=G P_perp and rank(G)<=k,

\[
\operatorname{rank}\Delta\le\min(k,n,c).
\]

For any q up to that bound, send q independent complement vectors to q independent output vectors and kill the remaining basis vectors. The resulting Delta has rank q; choosing G=Delta gives Delta=G P_perp and the same cap. For a fixed proposed G, however, orientation can destroy rank: a generator supported on protected directions may yield G P_perp=0 despite a positive rank budget.

At r=d, the unrestricted exact annihilator is zero. At r=0 it is the full n-by-d space. With k=0 only zero is allowed even if c>0. These are algebraic statements; the constructions need not be representable endpoint changes at a fixed old bank.

### Simultaneous target control

Let pi be the quotient map to K^d/V and Y=pi X in any quotient basis. Then

\[
\dim\{\Delta X:\Delta\in U(V)\}=ns,
\quad
\dim\{\Delta\in U(V):\Delta X=0\}=n(c-s).
\]

A prescribed R is feasible exactly when ker(Y) is contained in ker(R). A constructive proof defines a map on im(Y) by `Y alpha -> R alpha`, extends it by zero on a complementary subspace, and composes with pi. Its image equals im(R), so its update rank is exactly rank(R), which is minimal. Under generator cap k, feasibility additionally requires rank(R)<=k.

The maximum attainable response rank is min(k,n,s), or min(n,s) without an active cap. Nonzero target-silent exact updates exist when c>s, provided a cap admits rank one. When s=c, every nonzero exact annihilator changes at least one selected target. When s=0, all selected targets lie in V and every exact protected update is silent on them.

Arbitrary independent target labels require quotient column rank s=m, where m is the number of target columns, and cap k>=min(n,m) to realize every n-by-m R. Merely having c>=m is not enough if target classes are dependent. For example, with V=span(e1), targets e2 and e1+e2 must receive the same exact response from any annihilator. Asking for scalar responses `(1,2)` is impossible even though the requested response has rank one and the complement is nonzero.

These characterize possible exact linear changes at specified inputs. They do not prove optimization convergence, generalization, semantic usefulness or a learning task's reward improvement.

### Protection growth and provenance

For V contained in U with ranks r and r', U(U) is contained in U(V), and the unrestricted exact dimension decreases by n(r'-r). Shared calls require their global summed space. A proved containing space safely sacrifices possible algebraic freedom; a legal sample span gives an optimistic upper bound on algebraic capacity and cannot authorize protection of omitted inputs.

Finite ALG endpoint sets shrink under added protected linear constraints at the same old bank and endpoint family. BIT sets shrink under genuinely nested raw protected domains with graph, policy, observations and admissibility fixed. Merely increasing the rank of a numeric sample, or comparing different programs with changed preparations, does not establish BIT monotonicity. This is a fixed-contract result, not a theorem about unrestricted long-term training.

### Finite counts and a concrete exhaustion criterion

Let N be the number of admitted canonical finite format words. If the admissible algebraic endpoint constraints lie in an affine space of dimension q, then

\[
|E_{\rm ALG}|\le\min(|E|,N^q),
\qquad q=n(d-r)\text{ for unrestricted annihilation.}
\]

The proof selects q scalar coordinates on which the affine solution space projects injectively; each has at most N choices. Not all such tuples must extend to representable endpoints. The bound is attained when protection fixes r coordinate columns and leaves every remaining column unconstrained. For a finite A-total endpoint subset S,

\[
|\mathcal R_A(S)|\le\min(|S|,N^{nm}).
\]

These are counting bounds, not vector-space dimensions or measured information throughput. The no-op supplies a lower bound of one only when the old bank belongs to E and meets the stated totality/domain requirements.

There is also an executable singleton criterion stronger than full numeric rank. For the direct zero-bias, full-output, ordered matrix graph, each standard basis input e_j returns exactly stored column j. If all e_j are protected actual inputs, every BIT endpoint must be the old bank. If all e_j are A targets instead, their response signature is injective on any endpoint subset, so response count equals endpoint count. Nonzero bias, restricted observations or another graph require a separate argument.

## Finite-format feasibility can differ radically at the same rank

Both formats use nearest-even rounding, gradual underflow and canonical arithmetic zero; NaN, infinity and negative-zero stored proposals are refused. Their accepted word counts are N_BF16=65,279 and N_FP32=4,278,190,079.

Take V=span(1,1), with two output rows. At the zero old bank, every exact-safe row has form `(a,-a)`. The symmetric canonical finite alphabet gives exactly N choices per row, hence **N² stored ALG endpoints**.

At an old bank whose every row is `(M,M)`, M the maximum finite value, exact protection requires `a+b=2M`. Since each finite endpoint coefficient is at most M, both must remain M. Thus **only one stored ALG endpoint exists**, although the abstract update-space dimension is still two. The protected input `(1/2,1/2)` keeps the old actual output finite at M, so this example does not depend on an invalid overflowing baseline.

The N² and singleton conclusions are full-format handwritten counting/impossibility proofs. Only their displayed boundary executions were probed; FP32 endpoint space was not enumerated. This proves that old-bank location matters in addition to protected rank.

## Actual finite endpoint searches

The discrete reference completely enumerates explicit families in the unchanged A3 registries. The `BIT` fields record the certificate-accepted route E_cert. For the supported canonical baselines and fixed complete registry domains, the extra closure checks follow from the checked identity output map; independent direct rounding tests confirm agreement with the local BIT predicate for every enumerated endpoint. No completeness over arbitrary programs or proof languages is claimed.

Both formats produced the following counts. Eta denotes that format's minimum positive subnormal.

| Candidate coefficient alphabet | Model / protected raw inputs | Candidates | ALG | Certificate/BIT |
|---|---|---:|---:|---:|
| `{-1,0,1,2}` | Duplicated bits: `{0,(1,1)}` | 256 | 16 | 16 |
| Same | Split: `{0,(1,1),e1}` | 256 | 1 | 1 |
| Same | Axes: `{e1,e2}` | 256 | 1 | 1 |
| `{0,eta,1}` | Duplicated bits | 81 | 4 | 16 |
| Same | Split | 81 | 1 | 2 |
| Same | Axes | 81 | 1 | 1 |

Across two formats, these are **2,022 endpoints in 12 finite families**. They are not all BF16/FP32 endpoints. The duplicate/split comparison is interpreted as a local raw-domain constraint comparison under the shared row evaluator; the whole registered programs have different input preparations and are not declared identical graphs.

For the tiny split family, the two BIT endpoints have only one raw response at target e1, two at e2, and one at zero. The nonzero edit is therefore silent on the selected nonzero legal target e1 but changes e2. Response capacity depends on the selected A target set, not just endpoint count.

In the tiny duplicate family, the BIT effective-update rank histogram is `{0:1, 1:7, 2:8}`, while its ALG subset has `{0:1, 1:3}`. The explicit edit `I_2 -> ((1,eta),(eta,1))` has rank-two effective difference, yet both protected duplicated-bit outputs round to their old words. Here d-r=1. This demonstrates that even the individual-rank bound is an ALG-only claim.

## Structural reserve versus geometric freedom

For a common reserved column set J, arbitrary independent edits in its n|J| cells are exact-safe precisely when every protected vector has zero coordinates there. The retained dimension is n|J| and the cost relative to geometric freedom is n(c-|J|). For a general per-row mask J_i, the exact dimension is

\[
\sum_i\bigl(|J_i|-\operatorname{rank}H[J_i,:]\bigr).
\]

Writable cells may require correlated changes. With V=span(1,1), no individual coordinate is independently free, even though correlated rows `(a,-a)` provide a geometric complement.

The concrete layout uses

\[
W(\theta)=\begin{pmatrix}1&0&\theta_0\\0&1&\theta_1\end{pmatrix}.
\]

The fixed D arithmetic graph reads the first two columns. The reserved third input is zero on every protected activation. A legal A observation at e3 returns the two reserved words exactly.

| D preparation | Protected rank | Geometric dimension | Reserve dimension | Cost |
|---|---:|---:|---:|---:|
| Every `(q,u,0)` | 2 | 2 | 2 | 0 |
| Every `(q,q,0)` | 1 | 4 | 2 | 2 |

Appending this coordinate to the protected 2-by-2 block adds two coefficient words: 32 BF16 bits or 64 FP32 bits, excluding alignment/metadata and input-port bookkeeping. The layout must also provide the zero-filled D input slot and an A input capable of using that coordinate. If all A targets are zero there too, the reserve cannot change their outputs.

There are exactly N² admissible reserve endpoint pairs and N² distinct A-e3 signatures; from zero reserve, N²-1 signatures change. This is **4,261,347,841 BF16** or **18,302,910,352,054,026,241 FP32** pairs by proof, not pair-space execution. The nonzero witness `(0,0)->(1,2)` preserves D outputs and feedback states while changing A-e3 to `(1,2)`. At A-e1 every reserve choice remains silent. Two free coefficients here still yield an individual update of rank at most one.

Read exclusion applies to the protected arithmetic after pure validation of admitted banks. The Python validator does inspect the reserved words; identical host memory traces, timing and side channels are not claimed. This is a pure layout/budget evaluator, not a new live transaction protocol. It is not a general C1 compiler implementation or C4 backend certification.

## Counterexamples, transaction safety and review

The [counterexample catalog](P2_A4_Counterexamples.md) covers the requested zero/full-rank cases, local low ranks merging to full rank, conservative overfreezing, sample underprotection, storage constraints, target incompatibility, silent and responding edits, and ALG/BIT failures in both directions.

Two earlier numerical boundaries are retained as new A4 finite-family checks. In the two-endpoint thirds family `{0,Q}`, both endpoints are ALG-safe but only zero passes BIT on the complete domain including `eta*ones(3)`. In the full-rank split family `{I,I+eta E12}`, only I is ALG-safe but both pass BIT and differ at A-e2. The ideal-null commit `(2^p,0)+(1,-1)` also remains a refusal: its actual stored difference is `(0,-1)`, not the ideal proposal.

Live accepted edits and refusal/rollback tests use A3's unchanged trusted interface. Its certificate binds old/new raw endpoints, derived difference, complete domain and all sites, invariant, graph, numeric policy, expected version and serialized same-snapshot schedule. A4 reports do not authorize a commit. Tampered or stale records, omitted domains, unsafe endpoints and unsupported policies are refused with the complete prior snapshot unchanged.

Independent review used determinant/minor constraint oracles, separately implemented IEEE decoding/nearest-even selection, direct candidate execution and independent state recurrences. It checked every one of the 2,022 discrete candidates, rather than trusting certificate counts alone. No unresolved blocking contradiction remains within the stated contracts. Clarifications include accepted A-output domains for count bounds, E_cert versus general BIT, and arithmetic-only read exclusion. [Errata](P2_A4_Errata.md) preserves these without changing old evidence.

## Actual verification and cost

The main [verification_results.json](verification_results.json) completed all four sections with no unexpected failure. Seed is **20261114**; environment is Python **3.12.14**, NumPy **2.3.5**, Linux x86-64. The main observed elapsed time was approximately **34.889 seconds**, not a throughput or scalability claim.

| Route | Actual evidence |
|---|---|
| Exact algebra | **45,199 checks**; 2,304 exhaustive response instances and 6,912 rank-cap queries; 192 rank-attainment cases; 256 response-image dimension cases; 80 seeded rational cases; 12 expected refusals |
| Discrete endpoints | **6,864 checks**; 2,022 endpoints across 12 families; 38 live refusal/rollback checks; 48 seeded accepted-patch/feedback steps per format |
| Structural budget | **74,911 checks**; 1,728 exhaustive row-mask cases and 60 seeded cases; 29 explicit refusals; both layouts and both formats exercised |
| Capacity boundaries | **50 checks**; eight format-specific boundary cases and one exact target-relation construction |
| Independent review | 1,296 direct annihilator pairs; 256 target spaces; 4,096 prescribed responses; 40 seeded rational cases; all 2,022 endpoints; 4,096 mask reports from 512 independent null-vector enumerations; 98 structural pairs and 784 state/input/layout cases, plus transaction/numerical boundaries |

Structural scalar validation executes all **65,536 BF16 bit patterns**: 65,279 admitted words return themselves under the declared A scalar read and 257 are refused. That entails 65,279 software multiplies and adds each, not all N² pairs. The FP32 check covers **524** distinct boundary/seeded words, of which 521 are admitted and 3 refused; its **1,042 native scalar operations** are rationally audited. State tests cover 128 paired length-five traces and 640 paired ticks per format across the two layouts. Arbitrary finite-time protection still follows from the conditional invariant/induction argument, not the tested horizon.

The independent recorded run took approximately **12.679 seconds**. Different units and overlapping subjects are kept separate; counts are not pooled into a machine-proof or confidence score. No SMT query or Lean/Coq proof was run. Universal dimension/count/impossibility results are handwritten proofs, whereas endpoint enumerations and native probes have exactly the stated finite scope.

Exact budget construction uses rational rank, basis extension and linear solving; arithmetic bit lengths and reduction costs matter in addition to polynomial field-operation counts. Exhausting an alphabet of size a over m editable cells requires a^m candidates; each candidate incurs exact classification, complete protected execution, target evaluation and any certificate serialization/source checks. The enumerator refuses families above its explicit 10,000-candidate reference limit rather than pretending to scale to full-format banks. Full-format symbolic counts are supplied by proof where possible. The structural scalar scan is linear in the raw word count and is not a practical way to exhaust FP32 pairs.

Foreign-working-directory reproduction completed in approximately **35.898 seconds**. Its results and source hashes match the primary run after excluding only timing and timestamp metadata; all four standalone component records also match their aggregate counterparts under that rule. The driver correctly refused `-O` and `-OO` before attempting any section, preserving the primary result. These checks are recorded in [driver_checks.json](driver_checks.json). [final_integrity.json](final_integrity.json) binds final artifacts and verifies all **377** baseline prior files unchanged. Only the listed Git/cache/virtual-environment internals are outside that hash inventory; no repository operation or old-stage suite was performed.

## Remaining limitations and next starting point

There is no full classification of arbitrary floating observational equivalence classes or arbitrary program invariants. Storage masks, saturation, bias, graph choices, reachable domains and target sets can all change feasible counts. Tiny rounded-away edits are not evidence of robust task learning. General nonlinear learning benefit and long-term protected training remain open.

GPU, native BF16, general concurrent publication, arbitrary compiler optimization, adversarial private-runtime mutation and whole host-stack formal verification are not certified. CPU FP32 evidence concerns the operations actually performed. The structural fixture and reused A3 protocol do not complete later compiler or hardware stages.

B1 should begin with an explicit candidate-generation/selection question from the shared plan and preserve four separate capacity objects. Exact target compatibility must precede rank budgeting; actual endpoint feasibility and a supported execution certificate must follow generation. The full-rank BIT exception and saturated-bank ALG impossibility remain required regression boundaries. [P2_B1_Handoff.md](P2_B1_Handoff.md) saves these conditions. A4 stops here for coordinator review; no B1 execution has begun.
