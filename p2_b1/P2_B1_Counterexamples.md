# P2-B1 counterexamples and regression evidence

This document separates exact counterexamples from finite execution probes and
transaction tests. The reproducible records are in `constraint_results.json`;
`verify_constraints.py` generates them with seed **20261114**. All matrices are
interpreted over the rationals for exact algebra unless an execution policy is
stated. BF16 means the inherited software RNE model. FP32 arithmetic probes use
the inherited audited local NumPy scalar backend with separate multiply/add,
gradual underflow and canonical positive zero. The host Adam proposal uses
ordered binary64 Python arithmetic, including `pow` and `math.sqrt`; it is not
the protected BF16/FP32 kernel and carries no endpoint authority.

## 1. Restricting the gradient is not enough

Let the protected space be `span{(1,1,1)}`. The raw gradient `(3,0,0)` projects
exactly to `g=(2,-1,-1)`. A raw all-ones gradient would project to zero and
therefore would not be a counterexample.

**B1-C1 — coordinatewise Adam normalization.** With zero moments, learning
rate 1, `beta1=beta2=1/2`, epsilon 1 and no decay, the ideal first parameter
increment from `g` is `(-2/3,1/2,1/2)`, with protected row sum `1/3`. The actual
recorded host increment is

```
(-6004799503160661/9007199254740992, 1/2, 1/2)
```

whose exact decoded row sum is `3002399751580331/9007199254740992`, also nonzero.
The final-projection strategy separately forms the optimizer proposal from the
raw gradient and then projects its entire increment; its recorded increment is
`(-1/2,1/4,1/4)`. These are two explicitly different strategies. The assertion
is that only the latter strategy enforces the exact increment constraint by
construction. Quantization and the endpoint certificate remain necessary.

**B1-C2 — off-space momentum.** Start with old momentum `(1,0,0)` and use
momentum coefficient `1/2` with safe gradient `g`. The next momentum is
`(3/2,-1/2,-1/2)`. Its negative parameter step has row sum `-1/2`. Final
projection gives `(-4/3,2/3,2/3)`. Projection of the step does not assert that
stored moments themselves are repaired or confined to the annihilator.

**B1-C3 — weight decay after gradient projection.** At `W=(1,0,0)`, learning
rate 1 and decoupled decay coefficient `1/4`, the otherwise safe SGD step gets
an additional `(-1/4,0,0)`. The total protected change is `-1/4`. The final
projection must include decay if the claimed constraint covers the total
proposal.

**B1-C4 — clipping order.** Coordinate clipping `g` to `[-1,1]` gives
`(1,-1,-1)`, with row sum `-1`. A common exact rational scalar times `g` still
annihilates the protected vector. The implementation's global-norm mode uses a
host norm estimate and then exact common rational scaling. This proves
constraint preservation for that scaling; it does not certify an exact
norm-threshold decision or independently certify the stored endpoint.

## 2. Low rank has several different meanings

**B1-C0 — per-step versus accumulated rank.** With `V={0}`, take
`D1=diag(1,0)` and `D2=diag(0,1)`. Both increments have rank 1, while
`D1+D2=I2` has rank 2. A per-step rank bound does not bound cumulative rank.

Likewise, an old rank-1 adapter `diag(1,0)` and a new rank-1 adapter
`diag(0,1)` differ by `diag(-1,1)`, of rank 2. The generic bound on the
difference of two rank-k adapters is `2k`, subject to ambient dimensions.
Both adapters and their difference still annihilate `V={0}`. Exact proposal
rank, accumulated adapter rank and final decoded endpoint-difference rank are
recorded separately by the implementation; no endpoint rank cap is implicit.

## 3. Exact proposals are not stored or executed guarantees

**B1-C5 — endpoint quantization.** For precision `p` (8 for BF16, 24 for
FP32), take a row `W=(2^p,0)` and the exact safe proposal `(1,-1)`, protected
against `(1,1)`. RNE of `2^p+1` is `2^p`, while `-1` is stored exactly. Thus
the effective increment is `(0,-1)`, not `(1,-1)`, and the protected output
changes from `2^p` to `2^p-1`. Both formats reproduce this and the inherited
complete-domain certificate rejects the endpoint.

**B1-C6 — algebraic safety and a zero basis test do not imply BIT.** Store the
3-by-3 rounded thirds matrix with diagonal `RNE(2/3)` and off-diagonal
`RNE(-1/3)`. Its decoded row sums are exactly zero. The fixed execution
produces zero on `(1,1,1)`, but produces raw word 1 in each output coordinate
on `(eta,eta,eta)`, where `eta` is the smallest positive subnormal of the
format. The exact algebraic product is zero on both inputs. This refutes both
ALG-implies-BIT and the use of floating basis probes as full-space evidence.
Both formats reject this candidate under the registered two-input domain.

**B1-C7 — full protected rank does not eliminate BIT-only edits.** Starting
from `I2`, add `eta` in entry `(0,1)`. The split feedback model's global
protected vectors include `(1,1)` and `(1,0)`, so their rank is 2. All its
registered D traces remain bitwise identical because the tiny extra term is
rounded away beside 1. The exact delta does not annihilate this full space.
The legal A input `e2` changes its output from `(0,1)` to `(eta,1)`. This is a
stored nonzero BIT-only modification, not an exact algebraic safe direction.
The B1 BIT contract accepts it; the stronger ALG_AND_BIT contract rejects it.
An axis-protecting registry also rejects it because that registry includes
the exposing activation `e2`.

**B1-C8 — BIT edit rank can exceed the algebraic complement dimension.** Add
`eta` in both off-diagonal entries of `I2` in the duplicate-feedback model.
The effective delta has rank 2, while the protected span has rank 1 in input
dimension 2. The registered D outputs are unchanged. This does not contradict
the algebraic rank bound because the edit is not an exact annihilator.

**B1-C9 — finite storage can collapse algebraic capacity.** Let every entry
of a 2-by-2 weight matrix equal the largest finite format value `Fmax` and
protect `(1/2,1/2)`. The algebraic annihilator dimension is 2. For a finite
stored algebraic-safe endpoint, each row must retain sum `2 Fmax`, while
each entry is at most `Fmax`; hence both entries must equal `Fmax`. The only
such endpoint is the original. This is an extremal proof over all finite
format values, accompanied by a probe showing the original execution returns
finite `Fmax`. It is not an exhaustive enumeration and does not assert that
the BIT-only endpoint set is a singleton.

**B1-C12 — rounded projector coefficients.** For `H=(1,3)^T`, the exact
orthogonal projector onto its annihilator is

```
P = [[9/10, -3/10], [-3/10, 1/10]].
```

Independently rounding its coefficients to a stored matrix Q gives:

| Format | Exact decoded QH |
|---|---|
| BF16 | `(-1/256, -1/2048)^T` |
| FP32 | `(-1/16777216, -1/134217728)^T` |

An approximate projector is a proposal generator, not an acceptance proof.
No general numerical conditioning bound is established in B1.

## 4. Coverage and requested output changes matter

**B1-C10 — samples and omitted shared calls.** Replace `I2` by `diag(1,2)`.
The output on `e1` is unchanged, but the output on `e2` changes. A sampled
single call cannot authorize a shared matrix when another legal call uses
`e2`. Both format-specific complete shared-axis certificates reject it.

**B1-C11 — safe updates can be silent and targets can be impossible.** With
protected space `span{e1}`, the nonzero update row `(0,1)` is silent on `e1`
and responds on `e2`. On target matrix `X=I2`, requested response `(0,2)` is
feasible, but `(1,2)` is impossible: its first target lies in the protected
space and requests a nonzero response there. This is exact target-relation
incompatibility, not a failed optimizer search. Existence of a responding
safe update alone does not establish learning-task benefit.

## 5. Transaction and stale-certificate regressions

The new B1 interface is tested after accepting a nonzero momentum update,
so rollback comparisons include nonzero moments. For each format it accepts
one exact, bitwise-safe optimizer update and verifies that weights/version and
optimizer step advance together without changing q/ticks. Its refusal checks
compare the **entire** current snapshot: weights, optimizer moments/step,
protected state, clocks, version, config, model, format, claim and schedule.

The 32 B1 refusal records cover, in each format:

- replay after a successful commit;
- a protected tick between prepare and commit, even though the underlying
  complete-domain D proof still holds;
- an unsafe AI endpoint, unknown restriction, wrong gradient shape and
  malformed packet;
- graph, numerical policy, schedule, model/domain identity, weight version,
  optimizer state, config, request and endpoint corruption, with the envelope
  hash recomputed after corruption;
- the stronger joint contract refusing the same tiny endpoint accepted by BIT.

The stale tick case preserves the state reached by that tick; it does not
roll the protected state back to the earlier prepared snapshot. These checks
are semantic packet validation under a trusted serialized API, not
cryptographic authentication, arbitrary memory isolation, crash consistency
or general concurrent execution certification.

## 6. Actual finite scope and development findings

The saved run contains **2,400 checks**: 2,316 exact/optimizer checks, 38
numeric/domain checks and 46 transaction checks. It includes 324 exhaustive
binary-generator/ternary-direction projection pairs, 64 seeded rational
factor cases, four named edge cases, eight inherited pure-certificate
refusals, and 32 new B1 transaction refusals. Refusal counts are a subset of
the checks, not an additional total. There were zero unexpected failures in
the saved run. No SMT or proof assistant was used by this verifier.

During development, the verifier initially assumed the prior response solver
returned a report directly; its documented API actually returns
`(update_or_None, report)`. The verifier was corrected and rerun. This was a
test adapter mismatch, not a corrected theorem or hidden implementation
failure. The counterexamples above intentionally falsify overstrong closure
claims; none was discarded to obtain a passing result.

Run from any directory:

```sh
python -B /workspace/p2_b1/verify_constraints.py
```

The original finite results remain separate from the general proofs in
`P2_B1_Theorems.md` and the independent review. GPU, native BF16, arbitrary
optimization/fusion, large-model learning performance and general concurrency
remain outside this evidence.
