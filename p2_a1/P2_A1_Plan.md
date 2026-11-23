# P2-A1 research plan

Status: completed for the stated P2-A1 scope; subsequent stages are not started. The plan below was saved before derivation and implementation.

## Objective and frozen boundary

Define the complete activation set and its exact linear span for every fixed shared deterministic weight matrix, ranging over all admitted initial states, legal input histories, call sites, and finite execution times. Establish when a nontrivial complement exists, and distinguish exact reachability, sound superspaces, and sample-only estimates.

Continue in `/workspace/p2_a1` within the existing research workspace. Treat the published P1 reference in the sibling `dmwk-p1-foundations` directory as a read-only dependency. Read only necessary compiler/execution interfaces; do not rerun P1 suites, change P1 delivery files, recreate a repository, publish, or implement P2-A2.

## Work sequence and deliverables

1. **Definitions.** Specify fixed D, numerical/execution policy, legal encodings, initial states, legal-input histories or a finite environment monitor, deterministic scheduling, same-snapshot state updates, and call-event semantics. Fix rational and real scalar fields, numeric decoding of finite float words, affine homogenization, and the common physical coordinate frame for shared calls. Save `P2_A1_Definitions.md`.
2. **Derivation.** Prove existence and finite dimension, rational/real rank agreement, call-site union/sum and monotonicity, finite-state reachability and termination under explicit finite/decidable assumptions, and sound invariant-space construction under a specified operation family. Treat nonlinear/rounded transitions separately; do not assume their linearity. Prove full-rank and rank-deficient examples, affine-span subtleties, and finite-sample insufficiency. Save `P2_A1_Theorems.md`.
3. **Implementation.** Build exact rational rank/basis computation, finite-state reachability with recorded calls, common-coordinate sharing, and a checked affine invariant-hull construction. Connect a small actual P1 compiler graph through its supported interface where feasible. Save `activation_spaces.py` and `verify_activation_spaces.py`; no weight-patch application or P2-A2 implementation.
4. **Counterexamples and experiments.** Use a fixed seed and explicit exhaustive domains. Cover delayed unseen directions, pointwise versus shared rank, repeats/zero activations, legal-input/reset changes, affine bias augmentation, nonlinear failure of a naive linear closure, and real null-product versus finite-precision bit changes. Record software BF16 separately from native scalar CPU FP32. Save actual `verification_results.json` and any small machine-readable certificates needed for reproduction.
5. **Independent review and correction.** Review hidden assumptions, validity of invariants, arithmetic semantics, all-time versus sampled claims, complexity, and dependency provenance. Fix and rerun affected checks only. Separate handwritten proofs, exhaustive model checks, any bounded SMT, and random sampling; never label absent machine proofs as completed.
6. **Synthesis.** Save `P2_A1_Report.md`, an evidence map, and a precise stop-state record. Report dimensions/examples, cost, limitations, open problems, dependency hashes, and reproduction commands. Stop after P2-A1 and wait for the user; do not begin P2-A2.

## Acceptance criteria

- A mathematically precise activation set over all legal finite prefixes, with a separate merged space for each physically shared matrix.
- A finite dimensionality argument that does not mistake a finite floating-point set for a vector space.
- Complete proofs for claimed span or invariant containment, including the exact closure operation family and its applicability conditions.
- Both full-rank and non-full-rank deterministic examples; explain how sharing, bias, legal inputs, and compilation can remove apparent freedom.
- An exhaustive small finite-state/reference-compiler check and an explicit finite-sampling counterexample.
- Exact rank arithmetic, true observed test results, reproducible commands, and no claim of GPU/native-BF16 or Lean/Coq certification.

## Initial evidence status

No P2-A1 directory or earlier P2 plan was found before this plan was created. P1 publication is an existing completed result, not a prerequisite task to repeat. No P2 result is assumed from the plan itself.

## Recorded outcome and stop point

All six planned work steps have a corresponding deliverable. The main verifier passed 2,533 checks; a foreign-working-directory rerun produced identical stage records and source hashes. Independent review exhausted 512 binary 3x3 rank cases and documented the resolved registry, invariant-family and evidence-labeling gaps. The theorem documents retain conditional execution assumptions and open scalability/backend/formalization boundaries. No SMT or proof-assistant result was added, no P1 suite was rerun, and no P2-A2 code or publication action was performed. Continue only after a new user instruction.
