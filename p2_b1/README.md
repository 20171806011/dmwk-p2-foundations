# DMWK / P2-B1: constrained proposals and transactional optimization

This stage defines an exact restriction of proposed weight updates, shows why restricting a gradient alone does not generally constrain the resulting optimizer step, and implements a certificate-gated transaction that publishes stored weights and optimizer state together. It completes **B1 only**. The next-stage interface is recorded in [P2_B2_Handoff.md](P2_B2_Handoff.md); B2 is not implemented here.

The reference supports AI-supplied exact directions and SGD, EMA-momentum and AdamW-style proposals. It preserves the distinction between an exact algebraic update, a representable endpoint, fixed-graph bitwise equivalence and a response on specified A inputs. Projection and rank bounds do not substitute for endpoint certification.

## Mathematical results

The complete arguments are in [P2_B1_Theorems.md](P2_B1_Theorems.md), with assumptions in [P2_B1_Definitions.md](P2_B1_Definitions.md).

- **T1:** For a globally justified protected span V, `G P_perp` is the unique Frobenius-nearest exact annihilator. This is an exact Q/R statement.
- **T2:** Nullspace coordinates parameterize every exact-safe update; low-rank factors cover the rank-constrained family. Coordinate SGD with a nonorthonormal basis need not equal Frobenius-projected SGD. A per-step rank cap is distinct from a cumulative or persistent-adapter rank cap.
- **T3:** Scalar combinations preserve a fixed annihilator space. Off-space momentum, adaptive coordinate scaling, coordinate clipping and decay can destroy gradient-only closure. The full final increment must be restricted unless the later operations have separately proved closure.
- **T4:** Quantizing `W + Delta` can change the effective update. Exact endpoint annihilation and fixed-graph BIT equivalence remain distinct requirements.
- **T5:** Under the trusted serialized ownership contract, validation and complete recomputation precede one combined publication. Refusal preserves weights, protected state, counters and optimizer state; success publishes the staged optimizer state together with the checked endpoint.
- **T6:** A small reserved-column layout admits nonzero stored updates and changed legal A outputs while keeping all declared protected transitions exact. This is a concrete construction, not a complete compiler.

These are handwritten proofs. The executable checks are finite corroboration, not Lean/Coq verification, a universal SMT proof or a theorem of useful learning performance.

Recorded validation passed: 2,400 constraint checks, 1,013 optimization checks and a separate independent reference. The 24 toy runs contain 192 proposals: 75 accepted safe commits, 21 joint-contract refusals and 96 offline baseline applications. Independent replay confirmed that all 21 refused endpoints met BIT but failed the selected ALG condition. Main and different-working-directory runs both passed and verified 413 previous artifacts unchanged. See the [evidence map](P2_B1_Evidence_Map.md) for exact scopes, seeds and costs.

Both the aggregate and independent verifier were repeated from `/tmp`. Their scientific results and source bindings match their respective primary runs after omitting only timing/timestamps. [driver_checks.json](driver_checks.json) records the comparisons, component-to-aggregate agreement and expected optimized-mode preflight refusals. Reproduction uses the same environment and dependency tree; it is not a clean-room installation or cross-platform certification.

## Implementation and operation order

See [B1_Interface.md](B1_Interface.md) for signatures and serialization. [constrained_updates.py](constrained_updates.py) implements exact projection, nullspace/low-rank construction, clipping and staged proposals. [optimizer_kernel.py](optimizer_kernel.py) owns the combined immutable bank and the acceptance protocol.

The declared order is: optional gradient-only restriction for an offline baseline; moment calculation; parameter step; decoupled decay; increment clipping; final projection or structural mask; endpoint quantization; complete endpoint check; combined publication. The live optimizer interface allows the final projected and structural routes. Unconstrained and gradient-only experiments remain offline simulations.

SGD and momentum use exact rational proposal arithmetic. AdamW uses explicitly ordered finite host binary64 operations, including Python power and `math.sqrt`, then exact decoding of the resulting floats. Those host functions are not certified as correctly rounded mathematical primitives or as reproducible on arbitrary platforms. Protected execution is separate: software BF16 and audited local CPU FP32 with the stated rounding/zero policy.

The default acceptance claim is `ALG_AND_BIT`; explicit `BIT` is also supported. The selected claim is fixed and never silently weakened after rejection. The actual endpoint difference is always computed by exact decoding of `W' - W`. A prepared record binds the full old snapshot, including q and tick count; a D tick after preparation makes it stale. Dense checks use the unchanged A3 pure certificate checker, followed by B1's single combined publication. The structural route has its own complete four-case Boolean state/input descriptor and proof.

Canonical recomputation is not authentication of historical caller intent. An inconsistent packet is rejected. A coherently reissued request with valid complete evidence is another authorized request from the trusted caller. There is no secret signature or claim of protection from malicious private-memory mutation.

## Reproduce

The saved environment uses Python 3.12 and `numpy==2.3.5`; see [requirements.txt](requirements.txt). The scripts use the current workspace's **read-only prior artifacts**, including the P1 arithmetic and A2/A3/A4 interfaces. Keep the existing adjacent research directories and their paths; this folder alone is not advertised as a standalone distribution. [dependency_baseline.json](dependency_baseline.json) records 413 prior files, and the aggregate runner checks their contents and inventory before and after its work. Old-stage verification suites are not imported or rerun.

From any working directory, run the aggregate verifier with a fresh output path:

```bash
PYTHONDONTWRITEBYTECODE=1 python /workspace/p2_b1/verify_b1.py \
  --output /tmp/p2_b1_verification.json

PYTHONDONTWRITEBYTECODE=1 python /workspace/p2_b1/verify_independent.py \
  --output /tmp/p2_b1_independent.json
```

Do not use `python -O` or `python -OO`; the verifiers explicitly reject those modes. The aggregate runs [verify_constraints.py](verify_constraints.py) and [verify_training.py](verify_training.py). Their standalone entry points write their named component result files in this folder. The independent checker also reads the recorded producer training results and reconstructs their proposals, endpoints, losses and protected contexts using a separate reference.

The toy optimization objective is decoded `1/2 ||y - (0,2)||^2` on one legal A basis input. Its supplied gradient is the gradient of the continuous linear extension at the decoded bank, not the derivative of the rounded execution function. Experiments use three optimizer configurations, four routes, both formats and eight proposals per run with seed **20261114**. Dense and structural routes use different parameterizations and protected graphs; their losses and costs are not a controlled performance comparison.

## Research artifacts

| Purpose | Files |
|---|---|
| Plan and proof checkpoint | [P2_B1_Plan.md](P2_B1_Plan.md), [P2_B1_Mathematical_Checkpoint.md](P2_B1_Mathematical_Checkpoint.md) |
| Definitions and proofs | [P2_B1_Definitions.md](P2_B1_Definitions.md), [P2_B1_Theorems.md](P2_B1_Theorems.md) |
| Findings and counterexamples | [P2_B1_Report.md](P2_B1_Report.md), [P2_B1_Counterexamples.md](P2_B1_Counterexamples.md), [P2_B1_Optimization_Experiment.md](P2_B1_Optimization_Experiment.md) |
| Interface and implementation | [B1_Interface.md](B1_Interface.md), [constrained_updates.py](constrained_updates.py), [optimizer_kernel.py](optimizer_kernel.py), [b1_runtime.py](b1_runtime.py) |
| Main validation | [verify_b1.py](verify_b1.py), [verify_constraints.py](verify_constraints.py), [verify_training.py](verify_training.py) |
| Independent validation | [verify_independent.py](verify_independent.py) |
| Producer evidence | [constraint_results.json](constraint_results.json), [training_results.json](training_results.json), [P2_B1_Evidence_Map.md](P2_B1_Evidence_Map.md) |
| Independent and reproduced evidence | [independent_results.json](independent_results.json), [verification_results.json](verification_results.json), [reproduction_results.json](reproduction_results.json), [independent_reproduction_results.json](independent_reproduction_results.json), [driver_checks.json](driver_checks.json) |
| Review and final integrity | [P2_B1_Review.md](P2_B1_Review.md), [completion_status.json](completion_status.json), [final_integrity.json](final_integrity.json) |
| Prior-state boundary | [dependency_baseline.json](dependency_baseline.json), [dependency_inspection.json](dependency_inspection.json), [P2_B1_Errata.md](P2_B1_Errata.md) |
| Next-stage boundary | [P2_B2_Handoff.md](P2_B2_Handoff.md) |

Actual component/aggregate/independent results, counterexamples and their claim-level attribution are listed in [P2_B1_Evidence_Map.md](P2_B1_Evidence_Map.md). A filename or stage heading alone is not evidence of a passed run.

## Scope that remains open

The safety reasoning fixes D, the globally covered legal domain, admitted initial states, graph, numerical policy, same-snapshot schedule and trusted APIs. It excludes arbitrary A-to-D feedback, hidden call sites, concurrent writers and unverified graph transformations. Structural read exclusion concerns D arithmetic after pure admitted-bank validation, not all host branches, memory accesses or runtime cost.

GPU, native BF16, arbitrary compiler optimizations, FMA/reassociation changes, general concurrency, crash recovery and malicious runtime mutation remain uncertified. Projected proposals may legitimately be refused after quantization; retrying the same rejected state does not establish progress. The tests do not claim universal convergence, generalization, a completed long-term training policy, a universal safe projection onto a finite BIT class, or completion of the remaining P2 stages.
