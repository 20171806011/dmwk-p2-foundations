# P2-C1 plan — Capacity-aware compilation with protected and learnable regions

## Authorized scope and preservation

Implement only P2-C1 in this existing workspace. Earlier P1/P2 research and the publication repository are read-only. Inspect the B4 handoff, definitions/proofs, capacity/numerical analyses, counterexamples, evidence, review, actual primary/independent/reproduction records, completion and integrity; inspect necessary older interfaces without running their suites or optimizer histories. Record a new predecessor content/inventory baseline before implementation. Any predecessor issue receives a separate C1 erratum, never an overwritten old artifact. C2/C3/C4 remain future work.

## Ordered research work

1. **Dependency and scope audit.** Verify recorded B4 evidence and source bindings. Select an explicit finite Boolean synchronous-state-machine IR and bounded trusted front end. State legal inputs, initial states, outputs, reset/control semantics if supported, and the exact allowed compiler transformations. Reject unsupported language/policy requests.
2. **Proof checkpoint before implementation.** Define a structural shared-bank layout that reserves fixed deterministic coordinates and editable A coordinates. Specify input preparation, gate/call identities, activation and bias policy, physical sharing, state/output observations and serial scheduling. Prove source-to-graph correspondence, Boolean invariance, and global activation containment across every legal source state/input and gate call. Derive capacity and response feasibility under the layout. Specify the limited role of exact geometric analysis versus BIT authorization.
3. **Compile and validate.** Implement a small deterministic capacity-aware compiler emitting the physical layout, all calls, protected generators, writable mask, provenance/certificate and budget receipt. The trusted checker reconstructs from the complete source rather than accepting a generic externally asserted graph. Reject missing calls, unsupported transformations, insufficient budgets, incompatible task/response anchors and unproved numerical/domain premises.
4. **Integrate exact publication.** Separate source/graph compilation, candidate generation, stored-endpoint formation, endpoint verification and copy/check/publish. Bind source/IR/graph identities, parameters, domain/initial relation, numerical policy, all call sites, endpoints/version, D state, optimizer, counters, schedule and ledger. Accepted edits preserve only the declared D observations; rejection preserves the entire owned snapshot. Numerical/geometric diagnostics remain read-only unless separately certified under the exact gate.
5. **Main evidence.** Exhaust complete named small programs and finite legal state/input domains; add seeded properties and adversarial omissions, cross-region dependencies, bias/activation/state changes, stale/tampered records, capacity/response failures, storage saturation, subnormal/thirds/rounding and forbidden rotations/branches. Demonstrate at least one compiled source with actual nonzero A updates and loss/response changes while its D trace stays bitwise correct.
6. **Independent audit and reproducibility.** Use an independently implemented source interpreter and exact word/linear-algebra reference, not the main assertions. Review proof assumptions and failure paths. Reproduce new primary and independent verification from a different working directory. Separate finite cases, empirical native FP32, software BF16 and handwritten general proofs. Preserve B1's 21 BIT-equal ALG-failing refusals and dense FP32 AdamW's eight refusals with loss 5/2 by read-only evidence.
7. **Synthesis and stop.** Deliver English definitions, proofs, compiler specification/code, counterexamples, actual results, evidence map, review/report, README, integrity and C2 handoff. Record concrete unresolved boundaries. Do not publish or begin C2.

## Planned mathematical obligations

- A closed source language and complete compiler-owned call graph, with simultaneous old-state reads and synchronized next-state publication.
- A canonical finite encoding and exact fixed arithmetic graph; all D activations and fixed parameters remain in the proven exact gate domain.
- Full sharing and effects: matrix zero blocks alone are insufficient; inputs, biases, activations, state and observation interfaces must be separated as well.
- Capacity descriptors distinguish algebra dimension, per-update rank, low-rank families, finite stored endpoints, BIT classes and target responses. Unrestricted n(d-r) is not the size of a structural mask or a claim of useful learning.
- Requested target responses retain the relation condition X alpha in V implies R alpha=0. Storage and actual graph authorization are separate checks.
- New compiled layouts receive their own activation/invariant/graph proof; inherited numerical coefficients are not reused across layouts without proof.
- Safe updates use actual stored endpoint differences. Read-only perturbation bounds do not authorize exact-D publication; both execution roundings remain relevant to numerical comparisons.
- Only trusted serial copy-and-publish is considered; no concurrency, crash or hostile-memory guarantee.

## Evidence and costs

Use fixed seed 20261114. Record exact program/endpoint/trajectory case counts, accepted/rejected compile and update counts, refusal causes, dimensions/ranks, actual A loss/response, D word comparisons, wall time and environment. Validate types and word-level rounding. Avoid treating sampled spans, a finite run, SMT on a bounded formula or an exact-arithmetic reference as a general machine proof. GPU, native BF16, arbitrary FMA/reassociation/compiler optimization, full-host proof and universal learning remain unverified.

## Literature boundary

If an original-source search is available, verify GPM and OGD titles, years, sources and limited projection claims. Keep prior projection ideas separate from this stage's bounded compiler/verification contract. Unavailable literature access must not block the main work; do not invent citations, novelty or performance advantages.

## Expected deliverables

`P2_C1_Definitions.md`, `P2_C1_Theorems.md`, `P2_C1_Compiler.md`, `P2_C1_Counterexamples.md`, implementation modules, `verify_c1.py`, `verify_independent.py`, actual primary/independent/reproduction JSON, `P2_C1_Evidence_Map.md`, `P2_C1_Review.md`, `P2_C1_Report.md`, `README.md`, dependency/completion/integrity records and `P2_C2_Handoff.md`. Names may be refined within this directory; only actual files will be reported.
