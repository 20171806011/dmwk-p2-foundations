# P2-A4 — Independent mathematical and executable review

## Disposition and scope

The reviewed A4 results are consistent within their stated contracts. No blocking error remains in the mathematical statements or in the tested reference interfaces. This is a conditional research review, not a certification of an arbitrary learner, compiler, hardware backend or concurrent runtime.

The review read the A4 plan, mathematical checkpoint, definitions, theorem proofs, algebra/discrete/structural implementations and the root boundary verifier. It consulted the A3 handoff and required interfaces read-only. No prior-stage verification suite was run and no prior-stage artifact was edited. The mathematical checkpoint preceded implementation. The final independent run passed on the frozen implementation sources; its source digests and environment are recorded in [review_results.json](review_results.json).

## Mathematical review

| Claim family | Independent reasoning and qualifications |
| --- | --- |
| T1: dimension, rank and attainment | An annihilator is precisely a linear map on the quotient of dimension `c=d-r`; hence its dimension is `n*c` and its rank is at most `min(n,c)`. Basis extension attains every allowed rank. Setting `G=Delta` establishes the stated generator-cap converse. This requires freely chosen exact coefficients, not a stored endpoint at an arbitrary old bank. The rank-constrained subset is generally not linear. |
| T2: protection growth and sharing | Vanishing on a larger subspace imposes additional linear equations. Shared sites require the sum of their spaces. Exhaustion iff full rank describes the unrestricted annihilator; a zero rank cap or additional masks can exhaust earlier. BIT monotonicity requires inclusion of actual protected contexts with the same graph, observations, old bank, numerical policy and endpoint family. Span inclusion alone is insufficient for BIT. |
| T3: prescribed responses | The necessary and sufficient condition is `ker(pi X) subset ker(R)`. It makes the induced map on `im(pi X)` well-defined. Extending that map by zero on a complementary quotient subspace gives rank exactly `rank(R)`, which is also a lower bound for every implementing update. This establishes feasibility under the cap precisely when the relation condition and `rank(R)<=k` both hold. The image dimension `n*s` and silent dimension `n*(c-s)` follow by restriction and rank-nullity. A nonzero silent map under a cap additionally needs `k>=1`. |
| T4: finite counts | Projection onto a nonsingular set of `q` affine-subspace coordinates is injective, so an alphabet of size `N` yields at most `N^q` endpoints. This proof does not assume all projected tuples extend to representable endpoints. Exact response counts are bounded by the endpoint count. The raw-output alphabet bound also requires accepted finite A executions, or an explicitly different failure alphabet. |
| T5: storage obstruction | At a row `(Fmax,Fmax)`, preservation of the exact sum forces each new entry to equal `Fmax`, despite positive annihilator dimension. The protected input `(1/2,1/2)` has finite exact products and sum, so the example does not depend on an overflowing baseline. At a zero old row the same equation permits exactly `(a,-a)` for every canonical finite `a`. These are ALG counts; they do not classify all BIT endpoints. |
| T6: ALG and BIT are not nested | Rounded thirds annihilate the exact protected line but leak on the smallest-subnormal activation under the fixed separate-rounding graph. Conversely, a stored subnormal off-diagonal change is invisible on a declared finite full-rank protected domain while visible at an A basis input. Even a rank-two effective BIT change can exist when the protected complement has dimension one. No annihilator rank bound applies to that non-ALG edit. |
| T7: masks and reservations | For each row mask, direct restriction gives nullity `|J_i|-rank(H[J_i,:])`. Applying the quotient argument on that restricted coordinate space gives the claimed target-response dimension. Arbitrarily independent reserved columns require every protected vector to be zero on those columns. A non-coordinate geometric complement does not imply such independently writable columns exist. |
| T8: finite structural family | The admitted `2 x 3` layout fixes the first two columns and varies the third. The protected arithmetic graph excludes that column; its admitted validator is pure and total. The A `e3` observer returns the two stored values exactly, so its response signature is injective and there are `N_F^2` signatures. This is a small specified graph/layout construction, with no new live commit authorization or general compiler theorem. |

The canonical-basis observation corollary in T4 is also valid under its explicit zero-bias, full-output, ordered separate-RNE graph. At `e_j`, each output row has just one possibly nonzero product; its stored word survives products by one and additions of canonical zero. Therefore observing all basis inputs distinguishes every stored bank. Protecting those actual inputs forces a singleton BIT class. This does not extend to an arbitrary full-rank finite input set, nonzero bias, nonlinear observations or another graph.

The root [boundary verifier](verify_boundary_cases.py) was reviewed independently at the level of its fixtures and formulas. In particular, its quotient-target relation, full-rank BIT/non-ALG example, maximum-endpoint obstruction and effective-commit leakage use the same hypotheses as the proofs. The independent script below supplies separate direct-equation and rounding checks for these boundary mechanisms; it does not import that verifier's assertions.

## Clarifications incorporated before final delivery

The review identified precision requirements rather than a need to weaken the core quotient theorems:

- Target-response signatures count only accepted finite A executions. Failed A executions are recorded separately. Exact rational response values are not assumed to belong to the target-format alphabet.
- Full-rank exhaustion is a statement about unrestricted ALG maps. It is not an exhaustion theorem for arbitrary finite-domain BIT edits. A rank cap of zero, masks or storage can exhaust capacity earlier.
- The discrete producer uses the inherited A3 certificate route. Its `E_cert` alias and metadata now identify this explicitly. For the named supported registries, admitted baseline and enumerated candidate alphabets, the independent direct-output oracle confirms equality with the local BIT predicate on every enumerated endpoint. This equality is not asserted for unsupported programs or arbitrary proof checkers.
- The structural endpoint validator inspects all entries. Read exclusion therefore applies to the protected arithmetic graph after pure, total validation on admitted banks, not to the complete Python memory-access trace, branching behavior or timing. The `global_provenance_verified` diagnostic remains Boolean false; a separate layout-domain metadata field records the declared fixture provenance.
- Full-format cardinalities obtained by proof are kept separate from finite endpoint enumerations and single-coordinate tests. Positive algebraic dimension is not labeled a dimension of a finite endpoint set.

No predecessor error requiring modification of A1–A3 was found. The effective-endpoint distinction, complete-domain requirement and fixed-graph acceptance boundary remain unchanged.

## Independent executable evidence

[verify_review_checks.py](verify_review_checks.py) does not import a production verification module or prior-stage test suite. It compares production APIs against the following distinct mechanisms:

1. Exact ranks use recursive determinants and nonsingular-minor row-basis selection, rather than the producer's Gaussian elimination.
2. Response feasibility is checked by direct row-space consistency of the equations `Delta[H X]=[0 R]`; successful constructions are checked by direct exact products and minimum rank. Impossible-response witnesses are checked independently.
3. BF16/FP32 words are independently decoded as exact fractions. Each rounded operation uses binary search over ordered positive finite words with nearest-even tie resolution and explicit finite overflow boundaries. This does not call the inherited rounding implementation.
4. Candidate stored endpoints are independently classified by decoded effective differences, complete declared protected call operands, ordered rounded outputs and raw A response signatures. Producer group counts, ranks and response-image counts are compared endpoint by endpoint.
5. Row-mask dimensions and response dimensions are checked by enumerating direct small-coordinate null solutions and taking their independent spans.

The final standalone run started at `2026-11-14T07:27:03.015126+00:00`, passed in `12.67862760799835` seconds, and produced the following actual coverage. These are case counts, not a universal proof count and not a count of every internal assertion.

| Independent coverage | Actual count |
| --- | ---: |
| Binary `2 x 2` protected generator matrices | 16 |
| Direct generator/update pairs using 81 ternary updates each | 1,296 |
| Target-space sweeps | 256 |
| Prescribed binary response matrices checked | 4,096 |
| Seeded rational/rectangular cases, seed `20261114` | 40 |
| Named finite endpoint families across BF16 and FP32 | 12 |
| Stored endpoints independently classified and compared | 2,022 |
| Binary `3 x 2` protected generator matrices for mask checks | 64 |
| Independent single-row mask solution enumerations | 512 |
| Two-row mask reports compared | 4,096 |
| Structural boundary endpoint pairs, both formats combined | 98 |
| Structural state/input/layout cases, both formats combined | 784 |

Both formats produced the same counts for the following restricted `2 x 2` candidate alphabets. These are not full-format endpoint counts.

| Alphabet | Protected model | Candidates | ALG | BIT / checked certificate set | Joint |
| --- | --- | ---: | ---: | ---: | ---: |
| `{-1,0,1,2}` | duplicate feedback | 256 | 16 | 16 | 16 |
| `{-1,0,1,2}` | split feedback | 256 | 1 | 1 | 1 |
| `{-1,0,1,2}` | shared axes | 256 | 1 | 1 | 1 |
| `{0,eta,1}` | duplicate feedback | 81 | 4 | 16 | 4 |
| `{0,eta,1}` | split feedback | 81 | 1 | 2 | 1 |
| `{0,eta,1}` | shared axes | 81 | 1 | 1 | 1 |

Here `eta` is the format's smallest positive subnormal. The listed A observers include all standard basis inputs, which explains why the raw-response image distinguishes every accepted endpoint in these families. This is the restricted graph corollary, not a general assertion that endpoint capacity equals task-response capacity.

For each format, an independently checked nonzero stored safe patch changes A output and preserves eight paired feedback transitions. Five transaction failures preserve the complete protected snapshot: stale replay, omitted call sites, observed-sample coverage substituted for the complete domain, altered numerical policy and altered schedule. In addition, the thirds/subnormal and actual-commit leakage proposals are refused. For the latter, an ideal null increment `(1,-1)` at the row `(2^p,0)` commits to an effective row change whose exact protected residual is `-1`, and the independently rounded protected output changes by `-1`. These checks retain the A3 trusted API and serialized publication assumptions.

The structural full-format pair counts, `4,261,347,841` for BF16 and `18,302,910,352,054,026,241` for FP32, are counting-theorem values. The independent reviewer executed only 49 selected boundary pairs per format, including zero, signed smallest subnormals, signed one and signed maximum finite values. No exhaustive enumeration of those pair spaces is claimed.

## Reproduction and remaining boundaries

Run the independent review alone with:

```sh
python -B /workspace/p2_a4/verify_review_checks.py
```

To retain the recorded result and write a new run elsewhere:

```sh
python -B /workspace/p2_a4/verify_review_checks.py --output /tmp/p2_a4_review_results.json
```

The JSON binds the five executed local source files by SHA-256 and fails if they change during a run. It records the actual environment and the read-only dependency provenance supplied by the runtime adapter. The source-hash binding is an evidence aid, not a cryptographic authorization protocol.

The independent floating oracle is software exact arithmetic for the declared BF16/FP32 semantics. It does not certify native BF16, GPU behavior, arbitrary FMA/reassociation, flush-to-zero modes or arbitrary backend optimizations. Any native CPU observations in other A4 results remain separately scoped evidence. There were zero SMT queries and no Lean/Coq proof check in this independent review. The universal theorems remain explicit handwritten proofs. General concurrency, malicious host mutation, unsupported certificate routes, full P2-C composition and learning-task improvement remain outside the established results. A changed legal A output demonstrates response capacity, not useful learning performance.

## Final synthesis audit

A subsequent read-only audit examined `P2_A4_Report.md`, `README.md`, `P2_B1_Handoff.md`, `P2_A4_Evidence_Map.md`, `P2_A4_Counterexamples.md`, the aggregate result and `driver_checks.json`. Counts, capacity distinctions, reproduction scope and the next-stage stopping boundary were consistent with the recorded evidence. No tests were rerun for this document audit. The driver record reports matching non-timing scientific results and source bindings from the foreign-directory reproduction, component-to-aggregate agreement, and expected refusals under both Python optimization modes.

Two wording corrections were requested and incorporated: the opening report now describes a nonzero **A-target response preserving D**, and the evidence map attributes the maximum-endpoint neighboring-candidate residual probe to `boundary_results.json` rather than to the independent verifier. The independent verifier's maximum-endpoint check covers the displayed word and finite baseline execution. No synthesis blocker remains within the stated assumptions. Final integrity and completion manifests are separate subsequent delivery records; this audit does not infer their existence or success.
