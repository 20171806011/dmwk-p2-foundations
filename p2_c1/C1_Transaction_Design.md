# C1 transaction design before implementation

This design is subordinate to the mathematical checkpoint and final compiler interface. It introduces no implementation or previous-stage modification. The new source/layout must receive its own compiler proof; B1's fixed model registry cannot authorize an arbitrary new layout.

## Closed owner and observations

A compiled-program owner receives the complete source, compilation budget, numerical format and optimizer configuration, and obtains or validates an artifact against those externally expected values. The artifact includes every deterministic call, physical bank, fixed/writable cells, input preparation, activation/bias policy, initial relation, graph and schedule. The owner stores a canonical detached copy; returned snapshots and previews must not alias owned mutable data.

The proposed shared bank has a fixed AND/NOT block and separate editable A block, with fixed zero cross connections. D reads the compiled sparse deterministic coordinates and uses only canonical Boolean source state/input. A uses only its own coordinates and has no callback into D state, inputs or effects. D observations are next state and labelled source outputs; accepted optimizer, weight, version and history changes are not themselves required to equal an unpatched reference.

The proposed A input domain is zero plus the coordinate unit vectors of the A block. A uses the identity activation with fixed zero bias. For this domain each output accumulates at most one nonzero finite coefficient, so canonical finite A words remain total under the fixed separate multiply/add order. General dense A input domains need new range/totality evidence and are not silently admitted.

## Proposal and publication order

1. Validate the current complete artifact and request schema.
2. On an unexposed temporary value, form an AI direct candidate or an optimizer proposal. A limited exact-rational SGD/EMA-momentum route may reuse pure B1 mathematical helpers; it does not reuse B1's fixed-model authorization.
3. Apply the declared final structural mask to an optimizer increment after momentum, scaling and any explicitly supported candidate operations. Direct endpoint proposals are checked rather than assumed safe. Quantize the actual endpoint and use exact decoded `W_new-W_old` for every algebraic diagnostic.
4. Validate canonical words, shapes, fixed cells, full compiled graph/domain identity and complete-domain structural ALG_AND_BIT obligations. Check A totality on the declared domain. A finite set of source-state tests is supporting evidence, not a replacement for the compiler invariant proof.
5. Construct the complete next optimizer/version/history state and publication receipt. Administrative accepted-update limits are separate from algebraic capacity and numerical budgets.
6. Recompute and compare the prepared canonical candidate against the current complete owner snapshot. Publish a single complete replacement only after every potentially rejecting protocol check and record construction succeeds.

A refusal at any point changes neither weights nor D state nor optimizer, versions, counters or ledgers. A tick similarly computes every next register and output from one old source-state snapshot, then publishes a complete successor. Accepted no-op updates may advance versions/optimizer/history without representing a nonzero stored update.

## Binding and refusals

Bind source/IR, expected compilation budget, artifact/graph/call identity, physical bank words, numerical format/policy, version, source state/tick, optimizer/configuration, both ledgers, initial relation, A task, schedule, actual candidate endpoint and implementation-source fingerprints. Rehashed inconsistent records, omitted/shared calls, changed activation/bias/domain/ports, stale ticks or versions, altered optimizer states and numerical-only receipts must refuse. Hash consistency is not authentication or protection from hostile private-memory mutation.

## Planned evidence

Use a compiled feedback source and a legal A unit-vector target for nonzero SGD learning, plus a momentum fixture with already nonzero moments and a late administrative refusal. Compare D ticks to an independently supplied source interpreter. Enumerate the small declared D domain, verify complete snapshots on refusal, and exercise stored no-ops, direct safe A patches, protected/cross-region edits, saturation, nonfinite and negative-zero words, stale and rehashed certificates, and attempt to submit a read-only diagnostic as an exact update.

The model is trusted serialized copy/check/publish only. It provides no concurrency, crash durability, arbitrary compiler/FMA transformation, hostile-memory or universal learning guarantee, and it does not complete C2.
