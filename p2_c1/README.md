# DMWK P2-C1 — Compiling a Boolean state machine with reserved learning coordinates

The compiler accepts a synchronous Boolean state machine and a resource request. It emits an ordered graph, a shared weight bank, the bank's writable cells, all deterministic (D) and learnable (A) call identities, and evidence of activation coverage. A checker reconstructs the artifact from the caller's expected source, budget, format and initial A anchors. Under the specified word arithmetic, storage and serial schedule, each permitted A update preserves all declared D state and output words on every finite legal execution. [Research report](P2_C1_Report.md) · [Compiler implementation](c1_compiler.py) · [Definitions](P2_C1_Definitions.md) · [Handwritten proofs](P2_C1_Theorems.md)

## Compile the parity example

The example begins with parity zero. Each tick emits the previous parity bit and updates it by XOR with the input bit. Its BF16 artifact has one 4-by-4 bank with 16 matrix words and four fixed bias words. Seven shared gate calls cost 84 separate floating multiply/add operations and 14 scalar ReLUs per tick. Two matrix entries are writable. Their two responses can vary independently at the legal nonzero A input. The graph, its wires and state storage account for the rest of the program. [Source and budget](example_request.json) · [Inspect the compiled artifact](example_artifact.json)

For budget-driven layout selection, supply `layout_limits` in place of `budget`, and omit `a_rows` and `a_cols`. The CLI checks all four supported shapes in order of dense matrix word cost, returns the first feasible layout and records its concrete budget. For example, removing both shape fields from the displayed parity budget lets a 1-by-2 reserve satisfy the two response degrees using 15 matrix words. A required two-output initial anchor instead selects a 2-by-1 reserve with 16 matrix words. The search optimizes storage within these four shapes. [Layout planning proof](P2_C1_Layout_Search.md) · [104 budget cases](layout_results.json)

The saved example returns old-output/next-state pairs (0,1), (1,0), (0,0), (0,1) on input bits 1,1,0,1. Its foreign working-directory build is byte-identical to the supplied artifact. [Example run](example_run.json)

Run from the existing workspace layout with Python 3.12.14 and NumPy 2.3.5. The CLI takes two paths and writes a new file only after compilation and artifact reconstruction succeed. The following commands use fresh output paths.

```bash
run_dir=$(mktemp -d /tmp/dmwk-c1.XXXXXX)
cd "$run_dir"
python -B /workspace/p2_c1/compile_ir.py /workspace/p2_c1/example_request.json "$run_dir/parity.json"
cmp "$run_dir/parity.json" /workspace/p2_c1/example_artifact.json
python -B /workspace/p2_c1/verify_c1.py --output "$run_dir/main.json"
python -B /workspace/p2_c1/verify_independent.py --output "$run_dir/independent.json"
```

The pinned dependency and sibling research directories supply the arithmetic backend and previous evidence used by these entry points. Source fingerprints and workspace paths form part of the artifact. Use the documented workspace layout for byte-for-byte reproduction. [Dependencies](requirements.txt) · [Predecessor inventory](dependency_baseline.json) · [Compiler interface](C1_Compiler_Interface.md)

## Capacity and execution contract

The shared bank contains a fixed 2-by-3 D block with rows `(1,1,-1)` and `(-1,0,1)`, two fixed zero cross blocks, and an editable m-by-c A block. D calls evaluate both fixed rows on `(a,b,1)` using coordinate ReLU. A calls select only A rows and columns, use identity activation, and admit zero or a coordinate unit vector. All state updates read one old Boolean snapshot. These port, dataflow and schedule conditions enter both the proof and the checker. [Compiler specification](P2_C1_Compiler.md)

| Quantity | Meaning in this compiler |
|---|---|
| D containing space | Rank three across all legal histories. The additional complete all-state/input envelope may have smaller rank, including zero for a pure wire. A declared initial subset may make some enumerated states unreachable. |
| Algebraic A freedom | The structural mask admits mc scalar degrees of freedom and maximum individual update rank min(m,c). The unrestricted full-output annihilator of the reserved space has dimension (2+m)c. |
| Stored endpoints | The structural class has exactly N^(mc) members with canonical finite words, N=65,279 for BF16 or 4,278,190,079 for FP32. Querying all c basis inputs recovers every column exactly. This count follows by proof. |
| Target responses | On target columns Z, structural response dimension is m rank(Z). Initial basis anchors must respect duplicate and zero input relations and be exactly storable. Learning may subsequently change those initial A assignments. |
| Resource budget | The layout uses (2+m)(3+c) matrix words, 12 floating binary operations per D gate and 2mc per A call. The graph and per-tick work grow with the source. |

Structural endpoint admission binds the whole current owner, including the source, graph, budget, actual stored weights, optimizer, state, version, schedule and ledgers. Successful publication changes A values and permitted metadata. Rejection leaves every owned component unchanged. For a separately reconstructed constant-gate program, the read-only geometry checker compares a coupled change to the AND row and a cancellation-prone change. Both exactly annihilate the program’s protected span. Only the former preserves every finite word tested across the complete Boolean domain. The live owner rejects both edits outside the compilation mask. [Owner implementation](compiled_owner.py) · [Serial publication specification](P2_C1_Transaction_Spec.md) · [Geometry results](geometric_results.json) · [Geometric comparison](P2_C1_Geometric_Comparison.md) · [Counterexamples](P2_C1_Counterexamples.md)

## Results

The primary compiler suite recorded 1,400 successful compile requests and 69 refused compile requests. It exercised 672 specified programs in each format and all four Boolean state/input contexts for each program. The 5,376 contexts were evaluated at two A endpoints, for 10,752 endpoint/context executions. A separate seeded set exercised deeper programs. The independent verifier used its own Boolean interpreter and word-rounding reference. [Compiler results](compiler_results.json) · [Independent results](independent_results.json) · [Evidence map](P2_C1_Evidence_Map.md)

The learning example made 32 SGD attempts per format from A output (0,0), targeting (1,-1). All 64 updates were accepted. D had zero word mismatches across 64 paired ticks, with complete D tables checked after each update. [Transaction results](transaction_results.json)

| Format | Nonzero stored changes | Accepted no-ops | Initial loss | Final loss |
|---|---:|---:|---:|---:|
| Software BF16 | 16 | 16 | 1 | 1/16384 |
| Local CPU FP32 | 32 | 0 | 1 | 2839225/281474976710656 |

The BF16 run's first no-op occurred on attempt 17 despite both writable coordinates remaining available. The measured loss is half the sum of squared errors on this single declared A input. B1's earlier dense FP32 AdamW example retained loss 5/2 after eight refusals. All 21 saved B1 joint-contract refusals had passed the BIT check and failed the algebraic condition. [Evidence and scope](P2_C1_Evidence_Map.md)

The primary aggregate passed all 4 sections with 321,198 assertions, 310 expected refusals and zero unexpected failures in 85.188 seconds. It verified the 782 prior artifacts and bound 14 source and dependency inputs. The independent verifier separately passed 212,851 assertions with 95 expected refusals. [Primary results](verification_results.json) · [Independent results](independent_results.json)

Both verification entry points passed from `/tmp`. The foreign main run took 84.928 seconds and the foreign independent run took 17.813 seconds. All 6 comparisons matched after excluding wall-clock fields. These compare the two foreign runs with their primary records and each of the four standalone suites with its aggregate section. Both optimized interpreter modes refused before any test section. [Reproduction results](reproduction_driver_results.json) · [Foreign main record](reproduction_results.json) · [Foreign independent record](independent_reproduction_results.json)

## Research and scope

The language has one or two state bits, zero to two Boolean inputs and one or two outputs. Depth is limited to eight and the source to 256 expression-node occurrences. A dimensions each range from one to two. The D graph uses fixed ordered separate multiply/add, round-to-nearest-even, gradual underflow and canonical zero. Hardware evidence covers local scalar CPU FP32, and BF16 uses software arithmetic. The owner assumes trusted serial operation. Broader precision policies, GPU/native BF16, FMA or arbitrary optimizer transformations, concurrent/crash-safe publication, general learning performance and a full host machine proof remain open. [Independent review](P2_C1_Review.md) · [Corrections](P2_C1_Errata.md)

Original-source positioning covers OGD (AISTATS 2020) and GPM (ICLR 2021), including the gradients or sampled representations they protect. The C1 question concerns source-derived global activation coverage, actual endpoints, graph provenance and serial authorization. No comparative benchmark or novelty assessment was performed. [Related work](P2_C1_Related_Work.md) · [Source receipts](literature_sources.json)

The 782-file read-only baseline includes B4 and its predecessors. The C2 handoff records the additional interface conditions that bidirectional composition would require. [Plan](P2_C1_Plan.md) · [Proof checkpoint](P2_C1_Mathematical_Checkpoint.md) · [Dependency inspection](dependency_inspection.json) · [C2 handoff](P2_C2_Handoff.md)

The completion record identifies the scoped claims and source and result hashes. The final manifest records byte sizes and checksums of the other deliverables. [Completion status](completion_status.json) · [Final integrity](final_integrity.json)
