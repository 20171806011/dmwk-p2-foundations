# DMWK P2-B3: nonlinear and finite-time perturbation propagation

B3 proves conditional propagation bounds for fixed old/new stored endpoint banks, shared affine/ReLU networks and synchronous state maps. It proves intermediate-domain containment together with the error recurrence. It does not turn a numerical budget into permission to modify a deterministic program.

For exact maps and two separately rounded executions, the main recurrence is

\[
E_{k+1}\le L_k E_k+a_k+\rho_k+\rho'_k.
\]

Here `E0` comes from the admitted initial-state **pair relation**, `a` bounds the actual endpoint difference at the same input, and the two `rho` terms bound old/new execution separately. The nonhomogeneous product-sum is proved for arbitrary finite depth/time. A uniform contraction bound additionally requires a joint invariant and uniform all-time premises. See [Report](P2_B3_Report.md), [Definitions](P2_B3_Definitions.md), [Theorems T1–T8](P2_B3_Theorems.md) and the [Evidence Map](P2_B3_Evidence_Map.md).

The concrete reference uses exact rational infinity-norm bounds, canonical finite BF16/FP32 words, nearest-even rounding, gradual underflow and bias-first ordered separate multiply/add. BF16 is software; FP32 uses local NumPy scalar operations audited against exact RNE. ReLU/identity are explicit. The implementation admits at most 32 calls per graph and recurrent horizons 0–64; these are reference limits, not limits of the mathematical induction.

## Recorded evidence

The currently saved producer records all pass with zero unexpected failures. These counts measure finite assertions, not proved theorems or a count of all legal raw inputs.

| Record | Checks | Expected refusals | Recorded elapsed time |
|---|---:|---:|---:|
| [Propagation](propagation_results.json) | 2,103 | 6 | 10.305082273 s |
| [Control/rounding](control_results.json) | 1,578 | 28 | 4.078897967 s |
| [Read-only receipts](certificate_results.json) | 498 | 128 | 9.478728363 s |

Propagation includes 324 complete histories of length 3 over `{-1,0,1}` across 12 declared endpoint/format/initial-relation families, 96 seeded length 6 histories, 36 two-layer points, 16 retained floating-boundary executions and one exact target-relation record. Control evidence includes 324 complete small guard-pair executions, 48 seeded guard cases with 240 pair executions, and named branch/rounding counterexamples. Receipt evidence includes 44 registered cases, 46 rehashed inconsistent-record cases, 8 seeded endpoint receipts and 2 B1 rollback checks with nonzero optimizer moments.

[Independent verification](independent_results.json) also passed in 39.415879754 s. It used separate exact word decoding/RNE, direct product-sums, interval reconstruction and paired trajectories. Its scope includes 5,655 complete recurrence/initial-value cases, 180 constant envelopes, 1,944 named initial-pair/history cases, and separate network, guard, receipt and rollback checks. Its counts are different evidence units, not an additional universal-theorem count.

[Aggregate verification](verification_results.json) passed all 3 sections in 27.699216039 s and confirmed all 699 predecessor artifacts unchanged before/after execution. Its section counts match the saved producer records. [Driver checks](driver_checks.json) confirm successful reproduction from `/tmp`: main 26.186360291 s and independent 38.071814596 s. All five scientific comparisons matched after excluding only explicitly listed timestamps/durations; source identities, environment, refusal reasons and scientific values were retained.

The driver also verified intentional `-O` and `-OO` preflight refusals, each with exit code 1 and zero attempted scientific sections. These recorded refusals protect verification from disabled assertions; they are not failed scientific runs.

Universal box/tube claims come from the conditional proofs and the validated domain/range witnesses. Finite enumeration covers only the named alphabets, initial pairs and horizons. A sample maximum, original-only activation collection or fitted low rank supplies no modified-trajectory guarantee.

## Reproduce in the existing workspace

Recorded environment: Python 3.12.14, NumPy 2.3.5, Linux x86_64. The dependency pin is in [requirements.txt](requirements.txt). This directory uses read-only sibling P1/P2 implementations and integrity baselines; copying only `p2_b3` is insufficient. Keep the archived workspace layout, including `/workspace/dmwk-p1-foundations` and the predecessor directories indexed by [dependency_baseline.json](dependency_baseline.json).

Use a fresh output directory, without `-O` or `-OO`:

```bash
B3_REPRO_DIR=$(mktemp -d /tmp/dmwk-p2-b3-repro.XXXXXX)
cd "$B3_REPRO_DIR"
python -B /workspace/p2_b3/verify_b3.py --output "$B3_REPRO_DIR/main.json"
python -B /workspace/p2_b3/verify_independent.py --output "$B3_REPRO_DIR/independent.json"
```

The main runner invokes only new B3 suites. It checks predecessor content/inventory and current source identities before/after execution. The independent runner uses its own exact word decoding/RNE and propagation/interval references rather than producer test assertions. Runtime, timestamps and execution-cost fields vary; scientific records must be compared with the stated reproduction exclusions. If creating a separate Python environment is necessary, install only the declared dependency there using `python -m pip install -r /workspace/p2_b3/requirements.txt`; do not modify archived environments or stage artifacts.

## Artifact index

| Purpose | Files |
|---|---|
| Saved plan and derivation order | [Plan](P2_B3_Plan.md), [Mathematical checkpoint](P2_B3_Mathematical_Checkpoint.md) |
| Definitions, proofs and synthesis | [Definitions](P2_B3_Definitions.md), [Theorems](P2_B3_Theorems.md), [Report](P2_B3_Report.md), [Evidence map](P2_B3_Evidence_Map.md) |
| Numerical method and counterexamples | [Numerical analysis](P2_B3_Numerical_Analysis.md), [Counterexamples](P2_B3_Counterexamples.md) |
| Review, corrections and next-stage boundary | [Review](P2_B3_Review.md), [Errata](P2_B3_Errata.md), [B4 handoff](P2_B4_Handoff.md) |
| Core interface and implementation | [B3_Interface.md](B3_Interface.md), [propagation_bounds.py](propagation_bounds.py), [b3_runtime.py](b3_runtime.py) |
| Control-flow scope | [Control flow](P2_B3_Control_Flow.md), [control_flow.py](control_flow.py) |
| Read-only receipt design, specification and implementation | [Certificate design](B3_Certificate_Design.md), [Certificate specification](P2_B3_Certificate_Spec.md), [propagation_certificate.py](propagation_certificate.py) |
| Main and independent entry points | [verify_b3.py](verify_b3.py), [verify_independent.py](verify_independent.py) |
| Aggregate and independent actual results | [verification_results.json](verification_results.json), [independent_results.json](independent_results.json) |
| Foreign-directory reproduction and comparisons | [reproduction_results.json](reproduction_results.json), [independent_reproduction_results.json](independent_reproduction_results.json), [driver_checks.json](driver_checks.json) |
| Intentional optimized-interpreter refusals | [optimized_O_refusal.json](optimized_O_refusal.json), [optimized_OO_refusal.json](optimized_OO_refusal.json) |
| Producer suites and actual output | [verify_propagation.py](verify_propagation.py), [propagation_results.json](propagation_results.json); [verify_control.py](verify_control.py), [control_results.json](control_results.json); [verify_certificates.py](verify_certificates.py), [certificate_results.json](certificate_results.json) |
| Dependency provenance | [dependency_inspection.json](dependency_inspection.json), [dependency_baseline.json](dependency_baseline.json), [requirements.txt](requirements.txt) |

The baseline contains 699 preceding files, including original loose P1 directories, the publication worktree and root P1 summaries. Its scope excludes `.git`, virtual environments and caches. Initial inspection, aggregate checks and the final driver content/inventory checks all passed. These integrity results describe the recorded baseline scope rather than a new exhaustive audit of every old proof.

## Boundaries retained

[completion_status.json](completion_status.json) records the scoped B3 delivery status. [final_integrity.json](final_integrity.json) binds every other delivered file and verifies the 699-file predecessor baseline; it excludes itself to avoid a circular content hash. These records establish artifact identity and scope, not additional theorem proof or live authorization.

Receipts are read-only and have no BIT/ALG_AND_BIT authority. The hard-guard diagnostic uses `g>0`, with zero false; it is separate from the registered affine/ReLU propagation graphs and does not implement arbitrary branched programs. A strict full-domain output gap below the format's smallest positive subnormal can prove canonical output-word equality, but program lifting still requires every A3 interface, input, invariant and same-snapshot scheduling premise.

B1's frozen 21 BIT-preserving but ALG-failing refusals remain unchanged, as does its dense FP32 AdamW result of zero accepted steps in 8 attempts and final loss 5/2. Those results were read, not rerun. GPU, native BF16, general concurrency, arbitrary compilation/FMA/reassociation, hardware faults, complete machine proofs and universal learning benefit remain uncertified. B4 is a saved handoff only; it is not executed here.
