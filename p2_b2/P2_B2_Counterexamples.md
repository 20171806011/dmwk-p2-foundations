# P2-B2 counterexamples, tightness and finite evidence

This document reports the current B2 checks in `verify_bounds.py` and
`bound_results.json`. Exact mathematical examples, finite tests and backend
coverage are distinguished below. It does not reuse any prior test suite.
The prior implementation interfaces are read-only dependencies.

## Geometry: what must be bounded separately

Take the true protected space `V=span{e1}` in two input dimensions. Every
example in this section is exact rational algebra; the norm bounds use
outward rational intervals, with squared comparisons performed exactly.

1. **Each term can be tight.** For `Delta=(3,0)` and `h=e1`, the protected
   term is exactly 3 and the residual term is zero. For `Delta=(0,5)` and
   `h=e2`, the protected term is zero and the residual term is exactly 5.
   The latter also shows that zero update action on V does not remove the
   activation-residual term for an input outside V.
2. **Separate triangle terms can overestimate.** For `Delta=(3,4)` and
   `h=(1,1)`, the actual change is 7; `epsilon=3`, `M=5`, and the decomposed
   bound is `3+5=8`. The additional uniform bound is an outward enclosure of
   `5 sqrt(2)`. The general theorem and any sharper envelope must account for
   the coupling imposed by the same operator norm M; this example does not
   prove universal simultaneous tightness of separate terms.
3. **Scaling is not subspace error.** `U=e1/2` spans the correct V but has
   Gram deviation `3/4`; the conditioning factor is 2. Calling it
   orthonormal would incorrectly omit that factor. `U=2e1` also spans V but
   has Gram deviation 3. The implemented `delta_G<1` sufficient-condition
   route refuses that certificate. This is not proof that the space is
   singular or that no different conditioning certificate could work.
4. **Gram quality is not true-space coverage.** `U=e2` is exactly
   orthonormal, and `Delta=(1,0)` annihilates U. Nevertheless, its response on
   the true protected input `e1` is 1. The projector deviation is 1. A basis
   fitted or selected for another subspace cannot certify V. The rational
   rotation `U=(3/5,4/5)^T` supplies a less extreme exact test: its true
   projector gap is `4/5`, while the implementation may use a larger
   certified spectral upper bound.

The geometry verifier additionally covers zero input, zero update, empty
protected span, full protected span, and distinct generator matrices for the
same space. A zero basis column, a false orthonormal label and a falsely
claimed true space are refused. Finite-precision bitstring inputs are not
treated as a vector space closed under real linear combinations.

## A disjoint ledger can cancel; do not add it twice

Use `H=e1`, `P=diag(0,1)`, `G*=(1,2)`,
`P_tilde=diag(1/4,3/4)`, `G_hat=(2,3)` and
`D_hat=(5/8,19/8)`. For either tested format with precision p, let
`W=(2^p,0)` and store `W'=RNE(W+D_hat)=(2^p,19/8)`. Then:

| Disjoint component | Exact value |
|---|---|
| Ideal safe increment `G* P` | `(0,2)` |
| Representation error | `(1/4,-1/2)` |
| Optimizer-candidate error | `(1/4,3/4)` |
| Generation error | `(1/8,1/8)` |
| Endpoint storage error | `(-5/8,0)` |
| Actual `Delta=W'-W` | `(0,19/8)` |

All four errors are nonzero. Their signed sum plus the ideal increment is
exactly Delta. On the protected input e1, the separate absolute ledger budget
is `5/4`, while the direct endpoint bound is exactly zero. These are two
alternative accounting routes. Adding the ledger to a direct Delta bound
counts upstream effects again and destroys the useful cancellation. The
identity checks accounting only; it does not certify that an asserted ideal
optimizer represents a particular external training procedure.

## Two independently rounded executions

The following observations were reproduced for both software BF16 and the
inherited locally audited FP32 backend. The graph is bias-first, ascending
column order, separate multiply/add, RNE, gradual underflow and canonical
positive zero. The direct references sum decoded values as exact rationals.
Let `eta` denote the smallest positive subnormal of the format and
`u=2^(-p)` its unit roundoff.

| Case | Exact algebraic change | Observed output change | Certified point infinity bound |
|---|---:|---:|---:|
| Zero to weight `1/2`, input `eta` | `eta/2` | 0 | `eta` |
| Zero to rounded-thirds matrix, input `(1,1,1)` | 0 | 0 | 0 |
| Same matrix, input `(eta,eta,eta)` | 0 | `eta` per coordinate | `eta` |
| Endpoint quantization case below, input `(1,1)` | -1 | -1 | 1 |
| Zero to row `(2^p,1,-2^p)`, input all ones | 1 | 0 | 2 |
| Tiny BIT-only edit, protected input `(1,1)` | nonzero, size `eta` per changed row | 0 | `2 eta` |

The infinity bound is an absolute number, so the sign of a scalar change is
shown only in the algebraic/observed columns. Where the observed norm is zero,
bound-to-observed ratios are recorded as undefined rather than divided by
zero.

**Relative-only rounding fails with underflow.** The exact product
`(1/2)*eta=eta/2` rounds to zero. Its error `eta/2` exceeds
`u*(eta/2)`. Thus a relative-only local model cannot cover this operation.
The additive underflow term is essential. The resulting positive absolute
bound is valid even though the actual old/new outputs happen to agree.

**A basis execution test is not a full-span BIT certificate.** The rounded
thirds matrix has exact decoded row sums zero. It also executes to zero on
the all-ones basis vector. At the tiny multiple of that vector, rounded
products produce raw word 1 in each output. Including both execution-rounding
contributions bounds this change; algebraic orthogonality alone does not.

**Commit rounding changes the relevant delta.** At `W=(2^p,0)`, the ideal
proposal `(1,-1)` annihilates `(1,1)`. The first proposed coordinate is a
tie and rounds back to `2^p`; the stored endpoint is `(2^p,-1)`, with actual
delta `(0,-1)`. Its protected output changes by -1. All B2 endpoint bounds
use this stored difference, not the proposal.

**Cancellation can make a valid bound loose.** The ordered execution of
`2^p+1-2^p` returns zero, whereas its exact value is 1. The point bound from
zero to this layer is 2: the absolute algebraic change and the execution
error cancel in the observed result. This is a conservative bound, not an
incorrect claim of a change of size 2.

**Zero reference outputs require an absolute component.** Starting from the
row `(1,-1)`, input `(1,1)` has output zero. Changing the second coefficient
to `-1/2` gives change `1/2`. The relative bound is undefined. A mixed budget
with absolute budget `1/2` accepts the bound at reference lower bound zero;
one with absolute budget `1/4` rejects it regardless of the supplied relative
budget 10. This is a numeric budget result, not live update authorization.

## Retained capacity and coverage boundaries

**Full rank does not eliminate rounded equivalence.** For the registered
split-feedback activation set `{(0,0),(1,1),(1,0)}`, the actual protected span
is full rank. Changing `I2` by an off-diagonal eta changes the exact product
but not any of those executed outputs. The B2 point bound on `(1,1)` is
`2 eta`, a conservative bound which does not itself certify BIT via the
strict separation rule. Exact complete-domain execution can still establish
BIT. This preserves the A3 distinction between BIT and exact ALG.

Adding eta in both off-diagonal positions gives an effective rank-2 change
that leaves the duplicate-feedback domain `{(0,0),(1,1)}` unchanged. Its
protected complement has dimension 1. The algebraic rank restriction does
not apply to this BIT-only edit.

**Finite storage can collapse algebraic capacity.** For row
`(Fmax,Fmax)` protected at `(1/2,1/2)`, the algebraic-safe row sum must remain
`2 Fmax`. Every finite stored entry is at most Fmax, so the only such stored
endpoint is the original. The actual original output is finite Fmax. This
is an extremal proof plus a finite probe, not enumeration of every format
word or a statement that the BIT-only feasible set is a singleton.

**Requested responses must respect quotient relations.** With V generated
by e1 and target matrix `I2`, response `(0,2)` is feasible but `(1,2)` is
not: the protected target e1 requests a nonzero change. A perturbation budget
does not remove that exact impossibility.

**Domain provenance remains separate.** The 9-point ternary tests below
exhaust their declared domain. They do not prove a global activation
envelope. The analytic box theorem covers all admitted raw inputs inside
its coordinate bounds only when those bounds are proved to contain every
relevant call. Sample omission, omitted shared sites and changed graph/policy
are tested separately by the B2 bounded-certificate verifier. Neither a point
bound nor a finite basis label supplies that provenance.

## Refusals and range certification

The saved bounds run records 26 expected exceptions: four invalid basis
certificates, two actual overflows, two analytic-box failures to certify
totality, and eighteen invalid-word cases across the two formats. The
invalid-word cases place negative zero, infinity and NaN separately in
weights, inputs and biases. Actual overflow uses `Fmax*2`.

A box refusal is a failure of a sufficient range proof, not necessarily
proof that every input in the box overflows. Only the explicit point
overflow example establishes an actual fault for that input. No relative
`gamma_n` specialization is used to bypass underflow or overflow checks in
this verifier. Its numerical evidence relies on exact local residuals and
the stated additive-underflow box recurrence.

## Actual coverage, bound ratios and development record

The saved run has **3,419 checks**, **26 expected refusals**, and zero
unexpected failures. Refusals are included in the check count. The fixed
seed is **20261114**. The sections contain:

| Section | Checks | Scope |
|---|---:|---|
| Geometry | 504 | 69 root intervals, 7 named and 64 seeded geometry cases, 3 approximate bases, 4 refusals |
| Ledger | 8 | Same nonzero four-error telescope, one stored endpoint pair per format |
| Finite execution | 2,614 | 12 seeded endpoint pairs × 9 complete inputs × 2 formats; 2 bias cases; 26 analytic box records |
| Counterexamples | 293 | 24 adversarial point records, target compatibility, mixed budgets and 22 numeric refusals |

For the 12 ternary-domain endpoint pairs in each format, the conservative box
infinity bound divided by the **observed finite-domain maximum** ranged from
approximately **1.00940249 to 1.01802679** in BF16 and **1.00000014305 to
1.00000027418** in FP32. Exact rational ratios and slack are saved for every
pair. These are descriptive values for these fixtures, not optimality or
performance claims. The analytic domain is larger than the 9 tested points.
Pointwise adversarial ratios can be undefined or much less informative, as
the zero-observation examples demonstrate.

During implementation, the root-interval API was improved from an absolute
dyadic grid to a scale-normalized grid. An initial verifier width assertion
for the old absolute grid then failed; it was replaced by the documented
relative-width assertion. The exact enclosure inequalities continued to
hold. The final saved run uses the normalized API. No counterexample was
removed to obtain a passing result.

Run from any directory:

```sh
python -B /workspace/p2_b2/verify_bounds.py
```

The execution costs are recorded by the script; they are local measurements.
This verifier makes no SMT or proof-assistant claim. Independent review,
general proofs, complete registered-domain receipts and B1 rollback tests
are separate artifacts. GPU, native BF16, arbitrary fusion/reassociation,
general concurrency and subsequent multilayer or long-term claims remain
outside this evidence.
