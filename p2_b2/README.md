# DMWK / P2-B2: certified single-layer perturbation bounds

This stage bounds the output change of one fixed full-output linear or affine layer after a stored weight replacement. It separates exact algebra, generation/storage accounting, and the difference between two independently rounded executions. The accompanying numerical receipt is **read-only evidence**, not authorization to weaken or bypass B1's BIT or ALG_AND_BIT transaction.

B2 is the only stage implemented here. [P2_B3_Handoff.md](P2_B3_Handoff.md) records the next starting point; it does not execute B3 or claim a multilayer/program-level perturbation theorem.

## Results and assumptions

For the actual decoded endpoint difference Delta=W'-W, an orthonormal basis Q of a declared reference space V, and h=Qa+e with e orthogonal to V, the core exact bound is

\[
\|\Delta h\|_2\le\|\Delta Q\|_2\,\|a\|_2
+\|\Delta\|_2\,\|e\|_2.
\]

The implementation can instead use the exact rational projector onto V, so it does not require constructing irrational orthonormal coordinates. If V is already proved to contain the actual legal activation, e=0. Nonzero e must refer to a declared reference space or perturbed envelope; it is not unexplained leakage from a supposedly complete protected span.

Approximate-basis certificates separately bound Gram error and true-subspace misalignment. Exact rational square-root enclosures and elementary matrix-norm inequalities replace unverified numerical SVD estimates. The square-root enclosure is scale-normalized, retaining precision for subnormal-scale responses.

For fixed bias-first, ascending-column, separate multiply/add execution, the point bound is

\[
\|\widehat y'-\widehat y\|_2
\le \|\Delta h+(b'-b)\|_2
+\rho_{\rm old}+\rho_{\rm new}.
\]

Both execution-error terms come from their own actual ordered traces. A separate analytic box method proves operation ranges and uses additive underflow-aware local error bounds for every admitted input in its stated envelope. A failed box range proof can be conservative; it is not automatically evidence of an observed overflowing execution.

Complete definitions and handwritten proofs appear in [Definitions](P2_B2_Definitions.md) and [Theorems](P2_B2_Theorems.md). [Numerical Analysis](P2_B2_Numerical_Analysis.md) specifies arithmetic, error accounting and costs. No Lean/Coq verification, unrestricted SMT proof, GPU certification or universal neural-network guarantee is claimed.

The recorded producer checks passed: 3,419 bound checks and 421 receipt/interface checks, with expected refusals preserved. A separate independent reference also passed, including 1,458 exhaustive and 128 seeded affine point pairs, exact norm/projector checks, complete small box/receipt checks and all 21 frozen B1 endpoint analyses. Both main and independent runners reproduced from `/tmp` with identical scientific results after timing-only exclusions, and all 447 prior artifacts remained unchanged. See [P2_B2_Evidence_Map.md](P2_B2_Evidence_Map.md) for precise coverage and limitations.

## Interface and evidence scopes

[certified_bounds.py](certified_bounds.py) supplies exact geometry, error ledgers, point traces, analytic boxes and relative/mixed checks. [B2_Interface.md](B2_Interface.md) describes signatures and exact numerator/denominator serialization. [bounded_certificate.py](bounded_certificate.py) binds the selected L2 or infinity norm, actual endpoints, bias, registered complete domain or containing box, fixed graph/policy, full outputs and numerical budget. Its precise contract is in [P2_B2_Certificate_Spec.md](P2_B2_Certificate_Spec.md).

The scopes are intentionally distinct:

- A point trace covers one input.
- A complete registered-domain maximum covers all inputs in that declared finite domain.
- An analytic box covers every admitted raw input inside its proved coordinate envelope, with separate legal-domain inclusion evidence.
- A small numerical budget does not establish candidate feedback closure or program safety. A strict sub-lattice-step bound can imply equality only with its separate canonical-output separation and complete-coverage premises.

Direct endpoint bounds already include optimizer, generation and storage effects. A named telescoping ledger is an alternative accounting route; adding those same errors again to a direct actual-endpoint bound double-counts them. Relative error is undefined at a zero reference output. Absolute and mixed budgets remain meaningful there.

The new analysis reads the 21 frozen B1 rejected endpoints without rerunning B1 optimization. It preserves the finding that all 21 are BIT-equal on their declared finite domain but fail the chosen ALG condition. B1's dense FP32 AdamW run still has zero accepted updates in eight attempts and unchanged loss 5/2. A B2 numerical receipt neither changes those outcomes nor grants a live commit.

## Reproduce

The reference environment uses Python 3.12 and `numpy==2.3.5`, recorded in [requirements.txt](requirements.txt). Keep the existing adjacent P1 and P2 research directories: this stage loads declared arithmetic/contract interfaces read-only and is not advertised as an isolated standalone package. [dependency_baseline.json](dependency_baseline.json) records 447 previous artifacts. The aggregate runner checks their inventory and hashes before and after execution and does not import their old test suites.

Use fresh output files to preserve the delivered evidence:

```bash
PYTHONDONTWRITEBYTECODE=1 python /workspace/p2_b2/verify_b2.py \
  --output /tmp/p2_b2_verification.json

PYTHONDONTWRITEBYTECODE=1 python /workspace/p2_b2/verify_independent.py \
  --output /tmp/p2_b2_independent.json
```

Do not run verifiers with `-O` or `-OO`. The main runner invokes [verify_bounds.py](verify_bounds.py) and [verify_certificates.py](verify_certificates.py). Their standalone entry points write their named component JSON results. Fixed seed 20261114 and any independent subseeds are recorded explicitly in the evidence map/results. Native CPU FP32 operations are audited against the exact reference; BF16 execution here is a software model.

## Artifact index

| Purpose | Files |
|---|---|
| Plan and checkpoint | [P2_B2_Plan.md](P2_B2_Plan.md), [P2_B2_Mathematical_Checkpoint.md](P2_B2_Mathematical_Checkpoint.md) |
| Definitions and proofs | [P2_B2_Definitions.md](P2_B2_Definitions.md), [P2_B2_Theorems.md](P2_B2_Theorems.md) |
| Findings and independent review | [P2_B2_Report.md](P2_B2_Report.md), [P2_B2_Review.md](P2_B2_Review.md) |
| Arithmetic and public contracts | [P2_B2_Numerical_Analysis.md](P2_B2_Numerical_Analysis.md), [B2_Interface.md](B2_Interface.md), [P2_B2_Certificate_Spec.md](P2_B2_Certificate_Spec.md) |
| Implementation | [certified_bounds.py](certified_bounds.py), [bounded_certificate.py](bounded_certificate.py), [b2_runtime.py](b2_runtime.py) |
| Verification | [verify_b2.py](verify_b2.py), [verify_bounds.py](verify_bounds.py), [verify_certificates.py](verify_certificates.py), [verify_independent.py](verify_independent.py) |
| Producer evidence and failures | [bound_results.json](bound_results.json), [certificate_results.json](certificate_results.json), [P2_B2_Counterexamples.md](P2_B2_Counterexamples.md) |
| Independent evidence and attribution | [independent_results.json](independent_results.json), [P2_B2_Evidence_Map.md](P2_B2_Evidence_Map.md) |
| Aggregate and reproduction evidence | [verification_results.json](verification_results.json), [reproduction_results.json](reproduction_results.json), [independent_reproduction_results.json](independent_reproduction_results.json), [driver_checks.json](driver_checks.json) |
| Preservation and scope | [dependency_inspection.json](dependency_inspection.json), [dependency_baseline.json](dependency_baseline.json), [P2_B2_Errata.md](P2_B2_Errata.md), [P2_B3_Handoff.md](P2_B3_Handoff.md) |

Actual independent/aggregate/reproduction status and theorem-level attribution are recorded separately in [P2_B2_Evidence_Map.md](P2_B2_Evidence_Map.md); a file's existence alone is not a passed verification result.

## Limits

Delivery status is recorded in [completion_status.json](completion_status.json). The packaging record [final_integrity.json](final_integrity.json) binds every other delivered file and the preserved prior inventory; it excludes its own bytes to avoid a circular hash. This is artifact identity evidence, not additional proof of a mathematical theorem or publication authority.

The graph, numerical policy, bias convention, full output observation and domain coverage are fixed. Approximate basis conditioning can be uncertified even for a mathematically valid basis. Analytic boxes and triangle bounds can be loose or refuse; their conservatism is retained in the record. The implementation does not use an unguarded gamma_n model to omit subnormal errors.

GPU, native BF16, FMA/reassociation or arbitrary compiler changes, general concurrency, crash recovery, malicious private-memory mutation and arbitrary A-to-D feedback remain uncertified. A numeric receipt does not authenticate historical caller intent or authorize state publication. No learning-performance advantage, universal safe-update policy, complete multilayer bound or completed P2 composition theorem is asserted.
