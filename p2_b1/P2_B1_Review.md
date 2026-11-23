# P2-B1 — Independent mathematical, optimizer and transaction review

## Disposition

No blocking inconsistency was found in the reviewed B1 theorems, reference implementation or executed fixtures under their stated assumptions. The result is a conditional candidate-and-publication mechanism, not universal learning progress, a nearest safe endpoint solver, a concurrent transaction system or a certified hardware backend.

The reviewer read the saved plan and mathematical checkpoint before implementation, reviewed the interface while implementation was underway, and reviewed the final definitions and T1–T6 proofs against `constrained_updates.py` and `optimizer_kernel.py`. The A4 handoff and necessary predecessor interfaces were read-only dependencies. No predecessor file was edited and no predecessor verification suite was imported or run.

The independent verifier ran after the producer sources and training result were frozen. [independent_results.json](independent_results.json) records a successful run starting at `2026-11-14T08:00:37.571438+00:00`, lasting `2.9748651509980846` seconds. Its hashes bind the executed implementation and verifier sources and the exact producer training log replayed. The elapsed time is a local observation, not a performance comparison.

## Mathematical and architecture audit

| Claim | Review and necessary qualification |
| --- | --- |
| T1: Frobenius projection | Annihilation plus a residual whose rows lie in the protected space uniquely characterizes the orthogonal projection. Symmetry and idempotence give the range, norm and nearest-point claims. The rational statement uses the real Euclidean norm and a rational minimizer. This projection is onto an exact linear space, not onto the finite BIT class. |
| T2: nullspace and low-rank parameterization | With `N` a basis of `V-perp`, `N^T` is onto the coordinate space, so `rank(Z N^T)=rank(Z)` and the coefficients are unique. The Gram inverse is needed for orthogonal projection when `N` is not orthonormal. The low-rank factorization covers the stated exact family but supplies no storage or execution guarantee. |
| T2(a–b): optimization metric and rank contract | Plain coordinate SGD induces `g N N^T`, which differs from the Frobenius projected gradient unless the coordinate metric is adjusted. A cap on each increment, a cap on accumulated change and a cap on a persistent adapter are distinct. The given rank-one diagonal examples correctly demonstrate accumulation and successive-adapter differences of rank two. |
| T3: optimizer closure | Scalar exact combinations preserve the fixed annihilator. The momentum iff is correctly restricted to an already-safe gradient and nonzero old-state coefficient; arbitrary unsafe terms may otherwise cancel. Global common-scalar clipping preserves the space, whereas coordinate scaling and clipping need not. Decay must be included before the final restriction unless separately proved safe. The ideal Adam example demonstrates failure before finite-format rounding. |
| T4: effective endpoints | The identity `Delta_eff=D+S` isolates commit rounding. Its residual on the protected space is `S h` when the ideal direction annihilates that space. This correctly separates candidate geometry, actual ALG membership and complete rounded BIT equality. The two implications between ALG and BIT both remain false in general. |
| T5: combined publication | Proposal computation, certification, record comparison, replacement-bank allocation and receipt allocation precede one owner-bank assignment. Full-snapshot binding includes q/ticks, preventing a later commit from restoring earlier D state. Failed preparations or commits retain moments and optimizer time as well as weights and protected state. Induction over supported finite events still needs the complete-domain/interface assumptions. |
| T6: new structural model | The two declared sites use `(q,q,0)` and `(u,u,0)` for all Boolean q/u. Immutable identity columns return the complete bit-pair outputs and the fixed same-snapshot XOR recurrence is closed. Third-column changes are excluded from protected arithmetic and visible at A input `e3`. Its new descriptor and owner are explicitly verified; A4's old pure layout is not treated as prior live authorization. |

The final definitions distinguish the true global activation span `V_exact` from a proved containing working space `V=col(H)`. Projection, nullspace and rank statements use that same working space. This avoids silently claiming that a conservative generator describes the exact attainable capacity.

The implementation's default `ALG_AND_BIT` and its explicit `BIT` option are different contracts. The full-rank tiny edit is accepted under BIT and refused under the joint condition. The API does not silently downgrade a rejected claim. Algebraic rank bounds are not applied to BIT-only edits.

The trusted caller may issue arbitrary coherent candidates. Public hashes are not signatures or a historical request registry. Inconsistent and stale records fail complete recomputation; a coherently reissued, currently bound and safe request can be a newly authorized request. The proof and code now state this distinction. Protection does not depend on pretending that an unkeyed checksum authenticates original intent.

## Independent methods

[verify_independent.py](verify_independent.py) imports the candidate and kernel APIs but no producer verifier or old-stage test module. It does not reuse their assertion logic.

- Projection is checked by direct exact annihilation and residual-span equations. Ranks are computed by determinant/minor selection, rather than the producer's elimination routine. These equations identify the unique orthogonal projection without invoking the producer projector as the reference answer.
- BF16, FP32 and host binary64 values are independently decoded from exponent/significand words. Rounding selects neighboring positive words by binary search and resolves nearest-even ties by exact rational distances. The square-root reference compares exact input values with squared midpoints between adjacent binary64 candidates.
- Optimizer references reconstruct each moment, parameter step, decay, clipping scalar, final restriction and staged state in the specified order. The tested Adam coefficients and step ranges have exactly representable dyadic bias-correction powers. This is no proof that arbitrary platform `pow` or `math.sqrt` is universally correctly rounded or reproducible.
- Every recorded training attempt is replayed from the initial endpoint using an independently derived gradient of the stated continuous linear extension. The replay independently rounds the candidate, decodes the effective difference, checks exact rank/annihilation, executes all protected input cases, computes raw A outputs and exact losses, decides the selected joint acceptance predicate, and advances or retains optimizer state accordingly.
- Additional live API tests mutate staged next moments and step counts, configuration and implementation metadata, candidate/request fields and schedule bindings. They check full-snapshot equality after refusal. Caller-owned configuration reinitialization and returned-record mutations are separately checked for alias isolation.

The optimizer fixture substream uses deterministic seed `20261115`, derived as base seed `20261114 + 1`; the algebra substream uses `20261114`. The recorded training log uses the producer's fixed `20261114` input sequence. Both seed choices are explicitly recorded rather than described as a single hidden random stream.

## Actual independent coverage

| Finite evidence | Actual coverage |
| --- | ---: |
| Binary `3 x 2` protected generator matrices | 64 |
| Projection instances checked by direct equations | 512 |
| Nullspace instances checked by exact null products and rank | 512 |
| Low-rank constructions checked by direct projection equations and rank bounds | 512 |
| Ordered optimizer proposals | 144, comprising 48 each for SGD, momentum and AdamW |
| Producer optimization runs fully replayed | 24 |
| Training attempts fully reconstructed | 192 |
| Protected contexts compared across proposed and actual training endpoints | 1,536 |
| Accepted joint-safe optimizer commits in replay | 75 |
| Joint-contract refusals in replay | 21 |
| Offline applications in replay | 96 |
| Additional live API refusals retaining the full snapshot | 58 |
| Additional direct complete-domain context probes | 22 |

The 144 optimizer proposals cover four restrictions (`none`, gradient-only projection, final projection and final structural mask), three clipping modes, and nonzero supplied moment state. The finite moment comparison includes both clipped and unclipped raw directions. These checks are not pooled into a universal proof count or a confidence score.

All 21 replayed joint refusals pass the independent registered-domain BIT predicate and fail exact annihilation of the actual endpoint difference. They are refusals under the deliberately stronger ALG_AND_BIT contract, **not observed D corruption**. The replay confirms that rejected attempts do not advance optimizer state; the subsequent legal protected tick is a separate event.

All recorded A outputs and exact losses agree with the independent replay. In particular, both formats' dense projected SGD accept eight steps and end at loss `5/131072`; structural SGD reaches loss zero on this small target. The replay also confirms stalled dense FP32 AdamW under the joint policy, not impossibility of BIT-safe optimization. An accepted zero weight change is distinguished from a new functional response. These finite results do not establish useful learning on other objectives, convergence or comparative optimizer performance.

The additional live tests exercise duplicate and structural models with nonzero first moments already published. They compare full candidate generation and staged state, confirm preparation is pure, reject staged next-state alterations even with a recomputed public envelope checksum, reject owner reinitialization, reject replay after publication or after a D tick, and reject optimizer-induced endpoint overflow without state advancement. A separate full-rank split-domain edit demonstrates BIT acceptance, exact ALG failure and joint refusal on the same stored endpoint. Accepted AI updates preserve optimizer state.

Independent numerical boundary checks in both formats retain:

- Ideal null increment `(1,-1)` at old row `(2^p,0)`, whose stored effective protected residual and output change are `-1`.
- A stored rounded-thirds exact annihilator whose ordinary basis output is zero but whose legal smallest-subnormal activation output consists of raw word `1`.
- A duplicate-domain BIT edit with exact effective rank two even though the algebraic complement has dimension one.

Three exact epsilon choices additionally check the ideal Adam non-closure formula, and coordinate clipping of `(2,-1,-1)` gives protected residual `-1`. The general counterexample proofs remain separate from these executed instances.

## Review findings and retained boundaries

Pre-code review requested explicit global-space identity, the restricted momentum iff, complete optimizer-state rollback, full q/tick snapshot binding and a separate proof for the new structural registry. These are present in the final definitions, proofs and implementation.

Implementation review additionally required the caller-owned optimizer configuration to be cloned, returned records to be detached, the default joint claim to match the interface, and coherent-request authenticity claims to be narrowed. Direct alias and mutation probes passed. The literal host power/square-root behavior is now documented as proposal arithmetic with a platform boundary, not as an automatically certified IEEE basic-operation theorem. A temporary producer caller/API return-shape mismatch was corrected before the successful producer run; it did not require modifying predecessor evidence. No production defect was exposed by the final independent run.

The new structural validator reads the reserved entries. Read exclusion applies only to protected arithmetic after total, side-effect-free validation of admitted banks; full Python instruction traces and timing are not protected. The complete-bank publication result assumes the trusted serialized owner, no concurrent/private mutation and no process failure. Fixed counters can exhaust and cause refusal, so safety is not an unlimited-progress guarantee.

The independent verifier performs software exact/reference calculations; the production protected FP32 operations are separately audited local CPU scalar operations, while BF16 uses software RNE. No GPU, native BF16, arbitrary compiler fusion/reassociation, distributed or concurrent publication, crash consistency, whole-host formal verification or unrestricted A-to-D feedback is certified. No SMT query or Lean/Coq proof was run. T1–T6 remain handwritten conditional proofs.

## Reproduction

```sh
python -B /workspace/p2_b1/verify_independent.py
```

To keep the recorded result unchanged:

```sh
python -B /workspace/p2_b1/verify_independent.py --output /tmp/p2_b1_independent_results.json
```

The default output is `independent_results.json`. The run refuses optimized Python modes and checks that its bound sources and replayed producer result remain unchanged while it executes. The source/result digests are evidence bindings, not authorization secrets. This review completes B1 only; B2 remains a saved handoff.

## Final synthesis audit

A subsequent read-only audit covered the Report, README, Evidence Map, Counterexamples, B2 Handoff, aggregate driver and `driver_checks.json`. The stated theorem scope, 75/21/96 training outcomes, independent case counts, distinct seed substream, complete-domain coverage and B2 stopping boundary match the recorded evidence. The report's momentum summary was qualified to the already-projected-gradient recurrence with a nonzero old-state coefficient, avoiding an unconditional necessity claim where unsafe terms could cancel.

The driver record reports main and independent reproductions from `/tmp` in the same dependency environment, with every non-timing scientific result and source binding unchanged. It also records component-to-aggregate agreement and preflight refusals in both optimized Python modes. This is foreign-directory reproduction, not a clean-room installation or cross-platform certification. No scientific test was rerun for this synthesis audit. No documentary blocker remains within the stated contracts. Final completion/integrity manifests are separate subsequent records and are not inferred by this note.
