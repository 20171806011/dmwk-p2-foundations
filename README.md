# DMWK P2 research through C1

This private research archive contains nine stages of the Dual-Mode Weight-Space Kernel project. The latest stage compiles a bounded Boolean state machine to a fixed execution graph and a shared weight matrix with reserved learnable coordinates. Under its canonical word encoding, fixed arithmetic policy and synchronous serial schedule, allowed edits preserve the deterministic state and outputs for every finite legal execution. The learnable port accepts zero and coordinate basis inputs.

Start with the [C1 research report](p2_c1/P2_C1_Report.md), [theorems and assumptions](p2_c1/P2_C1_Theorems.md), [claim-to-evidence map](p2_c1/P2_C1_Evidence_Map.md), and [example compiler artifact](p2_c1/example_artifact.json).

| Stage | Question and evidence |
|---|---|
| [A1](p2_a1/README.md) | Which activations can reach every deterministic call site? |
| [A2](p2_a2/README.md) | How can updates annihilate a protected activation space? |
| [A3](p2_a3/README.md) | Which algebraic and executed conditions imply noninterference? |
| [A4](p2_a4/README.md) | How much rank and target-response capacity remains? |
| [B1](p2_b1/README.md) | How should direct and optimizer-generated updates be constrained? |
| [B2](p2_b2/README.md) | What can be certified about a single layer under approximate orthogonality? |
| [B3](p2_b3/README.md) | How do perturbations propagate through nonlinear layers and finite-time feedback? |
| [B4](p2_b4/README.md) | How do capacity and stability change over repeated updates? |
| [C1](p2_c1/README.md) | How can a compiler allocate deterministic and learnable coordinates under a budget? |

## Run the C1 example

From the repository root, use Python 3.12 and NumPy 2.3.5. Use an unused temporary directory for generated results. The compiler deliberately refuses to overwrite its output.

```bash
python -m pip install -r p2_c1/requirements.txt
results=$(mktemp -d)
python -B p2_c1/compile_ir.py p2_c1/example_request.json "$results/parity.json"
python -B p2_c1/verify_independent.py --output "$results/independent.json"
```

The example compiles seven deterministic gate sites into a graph sharing one 4-by-4 weight matrix. Two cells remain editable. The two-port learning example accepted 32 updates in each format. Software BF16 changed stored weights 16 times and ended at loss 1/16384. CPU FP32 changed them 32 times and ended at loss 2839225/281474976710656. The initial loss was 1. All 64 paired feedback ticks agreed on deterministic observations. The [training record](p2_c1/transaction_results.json) identifies the source, domains and numerical policy.

The archived C1 primary run records 321,198 assertions and the separate verifier records 212,851. The [reproduction record](p2_c1/reproduction_driver_results.json) compares six pairs of results from the original research environment. General proofs are handwritten. The supported execution evidence covers software BF16 and local CPU FP32 under fixed graphs. GPU, native BF16, arbitrary compiler transformations, FMA, general concurrency and universal learning performance remain open. C2 appears only as a handoff.

## Provenance and reproducibility

[RELEASE_FILES.json](RELEASE_FILES.json) gives SHA-256 hashes for 326 research artifacts and four runtime source files from P1 commit `40854b62aee03af20f28e8fe2627e1872d05239e`. Each stage retains its original reports, evidence and original-workspace integrity records. The public-paper comparisons and checked original sources for OGD and GPM are in [C1 related work](p2_c1/P2_C1_Related_Work.md).

The release excludes the original user instruction attachment from A2. Its technical content is available in the stage definitions, plan and report. The stored workspace baselines reference that file and other original P1 working files. Historical full-workspace inventory preflights therefore require that original workspace. For a fresh clone use the commands above. Regenerated artifacts can carry different absolute path bindings from the archived originals. The [release validation record](RELEASE_VALIDATION.json) reports the checks made with the exported files.
