# P2-A1 claim-to-evidence map

Every universal claim below is conditional on its stated model and is supported by the handwritten argument, not inferred solely from passing tests. The theorem labels refer to [P2_A1_Theorems.md](P2_A1_Theorems.md). Result field names refer to [verification_results.json](verification_results.json).

| Claim | Proof | Actual finite evidence | Cost and boundary |
|---|---|---|---|
| Finite activation set; Q/R rank agreement; finite basis witnesses | A1.1 | `rational_algebra`; independent `review_checks.json` | 80 seeded rational matrices; 512 exhaustive binary 3x3 matrices. These test rank code, not the general theorem. |
| Shared space is the sum of site spaces; sample lower bounds/full-rank witness rule | A1.2 | `sharing_and_state_examples`, `actual_compiler_examples` | Explicit finite models and two fixed source graphs; no arbitrary sharing-layout certification. |
| Complement dimension d-r, common annihilator intersection | A1.3 | Exact reported bases and rank differences | Algebraic conclusion only; no patch applied or bitwise update theorem. |
| Homogeneous rank equals affine dimension plus one | A1.4 | Nine `finite_activation_examples`, operand/augmented compiler summaries | Finite domain enumeration; fixed-bias and jointly represented bias are distinct parameter questions. |
| Exact all-time space from complete finite augmented-state exploration | A1.5 | `sharing_and_state_examples`, `delayed_direction`, `actual_compiler_examples` | Compiler fixtures: 6 states/6 edges and 4 states/8 edges per format. Step/monitor fidelity is a premise; no P1 suite rerun. |
| Least invariant state-feature space and sound observation superspace | A1.6 | `invariant_examples`, `finite_affine_fp_bridge` | Boolean bridge: 2 states/6 edges per format, homogeneous rank sequence 1,2,2. Basis closure applies only to proved rational linear generators. |
| Finite one-hot transition lift exists | A1.7 | Handwritten proof only | No separate exhaustive test of every lifted transition family; feature dimension may equal the whole state count. |
| Full rank and deficiency both occur; sharing/reset can remove deficiency | A1.8 | Boolean, sharing, reset, initialization, compiler cases | Exact small domains; not an empirical statement about typical large models. |
| Arbitrarily long low-rank prefixes cannot certify deficiency | A1.9 | `delayed_direction` | One 9-state instance: first 8 calls rank1, all-time rank2. The any-horizon family is proved separately. |
| No universal exact-rank algorithm for arbitrary computable unbounded-history policies | A1.10 | Handwritten halting reduction only | No SMT or experiment verifies the undecidability theorem. Finite monitor assumptions are explicitly absent here. |
| Encoding, PC constraints and nonlinear feature construction change rank | A1.11 | Nine finite domain examples and two nonlinear closure counterexamples | No universal optimized-compiler representation result. |
| Real/rational annihilation does not imply ordered FP zero | A1.12 | `floating_null_dot_counterexamples` | BF16 software RNE and actual CPU FP32, 4 products+4 sums per format. Constants exceed A4's legal small gate coefficient set; no D patch is claimed. |

## Verification classes

- Handwritten proofs: the twelve numbered theorem/proposition/counterexample sections, with their stated assumptions.
- Exhaustive finite checks: only the declared activation alphabets, finite state graphs, and binary 3x3 matrix set.
- Sampling: the 80 seeded rational matrices test implementation behavior; low sampled rank is never used as a universal upper bound.
- Finite SMT: **none executed in P2-A1**. P1's earlier SMT results are not relabelled as P2 proof evidence.
- Native arithmetic: local scalar CPU FP32 only, with dtype/raw-word checks. BF16 is software modeled.
- Full system or proof-assistant certification: **none**.

[Independent review](P2_A1_Review.md) records the implementation/reporting gaps found and their resolution. [The report](P2_A1_Report.md) gives dimensions, timing units, algorithmic costs and unresolved work.
