# B4 capacity/history interface

The saved mathematical checkpoint precedes implementation. This module uses exact A2 rational matrices and canonical finite endpoint words. Every function is a diagnostic; none authorizes a live update or proves global application coverage from a sample matrix.

## Exact and registered protection

- `algebra_budget(H, output_rows, targets=None, rank_cap=None) -> dict` delegates the proved exact A4 dimension/rank/quotient formulas to its pure reference. H is explicitly only a supplied span; this route reports no verified global provenance.
- `registered_budget(model_id, fmt, output_rows=None, targets=None, rank_cap=None) -> dict` derives H from **all** sites/inputs in the unchanged A3 fixed registry and binds that descriptor. It certifies the declared registered envelope under its inherited hypotheses, not every application or an arbitrary modified program's reachability.
- `response_feasibility(H, X, R, rank_cap=None) -> dict` returns the exact A4 construction or an explicit quotient-relation/rank-cap obstruction. Algebraic feasibility does not establish storable or BIT feasibility.
- `joint_task_feasibility(tasks) -> dict` takes a nonempty sequence `(H_i,Y_i)` with desired linear task anchors `W H_i=Y_i`. It checks all relations of the concatenated generators, not merely pairwise intersections. On compatibility it returns a particular map and the unrestricted affine-family dimension; otherwise an exact relation witness is returned.
- `task_anchor_check(words,fmt,H,Y) -> dict` compares the current actual endpoint with the requested new anchor. Freezing H cannot retroactively repair a mismatch, even if some other endpoint could jointly satisfy all tasks.

## Stored histories

`analyze_history(word_history, fmt, spaces, mode="fixed", targets=None, rank_cap=None) -> dict` takes K+1 complete raw matrix endpoints and computes every actual decoded increment `W_(k+1)-W_k`.

- `fixed`: `spaces` contains one H reused at every update.
- `cumulative`: `spaces` contains K arriving task-generator matrices; update k protects their sum through k.
- `moving`: `spaces` contains K current generator matrices with no nesting assumption.

The result records dimensions/ranks at every step, actual increments and prefix totals, exact current-space residuals, original-space and seen-union prefix residuals, per-update cap checks, cumulative rank and the exact telescope. It also checks task-anchor preservation relative to each task's arrival endpoint W_i, rather than incorrectly claiming newly protected directions were already preserved relative to W_0. Supplied matrices carry no automatic global provenance; use `registered_budget` separately when the intended domain is a fixed supported registry.

A fixed absolute endpoint family and fixed anchor are not consumed by update count. Along an ALG-safe fixed-space chain the entire feasible endpoint class is unchanged; fixed-domain BIT equivalence has the same class-invariance property. Step-bounded neighborhoods, optimizer proposals, quantization reachability and rank-constrained **increments** remain different objects and can change or stall.

## Finite endpoints and quantization

`enumerate_endpoint_family(model_id,fmt,old_words,palette_words,targets=None,mutable_cells=None,max_candidates=4096) -> dict` completely enumerates the stated finite Cartesian endpoint family. The palette consists of distinct canonical finite raw words. Mutable cells default to all cells; fixed cells retain their old words. The registered model supplies global protected calls; default A observations are canonical basis inputs plus zero, with stateful versus diagnostic scope named explicitly.

Groups `storable`, `ALG`, `BIT`, `ALG_AND_BIT`, `ALG_NOT_BIT`, and `BIT_NOT_ALG` retain separate endpoint counts, actual-update rank histograms and exact/raw A response-image counts. Here BIT means actual total full-output equality at every fixed registered raw call. The old endpoint must execute totally on that domain. A separately named `E_CERT` group records A3 certificate acceptance, which can impose additional original-state/invariant obligations; it is not silently identified with raw-domain BIT. Every candidate records its actual decoded difference. The family is finite and is not called a vector space. The enumeration is not a whole-format capacity classification.

`quantize_proposal(old_words,ideal_increment,fmt) -> dict` returns the actual endpoint, exact effective difference, and no-op/nonzero-proposal flags. This is a storage diagnostic, not a candidate generator or training loop.

`record(value)` serializes exact Fractions as numerator/denominator pairs and matrices with explicit shapes. The new verifier uses root seed 20261114, exact rational direct constraints and explicit finite palettes. Independent review uses separate determinant/minor and word-rounding references. Prior-stage verifiers are never imported.
