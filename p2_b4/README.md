# DMWK P2-B4: capacity and stability across repeated updates

B4 separates accepted update index `k` from execution time `t`, and separates original-reference, adjacent-endpoint and two-history comparisons. It analyzes actual stored differences `Delta_k=W_(k+1)-W_k`, with complete shared-call domains and fixed numerical policies.

The main conclusions are conditional:

- A fixed exact protection space is not consumed by update count. Every increment annihilates it if and only if every endpoint prefix preserves its original anchor. Final cancellation alone is insufficient.
- In a fixed absolute endpoint universe, a fixed ALG/BIT equivalence class and its absolute target-response image stay unchanged along a chain within that class. Local step/rank/optimizer/quantization restrictions can still stall. Adding independent cumulative tasks can reduce capacity; moving nonnested spaces need not do so monotonically and can forget earlier tasks.
- Changing histories obey a time-varying recurrence only after joint domains, actual endpoints and both rounded executions are certified. A common invariant and one common contraction norm can give a uniform bound. Individually stable modes in different norms can amplify under switching.
- Numerical history budgets are read-only. The exact-D transaction experiment preserves the existing B1/A3 `ALG_AND_BIT` gate and stages endpoint, optimizer and history changes before one serial publication.

Definitions and complete handwritten proofs are in [Definitions](P2_B4_Definitions.md) and [Theorems T1–T9](P2_B4_Theorems.md). The [Evidence Map](P2_B4_Evidence_Map.md) keeps those proofs separate from finite experiments and backend evidence. C1 is a [future handoff](P2_C1_Handoff.md), not an implemented stage.

## Current recorded evidence

[capacity_results.json](capacity_results.json) reports `passed`, seed 20261114, 14,345 finite assertions, 10 expected refusals and zero unexpected failures in 14.841555603 s. It covers 1,458 complete stored three-endpoint histories in the named small palette, 72 seeded fixed-space cases, 1,728 prescribed-response/cap queries, 27 three-task anchor assignments and 1,892 endpoint examinations across 12 explicit finite families. Whole-format counts and arbitrary-history statements remain separate mathematical results.

[switching_results.json](switching_results.json) reports `passed`, seed 20261114, 4,028 finite assertions, 10 expected refusals and zero unexpected failures, in 22.620926238 s. It includes:

- 64 named complete mode-pair families and 1,152 trajectory pairs over their stated ternary input alphabets and finite horizons;
- 12 separately labelled seeded trajectory pairs of length 12;
- two common-family invariant proofs, each checking four modes and 16 ordered mode pairs;
- skipped/repeated version schedules, identical changing histories with zero actual error, switched nilpotent amplification, prefix-budget failures and retained numerical boundaries.

[transaction_results.json](transaction_results.json) also reports `passed`: 1,120 assertions, 98 expected refusals and zero unexpected failures in 30.747024295 s. The new structural SGD experiment uses learning rate 1/4 and target `(1,-1)` at legal A input e3:

| Format | Accepted updates | Nonzero stored changes | Accepted no-ops | Exact decoded toy loss |
|---|---:|---:|---:|---|
| BF16 | 32 | 16 | 16 | 1/2 → 1/32768 |
| FP32 | 32 | 32 | 0 | 1/2 → 2839225/562949953421312 |

All 64 paired D ticks preserve the unchanged reference observations. The fixed algebraic dimension remains 4, the reserved-column dimension 2 and the exact A-response dimension 2. BF16's local quantization stall does not consume that global capacity; an accepted no-op is not new functional progress. These are measured toy results, not universal learning guarantees.

[independent_results.json](independent_results.json) reports `passed`: 33,901 assertions, 56 expected refusals and zero unexpected failures in 79.998951999 s. Its independent exact minors/direct equations, word-rounding search, interval recurrences and product sums cover separately named finite cases, including 1,136 endpoint examinations, 1,142 schedule/input/initial-pair histories, 32 toy learning steps and 12 read-only receipts. It also redecodes the frozen B1 refused endpoints without regenerating their optimizer trajectories.

[verification_results.json](verification_results.json) passes all three new B4 sections in 70.286952879 s and confirms the 739 predecessor artifacts unchanged. This aggregate repeats the named producer suites; it is not additional distinct experimental coverage. [reproduction_driver_results.json](reproduction_driver_results.json) also passes: independent `/tmp` runs reproduce the main and independent scientific results, and all three standalone producer outputs match their aggregate sections, excluding timing only. The foreign main and independent runtimes are 74.400552056 s and 85.498845732 s. Both `-O` and `-OO` refuse before running tests. The all-time common-family conclusion comes from its invariant/common-norm proof; it is not extrapolated from the finite stress histories.

## Reproduce in the existing workspace

The recorded environment is Python 3.12.14 with NumPy 2.3.5 on Linux x86_64; [requirements.txt](requirements.txt) pins the package. Pure reference imports use the archived sibling P1/P2 directories and `/workspace/dmwk-p1-foundations`. Copying only `p2_b4` is insufficient; retain the workspace layout and the predecessor files named in [dependency_baseline.json](dependency_baseline.json).

Use a fresh output directory without `-O` or `-OO`:

```bash
B4_REPRO_DIR=$(mktemp -d /tmp/dmwk-p2-b4-repro.XXXXXX)
cd "$B4_REPRO_DIR"
python -B /workspace/p2_b4/verify_b4.py --output "$B4_REPRO_DIR/main.json"
python -B /workspace/p2_b4/verify_independent.py --output "$B4_REPRO_DIR/independent.json"
```

The aggregate invokes only new B4 suites and checks predecessor hashes/inventory and current source identity. Reproduction must compare scientific values, environments, refusal reasons and source bindings, excluding only explicitly recorded timing fields. If a separate Python environment is needed, install the pinned dependency there using `python -m pip install -r /workspace/p2_b4/requirements.txt`; archived environments and evidence should remain unchanged.

## Execution and capacity boundaries

Concrete numerical analysis uses the infinity norm, exact rational bounds, canonical finite BF16/FP32 encodings, nearest-even rounding, gradual underflow and bias-first ordered separate multiply/add. BF16 is software; the available CPU FP32 path audits each scalar operation against exact RNE. Identity/ReLU and all shared calls are explicit. Hard branches retain their separate strict-margin obligations.

The switching reference supports one or two state coordinates, horizons at most 64, at most 128 stored versions per history, and at most 16 distinct modes in a common-family proof. These are implementation limits. A stored numerical history is not evidence that each endpoint was accepted by the live exact-D gate. A numerical receipt cannot authorize or bypass that gate.

The structural exact-D fixture preserves its full Boolean shared-call domain while changing reserved A coordinates. Its declared squared-loss toy target is a finite experiment, not a claim of general learning benefit. Accepted no-ops, nonzero stored changes, optimizer steps and D ticks are different counts. Administrative ledger limits are not algebraic exhaustion.

The initial predecessor inspection verified a 739-file baseline and the saved B3 integrity/result records without rerunning old suites; the completed B4 aggregate and reproduction driver confirm that baseline and inventory unchanged. Frozen B1 evidence remains 21 BIT-equal but ALG-failing refusals, and dense FP32 AdamW 0 accepted / 8 refused with final loss 5/2.

## Artifact index

| Purpose | Existing files |
|---|---|
| Plan and derivation checkpoint | [Plan](P2_B4_Plan.md), [Mathematical checkpoint](P2_B4_Mathematical_Checkpoint.md) |
| Definitions, proofs and synthesis | [Definitions](P2_B4_Definitions.md), [Theorems](P2_B4_Theorems.md), [Report](P2_B4_Report.md), [Evidence Map](P2_B4_Evidence_Map.md) |
| Numerical/capacity analysis and counterexamples | [Analysis](P2_B4_Analysis.md), [Capacity analysis](P2_B4_Capacity_Analysis.md), [Counterexamples](P2_B4_Counterexamples.md) |
| Review, corrections and next-stage boundary | [Review](P2_B4_Review.md), [Errata](P2_B4_Errata.md), [C1 handoff](P2_C1_Handoff.md) |
| Capacity interface and implementation | [B4_Capacity_Interface.md](B4_Capacity_Interface.md), [capacity_history.py](capacity_history.py) |
| Switching interface and implementation | [B4_Interface.md](B4_Interface.md), [switching_bounds.py](switching_bounds.py), [b4_runtime.py](b4_runtime.py) |
| Exact-D owner and read-only numerical receipts | [Transaction design](B4_Transaction_Design.md), [Transaction specification](P2_B4_Transaction_Spec.md), [update_sequence.py](update_sequence.py), [sequence_certificate.py](sequence_certificate.py) |
| Verification entry points | [verify_b4.py](verify_b4.py), [verify_independent.py](verify_independent.py), [verify_capacity.py](verify_capacity.py), [verify_switching.py](verify_switching.py), [verify_transactions.py](verify_transactions.py) |
| Reproduction driver | [verify_reproduction.py](verify_reproduction.py) |
| Actual producer outputs | [capacity_results.json](capacity_results.json), [switching_results.json](switching_results.json), [transaction_results.json](transaction_results.json) |
| Actual independent output | [independent_results.json](independent_results.json) |
| Actual aggregate output | [verification_results.json](verification_results.json) |
| Foreign-directory and preflight evidence | [reproduction_driver_results.json](reproduction_driver_results.json), [reproduction_results.json](reproduction_results.json), [independent_reproduction_results.json](independent_reproduction_results.json), [optimized_O_results.json](optimized_O_results.json), [optimized_OO_results.json](optimized_OO_results.json) |
| Dependency provenance | [dependency_inspection.json](dependency_inspection.json), [dependency_baseline.json](dependency_baseline.json), [requirements.txt](requirements.txt) |

No GPU, native BF16, general concurrency, arbitrary compiler/FMA/reassociation, hardware-fault, complete proof-assistant or universal learning guarantee is claimed. B4 does not complete the C-series compiler/kernel work.

## Delivery records

[Completion status](completion_status.json) binds the scoped conclusions, actual primary/independent/reproduction records and preserved predecessor inventory. [Final integrity](final_integrity.json) lists every other delivered file's SHA256 and byte size and records the final packaging checks; it excludes itself to avoid a circular digest. The manifest is an integrity receipt, not authentication or a machine proof. No C1 implementation or publication is included.
