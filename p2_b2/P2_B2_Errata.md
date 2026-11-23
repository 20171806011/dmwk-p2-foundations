# P2-B2 dependency errata and review corrections

The scoped read-only inspection found no predecessor error requiring changes to P1 or P2-A1 through B1. Previous files and test outputs remain untouched; no old suite was rerun. The preserved B1 facts are 21 BIT-preserving but ALG-failing joint refusals, and eight refused dense FP32 AdamW attempts with no loss improvement.

The following refinements were made within B2 before final evidence:

1. **Reference versus global space.** If the reference space contains the full legal activation domain, the leakage term is identically zero there. A nonzero leakage term requires an explicitly enlarged/perturbed domain or a distinct reference space. This qualification prevents unexplained 'leakage' from an exact span definition.
2. **Core geometry coefficient.** An early interface used the valid but looser factor `||h||`. It was refined to `||Pi_V h||=||a||` for the requested residual/leakage separation, with the separate total bound retained explicitly.
3. **Root precision at tiny scales.** Rational square-root enclosures use a normalized dyadic grid and exact rescaling, rather than an absolute grid that would be excessively loose for subnormals. One verifier assertion about the old grid width was adapted; the mathematical enclosure property did not fail.
4. **Snapshot adapter.** Independent pre-run review found that a new B2 context schema omitted B1's `schedule` field. The B2 schema was corrected to bind the full context. This context is identity metadata, not a proof of live-state validity or caller authenticity.
5. **Norm and degeneracy wording.** Receipt proofs explicitly cover their selected L2 or infinity norm. The Euclidean two-execution and box formulas match the implementation. Identical endpoints and fixed-bias zero inputs have explicit equality conclusions under the fixed numerical graph; the general annihilator condition alone still does not imply BIT.

The review records the independent disposition and any further issues. These corrections are not evidence that a prior result was false, and a conservative inability to certify a box is not relabeled as an actual overflowing execution.
