# P2-B4 counterexamples and finite evidence

This catalog separates exact arguments from the new finite experiments.
`switching_results.json` is produced by `verify_switching.py` with seed
**20261114**. Capacity and transaction evidence are separate artifacts.
No earlier test suite or optimizer run is repeated here.

## 1. Reference selection and the two indices

The main finite sets distinguish three comparisons:

- **Original reference:** the old endpoint stays at version zero while the
  updated execution selects later stored versions. This measures accumulated
  change relative to the original program.
- **Adjacent endpoints:** both executions use the same full version list,
  with new index exactly one above the old index at every tick. Their states
  can already differ because their earlier versions differed. This is not a
  same-state comparison unless the initial/history relation supplies one.
- **Two histories:** each execution has its own specified version history
  and schedule. Neither is implicitly relabelled as the original reference.

Another test stores four versions but executes five ticks on schedule
`(0,0,2,3,3)`. Version 1 is never ticked; versions 0 and 3 each serve two
ticks. These are stored numerical history premises. Whether each publication
was authorized belongs to the separate exact-D transaction evidence.
Update count, version index and execution time are different quantities.

## 2. A common contraction family versus individual stability

The scalar numerical family uses maps `s_next=a*s+u/8+b` drawn from four
stored modes:

| a | b |
|---:|---:|
| 1/2 | 0 |
| 1/4 | 0 |
| 1/2 | 1/64 |
| 1/4 | -1/64 |

The common state/input box is `|s|<=1, |u|<=1`. The analyzer proves rounded
inclusion for each mode and compares all **16 ordered mode pairs** in the
same infinity norm. The maximum exact state gain is 1/2. For equal initial
states, the resulting uniform error bound is approximately **0.5845499933**
in software BF16 and **0.5625003353** in audited local FP32. Exact rational
certificates are retained. These bounds cover finite continuations using
that same family and the same domain/policy. They do not certify arbitrary
future learned endpoints outside the family, and are not inferred from the
length-12 stress runs.

**Individually stable modes can amplify under switching.** Let

```
A = [[0,2],[0,0]],     B = [[0,0],[2,0]].
```

Both square to zero. Each is contractive in a suitable *different* weighted
infinity norm: weights `(1,4)` for A and `(4,1)` for B give gain 1/2.
However, `BA=diag(0,4)`. Starting from `(0,1/8)` and alternating A,B,A,B,A,B
gives state norms

```
1/8, 1/4, 1/2, 1, 2, 4, 8.
```

Holding A fixed instead reaches zero after two ticks. Both formats reproduce
these six steps exactly. Since BA has eigenvalue 4, no common norm can make
both A and B strict contractions. This is an exact real switching
counterexample plus a finite-format probe, not an infinite no-overflow claim.

## 3. A fixed-parameter bound expires after a patch

Start at `s0=1/8` with map `s_next=s/2`. The original reference keeps this
map; the updated execution uses coefficients `1/2,2,2`. Their observed
errors are

```
0, 0, 3/32, 15/64.
```

Reusing the pre-patch B3 coefficient L=1/2 and its old rounding/forcing
budget fails to cover the final error in both formats. Recomputing the
endpoint pair, joint domain and state gain at each tick gives a valid B4
bound. The fact that the first comparison was certified does not extend its
scope to later versions.

Conversely, two identical *changing* endpoint histories with the same
initial state and inputs have zero actual difference throughout. The generic
analysis can still return a positive bound because it separately bounds
both rounded executions. A conservative positive number is not observed D
drift, and a large upper coefficient alone is not proof of actual growth.

## 4. Final cancellation does not erase an earlier violation

The original map is constantly zero. The updated map has zero weights and
successive stored biases `1,0,0`. Starting from zero gives errors
`(0,1,0,0)`. The final analytical error bound is below 1/2, but a prefix
budget of 1/2 is refused at **index 1**. The ledger retains the running
maximum; later cancellation cannot restore an already violated prefix
claim.

The parameter-space analogue is equally simple: scalar endpoints
`W0=0,W1=1,W2=0` have safe final total difference zero but an unsafe first
prefix on the protected input 1. Per-prefix safety, adjacent-increment
safety and a final cancelling sum must not be conflated.

## 5. Domain and guard certificates also expire

Replacing a scalar coefficient 1/2 by 2 at state 1 sends the updated state
to 2. A claimed radius-one cap is refused, and the actual point exits that
domain. The analyzer does not clip the state back inside the cap.

A separate identity example preserves the state 1 exactly but the generic
range padding cannot prove the tight radius-one cap. That refusal is a
conservative failure, not an observed exit. Failure to certify a domain and
actual escape from a domain have separate records.

For the strict guard convention `branch(g)=1 iff g>0`, use a zero weight row
and successive bias versions `1,3/4,0`. The first change admits a strict
margin certificate relative to the original guard. The later change reaches
zero, selects the false branch and refuses the updated certificate. A stale
margin for an earlier endpoint cannot protect a later branch. This uses the
prior pure control interface on a new version sequence, not its old suite.

A large stored coefficient Fmax supplies an overflow boundary: from state 1
the first point transition is finite Fmax, while a second transition
multiplies Fmax by itself and overflows. The analytical history is refused.
Its sufficient range proof may fail before the particular point actually
overflows; the independently executed later overflow is recorded separately.

## 6. Actual storage changes the cumulative update

Let `B=2^p`, for precision p=8 or 24, and start the first matrix row at
`(B,0)`. Two proposed increments are `(1,-1)` and `(-1,1)`. Their ideal sum
is zero, but committing each proposal separately gives

```
(B,0) -> (B,-1) -> (B-1,0).
```

The first coordinate of the first proposal ties and rounds back to B. The
second proposal is applied to that *stored* endpoint. The actual cumulative
difference is `(-1,0)`, not zero. The two-row state experiment starts at
`(1,1)`, with a zero second row. Relative to the unchanged original endpoint,
the observed errors after the two ticks are `1,512` in BF16 and
`1,33554432` in FP32. Those large second errors include state amplification;
they are not attributed solely to a same-input parameter difference.

Direct endpoint bounds include generation and storage effects already.
Adding an upstream error ledger again would count those effects twice.

## 7. Subnormals, cancellation and numerical policy

**Thirds followed by identity.** A scalar state with two shared external
inputs uses the rounded row `(2/3,-1/3,-1/3)`, then changes to an identity
state map. On all-one initial/input values, the new execution is zero. On
all-eta values, where eta is the smallest subnormal, the first tick produces
eta and the identity version retains it. The exact real state is zero.
Changing to a later exact identity does not repair an earlier rounded
deviation.

**Nonzero real response, zero observed response.** A new row
`(2^p,1,-2^p)` applied to all-one state/input values has exact output 1 but
ordered rounded output zero. A subsequent zero map stays at zero. The
stored patch is nonzero and the numerical bound is positive, while the
observed paired trajectory difference is zero. Ratios with a zero observed
denominator are reported as undefined.

**Fusion changes the contract.** Put `epsilon=2^(1-p)`,
`a=1+epsilon`, `b=1-epsilon` and bias -1. Separate rounded multiplication
then addition gives zero. A one-round reference for `a*b-1` gives
`-epsilon^2`, a representable nonzero value. This is a rational one-round
reference, **not a native FMA experiment**. A receipt for the separate graph
cannot be carried over to fused or reordered execution by retaining only
the endpoints. The transaction/receipt suite separately rejects altered
policy and graph evidence.

## 8. Capacity counterexamples remain separate from numerical bounds

For a fixed globally proved V, repeating updates in its annihilator does not
consume a new algebraic dimension per update. With `V=span{e1}`, arbitrarily
many exact row increments `(0,a_k)` remain in the same one-dimensional
space. In contrast, accumulating independent protected directions e1 and e2
in two input dimensions exhausts exact annihilator capacity.

Moving spaces do not preserve history automatically: an update safe for
current `span{e2}` may change an earlier task protected by `span{e1}`.
Likewise, two rank-one increments `diag(1,0)` and `diag(0,1)` can sum to a
rank-two update. These are exact algebraic statements, not claims about the
same dimension of a finite stored or BIT-safe set.

Anchor compatibility requires all linear relations, not merely pairwise
overlap. On the three lines generated by e1, e2 and e1+e2, requested values
0, 0 and 1 agree on pairwise intersections, yet cannot be restrictions of one
linear map. Adding such a task cannot be solved merely by shrinking the
future update space.

Finite storage and optimizer proposals add different restrictions. Saturated
rows can have a singleton stored ALG endpoint despite positive algebraic
dimension. This is a different anchored class, not depletion reached by safe
updates from a wider fixed ALG class. Conversely, a particular rounded proposal can stall while other
safe stored endpoints still exist. For one fixed finite endpoint family and
fixed protection/domain/graph, moving inside the same ALG or BIT class does
not by itself shrink that whole class. Local proposal failure is not proof
that the entire class has disappeared. These claims are developed and
tested by the separate B4 capacity deliverables.

The actual `capacity_results.json` run records **14,345 checks** and **10
expected refusals**. It evaluates 1,892 candidates in 12 explicitly finite
endpoint families, 27 anchor assignments (seven jointly compatible), 81
pairwise anchor checks, and 1,728 response/rank-cap queries (468 feasible).
In each format's specified tiny duplicate family, ALG has four endpoints
and BIT has sixteen, including eight rank-two BIT updates. In its tiny split
family, ALG has one endpoint and BIT has two. These are finite-palette
counts, not entire-format cardinalities. The fixed integer family has the
same ALG and BIT class of size sixteen before and after a safe anchor move.
The whole-format Fmax result uses its separate extremal proof rather than
finite enumeration.

## 9. Exact-D integration and numerical non-authority

The separate transaction run records **1,120 checks**, **98 expected
refusals**, **64 accepted SGD commits** and **64 paired protected ticks**.
Of those commits, 48 changed stored words. BF16 produced 16 nonzero changes
followed by 16 storage no-ops, beginning at attempt 17; FP32 produced 32
nonzero changes. The final toy losses were respectively `1/32768` and
`2839225/562949953421312`.

A distinct small-proposal no-op followed by a larger accepted safe edit
demonstrates that the local stall is not global capacity exhaustion. The
test shows nontrivial A responses and benefit on its declared toy loss, not
general learning performance. Its old protected domain, exact admission
policy and schedule stay explicit.

The transaction evidence includes rehashed tampering, budget exhaustion,
stale records and late failures after a copied inner transaction. Refusal
preserves the owned endpoint/state/optimizer/history/ledger snapshot. A
read-only numerical receipt cannot bypass B1 BIT/ALG_AND_BIT authorization.
Those transaction numbers and claims belong to `transaction_results.json`,
not the switching checks below.

## 10. Actual switching scope, storage and reproduction

The saved switching run has **4,028 checks**, including **10 expected
refusals**, zero unexpected failures and seed **20261114**:

| Section | Checks | Scope |
|---|---:|---|
| Complete and seeded histories | 3,944 | 64 complete mode-pair families, 1,152 complete input-history trajectory pairs, 12 seeded length-12 pairs, common family and schedule examples |
| Switching and budgets | 36 | Nilpotent modes, stale coefficients, prefix exhaustion, actual and conservative domain failures |
| Numeric boundaries | 48 | Changing thirds/identity, repeated quantization, cancellation, fusion reference, guards and overflow |

Original and adjacent comparisons enumerate all eight binary mode histories
of length 3 and all 27 ternary input histories for each. Two-history
comparisons enumerate all 16 paired binary mode histories of length 2 and
all nine ternary input histories. The completeness claim is for these fixed
finite sets and specified initial pairs, not all possible format states.
The analytical domain proof has its separate quantified premises.

Every endpoint, raw trajectory, exact decoded error, recurrence coefficient,
state tube and prefix budget is retained. Repeated nested operation-range
details are represented by SHA256 digests of their exact canonical records,
with two full representative network proofs retained. The code reconstructs
all detailed proofs from the recorded histories and domains. Digests identify
data; they do not turn these experiments into a machine-checked theorem.

Bounds are often loose because the certified domain is larger than the
finite observed trajectories. For example, the original-reference bound to
observed-maximum ratio ranges approximately from 1.58 to 11.13 in BF16 and
1.000009 to 10.67 in FP32 across the finite families. Exact ratios and slack
are recorded per family. These are descriptive measurements, not efficiency
or optimality claims.

Run from any directory:

```sh
python -B /workspace/p2_b4/verify_switching.py
```

The saved run took approximately 22.6 seconds locally. No unexpected
scientific failure or predecessor correction was needed in this verifier.
BF16 is the software RNE model; FP32 uses the inherited audited local CPU
path. There is no SMT or proof-assistant claim. GPU, native BF16, arbitrary
fusion/reassociation, general concurrency, hardware faults and C-series
compiler/kernel guarantees remain outside the evidence. A finite stress run
does not prove an unrestricted infinite update process safe.
