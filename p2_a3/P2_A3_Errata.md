# A3 errata and dependency clarifications

## Prior work

No contradictory prerequisite claim has been identified in the read-only examination of the A1/A2 definitions, proofs, execution contracts, independent reviews and A3 handoff used here. This is an interface/dependency check, not a new full review or rerun of previous stages. Existing evidence is retained unchanged. If a prior error is found during A3 review, it will be recorded here and any corrective implementation will be placed in A3 only.

## Clarifications required for this stage

1. Annihilation is checked on the exact decoded endpoint difference, not on a proposed increment that might be changed by storage rounding.
2. For a changing bias, augment the actual activation family before selecting a basis, or use an independently justified augmented-space generator. Appending one to an arbitrary basis of the unaugmented linear span is unsound. This is consistent with A1's affine-span theorem and is explicitly tested in A3.
3. Exact algebraic equality and equality of a rounded computation on a complete finite legal domain are different, non-nested contracts. A change can be rounded away on that finite domain even when its exact linear response is nonzero. Conversely, exact annihilation need not preserve rounded execution.
4. A domain/model hash or a claim of exhaustive sampling does not establish global coverage. Only a checker-owned declared finite model with proved closure, or an independently verified invariant proof under an explicitly supported interface, can supply that premise. The delivered executable checker uses the former route.
5. A positive numerical bound is not automatically a bitwise certificate, but it is too strong to say that no positive bound can ever imply equality. With a fixed finite output format, canonical injective encoding and a proved separation threshold, a certified difference bound strictly below that threshold does imply raw equality. The final A3 theorem states this additional condition explicitly. The implemented BOUND reporter does not turn such a bound into global commit permission; domain coverage and program lifting remain separate obligations.

The final independent review documents A3 implementation findings and fixes separately. No hash, finite experiment, or review judgment is called a machine proof.
