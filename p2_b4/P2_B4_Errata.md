# P2-B4 dependency errata and design clarifications

The scoped initial inspection verified B3's 39-file manifest, successful main/independent/reproduction records and source/evidence bindings, plus its 699 predecessor entries. The expanded B4 baseline covers 739 prior files. No prior suite or optimizer trajectory was rerun and no predecessor file was changed. No blocking predecessor error was found in this inspection; this is not a fresh exhaustive audit of every earlier proof.

## Clarifications established before implementation

- Fixed-space algebraic freedom does not decrease merely because the update count increases. More strongly, within a fixed absolute endpoint universe, fixed-anchor safe chains retain the same complete ALG class, and fixed-domain BIT chains retain the same observational equivalence class. Local proposal accessibility may still stall.
- Saturated and zero old banks with different protected anchors may have different stored feasible counts. This does not demonstrate shrinkage along a fixed-anchor safe chain.
- Cumulative task spaces need compatible target anchors and a check at task admission. An update rule that annihilates a newly added space does not itself prove that the current model already satisfies that task.
- Accepted-update count, nonzero-effective-update count, optimizer step and execution tick count are distinct. Intermediate updates can occur without a numerical transition; repeated transitions can use the same endpoint version. Observations and schedule must identify which events count.
- Full rollback concerns the entire owned bank. Historical D equivalence concerns the designated protected state/outputs, not equality of changing weight/version/optimizer metadata to an unpatched reference.
- Numerical switching receipts remain read-only. Exact-D transactions stage an unpublished copy and all ledger changes before the sole trusted serial publication point. This is not a general concurrency or crash-recovery theorem.

Any later implementation/review correction will be recorded here or in Review before sealing. Conservative rejection, actual drift, local quantization stall and algebraic capacity exhaustion must not be relabelled as one another.
## Independent fixture correction during B4

The first independent repeated-learning oracle assumed that the registered structural bank began with reserved coordinates `(0,0)`. Read-only inspection of the actual inherited B1 initial bank showed `(1,0)`. The oracle was corrected to decode the actual baseline rather than impose an invented one, then the affected independent sequence checks were rerun successfully. This was a reviewer-fixture error, not an endpoint implementation defect or a modification of B1. The final results bind the corrected verifier. No counts from the unsuccessful draft fixture are presented as successful evidence.

## Numerical integration fixture correction

An initial transaction integration exposed a scalar state cap being forwarded to a core interface requiring one bound per state coordinate. Before the passing run, the new numerical receipt adapter was corrected to normalize a scalar to a one-coordinate vector. The core still checks the required state dimension: this is not broadcasting one bound to an arbitrary state layout or accepting a mismatched domain certificate. The complete affected transaction suite was then rerun. No old source or result was edited. The final transaction evidence records 1,120 checks with zero unexpected failures and 98 intentional refusals.

## Final evidence-to-document reconciliation

The final packaging review found that README and Evidence Map still quoted the switching suite's earlier development wall time (22.473456970 seconds). Both now quote the final stored standalone result, 22.620926238 seconds. Scientific counts, data, source code and all reproduction comparisons were unchanged; no scientific rerun was needed for this documentation correction. The final integrity receipt was regenerated after the correction.
