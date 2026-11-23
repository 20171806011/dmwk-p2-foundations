# P2-B3 counterexamples and finite propagation evidence

This document separates exact arguments from the finite evidence in
`propagation_results.json` and the complementary `control_results.json`.
The main producer is `verify_propagation.py`, with seed **20261114**.
All earlier files and test suites remain unchanged. General proofs are in
`P2_B3_Theorems.md`; control-flow details are in `P2_B3_Control_Flow.md`.

## 1. Contraction, neutral and amplifying envelopes

The principal fixed-endpoint scalar pair is

```
old: s_next = a*s + u/8
new: s_next = a*s + u/8 + 1/64
```

with `a=1/2`, 1 or 2. Both executions receive the same external input.
Weights, biases and schedule stay fixed throughout every trajectory. The
exact error recurrence for a nonnegative initial difference is

`E_t = a^t E_0 + (1/64) sum_{j=0}^{t-1} a^j`.

For each format, each a, and each initial pair `(0,0)` or `(0,1/8)`, the
verifier exhausts all **27 input histories** of length 3 over `{-1,0,1}`.
Every intermediate in these particular short dyadic fixtures is exactly
representable, and every observed error equals the exact recurrence:

| a | E3 when E0=0 | E3 when E0=1/8 |
|---:|---:|---:|
| 1/2 | 7/256 | 11/256 |
| 1 | 3/64 | 11/64 |
| 2 | 7/64 | 71/64 |

This is attainment of the exact scalar recurrence in these finite fixtures.
It does not claim that a universal rounded-arithmetic envelope is tight, or
that all later iterations remain exact. The additional eight seeded
length-6 histories per case are checked against the full rounded bound; their
observed errors are not assumed to equal the ideal recurrence.

The registered analysis covers a larger domain than the enumerated histories:
all canonical initial states of magnitude at most 1 satisfying the supplied
initial-pair relation, and all common raw input histories with `|u|<=1`.
The simultaneous old/new state boxes, operation ranges and error radii are
derived inductively. The finite experiments do not supply that universal
domain premise.

For `a=1/2`, both rounded endpoint maps preserve the common state box
`|s|<=1`. With initial difference at most `1/8`, the resulting uniform
all-finite-time error bound is `1/8` in both formats. The separately computed
forcing-limit term is approximately 0.058937669 in BF16 and 0.031250421 in
FP32. The exact scalar limit `1/32` is not silently substituted for these
rounded-arithmetic bounds. The uniform conclusion depends on the fixed
endpoints, complete input policy and proved common invariant at every time.

**An amplifying upper coefficient is not a lower-growth theorem.** A second
fixture uses identical old/new endpoints `s_next=2*s` and the same initial
state. Their actual errors remain zero, although the generic analysis uses
an exact-map coefficient L=2 and conservative rounding envelopes. L>1
permits growth of an upper bound; it does not prove actual error growth.

## 2. Domain closure and failed certificates

Two distinct invariant failures are recorded for each format:

- **Conservative failure:** the map `s_next=s`, with zero input coefficient
  and bias, actually preserves every admitted raw state. At `s=1`, the
  observed successor is exactly 1. The generic box arithmetic includes
  conservative local-error padding and cannot certify the radius-one
  invariant by its sufficient inequality. Its refusal is not an observed
  domain exit.
- **Actual exit:** the map `s_next=2*s` at `s=1,u=0` produces 2, which leaves
  the claimed radius-one domain. An error comparison on a falsely retained
  original domain would not justify continuing to apply that domain's
  premises.

The finite time-tube analysis may still handle expanding maps by proving
larger successive boxes. It never clips a computed image back into a claimed
cap. A finite valid tube is not a time-independent invariant.

An additional conservative refusal occurs at a saturated two-layer example:
the first row is `(Fmax,Fmax)`, input `(1/2,1/2)`, and the second layer is
identity. Actual execution returns finite Fmax, while the generic analytic
range enclosure cannot prove totality on the declared box. It is explicitly
recorded as **not** an actual overflow.

## 3. Nonlinear composition and sharing

The main verifier checks two layer types on all nine inputs in
`{-1,0,1}^2`, in both formats:

1. A perturbed affine layer followed by ReLU, then a separately perturbed
   affine identity layer. Every layer's actual error and both endpoints'
   output ranges are checked against the propagated bounds.
2. One physical 2-by-2 bank used at two separately labelled calls, first with
   ReLU and then with identity. Both calls refer to the same stored endpoint
   bank; the analysis includes each call and its own intermediate envelope.

The observed maximum final changes are `7/32` and `1/8`, respectively.
The universal bound divided by the observed maximum over these nine inputs
is approximately:

| Example | BF16 | FP32 |
|---|---:|---:|
| Two distinct banks | 2.280246726 | 2.000004240 |
| Shared bank at two calls | 1.861257960 | 1.625003576 |

These are fixture-specific slack measurements, not performance or optimality
claims. The analytical domain is the complete coordinate box, which is
larger than the finite input alphabet. Treating only the first shared call as
protected would omit the second call's drift and range obligations. The
separate receipt tests exercise graph/site omission and policy tampering.

**ReLU is not equivariant under general rotations.** The control verifier
checks a 90-degree rotation R and vector x for which
`ReLU(Rx) != R ReLU(x)`. Coordinatewise ReLU is 1-Lipschitz in the chosen
norm, but that does not make arbitrary changes of basis preserve its
semantics. A ReLU activation-pattern change itself does not invalidate its
continuous Lipschitz bound; a discontinuous hard branch is different.

## 4. Rounded staircases and both execution errors

The control-flow verifier supplies two exact counterexamples, reproduced in
both formats. Let eta be the minimum positive subnormal and p the precision.

**Half-eta example.** The exact map `F(x)=x/2` has Lipschitz constant 1/2.
At stored inputs eta and `2 eta`, its rounded outputs are 0 and eta. The
output distance eta exceeds one half of the input distance eta. The exact
map's Lipschitz constant therefore cannot be assigned directly to its
rounded staircase.

**Two independent rounding terms are necessary.** Use the exact map
`F(x)=x+1`, with stored inputs

```
x  = 2^(-p)
x' = 2^(-p) + 2^(1-2p).
```

The old addition is a tie and rounds to 1. The new addition rounds to
`1+2^(1-p)`. The actual output/input distance ratio is `2^p`. The old
execution error is `-2^(-p)` and the new error is
`2^(-p)-2^(1-2p)`. Adding the initial distance and the magnitudes of **both**
errors gives the exact output jump. Omitting either execution error fails
the bound. These are fixed-format points, not a claim of arbitrarily small
nonzero encoded gaps within one format.

## 5. Strict branch margins

The control interface fixes `branch(g)=1` exactly when `g>0`; zero selects
the false branch. A certified positive margin must **strictly exceed** the
guard-change bound. Equality is insufficient: old guard `+eta` and new guard
0 flip from true to false at change equal to the old margin. A zero guard
can also flip after the smallest positive encoded change.

In real algebra, old/new guards `+epsilon` and `-epsilon` can differ by an
arbitrarily small `2 epsilon` while their branch outputs differ by 1. In
BF16/FP32 the minimum positive stored gap is finite, so the concrete eta
examples establish the encoded boundary case rather than a continuum limit.
The margin certificate includes endpoint drift, input perturbation and both
rounded guard executions on its declared domain. It is read-only evidence,
not proof of arbitrary subsequent branch-dependent effects.

## 6. Earlier endpoint boundaries survive composition

These are new two-call B3 tests, not reruns of prior suites:

- **Rounded thirds:** a rounded-thirds matrix is followed by ReLU and an
  identity layer. Its exact real output is zero on both `(1,1,1)` and
  `(eta,eta,eta)`. The first input executes to zero, but the tiny input
  executes to eta in each final coordinate. A downstream layer does not
  convert algebraic zero action into bitwise zero action.
- **Endpoint quantization:** the ideal first-layer proposal `(1,-1)` at
  `(2^p,0)` becomes actual difference `(0,-1)`. ReLU stays on its positive
  branch for the tested input `(1,1)`; a downstream factor 1/2 propagates the
  actual change to a final output difference of 1/2. Bounding the ideal
  proposal would miss it.
- **Full-rank BIT-only edit through shared calls:** add eta in one
  off-diagonal position of I2 and reuse the bank at two calls. All protected
  outputs remain equal on `{(0,0),(1,0),(1,1)}`, whose merged span is full
  rank. The effective update does not annihilate that span. This preserves
  the distinction between exact ALG and finite-domain BIT.
- **BIT update rank can exceed algebraic complement dimension:** add eta in
  both off-diagonal positions and use the shared domain `{(0,0),(1,1)}`.
  The effective rank is 2; the protected complement dimension is 1; both
  calls still preserve the protected raw outputs. Algebraic rank bounds
  do not constrain arbitrary BIT-only edits.
- **Saturated storage:** the finite-safe row sum at `(Fmax,Fmax)` protected
  by `(1/2,1/2)` must remain `2 Fmax`. Finite entries cannot exceed Fmax, so
  the original row is the unique stored ALG endpoint despite algebraic
  annihilator dimension 1. The identity downstream does not change this
  extremal proof. No claim is made that the BIT-only endpoint set is a
  singleton or that all format values were enumerated.
- **Incompatible targets:** with protected first-layer space `span{e1}`,
  targets I2 and fixed identity downstream, response `(0,2)` is feasible,
  while `(1,2)` is not. A propagation bound cannot manufacture an exact
  protected response that the quotient relation forbids.

## 7. Actual finite scope, costs and limitations

The saved main propagation run contains **2,103 checks**, including **six
expected refusals**, with zero unexpected failures:

| Section | Checks | Actual scope |
|---|---:|---|
| Algebraic recurrences | 160 | 64 seeded nonhomogeneous and 32 constant-coefficient cases, including T=0 and E0 nonzero |
| State trajectories and domains | 1,640 | 324 complete-input-history cases through T=3, 96 seeded histories through T=6, invariants and domain failures |
| Nonlinear/shared networks | 186 | 36 point cases and complete per-case nine-input sets |
| Retained boundaries | 117 | 16 two-call point cases, capacity/target arguments and two conservative saturation refusals |

The 420 recurrent histories contain 1,548 paired time transitions; their raw
states and exact decoded error at every time are retained. The completeness
claim applies to the finite input histories for the specified initial pairs,
not all canonical initial states. Global initial/history coverage comes from
the conditional analytical tube proof.

For the E0=0, T=3 fixtures, the analytic all-time-observation bound divided by
the observed maximum was about 1.581881909, 2.870981386 and 6.663343621 in
BF16 for contraction, neutral and amplification, respectively. FP32 values
were about 1.000008770, 1.000028133 and 1.000085098. Exact rational slack and
ratios are saved per family. A coarse analytic envelope is not relabelled as
a measured error, and a ratio at zero observed difference remains undefined.

The complementary control run records **1,578 checks** and **28 expected
refusals**. Its complete small guard-pair families, seeded cases, rotations
and branch boundaries have their own scope and counts. Receipt and
independent-review results are separate; these section counts are not
presented as a complete-machine-proof total.

Run the main scientific checks from any directory:

```sh
python -B /workspace/p2_b3/verify_propagation.py
```

The saved main run took approximately 10.3 seconds locally; the exact elapsed
time is in its JSON and will vary on reproduction. BF16 is the software RNE
model; FP32 is the inherited audited local CPU execution path. No SMT or
proof assistant was used by this verifier. No unexpected main-suite failure
or predecessor correction was needed for these delivered fixtures.

GPU, native BF16, arbitrary fusion/reassociation, general concurrency,
evolving endpoints, large-model learning benefit and whole-program side
effects remain outside these results. Fixed-endpoint finite propagation does
not complete B4, and a nonzero numerical budget does not authorize a change
under B1's BIT/ALG_AND_BIT transaction policy.
